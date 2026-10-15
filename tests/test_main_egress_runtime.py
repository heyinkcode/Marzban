"""Optional pinned-core, real loopback proxy and local API integration tests."""
import copy
import os
import socket
import subprocess
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import test_user_device_limit as bootstrap
from app.xray.config import XRayConfig
from app.xray.main_core import ManagedMainCore, MainCoreError
from app.xray.main_egress import for_main

BINARY = os.environ.get("MR_SHAW_RELAY_TEST_XRAY", "")


def receive(sock, size):
    data=b""
    while len(data)<size:
        value=sock.recv(size-len(data))
        if not value: raise EOFError("short test frame")
        data+=value
    return data


@unittest.skipUnless(BINARY,"explicit pinned Xray integration binary not configured")
class MainCoreRuntimeTests(unittest.TestCase):
    def setUp(self):
        result=subprocess.run([BINARY,"version"],capture_output=True,text=True,check=True)
        self.assertIn("26.3.27",result.stdout)
        self.ports=set()
        self.core=ManagedMainCore(BINARY,str(Path(BINARY).parent))
        if os.name=="nt": self.core._env['SystemRoot']=os.environ['SystemRoot']
        self.addCleanup(self.core.stop)
        self.profile=None
        self.runtime=patch.object(self.core,"_runtime",side_effect=lambda base:for_main(base,self.profile))
        self.runtime.start();self.addCleanup(self.runtime.stop)
        self.base=XRayConfig({"inbounds":[{"tag":"TEST_CLIENT","listen":"127.0.0.1","port":self.port(),
            "protocol":"socks","settings":{"auth":"noauth","udp":False}}],
            "outbounds":[{"tag":"DIRECT","protocol":"freedom"}],"routing":{"rules":[]}},api_port=self.port())
        self.business_port=next(row['port'] for row in self.base['inbounds'] if row['tag']=='TEST_CLIENT')
        self.original=copy.deepcopy(self.base)

    def port(self):
        while True:
            with socket.socket() as listener:
                listener.bind(('127.0.0.1',0));port=listener.getsockname()[1]
            if port not in self.ports:self.ports.add(port);return port

    def server(self, proxy=False):
        listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen();listener.settimeout(.2)
        stop=threading.Event();captured=[];errors=[]
        def worker():
            while not stop.is_set():
                try:connection,_=listener.accept()
                except socket.timeout:continue
                except OSError:break
                try:
                    with connection:
                        connection.settimeout(3)
                        if proxy:
                            header=b''
                            while not header.endswith(b'\r\n\r\n'):header+=receive(connection,1)
                            captured.append(header)
                            connection.sendall(b'HTTP/1.1 200 Connection established\r\n\r\n')
                        data=receive(connection,4)
                        if data!=b'ping':raise ValueError('wrong test data')
                        connection.sendall(b'proxied' if proxy else b'direct')
                except Exception as error:errors.append(type(error).__name__)
        thread=threading.Thread(target=worker,daemon=True);thread.start()
        def close():stop.set();listener.close();thread.join(4)
        self.addCleanup(close)
        return listener.getsockname()[1],captured,errors

    def request(self,target):
        with socket.create_connection(('127.0.0.1',self.business_port),timeout=3) as client:
            client.settimeout(3);client.sendall(b'\x05\x01\x00');self.assertEqual(receive(client,2),b'\x05\x00')
            client.sendall(b'\x05\x01\x00\x01'+socket.inet_aton('127.0.0.1')+target.to_bytes(2,'big'))
            header=receive(client,4);self.assertEqual(header[:2],b'\x05\x00')
            if header[3]==1:receive(client,6)
            elif header[3]==4:receive(client,18)
            else:receive(client,receive(client,1)[0]+2)
            client.sendall(b'ping');return client.recv(16)

    def test_real_proxy_apply_delete_api_and_base_isolation(self):
        target,_,direct_errors=self.server()
        proxy,captured,proxy_errors=self.server(True)
        self.core.start(self.base);self.assertEqual(self.request(target),b'direct')
        value={"protocol":"http","udp_mode":"legacy","server":"127.0.0.1","port":proxy,"username":None,"password":None}
        old=self.core.process
        with self.core.change():self.core.replace_runtime(for_main(self.base,value))
        self.assertIsNotNone(old.poll());self.assertEqual(self.request(target),b'proxied')
        self.core._wait_ready(self.core._last_config)
        with self.core.change():self.core.replace_runtime(for_main(self.base,None))
        self.assertEqual(self.request(target),b'direct');self.assertEqual(self.base,self.original)
        self.assertIn(b'CONNECT 127.0.0.1:',captured[0]);self.assertFalse(direct_errors+proxy_errors)

    def test_restarts_and_health_recovery_keep_saved_overlay(self):
        target,_,_=self.server();proxy,captured,errors=self.server(True)
        self.profile={"protocol":"http","server":"127.0.0.1","port":proxy,"username":None,"password":None}
        self.core.start(self.base);self.assertEqual(self.request(target),b'proxied')
        self.core.restart(self.base);self.assertEqual(self.request(target),b'proxied')
        self.core.stop();self.core.restart(self.base);self.assertEqual(self.request(target),b'proxied')
        self.assertEqual(len(captured),3);self.assertEqual(self.base,self.original);self.assertFalse(errors)

    def test_invalid_preflight_and_bind_failure_restore_working_core(self):
        target,_,_=self.server();self.core.start(self.base);original_process=self.core.process
        invalid=copy.deepcopy(self.base);invalid['outbounds'].append({'tag':'INVALID','protocol':'not-a-protocol'})
        with self.core.change(),self.assertRaises(MainCoreError) as failure:self.core.replace_runtime(invalid)
        self.assertEqual(failure.exception.code,'MAIN_PREFLIGHT_FAILED')
        self.assertIs(self.core.process,original_process);self.assertEqual(self.request(target),b'direct')
        with socket.socket() as occupied:
            occupied.bind(('127.0.0.1',0));occupied.listen()
            invalid=copy.deepcopy(self.base)
            next(row for row in invalid['inbounds'] if row['tag']=='TEST_CLIENT')['port']=occupied.getsockname()[1]
            with self.core.change(),self.assertRaises(MainCoreError) as failure:self.core.replace_runtime(invalid)
            self.assertEqual(failure.exception.code,'MAIN_APPLY_FAILED_ROLLED_BACK')
        self.assertEqual(self.request(target),b'direct')

    def test_real_core_preflight_all_udp_modes_and_collision_safety(self):
        for protocol,mode in (('http','legacy'),('http','tcp_only'),('socks','proxy'),('socks','tcp_only')):
            value={'protocol':protocol,'udp_mode':mode,'server':'127.0.0.1','port':1080,'username':None,'password':None}
            self.core.validate_config(for_main(self.base,value))
        collision=copy.deepcopy(self.base);collision['outbounds'].append({'tag':'managed-residential-egress','protocol':'freedom'})
        with self.assertRaises(ValueError):for_main(collision,value)
        self.assertEqual(self.base,self.original)

    def test_stop_reaps_process_and_closes_generation_pipes(self):
        self.core.start(self.base);process=self.core.process;reader=self.core._logs_thread;writer=self.core._input_thread
        self.core.stop();self.assertIsNotNone(process.poll());self.assertFalse(reader.is_alive());self.assertFalse(writer.is_alive())
        self.assertTrue(process.stdin.closed);self.assertTrue(process.stdout.closed)
