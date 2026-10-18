#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Clasifica el argumento (el porqué) de cada respuesta en la taxonomía de Emily.

    DELPHI_RESULTADOS=Resultados_v4r python3 tools/argumentos.py [--k 3]

Entrada: <resultados>/02_extracted.csv (el `core_argument` que ya produce la extracción).
Salida:  <resultados>/04_argumentos.csv — una fila por respuesta de opción, con el argumento
         por voto mayoritario de k corridas y el acuerdo entre ellas.
         <resultados>/argumentos/corridas.json — la salida cruda de cada corrida (caché).

Cómo
----
Una llamada por pregunta y corrida: el modelo recibe la pregunta, la lista cerrada de los nueve
perfiles de Emily (con su descripción y ejemplo) y el argumento de cada respuesta, y asigna a
cada una el perfil cuyo razonamiento mejor la describe, o «Sin argumento». Se repite k veces y
se vota, igual que con las posturas: una corrida sola del servidor no es una medición. Una
respuesta sin mayoría queda «Sin argumento».

La clasificación es automática y todavía no está validada contra una persona: la taxonomía es
de Emily, las etiquetas son del sistema.
"""
import argparse
import collections
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "pipeline"))
sys.path.insert(0, os.path.join(RAIZ, "sitio"))

import pandas as pd                                    # noqa: E402
from config import *                                   # noqa: E402,F401
import extract_arguments as ea                         # noqa: E402
from argumentos import ARGUMENTOS, NINGUNO             # noqa: E402

PROMPT = """You are classifying the REASONING behind answers from a Delphi study on medical
education (panelists are medical students). Question:
"{pregunta}"

Reasoning profiles (defined by the domain expert, in Spanish):
{perfiles}

Each line below is: <id> [<position taken>] <paraphrase of the panelist's argument>.
Assign each id to the ONE profile whose reasoning best describes WHY the panelist holds that
position — not the position itself. Use "C0" if the argument gives no reason, or if no profile
fits.

Respond ONLY with valid JSON: {{"<id>": "<C0..C9>", ...}} with every id exactly once.

{lineas}
"""


def perfiles_txt():
    return "\n".join(f'C{i}. {n}: {d} Ejemplo: "{e}"'
                     for i, (n, (d, e)) in enumerate(ARGUMENTOS.items(), 1))


def clasificar(cliente, filas):
    nombres = [None] + list(ARGUMENTOS)
    lineas = "\n".join(f"R{i} [{f['base']}] {f['arg']}" for i, f in enumerate(filas))
    prompt = PROMPT.format(pregunta=filas[0]["texto"], perfiles=perfiles_txt(), lineas=lineas)
    # Las preguntas con más respuestas (24-29) agotaban 16 000 tokens razonando y no llegaban a
    # responder: cinco quedaron sin ninguna corrida. Más presupuesto y un intento más.
    for intento in range(4):
        try:
            js = ea.extract_json(ea.call_llm(cliente, prompt, {"type": "open"}, max_tokens=32000))
            out = {}
            for k, v in js.items():
                if not (k.startswith("R") and k[1:].isdigit() and int(k[1:]) < len(filas)):
                    continue
                c = str(v).strip().upper().lstrip("C")
                out[filas[int(k[1:])]["rid"]] = (nombres[int(c)] if c.isdigit()
                                                 and 0 < int(c) < len(nombres) else NINGUNO)
            return out
        except Exception as e:                                       # noqa: BLE001
            print(f"    intento {intento + 1} falló ({e})")
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=None,
                    help="segundos por llamada; con el servidor cargado, 120 no alcanza")
    args = ap.parse_args()
    if args.timeout:
        ea.REQUEST_TIMEOUT = args.timeout      # sólo para esta herramienta
    from openai import OpenAI
    import figuras
    carpeta = os.path.join(OUTPUT_DIR, "argumentos")
    os.makedirs(carpeta, exist_ok=True)
    cache_p = os.path.join(carpeta, "corridas.json")
    cache = json.load(open(cache_p, encoding="utf-8")) if os.path.exists(cache_p) else {}

    e = pd.read_csv(os.path.join(OUTPUT_DIR, "02_extracted.csv"))
    e = e[e.is_valid_response & e.question_type.isin(["nominal", "binary"])
          & e.selected_option.notna() & ~e.selected_option.isin(["Unclassified", OFF_TOPIC_LABEL])]
    e["qid"] = "P" + e.Panel.astype(str) + "_Q" + e.Question.astype(str)
    cliente = OpenAI(base_url=URL_LLM, api_key=API_KEY)

    for q, g in e.groupby("qid"):
        cat, _, _, _ = figuras.esquema(q, g.selected_option)
        filas = [{"rid": r.response_id, "texto": r["Question Text"],
                  "base": cat(r.selected_option), "arg": str(r.core_argument)}
                 for _, r in g.iterrows() if isinstance(r.core_argument, str) and r.core_argument.strip()]
        corridas = cache.setdefault(q, [])
        while len(corridas) < args.k:
            print(f"  {q}: corrida {len(corridas) + 1} de {args.k}")
            res = clasificar(cliente, filas)
            if res is None:
                break
            corridas.append(res)
            json.dump(cache, open(cache_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    filas_out = []
    for _, r in e.iterrows():
        votos = [c[r.response_id] for c in cache.get(r.qid, []) if r.response_id in c]
        top = collections.Counter(votos).most_common(2)
        if not top:
            arg, n = None, 0           # ninguna corrida la clasificó: «no clasificado», que no
        elif len(top) > 1 and top[0][1] == top[1][1]:   # es lo mismo que «sin argumento»
            arg, n = NINGUNO, top[0][1]
        else:
            arg, n = top[0]
        filas_out.append({"response_id": r.response_id, "question_id": r.qid, "Panel": r.Panel,
                          "Question": r.Question, "Round": r.Round, "Panelist": r.Panelist,
                          "selected_option": r.selected_option, "argumento": arg,
                          "n_corridas": len(votos), "n_acuerdo": n})
    out = pd.DataFrame(filas_out)
    out.to_csv(os.path.join(OUTPUT_DIR, "04_argumentos.csv"), index=False)
    con = out[out.n_corridas > 0]
    unan = (con.n_acuerdo == con.n_corridas).mean() * 100 if len(con) else float("nan")
    completas = int((out.n_corridas == args.k).sum())
    print(f"\n04_argumentos.csv: {len(out)} respuestas; {completas} con las {args.k} corridas, "
          f"{int((out.n_corridas == 0).sum())} sin ninguna; unánimes (entre las clasificadas): {unan:.1f} %")
    print(out.argumento.fillna("(no clasificado)").value_counts().to_string())


if __name__ == "__main__":
    main()
