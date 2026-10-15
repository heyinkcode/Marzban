import asyncio
import json
import socket
import subprocess
import threading
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

import test_user_device_limit as bootstrap
from app.xray import main_egress_probe as probe
from fastapi import HTTPException
from app.xray.managed_outbounds import _profile


def profile(**changes):
    return {"protocol":"socks","server":"proxy.example.test","port":1080,
            "username":"test-user","password":" test-password ","udp_mode":"legacy",**changes}


class ProbeTests(unittest.TestCase):
    def test_validation_bounds_and_preserved_password(self):
        for timeout, attempts in ((True,1),(5,True),(0,1),(20,1),(5,2)):
            with self.assertRaises(ValueError): probe.validate_request(profile(),timeout,attempts)
        for update in ({"protocol":"vless"},{"port":0},{"udp_mode":"proxy","protocol":"http"},{"username":"a","password":None}):
            with self.assertRaises(ValueError): probe.validate_request(profile(**update),5,1)
        value = probe.validate_request(profile(),5,1)
        self.assertEqual(_profile(value,set())["settings"]["pass"]," test-password ")

    def test_dns_public_only_and_no_rebinding(self):
        for addresses in (["127.0.0.1"],["10.0.0.1"],["169.254.169.254"],["8.8.8.8","192.168.1.1"]):
            answers=[(socket.AF_INET,socket.SOCK_STREAM,6,"",(address,1080)) for address in addresses]
            with patch.object(probe.socket,"getaddrinfo",return_value=answers),self.assertRaises(probe.ProbeFailure):
                probe._public_addresses("proxy.test",1080)
        answers=[(socket.AF_INET,socket.SOCK_STREAM,6,"",("8.8.8.8",1080))]
        with patch.object(probe.socket,"getaddrinfo",return_value=answers):
            self.assertEqual(probe._public_addresses("proxy.test",1080),answers)

    def wire(self, response, config, action=None):
        client, server=socket.socketpair(); client.settimeout(2); server.settimeout(2)
        captured=[]
        def serve():
            try:
                if action: action(server,captured)
                else:
                    captured.append(server.recv(4096)); server.sendall(response)
            finally: server.close()
        worker=threading.Thread(target=serve,daemon=True); worker.start()
        try: return probe._negotiate(client,config),captured
        finally: client.close(); worker.join(3)

    def test_real_http_connect_and_407_redacted(self):
        _, captured=self.wire(b"HTTP/1.1 200 OK\r\n\r\n",profile(protocol="http"))
        self.assertIn(b"CONNECT www.cloudflare.com:443 HTTP/1.1",captured[0])
        self.assertIn(b"Proxy-Authorization: Basic ",captured[0])
        with self.assertRaises(probe.ProbeFailure) as error:
            self.wire(b"HTTP/1.1 407 Authentication required\r\n\r\n",profile(protocol="http"))
        self.assertEqual(error.exception.code,"PROXY_AUTH_REJECTED")
        self.assertNotIn("test-password",str(error.exception))

    def test_real_socks5_userpass_and_connect(self):
        def serve(server,captured):
            captured.append(probe._read(server,3)); server.sendall(b"\x05\x02")
            version,length=probe._read(server,2); self.assertEqual(version,1)
            user=probe._read(server,length); length=probe._read(server,1)[0]; password=probe._read(server,length)
            captured.extend([user,password]); server.sendall(b"\x01\x00")
            head=probe._read(server,5); host=probe._read(server,head[4]); port=probe._read(server,2)
            captured.append(host); server.sendall(b"\x05\x00\x00\x01\x08\x08\x08\x08\x01\xbb")
        value,captured=self.wire(None,profile(),serve)
        self.assertEqual(value,("8.8.8.8",443)); self.assertEqual(captured[2],b" test-password ")
        self.assertEqual(captured[3],b"www.cloudflare.com")

    def test_socks_no_auth_rejection_eof_and_dns_transaction(self):
        with self.assertRaises(probe.ProbeFailure):
            self.wire(b"\x05\xff",profile(username=None,password=None))
        query=probe._dns_query(); good=query[:2]+b"\x81\x80"+query[4:]
        probe._check_dns(good,query)
        with self.assertRaises(probe.ProbeFailure): probe._check_dns(b"bad",query)
        with self.assertRaises(probe.ProbeFailure): probe._check_dns(b"xx"+good[2:],query)

    def test_timeout_and_auth_errors_identify_stage_without_secret(self):
        with patch.object(probe,"_public_addresses",return_value=[1]),patch.object(probe,"_connect",side_effect=TimeoutError("test-password")):
            result=probe.run_round(profile(),5)
        self.assertFalse(result["ok"]); self.assertEqual(result["steps"][-1]["stage"],"proxy_tcp")
        self.assertEqual(result["steps"][-1]["code"],"TIMEOUT"); self.assertNotIn("test-password",json.dumps(result))
        with patch.object(probe,"_public_addresses",side_effect=probe.ProbeFailure("PROXY_ADDRESS_NOT_PUBLIC")):
            self.assertEqual(probe.run_round(profile(),5)["steps"][-1]["stage"],"proxy_dns")

    def test_unreachable_first_dns_answer_tries_next_with_one_deadline(self):
        first, second=Mock(),Mock()
        first.connect.side_effect=ConnectionRefusedError()
        answers=[(socket.AF_INET6,socket.SOCK_STREAM,6,"",("2001:4860:4860::8888",1080,0,0)),
                 (socket.AF_INET,socket.SOCK_STREAM,6,"",("8.8.8.8",1080))]
        with patch.object(probe.socket,"socket",side_effect=[first,second]):
            self.assertIs(probe._connect(answers,5),second)
        first.close.assert_called_once(); second.connect.assert_called_once_with(("8.8.8.8",1080))

    def test_worker_deadline_cleanup_does_not_guess_success(self):
        process=Mock(); process.communicate.side_effect=[subprocess.TimeoutExpired("probe",30),("",None)]
        process.returncode=-9; process.poll.return_value=-9
        with patch.object(probe.subprocess,"Popen",return_value=process): result=probe.probe(profile(),5,3)
        self.assertFalse(result["ok"]); self.assertEqual(result["completed"],0)
        self.assertEqual(result["code"],"TOTAL_DEADLINE"); process.kill.assert_called_once()
        self.assertNotIn("test-password",json.dumps(result))

    def test_real_tcp_framed_dns_through_proxy_connection(self):
        client,server=socket.socketpair(); client.settimeout(2); server.settimeout(2)
        recorded=[]
        def answer():
            with server:
                size=int.from_bytes(probe._read(server,2),'big'); query=probe._read(server,size); recorded.append(query)
                response=query[:2]+b"\x81\x80"+query[4:]
                server.sendall(len(response).to_bytes(2,'big')+response)
        thread=threading.Thread(target=answer,daemon=True); thread.start()
        with patch.object(probe,"_connect",return_value=client),patch.object(probe,"_negotiate") as negotiate:
            self.assertEqual(probe._dns_test(profile(udp_mode='tcp_only'),[],2),"DNS_TCP_THROUGH_PROXY_OK")
            self.assertEqual(negotiate.call_args.args[2:],('1.1.1.1',53))
        thread.join(3); self.assertEqual(len(recorded),1)

    def test_real_udp_dns_datagram_not_just_associate_ack(self):
        client,server=socket.socketpair(); udp=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        udp.bind(('127.0.0.1',0)); udp.settimeout(2); recorded=[]
        def answer():
            packet,address=udp.recvfrom(4096); recorded.append(packet)
            udp.sendto(packet[:12]+b"\x81\x80"+packet[14:],address)
        thread=threading.Thread(target=answer,daemon=True); thread.start()
        relay=[(socket.AF_INET,socket.SOCK_STREAM,6,'',udp.getsockname())]
        try:
            with patch.object(probe,'_connect',return_value=client),patch.object(probe,'_negotiate',return_value=('8.8.8.8',1080)),patch.object(probe,'_public_addresses',return_value=relay):
                self.assertEqual(probe._dns_test(profile(udp_mode='proxy'),[],2),'DNS_UDP_THROUGH_PROXY_OK')
            thread.join(3); self.assertEqual(recorded[0][:10],b'\x00\x00\x00\x01\x01\x01\x01\x01\x00\x35')
        finally: server.close(); udp.close(); thread.join(3)

    def test_busy_and_worker_serialization_no_password_argv(self):
        probe._gate.acquire()
        try:
            with self.assertRaisesRegex(RuntimeError,"PROBE_BUSY"): probe.probe(profile())
        finally: probe._gate.release()
        process=Mock(returncode=0); process.poll.return_value=0
        process.communicate.return_value=(json.dumps({"ok":True,"steps":[],"exit_ip":"8.8.8.8"})+"\n",None)
        with patch.object(probe.subprocess,"Popen",return_value=process) as launch: result=probe.probe(profile())
        self.assertTrue(result["ok"]); self.assertNotIn("test-password",str(launch.call_args.args))
        self.assertIn("test-password",process.communicate.call_args.args[0])

    def test_real_worker_process_rejects_private_target_without_network(self):
        result=probe.probe(profile(server='127.0.0.1',username=None,password=None),5,1)
        self.assertFalse(result['ok']); self.assertEqual(result['completed'],1)
        self.assertEqual(result['rounds'][0]['steps'][0]['code'],'PROXY_ADDRESS_NOT_PUBLIC')
