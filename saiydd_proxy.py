import sys
import json
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

OLLAMA_URL = "http://localhost:11434/api/generate"
PROXY_PORT = 3000

SYSTEM_PROMPT = (
    "Eres un asistente educativo infantil llamado Orion para niños de 4 a 8 años. "
    "Responde en español, corto, amigable y seguro. "
    "No sugieras actividades peligrosas. "
    "Si no sabes la respuesta, di: 'No estoy seguro, pero podemos seguir jugando'. "
    "Nunca reveles información personal."
)

BLOCKLIST = ["https://", "http://", "ftp://", "email", "contraseña", "password", "dirección", "address"]
MAX_RESPONSE = 300

def is_safe(text):
    t = (text or "").lower()
    if not t.strip():
        return False
    return not any(b in t for b in BLOCKLIST)

def clamp(text, max_len=MAX_RESPONSE):
    if not text:
        return ""
    text = text.strip()
    return text if len(text) <= max_len else text[:max_len - 3] + "..."

def ask_ollama(prompt):
    payload = json.dumps({
        "model": "qwen2.5-coder:1.5b-16k",
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_ctx": 16384,
            "temperature": 0.7,
            "top_p": 0.9
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "")
    except Exception as e:
        print(f"[proxy] Error llamando a Ollama: {e}", flush=True)
        return ""

class ProxyHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(content_len).decode("utf-8"))
            message = (body.get("message") or "").strip()
            child_id = body.get("childId") or "unknown"

            if not is_safe(message):
                self.send_json(200, {"reply": "No podemos procesar ese mensaje. Probá con otra cosa."})
                return

            prompt = f"{SYSTEM_PROMPT}\n\nNiño: {message}\nOrion:"
            raw = ask_ollama(prompt)

            reply = clamp(raw)
            if not is_safe(reply):
                reply = "No estoy seguro, pero podemos seguir jugando."

            self.send_json(200, {"reply": reply})
        except Exception as e:
            print(f"[proxy] Error interno: {e}", flush=True)
            self.send_json(500, {"reply": "Ups, algo falló. Intentá de nuevo."})

    def send_json(self, code, obj):
        payload = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):
        sys.stderr.write(f"[proxy] {args[0]}\n")

def run():
    server = HTTPServer(("127.0.0.1", PROXY_PORT), ProxyHandler)
    print(f"[proxy] SaIyDD proxy escuchando en http://127.0.0.1:{PROXY_PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == "__main__":
    run()
