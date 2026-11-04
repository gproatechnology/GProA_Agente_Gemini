from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import os
import google.generativeai as genai

# Cargar variables de entorno
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("Falta GOOGLE_API_KEY en el archivo .env")

genai.configure(api_key=API_KEY)

app = Flask(__name__)
CORS(app)  # Permite peticiones desde cualquier origen (widget embebido)

MODELO_PREDETERMINADO = "models/gemini-2.5-flash"

@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Endpoint para chatear con Gemini.
    Body JSON: { "mensaje": "texto", "modelo": "models/gemini-2.5-flash" }
    """
    try:
        data = request.get_json()
        if not data or "mensaje" not in data:
            return jsonify({"error": "Se requiere 'mensaje' en el body"}), 400

        mensaje = data["mensaje"]
        nombre_modelo = data.get("modelo", MODELO_PREDETERMINADO)

        modelo = genai.GenerativeModel(nombre_modelo)
        respuesta = modelo.generate_content(mensaje)

        return jsonify({
            "respuesta": respuesta.text,
            "modelo": nombre_modelo,
            "exito": True
        })

    except Exception as e:
        return jsonify({
            "error": str(e),
            "exito": False
        }), 500


@app.route("/api/salud", methods=["GET"])
def salud():
    """Endpoint de salud para verificar que el servidor está activo."""
    return jsonify({"estado": "ok", "servicio": "Agente GProA Gemini Widget"})


@app.route("/api/modelos", methods=["GET"])
def listar_modelos():
    """Lista los modelos disponibles para la API Key."""
    try:
        modelos = genai.list_models()
        modelos_validos = [m.name for m in modelos if 'generateContent' in m.supported_generation_methods]
        return jsonify({"modelos": modelos_validos, "exito": True})
    except Exception as e:
        return jsonify({"error": str(e), "exito": False}), 500


@app.route("/widget.js")
def servir_widget():
    """Sirve el archivo JS del widget embebido."""
    return send_file("widget/widget/js/widget.js")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
