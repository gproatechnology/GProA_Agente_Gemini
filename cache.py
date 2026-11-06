import json
import os
import re
import unicodedata
from difflib import SequenceMatcher


_DIR_BASE = os.path.dirname(os.path.abspath(__file__))


def _leer_bool_env(nombre, defecto):
    valor = os.getenv(nombre, str(defecto)).strip().lower()
    return valor in ("1", "true", "si", "sí", "yes", "on")


def _leer_int_env(nombre, defecto):
    try:
        return int(os.getenv(nombre, str(defecto)).strip())
    except (TypeError, ValueError):
        return defecto


def _leer_float_env(nombre, defecto):
    try:
        return float(os.getenv(nombre, str(defecto)).strip())
    except (TypeError, ValueError):
        return defecto


_CARCHE_FILE_DEFECTO = os.path.join(_DIR_BASE, "respuestas_cache.json")
_CARCHE_SEED_DEFECTO = os.path.join(_DIR_BASE, "respuestas_precargadas.json")

CACHE_ENABLED = _leer_bool_env("CACHE_ENABLED", True)
CACHE_FILE = os.getenv("CACHE_FILE", _CARCHE_FILE_DEFECTO)
CACHE_SEED_FILE = os.getenv("CACHE_SEED_FILE", _CARCHE_SEED_DEFECTO)
MAX_CACHE_ENTRIES = _leer_int_env("MAX_CACHE_ENTRIES", 200)
CACHE_SIMILARITY_THRESHOLD = _leer_float_env("CACHE_SIMILARITY_THRESHOLD", 0.85)


def normalizar(texto: str) -> str:
    """Normaliza una pregunta para usarla como clave de caché."""
    if not texto:
        return ""
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"[^\w\s]", "", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def _similaridad(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


class CacheRespuestas:
    """Caché de respuestas con base de conocimientos pre-cargada protegida."""

    def __init__(
        self,
        ruta_archivo=CACHE_FILE,
        ruta_seed=CACHE_SEED_FILE,
        habilitado=CACHE_ENABLED,
        max_entradas=MAX_CACHE_ENTRIES,
        umbral=CACHE_SIMILARITY_THRESHOLD,
    ):
        self.ruta_archivo = ruta_archivo
        self.ruta_seed = ruta_seed
        self.habilitado = habilitado
        self.max_entradas = max_entradas
        self.umbral = umbral
        # Entradas dinámicas (aprendidas en tiempo real, sujetas a FIFO)
        self.entradas = {}
        self._orden_insercion = []
        # Entradas pre-cargadas (protegidas, nunca se eliminan por FIFO)
        self.entradas_seed = {}
        self._cargar_seed()
        self._cargar()

    def _cargar_seed(self):
        """Carga las respuestas pre-cargadas protegidas desde el archivo JSON."""
        if not self.habilitado:
            return
        if not os.path.exists(self.ruta_seed):
            self.entradas_seed = {}
            return
        try:
            with open(self.ruta_seed, "r", encoding="utf-8") as f:
                datos = json.load(f)
            raw = datos.get("entradas", {}) if isinstance(datos, dict) else {}
            self.entradas_seed = {k: v for k, v in raw.items()}
        except (json.JSONDecodeError, OSError):
            self.entradas_seed = {}

    def _cargar(self):
        """Carga el caché dinámico aprendido desde disco."""
        if not self.habilitado:
            return
        if not os.path.exists(self.ruta_archivo):
            self.entradas = {}
            self._orden_insercion = []
            return
        try:
            with open(self.ruta_archivo, "r", encoding="utf-8") as f:
                datos = json.load(f)
            raw = datos.get("entradas", {}) if isinstance(datos, dict) else {}
            self.entradas = {}
            self._orden_insercion = []
            for clave, valor in raw.items():
                self.entradas[clave] = valor
                self._orden_insercion.append(clave)
        except (json.JSONDecodeError, OSError):
            self.entradas = {}
            self._orden_insercion = []

    def _guardar(self):
        if not self.habilitado:
            return
        try:
            datos = {
                "version": 1,
                "entradas": self.entradas,
            }
            with open(self.ruta_archivo, "w", encoding="utf-8") as f:
                json.dump(datos, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def _eviccion_fifo(self):
        """Elimina entradas dinámicas más antiguas al superar el límite.
        Las entradas pre-cargadas (seed) nunca se eliminan."""
        while len(self._orden_insercion) > self.max_entradas:
            clave_antigua = self._orden_insercion.pop(0)
            self.entradas.pop(clave_antigua, None)

    def obtener(self, pregunta: str):
        """Devuelve la respuesta cacheada si hay coincidencia, o None.
        Busca primero en las respuestas pre-cargadas (0 tokens), luego en dinámico."""
        if not self.habilitado:
            return None
        clave = normalizar(pregunta)
        if not clave:
            return None

        # 1. Respuestas pre-cargadas (protegidas, exactas o por similitud)
        if clave in self.entradas_seed:
            return self.entradas_seed[clave]
        mejor_seed = None
        mejor_puntaje_seed = 0.0
        for k in self.entradas_seed:
            puntaje = _similaridad(clave, k)
            if puntaje > mejor_puntaje_seed:
                mejor_puntaje_seed = puntaje
                mejor_seed = k
        if mejor_seed is not None and mejor_puntaje_seed >= self.umbral:
            return self.entradas_seed[mejor_seed]

        # 2. Caché dinámico aprendido
        if clave in self.entradas:
            return self.entradas[clave]
        mejor_din = None
        mejor_puntaje_din = 0.0
        for k in self.entradas:
            puntaje = _similaridad(clave, k)
            if puntaje > mejor_puntaje_din:
                mejor_puntaje_din = puntaje
                mejor_din = k
        if mejor_din is not None and mejor_puntaje_din >= self.umbral:
            return self.entradas[mejor_din]

        return None

    def guardar(self, pregunta: str, respuesta: str):
        """Guarda una pregunta y su respuesta en el caché dinámico (no en seed)."""
        if not self.habilitado:
            return
        clave = normalizar(pregunta)
        if not clave:
            return
        if clave not in self.entradas:
            self.entradas[clave] = respuesta
            self._orden_insercion.append(clave)
            self._eviccion_fifo()
        self._guardar()

    def stats(self):
        return {
            "habilitado": self.habilitado,
            "entradas_dinamicas": len(self.entradas),
            "entradas_seed": len(self.entradas_seed),
            "max_entradas_dinamicas": self.max_entradas,
            "archivo_dinamico": self.ruta_archivo,
            "archivo_seed": self.ruta_seed,
        }


_cache_global = None


def obtener_cache():
    global _cache_global
    if _cache_global is None:
        _cache_global = CacheRespuestas()
    return _cache_global
