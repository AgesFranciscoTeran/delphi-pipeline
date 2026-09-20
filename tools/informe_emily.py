#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera el documento para Emily: qué preguntas hay que arreglar y con qué evidencia.

    python3 tools/informe_emily.py Resultados_k1 ... Resultados_k5 --salida docs/para-emily.md

Dos señales, no una
-------------------
**Sin clasificar** — el panelista dijo algo que no cabe en ninguna opción. Falta una opción.

**Inestable** — el mismo texto recibe distinta etiqueta en distintas corridas. No es que falte
una opción: es que dos opciones no se distinguen lo suficiente como para que la elección sea
determinista. Emily puede arreglarlo redactándolas mejor o fusionándolas.

La segunda señal aparece sólo al correr k veces y comparar; antes era invisible porque una sola
corrida siempre parece segura de sí misma. Detecta un problema distinto y a veces en preguntas
que tienen 0 % sin clasificar, así que no se puede sustituir una por otra.

El documento sale con las respuestas textuales que no encajaron y con los pares de opciones
entre los que el modelo duda. Sin eso, decirle "P4_Q6 va mal" no le sirve de nada.
"""
import argparse
import collections
import os
import sys
import textwrap

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comentarios_emily

TEXTOS_ES = {}
try:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sitio"))
    from datos import TEXTOS as TEXTOS_ES          # enunciados en español, ya traducidos
except Exception:
    pass


def qid_de(panel, pregunta):
    q = str(pregunta)
    return "P%s_Q%s" % (panel, q[1:] if q.upper().startswith("Q") else q)


def etiqueta_de(fila):
    if fila.get("question_type") in ("nominal", "binary"):
        v = fila.get("selected_option")
        return v if isinstance(v, str) and v else None
    b = fila.get("band")
    if isinstance(b, str) and b:
        return b
    v = fila.get("numeric_value")
    return f"{float(v):g}" if v is not None and not pd.isna(v) else None


def cargar(carpetas):
    corridas = []
    for c in carpetas:
        d = pd.read_csv(os.path.join(c, "02_extracted.csv"))
        d["qid"] = [qid_de(p, q) for p, q in zip(d.Panel, d.Question)]
        corridas.append(d.set_index("response_id"))
    return corridas


def analizar(corridas):
    """Por pregunta: % sin clasificar, % inestable, respuestas huérfanas y pares en disputa."""
    base = corridas[0]
    filas = {}
    for rid in base.index:
        votos = []
        for d in corridas:
            if rid in d.index and d.loc[rid].get("extraction_status") == "ok":
                e = etiqueta_de(d.loc[rid])
                if e:
                    votos.append(e)
        if votos:
            filas[rid] = votos

    por_pregunta = collections.defaultdict(lambda: {
        "n": 0, "sin_clasificar": 0, "inestables": 0,
        "huerfanas": [], "disputas": collections.Counter()})

    for rid, votos in filas.items():
        f = base.loc[rid]
        if f.get("question_type") not in ("nominal", "binary"):
            continue                      # el informe para Emily es de opciones, no de cifras
        q = por_pregunta[f["qid"]]
        q["n"] += 1
        cuenta = collections.Counter(votos)
        modal = cuenta.most_common(1)[0][0]
        if modal == "Unclassified":
            q["sin_clasificar"] += 1
            q["huerfanas"].append(str(f.get("Response", "")))
        if len(cuenta) > 1:
            q["inestables"] += 1
            q["disputas"][" ⇄ ".join(sorted(cuenta))] += 1
    return por_pregunta


def recortar(t, n=150):
    return textwrap.shorten(" ".join(str(t).split()), n, placeholder="…")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("carpetas", nargs="+")
    ap.add_argument("--salida", default="docs/para-emily.md")
    ap.add_argument("--umbral", type=float, default=10.0,
                    help="%% mínimo (sin clasificar o inestable) para entrar en el informe")
    args = ap.parse_args()

    corridas = cargar(args.carpetas)
    k = len(corridas)
    datos = analizar(corridas)

    ranking = []
    for q, d in datos.items():
        if not d["n"]:
            continue
        pc_sin = d["sin_clasificar"] / d["n"] * 100
        pc_ines = d["inestables"] / d["n"] * 100
        if max(pc_sin, pc_ines) >= args.umbral:
            ranking.append((q, d, pc_sin, pc_ines))
    ranking.sort(key=lambda r: -max(r[2], r[3]))

    L = []
    L.append("# Preguntas que hace falta arreglar en la taxonomía\n")
    L.append(f"*Generado desde {k} corridas del pipeline — {pd.Timestamp.now():%d-%m-%Y}*\n")
    L.append("Hay **dos** problemas distintos y conviene no confundirlos.\n")
    L.append("**Sin clasificar**: el panelista dijo algo que no cabe en ninguna opción. "
             "Falta una opción.\n")
    L.append("**Inestable**: el mismo texto recibe distinta etiqueta según la corrida. No falta "
             "una opción — hay dos que no se distinguen lo suficiente. Se arregla redactándolas "
             "mejor o fusionándolas. Esto sólo se ve corriendo el análisis varias veces, y una "
             "pregunta puede estar al 0 % sin clasificar y aun así ser inestable.\n")
    L.append("| Pregunta | Sin clasificar | Inestable | Qué le pasa |")
    L.append("|---|---|---|---|")
    for q, d, pc_sin, pc_ines in ranking:
        # Los dos problemas pueden convivir: no es una u otra. El umbral de 10 % es el mismo
        # que decide entrar al informe, así que "las dos" significa que ambas señales por sí
        # solas bastarían para que la pregunta estuviera aquí.
        if pc_sin >= args.umbral and pc_ines >= args.umbral:
            dx = "faltan opciones **y** las que hay se confunden"
        elif pc_sin >= pc_ines:
            dx = "falta una opción"
        else:
            dx = "dos opciones no se distinguen"
        L.append(f"| **{q}** | {pc_sin:.0f} % | {pc_ines:.0f} % | {dx} |")
    L.append("")

    notas = comentarios_emily.por_pregunta()
    for q, d, pc_sin, pc_ines in ranking:
        L.append(f"\n## {q} — {TEXTOS_ES.get(q, q)}\n")
        L.append(f"De {d['n']} respuestas: **{d['sin_clasificar']} sin clasificar** "
                 f"({pc_sin:.0f} %), **{d['inestables']} inestables** ({pc_ines:.0f} %).\n")
        L += comentarios_emily.bloque(notas.get(q))
        if d["huerfanas"]:
            L.append("**Respuestas que no encajan en ninguna opción:**\n")
            for t in d["huerfanas"][:6]:
                L.append(f"> {recortar(t)}\n")
            if len(d["huerfanas"]) > 6:
                L.append(f"*(y {len(d['huerfanas']) - 6} más)*\n")
        if d["disputas"]:
            L.append("**Opciones entre las que el sistema duda** "
                     "(la misma respuesta recibe una u otra según la corrida):\n")
            hay_ninguna = False
            for par, n in d["disputas"].most_common(5):
                legible = par.replace("Unclassified", "*(ninguna)*")
                hay_ninguna = hay_ninguna or "Unclassified" in par
                L.append(f"- {legible} — {n} respuesta{'s' if n > 1 else ''}")
            L.append("")
            if hay_ninguna:
                # Que una opción compita con "ninguna" es un síntoma distinto de que compitan
                # dos opciones entre sí: no es que se confundan, es que la opción encaja sólo
                # a medias. Vale la pena separarlo porque la corrección es otra.
                L.append("Donde la duda es contra *(ninguna)*, el problema no es que dos "
                         "opciones se confundan: es que **la opción encaja sólo a medias**. "
                         "A veces la da por buena y a veces no. Suele querer decir que hace "
                         "falta ampliarla o partirla en dos.\n")

    L.append("\n---\n")
    L.append("## Cómo leerlo\n")
    L.append("Una pregunta con mucho **sin clasificar** necesita una opción nueva: mirá las "
             "respuestas citadas y decidí qué opción les daría cabida.\n")
    L.append("Una pregunta con mucho **inestable** necesita que dos opciones se separen mejor. "
             "En la lista de dudas, cada línea es un par de opciones que el sistema no logra "
             "distinguir de forma consistente — si a vos te cuesta decidir entre esas dos "
             "leyendo la respuesta, al sistema también.\n")

    os.makedirs(os.path.dirname(args.salida) or ".", exist_ok=True)
    with open(args.salida, "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    print(f"{len(ranking)} preguntas por encima del {args.umbral:.0f} %")
    for q, d, a, b in ranking:
        print(f"  {q:8} sin clasificar {a:5.0f} %   inestable {b:5.0f} %")
    print(f"\nEscrito en {args.salida}")
    print("  Lleva citas textuales de panelistas: está en .gitignore, no se publica.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
