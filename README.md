# Agente GProA Gemini

Agente de software basado en **Google Gemini** para auditar, explicar y responder preguntas sobre tus proyectos de desarrollo.

## Estructura

| Archivo | Propósito |
|---------|-----------|
| `agente_gemini.py` | Agente principal: responde preguntas y audita archivos de código |
| `start-agent.ps1` | Script de inicio: crea `.venv`, instala dependencias y abre `.env` |
| `requirements.txt` | Dependencias de Python (`google-generativeai`, `python-dotenv`) |
| `.env.example` | Plantilla para tu archivo `.env` (no subir a Git) |
| `.env` | **Tu archivo privado con la API Key** (no compartir, no subir) |

## Primer uso

1. Ejecuta `.\start-agent.ps1` (crea el entorno virtual e instala dependencias).
2. Edita `.env` y agrega tu `GOOGLE_API_KEY` de Google AI Studio.
3. Ejecuta `python agente_gemini.py`.
4. Escribe tus preguntas o usa `auditar <nombre_de_archivo>` para analizar código.

## Seguridad

- Nunca subas `.env` a GitHub. Está en `.gitignore`.
- Tu API Key de Google es privada. Trátala como una contraseña.
