"""Pinned Xray VLESS loopback authorization; no external servers or production."""
import os
import socket
import threading
import unittest
from pathlib import Path
from uuid import UUID, uuid4

import test_dedicated_access as fixtures
from app import xray
from app.db.models import UserDevice
from app.models.proxy import ProxyTypes
from app.xray import node_access
from app.xray.config import XRayConfig
from app.xray.main_core import ManagedMainCore
from xray_api import XRay as XRayAPI

BINARY = os.environ.get("MR_SHAW_RELAY_TEST_XRAY", "")
TAG = fixtures.TAG


def receive(sock, size):
    data = b""
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise EOFError("connection rejected/closed")
        data += chunk
    return data


@unittest.skipUnless(BINARY, "explicit pinned Xray 26.3.27 binary required")
class DedicatedCoreRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.DedicatedAccessTests()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        self.protocol = "vmess" if "vmess" in self._testMethodName else "trojan" if "trojan" in self._testMethodName else "vless"
        if self.protocol != "vless":
            for user in (self.fixture.user, self.fixture.other_user):
                proxy = user.proxies[0]
                credential = proxy.settings["id"]
                proxy.type = ProxyTypes._value2member_map_[self.protocol]
                proxy.settings = {"password": credential} if self.protocol == "trojan" else {"id": credential}
            self.fixture.db.commit()
        self.server_port, self.api_port = self.port(), self.port()
        self.base = XRayConfig({"inbounds": [{"tag": TAG, "listen": "127.0.0.1", "port": self.server_port,
            "protocol": self.protocol, "settings": {"clients": [], **({"decryption": "none"} if self.protocol == "vless" else {})},
            "streamSettings": {"network": "tcp"}}], "outbounds": [{"tag": "DIRECT", "protocol": "freedom"}]},
            api_port=self.api_port)
        self.fixture.config.clear()
        self.fixture.config.update(self.base)
        self.fixture.config.api_port = self.api_port
        self.fixture.config.inbounds_by_tag = self.base.inbounds_by_tag
        self.fixture.config.inbounds_by_protocol = self.base.inbounds_by_protocol
        self.core = ManagedMainCore(BINARY, str(Path(BINARY).parent))
        self.core._runtime = lambda config: config
        if os.name == "nt":
            self.core._env["SystemRoot"] = os.environ["SystemRoot"]
        self.addCleanup(self.core.stop)
        core, api_port = self.core, self.api_port
        class LocalCore(fixtures.FakeNode):
            @property
            def started(self):
                return core.started
            @started.setter
            def started(self, value):
                pass
            def restart(self, config):
                core.restart(config)
                self.restarts.append(config)
        self.remote = LocalCore()
        self.remote.api = XRayAPI("127.0.0.1", api_port)
        self.fixture.nodes[self.fixture.private.id] = self.remote
        initial, mode, revision = node_access.prepare_config(self.fixture.config.include_db_users(), self.fixture.private.id)
        self.core.start(initial)
        node_access.acknowledge(self.remote, mode, revision)
        self.listener = socket.socket()
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen()
        self.listener.settimeout(.1)
        self.target_port = self.listener.getsockname()[1]
        self.stopped = threading.Event()
        self.hits = []
        def echo():
            while not self.stopped.is_set():
                try:
                    conn, _ = self.listener.accept()
                except socket.timeout:
                    continue
                except OSError:
                    break
                with conn:
                    conn.settimeout(2)
                    try:
                        self.hits.append(receive(conn, 4))
                        conn.sendall(b"pong")
                    except (EOFError, OSError):
                        pass
        self.worker = threading.Thread(target=echo, daemon=True)
        self.worker.start()
        self.addCleanup(self.stop_echo)

    def port(self):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            return listener.getsockname()[1]

    def stop_echo(self):
        self.stopped.set()
        self.listener.close()
        self.worker.join(3)

    def request(self, credential):
        with socket.create_connection(("127.0.0.1", self.server_port), timeout=1) as client:
            client.settimeout(1)
            client.sendall(b"\x00" + UUID(credential).bytes + b"\x00\x01" + self.target_port.to_bytes(2, "big")
                           + b"\x01" + socket.inet_aton("127.0.0.1") + b"ping")
            header = receive(client, 2)
            self.assertEqual(header[0], 0)
            if header[1]:
                receive(client, header[1])
            return receive(client, 4)

    def assert_denied(self, credential):
        before = len(self.hits)
        with self.assertRaises((EOFError, OSError, TimeoutError)):
            self.request(credential)
        self.assertEqual(len(self.hits), before)

    def socks_client(self, credential):
        port = self.port()
        server = {"address": "127.0.0.1", "port": self.server_port}
        if self.protocol == "vmess":
            settings = {"vnext": [{**server, "users": [{"id": credential, "security": "auto"}]}]}
        else:
            settings = {"servers": [{**server, "password": credential}]}
        config = XRayConfig({"inbounds": [{"tag": "TEST_SOCKS", "listen": "127.0.0.1", "port": port,
                                          "protocol": "socks", "settings": {"auth": "noauth"}}],
            "outbounds": [{"tag": "TEST_PROXY", "protocol": self.protocol, "settings": settings,
                           "streamSettings": {"network": "tcp"}}]}, api_port=self.port())
        client = ManagedMainCore(BINARY, str(Path(BINARY).parent))
        client._runtime = lambda base: base
        if os.name == "nt":
            client._env["SystemRoot"] = os.environ["SystemRoot"]
        self.addCleanup(client.stop)
        client.start(config)
        return port

    def socks_request(self, port):
        with socket.create_connection(("127.0.0.1", port), timeout=1) as client:
            client.settimeout(1)
            client.sendall(b"\x05\x01\x00")
            self.assertEqual(receive(client, 2), b"\x05\x00")
            client.sendall(b"\x05\x01\x00\x01" + socket.inet_aton("127.0.0.1") + self.target_port.to_bytes(2, "big"))
            header = receive(client, 4)
            if header[1] != 0:
                raise OSError("SOCKS outbound denied")
            receive(client, 6 if header[3] == 1 else 18)
            client.sendall(b"ping")
            return receive(client, 4)

    def generic_protocol_flow(self):
        key = "password" if self.protocol == "trojan" else "id"
        alice = self.socks_client(self.fixture.user.proxies[0].settings[key])
        bob = self.socks_client(self.fixture.other_user.proxies[0].settings[key])
        with self.assertRaises((EOFError, OSError, TimeoutError)):
            self.socks_request(alice)
        self.assertEqual(self.fixture.access()[0], 200)
        self.assertEqual(self.socks_request(alice), b"pong")
        with self.assertRaises((EOFError, OSError, TimeoutError)):
            self.socks_request(bob)
        self.assertEqual(self.fixture.access("DELETE")[0], 200)
        with self.assertRaises((EOFError, OSError, TimeoutError)):
            self.socks_request(alice)

    def test_real_vmess_authorization_and_revocation(self):
        self.generic_protocol_flow()

    def test_real_trojan_authorization_and_revocation(self):
        self.generic_protocol_flow()

    def test_real_core_blocks_ungranted_credentials_allows_grant_and_rejects_after_revoke(self):
        alice = self.fixture.user.proxies[0].settings["id"]
        bob = self.fixture.other_user.proxies[0].settings["id"]
        self.assert_denied(alice)
        self.assert_denied(bob)
        code, result, _ = self.fixture.access()
        self.assertEqual(code, 200)
        self.assertTrue(result["effective"])
        self.assertEqual(self.request(alice), b"pong")
        self.assert_denied(bob)
        self.assertEqual(self.fixture.access("DELETE")[0], 200)
        self.assert_denied(alice)
        self.assertEqual(self.fixture.public_remote.restarts, [])

    def test_real_device_credential_and_reconnect_keep_the_same_node_authorization(self):
        credential = str(uuid4())
        self.fixture.db.add(UserDevice(user_id=self.fixture.user.id, hwid_hash="b" * 64,
            credentials={"vless": {"id": credential}}))
        self.fixture.db.commit()
        self.assert_denied(credential)
        self.fixture.access()
        self.assertEqual(self.request(credential), b"pong")
        # A recreated control transport has no trusted acknowledgement: rebuild
        # the core from current DB permissions instead of reviving all users.
        self.remote.access_applied_revision = None
        node_access.reconcile(self.fixture.private.id)
        self.assertEqual(self.request(credential), b"pong")
        self.fixture.access("DELETE")
        self.remote.access_applied_revision = None
        node_access.reconcile(self.fixture.private.id)
        self.assert_denied(credential)
