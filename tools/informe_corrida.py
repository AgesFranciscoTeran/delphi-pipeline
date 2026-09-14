#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resumen de una corrida para decidir qué pedirle a Emily.

    python3 tools/informe_corrida.py
    DELPHI_RESULTADOS=/ruta/otra python3 tools/informe_corrida.py

Imprime el % sin clasificar de TODAS las preguntas categóricas (el resumen del pipeline sólo
muestra el top 5), las respuestas concretas que no encajan en la peor, cuántas respuestas
numéricas llegaron sin periodo declarado, y qué modelo y taxonomía produjeron todo eso.
"""
import pandas as pd, sys, os, json, collections
R = os.environ.get("DELPHI_RESULTADOS", "Resultados")
d = pd.read_csv(os.path.join(R, "02_extracted.csv"))
d["qid"] = ["P%s_Q%s" % (p, str(q)[1:] if str(q).upper().startswith("Q") else q)
            for p, q in zip(d.Panel, d.Question)]
v = d[d.is_valid_response & (d.extraction_status == "ok")]
cat = v[v.question_type.isin(["nominal", "binary"])]

print("### SIN CLASIFICAR POR PREGUNTA (todas las categóricas)")
filas = []
for q, g in cat.groupby("qid"):
    sinc = g.selected_option.eq("Unclassified")
    filas.append((q, len(g), int(sinc.sum()), round(sinc.mean() * 100)))
filas.sort(key=lambda r: -r[3])
for q, n, s, pct in filas:
    print(f"  {q:8} {s:3}/{n:<3} {pct:3}%")

print("\n### P4_Q8 — qué responden los que no encajan")
for t in cat[cat.qid.eq("P4_Q8") & cat.selected_option.eq("Unclassified")].Response.astype(str).head(8):
    print("   -", " ".join(t.split())[:130])

print("\n### UNIDADES SIN PERIODO (decisión 5)")
qn = v[v.question_type.isin(["quantitative", "hybrid"])]
amb = qn[qn.value_unit.eq("hours/?")]
print("  hours/? :", len(amb), "respuestas, en", sorted(amb.qid.unique()))
print("  por pregunta:", dict(collections.Counter(amb.qid)))

print("\n### FALLOS QUE QUEDAN")
e = os.path.join(R, "02_extraction_errors.csv")
if os.path.exists(e):
    er = pd.read_csv(e)
    print(" ", len(er), "->", dict(er.error.str.slice(0, 45).value_counts().head(3)))

mp = os.path.join(R, "run_manifest.json")
if os.path.exists(mp):
    ext = [r for r in json.load(open(mp)) if r.get("step") == "extract_arguments"]
    if ext:
        u = ext[-1]
        print("\n### CORRIDA:", u.get("model"), "| taxonomía", u.get("taxonomy_hash"),
              "| fallos", u.get("n_failed"), "|", str(u.get("timestamp"))[:16])
