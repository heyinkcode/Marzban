import asyncio
import json
import threading
import unittest
from contextlib import ExitStack
from unittest.mock import Mock, patch
from cryptography.fernet import Fernet
from fastapi import FastAPI

import test_main_usage_coefficient as main_test
from test_node_relay import config
from app.models.admin import Admin
from app.models.node import NodeEgressProbe
from app.routers import node as routes
from app.xray import node_egress_service as service
from app.xray import node_egress_store as store


class EgressApplyTests(unittest.TestCase):
    def setUp(self):
        main_test.MainUsageTests.setUp(self)
        self.stack=ExitStack()
        self.stack.enter_context(patch.object(store,"_cipher",return_value=Fernet(Fernet.generate_key())))
        self.remote=Mock(connected=True)
        self.remote.get_health.return_value={"source":"node-runtime","capabilities":[service.CAPABILITY,"managed-outbounds-v1","managed-outbounds-udp-v1"]}
        self.lock=threading.Lock()
        self.stack.enter_context(patch.dict(service.xray.nodes,{self.node.id:self.remote},clear=True))
        self.stack.enter_context(patch.object(service.xray,"config",Mock(include_db_users=config)))
        self.stack.enter_context(patch.object(service.xray.operations,"node_lifecycle_lock",return_value=self.lock))
        self.stack.enter_context(patch.object(service.xray.operations,"sync_node_device_policies"))
        self.stack.enter_context(patch.object(service.xray.operations,"sync_all_node_device_accounts"))
        self.profile={"protocol":"socks","udp_mode":"tcp_only","server":"proxy.example.test","port":1080,"username":"test-user","password":"test-password"}

    def tearDown(self):
        self.stack.close(); main_test.MainUsageTests.tearDown(self)

    def request(self, method, tail="", body=None, authorized=True):
        app=FastAPI(); app.include_router(routes.router)
        app.dependency_overrides[routes.get_db]=lambda:self.db
        app.dependency_overrides[routes.get_dbnode]=lambda:self.node
        if authorized: app.dependency_overrides[Admin.check_sudo_admin]=lambda:Admin(username="test",is_sudo=True)
        path=f"/api/node/{self.node.id}/egress"+tail
        raw=json.dumps(body).encode() if body is not None else b""; messages=[]
        scope={"type":"http","asgi":{"version":"3.0"},"http_version":"1.1","method":method,"scheme":"https","path":path,
            "raw_path":path.encode(),"query_string":b"","root_path":"","server":("test.local",443),"client":("192.0.2.1",1000),
            "headers":[(b"content-type",b"application/json")]+([] if authorized else [(b"authorization",b"Bearer test")])}
        async def receive(): return {"type":"http.request","body":raw,"more_body":False}
        async def send(message): messages.append(message)
        asyncio.run(app(scope,receive,send))
        return next(m["status"] for m in messages if m["type"]=="http.response.start"),json.loads(b"".join(m.get("body",b"") for m in messages))

    def test_probe_saved_secret_resolution_no_write_and_redacted_response(self):
        store.save_egress(self.db,self.node,self.profile)
        self.remote.probe_egress.return_value={"version":1,"source":"node-egress-probe","rounds":[],"ok":False}
        status,result=self.request("POST","/test",{"profile":{**self.profile,"password":None},"timeout_seconds":10,"attempts":3})
        self.assertEqual(status,200); self.assertNotIn("test-password",json.dumps(result))
        self.assertEqual(self.remote.probe_egress.call_args.args[0]["password"],"test-password")
        self.assertEqual(self.remote.probe_egress.call_args.args[1:],(10,3)); self.remote.restart.assert_not_called()

    def test_apply_ack_then_persist_and_no_rescale(self):
        status,result=self.request("PUT",body=self.profile)
        self.assertEqual(status,200); self.assertTrue(result["configured"]); self.assertNotIn("test-password",json.dumps(result))
        self.assertEqual(store.read_egress(self.db,self.node)["server"],"proxy.example.test")
        self.remote.restart.assert_called_once(); self.assertEqual(self.user.used_traffic,50)

    def test_timeout_keeps_saved_settings_and_does_not_replay_mutation(self):
        store.save_egress(self.db,self.node,self.profile)
        self.remote.restart.side_effect=TimeoutError("test-password")
        status,result=self.request("PUT",body={**self.profile,"server":"new.example.test"})
        self.assertEqual(status,502); self.assertNotIn("test-password",json.dumps(result)); self.remote.restart.assert_called_once()
        self.assertEqual(store.read_egress(self.db,self.node)["server"],"proxy.example.test")

    def test_old_node_never_probes_or_mutates(self):
        self.remote.get_health.return_value={"source":"node-runtime","capabilities":["managed-outbounds-v1"]}
        for method,tail,body in (("POST","/test",{"profile":self.profile}),("PUT","",self.profile),("DELETE","",None)):
            status,result=self.request(method,tail,body); self.assertEqual(status,409)
            self.assertEqual(result["detail"]["code"],"NODE_UPGRADE_REQUIRED")
        self.remote.restart.assert_not_called(); self.remote.probe_egress.assert_not_called()

    def test_sudo_required_and_invalid_probe_bounds(self):
        with patch.object(Admin,"get_admin",return_value=Admin(username="ordinary",is_sudo=False)):
            self.assertEqual(self.request("POST","/test",{"profile":self.profile},False)[0],403)
        self.assertEqual(self.request("POST","/test",{"profile":self.profile,"attempts":100})[0],422)
        self.remote.probe_egress.assert_not_called()

    def test_busy_node_does_not_queue_or_change_settings(self):
        self.lock.acquire()
        try: self.assertEqual(self.request("PUT",body=self.profile)[1]["detail"]["code"],"NODE_BUSY")
        finally:self.lock.release()
        self.remote.restart.assert_not_called()

    def test_delete_ack_then_restores_original_config(self):
        store.save_egress(self.db,self.node,self.profile)
        self.assertEqual(self.request("DELETE")[0],200)
        self.db.expire_all(); self.assertIsNone(store.read_egress(self.db,self.node))
        self.assertNotIn("marzban_node_extensions",self.remote.restart.call_args.args[0])

    def test_database_failure_rolls_runtime_back(self):
        store.save_egress(self.db,self.node,self.profile)
        with patch.object(service,"save_egress",side_effect=RuntimeError("test-password")):
            status,result=self.request("PUT",body={**self.profile,"server":"new.example.test"})
        self.assertEqual(status,503); self.assertEqual(result["detail"]["code"],"SAVE_FAILED_ROLLED_BACK")
        self.assertEqual(self.remote.restart.call_count,2); self.assertNotIn("test-password",json.dumps(result))
        self.assertEqual(store.read_egress(self.db,self.node)["server"],"proxy.example.test")
