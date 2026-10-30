"""Authorization and durable, idempotent grant acceptance for dedicated Nodes."""
import hashlib
import json
from datetime import datetime
from time import time
from sqlalchemy import update
from app.db.models import (Admin as DBAdmin, DedicatedNodeAdmin, DedicatedNodeGrant,
                           DedicatedNodeOperation, Node, User)

CAPABILITY = "dedicated-node-access-v1"
SUPPORTED_PROTOCOLS = frozenset(("vless", "vmess", "trojan"))


class AccessError(RuntimeError):
    def __init__(self, code, status=409):
        self.code, self.status = code, status


def validate_distinct_core(db, address, mode, excluding=None):
    normalized = address.strip().strip("[]").rstrip(".").lower()
    collisions = [node for node in db.query(Node).all() if node.id != excluding
                  and node.address.strip().strip("[]").rstrip(".").lower() == normalized]
    if collisions and (mode == "restricted" or any(node.access_mode == "restricted" for node in collisions)):
        raise ValueError("Dedicated Nodes require a distinct server/core, not a duplicate Node address")


def is_usable(user):
    status = getattr(user.status, "value", user.status)
    return (status in {"active", "on_hold"}
            and (not user.expire or user.expire > time())
            and (not user.data_limit or user.used_traffic < user.data_limit))


def grant_matches(grant, user):
    return (grant is not None and grant.user_id == user.id and grant.username == user.username
            and grant.user_created_at == user.created_at)


def has_grant(db, node_id, user):
    return grant_matches(db.get(DedicatedNodeGrant, (node_id, user.id)), user)


def can_allocate(db, actor, node_id):
    if actor.is_sudo:
        return True
    admin = db.query(DBAdmin).filter(DBAdmin.username == actor.username).first()
    return admin is not None and db.get(DedicatedNodeAdmin, (node_id, admin.id)) is not None


def authorized_user(db, actor, username):
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise AccessError("USER_NOT_FOUND", 404)
    if not actor.is_sudo and (user.admin is None or user.admin.username != actor.username):
        raise AccessError("USER_FORBIDDEN", 403)
    return user


def authorized_node(db, actor, node_id):
    node = db.get(Node, node_id)
    if node is None:
        raise AccessError("NODE_NOT_FOUND", 404)
    if not can_allocate(db, actor, node_id):
        raise AccessError("NODE_ALLOCATION_FORBIDDEN", 403)
    return node


def allowed_identities(db, node):
    if node.access_mode == "public":
        return None
    if node.access_mode != "restricted":
        raise AccessError("INVALID_NODE_ACCESS_POLICY", 503)
    users = db.query(User).join(DedicatedNodeGrant, DedicatedNodeGrant.user_id == User.id).filter(
        DedicatedNodeGrant.node_id == node.id,
        DedicatedNodeGrant.username == User.username,
        DedicatedNodeGrant.user_created_at == User.created_at).all()
    return {f"{user.id}.{user.username}" for user in users if is_usable(user)}


def identity_from_email(email):
    if not isinstance(email, str):
        return None
    parts = email.split(".")
    if len(parts) not in (2, 3) or not parts[0].isdigit():
        return None
    if len(parts) == 3 and (not parts[2].startswith("device-") or len(parts[2]) != 23):
        return None
    return ".".join(parts[:2])


def policy_snapshot(db, node_id):
    node = db.get(Node, node_id)
    if node is None:
        raise AccessError("NODE_NOT_FOUND", 404)
    return node.access_mode, node.access_revision, allowed_identities(db, node)


def catalog(db, actor):
    from app.xray.node_access import runtime_state
    return {"capability": CAPABILITY, "nodes": [
        {"id": node.id, "name": node.name,
         "enabled": getattr(node.status, "value", node.status) != "disabled",
         "status": getattr(node.status, "value", node.status),
         "supported_protocols": sorted(SUPPORTED_PROTOCOLS),
         **runtime_state(node)}
        for node in db.query(Node).filter(Node.access_mode == "restricted").order_by(Node.id)
        if can_allocate(db, actor, node.id)]}


def state(db, actor, username, node_id, operation=None):
    from app.xray.node_access import runtime_state
    user = authorized_user(db, actor, username)
    node = authorized_node(db, actor, node_id)
    runtime = runtime_state(node)
    granted = node.access_mode == "restricted" and has_grant(db, node_id, user)
    supported = any(getattr(protocol, "value", protocol) in SUPPORTED_PROTOCOLS and tags
                    for protocol, tags in user.inbounds.items())
    result = {"node_id": node_id, "username": user.username, "granted": granted,
              "effective": granted and is_usable(user) and supported and runtime["sync_state"] == "synced",
              **runtime}
    if operation is not None:
        result.update(operation_id=operation.operation_id, requested_granted=operation.granted,
                      external_reference=operation.external_reference)
    if granted and not is_usable(user):
        result["detail"] = "USER_INACTIVE_EXPIRED_OR_OVER_QUOTA"
    elif granted and not supported:
        result["detail"] = "NO_SUPPORTED_PROTOCOL"
    return result


def change_grant(db, actor, username, node_id, request, granted):
    """No counters/expiry/credentials are changed. Replays never re-grant."""
    user = authorized_user(db, actor, username)
    node = authorized_node(db, actor, node_id)
    if node.access_mode != "restricted":
        raise AccessError("NODE_IS_NOT_DEDICATED")
    # No-op write serializes SQLite writers too; refresh after taking the lock.
    db.execute(update(Node).where(Node.id == node_id).values(access_revision=Node.access_revision))
    db.refresh(node)
    db.refresh(user)
    # Ownership/delegation can have changed since the initial read.
    authorized_user(db, actor, username)
    authorized_node(db, actor, node_id)
    if node.access_mode != "restricted":
        raise AccessError("NODE_IS_NOT_DEDICATED")
    payload = {"username": user.username, "node_id": node_id, "granted": granted,
               "actor": actor.username, "external_reference": request.external_reference}
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    previous = db.get(DedicatedNodeOperation, request.operation_id)
    if previous is not None:
        if previous.payload_sha256 != digest:
            raise AccessError("OPERATION_PAYLOAD_MISMATCH")
        if (previous.user_id != user.id or previous.username != user.username
                or previous.user_created_at != user.created_at):
            raise AccessError("USER_IDENTITY_CHANGED")
        db.commit()
        return previous, True
    row = db.get(DedicatedNodeGrant, (node_id, user.id))
    old_granted = grant_matches(row, user)
    if granted and not old_granted:
        if row is not None:
            db.delete(row)
            db.flush()
        db.add(DedicatedNodeGrant(node_id=node_id, user_id=user.id, username=user.username,
                                 user_created_at=user.created_at, granted_by=actor.username))
    elif not granted and row is not None:
        db.delete(row)
    if old_granted != granted:
        node.access_revision += 1
    operation = DedicatedNodeOperation(operation_id=request.operation_id, payload_sha256=digest,
        node_id=node_id, user_id=user.id, username=user.username, user_created_at=user.created_at,
        granted=granted, actor=actor.username, external_reference=request.external_reference,
        revision=node.access_revision)
    db.add(operation)
    db.commit()
    return operation, False


def filter_hosts(hosts, username=None, created_at=None, protocol=None):
    """Fail closed for unbound/ambiguous dedicated endpoints, including relays."""
    if not hosts:
        return hosts
    from app.db import GetDB
    with GetDB() as db:
        nodes = {node.id: node for node in db.query(Node).all()}
        restricted = {key for key, node in nodes.items() if node.access_mode != "public"}
        if not restricted:
            return hosts
        by_address = {}
        for node in nodes.values():
            by_address.setdefault(node.address.strip().lower(), set()).add(node.id)
        user = db.query(User).filter(User.username == username).first() if username else None
        if user is not None and (created_at is None or user.created_at != created_at):
            user = None
        allowed = {key for key in restricted if nodes[key].access_mode == "restricted"
                   and user is not None and is_usable(user) and has_grant(db, key, user)}
        result = []
        for host in hosts:
            node_id = host.get("node_id")
            if node_id is not None:
                if node_id not in nodes:
                    continue
                if node_id in restricted and (node_id not in allowed or protocol not in SUPPORTED_PROTOCOLS):
                    continue
            else:
                # Legacy manually entered addresses must not bypass ownership.
                addresses = host.get("address", [])
                if isinstance(addresses, str):
                    addresses = addresses.split(",")
                matches = set().union(*(by_address.get(address.strip().lower(), set()) for address in addresses))
                if matches & restricted:
                    continue  # Require an explicit node_id, including comma-separated Hosts.
            result.append(host)
        return result
