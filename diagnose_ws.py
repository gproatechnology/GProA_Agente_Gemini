import http.client
import base64
import hashlib

# 1. Prueba HTTP básica para ver qué devuelve OpenClaw
print("=== HTTP GET / ===")
conn = http.client.HTTPConnection("127.0.0.1", 18791, timeout=5)
conn.putrequest("GET", "/")
conn.putheader("Host", "localhost:18791")
conn.putheader("Authorization", "7e5afe89ced49cea1145c87e98637a27726876fcdd2e488d")
conn.putheader("User-Agent", "diagnostic")
conn.endheaders()
resp = conn.getresponse()
print(f"Status: {resp.status} {resp.reason}")
for k, v in resp.getheaders():
    print(f"{k}: {v}")
print(resp.read(500).decode(errors="replace"))
conn.close()

# 2. Prueba WebSocket raw con SEC-WEBSOCKET-KEY generado correctamente
print("\n=== WebSocket handshake raw ===")
key = base64.b64encode(b"diagnostic-key-2026").decode()
conn2 = http.client.HTTPConnection("127.0.0.1", 18791, timeout=5)
conn2.putrequest("GET", "/")
conn2.putheader("Host", "localhost:18791")
conn2.putheader("Upgrade", "websocket")
conn2.putheader("Connection", "Upgrade")
conn2.putheader("Sec-WebSocket-Key", key)
conn2.putheader("Sec-WebSocket-Version", "13")
conn2.putheader("Authorization", "7e5afe89ced49cea1145c87e98637a27726876fcdd2e488d")
conn2.endheaders()
try:
    resp2 = conn2.getresponse()
    print(f"Status: {resp2.status} {resp2.reason}")
    for k, v in resp2.getheaders():
        print(f"{k}: {v}")
    print(resp2.read(200).decode(errors="replace"))
except Exception as e:
    print(f"Error en handshake: {e}")
conn2.close()

# 3. Prueba con diferentes paths
for path in ["/gateway", "/ws", "/api/ws", "/__openclaw__/canvas/"]:
    print(f"\n=== GET {path} ===")
    c = http.client.HTTPConnection("127.0.0.1", 18791, timeout=5)
    c.putrequest("GET", path)
    c.putheader("Host", "localhost:18791")
    c.putheader("Authorization", "7e5afe89ced49cea1145c87e98637a27726876fcdd2e488d")
    c.endheaders()
    try:
        r = c.getresponse()
        print(f"Status: {r.status} {r.reason}")
        print(r.read(200).decode(errors="replace"))
    except Exception as e:
        print(f"Error: {e}")
    c.close()
