"""Real SQLite/WAL + HTTP/Bearer tests; Node transport is explicitly simulated."""
import copy
import importlib.util
import json
import socket
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

import test_user_device_limit as bootstrap
from alembic.migration import MigrationContext
from alembic.operations import Operations
from fastapi import FastAPI
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import uvicorn
from app import xray
from app.db import crud
from app.db.base import Base
from app.db import dedicated_access as service
from app.db.models import (Admin, DedicatedNodeAdmin, DedicatedNodeGrant, DedicatedNodeOperation,
                           Node, Proxy, User, UserDevice, UserUsageResetLogs)
from app.models.dedicated_access import DedicatedAccessRequest
from app.models.node import NodeCreate
from app.models.user import UserResponse
from app.routers import dedicated_access as routes
from app.subscription.share import generate_subscription
from app.utils import jwt
from app.xray import node_access
from app.xray.config import XRayConfig
from test_node_relay import original_host

TAG = "PRIVATE_TEST"
ROOT = Path(__file__).resolve().parents[1]


class FakeNode:
    """A simulated, acknowledged remote restart. Real core tests are separate."""
    def __init__(self):
        self.connected, self.started, self.access_mode = True, True, "restricted"
        self.restarts, self.fail, self.fail_after_apply = [], False, False
        self.api = Mock()
    def restart(self, config):
        if self.fail:
            raise TimeoutError("simulated transport failure")
        self.restarts.append(copy.deepcopy(config))
        if self.fail_after_apply:
            raise TimeoutError("simulated lost acknowledgement")
    def set_device_policies(self, policies):
        self.policies = copy.deepcopy(policies)
        return {"accepted": True, "policy_count": len(policies),
                "policy_enforcement": "subscription_request_and_node_credentials",
                "direct_connection_enforced": True}


class DedicatedAccessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dedicated-access-")
        self.addCleanup(self.temp.cleanup)
        self.engine = create_engine("sqlite:///" + str(Path(self.temp.name) / "fixture.db"),
            connect_args={"check_same_thread": False, "timeout": 15})
        self.addCleanup(self.engine.dispose)
        with self.engine.begin() as conn:
            conn.exec_driver_sql("PRAGMA journal_mode=WAL")
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine)
        self.db = self.sessions()
        self.addCleanup(self.db.close)
        self.admin = Admin(username="site_admin", hashed_password="unused", is_sudo=False)
        self.other_admin = Admin(username="other_admin", hashed_password="unused", is_sudo=False)
        self.root_admin = Admin(username="root_admin", hashed_password="unused", is_sudo=True)
        self.private = Node(name="Dedicated A", address="dedicated.example.invalid", port=62050,
                            api_port=62051, status="connected", access_mode="restricted", access_revision=1)
        self.public = Node(name="Public A", address="public.example.invalid", port=62050,
                           api_port=62051, status="connected")
        self.db.add_all([self.admin, self.other_admin, self.root_admin, self.private, self.public])
        self.db.commit()
        self.user = self.make_user("alice", self.admin)
        self.other_user = self.make_user("bob", self.other_admin)
        self.db.add(DedicatedNodeAdmin(node_id=self.private.id, admin_id=self.admin.id))
        self.db.commit()
        self.remote = FakeNode()
        self.public_remote = FakeNode()
        self.public_remote.access_mode = "public"
        self.nodes = {self.private.id: self.remote, self.public.id: self.public_remote}
        self.config = XRayConfig({"inbounds": [{"tag": TAG, "listen": "127.0.0.1", "port": 18443,
            "protocol": "vless", "settings": {"clients": [], "decryption": "none"},
            "streamSettings": {"network": "tcp"}}], "outbounds": [{"tag": "DIRECT", "protocol": "freedom"}]})
        self.hosts = {TAG: [{**original_host("Public", self.public.address), "node_id": self.public.id},
                           {**original_host("Dedicated", self.private.address), "node_id": self.private.id}]}
        for item in (patch("app.db.SessionLocal", self.sessions), patch.object(xray, "nodes", self.nodes),
                     patch.object(xray, "config", self.config), patch.object(xray, "hosts", self.hosts),
                     patch.object(jwt, "get_secret_key", return_value="isolated-http-test-only-key")):
            item.start()
            self.addCleanup(item.stop)
        self.actor = SimpleNamespace(username="site_admin", is_sudo=False)
        self.sudo = SimpleNamespace(username="root_admin", is_sudo=True)
        self.start_http()

    def make_user(self, name, admin):
        user = User(username=name, status="active", created_at=datetime.utcnow() - timedelta(days=1),
                    expire=int(time.time()) + 86400, data_limit=100000, used_traffic=123,
                    admin_id=admin.id, device_limit=2, device_limit_action="reject_new",
                    data_limit_reset_strategy="no_reset")
        user.proxies = [Proxy(type="vless", settings={"id": str(uuid4()), "flow": ""})]
        user.usage_logs = [UserUsageResetLogs(used_traffic_at_reset=0, reset_at=user.created_at)]
        self.db.add(user)
        self.db.commit()
        return user

    def start_http(self):
        app = FastAPI()
        app.include_router(routes.router)
        self.server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=0, log_level="critical", lifespan="off"))
        self.listener = socket.socket()
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen(50)
        self.base = f"http://127.0.0.1:{self.listener.getsockname()[1]}"
        self.thread = threading.Thread(target=lambda: self.server.run(sockets=[self.listener]), daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_http)
        deadline = time.monotonic() + 5
        while not self.server.started and time.monotonic() < deadline:
            time.sleep(.01)
        self.assertTrue(self.server.started)

    def stop_http(self):
        self.server.should_exit = True
        self.thread.join(5)
        self.listener.close()
        self.assertFalse(self.thread.is_alive())

    def http(self, method, path, body=None, actor="site_admin", token=None):
        headers = {"Content-Type": "application/json"}
        if actor is not None:
            headers["Authorization"] = "Bearer " + (token or jwt.create_admin_token(actor, actor == "root_admin"))
        request = urllib.request.Request(self.base + path, method=method, headers=headers,
            data=json.dumps(body).encode() if body is not None else None)
        try:
            response = urllib.request.urlopen(request, timeout=10)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            return response.status, json.load(response), response.headers

    def body(self):
        return {"operation_id": str(uuid4()), "external_reference": "generic-site-order-test"}

    def access(self, method="PUT", user="alice", node=None, body=None, **kwargs):
        return self.http(method, f"/api/user/{user}/dedicated-nodes/{node or self.private.id}",
                         body if body is not None else self.body(), **kwargs)

    def refresh(self):
        self.db.expire_all()
        return self.db.get(User, self.user.id)

    def test_real_http_auth_catalog_and_no_infrastructure_secrets(self):
        for token in (None, "invalid-bearer"):
            code, _, _ = self.http("GET", "/api/dedicated-nodes", actor=None if token is None else "site_admin", token=token)
            self.assertEqual(code, 401)
        code, body, headers = self.http("GET", "/api/dedicated-nodes")
        self.assertEqual(code, 200)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual([node["id"] for node in body["nodes"]], [self.private.id])
        raw = json.dumps(body)
        for hidden in (self.private.address, "62050", "62051", "password", "certificate", "hashed_password"):
            self.assertNotIn(hidden, raw)

    def test_website_flow_grant_receipt_refresh_subscription_and_revoke(self):
        before = generate_subscription(UserResponse.model_validate(self.refresh()), "v2ray", False, False)
        self.assertNotIn(self.private.address, before)
        self.assertIn(self.public.address, before)
        body = self.body()
        code, result, _ = self.access(body=body)
        self.assertEqual(code, 200)
        self.assertTrue(result["effective"])
        self.assertEqual(result["sync_state"], "synced")
        self.assertEqual(self.http("GET", "/api/dedicated-node-operations/" + body["operation_id"])[1], result)
        after = generate_subscription(UserResponse.model_validate(self.refresh()), "v2ray", False, False)
        self.assertIn(self.private.address, after)
        self.assertIn(self.public.address, after)
        self.assertEqual(len(self.remote.restarts), 1)
        self.assertEqual(self.public_remote.restarts, [])
        _, revoked, _ = self.access("DELETE")
        self.assertFalse(revoked["granted"])
        self.assertFalse(revoked["effective"])
        final = generate_subscription(UserResponse.model_validate(self.refresh()), "v2ray", False, False)
        self.assertNotIn(self.private.address, final)
        self.assertIn(self.public.address, final)

    def test_no_quota_usage_expiry_uuid_history_or_other_user_mutations(self):
        saved = {column.name: getattr(self.user, column.name) for column in User.__table__.columns}
        credentials = copy.deepcopy(self.user.proxies[0].settings)
        logs = [(row.id, row.used_traffic_at_reset) for row in self.user.usage_logs]
        self.assertEqual(self.access()[0], 200)
        self.assertEqual(self.access("DELETE")[0], 200)
        current = self.refresh()
        self.assertEqual(saved, {key: getattr(current, key) for key in saved})
        self.assertEqual(current.proxies[0].settings, credentials)
        self.assertEqual(logs, [(row.id, row.used_traffic_at_reset) for row in current.usage_logs])
        self.assertEqual(self.db.get(User, self.other_user.id).used_traffic, 123)

    def test_three_users_three_lines_subscription_and_runtime_matrix(self):
        """A: 1+2, B: 1, C: 1+2+3; public endpoints never inherit this ACL."""
        users = [self.make_user(name, self.admin) for name in ("user_a", "user_b", "user_c")]
        lines = [self.private]
        for number in (2, 3):
            line = crud.create_node(self.db, NodeCreate(name=f"Dedicated {number}",
                address=f"line-{number}.example.invalid", access_mode="restricted"))
            line.status = "connected"
            self.db.commit()
            lines.append(line)
            self.nodes[line.id] = FakeNode()
            self.hosts[TAG].append({**original_host(line.name, line.address), "node_id": line.id})
        expected = [{0, 1}, {0}, {0, 1, 2}]
        for user, indexes in zip(users, expected):
            for index in indexes:
                code, receipt, _ = self.access(user=user.username, node=lines[index].id, actor="root_admin")
                self.assertEqual(code, 200)
                self.assertTrue(receipt["effective"])

        def verify_matrix():
            self.db.expire_all()
            for user, indexes in zip(users, expected):
                current = self.db.get(User, user.id)
                for fmt in ("v2ray", "v2ray-json", "clash-meta", "sing-box"):
                    with self.subTest(user=current.username, format=fmt, expected=indexes):
                        subscription = generate_subscription(UserResponse.model_validate(current), fmt, False, False)
                        self.assertIn(self.public.address, subscription)
                        for index, line in enumerate(lines):
                            self.assertEqual(line.address in subscription, index in indexes)
                self.assertEqual((current.used_traffic, current.data_limit), (123, 100000))
            for index, line in enumerate(lines):
                # Reconstruct initial/reconnected configs, not just the last in-memory acknowledgement.
                scoped, mode, _ = node_access.prepare_config(self.config.include_db_users(), line.id)
                clients = next(item for item in scoped["inbounds"] if item["tag"] == TAG)["settings"]["clients"]
                self.assertEqual(mode, "restricted")
                self.assertEqual({item["email"] for item in clients},
                    {f"{user.id}.{user.username}" for user, indexes in zip(users, expected) if index in indexes})
            self.assertEqual(self.public_remote.restarts, [])

        verify_matrix()
        self.assertEqual(self.access("DELETE", user=users[0].username, node=lines[1].id, actor="root_admin")[0], 200)
        expected[0] = {0}
        verify_matrix()
        # A fresh DB session and empty runtime acknowledgement cannot restore a revoked grant.
        for line in lines:
            self.nodes[line.id].access_applied_revision = None
            node_access.reconcile(line.id)
        verify_matrix()

    def test_owner_and_node_delegation_checked_before_writes(self):
        self.assertEqual(self.access(user="bob")[0], 403)
        self.assertEqual(self.access(actor="other_admin")[0], 403)
        self.assertEqual(self.access(node=self.public.id)[0], 403)
        self.assertEqual(self.access(node=self.public.id, actor="root_admin")[0], 409)
        self.assertEqual(self.db.query(DedicatedNodeGrant).count(), 0)
        self.assertEqual(self.remote.restarts, [])

    def test_repeated_operation_and_concurrent_delivery_only_grant_once(self):
        body = self.body()
        with ThreadPoolExecutor(max_workers=3) as pool:
            results = list(pool.map(lambda _: self.access(body=body), range(3)))
        self.assertTrue(all(code == 200 for code, _, _ in results))
        self.db.expire_all()
        self.assertEqual(self.db.query(DedicatedNodeOperation).count(), 1)
        self.assertEqual(self.db.query(DedicatedNodeGrant).count(), 1)
        self.assertEqual(len(self.remote.restarts), 1)

    def test_changed_payload_or_action_cannot_reuse_operation_id(self):
        body = self.body()
        self.access(body=body)
        self.assertEqual(self.access("DELETE", body=body)[0], 409)
        changed = {**body, "external_reference": "different"}
        self.assertEqual(self.access(body=changed)[0], 409)
        self.assertTrue(self.access("GET")[1]["granted"])

    def test_old_grant_replay_after_revocation_never_regrants(self):
        old = self.body()
        self.access(body=old)
        self.access("DELETE")
        code, result, _ = self.access(body=old)
        self.assertEqual(code, 200)
        self.assertTrue(result["requested_granted"])
        self.assertFalse(result["granted"])
        self.assertFalse(result["effective"])
        self.assertEqual(len(self.remote.restarts), 2)

    def test_offline_node_is_accepted_pending_never_marked_effective(self):
        self.remote.connected = False
        body = self.body()
        code, result, _ = self.access(body=body)
        self.assertEqual(code, 202)
        self.assertTrue(result["granted"])
        self.assertFalse(result["effective"])
        self.assertEqual(result["sync_state"], "pending")
        self.assertEqual(self.remote.restarts, [])
        self.remote.connected = True
        node_access.reconcile(self.private.id)
        self.assertTrue(self.access("GET")[1]["effective"])

    def test_lost_ack_keeps_audit_readonly_get_never_restarts(self):
        self.remote.fail_after_apply = True
        body = self.body()
        code, result, _ = self.access(body=body)
        self.assertEqual(code, 202)
        self.assertEqual(result["sync_state"], "error")
        self.assertEqual(len(self.remote.restarts), 1)
        for _ in range(3):
            self.http("GET", "/api/dedicated-node-operations/" + body["operation_id"])
        self.assertEqual(len(self.remote.restarts), 1)
        self.remote.fail_after_apply = False
        self.access(body=body)  # Explicit resume, same operation; current policy only.
        self.assertTrue(self.access("GET")[1]["effective"])
        self.assertEqual(self.db.query(DedicatedNodeOperation).count(), 1)

    def test_disabled_expired_or_overquota_grants_do_not_bypass_account_state(self):
        for values in ({"status": "disabled"}, {"status": "expired"}, {"expire": 1}, {"used_traffic": 100000}):
            for key, value in values.items():
                setattr(self.user, key, value)
            self.db.commit()
            code, result, _ = self.access()
            self.assertEqual(code, 200)
            self.assertFalse(result["effective"])
            self.assertEqual(node_access.prepare_config(self.config.include_db_users(), self.private.id)[0]["inbounds"][1]["settings"]["clients"], [])
            self.user.status, self.user.expire, self.user.used_traffic = "active", int(time.time()) + 86400, 123
            self.db.commit()

    def test_device_and_legacy_credentials_share_same_node_permission(self):
        device = UserDevice(user_id=self.user.id, hwid_hash="a" * 64,
                            credentials={"vless": {"id": str(uuid4())}})
        self.db.add(device)
        self.db.commit()
        self.access()
        clients = next(item for item in self.remote.restarts[-1]["inbounds"] if item["tag"] == TAG)["settings"]["clients"]
        self.assertEqual({row["email"] for row in clients}, {f"{self.user.id}.alice", f"{self.user.id}.alice.device-{'a' * 16}"})
        self.assertNotIn(f"{self.other_user.id}.bob", {row["email"] for row in clients})
        self.assertEqual([row["user"] for row in self.remote.policies], [f"{self.user.id}.alice"])

    def test_incremental_add_checks_current_acl_even_when_target_was_public(self):
        self.remote.access_mode = "public"
        api = node_access.guard_api(self.private.id, self.remote)
        self.remote.access_mode = "restricted"
        account = SimpleNamespace(email=f"{self.other_user.id}.bob")
        api.add_inbound_user(TAG, account)
        self.remote.api.add_inbound_user.assert_not_called()
        self.remote.api.remove_inbound_user.assert_called_once()
        self.access()
        api.add_inbound_user(TAG, SimpleNamespace(email=f"{self.user.id}.alice", id=self.user.proxies[0].settings["id"]))
        self.remote.api.add_inbound_user.assert_called_once()

    def test_all_subscription_formats_filter_and_preserve_original_credentials(self):
        for fmt in ("v2ray", "v2ray-json", "clash", "clash-meta", "sing-box", "outline"):
            with self.subTest(format=fmt):
                before = generate_subscription(UserResponse.model_validate(self.refresh()), fmt, False, False)
                self.assertNotIn(self.private.address, before)
        self.access()
        # Ordinary Clash/Outline cannot encode VLESS; they intentionally stay empty.
        for fmt in ("v2ray", "v2ray-json", "clash-meta", "sing-box"):
            after = generate_subscription(UserResponse.model_validate(self.refresh()), fmt, False, False)
            self.assertIn(self.private.address, after)
            self.assertIn(self.user.proxies[0].settings["id"], after)

    def test_unbound_legacy_dedicated_alias_requires_explicit_host_binding(self):
        self.access()
        unbound = original_host("Old dedicated", self.private.address)
        self.assertEqual(service.filter_hosts([unbound], self.user.username, self.user.created_at, "vless"), [])
        bound = {**unbound, "node_id": self.private.id}
        self.assertEqual(service.filter_hosts([bound], self.user.username, self.user.created_at, "vless"), [bound])
        self.assertEqual(service.filter_hosts([bound], "alice", self.user.created_at + timedelta(seconds=1), "vless"), [])

    def test_relay_keeps_target_identity_and_cannot_inherit_source_permission(self):
        from app.xray.node_relay import rewrite_hosts
        host = {**self.hosts[TAG][1]}
        relayed = rewrite_hosts([host], [{"target_address": self.private.address, "target_port": 8443,
            "entry_address": self.public.address, "listen_port": 18443}], 8443)
        self.assertEqual(relayed[0]["node_id"], self.private.id)
        self.assertEqual(service.filter_hosts(relayed, "alice", self.user.created_at, "vless"), [])
        self.access()
        self.assertEqual(service.filter_hosts(relayed, "alice", self.user.created_at, "vless"), relayed)

    def test_unknown_static_accounts_and_unauthenticated_inbounds_are_removed(self):
        config = copy.deepcopy(self.config)
        config["inbounds"].append({"tag": "NOAUTH", "protocol": "socks", "settings": {"auth": "noauth"}})
        business = next(item for item in config["inbounds"] if item["tag"] == TAG)
        business["settings"]["clients"] = [{"email": "static", "id": str(uuid4())},
                                           {"email": f"{self.user.id}.alice", "id": str(uuid4())}]
        scoped = node_access.scope_config(config, {f"{self.user.id}.alice"})
        self.assertNotIn("NOAUTH", {item["tag"] for item in scoped["inbounds"]})
        self.assertEqual(len(scoped["inbounds"][1]["settings"]["clients"]), 1)
        self.assertEqual(len(config["inbounds"][1]["settings"]["clients"]), 2)

    def test_only_sudo_can_delegate_and_revoking_delegation_does_not_revoke_users(self):
        path = f"/api/admin/other_admin/dedicated-nodes/{self.private.id}"
        self.assertEqual(self.http("PUT", path)[0], 403)
        self.assertEqual(self.http("PUT", path, actor="root_admin")[0], 200)
        self.assertEqual(self.access(user="bob", actor="other_admin")[0], 200)
        self.assertEqual(self.http("DELETE", path, actor="root_admin")[0], 200)
        self.assertEqual(self.access("DELETE", user="bob", actor="other_admin")[0], 403)
        self.assertTrue(self.access("GET", user="bob", actor="root_admin")[1]["granted"])

    def test_policy_transition_requires_connection_and_public_confirmation(self):
        path = f"/api/node/{self.public.id}/access"
        self.public_remote.connected = False
        self.assertEqual(self.http("PUT", path, {"access_mode": "restricted"}, actor="root_admin")[0], 409)
        self.public_remote.connected = True
        self.assertEqual(self.http("PUT", path, {"access_mode": "restricted"}, actor="root_admin")[0], 200)
        self.assertEqual(self.http("PUT", path, {"access_mode": "public"}, actor="root_admin")[0], 409)
        self.assertEqual(self.http("PUT", path, {"access_mode": "public", "confirm_public_access": True}, actor="root_admin")[0], 200)

    def test_new_restricted_node_created_before_any_runtime_or_user_grant(self):
        node = crud.create_node(self.db, NodeCreate(name="Dedicated new", address="new.example.invalid",
                               access_mode="restricted", usage_coefficient=5))
        self.assertEqual((node.access_mode, node.access_revision, node.usage_coefficient), ("restricted", 1, 5))
        self.assertEqual(service.allowed_identities(self.db, node), set())
        initial, mode, _ = node_access.prepare_config(self.config.include_db_users(), node.id)
        self.assertEqual(mode, "restricted")
        self.assertEqual(next(item for item in initial["inbounds"] if item["tag"] == TAG)["settings"]["clients"], [])
        ordinary = crud.create_node(self.db, NodeCreate(name="Ordinary new", address="ordinary.example.invalid"))
        self.assertEqual(ordinary.access_mode, "public")
        self.assertIsNone(service.allowed_identities(self.db, ordinary))

    def test_invalid_or_unknown_request_fields_are_rejected(self):
        for body in ({}, {"operation_id": "not-uuid"}, {**self.body(), "paid": True},
                     {**self.body(), "data_limit": 999999}, {**self.body(), "external_reference": "x" * 129}):
            self.assertEqual(self.access(body=body)[0], 422)
        self.assertEqual(self.db.query(DedicatedNodeOperation).count(), 0)

    def test_new_host_binding_survives_rename_before_background_creation(self):
        from app.routers.node import add_host_if_needed
        draft = NodeCreate(name="Before rename", address="renamed.example.invalid", access_mode="restricted")
        node = crud.create_node(self.db, draft)
        node.name = "After rename"
        self.db.commit()
        add_host_if_needed(draft, self.db, node.id)
        hosts = [host for host in crud.get_hosts(self.db, TAG) if host.address == draft.address]
        self.assertEqual(len(hosts), 1)
        self.assertEqual(hosts[0].node_id, node.id)
        self.assertEqual(service.filter_hosts([{"node_id": node.id, "address": draft.address}],
            self.user.username, self.user.created_at, "vless"), [])

    def test_reference_website_client_runs_over_real_http_with_existing_admin_bearer(self):
        spec = importlib.util.spec_from_file_location("generic_website_client", ROOT / "examples/dedicated_access_client.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        client = module.DedicatedAccessClient(self.base, jwt.create_admin_token("site_admin"), allow_loopback_http=True)
        self.assertEqual(client.catalog()["capability"], service.CAPABILITY)
        operation_id = str(uuid4())
        granted = client.grant("alice", self.private.id, operation_id, "site-order-example")
        self.assertTrue(granted["effective"])
        self.assertEqual(client.receipt(operation_id)["operation_id"], operation_id)
        self.assertEqual(client.grant("alice", self.private.id, operation_id, "site-order-example"), granted)
        self.assertTrue(client.user_access("alice")["nodes"][0]["granted"])
        self.assertFalse(client.revoke("alice", self.private.id, str(uuid4()))["granted"])
        self.assertEqual(self.db.query(DedicatedNodeOperation).count(), 2)

    def test_reference_client_requires_https_and_rejects_redirect_credentials_or_bad_origin(self):
        spec = importlib.util.spec_from_file_location("generic_website_client", ROOT / "examples/dedicated_access_client.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for url in ("http://panel.example.invalid", "https://user:password@panel.example.invalid", "https://panel.example.invalid/?token=bad", "https://panel.example.invalid/not-api"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                module.DedicatedAccessClient(url, "test")
        self.assertIsNone(module._NoRedirect().redirect_request(None, None, None, None, None, None))

    def test_receipt_is_for_current_owned_user_not_a_bearer_capability(self):
        body = self.body()
        self.access(body=body)
        path = "/api/dedicated-node-operations/" + body["operation_id"]
        self.assertEqual(self.http("GET", path, actor="other_admin")[0], 403)
        self.assertEqual(self.http("GET", path, actor=None)[0], 401)
        self.assertEqual(self.http("GET", "/api/dedicated-node-operations/" + str(uuid4()))[0], 404)

    def test_deleting_and_recreating_same_username_does_not_inherit_grant_or_old_operation(self):
        body = self.body()
        self.access(body=body)
        old_id = self.user.id
        self.db.expire_all()
        self.db.delete(self.db.get(User, old_id))
        self.db.commit()
        replacement = self.make_user("alice", self.admin)
        self.assertEqual(self.db.query(DedicatedNodeGrant).count(), 0)
        self.assertFalse(self.access("GET")[1]["granted"])
        self.assertEqual(self.access(body=body)[0], 409)
        self.assertEqual(self.db.query(DedicatedNodeOperation).count(), 1)

    def test_disconnect_invalidates_old_synced_state_without_mutations(self):
        self.access()
        self.remote.connected = False
        before = len(self.remote.restarts)
        result = self.access("GET")[1]
        self.assertFalse(result["effective"])
        self.assertEqual(result["sync_state"], "pending")
        self.assertEqual(len(self.remote.restarts), before)

    def test_static_client_spoofing_authorized_email_is_not_loaded(self):
        self.access()
        business = next(row for row in self.config["inbounds"] if row["tag"] == TAG)
        fake_id = str(uuid4())
        business["settings"]["clients"] = [{"email": f"{self.user.id}.alice", "id": fake_id}]
        scoped, _, _ = node_access.prepare_config(self.config, self.private.id)
        clients = next(row for row in scoped["inbounds"] if row["tag"] == TAG)["settings"]["clients"]
        self.assertEqual([row["id"] for row in clients], [self.user.proxies[0].settings["id"]])
        self.assertNotIn(fake_id, json.dumps(scoped))

    def test_shared_relay_source_cannot_be_converted_into_dedicated(self):
        from app.db.models import NodeRelay
        self.db.add(NodeRelay(node_id=self.private.id, entry_address=self.public.address, listen_port=18443,
                             inbound_tag=TAG, source="node", source_node_id=self.public.id))
        self.db.commit()
        result = self.http("PUT", f"/api/node/{self.public.id}/access", {"access_mode": "restricted"}, actor="root_admin")
        self.assertEqual(result[0], 409)
        self.assertEqual(result[1]["detail"]["code"], "REMOVE_SHARED_RELAYS_BEFORE_RESTRICTING")
        self.assertEqual(self.public_remote.restarts, [])

    def test_rotated_or_revoked_device_credentials_cannot_be_readded_by_queued_update(self):
        credential = str(uuid4())
        device = UserDevice(user_id=self.user.id, hwid_hash="c" * 64, credentials={"vless": {"id": credential}})
        self.db.add(device)
        self.db.commit()
        self.access()
        guard = node_access.guard_api(self.private.id, self.remote)
        account = SimpleNamespace(email=f"{self.user.id}.alice.device-{'c' * 16}", id=credential)
        guard.add_inbound_user(TAG, account)
        self.remote.api.add_inbound_user.assert_called_once()
        self.remote.api.add_inbound_user.reset_mock()
        device.revoked_at = datetime.utcnow()
        self.db.commit()
        guard.add_inbound_user(TAG, account)
        self.remote.api.add_inbound_user.assert_not_called()
        shared = SimpleNamespace(email=f"{self.user.id}.alice", id=str(uuid4()))
        guard.add_inbound_user(TAG, shared)
        self.remote.api.add_inbound_user.assert_not_called()

    def test_dedicated_and_public_nodes_cannot_share_known_control_destination(self):
        with self.assertRaisesRegex(ValueError, "distinct"):
            crud.create_node(self.db, NodeCreate(name="Duplicate private", address=self.public.address, access_mode="restricted"))
        with self.assertRaisesRegex(ValueError, "distinct"):
            crud.create_node(self.db, NodeCreate(name="Duplicate public", address=self.private.address, access_mode="public"))

    def test_unknown_policy_value_fails_closed(self):
        self.private.access_mode = "unexpected"
        self.db.commit()
        with self.assertRaises(service.AccessError):
            node_access.prepare_config(self.config, self.private.id)
        self.assertEqual(service.filter_hosts([self.hosts[TAG][1]], "alice", self.user.created_at, "vless"), [])

    def test_openapi_documents_bearer_closed_request_and_distinct_mutations(self):
        code, schema, _ = self.http("GET", "/openapi.json", actor=None)
        self.assertEqual(code, 200)
        path = schema["paths"]["/api/user/{username}/dedicated-nodes/{node_id}"]
        self.assertEqual(set(path) & {"get", "put", "delete"}, {"get", "put", "delete"})
        self.assertTrue(path["put"]["security"])
        request = schema["components"]["schemas"]["DedicatedAccessRequest"]
        self.assertFalse(request["additionalProperties"])
        self.assertEqual(request["required"], ["operation_id"])
        contract = json.loads((ROOT / "docs/contracts/dedicated-node-access-v1.json").read_text(encoding="utf-8"))
        self.assertEqual(contract["capability"], service.CAPABILITY)
        self.assertEqual(contract["supported_protocols"], sorted(service.SUPPORTED_PROTOCOLS))
        for method, endpoint in contract["endpoints"] + contract["sudo_endpoints"]:
            self.assertIn(method.lower(), schema["paths"][endpoint])

    def test_error_responses_never_echo_invalid_sensitive_input(self):
        code, body, headers = self.access(body={**self.body(), "password": "never-echo-input-secret"})
        self.assertEqual(code, 422)
        self.assertNotIn("never-echo-input-secret", json.dumps(body))
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(self.http("GET", "/api/dedicated-nodes", actor=None)[2]["Cache-Control"], "no-store")


class DedicatedMigrationTests(unittest.TestCase):
    def test_real_alembic_cli_old_data_repeat_upgrade_and_nonempty_audit_downgrade(self):
        import os
        spec = importlib.util.spec_from_file_location("dedicated_release_verify", ROOT / "tools/verify_dedicated_access_release.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.verify(os.environ.get("MR_SHAW_RELAY_TEST_XRAY"))["migration"], "passed")

    def test_upgrade_preserves_old_rows_backfills_only_exact_ownership_and_guards_downgrade(self):
        spec = importlib.util.spec_from_file_location("dedicated_migration", ROOT / "app/db/migrations/versions/d456ef78ab90_dedicated_node_access.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        engine = create_engine("sqlite:///:memory:")
        with engine.begin() as conn:
            for sql in ("CREATE TABLE nodes (id INTEGER PRIMARY KEY, address VARCHAR(256))",
                        "CREATE TABLE hosts (id INTEGER PRIMARY KEY, address VARCHAR(256))",
                        "CREATE TABLE users (id INTEGER PRIMARY KEY)", "CREATE TABLE admins (id INTEGER PRIMARY KEY)",
                        "INSERT INTO nodes VALUES (1, 'unique.invalid'),(2,'same.invalid'),(3,'same.invalid')",
                        "INSERT INTO hosts VALUES (1,'unique.invalid'),(2,'same.invalid'),(3,'alias.invalid')"):
                conn.execute(text(sql))
            with patch.object(module, "op", Operations(MigrationContext.configure(conn))):
                module.upgrade()
                self.assertEqual(conn.execute(text("SELECT id, access_mode, access_revision FROM nodes ORDER BY id")).fetchall(),
                                 [(1, "public", 0), (2, "public", 0), (3, "public", 0)])
                self.assertEqual(conn.execute(text("SELECT id,node_id FROM hosts ORDER BY id")).fetchall(), [(1, 1), (2, None), (3, None)])
                module.downgrade()
                self.assertEqual(conn.execute(text("SELECT * FROM hosts ORDER BY id")).fetchall(),
                                 [(1, "unique.invalid"), (2, "same.invalid"), (3, "alias.invalid")])
                module.upgrade()
                conn.execute(text("UPDATE nodes SET access_mode='restricted' WHERE id=1"))
                with self.assertRaisesRegex(RuntimeError, "would expose"):
                    module.downgrade()
        engine.dispose()
