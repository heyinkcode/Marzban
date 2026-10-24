"""Narrow, auditable recovery of one reset's current-entitlement effect.

    No Xray calls, status transitions, quota edits or inferred payment decisions.
    SQLite write serialization is intentionally required for the first version.
"""
import hashlib
import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update

from app.db.models import User, UserUsageRecovery
from app.models.usage_continuity import CAPABILITY, ExpectedSnapshot

MAX_BYTES = 2**63 - 1


class RecoveryError(Exception):
    def __init__(self, code, status=409, blockers=None):
        self.status = status
        self.detail = {"code": code}
        if blockers is not None:
            self.detail["blockers"] = blockers
        super().__init__(code)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=True).encode("utf-8")).hexdigest()


def utc(value):
    return value.replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ") if value else None


def enum_value(value):
    return getattr(value, "value", value)


def _transaction(db, write=False):
    if db.get_bind().dialect.name != "sqlite":
        raise RecoveryError("unsupported_database", 503)
    if db.new or db.dirty or db.deleted:
        raise RuntimeError("recovery must own a clean transaction")
    # Authentication may have read using the same session. Do not reuse its
    # snapshot. Explicit BEGIN also gives the read-only preview a coherent view.
    db.rollback()
    db.connection().exec_driver_sql("BEGIN IMMEDIATE" if write else "BEGIN")


def _user(db, username):
    user = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if user is None or user.username != username:
        raise RecoveryError("user_not_found", 404)
    return user


def _preview(user, now):
    history = [{"id": log.id, "reset_at": utc(log.reset_at),
                "used_traffic_at_reset": str(log.used_traffic_at_reset)}
               for log in sorted(user.usage_logs, key=lambda log: (log.reset_at, log.id))]
    # Never return credentials. The seal detects account/configuration changes,
    # but is not an authentication token or evidence of entitlement legitimacy.
    identity = {column.name: enum_value(getattr(user, column.name)) for column in User.__table__.columns
                if column.name not in {"used_traffic", "online_at", "sub_updated_at", "sub_last_user_agent"}}
    identity = {key: utc(value) if isinstance(value, datetime) else value for key, value in identity.items()}
    identity["proxies"] = [{"id": proxy.id, "type": enum_value(proxy.type), "settings": proxy.settings,
                            "excluded_inbounds": sorted(item.tag for item in proxy.excluded_inbounds)}
                           for proxy in sorted(user.proxies, key=lambda proxy: proxy.id)]
    snapshot = ExpectedSnapshot(
        user_id=user.id, username=user.username, created_at=utc(user.created_at),
        status=enum_value(user.status), data_limit=str(user.data_limit) if user.data_limit is not None else None,
        expire=user.expire, reset_strategy=enum_value(user.data_limit_reset_strategy),
        device_limit=user.device_limit, device_limit_mode=enum_value(user.device_limit_mode),
        device_limit_action=enum_value(user.device_limit_action), has_next_plan=user.next_plan is not None,
        identity_seal=digest(identity), history_sha256=digest(history), history_count=len(history),
        initial_reset=history[0] if history else None, latest_reset=history[-1] if history else None,
        observed_used_traffic=str(user.used_traffic), observed_lifetime_used_traffic=str(user.lifetime_used_traffic),
    ).model_dump(mode="json")
    blockers = []
    if enum_value(user.status) != "active":
        blockers.append("not_active")
    if not user.expire or user.expire <= int(now.replace(tzinfo=timezone.utc).timestamp()):
        blockers.append("expired_or_unbounded")
    if not user.data_limit or not 0 < user.data_limit <= MAX_BYTES:
        blockers.append("invalid_quota")
    if enum_value(user.data_limit_reset_strategy) != "month":
        blockers.append("not_monthly")
    if user.next_plan is not None:
        blockers.append("pending_next_plan")
    if user.usage_recoveries:
        blockers.append("already_recovered")
    logs = sorted(user.usage_logs, key=lambda log: (log.reset_at, log.id))
    shape_ok = (len(logs) == 2 and logs[0].used_traffic_at_reset == 0
                and logs[1].used_traffic_at_reset > 0
                and timedelta(0) <= logs[0].reset_at - user.created_at <= timedelta(minutes=5)
                and logs[1].reset_at >= logs[0].reset_at + timedelta(days=30)
                and logs[1].reset_at <= now)
    amount = logs[-1].used_traffic_at_reset if shape_ok else 0
    if not shape_ok:
        blockers.append("unsupported_history")
    elif now >= logs[-1].reset_at + timedelta(days=30):
        blockers.append("next_reset_due")
    if not 0 <= user.used_traffic <= MAX_BYTES or not 0 <= amount <= MAX_BYTES - user.used_traffic:
        blockers.append("invalid_counter")
    if user.data_limit and user.used_traffic + amount >= user.data_limit:
        blockers.append("would_reach_quota")
    return {"capability": CAPABILITY, "eligible": not blockers, "blockers": blockers,
            "history_complete": True, "reset_origin": "unrecorded", "history": history,
            "restorable_bytes": str(amount), "expected": snapshot}


def preview(db, username):
    try:
        _transaction(db)
        return _preview(_user(db, username), datetime.utcnow())
    finally:
        db.rollback()


def receipt(db, operation_id):
    row = db.get(UserUsageRecovery, str(operation_id))
    if row is None:
        raise RecoveryError("receipt_not_found", 404)
    return dict(row.receipt)


def apply(db, username, request, actor):
    fingerprint = digest({"username": username, "request": request.model_dump(mode="json")})
    try:
        _transaction(db, write=True)
        old = db.get(UserUsageRecovery, str(request.operation_id))
        if old:
            if old.payload_sha256 != fingerprint:
                raise RecoveryError("operation_payload_mismatch")
            result = dict(old.receipt)
            db.rollback()
            return result
        user = _user(db, username)
        now = datetime.utcnow()
        current = _preview(user, now)
        if not current["eligible"]:
            raise RecoveryError("ineligible", blockers=current["blockers"])
        expected = request.expected.model_dump(mode="json")
        actual = current["expected"]
        moving = {"observed_used_traffic", "observed_lifetime_used_traffic"}
        if {k: v for k, v in expected.items() if k not in moving} != {
                k: v for k, v in actual.items() if k not in moving}:
            raise RecoveryError("snapshot_changed")
        amount = int(current["restorable_bytes"])
        before, lifetime = user.used_traffic, user.lifetime_used_traffic
        if (int(expected["observed_used_traffic"]) > before
                or int(expected["observed_lifetime_used_traffic"]) != int(expected["observed_used_traffic"]) + amount):
            raise RecoveryError("observed_counter_changed")
        result = {"capability": CAPABILITY, "status": "applied", "operation_id": str(request.operation_id),
                  "payload_sha256": fingerprint, "evidence_sha256": request.evidence_sha256,
                  "user_id": user.id, "username": username, "created_at": utc(user.created_at),
                  "reset_id": actual["latest_reset"]["id"], "reset_at": actual["latest_reset"]["reset_at"],
                  "restored_bytes": str(amount), "used_traffic_before": str(before),
                  "used_traffic_after": str(before + amount), "lifetime_used_traffic_before": str(lifetime),
                  "lifetime_used_traffic_after": str(lifetime), "data_limit": str(user.data_limit),
                  "expire": user.expire, "reset_strategy": enum_value(user.data_limit_reset_strategy),
                  "applied_at": utc(now), "actor": actor}
        updated = db.execute(update(User).where(User.id == user.id, User.used_traffic == before).values(
            used_traffic=User.used_traffic + amount).execution_options(synchronize_session=False))
        if updated.rowcount != 1:
            raise RecoveryError("concurrent_change")
        db.add(UserUsageRecovery(operation_id=str(request.operation_id), user_id=user.id,
               username=username,
               user_created_at=user.created_at, reset_id=result["reset_id"], restored_bytes=amount,
               payload_sha256=fingerprint, receipt=result))
        db.flush()
        db.expire(user)
        if user.lifetime_used_traffic != lifetime or user.used_traffic != before + amount:
            raise RuntimeError("usage recovery invariant failed")
        db.commit()
        return result
    except Exception:
        db.rollback()
        raise
