#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Consolida k corridas en una sola por voto mayoritario, y mide la estabilidad de cada ítem.

    python3 tools/consolidar.py Resultados_libre_1 Resultados_libre_2 ... --salida Resultados_k5
    DELPHI_RESULTADOS=Resultados_k5 ./run.sh --solo-sitio

Por qué existe
--------------
Medido el 15-09-2026 con GLM-5.3-Flash a temperatura 0 y semilla fija: dos corridas idénticas
del mismo código sobre los mismos datos difieren en el **5,8 %** de las etiquetas, y no sólo en
la capa numérica — las categóricas se mueven un 6 %. No es un bug del pipeline: vLLM agrupa
peticiones en lotes de composición variable y la suma en coma flotante no es asociativa, así
que el mismo prompt puede dar distinta salida. `seed` no lo evita.

Consecuencia: **una corrida sola no es una medición.** Es una muestra de un clasificador
estocástico. Lo que sí es una medición es el voto mayoritario de k corridas, acompañado del
grado de acuerdo entre ellas — que además dice, ítem por ítem, de cuáles fiarse.

Qué produce
-----------
Un `02_extracted.csv` con la etiqueta modal y tres columnas nuevas:

    n_corridas     en cuántas corridas se extrajo este ítem
    n_acuerdo      cuántas coinciden con la etiqueta modal
    estabilidad    n_acuerdo / n_corridas

Para que el resto de columnas sea coherente (valor, unidad, argumento), la fila se toma
entera de una corrida que votó con la mayoría, en vez de mezclar campos de varias.

Un ítem que falló en una corrida y salió en otras queda resuelto: con k corridas los fallos
por truncado se cubren entre sí.
"""
import argparse
import collections
import json
import os
import shutil
import sys

import pandas as pd


def cargar(carpeta):
    ruta = os.path.join(carpeta, "02_extracted.csv")
    if not os.path.exists(ruta):
        raise SystemExit(f"No encuentro {ruta}")
    return pd.read_csv(ruta)


def etiqueta_de(fila):
    """La etiqueta que termina en la tabla.

    Categóricas: la opción. Numéricas: la banda si la hay y, si no, el valor — porque muchas
    respuestas numéricas traen cifra sin banda (el panelista dijo "4 horas" y la banda se
    deriva después, en consensus_metrics). Tratarlas como no resueltas por no tener banda
    dejaba fuera de la consolidación casi un centenar de ítems perfectamente extraídos.
    """
    if fila.get("question_type") in ("nominal", "binary"):
        v = fila.get("selected_option")
        return v if isinstance(v, str) and v else None
    banda = fila.get("band")
    if isinstance(banda, str) and banda:
        return banda
    valor = fila.get("numeric_value")
    if valor is not None and not pd.isna(valor):
        return f"num:{float(valor):g}"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("carpetas", nargs="+")
    ap.add_argument("--salida", required=True)
    ap.add_argument("--curva", action="store_true",
                    help="cuánto se parece el voto de k' corridas al de todas: justifica el k")
    args = ap.parse_args()

    if len(args.carpetas) < 2:
        raise SystemExit("Hacen falta al menos dos corridas: con una no hay nada que consolidar.")

    corridas = {os.path.basename(c.rstrip("/")): cargar(c) for c in args.carpetas}
    k = len(corridas)
    print(f"Consolidando {k} corridas: {', '.join(corridas)}\n")

    # Todas comparten el mismo universo de respuestas (sale del mismo Excel).
    base = list(corridas.values())[0].copy()
    filas_por_id = {n: d.set_index("response_id") for n, d in corridas.items()}

    salida, estab = [], []
    for _, fila_base in base.iterrows():
        rid = fila_base["response_id"]
        votos, filas = [], {}
        for nombre, d in filas_por_id.items():
            if rid not in d.index:
                continue
            f = d.loc[rid]
            if f.get("extraction_status") != "ok":
                continue
            e = etiqueta_de(f)
            if e is None:
                continue
            votos.append(e)
            filas.setdefault(e, (nombre, f))

        if not votos:
            salida.append(fila_base)          # nadie la resolvió: se conserva como está
            estab.append((len(votos), 0, None))
            continue

        cuenta = collections.Counter(votos)
        modal, n_acuerdo = cuenta.most_common(1)[0]
        _, representante = filas[modal]       # fila completa de una corrida que votó con la mayoría
        salida.append(representante.rename(rid))
        estab.append((len(votos), n_acuerdo, n_acuerdo / len(votos)))

    df = pd.DataFrame(salida).reset_index(drop=True)
    df["response_id"] = base["response_id"].values
    df["n_corridas"] = [e[0] for e in estab]
    df["n_acuerdo"] = [e[1] for e in estab]
    df["estabilidad"] = [e[2] for e in estab]

    os.makedirs(args.salida, exist_ok=True)
    # El resto de la salida (01_*, 02a_*) no depende del LLM: se copia de la primera corrida.
    for nombre in ("01_individual_clean.csv", "01_synthesis_clean.csv",
                   "01_coverage_stats.json", "02a_question_types.csv"):
        origen = os.path.join(args.carpetas[0], nombre)
        if os.path.exists(origen):
            shutil.copy2(origen, os.path.join(args.salida, nombre))
    df.to_csv(os.path.join(args.salida, "02_extracted.csv"), index=False)

    manifiestos = []
    for c in args.carpetas:
        mp = os.path.join(c, "run_manifest.json")
        if os.path.exists(mp):
            manifiestos.extend(json.load(open(mp)))
    manifiestos.append({"step": "consolidar", "k_corridas": k,
                        "corridas": [os.path.basename(c.rstrip("/")) for c in args.carpetas],
                        "model": manifiestos[-1].get("model") if manifiestos else None,
                        "taxonomy_hash": manifiestos[-1].get("taxonomy_hash") if manifiestos else None,
                        "timestamp": pd.Timestamp.now().isoformat(timespec="seconds")})
    json.dump(manifiestos, open(os.path.join(args.salida, "run_manifest.json"), "w"), indent=2)

    # ── informe ──
    res = df[df.n_corridas > 0]
    unanimes = int((res.estabilidad == 1.0).sum())
    validos = int(df.is_valid_response.sum()) if "is_valid_response" in df else len(df)
    print(f"── Estabilidad sobre {len(res)} ítems resueltos (de {validos} válidos) ──")
    print(f"  unánimes en las {k} corridas: {unanimes}  ({unanimes / len(res) * 100:.1f} %)")
    for umbral in (0.8, 0.6):
        n = int((res.estabilidad >= umbral).sum())
        print(f"  acuerdo >= {umbral:.0%}:{'':13} {n:4}  ({n / len(res) * 100:.1f} %)")
    # "Sin etiqueta" no es lo mismo que "falló": una respuesta numérica en la que el panelista
    # no dio ninguna cifra se extrae perfectamente y no tiene nada que votar. Contarlas juntas
    # hacía parecer que 28 ítems habían fallado cuando la mayoría son respuestas sin número.
    sin = df[(df.n_corridas == 0) & df.get("is_valid_response", True)]
    fallidos = int((sin.get("extraction_status") == "failed").sum()) if len(sin) else 0
    print(f"  sin etiqueta en ninguna corrida: {len(sin)}")
    print(f"     de esos, extracciones fallidas: {fallidos}")
    print(f"     el resto se extrajo bien pero no tiene nada que votar")
    print(f"     (respuesta numérica sin cifra, o categórica sin opción)")
    print(f"\n  La columna `estabilidad` queda en el CSV: un ítem con acuerdo < 100 % es")
    print(f"  una etiqueta que depende de qué corrida miraste.")

    inestables = res[res.estabilidad < 1.0]
    if len(inestables):
        d = inestables.copy()
        d["qid"] = ["P%s_Q%s" % (p, str(q)[1:] if str(q).upper().startswith("Q") else q)
                    for p, q in zip(d.Panel, d.Question)]
        print("\n  preguntas con más ítems inestables:")
        for q, n in d.qid.value_counts().head(8).items():
            total = sum(1 for _, r in res.iterrows()
                        if "P%s_Q%s" % (r.Panel, str(r.Question)[1:]) == q)
            print(f"     {q:8} {n:3}")
    if args.curva and k >= 3:
        import itertools
        print(f"\n── ¿Cuántas corridas hacen falta? ──")
        print(f"  Acuerdo del voto de k' corridas con el voto de las {k}, sobre los {len(res)}")
        print(f"  ítems resueltos. Si se aplana, añadir corridas ya no cambia el resultado.")
        voto_pleno = {r["response_id"]: etiqueta_de(r) for _, r in res.iterrows()}
        nombres = list(filas_por_id)
        for kp in range(2, k):
            coincidencias, total = 0, 0
            for sub in itertools.combinations(nombres, kp):
                for rid, pleno in voto_pleno.items():
                    v = []
                    for nombre in sub:
                        d = filas_por_id[nombre]
                        if rid in d.index and d.loc[rid].get("extraction_status") == "ok":
                            e = etiqueta_de(d.loc[rid])
                            if e:
                                v.append(e)
                    if not v:
                        continue
                    total += 1
                    coincidencias += (collections.Counter(v).most_common(1)[0][0] == pleno)
            print(f"     k={kp}: {coincidencias / total * 100:5.1f} %")
        print(f"     k={k}: 100.0 %  (es la referencia)")

    print(f"\nEscrito en {args.salida}/02_extracted.csv")
    print(f"  DELPHI_RESULTADOS={args.salida} ./run.sh --sin-llm")
    return 0


if __name__ == "__main__":
    sys.exit(main())
