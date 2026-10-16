#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prototipo EXPLORATORIO del grafo de argumentos: postura → razón, por pregunta.

    DELPHI_RESULTADOS=Resultados_v4r python3 tools/argumentos_exploratorio.py

Qué hace
--------
La taxonomía de argumentos (el porqué de cada postura) todavía no existe: la define Emily.
Mientras tanto, esto propone una a partir de los datos. Para cada pregunta de opción le pasa
al modelo el resumen del argumento de cada respuesta (`core_argument`, que la extracción ya
produce) y le pide de 3 a 6 temas de razones, más la asignación de cada respuesta a uno.
Después dibuja, para la ronda final, de qué postura (u opción) sale cada razón.

Qué NO es
---------
No es un resultado: los temas los propone el modelo en UNA corrida, sin validar. Sirve como
borrador para que Emily construya la taxonomía de argumentos, y para ver si el grafo vale la
pena. Por eso no va al sitio público. Salida: <resultados>/argumentos/ (JSON + figuras PNG).
"""
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "pipeline"))
sys.path.insert(0, os.path.join(RAIZ, "sitio"))

import pandas as pd                                    # noqa: E402
from config import *                                   # noqa: E402,F401
import extract_arguments as ea                         # noqa: E402

PROMPT = """Below are paraphrased arguments from Delphi panelists (medical students) answering:
"{pregunta}"

Each line is: <id> [<position taken>] <argument>.

Group the arguments into 3 to 6 themes according to the REASON given — not the position taken.
Two panelists with opposite positions can share a reason theme. Use "T0" for responses that
give no reason at all.

Respond ONLY with valid JSON:
{{
  "themes": [{{"id": "T1", "name": "<short name, max 6 words, in Spanish>",
               "description": "<one sentence, in Spanish>"}}],
  "assignments": {{"<id>": "<theme id>"}}
}}
Every id below must appear in "assignments" exactly once.

{lineas}
"""


def proponer(cliente, q, filas):
    lineas = "\n".join(f"R{i} [{f['base']}] {f['arg']}" for i, f in enumerate(filas))
    prompt = PROMPT.format(pregunta=filas[0]["texto"], lineas=lineas)
    for intento in range(3):
        try:
            crudo = ea.call_llm(cliente, prompt, {"type": "open"}, max_tokens=16000)
            js = ea.extract_json(crudo)
            asig = js["assignments"]
            return js["themes"], {filas[int(k[1:])]["rid"]: v for k, v in asig.items()
                                  if k.startswith("R") and k[1:].isdigit()
                                  and int(k[1:]) < len(filas)}
        except Exception as e:                                       # noqa: BLE001
            print(f"  {q}: intento {intento + 1} falló ({e})")
    return None, None


def main():
    from openai import OpenAI
    import figuras
    salida = os.path.join(OUTPUT_DIR, "argumentos")
    os.makedirs(salida, exist_ok=True)
    cache_p = os.path.join(salida, "temas.json")
    cache = json.load(open(cache_p, encoding="utf-8")) if os.path.exists(cache_p) else {}

    e = pd.read_csv(os.path.join(OUTPUT_DIR, "02_extracted.csv"))
    e = e[e.is_valid_response & e.question_type.isin(["nominal", "binary"])
          & e.selected_option.notna() & ~e.selected_option.isin(["Unclassified", OFF_TOPIC_LABEL])]
    e["qid"] = "P" + e.Panel.astype(str) + "_Q" + e.Question.astype(str)
    cliente = OpenAI(base_url=URL_LLM, api_key=API_KEY)

    for q, g in e.groupby("qid"):
        if q in cache:
            continue
        cat, _, _, _ = figuras.esquema(q, g.selected_option)
        filas = [{"rid": r.response_id, "texto": r["Question Text"], "base": cat(r.selected_option),
                  "arg": str(r.core_argument)} for _, r in g.iterrows()
                 if isinstance(r.core_argument, str) and r.core_argument.strip()]
        temas, asig = proponer(cliente, q, filas)
        if temas:
            cache[q] = {"temas": temas, "asignacion": asig, "modelo": MODEL_LLM}
            json.dump(cache, open(cache_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print(f"  {q}: {len(temas)} temas, {len(asig)} de {len(filas)} respuestas asignadas")

    for panel in sorted(e.Panel.unique()):
        ruta = fig_argumentos(int(panel), e, cache, salida, figuras)
        print("  figura:", ruta)


def fig_argumentos(panel, e, cache, salida, figuras):
    """Por pregunta: postura (u opción) en la ronda final → tema de la razón. Cinta = panelistas."""
    import collections
    import matplotlib.pyplot as plt
    g = e[e.Panel == panel]
    preguntas = sorted([q for q in g.qid.unique() if q in cache],
                       key=lambda q: int(q.split("_Q")[1]))
    fig, axes = plt.subplots(len(preguntas), 1, figsize=(7.6, 2.6 * len(preguntas)))
    axes = [axes] if len(preguntas) == 1 else list(axes)
    for ax, q in zip(axes, preguntas):
        gq = g[g.qid == q]
        fin = gq[gq.Round == gq.Round.max()]
        cat, pal, orden, marcas = figuras.esquema(q, gq.selected_option)
        nombres = {t["id"]: t["name"] for t in cache[q]["temas"]}
        nombres.setdefault("T0", "Sin razón explícita")
        pares = collections.Counter(
            (cat(r.selected_option), cache[q]["asignacion"].get(r.response_id, "T0"))
            for _, r in fin.iterrows())
        izq = [c for c in orden if any(a == c for a, _ in pares)]
        der = sorted({b for _, b in pares}, key=lambda t: (t == "T0", t))
        total = sum(pares.values())
        GAP = .05

        def apilar(claves, lado):
            pos, y = {}, 0.0
            for k in claves:
                n = sum(v for (a, b), v in pares.items() if (a if lado == 0 else b) == k)
                h = n / total * (1 - GAP * (len(claves) - 1))
                pos[k] = [y, y + h, n, 0.0]
                y += h + GAP
            return pos
        pi, pd_ = apilar(izq, 0), apilar(der, 1)
        for (a, b), n in sorted(pares.items(), key=lambda kv: (izq.index(kv[0][0]), der.index(kv[0][1]))):
            h0 = (pi[a][1] - pi[a][0]) * n / pi[a][2]
            h1 = (pd_[b][1] - pd_[b][0]) * n / pd_[b][2]
            y0, y1 = pi[a][0] + pi[a][3], pd_[b][0] + pd_[b][3]
            figuras._cinta(ax, .12, 1.88, y0, y0 + h0, y1, y1 + h1, pal.get(a, figuras.OTRAS), .5)
            pi[a][3] += h0
            pd_[b][3] += h1
        for k, (y0, y1, n, _) in pi.items():
            ax.add_patch(plt.Rectangle((0, y0), .12, y1 - y0, facecolor=pal.get(k, figuras.OTRAS),
                                       edgecolor="white", lw=1.2))
            ax.text(-.05, (y0 + y1) / 2, f"{marcas.get(k, '')} {figuras._corta(k, 26)} ({n})",
                    ha="right", va="center", fontsize=7.8, color=figuras.TINTA2)
        for k, (y0, y1, n, _) in pd_.items():
            ax.add_patch(plt.Rectangle((1.88, y0), .12, y1 - y0, facecolor=figuras.OTRAS,
                                       edgecolor="white", lw=1.2))
            ax.text(2.07, (y0 + y1) / 2, f"{figuras._envuelve(nombres.get(k, k), 34, 2)} ({n})",
                    ha="left", va="center", fontsize=7.8, color=figuras.TINTA2, linespacing=1.1)
        ax.set_title(f"{q} — {figuras._corta(figuras.datos.texto(q), 70)}   (ronda final, n = {total})",
                     fontsize=9, color=figuras.TINTA, loc="left")
        ax.set_xlim(-1.9, 4.1)
        ax.set_ylim(1.02, -.04)
        ax.axis("off")
    fig.suptitle("EXPLORATORIO — temas propuestos por el modelo, sin validar",
                 fontsize=9, color="#a32c2c", x=.01, ha="left")
    fig.tight_layout()
    ruta = os.path.join(salida, f"argumentos_panel{panel}.png")
    fig.savefig(ruta, dpi=150)
    plt.close(fig)
    return ruta


if __name__ == "__main__":
    main()
