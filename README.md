# Agente GProA Gemini

Agente de software basado en **Google Gemini** para auditar, explicar y responder preguntas sobre tus proyectos de desarrollo.

## Estructura

| Archivo | Propósito |
|---------|-----------|
| `agente_gemini.py` | Lógica del agente (funciones `preguntar()` y `auditar_proyecto()`) |
| `ui/streamlit_app.py` | Interfaz web con Streamlit (chat, auditoría de archivos, resumen de proyectos) |
| `start-agent.ps1` | Script de inicio: crea `.venv`, instala dependencias, prepara `.env` |
| `requirements.txt` | Dependencias de Python (`google-generativeai`, `python-dotenv`, `streamlit`) |
| `.env.example` | Plantilla para tu archivo `.env` (no compartir) |
| `.env` | **Tu archivo privado con la API Key** (no compartir, no subir) |
| `README.md` | Instrucciones de uso |

## Primer uso

1. Ejecuta `.\start-agent.ps1` (crea el entorno virtual e instala dependencias).
2. Edita `.env` y agrega tu `GOOGLE_API_KEY` de Google AI Studio.
3. Ejecuta `.\start-agent.ps1` y selecciona la opción **1** para abrir la interfaz web.
4. O ejecuta `python agente_gemini.py` para usar la consola.

## Seguridad

- Nunca subas `.env` a GitHub. Está en `.gitignore`.
- Tu API Key de Google es privada. Trátala como una contraseña.
