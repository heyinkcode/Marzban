import asyncio
import importlib.util
import json
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text

import test_usage_continuity as fixtures
from app.db import crud, user_entitlement as service
from app.db.models import NextPlan, UserEntitlementOperation, UserUsageRecovery, UserUsageResetLogs
from app.db.usage_continuity import RecoveryError
from app.models.admin import Admin
from app.models.user import UserModify
from app.models.user_entitlement import EntitlementApply, EntitlementCommand
from app.routers import user_entitlement as routes


class NativeEntitlementTests(unittest.TestCase):
    setUp = fixtures.ContinuityTests.setUp
    make_user = fixtures.ContinuityTests.make_user
    latest_user = fixtures.ContinuityTests.latest_user
    sudo = Admin(username="operator", is_sudo=True)

    def expires(self, days):
        return int((self.now + timedelta(days=days)).replace(tzinfo=timezone.utc).timestamp())

    def payload(self, action, **fields):
        command = EntitlementCommand(action=action, **fields)
        out = service.preview(self.db, self.user.username, command, self.sudo)
        return {"operation_id": str(uuid4()), "guard": out["guard"], "command": command.model_dump(exclude_none=True),
                "confirmed": action in ("renew", "restore")}

    def apply(self, body, db=None, admin=None):
        return service.apply(db or self.db, "example_user", EntitlementApply.model_validate(body), admin or self.sudo)

    def test_extend_preserves_exhaustion_traffic_strategy_and_next_plan(self):
        self.user.status = "expired"
        self.user.expire = self.expires(-1)
        self.user.used_traffic = 10000
        self.user.next_plan = NextPlan(data_limit=12000, expire=self.expires(60))
        self.db.commit()
        before = self.user.lifetime_used_traffic
        result = self.apply(self.payload("extend", expires_at=self.expires(30)))
        user = self.latest_user()
        self.assertEqual(user.expire, self.expires(30))
        self.assertEqual(user.used_traffic, 10000)
        self.assertEqual(user.status, "limited")
        self.assertEqual(user.data_limit, 10000)
        self.assertEqual(user.data_limit_reset_strategy, "month")
        self.assertEqual(user.lifetime_used_traffic, before)
        self.assertEqual(user.next_plan.data_limit, 12000)
        self.assertEqual(result["after"]["remaining_bytes"], "0")

    def test_add_only_quota_and_deduplicates_same_payload(self):
        self.user.status = "limited"
        self.user.used_traffic = 10000
        self.db.commit()
        body = self.payload("add", extra_bytes="2000")
        first = self.apply(body)
        self.assertEqual(self.apply(body), first)
        self.assertEqual(self.latest_user().data_limit, 12000)
        self.assertEqual(self.user.used_traffic, 10000)
        self.assertEqual(self.user.expire, self.expires(15))
        self.assertEqual(self.user.status, "active")
        self.assertEqual(len(self.user.usage_logs), 2)
        self.assertEqual(self.db.query(UserEntitlementOperation).count(), 1)
        with self.assertRaisesRegex(RecoveryError, "operation_conflict"):
            self.apply({**body, "command": {"action": "add", "extra_bytes": "4000"}})

    def test_renew_requires_confirmation_preserves_history_and_keeps_new_traffic_on_replay(self):
        body = self.payload("renew", expires_at=self.expires(40))
        with self.assertRaisesRegex(RecoveryError, "explicit_confirmation_required"):
            self.apply({**body, "confirmed": False})
        self.user.used_traffic += 25
        self.db.commit()
        lifetime = self.user.lifetime_used_traffic
        first = self.apply(body)
        user = self.latest_user()
        self.assertEqual(first["before"]["used_bytes"], "125")
        self.assertEqual(user.used_traffic, 0)
        self.assertEqual(user.expire, self.expires(40))
        self.assertEqual(user.lifetime_used_traffic, lifetime)
        self.assertEqual(user.data_limit, 10000)
        self.assertEqual(service.get_overview(self.db, user.username, self.sudo)["latest_reset"]["origin"], "native_renewal")
        with self.assertRaisesRegex(RecoveryError, "reset_not_restorable"):
            self.payload("restore", reset_id=first["reset_id"], reason="wrong-cycle negative test")
        user.used_traffic = 37
        self.db.commit()
        self.assertEqual(self.apply(body), first)
        self.assertEqual(self.latest_user().used_traffic, 37)
        self.assertEqual(len(self.user.usage_logs), 3)

    def test_sudo_targeted_restoration_keeps_prior_audit_and_uses_live_counter(self):
        first = self.user.usage_logs[0]
        first.used_traffic_at_reset = 200
        self.db.flush()
        self.db.add(UserUsageRecovery(operation_id=str(uuid4()), user_id=self.user.id, username=self.user.username,
                    user_created_at=self.user.created_at, reset_id=first.id, restored_bytes=200,
                    payload_sha256="a"*64, receipt={"prior": True}))
        self.db.commit()
        latest = self.user.usage_logs[-1]
        body = self.payload("restore", reset_id=latest.id, reason="Verified accidental reset within this period")
        with self.assertRaisesRegex(RecoveryError, "permission_denied"):
            self.apply(body, admin=Admin(username="operator", is_sudo=False))
        self.user.used_traffic += 177
        self.db.commit()
        lifetime = self.user.lifetime_used_traffic
        result = self.apply(body)
        self.assertEqual(result["restored_bytes"], "6000")
        self.assertEqual(self.latest_user().used_traffic, 6277)
        self.assertEqual(self.user.lifetime_used_traffic, lifetime)
        self.assertEqual(self.db.query(UserUsageRecovery).count(), 2)
        self.assertEqual(self.apply(body), result)
        with self.assertRaisesRegex(RecoveryError, "reset_not_restorable"):
            self.payload("restore", reset_id=latest.id, reason="Must not restore twice")

    def test_guard_rejects_a_new_reset_and_quota_crossing_after_preview(self):
        latest = self.user.usage_logs[-1]
        body = self.payload("restore", reset_id=latest.id, reason="Same test period")
        self.user.used_traffic = 4000
        self.db.commit()
        with self.assertRaisesRegex(RecoveryError, "restore_would_reach_quota"):
            self.apply(body)
        self.user.used_traffic = 100
        self.user.usage_logs.append(UserUsageResetLogs(reset_at=self.now, used_traffic_at_reset=100))
        self.db.commit()
        with self.assertRaisesRegex(RecoveryError, "reset_not_restorable"):
            self.apply(body)
        self.assertEqual(self.db.query(UserEntitlementOperation).count(), 0)

    def test_new_operation_with_stale_preview_cannot_add_twice(self):
        body = self.payload("add", extra_bytes="200")
        second = {**body, "operation_id": str(uuid4())}
        def run(value):
            with self.sessions() as session:
                try:
                    return self.apply(value, db=session)["action"]
                except RecoveryError as error:
                    return error.detail["code"]
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertCountEqual(list(pool.map(run, [body, second])), ["add", "entitlement_changed"])
        self.assertEqual(self.latest_user().data_limit, 10200)

    def test_legacy_put_omission_keeps_plan_and_expiry_does_not_revive_exhausted_user(self):
        self.user.status = "expired"
        self.user.expire = self.expires(-1)
        self.user.used_traffic = 10000
        self.user.next_plan = NextPlan(data_limit=11000, expire=self.expires(50))
        self.db.commit()
        crud.update_user(self.db, self.user, UserModify(expire=self.expires(21)))
        self.assertEqual(self.user.status, "limited")
        self.assertEqual(self.user.used_traffic, 10000)
        self.assertIsNotNone(self.user.next_plan)
        crud.update_user(self.db, self.user, UserModify(next_plan=None))
        self.assertIsNone(self.user.next_plan)
        self.assertEqual(self.user.expire, self.expires(21))

    def test_disabled_preserved_and_renew_does_not_destroy_pending_plan(self):
        self.user.status = "disabled"
        self.user.next_plan = NextPlan(data_limit=11000, expire=self.expires(50))
        self.db.commit()
        with self.assertRaisesRegex(RecoveryError, "next_plan_conflict"):
            self.payload("renew")
        self.apply(self.payload("add", extra_bytes="100"))
        self.assertEqual(self.latest_user().status, "disabled")
        self.assertIsNotNone(self.user.next_plan)

    def test_legacy_quota_edit_preserves_on_hold_even_if_quota_is_exhausted(self):
        self.user.status = "on_hold"
        self.user.used_traffic = 9500
        self.db.commit()
        crud.update_user(self.db, self.user, UserModify(data_limit=9000))
        self.assertEqual((self.user.status, self.user.used_traffic, self.user.data_limit), ("on_hold", 9500, 9000))

    def test_receipt_scope_and_strict_inputs(self):
        valid = self.apply(self.payload("extend", expires_at=self.expires(31)))
        with self.assertRaisesRegex(RecoveryError, "permission_denied"):
            service.get_receipt(self.db, self.user.username, valid["operation_id"], Admin(username="other", is_sudo=False))
        self.assertEqual(service.get_receipt(self.db, self.user.username, valid["operation_id"],
                                            Admin(username="operator", is_sudo=False)), valid)
        for values in (dict(action="extend", expires_at=True), dict(action="extend", expires_at=1, extra_bytes="5"),
                       dict(action="add", extra_bytes=22), dict(action="restore", reset_id=1)):
            with self.assertRaises(ValueError):
                EntitlementCommand.model_validate(values)

    def test_preview_routes_are_registered_and_read_only(self):
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(routes.router)
        paths = app.openapi()["paths"]
        self.assertIn("/api/user/{username}/entitlement/preview", paths)
        self.assertIn("/api/user/{username}/entitlement/operations/{operation_id}", paths)
        self.payload("add", extra_bytes="300")
        self.assertEqual(self.db.query(UserEntitlementOperation).count(), 0)
        self.assertEqual(self.latest_user().data_limit, 10000)

    def test_http_owner_preview_submit_replay_and_read_receipt(self):
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(routes.router)
        app.dependency_overrides[routes.get_db] = lambda: self.db
        path = "/api/user/example_user/entitlement"

        def call(method, suffix="", body=None, token=None):
            target = path + suffix
            messages = []
            headers = [(b"content-type", b"application/json")]
            if token:
                headers.append((b"authorization", ("Bearer " + token).encode()))
            scope = {"type": "http", "method": method, "path": target, "raw_path": target.encode(),
                     "query_string": b"", "headers": headers, "http_version": "1.1", "scheme": "http"}
            async def receive():
                return {"type": "http.request", "body": json.dumps(body).encode() if body else b"", "more_body": False}
            async def send(message):
                messages.append(message)
            asyncio.run(app(scope, receive, send))
            start = messages[0]
            return start["status"], json.loads(b"".join(message.get("body", b"") for message in messages)), dict(start["headers"])

        operator = Admin(username="operator", is_sudo=False)
        stranger = Admin(username="stranger", is_sudo=False)
        with patch.object(Admin, "get_admin", side_effect=lambda token, db: operator if token == "owner" else stranger):
            self.assertEqual(call("GET")[0], 401)
            self.assertEqual(call("GET", token="other")[0:2], (403, {"detail":{"code":"permission_denied"}}))
            command = {"action":"add", "extra_bytes":"750"}
            status, preview, headers = call("POST","/preview",command,"owner")
            self.assertEqual((status, headers[b"cache-control"]), (200, b"no-store"))
            self.assertEqual(self.latest_user().data_limit, 10000)
            body = {"operation_id":str(uuid4()), "command":command, "guard":preview["guard"],"confirmed":False}
            status, receipt, _ = call("POST", "/operations", body, "owner")
            self.assertEqual(status, 200)
            self.assertEqual(receipt["after"]["quota_bytes"], "10750")
            self.assertEqual(call("POST", "/operations", body, "owner")[1], receipt)
            self.assertEqual(call("GET", "/operations/" + body["operation_id"], token="owner")[1], receipt)
            self.assertEqual(self.latest_user().data_limit, 10750)


class EntitlementMigrationTests(unittest.TestCase):
    def test_receipts_protect_downgrade(self):
        file = Path(__file__).resolve().parents[1]/"app/db/migrations/versions/e567fa89bc01_user_entitlement_operations.py"
        spec = importlib.util.spec_from_file_location("entitlement_migration", file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        engine = create_engine("sqlite://")
        with engine.begin() as conn:
            with Operations.context(MigrationContext.configure(conn)):
                module.upgrade()
                self.assertIn("user_entitlement_operations", inspect(conn).get_table_names())
                module.downgrade()
                module.upgrade()
                conn.execute(text("""insert into user_entitlement_operations(operation_id,user_id,username,user_created_at,
                    action,payload_sha256,recorded_at,receipt) values(
                    'example',1,'test','2026-01-01','add','example','2026-03-01','{}')"""))
                with self.assertRaisesRegex(RuntimeError, "receipts exist"):
                    module.downgrade()
                self.assertEqual(conn.execute(text("select count(*) from user_entitlement_operations")).scalar(), 1)
        engine.dispose()
