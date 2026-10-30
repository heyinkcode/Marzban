"""Per-Node fail-closed account filtering, without changing Node wire protocols."""
from copy import deepcopy
from app.db.dedicated_access import SUPPORTED_PROTOCOLS, identity_from_email


def scope_config(config, identities):
    if identities is None:
        return config
    result = deepcopy(config)
    # Dedicated Nodes expose only independently authenticated business inbounds.
    result["inbounds"] = [inbound for inbound in result.get("inbounds", [])
                          if inbound.get("tag") == "API_INBOUND"
                          or inbound.get("protocol") in SUPPORTED_PROTOCOLS]
    for inbound in result["inbounds"]:
        if inbound.get("tag") == "API_INBOUND":
            continue
        settings = inbound.setdefault("settings", {})
        settings["clients"] = [client for client in settings.get("clients", [])
                               if identity_from_email(client.get("email")) in identities]
    return result


def prepare_config(config, node_id, dbnode=None):
    from app.db import GetDB
    from app.db.dedicated_access import policy_snapshot
    if dbnode is not None and getattr(dbnode, "access_mode", "public") == "public":
        revision = getattr(dbnode, "access_revision", 0)
        return config, "public", revision if isinstance(revision, int) else 0
    with GetDB() as db:
        mode, revision, identities = policy_snapshot(db, node_id)
    if mode == "restricted":
        # Do not trust manually embedded clients, even if they spoof a granted
        # user's email. Rebuild credentials from the current database only.
        config = config.copy()
        for inbound in config.get("inbounds", []):
            if inbound.get("protocol") in SUPPORTED_PROTOCOLS:
                inbound.setdefault("settings", {})["clients"] = []
        config = config.include_db_users()
    return scope_config(config, identities), mode, revision


def acknowledge(node, mode, revision):
    node.access_mode = mode
    node.access_applied_revision = revision
    node.access_sync_error = False


def runtime_state(dbnode):
    from app import xray
    node = xray.nodes.get(dbnode.id)
    revision = dbnode.access_revision
    applied = getattr(node, "access_applied_revision", None) if node is not None else None
    # A database write or an old acknowledgement alone is not runtime readiness.
    ready = False
    if node is not None and getattr(dbnode.status, "value", dbnode.status) != "disabled":
        try:
            ready = node.connected and node.started
        except Exception:
            pass
    synced = ready and applied == revision
    error = bool(getattr(node, "access_sync_error", False)) if node is not None else False
    return {"policy_revision": revision, "applied_revision": applied,
            "sync_state": "synced" if synced else "error" if error else "pending"}


def reconcile(node_id):
    """Restart only this Node from authoritative DB state; never the main core."""
    from app import xray
    from app.db import GetDB
    from app.db.models import Node
    from app.xray.node_egress import for_node
    from app.xray.node_egress_store import read_egress
    with xray.operations.node_lifecycle_lock(node_id):
        node = xray.nodes.get(node_id)
        if node is None:
            return
        with GetDB() as db:
            dbnode = db.get(Node, node_id)
            if dbnode is None or getattr(dbnode.status, "value", dbnode.status) == "disabled":
                return
            if runtime_state(dbnode)["sync_state"] == "synced":
                return
            egress = read_egress(db, dbnode)
        try:
            if not node.connected or not node.started:
                return
            base, mode, revision = prepare_config(xray.config.include_db_users(), node_id)
            node.access_mode = mode
            health = node.get_health() if egress and egress.get("udp_mode", "legacy") != "legacy" else None
            node.restart(for_node(base, egress, health))
            if not node.started:
                raise RuntimeError("Node readiness not confirmed")
            acknowledge(node, mode, revision)
            xray.operations.sync_node_device_policies(node_id)
        except Exception:
            node.access_sync_error = True
            from app import logger
            logger.warning("Node %s access synchronization unconfirmed", node_id)


class GuardedNodeAPI:
    """Fence every incremental credential add against current authoritative ACL."""
    def __init__(self, node_id, api):
        self.node_id, self.api = node_id, api

    def __getattr__(self, name):
        return getattr(self.api, name)

    def add_inbound_user(self, tag, user, timeout=30):
        from app import xray
        from app.db import GetDB
        from app.db.dedicated_access import policy_snapshot
        with xray.operations.node_lifecycle_lock(self.node_id):
            live = xray.nodes.get(self.node_id)
            if live is not None and getattr(live, "access_mode", "public") == "public":
                return self.api.add_inbound_user(tag=tag, user=user, timeout=timeout)
            with GetDB() as db:
                mode, _, identities = policy_snapshot(db, self.node_id)
                # A queued device/account update must not revive credentials
                # revoked or rotated after its snapshot was captured.
                if mode == "restricted" and identity_from_email(user.email) in identities:
                    from app.db.models import User
                    from hmac import compare_digest
                    parts = user.email.split(".")
                    current = db.get(User, int(parts[0]))
                    inbound = xray.config.inbounds_by_tag.get(tag, {})
                    protocol = inbound.get("protocol")
                    tags = current.inbounds.get(protocol, []) if current is not None else []
                    if tag not in tags:
                        identities = identities - {identity_from_email(user.email)}
                    else:
                        proxy = next((row for row in current.proxies if row.type == protocol), None)
                        settings = dict(proxy.settings) if proxy is not None else {}
                        if len(parts) == 3:
                            matches = [device for device in current.devices if device.revoked_at is None
                                       and parts[2] == "device-" + device.hwid_hash[:16]]
                            if len(matches) != 1:
                                return None
                            settings.update((matches[0].credentials or {}).get(str(getattr(protocol, "value", protocol)), {}))
                        key = "password" if protocol == "trojan" else "id"
                        if not settings.get(key) or not compare_digest(str(settings[key]), str(getattr(user, key, ""))):
                            return None
            if mode == "restricted":
                inbound = xray.config.inbounds_by_tag.get(tag, {})
                if (inbound.get("protocol") not in SUPPORTED_PROTOCOLS
                        or identity_from_email(user.email) not in identities):
                    try:
                        self.api.remove_inbound_user(tag=tag, email=user.email, timeout=timeout)
                    except xray.exc.EmailNotFoundError:
                        pass
                    return None
            return self.api.add_inbound_user(tag=tag, user=user, timeout=timeout)


def guard_api(node_id, node):
    # Always wrap: a queued public-node add must not bypass a later restriction.
    return GuardedNodeAPI(node_id, node.api)
