"""
Muestra para la validación formal (Fase 3): hojas ciegas contra la taxonomía vigente.

    python muestra_validacion.py                    # 240 respuestas, dos codificadores
    python muestra_validacion.py --n 300 --codificadores A B C

Por qué existe
--------------
Las 44 etiquetas de Emily se hicieron contra una taxonomía que ya no existe: en 19 propuso una
categoría nueva, y la v3/v4 incorporaron varias. Ahora el modelo elige esa opción y la
puntuación lo cuenta como desacuerdo. Rehacer el κ exige etiquetar de nuevo, y lo eficiente es
hacerlo ya con la muestra de la validación formal: 200–300 respuestas, dos codificadores.

Cómo muestrea
-------------
Estratificada por pregunta: cada pregunta recibe una parte proporcional a sus respuestas
válidas, con un mínimo de MIN_POR_PREGUNTA (o todas, si tiene menos). Dentro de la pregunta,
se reparte entre rondas por turnos, para que no salga todo de una sola ronda. Semilla fija: la
misma taxonomía y los mismos datos dan la misma muestra.

Las hojas no muestran nada del modelo. Cada codificador recibe su propio archivo, con las
mismas respuestas en otro orden, para que ninguno vea las etiquetas del otro.

Salida: datos/validacion_v4_<codificador>.xlsx (no se versiona: tiene respuestas del panel).
Se puntúa con:
    python score_validation.py ../datos/validacion_v4_A.xlsx ../Resultados_v4/02_extracted.csv \\
                                ../datos/validacion_v4_B.xlsx
"""
import argparse
import math
import os

import numpy as np
import pandas as pd

from config import *
from taxonomy import get_taxonomy, taxonomy_hash

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
MIN_POR_PREGUNTA = 5
SEMILLA = 42

INSTRUCCIONES = [
    "Escribe en «human_label» la LETRA de la opción que mejor describe la respuesta.",
    "NONE si ninguna opción encaja.",
    "FUERA si la respuesta no contesta la pregunta (aunque la pregunta no tenga esa opción).",
    "Preguntas numéricas: la letra de la banda, y el número con su unidad en «notes».",
    "Etiqueta a ciegas: no mires la salida del sistema ni la hoja de la otra persona.",
    "Si dudas entre dos opciones, elige una y anota la otra en «notes».",
]


def opciones_de(tax):
    if tax["type"] in ("nominal", "binary"):
        return list(tax["options"])
    return [f"{nombre} ({rango})" for nombre, rango in tax["bands"].items()]


def asignar(tamanos, n):
    """{qid: cuántas} proporcional a tamanos, con mínimo, sin pasarse de lo que hay."""
    total = sum(tamanos.values())
    return {q: min(t, max(MIN_POR_PREGUNTA, round(n * t / total))) for q, t in tamanos.items()}


def muestrear(ind, n, semilla=SEMILLA):
    ind = ind[ind["is_valid_response"]].copy()
    ind["qid"] = "P" + ind[COL_PANEL].astype(str) + "_Q" + ind[COL_QUESTION].astype(str)
    ind = ind[[get_taxonomy(p, q) is not None for p, q in zip(ind[COL_PANEL], ind[COL_QUESTION])]]
    cuota = asignar(ind.groupby("qid").size().to_dict(), n)
    rng = np.random.default_rng(semilla)
    elegidas = []
    for qid, g in ind.groupby("qid", sort=True):
        # por turnos entre rondas: R1, R2, R3, R1, ...
        colas = [list(rng.permutation(r.index)) for _, r in g.groupby(COL_ROUND)]
        orden = [i for tanda in zip(*[c + [None] * (len(g) - len(c)) for c in colas])
                 for i in tanda if i is not None]
        elegidas.extend(orden[:cuota[qid]])
    return ind.loc[elegidas]


def hoja(muestra, semilla):
    filas = []
    for _, r in muestra.sample(frac=1, random_state=semilla).iterrows():
        tax = get_taxonomy(r[COL_PANEL], r[COL_QUESTION])
        filas.append({
            "response_id": r["response_id"],
            "panel": r[COL_PANEL],
            "question_type": tax["type"],
            "question": r[COL_QUESTION_TEXT],
            "response": r[COL_RESPONSE],
            "options": "\n".join(f"{LETTERS[i]}. {o}" for i, o in enumerate(opciones_de(tax))),
            "human_label": "",
            "notes": "",
        })
    return pd.DataFrame(filas)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=240)
    ap.add_argument("--codificadores", nargs="+", default=["A", "B"])
    args = ap.parse_args()

    ind = pd.read_csv(os.path.join(OUTPUT_DIR, "01_individual_clean.csv"))
    muestra = muestrear(ind, args.n)
    salida = os.path.dirname(DATA_PATH)
    print(f"Muestra: {len(muestra)} respuestas de {muestra.qid.nunique()} preguntas "
          f"(taxonomía {taxonomy_hash()})")
    print("  por panel:", muestra[COL_PANEL].value_counts().sort_index().to_dict())
    print("  por ronda:", muestra[COL_ROUND].value_counts().sort_index().to_dict())
    for i, cod in enumerate(args.codificadores):
        ruta = os.path.join(salida, f"validacion_v4_{cod}.xlsx")
        with pd.ExcelWriter(ruta) as xw:
            hoja(muestra, SEMILLA + i).to_excel(xw, sheet_name="etiquetas", index=False)
            pd.DataFrame({"instrucciones": INSTRUCCIONES}).to_excel(
                xw, sheet_name="instrucciones", index=False)
        print(f"  {ruta}")


if __name__ == "__main__":
    main()
