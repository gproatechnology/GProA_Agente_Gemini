# Agente GProA Gemini Widget - Backend API

API REST que expone un endpoint `/api/chat` para ser consumido por un widget embebido en cualquier página web.

## Estructura

| Archivo | Propósito |
|---------|-----------|
| `src/api/main.py` | Servidor Flask con endpoint `/api/chat`, `/api/salud`, `/api/modelos` |
| `requirements.txt` | Dependencias de Python |
| `.env.example` | Plantilla para GOOGLE_API_KEY |
| `.gitignore` | Ignora .env y .venv |
| `README.md` | Este archivo |

## Primer uso

1. Copia `.env.example` a `.env` y agrega tu `GOOGLE_API_KEY`
2. Instala dependencias: `pip install -r requirements.txt`
3. Ejecuta: `python src/api/main.py`
4. El servidor estará en `http://localhost:5000`

## Endpoints

### POST /api/chat
Envía un mensaje a Gemini y obtiene una respuesta.

**Request:**
```json
{
  "mensaje": "¿Cómo funciona el motor KNN de GlucAI?",
  "modelo": "models/gemini-2.5-flash"
}
```

**Response:**
```json
{
  "respuesta": "El motor KNN...",
  "modelo": "models/gemini-2.5-flash",
  "exito": true
}
```

### GET /api/salud
Verifica que el servidor esté activo.

### GET /api/modelos
Lista los modelos disponibles para la API Key.

## Seguridad

- Nunca subas `.env` a GitHub. Está en `.gitignore`.
- Tu API Key es privada.

## Despliegue

Puedes desplegar en Render como Web Service o Static Site.
Build command: `pip install -r requirements.txt`
Start command: `gunicorn src.api.main:app`