# Shared behavior ported from the paired heyinkcode/Marzban-node Fork (AGPL-3.0).
"""Bounded diagnostics of one managed proxy; never touches the business core.

The worker uses the standard HTTP CONNECT / SOCKS5 wire protocols. It does
not claim to be an end-to-end Xray/client test. Only fixed public test targets
are used. Credentials stay on stdin/memory, not argv, files or diagnostics.
"""
import base64
import http.client
import ipaddress
import json
import secrets
import socket
import ssl
import struct
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

if __package__:
    from .managed_outbounds import _profile
else:
    from managed_outbounds import _profile

CAPABILITY = "managed-egress-probe-v1"
_gate = threading.BoundedSemaphore(1)
TARGET = "www.cloudflare.com"
DNS_SERVER = "1.1.1.1"
MAX_SECONDS = 30


class ProbeFailure(Exception):
    def __init__(self, code):
        self.code = code


def validate_request(profile, timeout, attempts):
    if type(timeout) is not int or timeout not in (5, 10):
        raise ValueError("Probe timeout must be 5 or 10 seconds")
    if type(attempts) is not int or attempts not in (1, 3):
        raise ValueError("Probe attempts must be 1 or 3")
    if not isinstance(profile, dict):
        raise ValueError("Invalid proxy profile")
    candidate = dict(profile, tag="managed-residential-egress")
    _profile(candidate, set())
    # _profile validates the original runtime policy, including UDP mode.
    if candidate.get("udp_mode", "legacy") not in ("legacy", "proxy", "tcp_only"):
        raise ValueError("Invalid UDP mode")
    if candidate.get("udp_mode") == "proxy" and candidate.get("protocol") != "socks":
        raise ValueError("UDP proxy requires SOCKS5")
    for key in ("username", "password"):
        value = candidate.get(key)
        if value is not None and len(value.encode("utf8")) > 255:
            raise ValueError("Proxy credentials exceed 255 UTF-8 bytes")
    return candidate


def _public_addresses(host, port):
    answers = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    if not answers or len(answers) > 64:
        raise ProbeFailure("PROXY_DNS_FAILED")
    for family, _, _, _, address in answers:
        if family not in (socket.AF_INET, socket.AF_INET6) or not ipaddress.ip_address(address[0]).is_global:
            raise ProbeFailure("PROXY_ADDRESS_NOT_PUBLIC")
    return answers


def _read(sock, count):
    result = b""
    while len(result) < count:
        chunk = sock.recv(count - len(result))
        if not chunk:
            raise ProbeFailure("PROXY_PROTOCOL_ERROR")
        result += chunk
    return result


def _socks_address(sock):
    kind = _read(sock, 1)[0]
    if kind == 1:
        host = socket.inet_ntoa(_read(sock, 4))
    elif kind == 4:
        host = socket.inet_ntop(socket.AF_INET6, _read(sock, 16))
    elif kind == 3:
        host = _read(sock, _read(sock, 1)[0]).decode("ascii")
    else:
        raise ProbeFailure("PROXY_PROTOCOL_ERROR")
    return host, struct.unpack("!H", _read(sock, 2))[0]


def _negotiate(sock, profile, host=TARGET, port=443, command=1):
    user, password = profile.get("username"), profile.get("password")
    if profile["protocol"] == "http":
        auth = ""
        if user is not None:
            token = base64.b64encode((user + ":" + password).encode("utf8")).decode("ascii")
            auth = "Proxy-Authorization: Basic " + token + "\r\n"
        sock.sendall((f"CONNECT {host}:{port} HTTP/1.1\r\nHost: {host}:{port}\r\n" + auth + "\r\n").encode("ascii"))
        header = b""
        while not header.endswith(b"\r\n\r\n") and len(header) < 8192:
            header += _read(sock, 1)
        line = header.split(b"\r\n", 1)[0].split()
        if len(line) < 2 or not line[1].isdigit():
            raise ProbeFailure("PROXY_PROTOCOL_ERROR")
        status = int(line[1])
        if status == 407:
            raise ProbeFailure("PROXY_AUTH_REJECTED")
        if status != 200:
            raise ProbeFailure("PROXY_TARGET_REJECTED")
        return None
    method = 2 if user is not None else 0
    sock.sendall(bytes((5, 1, method)))
    if _read(sock, 2) != bytes((5, method)):
        raise ProbeFailure("PROXY_AUTH_REJECTED")
    if method == 2:
        encoded_user, encoded_pass = user.encode("utf8"), password.encode("utf8")
        sock.sendall(bytes((1, len(encoded_user))) + encoded_user + bytes((len(encoded_pass),)) + encoded_pass)
        if _read(sock, 2) != b"\x01\x00":
            raise ProbeFailure("PROXY_AUTH_REJECTED")
    if command == 3:
        destination = b"\x01\x00\x00\x00\x00\x00\x00"
    else:
        encoded_host = host.encode("idna")
        destination = bytes((3, len(encoded_host))) + encoded_host + struct.pack("!H", port)
    sock.sendall(bytes((5, command, 0)) + destination)
    reply = _read(sock, 3)
    if reply[0] != 5 or reply[2] != 0:
        raise ProbeFailure("PROXY_PROTOCOL_ERROR")
    if reply[1] != 0:
        raise ProbeFailure("UDP_ASSOCIATE_REJECTED" if command == 3 else "PROXY_TARGET_REJECTED")
    return _socks_address(sock)


def _connect(answers, timeout):
    # Pinned numeric address: DNS cannot rebind between validation and connect.
    deadline, failure = time.monotonic() + timeout, None
    for family, kind, proto, _, address in answers[:4]:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError()
        sock = socket.socket(family, kind, proto)
        sock.settimeout(remaining)
        try:
            sock.connect(address)
            return sock
        except OSError as exc:
            failure = exc
            sock.close()
    raise failure or ProbeFailure("CONNECTION_FAILED")


def _dns_query():
    token = secrets.token_bytes(2)
    return token + b"\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00" + b"\x07example\x03com\x00\x00\x01\x00\x01"


def _check_dns(data, query):
    if len(data) < 12 or data[:2] != query[:2] or not data[2] & 128 or data[3] & 15:
        raise ProbeFailure("DNS_INVALID_RESPONSE")


def _dns_test(profile, answers, timeout):
    query = _dns_query()
    with _connect(answers, timeout) as tcp:
        if profile.get("udp_mode") == "tcp_only":
            _negotiate(tcp, profile, DNS_SERVER, 53)
            tcp.sendall(struct.pack("!H", len(query)) + query)
            length = struct.unpack("!H", _read(tcp, 2))[0]
            if length > 4096:
                raise ProbeFailure("DNS_INVALID_RESPONSE")
            _check_dns(_read(tcp, length), query)
            return "DNS_TCP_THROUGH_PROXY_OK"
        relay_host, relay_port = _negotiate(tcp, profile, command=3)
        if relay_host in ("0.0.0.0", "::"):
            relay_host = tcp.getpeername()[0]
        relay = _public_addresses(relay_host, relay_port)[0]
        packet = b"\x00\x00\x00\x01" + socket.inet_aton(DNS_SERVER) + struct.pack("!H", 53) + query
        with socket.socket(relay[0], socket.SOCK_DGRAM) as udp:
            udp.settimeout(timeout)
            udp.connect(relay[4])
            udp.send(packet)
            response = udp.recv(4096)
        if len(response) < 10 or response[:4] != b"\x00\x00\x00\x01" or response[4:10] != packet[4:10]:
            raise ProbeFailure("UDP_INVALID_RESPONSE")
        _check_dns(response[10:], query)
        return "DNS_UDP_THROUGH_PROXY_OK"


def run_round(profile, timeout):
    steps = []
    stage, started, sock = "proxy_dns", time.monotonic(), None
    def done(code="OK"):
        steps.append({"stage": stage, "status": "ok", "code": code, "duration_ms": round((time.monotonic()-started)*1000)})
    try:
        answers = _public_addresses(profile["server"], profile["port"])
        done()
        stage, started = "proxy_tcp", time.monotonic()
        sock = _connect(answers, timeout)
        done()
        stage, started = "proxy_auth", time.monotonic()
        _negotiate(sock, profile)
        done()
        stage, started = "https_exit", time.monotonic()
        with ssl.create_default_context().wrap_socket(sock, server_hostname=TARGET) as tls:
            sock = tls
            tls.sendall((f"GET /cdn-cgi/trace HTTP/1.1\r\nHost: {TARGET}\r\nConnection: close\r\n\r\n").encode("ascii"))
            response = http.client.HTTPResponse(tls)
            response.begin()
            if response.status != 200:
                raise ProbeFailure("HTTPS_TARGET_FAILED")
            text = response.read(8193)
            if len(text) > 8192:
                raise ProbeFailure("HTTPS_INVALID_RESPONSE")
            values = dict(line.split("=", 1) for line in text.decode("ascii").splitlines() if "=" in line)
            address = ipaddress.ip_address(values.get("ip", ""))
            if not address.is_global:
                raise ProbeFailure("HTTPS_INVALID_RESPONSE")
            exit_ip = str(address)
        sock = None
        done()
        stage, started = "dns_udp", time.monotonic()
        if profile.get("udp_mode", "legacy") == "legacy":
            steps.append({"stage":stage,"status":"not_tested","code":"LEGACY_UDP_NOT_VERIFIED","duration_ms":0})
        else:
            done(_dns_test(profile, answers, timeout))
        return {"ok":True,"steps":steps,"exit_ip":exit_ip}
    except Exception as exc:
        code = exc.code if isinstance(exc, ProbeFailure) else (
            "TLS_VERIFY_FAILED" if isinstance(exc, ssl.SSLCertVerificationError) else
            "TIMEOUT" if isinstance(exc, (TimeoutError, socket.timeout)) else
            "PROXY_DNS_FAILED" if isinstance(exc, socket.gaierror) else "CONNECTION_FAILED")
        steps.append({"stage":stage,"status":"failed","code":code,"duration_ms":round((time.monotonic()-started)*1000)})
        return {"ok":False,"steps":steps}
    finally:
        if sock is not None:
            sock.close()


def summary(rounds, attempts):
    return {"version":1,"source":"main-egress-probe","scope":"main-to-proxy-to-fixed-target",
            "ok":len(rounds)==attempts and all(r["ok"] for r in rounds),
            "attempts":attempts,"completed":len(rounds),"rounds":rounds,
            "checked_at":datetime.now(timezone.utc).isoformat()}


def probe(profile, timeout=5, attempts=1):
    profile = validate_request(profile, timeout, attempts)
    if not _gate.acquire(blocking=False):
        raise RuntimeError("PROBE_BUSY")
    process = None
    try:
        process = subprocess.Popen([sys.executable,"-B","-u",str(Path(__file__).resolve()),"--worker"],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,encoding="utf8")
        payload = json.dumps({"profile":profile,"timeout":timeout,"attempts":attempts})
        try:
            output, _ = process.communicate(payload, timeout=MAX_SECONDS)
        except subprocess.TimeoutExpired:
            process.kill()
            output, _ = process.communicate()
        rounds = []
        for line in output.splitlines()[:3]:
            try:
                value = json.loads(line)
                if isinstance(value,dict) and isinstance(value.get("ok"),bool):
                    rounds.append(value)
            except ValueError:
                pass
        result = summary(rounds, attempts)
        if len(rounds) < attempts:
            result["code"] = "TOTAL_DEADLINE" if process.returncode else "PROBE_INCOMPLETE"
        return result
    finally:
        if process is not None and process.poll() is None:
            process.kill(); process.wait(timeout=3)
        _gate.release()


if __name__ == "__main__" and sys.argv[1:] == ["--worker"]:
    request = json.loads(sys.stdin.read(16384))
    profile = validate_request(request["profile"],request["timeout"],request["attempts"])
    for _ in range(request["attempts"]):
        result = run_round(profile,request["timeout"])
        print(json.dumps(result),flush=True)
        if any(s["code"] in ("PROXY_AUTH_REJECTED","PROXY_ADDRESS_NOT_PUBLIC") for s in result["steps"]):
            break
