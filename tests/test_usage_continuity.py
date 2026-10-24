"""Real isolated SQLite ledgers, transactions, routes, receipts and migrations.

No production credentials, network requests or live Xray state changes.
"""
import asyncio
import copy
import importlib.util
import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

import test_user_device_limit as bootstrap
from alembic.migration import MigrationContext
from alembic.operations import Operations
from fastapi import FastAPI, HTTPException, Response
from pydantic import ValidationError
from sqlalchemy import create_engine, func, select, text, update
from sqlalchemy.orm import sessionmaker

from app.db import crud
from app.db.base import Base
from app.db.models import (Admin as DBAdmin, NextPlan, NodeUserUsage, Proxy, System,
                           User, UserUsageRecovery, UserUsageResetLogs)
from app.db import usage_continuity as service
from app.db.usage_accounting import UsageHistoryProtectedError, lock_user_usage
from app.models.admin import Admin
from app.models.user import UserResponse, UserStatus
from app.models.usage_continuity import RepairRequest
from app.routers import usage_continuity as routes
from app.routers.subscription import get_subscription_user_info

ROOT = Path(__file__).resolve().parents[1]


class ContinuityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="usage-continuity-")
        self.addCleanup(self.temp.cleanup)
        self.engine = create_engine("sqlite:///" + str(Path(self.temp.name) / "ledger.db"),
                                    connect_args={"check_same_thread": False, "timeout": 15})
        self.addCleanup(self.engine.dispose)
        with self.engine.begin() as conn:
            conn.exec_driver_sql("PRAGMA journal_mode=WAL")
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine, autoflush=False)
        self.db = self.sessions()
        self.addCleanup(self.db.close)
        self.now = datetime.utcnow().replace(microsecond=0)
        self.admin = DBAdmin(username="operator", hashed_password="unused", users_usage=1234)
        self.system = System(uplink=50, downlink=70)
        self.db.add_all([self.admin, self.system])
        self.db.commit()
        self.user = self.make_user("example_user")

    def make_user(self, name):
        created = self.now - timedelta(days=31)
        user = User(username=name, status="active", data_limit=10000, used_traffic=100,
                    expire=int((self.now + timedelta(days=15)).replace(tzinfo=timezone.utc).timestamp()),
                    created_at=created, data_limit_reset_strategy="month", admin_id=self.admin.id,
                    device_limit=0, device_limit_action="reject_new", device_limit_mode="hwid")
        user.usage_logs = [UserUsageResetLogs(used_traffic_at_reset=0, reset_at=created),
                           UserUsageResetLogs(used_traffic_at_reset=6000, reset_at=created + timedelta(days=30))]
        user.proxies = [Proxy(type="vless", settings={"id": str(uuid4()), "flow": ""})]
        user.node_usages = [NodeUserUsage(used_traffic=100, created_at=self.now)]
        self.db.add(user)
        self.db.commit()
        return user

    def request_body(self, user=None):
        name = (user or self.user).username
        return {"operation_id": str(uuid4()), "reason": "restore_single_monthly_reset",
                "evidence_sha256": "d" * 64, "expected": service.preview(self.db, name)["expected"]}

    def apply(self, body, username="example_user", db=None):
        return service.apply(db or self.db, username, RepairRequest.model_validate(body), "operator")

    def latest_user(self):
        self.db.rollback()
        return self.db.query(User).filter_by(username="example_user").one()

    def http(self, method, path, body=None, admin=True, headers=None):
        app = FastAPI()
        app.include_router(routes.router)
        app.dependency_overrides[routes.get_db] = lambda: self.db
        if admin is True:
            app.dependency_overrides[Admin.check_sudo_admin] = lambda: Admin(username="operator", is_sudo=True)
        data = json.dumps(body).encode() if body is not None else b""
        messages = []
        scope = {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "method": method,
                 "scheme": "https", "path": path, "raw_path": path.encode(), "query_string": b"", "root_path": "",
                 "server": ("test.local", 443), "client": ("198.51.100.1", 1234),
                 "headers": [(b"content-type", b"application/json")] + (headers or [])}
        async def receive():
            return {"type": "http.request", "body": data, "more_body": False}
        async def send(message):
            messages.append(message)
        asyncio.run(app(scope, receive, send))
        start = next(item for item in messages if item["type"] == "http.response.start")
        return start["status"], json.loads(b"".join(item.get("body", b"") for item in messages)), dict(start["headers"])

    def test_preview_is_read_only_complete_and_no_credentials(self):
        self.user.proxies.append(Proxy(type="vless", settings={"id": "private-placeholder", "flow": ""}))
        self.db.commit()
        result = service.preview(self.db, self.user.username)
        self.assertTrue(result["eligible"])
        self.assertTrue(result["history_complete"])
        self.assertEqual(result["reset_origin"], "unrecorded")
        self.assertEqual(result["expected"]["history_count"], 2)
        self.assertEqual(result["expected"]["history_sha256"], service.digest(result["history"]))
        self.assertNotIn("private-placeholder", json.dumps(result))
        self.assertEqual(self.db.query(UserUsageRecovery).count(), 0)
        self.assertEqual(self.latest_user().used_traffic, 100)

    def test_apply_restores_current_not_lifetime_preserves_all_other_fields(self):
        body = self.request_body()
        initial = self.latest_user()
        saved = {column.name: getattr(initial, column.name) for column in User.__table__.columns if column.name != "used_traffic"}
        history = [(log.id, log.used_traffic_at_reset, log.reset_at) for log in initial.usage_logs]
        result = self.apply(body)
        user = self.latest_user()
        self.assertEqual((user.used_traffic, user.lifetime_used_traffic, user.reseted_usage), (6100, 6100, 0))
        self.assertEqual(self.db.query(User.reseted_usage).filter(User.id == user.id).scalar(), 0)
        self.assertEqual({key: getattr(user, key) for key in saved}, saved)
        self.assertEqual([(log.id, log.used_traffic_at_reset, log.reset_at) for log in user.usage_logs], history)
        self.assertEqual(self.db.query(DBAdmin).one().users_usage, 1234)
        self.assertEqual(self.db.query(System).one().uplink, 50)
        self.assertEqual(self.db.query(NodeUserUsage).one().used_traffic, 100)
        self.assertEqual(result["used_traffic_after"], "6100")
        self.assertEqual(result["lifetime_used_traffic_after"], result["lifetime_used_traffic_before"])

    def test_user_api_and_subscription_keep_original_quota_and_correct_download(self):
        self.apply(self.request_body())
        with patch("app.models.user.create_subscription_token", return_value="local-test-only"):
            user = UserResponse.model_validate(self.latest_user())
        self.assertEqual((user.used_traffic, user.lifetime_used_traffic, user.data_limit), (6100, 6100, 10000))
        info = get_subscription_user_info(user)
        self.assertEqual((info["download"], info["total"]), (6100, 10000))

    def test_concurrent_increase_since_preview_is_added_not_overwritten(self):
        body = self.request_body()
        with self.sessions.begin() as db:
            db.execute(update(User).values(used_traffic=User.used_traffic + 25))
        result = self.apply(body)
        self.assertEqual((result["used_traffic_before"], result["used_traffic_after"]), ("125", "6125"))

    def test_idempotent_receipt_survives_later_usage_reset_and_deleted_user(self):
        body = self.request_body()
        result = self.apply(body)
        self.assertEqual(self.apply(body), result)
        user = self.latest_user()
        crud.reset_user_data_usage(self.db, user)
        self.assertEqual(self.apply(body), result)
        crud.remove_user(self.db, self.latest_user())
        self.assertEqual(self.apply(body), result)
        self.assertEqual(service.receipt(self.db, body["operation_id"]), result)
        replacement = self.make_user("replacement")
        self.assertEqual(replacement.lifetime_used_traffic, 6100)

    def test_same_uuid_changed_payload_or_path_is_rejected(self):
        body = self.request_body()
        self.apply(body)
        changed = copy.deepcopy(body)
        changed["evidence_sha256"] = "e" * 64
        for candidate, name in ((changed, "example_user"), (body, "different")):
            with self.assertRaises(service.RecoveryError) as caught:
                self.apply(candidate, name)
            self.assertEqual(caught.exception.detail["code"], "operation_payload_mismatch")
        self.assertEqual(self.latest_user().used_traffic, 6100)

    def test_different_uuid_cannot_recover_same_target_twice(self):
        body = self.request_body()
        self.apply(body)
        body["operation_id"] = str(uuid4())
        with self.assertRaises(service.RecoveryError):
            self.apply(body)
        self.assertEqual(self.db.query(UserUsageRecovery).count(), 1)

    def test_reject_ineligible_account_states_and_limits(self):
        cases = [dict(status=status) for status in ("limited", "expired", "disabled", "on_hold")]
        cases += [dict(expire=1), dict(expire=None), dict(data_limit=None), dict(data_limit=0),
                  dict(data_limit=6100), dict(data_limit=6000), dict(data_limit_reset_strategy="no_reset"),
                  dict(data_limit_reset_strategy="day"), dict(data_limit_reset_strategy="year")]
        for index, changes in enumerate(cases):
            with self.subTest(changes=changes):
                user = self.make_user(f"invalid_{index}")
                name = user.username
                for key, value in changes.items():
                    setattr(user, key, value)
                self.db.commit()
                body = self.request_body(user)
                with self.assertRaises(service.RecoveryError) as caught:
                    self.apply(body, name)
                self.assertEqual(caught.exception.detail["code"], "ineligible")
        self.assertEqual(self.db.query(UserUsageRecovery).count(), 0)

    def test_reject_pending_plan_without_deleting_it(self):
        body = self.request_body()
        self.user.next_plan = NextPlan(data_limit=20000, expire=None)
        self.db.commit()
        with self.assertRaises(service.RecoveryError):
            self.apply(body)
        self.assertEqual(self.db.query(NextPlan).count(), 1)
        self.assertEqual(self.latest_user().used_traffic, 100)

    def test_snapshot_changes_fail_closed(self):
        changes = [dict(data_limit=20000), dict(expire=int((self.now + timedelta(days=20)).replace(tzinfo=timezone.utc).timestamp())),
                   dict(created_at=self.now - timedelta(days=32)), dict(device_limit=2),
                   dict(device_limit_action="log_only"), dict(note="edited")]
        for index, values in enumerate(changes):
            user = self.make_user(f"changed_{index}")
            name = user.username
            body = self.request_body(user)
            for key, value in values.items():
                setattr(user, key, value)
            self.db.commit()
            with self.subTest(values=values), self.assertRaises(service.RecoveryError):
                self.apply(body, name)

    def test_changed_proxy_identity_and_wrong_account_are_rejected(self):
        body = self.request_body()
        self.user.proxies.append(Proxy(type="vless", settings={"id": "changed-credential"}))
        self.db.commit()
        with self.assertRaises(service.RecoveryError):
            self.apply(body)
        other = self.make_user("other")
        with self.assertRaises(service.RecoveryError):
            self.apply(body, other.username)

    def test_reset_history_shape_and_latest_reset_change_rejected(self):
        body = self.request_body()
        self.user.usage_logs.append(UserUsageResetLogs(used_traffic_at_reset=0, reset_at=self.now))
        self.db.commit()
        with self.assertRaises(service.RecoveryError):
            self.apply(body)
        self.assertEqual(self.db.query(UserUsageResetLogs).count(), 3)

    def test_due_next_reset_and_noninitial_zero_log_rejected(self):
        for index, delta in enumerate((timedelta(days=31), timedelta(minutes=-10))):
            user = self.make_user(f"bad_history_{index}")
            name = user.username
            if index == 0:
                user.created_at -= delta
                for log in user.usage_logs:
                    log.reset_at -= delta
            else:
                user.usage_logs[0].reset_at -= delta
            self.db.commit()
            body = self.request_body(user)
            with self.assertRaises(service.RecoveryError):
                self.apply(body, name)

    def test_observed_counter_and_lifetime_inconsistency_rejected(self):
        for raw, lifetime in (("101", "6101"), ("100", "6200")):
            body = self.request_body()
            body["expected"]["observed_used_traffic"] = raw
            body["expected"]["observed_lifetime_used_traffic"] = lifetime
            with self.assertRaises(service.RecoveryError) as caught:
                self.apply(body)
            self.assertEqual(caught.exception.detail["code"], "observed_counter_changed")

    def test_counter_can_reach_quota_after_preview_and_is_rejected(self):
        body = self.request_body()
        with self.sessions.begin() as db:
            db.execute(update(User).values(used_traffic=4000))
        with self.assertRaises(service.RecoveryError):
            self.apply(body)
        self.assertEqual(self.latest_user().used_traffic, 4000)

    def test_exact_large_integer_accounting(self):
        big = 9007199254740993
        self.user.data_limit = 2**63 - 1
        self.user.usage_logs[-1].used_traffic_at_reset = big
        self.db.commit()
        result = self.apply(self.request_body())
        self.assertEqual(result["used_traffic_after"], str(big + 100))
        self.assertEqual(self.latest_user().lifetime_used_traffic, big + 100)

    def test_commit_failure_rolls_back_counter_and_receipt(self):
        body = self.request_body()
        with patch.object(self.db, "commit", side_effect=RuntimeError("test commit failure")):
            with self.assertRaisesRegex(RuntimeError, "test commit"):
                self.apply(body)
        with self.sessions() as db:
            self.assertEqual(db.query(User).one().used_traffic, 100)
            self.assertEqual(db.query(UserUsageRecovery).count(), 0)
        self.assertEqual(self.apply(body)["used_traffic_after"], "6100")

    def test_future_ordinary_resets_preserve_lifetime_python_sql_and_anchor(self):
        self.apply(self.request_body())
        user = self.latest_user()
        original = user.last_traffic_reset_time
        for increment in (13, 29):
            self.db.execute(update(User).where(User.id == user.id).values(used_traffic=User.used_traffic + increment))
            self.db.commit()
            lifetime = user.lifetime_used_traffic
            crud.reset_user_data_usage(self.db, user)
            self.assertEqual(user.used_traffic, 0)
            self.assertEqual(user.lifetime_used_traffic, lifetime)
            self.assertEqual(self.db.query(User.reseted_usage).scalar(), lifetime)
            self.assertGreater(user.last_traffic_reset_time, original)
        self.assertEqual(self.db.query(UserUsageRecovery).count(), 1)
        self.assertEqual(self.db.query(UserUsageResetLogs).count(), 4)

    def test_scheduled_reset_uses_preserved_anchor_and_rechecks_under_lock(self):
        body = self.request_body()
        anchor = self.user.last_traffic_reset_time
        self.apply(body)
        user = self.latest_user()
        self.assertEqual(user.last_traffic_reset_time, anchor)
        self.assertIsNone(crud.reset_user_data_usage(self.db, user, due_at=anchor + timedelta(days=29)))
        due = anchor + timedelta(days=30)
        self.assertIsNotNone(crud.reset_user_data_usage(self.db, user, due_at=due))
        self.assertEqual(user.lifetime_used_traffic, 6100)
        self.assertIsNone(crud.reset_user_data_usage(self.db, user, due_at=due))

    def test_future_next_plan_reset_preserves_recovered_lifetime(self):
        self.apply(self.request_body())
        user = self.latest_user()
        user.next_plan = NextPlan(data_limit=20000, expire=user.expire, add_remaining_traffic=True)
        self.db.commit()
        crud.reset_user_by_next(self.db, user)
        self.assertEqual((user.used_traffic, user.lifetime_used_traffic), (0, 6100))
        self.assertIsNone(user.next_plan)

    def test_full_history_clear_is_transactionally_rejected_for_repaired_users(self):
        self.make_user("untouched")
        self.apply(self.request_body())
        with self.assertRaises(UsageHistoryProtectedError):
            crud.reset_all_users_data_usage(self.db)
        self.assertEqual(sorted(row.used_traffic for row in self.db.query(User)), [100, 6100])
        self.assertEqual(self.db.query(UserUsageResetLogs).count(), 4)

    def test_normal_reset_does_not_reactivate_disabled_or_expired(self):
        for status in ("disabled", "expired"):
            user = self.make_user("reset_" + status)
            user.status = status
            self.db.commit()
            crud.reset_user_data_usage(self.db, user)
            self.assertEqual(user.status, status)

    def test_empty_history_sql_expression_matches_python(self):
        user = User(username="fresh", used_traffic=7)
        self.db.add(user)
        self.db.commit()
        self.assertEqual(user.reseted_usage, 0)
        self.assertEqual(self.db.query(User.reseted_usage).filter(User.id == user.id).scalar(), 0)
        self.assertEqual(user.lifetime_used_traffic, 7)

    def test_real_concurrent_increments_and_apply_do_not_lose_or_duplicate_bytes(self):
        body = self.request_body()
        barrier = threading.Barrier(4)
        def collect():
            barrier.wait()
            for _ in range(20):
                with self.sessions.begin() as db:
                    db.execute(update(User).where(User.username == "example_user").values(used_traffic=User.used_traffic + 1))
        def repair():
            barrier.wait()
            with self.sessions() as db:
                return self.apply(body, db=db)
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(collect) for _ in range(3)] + [pool.submit(repair)]
            for future in futures:
                future.result(timeout=30)
        self.assertEqual((self.latest_user().used_traffic, self.user.lifetime_used_traffic), (6160, 6160))
        self.assertEqual(self.db.query(UserUsageRecovery).count(), 1)

    def test_two_simultaneous_identical_requests_return_one_receipt(self):
        body = self.request_body()
        barrier = threading.Barrier(2)
        def repair():
            with self.sessions() as db:
                barrier.wait()
                return self.apply(body, db=db)
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(repair) for _ in range(2)]
            results = [future.result(timeout=30) for future in futures]
        self.assertEqual(results[0], results[1])
        self.assertEqual(self.latest_user().used_traffic, 6100)

    def test_stale_reset_session_refreshes_after_recovery(self):
        body = self.request_body()
        with self.sessions() as stale:
            user = stale.query(User).one()
            self.assertEqual(user.used_traffic, 100)
            self.apply(body)
            crud.reset_user_data_usage(stale, user)
            self.assertEqual((user.used_traffic, user.lifetime_used_traffic), (0, 6100))
            self.assertEqual(sorted(log.used_traffic_at_reset for log in user.usage_logs), [0, 6000, 6100])

    def test_reset_before_repair_rejects_old_expected(self):
        body = self.request_body()
        crud.reset_user_data_usage(self.db, self.latest_user())
        with self.assertRaises(service.RecoveryError):
            self.apply(body)
        self.assertEqual((self.latest_user().used_traffic, self.user.lifetime_used_traffic), (0, 6100))

    def test_receipt_route_unknown_and_complete_http_roundtrip(self):
        prefix = "/api/usage-continuity/v1"
        status, value, headers = self.http("GET", prefix + "/users/example_user/preview")
        self.assertEqual(status, 200)
        self.assertEqual(headers[b"cache-control"], b"no-store")
        body = self.request_body()
        status, receipt, _ = self.http("POST", prefix + "/users/example_user/repairs", body)
        self.assertEqual(status, 200)
        self.assertEqual(self.http("GET", prefix + "/repairs/" + body["operation_id"])[1], receipt)
        self.assertEqual(self.http("GET", prefix + "/repairs/" + str(uuid4()))[0], 404)
        self.assertEqual(self.http("GET", prefix + "/users/missing/preview")[0], 404)
        self.assertEqual(self.http("POST", prefix + "/users/example_user/repairs", body)[1], receipt)

    def test_all_routes_require_sudo_and_failures_do_not_write(self):
        body = self.request_body()
        prefix = "/api/usage-continuity/v1"
        paths = [("GET", prefix + "/users/example_user/preview", None),
                 ("POST", prefix + "/users/example_user/repairs", body),
                 ("GET", prefix + "/repairs/" + body["operation_id"], None)]
        for admin, expected in ((None, 401), (Admin(username="ordinary", is_sudo=False), 403)):
            with patch.object(Admin, "get_admin", return_value=admin):
                for method, path, request in paths:
                    self.assertEqual(self.http(method, path, request, False, [(b"authorization", b"Bearer test")])[0], expected)
        self.assertEqual(self.db.query(UserUsageRecovery).count(), 0)

    def test_contract_rejects_unknown_fields_numeric_bytes_and_uuid_variants(self):
        baseline = self.request_body()
        for path, value in (("operation_id", baseline["operation_id"].upper()), ("reason", "reset"),
                            ("evidence_sha256", "not-a-digest"), ("unknown", True)):
            body = copy.deepcopy(baseline)
            body[path] = value
            with self.subTest(path=path), self.assertRaises(ValidationError):
                RepairRequest.model_validate(body)
        for value in (100, True, "-1", "1.1", "0100", "1e3"):
            body = copy.deepcopy(baseline)
            body["expected"]["observed_used_traffic"] = value
            with self.assertRaises(ValidationError):
                RepairRequest.model_validate(body)
        body = copy.deepcopy(baseline)
        body["expected"]["unknown"] = True
        self.assertEqual(self.http("POST", "/api/usage-continuity/v1/users/example_user/repairs", body)[0], 422)

    def test_other_database_apply_and_preview_fail_closed(self):
        body = self.request_body()
        fake = SimpleNamespace(new=[], dirty=[], deleted=[], rollback=Mock(),
                               get_bind=lambda: SimpleNamespace(dialect=SimpleNamespace(name="postgresql")))
        for call in (lambda: service.preview(fake, "example_user"),
                     lambda: self.apply(body, db=fake)):
            with self.assertRaises(service.RecoveryError) as caught:
                call()
            self.assertEqual(caught.exception.status, 503)

    def test_receipt_fingerprint_matches_published_contract(self):
        body = self.request_body()
        self.assertEqual(self.apply(body)["payload_sha256"], service.digest({"username": "example_user", "request": body}))
        contract = json.loads((ROOT / "docs/contracts/usage-continuity-v1.json").read_text(encoding="utf-8"))
        preview = service.preview(self.db, "example_user")
        self.assertEqual(set(preview), set(contract["preview_example"]))
        result = service.receipt(self.db, body["operation_id"])
        self.assertEqual(set(result), set(contract["receipt_example"]))

    def test_sql_total_and_list_sort_remain_consistent(self):
        self.make_user("other")
        self.apply(self.request_body())
        total = self.db.query(func.sum(User.used_traffic + User.reseted_usage)).scalar()
        self.assertEqual(total, 12200)
        users = crud.get_users(self.db, sort=[crud.UsersSortingOptions['-used_traffic']])
        self.assertEqual([user.username for user in users], ["example_user", "other"])
        self.assertEqual([user.lifetime_used_traffic for user in users], [6100, 6100])

    def test_recovery_has_no_xray_side_effects_and_normal_quota_review_still_limits(self):
        from app import scheduler, xray
        spec = importlib.util.spec_from_file_location("isolated_recovery_review", ROOT / "app/jobs/review_users.py")
        reviewer = importlib.util.module_from_spec(spec)
        with patch.object(scheduler, "add_job"):
            spec.loader.exec_module(reviewer)
        with patch.object(xray.operations, "add_user") as add, \
             patch.object(xray.operations, "remove_user") as remove, \
             patch.object(xray.operations, "update_user") as alter:
            self.apply(self.request_body())
            add.assert_not_called()
            remove.assert_not_called()
            alter.assert_not_called()
        with self.sessions.begin() as db:
            db.execute(update(User).values(used_traffic=User.used_traffic + 3900))
        with patch("app.db.SessionLocal", self.sessions), patch.object(reviewer, "xray") as runtime, \
             patch.object(reviewer, "report"), patch("app.models.user.create_subscription_token", return_value="test"):
            reviewer.review()
            runtime.operations.remove_user.assert_called_once()
        self.assertEqual(self.latest_user().status, UserStatus.limited)
        self.assertEqual((self.user.used_traffic, self.user.lifetime_used_traffic, self.user.data_limit), (10000, 10000, 10000))

    def test_two_different_operations_race_only_one_can_apply(self):
        first = self.request_body()
        second = copy.deepcopy(first)
        second['operation_id'] = str(uuid4())
        barrier = threading.Barrier(2)
        def repair(body):
            with self.sessions() as db:
                barrier.wait()
                try:
                    return self.apply(body, db=db)['status']
                except service.RecoveryError as exc:
                    return exc.detail['code']
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(repair, body) for body in (first, second)]
            results = [future.result(timeout=30) for future in futures]
        self.assertEqual(sorted(results), ['applied', 'ineligible'])
        self.assertEqual(self.latest_user().used_traffic, 6100)

    def test_database_lock_error_is_503_and_does_not_modify_ledger(self):
        body = self.request_body()
        short_engine = create_engine(self.engine.url, connect_args={'timeout': 0.02})
        try:
            with self.engine.connect() as blocker, sessionmaker(bind=short_engine)() as blocked:
                blocker.exec_driver_sql('BEGIN IMMEDIATE')
                with self.assertRaises(HTTPException) as caught:
                    routes._call(Response(), service.apply, blocked, 'example_user', RepairRequest.model_validate(body), 'test')
                self.assertEqual(caught.exception.status_code, 503)
                self.assertEqual(caught.exception.detail, {'code': 'database_busy'})
                blocker.rollback()
        finally:
            short_engine.dispose()
        self.assertEqual(self.latest_user().used_traffic, 100)
        self.assertEqual(self.db.query(UserUsageRecovery).count(), 0)

    def test_reset_uses_newly_collected_bytes_instead_of_stale_orm_counter(self):
        with self.sessions() as stale:
            user = stale.query(User).one()
            self.assertEqual(user.used_traffic, 100)
            with self.sessions.begin() as db:
                db.execute(update(User).values(used_traffic=User.used_traffic + 17))
            crud.reset_user_data_usage(stale, user)
            self.assertEqual(user.lifetime_used_traffic, 6117)
            self.assertEqual(max(user.usage_logs, key=lambda log: log.reset_at).used_traffic_at_reset, 117)

    def test_reset_writer_lock_serializes_an_inflight_repair(self):
        body = self.request_body()
        with self.sessions() as reset_db:
            user = reset_db.query(User).one()
            lock_user_usage(reset_db, user)
            with ThreadPoolExecutor(max_workers=1) as pool:
                entered = threading.Event()
                def repair():
                    with self.sessions() as db:
                        entered.set()
                        try:
                            return self.apply(body, db=db)['status']
                        except service.RecoveryError as exc:
                            return exc.detail['code']
                pending = pool.submit(repair)
                self.assertTrue(entered.wait(5))
                crud.reset_user_data_usage(reset_db, user)
                self.assertEqual(pending.result(timeout=30), 'ineligible')
        self.assertEqual(self.latest_user().lifetime_used_traffic, 6100)
        self.assertEqual(self.db.query(UserUsageRecovery).count(), 0)

    def test_reset_history_changed_in_place_is_detected(self):
        for key, value in (('used_traffic_at_reset', 6001), ('reset_at', self.now - timedelta(hours=12))):
            user = self.make_user('tampered_' + key[:10])
            name = user.username
            body = self.request_body(user)
            setattr(user.usage_logs[-1], key, value)
            self.db.commit()
            with self.assertRaises(service.RecoveryError):
                self.apply(body, name)

    def test_full_history_clear_for_other_owner_does_not_touch_recovery(self):
        self.apply(self.request_body())
        other_admin = DBAdmin(username='separate_owner', hashed_password='unused')
        self.db.add(other_admin)
        self.db.commit()
        other = self.make_user('other')
        other.admin_id = other_admin.id
        self.db.commit()
        crud.reset_all_users_data_usage(self.db, other_admin)
        self.assertEqual(self.latest_user().used_traffic, 6100)
        self.assertEqual(self.db.query(User).filter_by(username='other').one().used_traffic, 0)
        self.assertEqual(self.db.query(UserUsageRecovery).count(), 1)


class ContinuityMigrationTests(unittest.TestCase):
    def test_additive_migration_and_guarded_downgrade(self):
        spec = importlib.util.spec_from_file_location("usage_recovery_migration", ROOT / "app/db/migrations/versions/c345de67fa89_usage_continuity.py")
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)
        self.assertEqual(migration.down_revision, "b234cd56ef78")
        engine = create_engine("sqlite:///:memory:")
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, used_traffic BIGINT)"))
            conn.execute(text("INSERT INTO users VALUES (1, 123)"))
            with patch.object(migration, "op", Operations(MigrationContext.configure(conn))):
                migration.upgrade()
                self.assertEqual(conn.execute(text("SELECT * FROM users")).one(), (1, 123))
                migration.downgrade()
                migration.upgrade()
                conn.execute(text("INSERT INTO user_usage_recoveries VALUES ('example',1,'example_user','2026-01-01',2,100,'digest','{}')"))
                with self.assertRaisesRegex(RuntimeError, "Applied usage recoveries"):
                    migration.downgrade()
                self.assertEqual(conn.execute(text("SELECT count(*) FROM user_usage_recoveries")).scalar(), 1)
        engine.dispose()
