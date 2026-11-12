"""v2 first-reset contract: real isolated SQLite/transactions and ASGI routes."""
import copy
import hashlib
import json
import unittest
from datetime import timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from unittest.mock import patch
from uuid import uuid4

from pydantic import ValidationError

import test_usage_continuity as base
from app.db import usage_continuity as service
from app.db.models import UserUsageRecovery
from app.models.admin import Admin
from app.models.usage_continuity import RepairRequest
from app.models.usage_continuity_v2 import CAPABILITY, FirstPaidPeriodRepairRequest
from app.routers import usage_continuity_v2 as routes


class FirstPaidPeriodTests(unittest.TestCase):
    setUp = base.ContinuityTests.setUp
    latest_user = base.ContinuityTests.latest_user

    def make_user(self, name):
        user = base.ContinuityTests.make_user(self, name)
        self.db.delete(user.usage_logs[0])
        user.created_at = self.now - timedelta(days=30, hours=6)
        user.usage_logs[-1].reset_at = user.created_at + timedelta(days=30)
        user.expire = int((user.created_at + timedelta(days=31)).replace(tzinfo=timezone.utc).timestamp())
        self.db.commit()
        self.db.refresh(user)
        return user

    def request_body(self, user=None):
        user = user or self.user
        proof = {"starts_at": service.utc(user.created_at),
                 "ends_at": service.utc(user.created_at + timedelta(days=31)),
                 "last_observed_at": service.utc(user.usage_logs[0].reset_at - timedelta(minutes=1)),
                 "last_observed_used_traffic": "5990"}
        return {"operation_id": str(uuid4()), "reason": "restore_first_paid_period_reset",
                "evidence_sha256": "d" * 64, "paid_period_evidence": proof,
                "expected": service.preview_first_paid_period(self.db, user.username)["expected"]}

    def apply(self, body, username="example_user", db=None):
        return service.apply_first_paid_period(db or self.db, username,
                    FirstPaidPeriodRepairRequest.model_validate(body), "operator")

    def http(self, method, path, body=None, admin=True, headers=None):
        with patch.object(base, "routes", routes):
            return base.ContinuityTests.http(self, method, path.replace('/v1/', '/v2/'), body, admin, headers)

    def test_v1_still_rejects_single_history_and_v2_is_structural_only(self):
        self.assertEqual(service.preview(self.db, self.user.username)["blockers"], ["unsupported_history"])
        result = service.preview_first_paid_period(self.db, self.user.username)
        self.assertTrue(result["eligible"])
        self.assertEqual(result["capability"], CAPABILITY)
        self.assertTrue(result["requires_paid_period_evidence"])
        self.assertEqual(result["eligibility_scope"], "panel_state_only")
        self.assertEqual(len(result["history"]), 1)
        self.assertIsNone(result['expected']['initial_reset'])
        self.assertEqual(result['expected']['latest_reset'], result['history'][0])
        legacy = self.request_body()
        legacy.pop('paid_period_evidence')
        legacy['reason'] = 'restore_single_monthly_reset'
        with self.assertRaises(service.RecoveryError):
            service.apply(self.db, self.user.username, RepairRequest.model_validate(legacy), 'operator')
        self.assertEqual(self.latest_user().used_traffic, 100)

    def test_v2_rejects_two_record_history_instead_of_relaxing_v1(self):
        legacy = base.ContinuityTests.make_user(self, 'legacy_user')
        self.assertTrue(service.preview(self.db, legacy.username)['eligible'])
        self.assertIn('unsupported_history', service.preview_first_paid_period(self.db, legacy.username)['blockers'])

    def test_paid_period_relationships_fail_closed(self):
        baseline = self.request_body()
        candidates = {
            'starts_at': [self.user.created_at - timedelta(minutes=6), self.user.created_at + timedelta(minutes=6)],
            'ends_at': [self.user.created_at + timedelta(days=30), self.user.created_at + timedelta(days=33),
                        self.user.created_at + timedelta(days=31, seconds=1)],
            'last_observed_at': [self.user.created_at - timedelta(seconds=1),
                                 self.user.usage_logs[0].reset_at + timedelta(seconds=1)],
        }
        for key, values in candidates.items():
            for value in values:
                body = copy.deepcopy(baseline)
                body['paid_period_evidence'][key] = service.utc(value)
                with self.subTest(key=key, value=value), self.assertRaises(service.RecoveryError) as error:
                    self.apply(body)
                self.assertEqual(error.exception.detail['code'], 'paid_period_evidence_mismatch')
        for count in ('0', '6001'):
            body = copy.deepcopy(baseline)
            body['paid_period_evidence']['last_observed_used_traffic'] = count
            with self.assertRaises(service.RecoveryError):
                self.apply(body)
        self.assertEqual(self.db.query(UserUsageRecovery).count(), 0)

    def test_first_month_microseconds_and_small_provision_delay_are_supported(self):
        body = self.request_body()
        start = self.user.created_at + timedelta(microseconds=969530)
        body['paid_period_evidence'].update(starts_at=service.utc(start),
                                            ends_at=service.utc(start + timedelta(days=31)))
        receipt = self.apply(body)
        self.assertEqual(receipt['capability'], CAPABILITY)
        self.assertEqual(receipt['reason'], body['reason'])
        self.assertEqual(receipt['paid_period_evidence'], body['paid_period_evidence'])
        self.assertEqual(service.receipt_first_paid_period(self.db, body['operation_id']), receipt)

    def test_schema_rejects_wrong_reason_missing_proof_unknown_fields_and_noncanonical_dates(self):
        baseline = self.request_body()
        for value in ('restore_single_monthly_reset', 'reset'):
            body = copy.deepcopy(baseline)
            body['reason'] = value
            with self.assertRaises(ValidationError):
                FirstPaidPeriodRepairRequest.model_validate(body)
        body = copy.deepcopy(baseline)
        del body['paid_period_evidence']
        with self.assertRaises(ValidationError):
            FirstPaidPeriodRepairRequest.model_validate(body)
        for key, value in [('unknown', True), ('last_observed_used_traffic', 5990),
                           ('last_observed_used_traffic', '05990'), ('starts_at', '2026-10-13T03:18:10Z'),
                           ('starts_at', '2026-10-13T03:18:10.000000+00:00')]:
            body = copy.deepcopy(baseline)
            body['paid_period_evidence'][key] = value
            self.assertEqual(self.http('POST', '/api/usage-continuity/v2/users/example_user/repairs', body)[0], 422)

    def test_paid_evidence_change_on_same_operation_id_rejected(self):
        body = self.request_body()
        self.apply(body)
        body['paid_period_evidence']['last_observed_used_traffic'] = '5989'
        with self.assertRaises(service.RecoveryError) as error:
            self.apply(body)
        self.assertEqual(error.exception.detail['code'], 'operation_payload_mismatch')

    def test_v2_receipt_does_not_mislabel_legacy_receipt(self):
        user = base.ContinuityTests.make_user(self, 'legacy_receipt')
        body = {'operation_id': str(uuid4()), 'reason': 'restore_single_monthly_reset',
                'evidence_sha256': 'd'*64, 'expected': service.preview(self.db, user.username)['expected']}
        service.apply(self.db, user.username, RepairRequest.model_validate(body), 'operator')
        with self.assertRaises(service.RecoveryError) as error:
            service.receipt_first_paid_period(self.db, body['operation_id'])
        self.assertEqual(error.exception.detail['code'], 'operation_version_mismatch')

    def test_machine_contract_and_exact_payload_digest_match_receipt(self):
        contract = json.loads((Path(__file__).resolve().parents[1] /
                              'docs/contracts/usage-continuity-v2.json').read_text(encoding='utf-8'))
        body = self.request_body()
        self.assertEqual(set(contract['apply_body']), set(body))
        self.assertEqual(set(contract['apply_body']['paid_period_evidence']), set(body['paid_period_evidence']))
        receipt = self.apply(body)
        canonical = json.dumps({'username':'example_user','request':body}, sort_keys=True,
                               separators=(',', ':'), ensure_ascii=True).encode()
        self.assertEqual(receipt['payload_sha256'], hashlib.sha256(canonical).hexdigest())
        self.assertEqual(receipt['capability'], contract['contract_version'])

    def test_non_sqlite_preview_and_apply_are_rejected(self):
        body = FirstPaidPeriodRepairRequest.model_validate(self.request_body())
        fake = SimpleNamespace(new=[], dirty=[], deleted=[], rollback=Mock(),
                               get_bind=lambda: SimpleNamespace(dialect=SimpleNamespace(name='postgresql')))
        for fn, args in ((service.preview_first_paid_period, (fake, 'example_user')),
                         (service.apply_first_paid_period, (fake, 'example_user', body, 'operator'))):
            with self.assertRaises(service.RecoveryError) as error:
                fn(*args)
            self.assertEqual(error.exception.status, 503)
            self.assertEqual(error.exception.detail['code'], 'unsupported_database')

    def test_inherited_strict_request_types_remain_enforced(self):
        original = self.request_body()
        for key, value in [('unknown',True), ('operation_id',original['operation_id'].upper()),
                           ('evidence_sha256','invalid')]:
            body = copy.deepcopy(original)
            body[key] = value
            with self.assertRaises(ValidationError):
                FirstPaidPeriodRepairRequest.model_validate(body)
        for value in (100, True, '-1', '1.2', '0100'):
            body = copy.deepcopy(original)
            body['expected']['observed_used_traffic'] = value
            with self.assertRaises(ValidationError):
                FirstPaidPeriodRepairRequest.model_validate(body)

    def test_no_synthetic_zero_log_and_history_remains_clear_protected(self):
        self.apply(self.request_body())
        self.assertEqual(len(self.latest_user().usage_logs), 1)
        self.assertEqual(self.user.usage_logs[0].used_traffic_at_reset, 6000)
        with self.assertRaises(base.UsageHistoryProtectedError):
            base.crud.reset_all_users_data_usage(self.db)
        self.assertEqual(len(self.latest_user().usage_logs), 1)


# Apply the unchanged generic accounting/permission/race assertions to the v2
# fixture too. Each entry is a separate discovered test, not copied production logic.
for name in (
    'test_apply_restores_current_not_lifetime_preserves_all_other_fields',
    'test_user_api_and_subscription_keep_original_quota_and_correct_download',
    'test_concurrent_increase_since_preview_is_added_not_overwritten',
    'test_idempotent_receipt_survives_later_usage_reset_and_deleted_user',
    'test_same_uuid_changed_payload_or_path_is_rejected',
    'test_different_uuid_cannot_recover_same_target_twice',
    'test_reject_ineligible_account_states_and_limits',
    'test_reject_pending_plan_without_deleting_it',
    'test_snapshot_changes_fail_closed',
    'test_changed_proxy_identity_and_wrong_account_are_rejected',
    'test_observed_counter_and_lifetime_inconsistency_rejected',
    'test_counter_can_reach_quota_after_preview_and_is_rejected',
    'test_exact_large_integer_accounting',
    'test_commit_failure_rolls_back_counter_and_receipt',
    'test_real_concurrent_increments_and_apply_do_not_lose_or_duplicate_bytes',
    'test_two_simultaneous_identical_requests_return_one_receipt',
    'test_reset_before_repair_rejects_old_expected',
    'test_receipt_route_unknown_and_complete_http_roundtrip',
    'test_all_routes_require_sudo_and_failures_do_not_write',
    'test_sql_total_and_list_sort_remain_consistent',
    'test_recovery_has_no_xray_side_effects_and_normal_quota_review_still_limits',
    'test_two_different_operations_race_only_one_can_apply',
    'test_reset_writer_lock_serializes_an_inflight_repair',
    'test_reset_history_changed_in_place_is_detected',
):
    setattr(FirstPaidPeriodTests, name, getattr(base.ContinuityTests, name))
