"""
Kappa de cada modelo contra las etiquetas de Emily (v2). Faltaba en la v1 (el README lo citaba).

Entradas:
  * la hoja de validación llenada por Emily (`validation_emily_done.xlsx` o la que genere
    make_validation_sample.py): columnas response_id, question_type, human_label, notes.
    `human_label` puede ser una LETRA (A, B…), un NÚMERO (1-based; 0 = ninguna), el TEXTO de la
    opción / banda, "NONE"/"--" (ninguna encaja / respuesta inválida) o una categoría nueva que
    no está en la taxonomía (se cuenta como "Unclassified" para el modelo, y se lista aparte
    porque es insumo para la Fase 1).
  * uno o más archivos con salidas de modelos: `model_comparison.csv` (columnas gemma/deepseek)
    o `02_extracted.csv` (columna selected_option / band; se etiqueta con el modelo del CSV).

Salida: acuerdo y kappa de Cohen con IC 95 % bootstrap, por tipo de pregunta, y la lista de
desacuerdos. Con n=44 los intervalos son anchos; la Fase 3 usa 200–300 ítems y dos codificadores.

    python score_validation.py Resultados/validation_emily_done.xlsx Resultados/model_comparison.csv
    python score_validation.py Resultados/validation_emily_done.xlsx Resultados/02_extracted.csv
"""
import re
import sys
import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score
from config import *
from taxonomy import EMILY_TAXONOMY

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def qid_of(rid):
    m = re.match(r"Pan(\d+)_R\d+_Q(\d+)_", rid)
    return f"P{m.group(1)}_Q{m.group(2)}"


def _norm(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def map_human_label(label, tax):
    """Devuelve (etiqueta comparable, estado). estado: in_taxonomy | none | invalid | new_category."""
    lab = "" if pd.isna(label) else str(label).strip()
    items = tax["options"] if tax["type"] in ("nominal", "binary") else list(tax["bands"].keys())
    if lab.upper() in ("NONE", "0") or lab == "":
        return "Unclassified", "none"
    if lab in ("--", "-", "N/A", "n/a"):
        return "Unclassified", "invalid"
    if len(lab) == 1 and lab.upper() in LETTERS[:len(items)]:
        return items[LETTERS.index(lab.upper())], "in_taxonomy"
    if lab.isdigit() and 1 <= int(lab) <= len(items):
        return items[int(lab) - 1], "in_taxonomy"
    for it in items:
        if _norm(lab) == _norm(it) or _norm(lab).startswith(_norm(it) + " "):
            return it, "in_taxonomy"
    return lab, "new_category"


def model_columns(df, path):
    """Columnas de modelos disponibles en un archivo de salidas."""
    if "gemma" in df.columns or "deepseek" in df.columns:
        return {c: c for c in df.columns if c in ("gemma", "deepseek")}
    if "selected_option" in df.columns:
        name = str(df.get("extraction_model", pd.Series(["model"])).dropna().iloc[0]).split("/")[-1]
        # Banda comparable: derivada del valor convertido a la unidad de la pregunta (igual que
        # consensus_metrics); la banda cruda del LLM sólo como respaldo cuando no hay número.
        from consensus_metrics import to_question_unit, derive_band, unit_from_raw
        from taxonomy import get_taxonomy
        bands = []
        for _, r in df.iterrows():
            if r.get("question_type") in ("quantitative", "hybrid"):
                tax = get_taxonomy(r["Panel"], r["Question"]) or {}
                u, _src = unit_from_raw(r.get("value_raw"), r.get("value_unit"))
                v, _st = to_question_unit(r.get("numeric_value"), u, tax.get("unit"))
                b = derive_band(v, tax.get("bands", {}))
                bands.append(b if b is not None else r.get("band"))
            else:
                bands.append(None)
        df["_band_final"] = bands
        df[name] = np.where(df["question_type"].isin(["nominal", "binary"]),
                            df["selected_option"], df["_band_final"])
        return {name: name}
    raise ValueError(f"No reconozco columnas de modelo en {path}")


def boot_ci(gold, pred, B=2000, seed=42):
    rng = np.random.default_rng(seed)
    ks = []
    idx = np.arange(len(gold))
    for _ in range(B):
        s = rng.choice(idx, len(idx), replace=True)
        g, p = gold.iloc[s], pred.iloc[s]
        if g.nunique() > 1 and p.nunique() > 1:
            ks.append(cohen_kappa_score(g, p))
    return (np.percentile(ks, [2.5, 97.5]) if ks else (np.nan, np.nan))


def main(human_path, *model_paths):
    hum = pd.read_excel(human_path) if human_path.endswith("xlsx") else pd.read_csv(human_path)
    hum["qid"] = hum["response_id"].map(qid_of)
    mapped = [map_human_label(l, EMILY_TAXONOMY[q]) for l, q in zip(hum["human_label"], hum["qid"])]
    hum["gold"] = [m[0] for m in mapped]
    hum["gold_status"] = [m[1] for m in mapped]
    hum["is_cat"] = hum["question_type"].isin(["nominal", "binary"])
    # Dos lecturas del gold: estricta (una categoría nueva de la codificadora cuenta como
    # desacuerdo) y laxa (cuenta como "Unclassified", que es lo que el modelo debía responder
    # cuando ninguna opción encaja). Se reportan ambas.
    hum["gold_strict"] = hum["gold"]
    hum["gold"] = np.where(hum["gold_status"].isin(["new_category", "invalid"]), "Unclassified", hum["gold"])

    preds = {}
    for p in model_paths:
        d = pd.read_csv(p)
        cols = model_columns(d, p)
        d = d.set_index("response_id")
        for name, col in cols.items():
            preds[name] = hum["response_id"].map(d[col]).fillna("Unclassified").astype(str).values
    for name, v in preds.items():
        hum[name] = v

    print(f"Ítems: {len(hum)} | etiquetas humanas: {hum['gold_status'].value_counts().to_dict()}")
    new = hum[hum["gold_status"] == "new_category"]
    if len(new):
        print("\nCategorías nuevas propuestas por la codificadora (insumo para la taxonomía v2):")
        for _, r in new.iterrows():
            print(f"  {r['qid']:7s} {r['response_id']:24s} -> '{r['human_label']}'")

    subsets = [("todos", hum), ("nominal + binary", hum[hum["is_cat"]]), ("bandas (quant + hybrid)", hum[~hum["is_cat"]])]
    for gold_col, title in (("gold", "LAXO: categoría nueva de la codificadora = Unclassified"),
                            ("gold_strict", "ESTRICTO: categoría nueva = desacuerdo")):
        print(f"\n── {title} ──")
        print("%-26s %-12s %8s %8s %16s" % ("subconjunto", "modelo", "n", "acuerdo", "kappa [IC 95%]"))
        for label, sub in subsets:
            for name in preds:
                if len(sub) < 3:
                    continue
                agree = (sub[name] == sub[gold_col]).mean()
                k = cohen_kappa_score(sub[gold_col], sub[name]) if sub[gold_col].nunique() > 1 else np.nan
                lo, hi = boot_ci(sub[gold_col].reset_index(drop=True), sub[name].reset_index(drop=True))
                print("%-26s %-12s %8d %7.0f%% %5.2f [%.2f, %.2f]" % (label, name, len(sub), agree * 100, k, lo, hi))

    print("\nDesacuerdos:")
    for name in preds:
        dis = hum[hum[name] != hum["gold"]]
        print(f"\n  {name}: {len(dis)} desacuerdos")
        for _, r in dis.iterrows():
            print(f"    {r['response_id']:24s} humano='{r['gold']}' modelo='{r[name]}'  | {str(r.get('response', ''))[:70]}")
    out = human_path.rsplit(".", 1)[0] + "_scored.csv"
    hum.to_csv(out, index=False)
    print(f"\nGuardado: {out}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    main(*sys.argv[1:])
