"""External expiry/policy contract: isolated SQLite, no live API or Xray calls."""
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from unittest.mock import patch

from fastapi import BackgroundTasks

import test_usage_continuity as fixture
from app.db import crud
from app.db.models import User, UserUsageResetLogs
from app.models.admin import Admin
from app.models.user import UserModify
from app.routers import user as routes


class ExternalResetControlTests(unittest.TestCase):
    setUp = fixture.ContinuityTests.setUp
    make_user = fixture.ContinuityTests.make_user

    def snapshot(self, user):
        return (user.used_traffic, user.lifetime_used_traffic, user.data_limit,
                user.expire, user.last_traffic_reset_time,
                [(p.type, dict(p.settings)) for p in user.proxies],
                [(n.node_id, n.used_traffic) for n in user.node_usages],
                [(r.id, r.reset_at, r.used_traffic_at_reset) for r in user.usage_logs])

    def put(self, body):
        # Exercise the real route and response validation; deliberately do not
        # run its background Xray/report tasks or claim HTTP/auth coverage.
        with patch("app.models.user.create_subscription_token", return_value="local-test-only"):
            return routes.modify_user(UserModify.model_validate(body), BackgroundTasks(),
                                      db=self.db, dbuser=self.user,
                                      admin=Admin(username="operator", is_sudo=True))

    def test_policy_only_route_preserves_usage_expiry_identity_and_history(self):
        before = self.snapshot(self.user)
        for _ in range(2):
            response = self.put({"data_limit_reset_strategy": "no_reset"})
            self.assertEqual(response.data_limit_reset_strategy, "no_reset")
            self.assertEqual(self.snapshot(self.user), before)

    def test_expiry_route_keeps_exact_timestamp_and_does_not_reset(self):
        before = self.snapshot(self.user)
        # Deliberately not the first day of a month; the API must not infer a cycle.
        expiry = 1894448467
        response = self.put({"expire": expiry, "data_limit_reset_strategy": "no_reset"})
        self.assertEqual(response.expire, expiry)
        after = self.snapshot(self.user)
        self.assertEqual(after[:3], before[:3])
        self.assertEqual(after[4:], before[4:])
        self.assertEqual(response.status, "active")

    def test_expired_timestamp_disables_without_zeroing_usage(self):
        before = self.user.used_traffic
        response = self.put({"expire": 1, "data_limit_reset_strategy": "no_reset"})
        self.assertEqual(response.expire, 1)
        self.assertEqual(response.status, "expired")
        self.assertEqual(self.user.used_traffic, before)
        self.assertEqual(len(self.user.usage_logs), 2)

    def test_no_reset_blocks_overdue_timer_but_not_explicit_authorized_reset(self):
        self.put({"data_limit_reset_strategy": "no_reset"})
        due = self.now + timedelta(days=400)
        self.assertIsNone(crud.reset_user_data_usage(self.db, self.user, due_at=due))
        self.assertEqual(self.user.used_traffic, 100)
        crud.reset_user_data_usage(self.db, self.user)
        self.assertEqual(self.user.used_traffic, 0)
        self.assertEqual(len(self.user.usage_logs), 3)

    def test_stale_timer_candidate_rechecks_committed_policy_under_lock(self):
        with self.sessions() as timer:
            stale = timer.query(User).filter_by(username=self.user.username).one()
            self.assertEqual(stale.data_limit_reset_strategy, "month")
            self.put({"data_limit_reset_strategy": "no_reset"})
            self.assertIsNone(crud.reset_user_data_usage(timer, stale,
                              due_at=self.now + timedelta(days=31)))
            self.assertEqual(stale.data_limit_reset_strategy, "no_reset")
            self.assertEqual(stale.used_traffic, 100)

    def test_timer_committed_before_handoff_is_not_silently_reversed(self):
        crud.reset_user_data_usage(self.db, self.user, due_at=self.now + timedelta(days=31))
        before = self.snapshot(self.user)
        self.put({"data_limit_reset_strategy": "no_reset"})
        self.assertEqual(self.snapshot(self.user), before)
        self.assertEqual(self.user.used_traffic, 0)
        self.assertEqual(len(self.user.usage_logs), 3)

    def test_independent_native_month_user_keeps_existing_behavior(self):
        other = self.make_user("native_user")
        self.put({"data_limit_reset_strategy": "no_reset"})
        self.assertIsNotNone(crud.reset_user_data_usage(self.db, other,
                             due_at=self.now + timedelta(days=31)))
        self.assertEqual(other.data_limit_reset_strategy, "month")
        self.assertEqual(other.used_traffic, 0)
        self.assertEqual(self.user.used_traffic, 100)

    def test_concurrent_policy_and_timer_serialize_and_future_timer_skips(self):
        username = self.user.username
        self.db.close()
        barrier = threading.Barrier(2)
        due = self.now + timedelta(days=31)

        def writer(policy):
            with self.sessions() as db:
                user = db.query(User).filter_by(username=username).one()
                barrier.wait(timeout=10)
                if policy:
                    crud.update_user(db, user, UserModify(data_limit_reset_strategy="no_reset"))
                else:
                    crud.reset_user_data_usage(db, user, due_at=due)

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(writer, p) for p in (True, False)]
            for future in futures:
                future.result(timeout=20)
        with self.sessions() as db:
            user = db.query(User).filter_by(username=username).one()
            self.assertEqual(user.data_limit_reset_strategy, "no_reset")
            logs = db.query(UserUsageResetLogs).filter_by(user_id=user.id).count()
            # Either commit order is valid; no_reset cannot undo an earlier reset.
            self.assertIn(logs, (2, 3))
            self.assertEqual(user.used_traffic, 100 if logs == 2 else 0)
            self.assertEqual(user.lifetime_used_traffic, 6100)
            self.assertIsNone(crud.reset_user_data_usage(db, user, due_at=due))
            self.assertEqual(len(user.usage_logs), logs)
