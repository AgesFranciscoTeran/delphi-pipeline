#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Los comentarios de Word de Emily, indexados por pregunta.

Los escribe tools/leer_docx_emily.py al convertir el .docx. Van anclados: cada comentario sabe
a qué pregunta pertenece y, cuando está pegado a una celda concreta, a qué opción.

Por qué se leen aquí
--------------------
Varios comentarios suyos son decisiones sobre casos que el informe le va a volver a mostrar:
«las dos respuestas que no se clasifican no responden la pregunta, no hace falta añadir
opciones». Si el informe no los lleva al lado, el siguiente ciclo le pregunta otra vez lo mismo
y ella contesta otra vez lo mismo.
"""
import collections
import json
import os

RUTA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "docs", "emily_posturas_varias_opciones_comentarios.json")


def por_pregunta(ruta=None):
    """{qid: [comentario, ...]}. Vacío si el archivo no existe — no es obligatorio."""
    ruta = ruta or RUTA
    salida = collections.defaultdict(list)
    if not os.path.exists(ruta):
        return salida
    with open(ruta, encoding="utf-8") as f:
        for c in json.load(f):
            if c.get("qid"):
                salida[c["qid"]].append(c)
    return salida


def bloque(comentarios):
    """Las líneas markdown de los comentarios de una pregunta, o [] si no hay."""
    if not comentarios:
        return []
    L = ["**Lo que ya dijiste sobre esta pregunta** (comentario en el documento):\n"]
    for c in comentarios:
        sobre = f" *(sobre «{c['opcion']}»)*" if c.get("opcion") else ""
        L.append(f"- {c['texto']}{sobre}")
    L.append("")
    return L
