import sys
import json
import socket
import base64
import struct
import os

TOKEN = "7e5afe89ced49cea1145c87e98637a27726876fcdd2e488d"
HOST = "127.0.0.1"
PORT = 18789

def make_key():
    return base64.b64encode(os.urandom(16)).decode()

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

def try_path(path):
    key = make_key()
    req = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: localhost:18789\r\n"
        f"Upgrade: websocket\r\n"
        f"Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        f"Sec-WebSocket-Version: 13\r\n"
        f"Authorization: {TOKEN}\r\n"
        f"\r\n"
    ).encode()
    try:
        sock = socket.create_connection((HOST, PORT), timeout=3)
        sock.settimeout(3)
        sock.sendall(req)
        status_line = recv_line(sock).decode(errors="replace").strip()
        headers = {}
        while True:
            line = recv_line(sock)
            if line in (b"\r\n", b"\n", b""):
                break
            if b":" in line:
                k, v = line.split(b":", 1)
                headers[k.decode().strip().lower()] = v.decode().strip()
        sock.close()
        return status_line, headers
    except Exception as e:
        return f"ERROR: {e}", {}

if __name__ == "__main__":
    paths = ["/", "/__openclaw__/canvas/", "/__openclaw__/canvas", "/gateway", "/ws"]
    for p in paths:
        status, hdrs = try_path(p)
        print(f"Path={p} -> {status}")
        if "101" in status:
            print(f"  SUCCESS! Headers: {hdrs}")
            break
