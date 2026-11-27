"""Real SQLite transactions for the local internal extended-allowance kernel."""
import copy
import unittest
from datetime import timedelta, timezone
from unittest.mock import patch
from uuid import uuid4

from sqlalchemy import update

import test_usage_continuity as fixtures
from app.db import usage_continuity as legacy
from app.db import usage_continuity_paid_extension as extension
from app.db.models import User, UserUsageRecovery, UserUsageResetLogs
from app.routers import usage_continuity_paid_extension as routes


class PaidExtensionTests(unittest.TestCase):
    setUp = fixtures.ContinuityTests.setUp
    latest_user = fixtures.ContinuityTests.latest_user

    def make_user(self, name):
        user = fixtures.ContinuityTests.make_user(self, name)
        self.paid_start = self.now - timedelta(days=31, hours=3)
        self.anchor = self.paid_start + timedelta(seconds=3)
        self.wrong_reset = self.anchor + timedelta(days=30, minutes=56)
        user.created_at = self.paid_start - timedelta(days=35)
        user.expire = int((self.paid_start + timedelta(days=38)).replace(tzinfo=timezone.utc).timestamp())
        user.usage_logs[0].reset_at = user.created_at
        user.usage_logs[1].reset_at = self.paid_start - timedelta(days=4)
        user.usage_logs[1].used_traffic_at_reset = 7000
        user.usage_logs.extend([UserUsageResetLogs(used_traffic_at_reset=8000, reset_at=self.anchor),
                                UserUsageResetLogs(used_traffic_at_reset=4500, reset_at=self.wrong_reset)])
        self.db.commit()
        self.old_id, self.anchor_id, self.reset_id = [log.id for log in user.usage_logs[1:]]
        self.old_recovery = str(uuid4())
        self.db.add(UserUsageRecovery(operation_id=self.old_recovery, user_id=user.id, username=name,
                    user_created_at=user.created_at, reset_id=self.old_id, restored_bytes=7000,
                    payload_sha256='0'*64, receipt={'applied_at':legacy.utc(self.anchor-timedelta(days=3))}))
        self.db.commit()
        return user

    def body(self):
        info = extension.preview(self.db, self.user.username)
        return {'operation_id':str(uuid4()), 'reason':'restore_renewed_allowance_during_extension',
                'evidence_sha256':'d'*64, 'expected':info['expected'],
                'prior_corrections_sha256':info['prior_corrections_sha256'],
                'paid_extension_evidence':{'paid_starts_at':legacy.utc(self.paid_start),
                    'paid_ends_at':legacy.utc(self.paid_start+timedelta(days=31)),
                    'access_ends_at':legacy.utc(self.paid_start+timedelta(days=38)),
                    'paid_reset_id':self.anchor_id, 'paid_reset_offset_bytes':'8000',
                    'last_observed_at':legacy.utc(self.wrong_reset-timedelta(seconds=100)),
                    'last_observed_used_traffic':'4500'}}

    def apply(self, body):
        return extension.apply(self.db, 'example_user', extension.PaidExtensionRequest.model_validate(body), 'operator')

    def set_used(self, amount):
        self.db.execute(update(User).where(User.id==self.user.id).values(used_traffic=amount))
        self.db.commit()

    def test_only_latest_is_added_to_fresh_current_usage_and_website_delta_is_not_doubled(self):
        body = self.body()
        self.assertIn('unsupported_history', legacy.preview(self.db, self.user.username)['blockers'])
        self.set_used(145)  # Arrived after preview.
        before = self.latest_user().lifetime_used_traffic
        receipt = self.apply(body)
        user = self.latest_user()
        self.assertEqual(receipt['reset_id'],self.reset_id)
        self.assertEqual(receipt['restored_bytes'],'4500')
        self.assertEqual(receipt['used_traffic_before'],'145')
        self.assertEqual(user.used_traffic,4645)
        # Website already retains the 4500-byte sample, so normal metering sees +145.
        self.assertEqual(user.used_traffic-int(body['paid_extension_evidence']['last_observed_used_traffic']),145)
        self.assertEqual(user.lifetime_used_traffic,before)
        self.assertEqual(user.expire,body['expected']['expire'])
        self.assertEqual(user.data_limit,10000)
        self.assertEqual(user.data_limit_reset_strategy,'month')
        self.assertEqual(len(user.usage_logs),4)
        self.assertEqual(self.db.query(UserUsageRecovery).count(),2)

    def test_idempotency_replay_keeps_later_usage_and_fresh_id_cannot_duplicate(self):
        body = self.body()
        receipt = self.apply(body)
        self.set_used(4715)
        self.assertEqual(self.apply(body),receipt)
        with self.assertRaisesRegex(legacy.RecoveryError,'reset_already_recovered'):
            self.apply(self.body())
        self.assertEqual(self.latest_user().used_traffic,4715)
        body['evidence_sha256']='0'*64
        with self.assertRaisesRegex(legacy.RecoveryError,'operation_payload_mismatch'):
            self.apply(body)

    def test_wrong_payment_boundary_quota_expiry_and_snapshot_fail_closed(self):
        original = self.body()
        for key,value in [('paid_reset_id',self.old_id),('paid_reset_offset_bytes','8001'),
                          ('last_observed_used_traffic','4499'),('paid_ends_at',legacy.utc(self.now+timedelta(seconds=10))),
                          ('access_ends_at',legacy.utc(self.now-timedelta(seconds=1)))]:
            with self.subTest(key=key),self.assertRaises(legacy.RecoveryError):
                body = copy.deepcopy(original)
                body['paid_extension_evidence'][key]=value
                self.apply(body)
        with self.assertRaisesRegex(legacy.RecoveryError,'snapshot_changed'):
            self.apply(dict(original,prior_corrections_sha256='b'*64))
        self.set_used(5500)
        with self.assertRaisesRegex(legacy.RecoveryError,'would_reach_quota'):
            self.apply(original)
        self.assertEqual(self.latest_user().used_traffic,5500)
        self.assertEqual(self.db.query(UserUsageRecovery).count(),1)

    def test_paid_renewal_or_another_reset_after_preview_invalidates_operation(self):
        body = self.body()
        self.user.usage_logs.append(UserUsageResetLogs(used_traffic_at_reset=100,reset_at=self.now))
        self.db.commit()
        with self.assertRaises(legacy.RecoveryError):
            self.apply(body)
        self.assertEqual(self.latest_user().used_traffic,100)
        self.assertEqual(self.db.query(UserUsageRecovery).count(),1)

    def test_failure_rolls_back_both_counter_and_receipt(self):
        body = self.body()
        with patch.object(self.db,'commit',side_effect=RuntimeError('fixture transaction failure')):
            with self.assertRaisesRegex(RuntimeError,'fixture transaction failure'):
                self.apply(body)
        self.assertEqual(self.latest_user().used_traffic,100)
        self.assertEqual(self.db.query(UserUsageRecovery).count(),1)

    def test_routes_require_sudo_and_roundtrip_original_receipt(self):
        body=self.body()
        prefix='/api/usage-continuity/paid-extension-v1'
        with patch.object(fixtures,'routes',routes):
            http=lambda method,path,**kw: fixtures.ContinuityTests.http(self,method,prefix+path,**kw)
            self.assertIn(http('POST','/users/example_user/repairs',body=body,admin=False)[0],(401,403))
            status,preview,headers=http('GET','/users/example_user/preview')
            self.assertEqual(status,200)
            self.assertEqual(preview['capability'],extension.CAPABILITY)
            self.assertIn(b'no-store',headers[b'cache-control'])
            self.assertEqual(http('GET','/repairs/'+body['operation_id'])[0],404)
            status,receipt,_=http('POST','/users/example_user/repairs',body=body)
            self.assertEqual(status,200)
            self.assertEqual(http('GET','/repairs/'+body['operation_id'])[1],receipt)
            self.assertEqual(http('GET','/repairs/'+self.old_recovery)[0],409)
