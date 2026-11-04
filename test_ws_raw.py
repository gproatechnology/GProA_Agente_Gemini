import http.client
import base64
import hashlib

key = base64.b64encode(b"test-key").decode()
body = (
    "GET / HTTP/1.1\r\n"
    "Host: localhost:18789\r\n"
    "Upgrade: websocket\r\n"
    "Connection: Upgrade\r\n"
    f"Sec-WebSocket-Key: {key}\r\n"
    "Sec-WebSocket-Version: 13\r\n"
    "Authorization: 7e5afe89ced49cea1145c87e98637a27726876fcdd2e488d\r\n"
    "Sec-WebSocket-Protocol: openclaw\r\n"
    "\r\n"
)
conn = http.client.HTTPConnection("127.0.0.1", 18789, timeout=5)
conn.putrequest("GET", "/")
for h in [
    ("Host", "localhost:18789"),
    ("Upgrade", "websocket"),
    ("Connection", "Upgrade"),
    ("Sec-WebSocket-Key", key),
    ("Sec-WebSocket-Version", "13"),
    ("Authorization", "7e5afe89ced49cea1145c87e98637a27726876fcdd2e488d"),
    ("Sec-WebSocket-Protocol", "openclaw"),
]:
    conn.putheader(*h)
conn.endheaders()
resp = conn.getresponse()
print(f"Status: {resp.status} {resp.reason}")
for k, v in resp.getheaders():
    print(f"{k}: {v}")
print()
print(resp.read(200).decode(errors="replace"))
