import streamlit as st
import os
import sys
from dotenv import load_dotenv
import google.generativeai as genai

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cache import obtener_cache

# --- Configuración de la página ---
st.set_page_config(
    page_title="GProA Gemini - Asistente IA",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS personalizado con tema GProA ---
st.markdown("""
<style>
    :root {
        --gproa-dark: #050812;
        --gproa-darker: #0a0f1c;
        --gproa-primary: #00e0ff;
        --gproa-secondary: #8a2be2;
        --gproa-gray: #b8c5d6;
        --gproa-bg: #050812;
        --gproa-card: #0a0f1c;
        --gproa-border: rgba(0, 224, 255, 0.15);
    }

    .stApp {
        background-color: var(--gproa-bg);
        color: #ffffff;
    }

    .main > div {
        padding-top: 2rem;
    }

    /* Header */
    .header-container {
        background: linear-gradient(180deg, #050812 0%, #0a0f1c 100%);
        border-bottom: 1px solid var(--gproa-border);
        padding: 2rem 1rem;
        margin-bottom: 2rem;
        text-align: center;
    }

    .header-title {
        font-family: 'Orbitron', monospace;
        font-size: 2.5rem;
        color: #ffffff;
        margin: 0;
        letter-spacing: 2px;
        text-transform: uppercase;
    }

    .header-subtitle {
        color: var(--gproa-gray);
        font-size: 1rem;
        margin-top: 0.5rem;
    }

    /* Sidebar */
    .stSidebar {
        background: linear-gradient(180deg, #0a0f1c 0%, #050812 100%);
        border-right: 1px solid var(--gproa-border);
    }

    .stSidebar .stSelectbox > div > div {
        background-color: rgba(0, 0, 0, 0.3);
        border: 1px solid var(--gproa-border);
        color: #ffffff;
    }

    .stSidebar .stButton > button {
        background: linear-gradient(135deg, var(--gproa-primary), var(--gproa-secondary));
        color: var(--gproa-dark);
        border: none;
        border-radius: 8px;
        font-weight: 700;
        width: 100%;
    }

    .stSidebar .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(0, 224, 255, 0.2);
    }

    /* Chat messages */
    .stChatMessage {
        background: rgba(20, 30, 50, 0.6);
        border: 1px solid var(--gproa-border);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }

    .stChatMessage.user {
        border-left: 4px solid var(--gproa-primary);
    }

    .stChatMessage.assistant {
        border-left: 4px solid var(--gproa-secondary);
    }

    /* Input */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: rgba(0, 0, 0, 0.3);
        border: 1px solid var(--gproa-border);
        color: #ffffff;
        border-radius: 8px;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--gproa-primary);
        box-shadow: 0 0 0 2px rgba(0, 224, 255, 0.2);
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--gproa-primary), var(--gproa-secondary));
        color: var(--gproa-dark);
        border: none;
        border-radius: 8px;
        font-weight: 700;
        padding: 0.75rem 1.5rem;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(0, 224, 255, 0.2);
    }

    /* Cards */
    .feature-card {
        background: linear-gradient(145deg, rgba(20, 30, 50, 0.9), rgba(10, 20, 35, 0.95));
        border: 1px solid var(--gproa-border);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }

    .feature-card h3 {
        color: var(--gproa-primary);
        margin-top: 0;
    }

    /* Divider */
    hr {
        border: none;
        border-top: 1px solid var(--gproa-border);
        margin: 2rem 0;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- Cargar variables de entorno ---
load_dotenv()

_cache = obtener_cache()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    st.error("❌ Falta GOOGLE_API_KEY en el archivo .env")
    st.info("Edita el archivo .env y agrega tu clave de Google AI Studio.")
    st.stop()

genai.configure(api_key=API_KEY)

# --- Selección de modelo ---
st.sidebar.title("⚙️ Configuración")
modelo_disponible = st.sidebar.selectbox(
    "Modelo de Gemini:",
    ["models/gemini-2.5-flash", "models/gemini-2.5-flash-lite", "models/gemini-2.5-pro", "models/gemini-flash-latest", "models/gemini-pro-latest"],
    index=0
)

if st.sidebar.button("Listar modelos disponibles"):
    try:
        modelos = genai.list_models()
        modelos_validos = [m.name for m in modelos if 'generateContent' in m.supported_generation_methods]
        st.sidebar.success("Modelos disponibles:")
        for m in modelos_validos:
            st.sidebar.write(f"• {m}")
    except Exception as e:
        st.sidebar.error(f"Error listando modelos: {e}")

# --- Funciones del agente ---
def preguntar(pregunta: str, contexto: str = "", nombre_modelo: str = "models/gemini-2.5-flash") -> str:
    prompt = f"{contexto}\n\nPregunta: {pregunta}" if contexto else pregunta
    respuesta_cache = _cache.obtener(prompt)
    if respuesta_cache is not None:
        return respuesta_cache
    modelo = genai.GenerativeModel(nombre_modelo)
    respuesta = modelo.generate_content(prompt)
    texto = respuesta.text
    _cache.guardar(prompt, texto)
    return texto

def auditar_archivo(ruta_proyecto: str, nombre_archivo: str, nombre_modelo: str = "models/gemini-2.5-flash") -> str:
    ruta_completa = os.path.join(ruta_proyecto, nombre_archivo)
    if not os.path.exists(ruta_completa):
        return f"❌ No se encontró el archivo: {ruta_completa}"
    try:
        with open(ruta_completa, "r", encoding="utf-8") as f:
            contenido = f.read()
    except Exception as e:
        return f"❌ Error leyendo el archivo: {e}"
    
    prompt = (
        "Eres un ingeniero de software senior. Analiza el siguiente código "
        "y dime qué hace, si tiene problemas de seguridad o rendimiento, "
        "y cómo mejorarlo:\n\n"
        f"{contenido}"
    )
    respuesta_cache = _cache.obtener(prompt)
    if respuesta_cache is not None:
        return respuesta_cache
    modelo = genai.GenerativeModel(nombre_modelo)
    respuesta = modelo.generate_content(prompt)
    texto = respuesta.text
    _cache.guardar(prompt, texto)
    return texto

def auditar_proyecto(ruta_proyecto: str, nombre_modelo: str = "models/gemini-2.5-flash") -> str:
    prompt = (
        "Eres un ingeniero de software senior. Dame un resumen ejecutivo "
        f"del proyecto en la carpeta: {ruta_proyecto}"
    )
    respuesta_cache = _cache.obtener(prompt)
    if respuesta_cache is not None:
        return respuesta_cache
    modelo = genai.GenerativeModel(nombre_modelo)
    respuesta = modelo.generate_content(prompt)
    texto = respuesta.text
    _cache.guardar(prompt, texto)
    return texto

# --- Interfaz de usuario ---
st.markdown("""
<div class="header-container">
    <h1 class="header-title">🤖 GProA Gemini</h1>
    <p class="header-subtitle">Asistente de IA para análisis de proyectos de desarrollo</p>
</div>
""", unsafe_allow_html=True)

# Sidebar con navegación
st.sidebar.title("📋 Menú")
opcion = st.sidebar.radio(
    "Selecciona una opción:",
    ["Chat con Gemini", "Auditar archivo de código", "Auditar proyecto (resumen)"]
)

# --- Opción 1: Chat general ---
if opcion == "Chat con Gemini":
    st.header("💬 Chat con Gemini")
    
    if "historial_chat" not in st.session_state:
        st.session_state.historial_chat = []
    
    # --- Botones rápidos de preguntas pre-cargadas (0 tokens) ---
    st.subheader("⚡ Preguntas frecuentes (respuesta instantánea)")
    st.caption("Haz clic en cualquier botón para ver la respuesta oficial sin gastar tokens de la API.")
    
    preguntas_seed = list(_cache.entradas_seed.keys())
    if preguntas_seed:
        cols = st.columns(2)
        for idx, pregunta_raw in enumerate(preguntas_seed):
            # Mostrar una versión legible de la pregunta (primera letra mayúscula, sin normalización)
            etiqueta = pregunta_raw[0].upper() + pregunta_raw[1:] if pregunta_raw else pregunta_raw
            with cols[idx % 2]:
                if st.button(f"❓ {etiqueta}", key=f"seed_{idx}", use_container_width=True):
                    respuesta_seed = _cache.obtener(pregunta_raw)
                    if respuesta_seed:
                        st.session_state.historial_chat.append({"usuario": pregunta_raw, "agente": respuesta_seed})
                    st.rerun()
    st.divider()
    
    pregunta = st.text_area("Escribe tu pregunta:", height=100, placeholder="Ej: ¿Cómo funciona el motor KNN de GlucAI?")
    
    if st.button("Enviar", type="primary"):
        if pregunta.strip():
            with st.spinner("Pensando..."):
                respuesta = preguntar(pregunta, nombre_modelo=modelo_disponible)
            st.session_state.historial_chat.append({"usuario": pregunta, "agente": respuesta})
        else:
            st.warning("Escribe una pregunta antes de enviar.")
    
    # Mostrar historial
    for i, item in enumerate(reversed(st.session_state.historial_chat)):
        with st.chat_message("user"):
            st.write(item["usuario"])
        with st.chat_message("assistant"):
            st.write(item["agente"])
        st.divider()

# --- Opción 2: Auditar archivo ---
elif opcion == "Auditar archivo de código":
    st.header("📄 Auditar archivo de código")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        ruta_proyecto = st.text_input("Ruta del proyecto:", value=".", help="Ruta relativa o absoluta al proyecto a auditar")
    with col2:
        nombre_archivo = st.text_input("Nombre del archivo:", placeholder="src/js/knn/clasificador.js")
    
    if st.button("Analizar archivo", type="primary"):
        if nombre_archivo.strip():
            with st.spinner("Analizando archivo..."):
                resultado = auditar_archivo(ruta_proyecto, nombre_archivo, nombre_modelo=modelo_disponible)
            st.subheader("Resultado del análisis:")
            st.markdown(resultado)
        else:
            st.warning("Ingresa el nombre del archivo.")

# --- Opción 3: Auditar proyecto completo ---
elif opcion == "Auditar proyecto (resumen)":
    st.header("📊 Auditar proyecto completo")
    
    ruta_proyecto = st.text_input("Ruta del proyecto:", value=".", help="Ruta al proyecto a analizar")
    
    if st.button("Generar resumen del proyecto", type="primary"):
        if ruta_proyecto.strip():
            with st.spinner("Analizando proyecto..."):
                resultado = auditar_proyecto(ruta_proyecto, nombre_modelo=modelo_disponible)
            st.subheader("Resumen del proyecto:")
            st.markdown(resultado)
        else:
            st.warning("Ingresa la ruta del proyecto.")

# --- Pie de página ---
st.divider()
st.caption("⚠️ Tu GOOGLE_API_KEY está guardada localmente en .env y no se comparte.")
st.caption("Desarrollado por GProA Technology • Tecnología de IA para automatización")
