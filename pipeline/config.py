"""
Delphi Pipeline v2 — configuración.

Fase 0: sólo lo que se usa. Las constantes muertas de la v1 (ARGUMENT_TYPES,
STANCE_OPTIONS, CERTAINTY_OPTIONS, SIMILARITY_EDGE_THRESHOLD, MIN_CLUSTER_SIZE)
se eliminaron; si algo de eso vuelve, vuelve junto con el código que lo use.
"""

# ── Rutas ─────────────────────────────────────────────────────────────────────
# Ancladas a la raíz del repositorio, no al directorio desde el que se llama al script.
# Antes eran relativas ("dataset_prueba.xlsx"), así que todo tenía que vivir en la raíz y
# cualquier `cd` rompía la corrida en silencio, creando un `Resultados/` nuevo donde tocara.
import os as _os

RAIZ = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))

DATA_PATH = _os.environ.get("DELPHI_DATOS", _os.path.join(RAIZ, "datos", "dataset_prueba.xlsx"))
OUTPUT_DIR = _os.environ.get("DELPHI_RESULTADOS", _os.path.join(RAIZ, "Resultados"))
FIGURES_DIR = _os.path.join(OUTPUT_DIR, "figures")

API_KEY = "local"

# ── Endpoints (verificar antes de cada corrida; la universidad cambia modelos sin aviso) ──
# Se pueden sobrescribir por entorno para no tener que editar (ni versionar) este archivo
# cuando la universidad cambia el modelo servido:
#     DELPHI_MODELO="zai-org/GLM-5.3-Flash" ./run.sh
# El modelo entra en la clave del caché, así que cambiarlo NO mezcla corridas: invalida todo
# y vuelve a extraer con un solo modelo. Anotar cuál se usó: sale en run_manifest.json.
# 14-09-2026: la universidad dejó de servir google/gemma-4-12B-it en este puerto y no lo va a
# reponer. GLM pasa a ser el modelo de trabajo. Todo lo anterior a esta fecha —incluida la
# validación contra las etiquetas de Emily, κ = 0,72— se midió con Gemma y no es comparable.
URL_LLM = _os.environ.get("DELPHI_LLM_URL", "http://172.28.230.10:12559/v1")
MODEL_LLM = _os.environ.get("DELPHI_MODELO", "zai-org/GLM-5.3-Flash")

URL_EMBEDDINGS = "http://172.28.230.10:12556/v1"
MODEL_EMBEDDINGS = "BAAI/bge-m3"

# ── Determinismo y rendimiento de la extracción ──
TEMPERATURE = 0.0          # reproducibilidad: la misma respuesta -> la misma etiqueta
SEED = 42                  # vLLM acepta `seed`; si el servidor lo ignora no pasa nada
# 2500 y no 512: los modelos de razonamiento gastan presupuesto "pensando" antes de emitir el
# JSON, y con 512 lo truncan a media respuesta. El síntoma no es un error claro sino una tasa
# alta de extracciones "failed" repartidas al azar. Gemma respondía directo y con 512 le bastaba;
# GLM no. Subirlo no cuesta nada en las respuestas cortas: se paga por token generado, no por
# el tope.
MAX_TOKENS = int(_os.environ.get("DELPHI_MAX_TOKENS", "2500"))

# Techo al que puede escalar el reintento cuando el fallo es "agotó max_tokens razonando".
# Escalar sólo ante ese fallo evita encarecer las 775 llamadas por culpa de cinco.
MAX_TOKENS_TECHO = int(_os.environ.get("DELPHI_MAX_TOKENS_TECHO", "16000"))

# Desactivar la cadena de pensamiento del modelo. Funciona —devuelve JSON válido—, pero no
# sirve para lo que se quería. Medido contra GLM-5.3-Flash el 14-09-2026 sobre el mismo ítem,
# tamaño de la salida:
#     sin extras 44 chars | guided_json 44 | enable_thinking=false 713 | las dos juntas 1259
# No elimina la explicación: la mueve del canal de razonamiento al de contenido, donde compite
# con el JSON por el mismo presupuesto. Empeora el truncado en vez de evitarlo.
# Queda como interruptor por si otro modelo se comporta distinto.
SIN_RAZONAMIENTO = _os.environ.get("DELPHI_SIN_RAZONAMIENTO", "0") == "1"
MAX_WORKERS = 8            # peticiones concurrentes al LLM (vLLM batchea; 8-16 es razonable)
REQUEST_TIMEOUT = 120      # segundos por petición
RETRIES = 3

# Tasa de fallos por encima de la cual la extracción se considera rota y NO se sobrescribe
# 02_extracted.csv. Una corrida con 28 % de fallos produce tablas que parecen resultados pero
# están hechas sobre la mitad del panel. Para saltárselo a propósito: DELPHI_IGNORA_FALLOS=1.
MAX_FALLOS_PCT = 5.0

# Decodificación guiada (vLLM). Suena a que resuelve el problema —el servidor restringe la
# salida al esquema— pero MEDIDO contra GLM-5.3-Flash el 14-09-2026 no ayudó: corrida completa
# con guiado 767/775 en 795 s, contra 770/775 sin él. El truncado ocurre ANTES de que el
# esquema aplique, así que restringir la salida no evita quedarse sin presupuesto.
# Se deja apagado y disponible: DELPHI_GUIADO=1.
USE_GUIDED_JSON = _os.environ.get("DELPHI_GUIADO", "0") == "1"

# ── Caché ──
CACHE_RESULTS = True
PROMPT_VERSION = "v2.0"    # súbelo cuando cambies un prompt: invalida el caché de forma explícita

# ── Columnas del Excel de entrada ──
COL_CATEGORY = "Category"
COL_PANEL = "Panel"
COL_ROUND = "Round"
COL_QUESTION = "Question"
COL_QUESTION_TEXT = "Question Text"
COL_RESPONSE_TYPE = "Response type"
COL_PANELIST = "Panelist"
COL_RESPONSE = "Response"

RESPONSE_TYPE_INDIVIDUAL = "Individual"
RESPONSE_TYPE_SYNTHESIS = "Synthesis"

# Marcadores de "sin respuesta" que se consideran vacíos (además de NaN y "")
EMPTY_MARKERS = {"nan", "n.a.", "na", "n/a", "-", "--", "."}
SHORT_RESPONSE_CHARS = 15  # sólo informativo (columna is_short); NO excluye

# ── Consenso (criterios provisionales de Fase 0; la Fase 2 los fija con literatura Delphi) ──
MIN_N_CLASSIFIED = 5          # por debajo de esto no se etiqueta consenso
MAX_UNCLASSIFIED_PCT = 40.0   # cobertura mínima: si más del 40 % quedó sin clasificar, "Insuficiente"
STRONG_AGREEMENT = 0.75       # modal share >= 75 % -> consenso fuerte
CLEAR_MAJORITY = 0.60         # >= 60 % -> mayoría clara
DOMINANT_OPTION = 0.40        # >= 40 % -> opción dominante
ENTROPY_DELTA = 0.05          # cambio mínimo de entropía normalizada para hablar de convergencia/dispersión
MIN_N_NUMERIC = 5             # mínimo de valores numéricos comparables para etiquetar
QUANT_STRONG = {"cv": 0.25, "rel_range": 0.30, "rel_iqr": 0.25}
QUANT_MODERATE = {"cv": 0.50, "rel_range": 0.75, "rel_iqr": 0.50}

# ── Unidades ──
# Vocabulario cerrado que el LLM debe usar (tal como lo dice el panelista, SIN convertir).
UNIT_VOCAB = [
    "hours/day", "hours/week", "hours/module", "hours/semester", "hours/session",
    "days/week", "semesters", "years", "students", "percent", "count", "other", "none",
]
# Conversiones explícitas hacia la unidad canónica de la pregunta. Sólo estas; lo demás
# se reporta como "unidad distinta" y no entra en el consenso numérico.
UNIT_CONVERSIONS = {
    ("hours/day", "hours/week"): 5.0,        # semana lectiva de 5 días (Emily: "20h para 5 días")
    ("hours/week", "hours/day"): 1 / 5.0,
    ("hours/module", "hours/week"): 1 / 4.0, # Emily: "cada módulo dura aprox 1 mes" (≈ 4 semanas)
    ("hours/module", "hours/day"): 1 / 20.0,
    ("years", "semesters"): 2.0,             # un año académico = 2 semestres (definición, no criterio)
    ("semesters", "years"): 0.5,
}
