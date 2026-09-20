#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Convierte el .docx de Emily en el JSON que consume tools/build_taxonomy.py.

    python3 tools/leer_docx_emily.py "Posturas varias opciones.docx" \\
            --salida docs/emily_posturas_varias_opciones.json

Por qué existe
--------------
Este paso se venía haciendo a mano cada vez que Emily mandaba una versión, y es el primer
eslabón de la cadena: docx → JSON → taxonomy.py → corrida. Si el primer eslabón no es
reproducible, no lo es ninguno. Con esto, una versión nueva del documento son dos comandos.

Estructura del documento
------------------------
  «Panel N»            un párrafo suelto fija el panel
  el enunciado          un párrafo antes de cada tabla
  la tabla              una celda por eje; el primer párrafo de la celda es el tipo
                        («Nominal», «Numerical per week»…) y el resto son las opciones

Una celda cuyo primer párrafo NO es un tipo conocido se marca «(sin etiqueta)»: así vienen las
continuaciones de rama («- No» y sus calificadores), que el generador sabe interpretar.

También extrae los comentarios de Word: Emily los usa para decir cosas que no caben en una
celda («esta respuesta no responde la pregunta, debería eliminarse»), y perderlos sería perder
decisiones suyas.

Cada comentario sale **anclado**: a qué pregunta pertenece y, si está pegado a una opción
concreta, a cuál. Sin el ancla, «la última respuesta sin clasificar no responde la pregunta» es
una frase que no se puede aplicar a nada — hay 32 preguntas y no dice cuál. Word guarda el ancla
en document.xml (`commentRangeStart`) y el texto en comments.xml; hay que cruzarlos.
"""
import argparse
import collections
import json
import os
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def q(t):
    return f"{{{W}}}{t}"


def parrafos(el):
    out = []
    for p in el.iter(q("p")):
        t = "".join(x.text or "" for x in p.iter(q("t"))).strip()
        if t:
            out.append(t)
    return out


# Un eje se reconoce por cómo empieza su primer párrafo. La lista es deliberadamente laxa:
# Emily escribe «Numerical per week», «Numerical sessions per month», «Quantitative»…
TIPO = re.compile(r"^(nominal|binary|numerical|quantitative|cuantitativ|numeric)", re.I)


def ids_de(el):
    """Los id de comentario que tocan este elemento (inicio de rango o marca de referencia)."""
    out = [e.get(q("id")) for e in el.iter(q("commentRangeStart"))]
    out += [e.get(q("id")) for e in el.iter(q("commentReference"))]
    return [i for i in out if i]


def leer(ruta):
    z = zipfile.ZipFile(ruta)
    cuerpo = ET.fromstring(z.read("word/document.xml")).find(q("body"))
    preguntas, panel, pendiente = [], None, None
    n_en_panel = collections.Counter()
    anclas = {}                                # id de comentario -> {qid, opcion}
    for hijo in cuerpo:
        tag = hijo.tag.split("}")[1]
        if tag == "p":
            t = "".join(x.text or "" for x in hijo.iter(q("t"))).strip()
            if not t:
                continue
            m = re.match(r"^Panel\s+(\d+)", t, re.I)
            if m:
                panel = int(m.group(1))
                continue
            if t.lower().startswith("posturas"):
                continue
            pendiente = t                      # el último párrafo antes de la tabla manda
            # un comentario sobre el enunciado pertenece a la pregunta que viene
            for i in ids_de(hijo):
                anclas.setdefault(i, {"qid": "P%s_Q%s" % (panel, n_en_panel[panel] + 1),
                                      "opcion": None})
        elif tag == "tbl" and pendiente is not None:
            n_en_panel[panel] += 1
            qid = "P%s_Q%s" % (panel, n_en_panel[panel])
            ejes = []
            for tc in hijo.iter(q("tc")):
                ps = parrafos(tc)
                # el ancla más fina posible: el párrafo (la opción) al que está pegado
                for pp in tc.iter(q("p")):
                    texto = "".join(x.text or "" for x in pp.iter(q("t"))).strip()
                    for i in ids_de(pp):
                        anclas[i] = {"qid": qid, "opcion": texto or None}
                for i in ids_de(tc):
                    anclas.setdefault(i, {"qid": qid, "opcion": None})
                if not ps:
                    continue
                if TIPO.match(ps[0]):
                    ejes.append({"tipo": ps[0], "opciones": ps[1:]})
                else:
                    ejes.append({"tipo": "(sin etiqueta)", "opciones": ps})
            for i in ids_de(hijo):
                anclas.setdefault(i, {"qid": qid, "opcion": None})
            preguntas.append({"panel": panel, "pregunta": pendiente,
                              "qid": qid, "ejes": ejes})
            pendiente = None

    comentarios = []
    if "word/comments.xml" in z.namelist():
        enunciados = {p["qid"]: p["pregunta"] for p in preguntas}
        for c in ET.fromstring(z.read("word/comments.xml")).iter(q("comment")):
            txt = " ".join(parrafos(c))
            if not txt:
                continue
            a = anclas.get(c.get(q("id")), {})
            comentarios.append({"autor": c.get(q("author")), "texto": txt,
                                "qid": a.get("qid"), "opcion": a.get("opcion"),
                                "pregunta": enunciados.get(a.get("qid"))})
    return preguntas, comentarios


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docx")
    ap.add_argument("--salida", default="docs/emily_posturas_varias_opciones.json")
    ap.add_argument("--comentarios", default=None,
                    help="dónde dejar los comentarios de Word (por defecto, junto al JSON)")
    args = ap.parse_args()

    preguntas, comentarios = leer(args.docx)
    por_panel = collections.Counter(p["panel"] for p in preguntas)
    n_ejes = sum(len(p["ejes"]) for p in preguntas)
    n_ops = sum(len(e["opciones"]) for p in preguntas for e in p["ejes"])

    if len(preguntas) != 32:
        print(f"  AVISO: salieron {len(preguntas)} preguntas, se esperaban 32.")
        print("  Revisar si el documento cambió de estructura antes de regenerar la taxonomía.")

    os.makedirs(os.path.dirname(args.salida) or ".", exist_ok=True)
    with open(args.salida, "w", encoding="utf-8") as f:
        json.dump(preguntas, f, ensure_ascii=False, indent=1)

    ruta_com = args.comentarios or os.path.splitext(args.salida)[0] + "_comentarios.json"
    if comentarios:
        with open(ruta_com, "w", encoding="utf-8") as f:
            json.dump(comentarios, f, ensure_ascii=False, indent=1)

    print(f"{len(preguntas)} preguntas  ·  {n_ejes} ejes  ·  {n_ops} opciones")
    print("  por panel:", dict(sorted(por_panel.items())))
    print(f"  -> {args.salida}")
    if comentarios:
        sin_ancla = sum(1 for c in comentarios if not c["qid"])
        print(f"\n{len(comentarios)} comentarios de Word -> {ruta_com}")
        for c in comentarios:
            donde = c["qid"] or "SIN ANCLA"
            sobre = f"  ·  sobre «{c['opcion']}»" if c.get("opcion") else ""
            print(f"  {donde:8}{sobre}")
            print(f"    [{c['autor']}] {c['texto'][:100]}")
        if sin_ancla:
            # Pasa cuando Emily borra el texto comentado pero deja el comentario: Word lo guarda
            # en comments.xml sin rango en document.xml. Hay que preguntarle a qué se refería.
            print(f"\n  AVISO: {sin_ancla} comentario(s) sin ancla — Word los guardó sueltos.")
    print("\nSiguiente paso:  python3 tools/build_taxonomy.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
