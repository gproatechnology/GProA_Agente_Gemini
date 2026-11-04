import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai

# --- Configuración de la página ---
st.set_page_config(
    page_title="Agente GProA Gemini",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Cargar variables de entorno ---
load_dotenv()
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
    ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro", "gemini-pro"],
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
def preguntar(pregunta: str, contexto: str = "", nombre_modelo: str = "gemini-1.5-pro") -> str:
    prompt = f"{contexto}\n\nPregunta: {pregunta}" if contexto else pregunta
    modelo = genai.GenerativeModel(nombre_modelo)
    respuesta = modelo.generate_content(prompt)
    return respuesta.text

def auditar_archivo(ruta_proyecto: str, nombre_archivo: str, nombre_modelo: str = "gemini-1.5-pro") -> str:
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
    modelo = genai.GenerativeModel(nombre_modelo)
    respuesta = modelo.generate_content(prompt)
    return respuesta.text

def auditar_proyecto(ruta_proyecto: str, nombre_modelo: str = "gemini-1.5-pro") -> str:
    prompt = (
        "Eres un ingeniero de software senior. Dame un resumen ejecutivo "
        f"del proyecto en la carpeta: {ruta_proyecto}"
    )
    modelo = genai.GenerativeModel(nombre_modelo)
    respuesta = modelo.generate_content(prompt)
    return respuesta.text

# --- Interfaz de usuario ---
st.title("🤖 Agente GProA Gemini")
st.markdown("Asistente de código basado en **Google Gemini** para analizar proyectos de desarrollo.")

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
