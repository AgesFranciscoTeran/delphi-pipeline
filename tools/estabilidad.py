#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compara dos o más corridas: ¿cuánto cambia la etiqueta de una respuesta entre corridas?

    python3 tools/estabilidad.py Resultados_a Resultados_b [Resultados_c ...]

Qué mide y por qué
------------------
Un artículo de métodos tiene que poder decir cuánto de un resultado es el método y cuánto es
ruido. Hay dos fuentes de variación distintas que se confunden con facilidad:

  * MISMA configuración, dos corridas -> no-determinación del servidor (vLLM batchea y no
    garantiza bit a bit).
  * CONFIGURACIONES distintas -> el efecto de la decisión de diseño (p. ej. decodificación
    guiada sí/no).

Sólo se pueden separar corriendo lo mismo dos veces. Comparar una corrida guiada contra una
libre y atribuir la diferencia al guiado es confundir las dos cosas: es exactamente el error
que este script existe para evitar.

Compara al nivel que importa —la etiqueta que termina en la tabla— y no el texto crudo:
la opción elegida en las categóricas y la banda en las numéricas.
"""
import itertools
import json
import os
import sys

import pandas as pd


def qid(panel, pregunta):
    q = str(pregunta)
    return "P%s_Q%s" % (panel, q[1:] if q.upper().startswith("Q") else q)


def cargar(carpeta):
    ruta = os.path.join(carpeta, "02_extracted.csv")
    if not os.path.exists(ruta):
        raise SystemExit(f"No encuentro {ruta}")
    d = pd.read_csv(ruta)
    d = d[d.is_valid_response].copy()
    d["qid"] = [qid(p, q) for p, q in zip(d.Panel, d.Question)]
    # La etiqueta comparable: opción en categóricas, banda en numéricas.
    d["etiqueta"] = d.selected_option.where(
        d.question_type.isin(["nominal", "binary"]), d.band)
    d["etiqueta"] = d.etiqueta.fillna("(sin etiqueta)")
    manifiesto = os.path.join(carpeta, "run_manifest.json")
    cfg = {}
    if os.path.exists(manifiesto):
        ext = [r for r in json.load(open(manifiesto)) if r.get("step") == "extract_arguments"]
        if ext:
            u = ext[-1]
            cfg = {"modelo": u.get("model"), "taxonomía": u.get("taxonomy_hash"),
                   "guiado": u.get("guided_json"), "fallos": u.get("n_failed"),
                   "fecha": str(u.get("timestamp"))[:16]}
    return d.set_index("response_id"), cfg


def comparar(a, b, nombre_a, nombre_b):
    comunes = a.index.intersection(b.index)
    ea, eb = a.loc[comunes, "etiqueta"], b.loc[comunes, "etiqueta"]
    distintas = ea != eb
    print(f"\n── {nombre_a}  vs  {nombre_b} ──")
    print(f"  respuestas comparables: {len(comunes)}")
    n = int(distintas.sum())
    print(f"  cambian de etiqueta:    {n}  ({n / len(comunes) * 100:.1f} %)")
    if not n:
        print("  idénticas.")
        return
    dif = pd.DataFrame({"qid": a.loc[comunes, "qid"][distintas],
                        "tipo": a.loc[comunes, "question_type"][distintas],
                        nombre_a: ea[distintas], nombre_b: eb[distintas]})
    por_tipo = dif.tipo.value_counts().to_dict()
    total_tipo = a.loc[comunes, "question_type"].value_counts().to_dict()
    print("  por tipo de pregunta:")
    for t, k in sorted(por_tipo.items(), key=lambda kv: -kv[1]):
        print(f"     {t:13} {k:3} de {total_tipo.get(t, 0):3}  ({k / total_tipo[t] * 100:.0f} %)")
    print("  preguntas más inestables:")
    for q, k in dif.qid.value_counts().head(6).items():
        print(f"     {q:8} {k}")
    print("  ejemplos:")
    for rid, r in dif.head(5).iterrows():
        print(f"     {rid}  {r[nombre_a]!r} -> {r[nombre_b]!r}")
    return dif


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    carpetas = sys.argv[1:]
    datos, cfgs = {}, {}
    for c in carpetas:
        nombre = os.path.basename(c.rstrip("/"))
        datos[nombre], cfgs[nombre] = cargar(c)

    print("── Qué produjo cada corrida ──")
    for nombre, cfg in cfgs.items():
        detalle = ", ".join(f"{k}={v}" for k, v in cfg.items()) if cfg else "(sin manifiesto)"
        print(f"  {nombre:34} {detalle}")

    misma = {tuple(sorted((c.get("modelo"), c.get("taxonomía"), c.get("guiado")) for c in [cfg]))
             for cfg in cfgs.values() if cfg}
    if len(misma) == 1 and len(carpetas) > 1:
        print("\n  Misma configuración en todas: lo que salga es no-determinación del servidor.")
    elif len(carpetas) > 1:
        print("\n  OJO: las configuraciones difieren. Lo que salga mezcla el efecto del cambio")
        print("  con la no-determinación. Para separarlos hacen falta dos corridas por config.")

    difs = []
    for x, y in itertools.combinations(datos, 2):
        difs.append(comparar(datos[x], datos[y], x, y))

    todas = [d for d in difs if d is not None and len(d)]
    if todas:
        salida = "estabilidad_diferencias.csv"
        pd.concat(todas).to_csv(salida)
        print(f"\n  Detalle completo en {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
