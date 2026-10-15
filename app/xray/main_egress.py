"""Main-only egress storage and a private runtime overlay; never a Node config."""
import base64
import hashlib
from copy import deepcopy

from cryptography.fernet import Fernet

from app.db import crud
from app.db.models import MainEgress
from app.xray.managed_outbounds import apply_managed_outbounds
from app.xray.node_egress import validate_egress


def _cipher(db):
    secret = crud.get_jwt_secret_key(db)
    if not secret:
        raise RuntimeError("Main egress encryption key unavailable")
    key = hashlib.sha256(b"marzban-main-egress-v1:" + secret.encode("utf8")).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def read_profile(db):
    row = db.get(MainEgress, 1)
    if row is None:
        return None
    return validate_egress({"protocol": row.protocol, "udp_mode": row.udp_mode,
        "server": row.server, "port": row.port, "username": row.username,
        "password": _cipher(db).decrypt(row.encrypted_password.encode("ascii")).decode("utf8")
        if row.encrypted_password else None})


def public_profile(db):
    row = db.get(MainEgress, 1)
    if row is None:
        return {"configured": False}
    return {"configured": True, "protocol": row.protocol, "udp_mode": row.udp_mode,
            "server": row.server, "port": row.port, "username": row.username,
            "has_password": bool(row.encrypted_password)}


def prepare_profile(db, draft):
    candidate = dict(draft)
    row = db.get(MainEgress, 1)
    if (row is not None and candidate.get("username") and row.username == candidate["username"]
            and not candidate.get("password") and row.encrypted_password):
        candidate["password"] = _cipher(db).decrypt(row.encrypted_password.encode("ascii")).decode("utf8")
    return validate_egress(candidate)


def persist_profile(db, value):
    """Called only after local core readiness; caller owns commit/rollback."""
    row = db.get(MainEgress, 1)
    if value is None:
        if row is not None:
            db.delete(row)
        db.commit()
        return
    value = validate_egress(value)
    if row is None:
        row = MainEgress(id=1)
        db.add(row)
    row.protocol, row.udp_mode = value["protocol"], value["udp_mode"]
    row.server, row.port, row.username = value["server"], value["port"], value["username"]
    row.encrypted_password = (_cipher(db).encrypt(value["password"].encode("utf8")).decode("ascii")
                              if value["password"] is not None else None)
    db.commit()


def for_main(base, profile):
    """Never edit xray.config or the object shared with remote Node startup."""
    runtime = deepcopy(base)
    if profile is None:
        return runtime
    if "marzban_node_extensions" in runtime:
        raise ValueError("Shared base config must not contain a managed Node extension")
    profile = validate_egress(profile)
    runtime["marzban_node_extensions"] = {"outbounds": [profile],
                                         "default_outbound_tag": profile["tag"]}
    apply_managed_outbounds(runtime)
    return runtime
