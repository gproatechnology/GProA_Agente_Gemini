# Agente GProA con Google Gemini
# Lee la API KEY desde .env y responde preguntas sobre proyectos.

import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("Falta GOOGLE_API_KEY en el archivo .env")

genai.configure(api_key=API_KEY)

modelo = genai.GenerativeModel("gemini-1.5-flash")


def preguntar(pregunta: str, contexto: str = "") -> str:
    """Envía una pregunta a Gemini con contexto opcional."""
    prompt = f"{contexto}\n\nPregunta: {pregunta}" if contexto else pregunta
    respuesta = modelo.generate_content(prompt)
    return respuesta.text


def auditar_proyecto(ruta_proyecto: str, archivo: str = None) -> str:
    """Lee un archivo de un proyecto y pide a Gemini que lo analice."""
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

    respuesta = modelo.generate_content(prompt)
    return respuesta.text


if __name__ == "__main__":
    print("=== Agente GProA Gemini ===")
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
