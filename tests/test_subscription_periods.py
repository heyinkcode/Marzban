import asyncio
import importlib.util
import json
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Barrier
from unittest.mock import patch
from uuid import uuid4

from fastapi import FastAPI

import test_usage_continuity as fixtures
from app import scheduler
from app.db import crud, user_entitlement as service
from app.db.models import NextPlan, User, UserSubscriptionPeriod, UserUsageResetLogs
from app.db.usage_continuity import RecoveryError
from app.models.admin import Admin
from app.models.user import UserModify
from app.models.user_entitlement import EntitlementApply, EntitlementCommand, SubscriptionPeriodCommand
from app.routers import user_entitlement as routes


class WebsitePeriodTests(unittest.TestCase):
    setUp = fixtures.ContinuityTests.setUp
    make_user = fixtures.ContinuityTests.make_user
    latest_user = fixtures.ContinuityTests.latest_user
    sudo = Admin(username="operator", is_sudo=True)
    ordinary = Admin(username="operator", is_sudo=False)

    def at_day(self, days):
        return int((self.now + timedelta(days=days)).replace(tzinfo=timezone.utc).timestamp())

    def period_request(self, action, days_now=0, *, confirmed=True, admin=None, **fields):
        command = SubscriptionPeriodCommand(action=action, **fields)
        with patch.object(service, "_now", return_value=self.now + timedelta(days=days_now)):
            preview = service.preview(self.db, "example_user", command, admin or self.sudo)
        return preview, EntitlementApply(operation_id=str(uuid4()), guard=preview["guard"],
                                         command=command, confirmed=confirmed)

    def apply(self, request, *, days_now=0, admin=None, db=None):
        with patch.object(service, "_now", return_value=self.now + timedelta(days=days_now)):
            return service.apply(db or self.db, "example_user", request, admin or self.sudo)

    def attach(self):
        token = str(uuid4())
        _, body = self.period_request("attach_period", period_id=token, starts_at=self.at_day(-15))
        return token, self.apply(body)

    def test_compensation_this_period_next_is_30_days_and_keeps_lifetime(self):
        lifetime = self.user.lifetime_used_traffic
        period_id, attach = self.attach()
        self.assertEqual(attach["before"]["used_bytes"], "100")
        self.assertEqual(attach["after"]["used_bytes"], "100")
        self.assertEqual(attach["after"]["expires_at"], self.at_day(15))
        self.assertEqual(attach["after"]["subscription_period"]["mode"], "monthly")
        preview, request = self.period_request("adjust_period", period_id=period_id,
                                               expires_at=self.at_day(22), extra_bytes="200")
        self.assertEqual(preview["after"]["subscription_period"]["mode"], "manual")
        self.assertEqual(self.db.get(User, self.user.id).data_limit, 10000)
        adjusted = self.apply(request)
        self.assertEqual(self.apply(request), adjusted)
        self.assertEqual(adjusted["after"]["used_bytes"], "100")
        self.assertEqual(adjusted["after"]["quota_bytes"], "10200")
        self.assertEqual(adjusted["after"]["expires_at"], self.at_day(22))
        self.assertEqual(adjusted["after"]["subscription_period"]["added_bytes"], "200")

        # Crossing the original boundary (or even the compensated one) never opens a period.
        for day in (15, 22, 23):
            self.assertIsNone(crud.reset_user_data_usage(self.db, self.latest_user(),
                              due_at=self.now + timedelta(days=day)))
            self.assertEqual(self.latest_user().used_traffic, 100)
        self.assertEqual(self.latest_user().lifetime_used_traffic, lifetime)
        next_id = str(uuid4())
        with self.assertRaisesRegex(RecoveryError, "subscription_period_start_invalid"):
            self.period_request("open_period", days_now=21, period_id=next_id,
                                starts_at=self.at_day(22), quota_bytes="10000")
        _, opening = self.period_request("open_period", days_now=22, period_id=next_id,
                                         starts_at=self.at_day(22), quota_bytes="10000")
        with self.assertRaisesRegex(RecoveryError, "explicit_confirmation_required"):
            self.apply(opening.model_copy(update={"confirmed": False}), days_now=22)
        opened = self.apply(opening, days_now=22)
        self.assertEqual(self.apply(opening, days_now=23), opened)
        self.assertEqual(opened["after"]["used_bytes"], "0")
        self.assertEqual(opened["after"]["quota_bytes"], "10000")
        self.assertEqual(opened["after"]["expires_at"], self.at_day(52))
        self.assertEqual(opened["after"]["subscription_period"]["default_ends_at"], self.at_day(52))
        self.assertEqual(opened["after"]["subscription_period"]["mode"], "monthly")
        self.assertEqual(opened["after"]["subscription_period"]["added_bytes"], "0")
        self.assertEqual(self.latest_user().lifetime_used_traffic, lifetime)
        self.assertEqual(self.db.query(UserUsageResetLogs).count(), 3)
        self.assertEqual(service.get_overview(self.db, "example_user", self.sudo)["latest_reset"]["origin"],
                         "native_renewal")
        with self.assertRaisesRegex(RecoveryError, "subscription_period_changed"):
            self.period_request("adjust_period", days_now=22, period_id=period_id, extra_bytes="200")
        with self.assertRaisesRegex(RecoveryError, "subscription_period_id_used"):
            self.period_request("open_period", days_now=52, period_id=period_id,
                                starts_at=self.at_day(52), quota_bytes="10000")

    def test_topup_only_preserves_deadline_and_usage(self):
        current, _ = self.attach()
        _, add = self.period_request("adjust_period", period_id=current, extra_bytes="10")
        out = self.apply(add)
        self.assertEqual((out["after"]["used_bytes"], out["after"]["quota_bytes"], out["after"]["expires_at"]),
                         ("100", "10010", self.at_day(15)))
        self.assertEqual(out["after"]["subscription_period"]["mode"], "manual")

    def test_legacy_retry_hash_and_unmanaged_policy_are_unchanged(self):
        command = EntitlementCommand(action="add", extra_bytes="10")
        preview = service.preview(self.db, "example_user", command, self.ordinary)
        raw = {"operation_id":str(uuid4()), "guard":preview["guard"],
               "command":{"action":"add", "extra_bytes":"10"},"confirmed":False}
        # Published clients and existing receipts serialize exactly the legacy optional keys.
        expected = {"action":"add", "expires_at":None, "extra_bytes":"10", "reset_id":None, "reason":None}
        request = EntitlementApply.model_validate(raw)
        self.assertEqual(request.model_dump(mode="json")["command"], expected)
        self.assertEqual(self.apply(request, admin=self.ordinary)["after"]["reset_strategy"], "month")
        self.assertIsNone(service.get_overview(self.db, "example_user", self.sudo)["state"].get("subscription_period"))

    def test_sudo_only_and_no_legacy_write_bypass(self):
        with self.assertRaisesRegex(RecoveryError, "permission_denied") as err:
            self.period_request("attach_period", admin=self.ordinary,
                                period_id=str(uuid4()), starts_at=self.at_day(-15))
        self.assertEqual(err.exception.status, 403)
        period_id, _ = self.attach()
        _, write = self.period_request("adjust_period", period_id=period_id, extra_bytes="500")
        with self.assertRaisesRegex(RecoveryError, "permission_denied"):
            self.apply(write, admin=self.ordinary)
        for legacy in (EntitlementCommand(action="extend", expires_at=self.at_day(25)),
                       EntitlementCommand(action="add", extra_bytes="500"), EntitlementCommand(action="renew")):
            with self.assertRaisesRegex(RecoveryError, "subscription_period_action_required"):
                service.preview(self.db, "example_user", legacy, self.sudo)
        for changes in ({"expire":self.at_day(25)}, {"data_limit":10001}, {"data_limit_reset_strategy":"month"},
                        {"status":"on_hold", "on_hold_expire_duration":86400},
                        {"next_plan":{"data_limit":12345,"expire":self.at_day(40)}}):
            with self.assertRaisesRegex(RecoveryError, "subscription_period_action_required"):
                crud.update_user(self.db, self.latest_user(), UserModify(**changes))
        crud.update_user(self.db, self.latest_user(), UserModify(note="Synthetic", expire=self.at_day(15),
                         data_limit=10000, data_limit_reset_strategy="no_reset"))
        self.assertEqual(self.latest_user().note, "Synthetic")
        self.assertIsNone(crud.reset_user_data_usage(self.db, self.latest_user()))
        with self.assertRaisesRegex(crud.UsageHistoryProtectedError, "managed_subscription_history_protected"):
            crud.reset_all_users_data_usage(self.db, self.admin)
        self.assertEqual(self.latest_user().used_traffic, 100)

    def test_existing_next_plan_never_discarded_and_no_future_activation(self):
        user = self.latest_user()
        user.next_plan = NextPlan(data_limit=10000, expire=self.at_day(30))
        self.db.commit()
        with self.assertRaisesRegex(RecoveryError, "next_plan_conflict"):
            self.period_request("attach_period", period_id=str(uuid4()), starts_at=self.at_day(-15))
        self.assertIsNotNone(self.latest_user().next_plan)
        self.assertEqual(self.db.query(UserSubscriptionPeriod).count(), 0)

    def test_stale_expiry_review_cannot_mark_opened_period_expired(self):
        self.attach()
        _, opening = self.period_request("open_period", days_now=15, period_id=str(uuid4()),
                                         starts_at=self.at_day(15), quota_bytes="10000")
        with self.sessions() as reviewer:
            stale = reviewer.query(User).filter_by(username="example_user").one()
            self.assertEqual(stale.expire, self.at_day(15))
            self.apply(opening, days_now=15)
            self.assertIsNone(crud.mark_active_user_due(reviewer, stale, self.at_day(15)))
        self.assertEqual(self.latest_user().status, "active")
        self.assertEqual(self.latest_user().expire, self.at_day(45))

    def test_hourly_reset_ignores_changed_strategy_and_still_resets_unmanaged_user(self):
        self.attach()
        ordinary = self.make_user("unmanaged_user")
        managed_id = self.user.id
        ordinary_id = ordinary.id
        self.db.rollback()
        later = self.now + timedelta(days=31)

        class Clock(datetime):
            @classmethod
            def utcnow(cls):
                return later

        script = Path(__file__).resolve().parents[1] / "app/jobs/reset_user_data_usage.py"
        spec = importlib.util.spec_from_file_location("scheduled_subscription_test", script)
        job = importlib.util.module_from_spec(spec)
        with patch.object(scheduler, "add_job"):
            spec.loader.exec_module(job)
        with patch.object(job, "GetDB", self.sessions), patch.object(job, "datetime", Clock):
            # Simulate a refreshed managed user still in a previously selected batch.
            with patch.object(job, "get_users", side_effect=lambda db, **_: [
                    db.get(User, managed_id), db.get(User, ordinary_id)]):
                job.reset_user_data_usage()
        self.assertEqual(self.latest_user().used_traffic, 100)
        self.assertEqual(self.db.get(User, ordinary_id).used_traffic, 0)
        self.assertEqual(self.db.query(UserUsageResetLogs).count(), 5)

    def test_parallel_open_with_distinct_operations_writes_only_one_reset(self):
        self.attach()
        period_id = str(uuid4())
        preview, first = self.period_request("open_period", days_now=15, period_id=period_id,
                                            starts_at=self.at_day(15), quota_bytes="10000")
        second = first.model_copy(update={"operation_id": str(uuid4())})
        barrier = Barrier(2, timeout=10)

        def attempt(request):
            with self.sessions() as db:
                barrier.wait()
                try:
                    return service.apply(db, "example_user", request, self.sudo)
                except RecoveryError as error:
                    return error.detail["code"]

        with patch.object(service, "_now", return_value=self.now + timedelta(days=15)):
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(attempt, (first, second)))
        receipts = [result for result in results if isinstance(result, dict)]
        self.assertEqual(len(receipts), 1, results)
        self.assertIn("subscription_period_start_invalid", results)
        self.assertEqual(receipts[0]["after"], preview["after"])
        self.assertEqual(self.latest_user().used_traffic, 0)
        self.assertEqual(self.db.query(UserSubscriptionPeriod).count(), 2)
        self.assertEqual(self.db.query(UserUsageResetLogs).count(), 3)

    def test_subscription_credential_rotation_does_not_change_terms(self):
        for attach in (False, True):
            if attach:
                self.attach()
            before = service.get_overview(self.db, "example_user", self.sudo)["state"]
            user = self.latest_user()
            old_credential = user.proxies[0].settings["id"]
            rotated = crud.revoke_user_sub(self.db, user)
            self.assertIsNotNone(rotated.sub_revoked_at)
            self.assertNotEqual(rotated.proxies[0].settings["id"], old_credential)
            self.assertEqual(service.get_overview(self.db, "example_user", self.sudo)["state"], before)

    def test_client_input_does_not_allow_missing_id_or_wrong_fields(self):
        token = str(uuid4())
        for body in (
            {"action":"open_period", "period_id":token, "starts_at":self.at_day(0), "quota_bytes":"0"},
            {"action":"attach_period", "period_id":token, "starts_at":self.at_day(0), "extra_bytes":"1"},
            {"action":"adjust_period", "period_id":token},
            {"action":"adjust_period", "extra_bytes":"10"},
            {"action":"adjust_period", "period_id":token, "extra_bytes":-1},
        ):
            with self.assertRaises(ValueError):
                SubscriptionPeriodCommand.model_validate(body)

    def test_http_permissions_preview_receipts_and_replay_all_three_commands(self):
        app = FastAPI()
        app.include_router(routes.router)
        app.dependency_overrides[routes.get_db] = lambda: self.db

        def call(method, suffix="", body=None, token="sudo"):
            path = "/api/user/example_user/entitlement" + suffix
            headers = [(b"content-type", b"application/json")]
            if token:
                headers.append((b"authorization", f"Bearer {token}".encode()))
            messages = []

            async def receive():
                return {"type": "http.request", "body": json.dumps(body).encode() if body else b"", "more_body": False}

            async def send(message):
                messages.append(message)

            scope = {"type": "http", "method": method, "path": path, "raw_path": path.encode(),
                     "query_string": b"", "headers": headers, "http_version": "1.1", "scheme": "http"}
            asyncio.run(app(scope, receive, send))
            return messages[0]["status"], json.loads(b"".join(msg.get("body", b"") for msg in messages))

        def run(command, day, confirmed):
            with patch.object(service, "_now", return_value=self.now + timedelta(days=day)):
                self.assertEqual(call("POST", "/preview", command, "owner"),
                                 (403, {"detail": {"code": "permission_denied"}}))
                before = call("GET")[1]
                status, preview = call("POST", "/preview", command)
                self.assertEqual(status, 200, preview)
                self.assertEqual(call("GET")[1], before)
                operation = str(uuid4())
                body = {"operation_id": operation, "command": command, "guard": preview["guard"],
                        "confirmed": confirmed}
                self.assertEqual(call("POST", "/operations", body, "owner"),
                                 (403, {"detail": {"code": "permission_denied"}}))
                self.assertEqual(call("GET", "/operations/" + operation)[0], 404)
                status, receipt = call("POST", "/operations", body)
                self.assertEqual(status, 200, receipt)
                if command["action"] == "open_period":
                    # Traffic arriving after the reset must survive a retry.
                    self.latest_user().used_traffic = 99
                    self.db.commit()
                self.assertEqual(call("POST", "/operations", body), (200, receipt))
                self.assertEqual(call("GET", "/operations/" + operation), (200, receipt))
                return receipt

        first, second = str(uuid4()), str(uuid4())
        with patch.object(Admin, "get_admin", side_effect=lambda token, db: self.sudo if token == "sudo" else self.ordinary):
            self.assertEqual(call("GET", token=None)[0], 401)
            self.assertFalse(call("GET", token="owner")[1]["can_manage_subscription_period"])
            overview = call("GET")[1]
            self.assertTrue(overview["can_manage_subscription_period"])
            self.assertEqual(overview["subscription_period_capability"], "website-subscription-period-v1")
            run({"action": "attach_period", "period_id": first, "starts_at": self.at_day(-15)}, 0, True)
            adjusted = run({"action": "adjust_period", "period_id": first, "expires_at": self.at_day(22),
                            "extra_bytes": "200"}, 0, False)
            self.assertEqual(adjusted["after"]["used_bytes"], "100")
            opened = run({"action": "open_period", "period_id": second, "starts_at": self.at_day(22),
                          "quota_bytes": "10000"}, 22, True)
            self.assertEqual(opened["after"]["expires_at"], self.at_day(52))
            self.assertEqual(call("GET")[1]["state"]["used_bytes"], "99")
            self.assertEqual(self.db.query(UserUsageResetLogs).count(), 3)
