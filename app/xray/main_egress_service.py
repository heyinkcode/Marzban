"""Sudo main-only egress actions; no Node or relay lifecycle operations."""
from app import xray
from app.xray import main_egress as store
from app.xray import main_egress_probe
from app.xray.main_core import MainCoreError


def apply(db, draft):
    with xray.core.change():
        if not xray.core.started:
            raise MainCoreError("MAIN_CORE_OFFLINE", 409)
        db.expire_all()
        candidate = store.prepare_profile(db, draft) if draft is not None else None
        base = xray.config.include_db_users()
        runtime = store.for_main(base, candidate)
        if xray.core._last_config is None:
            raise MainCoreError("MAIN_CORE_NOT_READY", 409)
        # Include the latest registered/shared accounts in the restore config.
        # The last process-start snapshot can predate live API account updates.
        previous = store.for_main(base, store.read_profile(db))
        xray.core.replace_runtime(runtime, rollback_config=previous)
        try:
            store.persist_profile(db, candidate)
        except Exception:
            db.rollback()
            try:
                xray.core.replace_runtime(previous)
            except Exception:
                raise MainCoreError("MAIN_SAVE_FAILED_ROLLBACK_FAILED") from None
            raise MainCoreError("MAIN_SAVE_FAILED_ROLLED_BACK") from None
        return store.public_profile(db)


def probe(db, settings):
    candidate = store.prepare_profile(db, settings.profile.model_dump())
    try:
        return main_egress_probe.probe(candidate, settings.timeout_seconds, settings.attempts)
    except RuntimeError as exc:
        if str(exc) == "PROBE_BUSY":
            raise MainCoreError("MAIN_PROBE_BUSY", 409) from None
        raise MainCoreError("MAIN_PROBE_UNAVAILABLE", 502) from None
