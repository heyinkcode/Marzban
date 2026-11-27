"""SQLite accounting kernel for one premature reset in a proven renewed allowance.

An external orchestrator must prove the payment, scope the repair
to the same unrenewed allowance, fence orders, and verify the original receipt.
This module does not register a route, write payment data or change policy.
"""
from datetime import datetime, timedelta, timezone
from typing import Literal

from pydantic import StrictInt, StrictStr, field_validator
from sqlalchemy import update

from app.db import usage_continuity as base
from app.db.models import User, UserUsageRecovery
from app.models.usage_continuity import ByteCount, ContractModel, Digest, RepairRequest
from app.models.usage_continuity_v2 import parse_utc

CAPABILITY = "usage-continuity-paid-extension-v1"


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class PaidExtensionEvidence(ContractModel):
    paid_starts_at: StrictStr
    paid_ends_at: StrictStr
    access_ends_at: StrictStr
    paid_reset_id: StrictInt
    paid_reset_offset_bytes: ByteCount
    last_observed_at: StrictStr
    last_observed_used_traffic: ByteCount

    @field_validator("paid_starts_at", "paid_ends_at", "access_ends_at", "last_observed_at")
    @classmethod
    def canonical_utc(cls, value):
        parse_utc(value)
        return value


class PaidExtensionRequest(RepairRequest):
    reason: Literal["restore_renewed_allowance_during_extension"]
    prior_corrections_sha256: Digest
    paid_extension_evidence: PaidExtensionEvidence


def _snapshot(user, now):
    legacy = base._preview(user, now)
    corrections = sorted((item.reset_id, item.operation_id, item.restored_bytes,
                          item.payload_sha256, item.receipt.get("applied_at") if isinstance(item.receipt, dict) else None)
                         for item in user.usage_recoveries)
    return legacy["expected"], legacy["history"], base.digest(corrections)


def preview(db, username):
    """Capture identity and counters. This is not proof of ownership or payment."""
    try:
        base._transaction(db)
        expected, history, seal = _snapshot(base._user(db, username), _now())
        return {"capability": CAPABILITY, "expected": expected, "history": history,
                "prior_corrections_sha256": seal, "eligibility_scope": "panel_state_only"}
    finally:
        db.rollback()


def receipt(db, operation_id):
    result = base.receipt(db, operation_id)
    if result.get("capability") != CAPABILITY:
        raise base.RecoveryError("operation_version_mismatch")
    return result


def _validate(user, history, now, evidence):
    start, paid_end, access_end, observed = (parse_utc(v) for v in (
        evidence.paid_starts_at, evidence.paid_ends_at, evidence.access_ends_at,
        evidence.last_observed_at))
    if len(history) < 2:
        raise base.RecoveryError("paid_reset_anchor_missing")
    previous, latest = history[-2:]
    anchor, target = parse_utc(previous["reset_at"]), parse_utc(latest["reset_at"])
    amount = int(latest["used_traffic_at_reset"])
    if (now.tzinfo is not None or base.enum_value(user.status) != "active" or
            base.enum_value(user.data_limit_reset_strategy) != "month" or user.next_plan is not None):
        raise base.RecoveryError("account_not_eligible")
    now_utc = now.replace(tzinfo=timezone.utc)
    if not (timedelta(days=30) <= paid_end - start <= timedelta(days=32)
            and timedelta(0) < access_end - paid_end <= timedelta(days=14)
            and paid_end <= now_utc < access_end and int(access_end.timestamp()) == user.expire
            and start <= anchor <= start + timedelta(minutes=5)
            and anchor <= observed <= target < paid_end
            and observed >= target - timedelta(minutes=10)
            and timedelta(days=30) <= target - anchor <= timedelta(days=30, hours=2)
            and anchor < target and now_utc < target + timedelta(days=30)
            and previous["id"] == evidence.paid_reset_id
            and 0 < amount == int(evidence.last_observed_used_traffic)):
        raise base.RecoveryError("paid_extension_evidence_mismatch")

    older = {r["id"]: r for r in history[:-2]}
    older_amounts = {i: int(r["used_traffic_at_reset"]) for i, r in older.items()}
    corrected = set()
    offset = sum(older_amounts.values()) + int(previous["used_traffic_at_reset"])
    for item in user.usage_recoveries:
        if item.reset_id == latest["id"]:
            raise base.RecoveryError("reset_already_recovered")
        if (item.reset_id in corrected or not 0 < item.restored_bytes <= older_amounts.get(item.reset_id, 0)
                or not isinstance(item.receipt, dict)):
            raise base.RecoveryError("prior_recovery_not_proven")
        try:
            recorded = parse_utc(item.receipt.get("applied_at"))
        except (TypeError, ValueError):
            raise base.RecoveryError("prior_recovery_not_proven") from None
        if not parse_utc(older[item.reset_id]["reset_at"]) <= recorded <= anchor:
            raise base.RecoveryError("prior_recovery_not_proven")
        corrected.add(item.reset_id)
        offset -= item.restored_bytes
    if not 0 <= offset == int(evidence.paid_reset_offset_bytes) <= base.MAX_BYTES:
        raise base.RecoveryError("paid_reset_offset_mismatch")
    return latest, amount, offset


def apply(db, username, request, actor):
    fingerprint = base.digest({"username": username, "request": request.model_dump(mode="json")})
    try:
        base._transaction(db, write=True)
        old = db.get(UserUsageRecovery, str(request.operation_id))
        if old is not None:
            if (old.payload_sha256 != fingerprint or not isinstance(old.receipt, dict)
                    or old.receipt.get("capability") != CAPABILITY):
                raise base.RecoveryError("operation_payload_mismatch")
            response = dict(old.receipt)
            db.rollback()
            return response
        user = base._user(db, username)
        now = _now()
        current, history, seal = _snapshot(user, now)
        latest, amount, offset = _validate(user, history, now, request.paid_extension_evidence)
        expected = request.expected.model_dump(mode="json")
        moving = {"observed_used_traffic", "observed_lifetime_used_traffic"}
        if (seal != request.prior_corrections_sha256 or
                {k: v for k, v in expected.items() if k not in moving} !=
                {k: v for k, v in current.items() if k not in moving}):
            raise base.RecoveryError("snapshot_changed")
        before = user.used_traffic
        observed = int(expected["observed_used_traffic"])
        lifetime = user.lifetime_used_traffic
        if (not 0 <= observed <= before or lifetime != offset + amount + before or
                int(expected["observed_lifetime_used_traffic"]) != offset + amount + observed):
            raise base.RecoveryError("observed_counter_changed")
        after = before + amount
        if not user.data_limit or not 0 <= before < after < user.data_limit <= base.MAX_BYTES:
            raise base.RecoveryError("would_reach_quota")
        response = {"capability": CAPABILITY, "status": "applied", "operation_id": str(request.operation_id),
                    "payload_sha256": fingerprint, "evidence_sha256": request.evidence_sha256,
                    "user_id": user.id, "username": username, "created_at": base.utc(user.created_at),
                    "reset_id": latest["id"], "reset_at": latest["reset_at"], "restored_bytes": str(amount),
                    "used_traffic_before": str(before), "used_traffic_after": str(after),
                    "lifetime_used_traffic_before": str(lifetime), "lifetime_used_traffic_after": str(lifetime),
                    "data_limit": str(user.data_limit), "expire": user.expire, "reset_strategy": "month",
                    "applied_at": base.utc(now), "actor": actor, "reason": request.reason,
                    "paid_extension_evidence": request.paid_extension_evidence.model_dump(mode="json")}
        updated = db.execute(update(User).where(User.id == user.id, User.used_traffic == before).values(
            used_traffic=after).execution_options(synchronize_session=False))
        if updated.rowcount != 1:
            raise base.RecoveryError("concurrent_change")
        db.add(UserUsageRecovery(operation_id=str(request.operation_id), user_id=user.id,
               username=username, user_created_at=user.created_at, reset_id=latest["id"], restored_bytes=amount,
               payload_sha256=fingerprint, receipt=response))
        db.flush()
        db.expire_all()
        if user.used_traffic != after or user.lifetime_used_traffic != lifetime:
            raise RuntimeError("paid extension recovery invariant failed")
        db.commit()
        return response
    except Exception:
        db.rollback()
        raise
