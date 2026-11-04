# Agente GProA Gemini - Widget Embebible

Widget de asistente de IA que se puede insertar en cualquier página web mediante un simple script.

## Estructura

```
widget/
├── css/
│   └── widget.css       # Estilos del widget (tema GProA)
├── js/
│   └── widget.js        # Lógica del widget (auto-inicializable)
├── index.html           # Página de demostración del widget
└── ejemplo.html         # Ejemplo de inserción en página externa
```

## Cómo usar

### Opción 1: Incluir el widget en cualquier página

Agrega este script al final de tu `<body>`:

```html
<script src="https://TU_DOMINIO.com/widget/js/widget.js"></script>
```

El widget aparecerá automáticamente en la esquina inferior derecha.

### Opción 2: Usar el widget desde tu propio servidor

1. Sube la carpeta `widget/` a tu servidor
2. Incluye el script:
   ```html
   <script src="/ruta/a/widget/js/widget.js"></script>
   ```

## API del widget

Una vez cargado, el widget expone una API global en `window.gproaGemini`:

```javascript
// Abrir el widget
window.gproaGemini.abrir();

// Cerrar el widget
window.gproaGemini.cerrar();

// Alternar visibilidad
window.gproaGemini.alternar();

// Enviar un mensaje directamente
window.gproaGemini.enviar("¿Cómo funciona el motor KNN?");
```

## Backend requerido

El widget necesita un backend que exponga el endpoint `POST /api/chat`. Puedes usar el backend incluido en este repositorio (`src/api/main.py`) o crear tu propio endpoint que acepte:

```json
{
  "mensaje": "texto del usuario",
  "modelo": "models/gemini-2.5-flash"
}
```

Y devuelva:
```json
{
  "respuesta": "texto de respuesta",
  "modelo": "models/gemini-2.5-flash",
  "exito": true
}
```

## Configurar URL del backend

Edita `widget/js/widget.js` y cambia `CONFIG.API_BASE_URL` por la URL de tu backend desplegado:

```javascript
const CONFIG = {
    API_BASE_URL: 'https://tu-backend.onrender.com',
    ENDPOINT_CHAT: '/api/chat',
    MODELO_PREDETERMINADO: 'models/gemini-2.5-flash'
};
```

## Despliegue

### Backend (Render)
1. Sube `src/api/main.py` y `requirements.txt` a un repositorio
2. Conecta a Render como Web Service
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn src.api.main:app`
5. Agrega tu `GOOGLE_API_KEY` como variable de entorno

### Widget
Sube la carpeta `widget/` a tu servidor web o incluye los archivos directamente en tu sitio.

## Seguridad

- El widget solo envía el mensaje del usuario al backend
- El backend maneja la API Key de Google (nunca expuesta al cliente)
- Todas las comunicaciones van por HTTPS