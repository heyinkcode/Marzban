"""Real SQLite/ASGI contracts and local lifecycle isolation, no production IO."""
import asyncio
import copy
import importlib.util
import json
import threading
import unittest
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import test_main_usage_coefficient as usage
from test_node_relay import config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from cryptography.fernet import Fernet
from fastapi import FastAPI
from sqlalchemy import create_engine, inspect, text

from app.db.models import MainEgress
from app.models.admin import Admin
from app.routers import node as routes
from app.xray import main_egress as store, main_egress_service as service
from app.xray.main_core import ManagedMainCore, MainCoreError
from app.xray.node_egress import for_node


class MainEgressTests(unittest.TestCase):
    def setUp(self):
        usage.MainUsageTests.setUp(self)
        self.stack = ExitStack()
        self.stack.enter_context(patch.object(store, "_cipher", return_value=Fernet(Fernet.generate_key())))
        with patch.object(ManagedMainCore, "get_version", return_value="26.3.27"):
            self.core = ManagedMainCore("test-xray", "test-assets")
        self.base = config()
        self.original = copy.deepcopy(self.base)
        self.core.process = SimpleNamespace(poll=lambda: None)
        self.core._last_config = copy.deepcopy(self.base)
        self.runtime_history = []
        def stop():
            self.core.process = None
        def ready(runtime):
            self.core.process = SimpleNamespace(poll=lambda: None)
            self.core._last_config = copy.deepcopy(runtime)
            self.runtime_history.append(copy.deepcopy(runtime))
        self.stop = self.stack.enter_context(patch.object(self.core, "_stop", side_effect=stop))
        self.ready = self.stack.enter_context(patch.object(self.core, "_ready", side_effect=ready))
        self.validate = self.stack.enter_context(patch.object(self.core, "validate_config"))
        self.stack.enter_context(patch.object(service.xray, "core", self.core))
        self.stack.enter_context(patch.object(service.xray, "config", Mock(include_db_users=lambda: self.base)))
        self.remote = Mock()
        self.stack.enter_context(patch.dict(service.xray.nodes, {self.node.id: self.remote}, clear=True))
        self.profile = {"protocol":"socks", "udp_mode":"tcp_only", "server":"proxy.example.test", "port":1080,
                        "username":"demo", "password":" secret with spaces "}

    def tearDown(self):
        self.core.process = None
        self.stack.close()
        usage.MainUsageTests.tearDown(self)

    def request(self, method, tail="", body=None, authorized=True):
        app = FastAPI(); app.include_router(routes.router)
        app.dependency_overrides[routes.get_db] = lambda: self.db
        if authorized:
            app.dependency_overrides[Admin.check_sudo_admin] = lambda: Admin(username="test", is_sudo=True)
        path = "/api/node/main/egress" + tail
        raw = json.dumps(body).encode() if body is not None else b""
        messages = []
        scope = {"type":"http","asgi":{"version":"3.0"},"http_version":"1.1","method":method,"scheme":"https",
                 "path":path,"raw_path":path.encode(),"query_string":b"","root_path":"","server":("test.local",443),
                 "client":("192.0.2.1",1000),"headers":[(b"content-type",b"application/json")]+
                 ([] if authorized else [(b"authorization",b"Bearer test")])}
        async def receive(): return {"type":"http.request","body":raw,"more_body":False}
        async def send(message): messages.append(message)
        asyncio.run(app(scope, receive, send))
        return next(m["status"] for m in messages if m["type"] == "http.response.start"), json.loads(
            b"".join(m.get("body",b"") for m in messages))

    def test_api_encrypted_save_and_no_remote_or_base_mutation(self):
        self.assertFalse(self.request("GET")[1]["configured"])
        status, result = self.request("PUT", body=self.profile)
        self.assertEqual(status, 200); self.assertTrue(result["configured"])
        self.assertNotIn(self.profile["password"], json.dumps(result))
        row = self.db.get(MainEgress,1)
        self.assertNotEqual(row.encrypted_password, self.profile["password"])
        self.assertEqual(store.read_profile(self.db)["password"], self.profile["password"])
        self.assertEqual(self.base, self.original); self.assertEqual(self.remote.mock_calls, [])
        self.assertIsNone(self.node.egress); self.assertEqual(self.node.usage_coefficient,3)
        self.assertEqual(self.user.used_traffic,50); self.assertEqual(self.system.usage_coefficient,1)
        self.assertNotIn("marzban_node_extensions", self.runtime_history[-1])
        self.assertEqual(for_node(self.base,None),self.original)

    def test_saved_password_preserved_probe_does_not_apply_or_save(self):
        store.persist_profile(self.db,self.profile)
        result = {"source":"main-egress-probe","version":1,"ok":False,"rounds":[]}
        with patch.object(service.main_egress_probe,"probe",return_value=result) as probe:
            status, response = self.request("POST","/test",{"profile":{**self.profile,"password":None},"timeout_seconds":10,"attempts":3})
        self.assertEqual(status,200); self.assertEqual(response,result)
        self.assertEqual(probe.call_args.args[0]["password"],self.profile["password"])
        self.assertEqual(probe.call_args.args[1:],(10,3)); self.ready.assert_not_called()
        self.assertEqual(self.remote.mock_calls,[])

    def test_delete_restores_private_base_only(self):
        self.assertEqual(self.request("PUT",body=self.profile)[0],200)
        status,result = self.request("DELETE")
        self.assertEqual(status,200); self.assertFalse(result["configured"])
        self.assertIsNone(self.db.get(MainEgress,1)); self.assertEqual(self.runtime_history[-1],self.original)
        self.assertEqual(self.remote.mock_calls,[])

    def test_all_actions_require_sudo(self):
        actions=(("GET","",None),("PUT","",self.profile),("DELETE","",None),("POST","/test",{"profile":self.profile}))
        for account, expected in ((None,401),(Admin(username="ordinary",is_sudo=False),403)):
            with patch.object(Admin,"get_admin",return_value=account):
                for method,tail,body in actions:
                    self.assertEqual(self.request(method,tail,body,False)[0],expected)
        self.ready.assert_not_called()

    def test_validation_and_detection_limits_leave_settings_intact(self):
        for changes in ({"protocol":"vless"},{"server":"http://proxy.test"},{"port":0},{"port":True},{"protocol":"http","udp_mode":"proxy"},{"username":None}):
            self.assertEqual(self.request("PUT",body={**self.profile,**changes})[0],422)
        for key,value in (("timeout_seconds",99),("attempts",2),("attempts",True)):
            self.assertEqual(self.request("POST","/test",{"profile":self.profile,key:value})[0],422)
        self.assertFalse(self.request("GET")[1]["configured"]); self.ready.assert_not_called()

    def test_busy_and_offline_reject_without_change(self):
        self.core.lifecycle_lock.acquire()
        try:
            self.assertEqual(self.request("PUT",body=self.profile)[1]["detail"]["code"],"MAIN_CORE_BUSY")
        finally: self.core.lifecycle_lock.release()
        self.core.process = None
        self.assertEqual(self.request("PUT",body=self.profile)[1]["detail"]["code"],"MAIN_CORE_OFFLINE")
        self.ready.assert_not_called()

    def test_preflight_failure_keeps_working_process_and_saved_value(self):
        store.persist_profile(self.db,self.profile)
        self.validate.side_effect = MainCoreError("MAIN_PREFLIGHT_FAILED",422)
        status,result = self.request("PUT",body={**self.profile,"server":"new.example.test"})
        self.assertEqual(status,422); self.assertEqual(result["detail"]["code"],"MAIN_PREFLIGHT_FAILED")
        self.stop.assert_not_called(); self.assertEqual(store.read_profile(self.db)["server"],self.profile["server"])

    def test_failed_start_restores_previous_config_and_keeps_saved_value(self):
        store.persist_profile(self.db,self.profile)
        normal_ready = self.ready.side_effect
        calls=[]
        def ready(runtime):
            calls.append(runtime)
            if len(calls)==1: raise RuntimeError("sensitive stderr")
            normal_ready(runtime)
        self.ready.side_effect=ready
        status,result=self.request("PUT",body={**self.profile,"server":"new.example.test"})
        self.assertEqual(status,502); self.assertEqual(result["detail"]["code"],"MAIN_APPLY_FAILED_ROLLED_BACK")
        self.assertNotIn("sensitive",json.dumps(result)); self.assertEqual(len(calls),2)
        self.assertEqual(calls[-1]["outbounds"][-3]["settings"]["address"],self.profile["server"])

    def test_failed_start_and_restore_report_both_failures(self):
        self.ready.side_effect=RuntimeError("secret")
        status,result=self.request("PUT",body=self.profile)
        self.assertEqual(status,503); self.assertEqual(result["detail"]["code"],"MAIN_APPLY_FAILED_ROLLBACK_FAILED")
        self.assertFalse(self.request("GET")[1]["configured"])

    def test_database_failure_restores_runtime_and_does_not_touch_nodes(self):
        store.persist_profile(self.db,self.profile)
        with patch.object(self.db,"commit",side_effect=RuntimeError("secret database")):
            status,result=self.request("PUT",body={**self.profile,"server":"new.example.test"})
        self.assertEqual(status,503); self.assertEqual(result["detail"]["code"],"MAIN_SAVE_FAILED_ROLLED_BACK")
        self.assertEqual(len(self.runtime_history),2)
        self.assertEqual(store.read_profile(self.db)["server"],self.profile["server"])
        self.assertEqual(self.remote.mock_calls,[])

    def test_start_and_every_restart_reload_saved_profile(self):
        store.persist_profile(self.db,self.profile)
        from contextlib import contextmanager
        @contextmanager
        def database(): yield self.db
        with patch("app.db.GetDB",database):
            self.core.process=None; self.core.start(self.base)
            self.core.restart(self.base)
        self.assertEqual(len(self.runtime_history),2)
        self.assertEqual(self.runtime_history[0],self.runtime_history[1])
        self.assertEqual(self.base,self.original); self.assertEqual(self.remote.mock_calls,[])

    def test_database_failure_with_failed_restore_is_explicit(self):
        store.persist_profile(self.db,self.profile)
        normal=self.ready.side_effect
        count=[]
        def ready(runtime):
            count.append(True)
            if len(count)==2:raise RuntimeError('restore could not start')
            normal(runtime)
        self.ready.side_effect=ready
        with patch.object(self.db,"commit",side_effect=RuntimeError('commit failed')):
            status,result=self.request("PUT",body={**self.profile,"server":"new.example.test"})
        self.assertEqual(status,503);self.assertEqual(result['detail']['code'],'MAIN_SAVE_FAILED_ROLLBACK_FAILED')
        self.assertEqual(store.read_profile(self.db)['server'],self.profile['server'])

    def test_probe_busy_and_deadline_report_without_restart(self):
        with patch.object(service.main_egress_probe,'probe',side_effect=RuntimeError('PROBE_BUSY')):
            status,result=self.request('POST','/test',{'profile':self.profile})
        self.assertEqual(status,409);self.assertEqual(result['detail']['code'],'MAIN_PROBE_BUSY')
        self.ready.assert_not_called()

    def test_recovery_decryption_error_never_runs_unproxied(self):
        store.persist_profile(self.db,self.profile)
        self.db.get(MainEgress,1).encrypted_password='invalid';self.db.commit()
        from contextlib import contextmanager
        @contextmanager
        def database():yield self.db
        with patch('app.db.GetDB',database),self.assertRaises(Exception):self.core.restart(self.base)
        self.ready.assert_not_called();self.stop.assert_not_called()

    def test_udp_modes_and_api_explicit_route_preserved(self):
        for protocol,mode in (("http","legacy"),("http","tcp_only"),("socks","proxy"),("socks","legacy")):
            runtime=store.for_main(self.base,{**self.profile,"protocol":protocol,"udp_mode":mode})
            self.assertEqual(runtime["inbounds"],self.original["inbounds"])
            self.assertEqual(runtime.api_port,self.base.api_port)
            api_rule=next(r for r in runtime["routing"]["rules"] if r.get("outboundTag")=="API")
            self.assertEqual(api_rule["inboundTag"],["API_INBOUND"])
        self.assertEqual(self.base,self.original)

    def test_missing_key_or_corrupt_password_never_falls_back_to_direct(self):
        store.persist_profile(self.db,self.profile)
        self.db.get(MainEgress,1).encrypted_password='invalid'; self.db.commit()
        status,result=self.request("PUT",body={**self.profile,"password":None})
        self.assertEqual(status,503); self.assertEqual(result["detail"]["code"],"MAIN_SETTINGS_UNAVAILABLE")
        self.ready.assert_not_called()


class MainEgressMigrationTests(unittest.TestCase):
    def test_additive_singleton_upgrade_and_downgrade(self):
        engine=create_engine("sqlite:///:memory:")
        path=Path(__file__).resolve().parents[1]/"app/db/migrations/versions/b234cd56ef78_main_egress.py"
        spec=importlib.util.spec_from_file_location("main_egress_migration",path)
        migration=importlib.util.module_from_spec(spec); spec.loader.exec_module(migration)
        self.assertEqual(migration.down_revision,"a123bc45de67")
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE existing_data (id INTEGER PRIMARY KEY, value TEXT)"))
            connection.execute(text("INSERT INTO existing_data VALUES (1,'preserve')"))
            migration.op=Operations(MigrationContext.configure(connection)); migration.upgrade()
            self.assertIn("main_egress",inspect(connection).get_table_names())
            self.assertEqual(connection.execute(text("SELECT COUNT(*) FROM main_egress")).scalar(),0)
            migration.downgrade()
            self.assertNotIn("main_egress",inspect(connection).get_table_names())
            self.assertEqual(connection.execute(text("SELECT value FROM existing_data")).scalar(),"preserve")
        engine.dispose()
