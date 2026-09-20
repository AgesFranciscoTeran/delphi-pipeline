#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Qué respuesta concreta dudó el sistema, y entre qué opciones.

    python3 tools/inestables_detalle.py Resultados_k1 ... --salida docs/inestables-para-emily.md

Por qué existe
--------------
El informe resumido decía "P3_Q4 tiene 4 respuestas inestables" y Emily contestó, con razón,
que así no puede hacer nada: no sabe cuál es la respuesta ni entre qué opciones dudó el sistema.

Y además señaló un error nuestro. En P3_Q4 una respuesta puede pertenecer a «Yes» Y a «Yes,
only with trained tutors» a la vez — la segunda es un detalle de la primera, no una alternativa.
Que el sistema elija una u otra entre corridas NO es que esté confundido: es que le obligamos a
elegir una sola cuando la estructura es un árbol. El desacuerdo es nuestro, no suyo.

Por eso la inestabilidad se parte en cuatro clases, que piden cosas distintas:

  MISMA POSTURA     «Yes» ⇄ «Yes, only with trained tutors»
                    No es un problema de taxonomía. La lectura de fondo no cambia, sólo el
                    nivel de detalle. Lo arreglamos nosotros (ver el aviso al final).

  DISTINTA POSTURA  «Yes» ⇄ «No»
                    Sí es grave: el sentido de la respuesta cambia según la corrida.

  CONTRA NINGUNA    «Yes, only in basic sciences» ⇄ (ninguna)
                    La opción encaja a medias: a veces la da por buena y a veces no.

  ENTRE HERMANAS    «Balanced» ⇄ «Based on student need»
                    Dos opciones del mismo nivel que no se distinguen. Redactar o fusionar.

La postura sale de pipeline/stance_map.py, que es el árbol del documento de Emily ya codificado.
Donde una pregunta no tiene postura (elección entre alternativas, no sí/no), toda duda entre
opciones cuenta como ENTRE HERMANAS.
"""
import argparse
import collections
import os
import sys
import textwrap

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comentarios_emily

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "pipeline"))
sys.path.insert(0, os.path.join(RAIZ, "sitio"))

try:
    from stance_map import stance_of
except ImportError:
    def stance_of(qid, opcion):
        return None, None
try:
    from datos import TEXTOS as TEXTOS_ES
except Exception:
    TEXTOS_ES = {}

NINGUNA = "Unclassified"
CLASES = ("distinta postura", "contra ninguna", "entre hermanas", "misma postura")


def qid_de(panel, pregunta):
    q = str(pregunta)
    return "P%s_Q%s" % (panel, q[1:] if q.upper().startswith("Q") else q)


def clasificar_duda(qid, opciones):
    """A qué clase pertenece una duda entre este conjunto de opciones."""
    if NINGUNA in opciones:
        return "contra ninguna"
    posturas = {stance_of(qid, o)[0] for o in opciones}
    posturas.discard(None)
    if not posturas:
        return "entre hermanas"          # pregunta sin árbol de postura
    if len(posturas) > 1:
        return "distinta postura"
    return "misma postura"               # mismo sí/no, distinto grado de detalle


def recortar(t, n=260):
    return textwrap.shorten(" ".join(str(t).split()), n, placeholder="…")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("carpetas", nargs="+")
    ap.add_argument("--salida", default="docs/inestables-para-emily.md")
    args = ap.parse_args()

    corridas = []
    for c in args.carpetas:
        d = pd.read_csv(os.path.join(c, "02_extracted.csv"))
        d["qid"] = [qid_de(p, q) for p, q in zip(d.Panel, d.Question)]
        corridas.append(d.set_index("response_id"))
    k = len(corridas)
    base = corridas[0]

    casos = []
    for rid in base.index:
        f = base.loc[rid]
        if f.get("question_type") not in ("nominal", "binary"):
            continue
        votos = []
        for d in corridas:
            if rid in d.index and d.loc[rid].get("extraction_status") == "ok":
                v = d.loc[rid].get("selected_option")
                if isinstance(v, str) and v:
                    votos.append(v)
        cuenta = collections.Counter(votos)
        if len(cuenta) < 2:
            continue
        casos.append({"rid": rid, "qid": f["qid"], "texto": f.get("Response", ""),
                      "cuenta": cuenta, "clase": clasificar_duda(f["qid"], set(cuenta))})

    notas = comentarios_emily.por_pregunta()
    por_clase = collections.Counter(c["clase"] for c in casos)
    por_pregunta = collections.defaultdict(list)
    for c in casos:
        por_pregunta[c["qid"]].append(c)

    L = []
    L.append("# Las respuestas donde el sistema dudó\n")
    L.append(f"*{len(casos)} respuestas, de {k} corridas del pipeline — "
             f"{pd.Timestamp.now():%d-%m-%Y}*\n")
    L.append("Emily: tenías razón. Lo que el informe anterior llamaba «inestable» mezclaba "
             "cuatro cosas distintas, y una de ellas **no es un problema de la taxonomía sino "
             "nuestro**. Aquí va separado, y con la respuesta concreta en cada caso.\n")
    L.append("| Clase | Cuántas | Qué significa | Quién lo arregla |")
    L.append("|---|---|---|---|")
    L.append(f"| Misma postura | {por_clase['misma postura']} | «Sí» ⇄ «Sí, sólo con tutores "
             "entrenados» — el mismo sí, distinto detalle | **nosotros** |")
    L.append(f"| Distinta postura | {por_clase['distinta postura']} | «Sí» ⇄ «No» — cambia el "
             "sentido de la respuesta | mirar una por una |")
    L.append(f"| Contra ninguna | {por_clase['contra ninguna']} | la opción encaja a medias | "
             "Emily: ampliar o partir |")
    L.append(f"| Entre hermanas | {por_clase['entre hermanas']} | dos opciones del mismo nivel "
             "que no se distinguen | Emily: redactar o fusionar |")
    L.append("")
    L.append("**Lo de «misma postura» no lo tenés que tocar.** Es exactamente lo que dijiste de "
             "P3_Q4: una respuesta pertenece a «Sí» y a «Sí, sólo con tutores entrenados» a la "
             "vez. El sistema no está confundido — le obligamos a elegir UNA opción de una lista "
             "plana cuando tu documento es un árbol. No hace falta que añadas nada.\n")

    for clase in CLASES:
        de_clase = {q: [c for c in cs if c["clase"] == clase] for q, cs in por_pregunta.items()}
        de_clase = {q: cs for q, cs in de_clase.items() if cs}
        if not de_clase:
            continue
        L.append(f"\n---\n\n# {clase.upper()}\n")
        if clase == "misma postura":
            L.append("*No requiere acción tuya. Va listado para que veas que es lo que "
                     "describiste.*\n")
        for q in sorted(de_clase, key=lambda x: (x[1], int(x.split("Q")[1]))):
            L.append(f"\n## {q} — {TEXTOS_ES.get(q, q)}\n")
            L += comentarios_emily.bloque(notas.get(q))
            for c in sorted(de_clase[q], key=lambda x: -sum(x["cuenta"].values())):
                reparto = ", ".join(f"**{o if o != NINGUNA else '(ninguna)'}** ×{n}"
                                    for o, n in c["cuenta"].most_common())
                L.append(f"> {recortar(c['texto'])}\n")
                L.append(f"→ {reparto}\n")

    L.append("\n---\n\n## Lo que falta de la v3\n")
    L.append("Cuatro ejes de horas siguen diciendo sólo «Numerical» sin decir el periodo: "
             "**P3_Q1, P2_Q3, P4_Q1 y P4_Q2**. En los otros lo escribiste en el nombre del eje "
             "(«Numerical per week») y eso basta. Mientras falten, cuando un panelista dice "
             "«8 horas» sin más, el sistema no sabe si son 8 al día o a la semana, y el mismo "
             "texto puede valer 8 o 40.\n")

    os.makedirs(os.path.dirname(args.salida) or ".", exist_ok=True)
    with open(args.salida, "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    print(f"{len(casos)} respuestas con duda, de {k} corridas")
    for clase in CLASES:
        print(f"  {clase:18} {por_clase[clase]:3}")
    print(f"\nEscrito en {args.salida}")
    print("  Lleva respuestas textuales: está en .gitignore, no se publica.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
