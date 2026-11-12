"""Experimento de señales: S3 (cita verificada) y S5 (rasgos atómicos), una corrida (k = 1).

Dos llamadas por respuesta, separadas a propósito:
  * S3 ve la etiqueta asignada y devuelve el fragmento literal que la sostiene (o "" si nada la
    sostiene). Que la cita exista se comprueba después, por código (tools/senales.py).
  * S5 NO ve la etiqueta: responde preguntas simples sobre el texto (postura, número,
    «depende», tema). Así la regla que compara rasgos y etiqueta no hereda el anclaje.

Uso (spark-adi, con ~/.delphi_env cargado):
  python -u tools/senales_llm.py Resultados_v4f_k4
Salida: <res>/senales_llm.jsonl (una línea por respuesta; se reanuda si se corta).
"""
import json
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
import extract_arguments as ea  # noqa: E402
from config import API_KEY, MAX_WORKERS, URL_LLM  # noqa: E402
from taxonomy import get_taxonomy  # noqa: E402

MAX_TOK = 8000
OPEN = {"type": "open"}


def etiqueta_mostrada(r, tax):
    if tax["type"] in ("quantitative", "hybrid"):
        if pd.isna(r.band):
            return "no number / no band was assigned"
        v = "" if pd.isna(r.numeric_value) else f" (value {r.numeric_value:g} {r.value_unit})"
        return f"{r.band}{v}"
    s = r.selected_option
    return "no option fits (unclassified)" if pd.isna(s) or s == "Unclassified" else str(s)


def prompt_s3(r, tax):
    return f"""A classifier assigned a label to this Delphi response. Do NOT judge or change the
label. Copy, character by character, the shortest fragment of the response that supports the
assigned label. If nothing in the response supports it, return an empty string.

Question: {r["Question Text"]}
Response:
\"\"\"{r.Response}\"\"\"
Assigned label: {etiqueta_mostrada(r, tax)}

Respond ONLY with valid JSON (no preamble, no markdown):
{{"evidence": "<verbatim fragment from the response, or empty string>"}}
"""


def prompt_s5(r):
    return f"""Read this answer to a Delphi question and describe it. Base every field strictly
on what the text says.

Question: {r["Question Text"]}
Response:
\"\"\"{r.Response}\"\"\"

Respond ONLY with valid JSON (no preamble, no markdown):
{{
  "stance": "<yes | no | conditional | none>  (does the response answer the question affirmatively, negatively, only under a condition, or take no position?)",
  "gives_number": <true | false>  (does the response state a number, in digits or words, as its answer?),
  "says_depends": <true | false>  (does it say the answer depends on something?),
  "on_topic": <true | false>  (does it address the question asked?)
}}
"""


def pedir(cliente, prompt):
    ultimo = None
    for _ in range(3):
        try:
            return ea.extract_json(ea.call_llm(cliente, prompt, OPEN, max_tokens=MAX_TOK))
        except Exception as e:  # noqa: BLE001
            ultimo = f"{type(e).__name__}: {str(e)[:150]}"
    return {"error": ultimo}


def main():
    res = sys.argv[1]
    from openai import OpenAI
    cliente = OpenAI(base_url=URL_LLM, api_key=API_KEY)
    df = pd.read_csv(os.path.join(res, "02_extracted.csv"))
    df = df[df.is_valid_response.astype(bool) & df.extraction_status.eq("ok")]
    salida = os.path.join(res, "senales_llm.jsonl")
    hechos = set()
    if os.path.exists(salida):
        for linea in open(salida, encoding="utf-8"):
            d = json.loads(linea)
            if "error" not in d.get("s3", {}) and "error" not in d.get("s5", {}):
                hechos.add(d["response_id"])
    filas = [r for _, r in df.iterrows() if r.response_id not in hechos]
    print(f"respuestas: {len(df)} | hechas: {len(hechos)} | por hacer: {len(filas)}", flush=True)
    lock = threading.Lock()

    def trabajo(r):
        tax = get_taxonomy(int(r.Panel), int(r.Question))
        return {"response_id": r.response_id, "etiqueta": etiqueta_mostrada(r, tax),
                "s3": pedir(cliente, prompt_s3(r, tax)), "s5": pedir(cliente, prompt_s5(r))}

    n = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool, open(salida, "a", encoding="utf-8") as f:
        for fut in as_completed([pool.submit(trabajo, r) for r in filas]):
            d = fut.result()
            with lock:
                f.write(json.dumps(d, ensure_ascii=False) + "\n")
                f.flush()
                n += 1
                if n % 25 == 0 or n == len(filas):
                    print(f"  {n}/{len(filas)}", flush=True)
    print("FIN senales_llm", flush=True)


if __name__ == "__main__":
    main()
