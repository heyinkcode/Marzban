"""Authenticated diagnostics and acknowledged per-Node egress replacement."""
from app import xray
from app.xray.node_egress import for_node
from app.xray.node_egress_store import prepare_egress, read_egress, save_egress, public_egress

CAPABILITY = "managed-egress-probe-v1"


class EgressError(RuntimeError):
    def __init__(self, code, status=409):
        self.code, self.status = code, status


def paired_node(dbnode):
    node = xray.nodes.get(dbnode.id)
    if dbnode.status == "disabled" or node is None:
        raise EgressError("NODE_OFFLINE")
    try:
        if not node.connected:
            raise EgressError("NODE_OFFLINE")
        health = node.get_health()
    except EgressError:
        raise
    except Exception:
        raise EgressError("NODE_CONTROL_UNAVAILABLE", 502) from None
    if not isinstance(health, dict) or health.get("source") != "node-runtime" or CAPABILITY not in health.get("capabilities", []):
        raise EgressError("NODE_UPGRADE_REQUIRED")
    return node, health


def probe(db, dbnode, settings):
    profile = prepare_egress(db, dbnode, settings.profile.model_dump())
    node, _ = paired_node(dbnode)
    try:
        result = node.probe_egress(profile, settings.timeout_seconds, settings.attempts)
    except Exception:
        raise EgressError("NODE_PROBE_UNAVAILABLE", 502) from None
    if not isinstance(result, dict) or result.get("source") != "node-egress-probe" or result.get("version") != 1:
        raise EgressError("NODE_PROBE_INVALID_RESPONSE", 502)
    return {**result, "node_id": dbnode.id}


def apply(db, dbnode, profile):
    # Serialize with reconnect, deletion and every other egress write.
    lock = xray.operations.node_lifecycle_lock(dbnode.id)
    if not lock.acquire(blocking=False):
        raise EgressError("NODE_BUSY")
    try:
        db.refresh(dbnode)
        candidate = prepare_egress(db, dbnode, profile) if profile is not None else None
        previous = read_egress(db, dbnode)
        node, health = paired_node(dbnode)
        config = for_node(xray.config.include_db_users(), candidate, health)
        try:
            node.restart(config)
        except Exception as exc:
            # Never blindly replay a mutation after a transport timeout. The
            # Node has local startup rollback, but a lost ACK is unconfirmed.
            detail = str(getattr(exc, "detail", exc))
            if "XRAY_RESTART_FAILED_ROLLED_BACK" in detail:
                raise EgressError("SAVE_FAILED_ROLLED_BACK", 502) from None
            if "XRAY_RESTART_BUSY" in detail:
                raise EgressError("NODE_BUSY") from None
            raise EgressError("APPLY_UNCONFIRMED_SAVED_UNCHANGED", 502) from None
        try:
            if candidate is None:
                if dbnode.egress is not None:
                    db.delete(dbnode.egress)
                    dbnode.egress = None
                db.commit()
            else:
                save_egress(db, dbnode, candidate)
        except Exception:
            db.rollback()
            try:
                node.restart(for_node(xray.config.include_db_users(), previous, health))
            except Exception:
                raise EgressError("SAVE_FAILED_ROLLBACK_UNCONFIRMED", 503) from None
            raise EgressError("SAVE_FAILED_ROLLED_BACK", 503) from None
        # Reconciliation is best effort after an acknowledged, persisted
        # change. Its failure must not masquerade as a failed database save.
        try:
            xray.operations.sync_node_device_policies(dbnode.id)
        except Exception:
            from app import logger
            logger.warning("Node %s egress applied; device reconciliation pending", dbnode.id)
        return public_egress(db, dbnode)
    finally:
        lock.release()
