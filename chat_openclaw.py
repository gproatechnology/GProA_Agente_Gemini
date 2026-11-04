import sys
import json
import socket
import base64
import os
import struct

TOKEN = "7e5afe89ced49cea1145c87e98637a27726876fcdd2e488d"
HOST = "127.0.0.1"
PORT = 18789
PATH = "/"
GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

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

def recv_all(sock, n):
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            break
        data += chunk
    return data

def connect_ws():
    key = make_key()
    req = (
        f"GET {PATH} HTTP/1.1\r\n"
        f"Host: localhost:18789\r\n"
        f"Upgrade: websocket\r\n"
        f"Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        f"Sec-WebSocket-Version: 13\r\n"
        f"Authorization: {TOKEN}\r\n"
        f"\r\n"
    ).encode()
    sock = socket.create_connection((HOST, PORT), timeout=10)
    sock.settimeout(10)
    sock.sendall(req)
    status_line = recv_line(sock).decode(errors="replace").strip()
    if "101" not in status_line:
        sock.close()
        raise RuntimeError(f"Handshake failed: {status_line}")
    return sock

def encode_frame(data_bytes):
    length = len(data_bytes)
    if length < 126:
        header = bytes([0x81, length])
    elif length < (1 << 16):
        header = bytes([0x81, 126]) + struct.pack("!H", length)
    else:
        header = bytes([0x81, 127]) + struct.pack("!Q", length)
    return header + data_bytes

def decode_frame(sock):
    b1 = recv_all(sock, 1)
    if not b1:
        return None
    b2 = recv_all(sock, 1)
    if not b2:
        return None
    opcode = b1[0] & 0x0F
    masked = bool(b2[0] & 0x80)
    length = b2[0] & 0x7F
    if length == 126:
        length = struct.unpack("!H", recv_all(sock, 2))[0]
    elif length == 127:
        length = struct.unpack("!Q", recv_all(sock, 8))[0]
    if masked:
        mask = recv_all(sock, 4)
    payload = recv_all(sock, length)
    if masked:
        payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    return opcode, payload

def send_message(sock, text):
    msg = json.dumps({"type": "message", "content": text}).encode()
    sock.sendall(encode_frame(msg))

def recv_message(sock):
    while True:
        frame = decode_frame(sock)
        if frame is None:
            return None
        opcode, payload = frame
        if opcode == 0x01:
            try:
                data = json.loads(payload)
                return data.get("content", payload.decode())
            except Exception:
                return payload.decode(errors="replace")
        elif opcode == 0x08:
            return None

def chat():
    print("Conectando a OpenClaw...", flush=True)
    try:
        sock = connect_ws()
    except Exception as e:
        print(f"Error conectando: {e}", flush=True)
        return

    print("Conectado. Escribe mensajes. Ctrl+C para salir.", flush=True)

    try:
        if len(sys.argv) > 1:
            text = " ".join(sys.argv[1:])
            send_message(sock, text)
            resp = recv_message(sock)
            if resp:
                print(resp, flush=True)
        else:
            while True:
                try:
                    text = input("> ")
                except EOFError:
                    break
                if text.lower() in ("salir", "exit", "quit"):
                    break
                if not text.strip():
                    continue
                send_message(sock, text)
                resp = recv_message(sock)
                if resp is None:
                    print("[Conexion cerrada por el servidor]", flush=True)
                    break
                print(resp, flush=True)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            sock.close()
        except Exception:
            pass

if __name__ == "__main__":
    chat()
