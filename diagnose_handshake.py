import sys
import json
import socket
import hashlib
import base64
import struct

TOKEN = "7e5afe89ced49cea1145c87e98637a27726876fcdd2e488d"
GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

def make_key():
    return base64.b64encode(b"kilo-diag-2026").decode()

def build_handshake(host, path="/", extra_headers=None):
    key = make_key()
    lines = [
        f"GET {path} HTTP/1.1",
        f"Host: {host}",
        "Upgrade: websocket",
        "Connection: Upgrade",
        f"Sec-WebSocket-Key: {key}",
        "Sec-WebSocket-Version: 13",
        f"Authorization: {TOKEN}",
    ]
    if extra_headers:
        for k, v in extra_headers.items():
            lines.append(f"{k}: {v}")
    lines.append("")
    return "\r\n".join(lines).encode()

def recv_line(sock):
    line = b""
    while True:
        chunk = sock.recv(1)
        if not chunk:
            break
        line += chunk
        if line.endswith(b"\n"):
            break
    return line

def recv_all(sock, n):
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            break
        data += chunk
    return data

def try_handshake(host, path, extra_headers=None, timeout=2):
    try:
        sock = socket.create_connection(("127.0.0.1", 18789), timeout=timeout)
        sock.settimeout(timeout)
        sock.sendall(build_handshake(host, path, extra_headers))

        status_line = recv_line(sock)
        headers = {}
        while True:
            line = recv_line(sock)
            if line in (b"\r\n", b"\n", b""):
                break
            if b":" in line:
                k, v = line.split(b":", 1)
                headers[k.decode().strip().lower()] = v.decode().strip()
        sock.close()
        return status_line.decode(errors="replace").strip(), headers
    except Exception as e:
        return f"ERROR: {e}", {}

if __name__ == "__main__":
    host = "localhost:18789"
    configs = [
        ("/", None),
        ("/ws", None),
        ("/gateway", None),
        ("/__openclaw__/canvas/", None),
        ("/", {"Origin": "http://localhost:18789"}),
        ("/", {"Sec-WebSocket-Protocol": "openclaw"}),
        ("/", {"Origin": "http://localhost:18789", "Sec-WebSocket-Protocol": "openclaw"}),
    ]
    for path, extra in configs:
        status, hdrs = try_handshake(host, path, extra)
        print(f"Path={path}  Extra={extra}  -> {status}", flush=True)
        if "101" in status:
            print(f"  SUCCESS! Headers: {hdrs}", flush=True)
            break
