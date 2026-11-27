"""Read period identity without inferring it from usage or expiry."""
from sqlalchemy import select

from app.db.models import User, UserSubscriptionPeriod

PERIOD_SECONDS = 30 * 86400
MAX_EPOCH = 253402300799
PERIOD_CAPABILITY = "website-subscription-period-v1"
PERIOD_ACTIONS = frozenset(("attach_period", "adjust_period", "open_period"))


def account_identity(user):
    table = UserSubscriptionPeriod
    return (table.user_id == user.id, table.user_created_at == user.created_at, table.username == user.username)


def current_period(db, user):
    table = UserSubscriptionPeriod
    return db.execute(select(table).where(*account_identity(user))
                      .order_by(table.starts_at.desc()).limit(1)).scalar_one_or_none()


def period_id_exists(db, user, period_id):
    table = UserSubscriptionPeriod
    return db.execute(select(table.id).where(*account_identity(user), table.period_id == period_id)
                      .limit(1)).scalar_one_or_none() is not None


def managed_account_exists():
    table = UserSubscriptionPeriod
    return select(table.id).where(table.user_id == User.id, table.user_created_at == User.created_at,
                                  table.username == User.username).correlate(User).exists()


def period_view(period, expires_at, quota):
    default_ends_at = period.starts_at + PERIOD_SECONDS
    added_bytes = quota - period.base_quota_bytes
    return {"period_id": period.period_id, "starts_at": period.starts_at, "default_ends_at": default_ends_at,
            "mode": "manual" if expires_at != default_ends_at or added_bytes else "monthly",
            "base_quota_bytes": str(period.base_quota_bytes), "added_bytes": str(added_bytes)}
