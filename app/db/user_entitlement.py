"""Native entitlement actions; no external billing service is required."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.models import NotificationReminder, User, UserEntitlementOperation, UserUsageRecovery, UserUsageResetLogs
from app.db.usage_continuity import MAX_BYTES, RecoveryError, digest, enum_value, utc
from app.models.user import ReminderType, UserStatus


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _epoch(now):
    return int(now.replace(tzinfo=timezone.utc).timestamp())


def status_for_entitlement(status, expires_at, used, quota, now_epoch):
    """An entitlement change never overrides admin disable or on-hold."""
    if status in (UserStatus.disabled, UserStatus.on_hold):
        return enum_value(status)
    if expires_at and expires_at <= now_epoch:
        return UserStatus.expired.value
    return UserStatus.limited.value if quota and used >= quota else UserStatus.active.value


def _lookup(db, username, admin, *, write=False):
    if write:
        # Auth may already have opened a read snapshot: renew that snapshot
        # before locking. SQLite and server SQL engines serialize differently.
        if db.new or db.dirty or db.deleted:
            raise RuntimeError("entitlement operations require a clean transaction")
        db.rollback()
        if db.get_bind().dialect.name == "sqlite":
            db.connection().exec_driver_sql("BEGIN IMMEDIATE")
    statement = select(User).where(User.username == username)
    user = db.execute(statement.with_for_update() if write else statement).scalar_one_or_none()
    if user is None or user.username != username:
        raise RecoveryError("user_not_found", 404)
    if not (admin.is_sudo or user.admin and user.admin.username == admin.username):
        raise RecoveryError("permission_denied", 403)
    return user


def _for_account(table, user):
    return (table.user_id == user.id, table.username == user.username, table.user_created_at == user.created_at)


def _latest_reset(db, user):
    log = db.execute(select(UserUsageResetLogs).where(UserUsageResetLogs.user_id == user.id)
                     .order_by(UserUsageResetLogs.reset_at.desc(), UserUsageResetLogs.id.desc()).limit(1)).scalar_one_or_none()
    if log is None:
        return None
    native = db.execute(select(UserEntitlementOperation.operation_id).where(
        *_for_account(UserEntitlementOperation, user), UserEntitlementOperation.action == "renew",
        UserEntitlementOperation.reset_id == log.id).limit(1)).scalar_one_or_none()
    corrected = db.execute(select(UserUsageRecovery.operation_id).where(
        *_for_account(UserUsageRecovery, user), UserUsageRecovery.reset_id == log.id).limit(1)).scalar_one_or_none()
    return {"id": log.id, "reset_at": utc(log.reset_at), "bytes": str(log.used_traffic_at_reset),
            "origin": "native_renewal" if native else "unrecorded", "restored": corrected is not None}


def _view(user, *, expires_at, quota, used, status):
    return {"expires_at": expires_at, "quota_bytes": str(quota) if quota else None, "used_bytes": str(used),
            "remaining_bytes": str(max(0, quota - used)) if quota else None, "status": enum_value(status),
            "reset_strategy": enum_value(user.data_limit_reset_strategy), "has_next_plan": user.next_plan is not None}


def _state(user):
    return _view(user, expires_at=user.expire, quota=user.data_limit, used=user.used_traffic, status=user.status)


def get_overview(db, username, admin):
    user = _lookup(db, username, admin)
    return {"username": user.username, "state": _state(user), "latest_reset": _latest_reset(db, user),
            "can_restore": admin.is_sudo}


def _project(db, user, command, now, admin):
    old = _state(user)
    latest = _latest_reset(db, user)
    last_op = db.execute(select(UserEntitlementOperation.operation_id).where(
        *_for_account(UserEntitlementOperation, user)).order_by(UserEntitlementOperation.recorded_at.desc(),
                                                               UserEntitlementOperation.operation_id.desc()).limit(1)).scalar_one_or_none()
    expires, quota, used = user.expire, user.data_limit, user.used_traffic
    if not 0 <= used <= MAX_BYTES or quota is not None and not 0 <= quota <= MAX_BYTES:
        raise RecoveryError("invalid_counter")
    action = command.action
    if action == "extend" or action == "renew" and command.expires_at is not None:
        if not expires or command.expires_at <= max(expires, _epoch(now)):
            raise RecoveryError("expiry_must_extend_finite_term")
        expires = command.expires_at
    if action == "add":
        extra = int(command.extra_bytes)
        if not quota or extra <= 0 or extra > MAX_BYTES - quota:
            raise RecoveryError("finite_quota_and_valid_increment_required")
        quota += extra
    if action in ("renew", "restore") and user.next_plan is not None:
        raise RecoveryError("next_plan_conflict")
    restored = 0
    if action == "renew":
        if expires and expires <= _epoch(now):
            raise RecoveryError("renewal_requires_future_expiry")
        used = 0
    if action == "restore":
        if not admin.is_sudo:
            raise RecoveryError("permission_denied", 403)
        if user.status != UserStatus.active or expires and expires <= _epoch(now):
            raise RecoveryError("restore_requires_active_term")
        if not latest or latest["id"] != command.reset_id or latest["restored"] or latest["origin"] == "native_renewal":
            raise RecoveryError("reset_not_restorable")
        restored = int(latest["bytes"])
        if not quota or restored <= 0 or restored > MAX_BYTES - used or used + restored >= quota:
            raise RecoveryError("restore_would_reach_quota")
        used += restored
    after = _view(user, expires_at=expires, quota=quota, used=used,
                  status=status_for_entitlement(user.status, expires, used, quota, _epoch(now)))
    # Current traffic can grow between preview and confirmation. Only reserve
    # static terms, reset identity and the last successful native operation.
    guard = digest({"user_id": user.id, "username": user.username, "created_at": utc(user.created_at),
                    "admin_id": user.admin_id, "expires_at": old["expires_at"], "quota_bytes": old["quota_bytes"],
                    "status": old["status"], "reset_strategy": old["reset_strategy"], "latest_reset": latest,
                    "next_plan": [user.next_plan.id, user.next_plan.expire, user.next_plan.data_limit,
                                  user.next_plan.fire_on_either, user.next_plan.add_remaining_traffic] if user.next_plan else None,
                    "last_operation": last_op, "command": command.model_dump(mode="json")})
    return {"guard": guard, "before": old, "after": after, "restored_bytes": str(restored)}


def preview(db, username, command, admin):
    user = _lookup(db, username, admin)
    return _project(db, user, command, _now(), admin)


def get_receipt(db, username, operation_id, admin):
    user = _lookup(db, username, admin)
    operation = db.get(UserEntitlementOperation, operation_id)
    if not _same_account(operation, user):
        raise RecoveryError("receipt_not_found", 404)
    return dict(operation.receipt)


def _same_account(operation, user):
    return operation is not None and (operation.user_id, operation.username, operation.user_created_at) == (
        user.id, user.username, user.created_at)


def _refresh_reminders(db, user, action, now):
    rows = db.execute(select(NotificationReminder).where(NotificationReminder.user_id == user.id)).scalars()
    for row in rows:
        if row.threshold is None:
            continue
        if action in ("extend", "renew") and row.type == ReminderType.expiration_date and (
                not user.expire or user.expire - _epoch(now) > row.threshold * 86400):
            db.delete(row)
        if action in ("add", "renew") and row.type == ReminderType.data_usage and (
                not user.data_limit or user.used_traffic * 100 < row.threshold * user.data_limit):
            db.delete(row)


def apply(db, username, request, admin):
    fingerprint = digest({"username": username, "body": request.model_dump(mode="json")})
    try:
        user = _lookup(db, username, admin, write=True)
        old_op = db.get(UserEntitlementOperation, request.operation_id)
        if old_op is not None:
            if not _same_account(old_op, user) or old_op.payload_sha256 != fingerprint:
                raise RecoveryError("operation_conflict")
            result = dict(old_op.receipt)
            db.rollback()
            return result
        action = request.command.action
        if action in ("renew", "restore") and not request.confirmed:
            raise RecoveryError("explicit_confirmation_required")
        now = _now()
        projected = _project(db, user, request.command, now, admin)
        if projected["guard"] != request.guard:
            raise RecoveryError("entitlement_changed")
        before, after = projected["before"], projected["after"]
        lifetime = user.lifetime_used_traffic if action in ("renew", "restore") else None
        reset_id = request.command.reset_id
        if action == "renew":
            log = UserUsageResetLogs(user=user, used_traffic_at_reset=user.used_traffic, reset_at=now)
            db.add(log)
            user.node_usages.clear()
            db.flush()
            reset_id = log.id
        if action in ("extend", "renew"):
            user.expire = after["expires_at"]
        if action == "add":
            user.data_limit = int(after["quota_bytes"])
        if action in ("renew", "restore"):
            user.used_traffic = int(after["used_bytes"])
        if before["status"] != after["status"]:
            user.status = after["status"]
        if action != "restore":
            _refresh_reminders(db, user, action, now)
        result = {"operation_id": request.operation_id, "action": action, "username": user.username,
                  "user_id": user.id, "account_created_at": utc(user.created_at), "applied_at": utc(now),
                  "actor": admin.username, "before": before, "after": after, "reset_id": reset_id,
                  "restored_bytes": projected["restored_bytes"]}
        if action == "restore":
            correction = {"capability": "native-entitlement-v1", "reset_id": reset_id, "applied_at": utc(now),
                          "operation_id": request.operation_id, "reason": request.command.reason,
                          "restored_bytes": projected["restored_bytes"], "actor": admin.username}
            db.add(UserUsageRecovery(operation_id=request.operation_id, user_id=user.id, username=user.username,
                     user_created_at=user.created_at, reset_id=reset_id, restored_bytes=int(projected["restored_bytes"]),
                     payload_sha256=fingerprint, receipt=correction))
            result["reason"] = request.command.reason
        db.add(UserEntitlementOperation(operation_id=request.operation_id, user_id=user.id, username=user.username,
                user_created_at=user.created_at, action=action, reset_id=reset_id, payload_sha256=fingerprint,
                recorded_at=now, receipt=result))
        db.flush()
        if lifetime is not None:
            db.expire(user, ["usage_logs", "usage_recoveries"])
            if lifetime != user.lifetime_used_traffic:
                raise RuntimeError("Entitlement operation changed lifetime accounting")
        db.commit()
        return result
    except IntegrityError as exc:
        db.rollback()
        raise RecoveryError("operation_conflict") from exc
    except Exception:
        db.rollback()
        raise
