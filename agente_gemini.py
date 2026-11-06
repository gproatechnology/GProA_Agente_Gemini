import os
import time
from dotenv import load_dotenv
import google.generativeai as genai

from cache import obtener_cache

load_dotenv()

_cache = obtener_cache()


def _cargar_api_keys():
    claves = []
    raw = os.getenv("GOOGLE_API_KEYS")
    if raw:
        claves.extend([c.strip() for c in raw.split(",") if c.strip()])
    indice = 1
    while True:
        clave = os.getenv(f"GOOGLE_API_KEY_{indice}")
        if not clave:
            break
        claves.append(clave.strip())
        indice += 1
    legacy = os.getenv("GOOGLE_API_KEY")
    if legacy and legacy not in claves:
        claves.append(legacy.strip())
    if not claves:
        raise ValueError(
            "Faltan API keys de Google en .env. Usa GOOGLE_API_KEYS, "
            "GOOGLE_API_KEY_1, GOOGLE_API_KEY_2... o GOOGLE_API_KEY"
        )
    return claves


API_KEYS = _cargar_api_keys()
_actual = 0

MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "512"))
GENERATION_CONFIG = {
    "max_output_tokens": MAX_OUTPUT_TOKENS,
    "temperature": 0.7,
}


def _configurar_clave(posicion):
    global _actual
    _actual = posicion % len(API_KEYS)
    genai.configure(api_key=API_KEYS[_actual])


_configurar_clave(0)


def _es_limite_tasa(error):
    mensaje = str(error).lower()
    return (
        "429" in mensaje
        or "quota" in mensaje
        or "rate limit" in mensaje
        or "resource exhausted" in mensaje
    )


def _generar_con_rotacion(modelo, prompt, max_intentos=None, generacion_config=None):
    if max_intentos is None:
        max_intentos = len(API_KEYS) * 3
    if generacion_config is None:
        generacion_config = GENERATION_CONFIG
    ultimo_error = None
    for _ in range(max_intentos):
        try:
            return modelo.generate_content(prompt, generation_config=generacion_config)
        except Exception as error:
            ultimo_error = error
            if not _es_limite_tasa(error):
                raise
            _configurar_clave(_actual + 1)
            time.sleep(1)
    raise ultimo_error


MODELO_PREDETERMINADO = "models/gemini-2.5-flash"


def obtener_modelo(nombre_modelo=MODELO_PREDETERMINADO):
    return genai.GenerativeModel(nombre_modelo)


def listar_modelos_disponibles():
    try:
        modelos = genai.list_models()
        return [m.name for m in modelos if 'generateContent' in m.supported_generation_methods]
    except Exception as e:
        return [f"Error listando modelos: {e}"]


def preguntar(pregunta: str, contexto: str = "", nombre_modelo: str = MODELO_PREDETERMINADO, generacion_config=None) -> str:
    prompt = f"{contexto}\n\nPregunta: {pregunta}" if contexto else pregunta
    respuesta_cache = _cache.obtener(prompt)
    if respuesta_cache is not None:
        return respuesta_cache
    modelo = obtener_modelo(nombre_modelo)
    respuesta = _generar_con_rotacion(modelo, prompt, generacion_config=generacion_config)
    texto = respuesta.text
    _cache.guardar(prompt, texto)
    return texto


def auditar_proyecto(ruta_proyecto: str, archivo: str = None, nombre_modelo: str = MODELO_PREDETERMINADO, generacion_config=None) -> str:
    if archivo:
        ruta_completa = os.path.join(ruta_proyecto, archivo)
        if not os.path.exists(ruta_completa):
            return f"No se encontró el archivo: {ruta_completa}"
        with open(ruta_completa, "r", encoding="utf-8") as f:
            contenido = f.read()
        prompt = (
            "Eres un ingeniero de software senior. Analiza el siguiente código "
            "y dime qué hace, si tiene problemas y cómo mejorarlo:\n\n"
            f"{contenido}"
        )
    else:
        prompt = (
            "Eres un ingeniero de software senior. Dame un resumen ejecutivo "
            f"del proyecto en la carpeta: {ruta_proyecto}"
        )

    modelo = obtener_modelo(nombre_modelo)
    respuesta = _generar_con_rotacion(modelo, prompt, generacion_config=generacion_config)
    texto = respuesta.text
    _cache.guardar(prompt, texto)
    return texto


if __name__ == "__main__":
    stats = _cache.stats()
    print("=== Agente GProA Gemini ===")
    print(f"API keys configuradas: {len(API_KEYS)}")
    print(f"Caché: {'activado' if stats['habilitado'] else 'desactivado'} ({stats['entradas']}/{stats['max_entradas']} entradas)")
    print("Escribe tu pregunta o 'auditar <archivo>' para analizar un archivo.")
    print("Escribe 'salir' para terminar.\n")

    while True:
        entrada = input("Tú: ").strip()
        if entrada.lower() in ("salir", "exit", "quit"):
            break
        if entrada.lower().startswith("auditar "):
            nombre_archivo = entrada[len("auditar "):].strip()
            print("\nAnalizando...\n")
            print(auditar_proyecto(ruta_proyecto=".", archivo=nombre_archivo))
        else:
            print("\nPensando...\n")
            print(preguntar(entrada))
        print("-" * 40)
