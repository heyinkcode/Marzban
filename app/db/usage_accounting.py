"""Serialize counter-reset writers with atomic usage collection and recovery."""
from sqlalchemy import update
from sqlalchemy.orm import object_session


class UsageHistoryProtectedError(RuntimeError):
    pass


def lock_user_usage(db, user):
    """Obtain a write lock before refreshing a previously read counter.

    A no-op UPDATE also obtains SQLite's writer lock (SELECT FOR UPDATE does not).
    No commit here: counter snapshot, reset log and zeroing share the transaction.
    """
    from app.db.models import User
    if object_session(user) is not db or db.is_modified(user, include_collections=True):
        raise ValueError("usage reset requires a clean attached user")
    with db.no_autoflush:
        changed = db.execute(update(User).where(User.id == user.id,
                            User.created_at == user.created_at).values(
                            used_traffic=User.used_traffic).execution_options(synchronize_session=False))
        if changed.rowcount != 1:
            raise ValueError("usage reset target changed")
        db.expire(user)
        db.refresh(user)
