"""
Paso 4 — métricas de consenso (v2).

Cambios respecto a la v1:
  * Entropía normalizada por log2(K) con K = número de opciones de la taxonomía (constante por
    pregunta). La v1 dividía por las opciones *usadas* en cada ronda, y la métrica subía cuando
    el panel se concentraba (p. ej. de 3 opciones a 2).
  * Los NaN (extracción fallida) ya no cuentan como categoría (`pd.notna`).
  * Un solo denominador para las etiquetas: la proporción modal se calcula sobre las respuestas
    clasificadas, y sólo se etiqueta consenso si la cobertura es suficiente
    (n_classified >= MIN_N_CLASSIFIED y % sin clasificar <= MAX_UNCLASSIFIED_PCT). Si no,
    "Insuficiente". Las etiquetas viven aquí (CSV), no en visualize.py, para que tablas y
    figuras digan lo mismo.
  * Cuantitativas: la unidad del panelista se compara con la unidad de la pregunta; sólo se
    convierte con UNIT_CONVERSIONS (día<->semana); el resto se reporta como "otra unidad" y no
    entra en el cálculo. Se añaden mediana e IQR (más robustos que media/CV con n=7-10).
  * Convergencia en cuatro categorías: convergió / se dispersó / estable en acuerdo /
    estable sin acuerdo (la v1 pintaba de rojo a las preguntas unánimes en todas las rondas).
"""
import os
import re
import json
import numpy as np
import pandas as pd
from collections import Counter
from config import *
from taxonomy import get_taxonomy

CATEGORICAL = ("nominal", "binary")
NUMERIC = ("quantitative", "hybrid")


# ── categóricas ───────────────────────────────────────────────────────────────

def clean_labels(labels):
    """Sólo etiquetas reales: fuera NaN, None, '' y 'Unclassified'."""
    return [l for l in labels if isinstance(l, str) and l and l != "Unclassified"]


def normalized_entropy(labels, k_options):
    """Entropía de Shannon sobre las clasificadas, normalizada por log2(K opciones)."""
    counts = Counter(clean_labels(labels))
    total = sum(counts.values())
    if total == 0 or k_options <= 1:
        return np.nan
    probs = np.array([c / total for c in counts.values()])
    h = float(-(probs * np.log2(probs)).sum())
    return h / np.log2(k_options)


def modal_share(labels):
    counts = Counter(clean_labels(labels))
    total = sum(counts.values())
    return max(counts.values()) / total if total else np.nan


def categorical_label(share, n_classified, pct_unclassified, is_tie=False):
    if pd.isna(share) or n_classified < MIN_N_CLASSIFIED or pct_unclassified > MAX_UNCLASSIFIED_PCT:
        return "Insuficiente"
    if is_tie:
        return "Sin consenso"          # dos opciones empatadas en el máximo no son una opción dominante
    if share >= STRONG_AGREEMENT:
        return "Consenso fuerte"
    if share >= CLEAR_MAJORITY:
        return "Mayoría clara"
    if share >= DOMINANT_OPTION:
        return "Opción dominante"
    return "Sin consenso"


def categorical_consensus(df):
    cat = df[df["question_type"].isin(CATEGORICAL) & df["is_valid_response"]]
    records = []
    for (panel, q, rnd), grp in cat.groupby([COL_PANEL, COL_QUESTION, COL_ROUND]):
        labels = grp["selected_option"].tolist()
        classified = clean_labels(labels)
        counts = Counter(classified)
        tax = get_taxonomy(panel, q) or {}
        options = tax.get("options", [])
        n_total = len(labels)
        n_cls = len(classified)
        n_failed = int(grp["extraction_status"].ne("ok").sum()) if "extraction_status" in grp else 0
        pct_unc = (n_total - n_cls) / n_total * 100 if n_total else np.nan
        share = modal_share(labels)
        top = counts.most_common()
        is_tie = len(top) > 1 and top[0][1] == top[1][1]
        modal = None
        if top:
            tied = [o for o, c in top if c == top[0][1]]
            modal = top[0][0] if not is_tie else "Empate: " + " / ".join(sorted(tied))
        rec = {
            COL_PANEL: panel, COL_QUESTION: q, COL_ROUND: rnd,
            "question_id": f"P{panel}_Q{q}",
            COL_QUESTION_TEXT: grp[COL_QUESTION_TEXT].iloc[0],
            "n_responses": n_total,
            "n_classified": n_cls,
            "n_unclassified": n_total - n_cls,
            "n_extraction_failed": n_failed,
            "pct_unclassified": pct_unc,
            "modal_option": modal,
            "is_tie": is_tie,
            "modal_share": share,                          # sobre clasificadas
            "modal_share_all": (max(counts.values()) / n_total) if counts else np.nan,  # sobre todas
            "norm_entropy": normalized_entropy(labels, len(options)),
            "n_distinct_options": len(counts),
            "k_options": len(options),
            "consensus_label": categorical_label(share, n_cls, pct_unc, is_tie),
            "option_counts": json.dumps({opt: counts.get(opt, 0) for opt in options}, ensure_ascii=False),
        }
        records.append(rec)
    return pd.DataFrame(records).sort_values([COL_PANEL, COL_QUESTION, COL_ROUND])


# ── cuantitativas ─────────────────────────────────────────────────────────────

# ── unidad: respaldo determinista desde el texto crudo ────────────────────────
# El modelo etiqueta mal la unidad en una parte de los casos (manda a "other"
# respuestas que dicen "8 hours a day"). El periodo está escrito en value_raw, así
# que se deduce con una regla fija: determinista, auditable y testeable. Sólo actúa
# cuando el modelo devolvió "none"/"other"/"count"; una unidad válida del modelo manda.
_TIME_NOUN = re.compile(r"\b(hours?|horas?|hrs?)\b", re.I)
_OTHER_NOUN = re.compile(r"\b(patients?|pacientes?|students?|estudiantes?|cases?|casos?)\b", re.I)
_PERIOD = [
    ("hours/day",    re.compile(r"(per|each|a|/)\s*day|daily|al d[ií]a|por d[ií]a|diaria?s?", re.I)),
    ("hours/week",   re.compile(r"(per|each|a|/)\s*week|weekly|a la semana|por semana|semanal", re.I)),
    ("hours/module", re.compile(r"(per|each|a|/)\s*module|por m[oó]dulo", re.I)),
    ("hours/semester", re.compile(r"(per|each|a|/)\s*semester|por semestre", re.I)),
    ("hours/session", re.compile(r"(per|each|a|/)\s*session|por sesi[oó]n", re.I)),
]
UNIT_HOURS_ANY = "hours/?"     # dice horas pero no dice el periodo


def unit_from_raw(value_raw, model_unit):
    """Unidad deducida del texto tal como lo escribió el panelista."""
    if isinstance(model_unit, str) and model_unit not in ("none", "other", "count", ""):
        return model_unit, "model"
    raw = "" if value_raw is None or (isinstance(value_raw, float) and pd.isna(value_raw)) else str(value_raw)
    if not _TIME_NOUN.search(raw):
        # no habla de horas: "20 cardiovascular patients", "10 patients per week", "50"
        return (model_unit or "none"), ("other_noun" if _OTHER_NOUN.search(raw) else "unstated")
    for unit, rx in _PERIOD:
        if rx.search(raw):
            return unit, "raw_text"
    return UNIT_HOURS_ANY, "raw_text"      # "5 hours", "4-5 hours"


def to_question_unit(value, unit, question_unit):
    """Devuelve (valor_convertido, estado): 'same' | 'converted' | 'assumed' | 'other' | 'none'.

    'assumed' = el panelista no declaró unidad y se asume la de la pregunta (con rastro).
    'other'   = unidad declarada que no se puede llevar a la de la pregunta -> NO entra al
                consenso numérico (antes se asumía en silencio, que es como "an hour per week"
                terminó contando como 1 semestre en P1_Q1).
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None, "none"
    unit = unit if isinstance(unit, str) else "none"
    if unit == UNIT_HOURS_ANY:
        # dice horas sin periodo: sólo vale si la pregunta se mide en horas
        return (float(value), "assumed") if str(question_unit).startswith("hours/") else (None, "other")
    if unit == question_unit:
        return float(value), "same"
    factor = UNIT_CONVERSIONS.get((unit, question_unit))
    if factor is not None:
        return float(value) * factor, "converted"
    if unit in ("none", "count", ""):
        return float(value), "assumed"
    return None, "other"


def _parse_band_range(rng):
    """'1-2' -> [1,2]; '>6' -> (6,inf); '<50' -> (-inf,50); '50' -> [50,50]; texto -> None.
    Devuelve (lo, hi, lo_abierto, hi_abierto)."""
    import re as _re
    rng = str(rng).strip()
    m = _re.match(r"^(\d+\.?\d*)\s*-\s*(\d+\.?\d*)", rng)
    if m:
        return float(m.group(1)), float(m.group(2)), False, False
    m = _re.match(r"^>\s*(\d+\.?\d*)", rng)
    if m:
        return float(m.group(1)), float("inf"), True, False
    m = _re.match(r"^<\s*(\d+\.?\d*)", rng)
    if m:
        return float("-inf"), float(m.group(1)), False, True
    m = _re.match(r"^(\d+\.?\d*)$", rng)
    if m:
        return float(m.group(1)), float(m.group(1)), False, False
    return None


def derive_band(value, bands):
    """
    Banda desde el valor en la unidad de la pregunta. Si el valor cae en un hueco entre bandas
    (p. ej. 5.5 con bandas 3-5 / 6-8), se asigna la banda con el borde más cercano y se marca
    con derive_band.last_gap = True (la Fase 1 define bordes contiguos con Emily).
    """
    derive_band.last_gap = False
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    parsed = {name: _parse_band_range(rng) for name, rng in bands.items()}
    parsed = {k: v for k, v in parsed.items() if v is not None}
    if not parsed:
        return None
    for name, (lo, hi, lo_open, hi_open) in parsed.items():
        if (value > lo if lo_open else value >= lo) and (value < hi if hi_open else value <= hi):
            return name
    def dist(item):
        lo, hi, *_ = item[1]
        edges = [e for e in (lo, hi) if abs(e) != float("inf")]
        return min(abs(value - e) for e in edges) if edges else float("inf")
    name = min(parsed.items(), key=dist)[0]
    derive_band.last_gap = True
    return name


def quantitative_label(cv, rel_range, rel_iqr, n):
    if n < MIN_N_NUMERIC or pd.isna(cv):
        return "Insuficiente"
    s, m = QUANT_STRONG, QUANT_MODERATE
    if cv <= s["cv"] and rel_range <= s["rel_range"] and rel_iqr <= s["rel_iqr"]:
        return "Consenso fuerte"
    if cv <= m["cv"] and rel_range <= m["rel_range"] and rel_iqr <= m["rel_iqr"]:
        return "Convergencia moderada"
    return "Sin consenso"


def quantitative_consensus(df):
    quant = df[df["question_type"].isin(NUMERIC) & df["is_valid_response"]].copy()
    for col in ("value_unit", "band"):          # tolerar CSVs de la v1
        if col not in quant.columns:
            quant[col] = None
    conv, resolved, sources = [], [], []
    for _, r in quant.iterrows():
        tax = get_taxonomy(r[COL_PANEL], r[COL_QUESTION]) or {}
        u, src = unit_from_raw(r.get("value_raw"), r.get("value_unit"))
        v, status = to_question_unit(r["numeric_value"], u, tax.get("unit"))
        conv.append((v, status)); resolved.append(u); sources.append(src)
    quant["unit_resolved"] = resolved
    quant["unit_source"] = sources
    quant["parsed_value"] = [c[0] for c in conv]
    quant["unit_status"] = [c[1] for c in conv]
    derived, gaps = [], []
    for (_, r), (v, _st) in zip(quant.iterrows(), conv):
        tax = get_taxonomy(r[COL_PANEL], r[COL_QUESTION]) or {}
        b = derive_band(v, tax.get("bands", {}))
        derived.append(b if b is not None else r.get("band"))
        gaps.append(bool(getattr(derive_band, "last_gap", False)) if b is not None else False)
    quant["band_final"] = derived        # banda del valor convertido; la del LLM sólo como respaldo
    quant["band_in_gap"] = gaps

    records = []
    for (panel, q, rnd), grp in quant.groupby([COL_PANEL, COL_QUESTION, COL_ROUND]):
        tax = get_taxonomy(panel, q) or {}
        vals = grp["parsed_value"].dropna().to_numpy(dtype=float)
        n = len(vals)
        rec = {
            COL_PANEL: panel, COL_QUESTION: q, COL_ROUND: rnd,
            "question_id": f"P{panel}_Q{q}",
            COL_QUESTION_TEXT: grp[COL_QUESTION_TEXT].iloc[0],
            "question_unit": tax.get("unit"), "unit_assumed": tax.get("unit_assumed", False),
            "n_responses": len(grp), "n_numeric": n,
            "n_other_unit": int((grp["unit_status"] == "other").sum()),
            "n_converted": int((grp["unit_status"] == "converted").sum()),
            "n_unit_assumed": int((grp["unit_status"] == "assumed").sum()),
            "unit_mix": json.dumps(dict(Counter(grp["unit_resolved"].fillna("none")))),
            "n_unit_from_raw": int((grp["unit_source"] == "raw_text").sum()),
            "band_counts": json.dumps({b: int((grp["band_final"] == b).sum()) for b in tax.get("bands", {})}),
            "n_band_in_gap": int(grp["band_in_gap"].sum()),
        }
        if n:
            q1, med, q3 = np.percentile(vals, [25, 50, 75])
            mean = vals.mean()
            std = vals.std(ddof=1) if n > 1 else 0.0
            cv = std / mean if (n > 1 and mean != 0) else np.nan
            rel_range = (vals.max() - vals.min()) / med if med else np.nan
            rel_iqr = (q3 - q1) / med if med else np.nan
            rec.update({"mean": mean, "median": med, "std": std, "q1": q1, "q3": q3, "iqr": q3 - q1,
                        "min": vals.min(), "max": vals.max(), "cv": cv,
                        "rel_range": rel_range, "rel_iqr": rel_iqr,
                        "consensus_label": quantitative_label(cv, rel_range, rel_iqr, n)})
        else:
            rec["consensus_label"] = "Insuficiente"
        records.append(rec)
    return pd.DataFrame(records).sort_values([COL_PANEL, COL_QUESTION, COL_ROUND]), quant


# ── trayectorias ──────────────────────────────────────────────────────────────

def categorical_trajectories(df):
    cat = df[df["question_type"].isin(CATEGORICAL) & df["is_valid_response"]]
    records = []
    for (panel, q, panelist), grp in cat.groupby([COL_PANEL, COL_QUESTION, COL_PANELIST]):
        grp = grp.sort_values(COL_ROUND)
        opts = [o if isinstance(o, str) else None for o in grp["selected_option"]]
        rounds = grp[COL_ROUND].tolist()
        real = [o for o in opts if o and o != "Unclassified"]
        records.append({
            COL_PANEL: panel, COL_QUESTION: q, COL_PANELIST: panelist,
            "trajectory": json.dumps(list(zip(rounds, opts)), ensure_ascii=False),
            "initial_option": opts[0], "final_option": opts[-1],
            "changed": len(set(real)) > 1, "n_rounds": len(rounds), "n_classified": len(real),
        })
    return pd.DataFrame(records)


def quantitative_trajectories(quant):
    records = []
    for (panel, q), qgrp in quant.groupby([COL_PANEL, COL_QUESTION]):
        round_median = qgrp.groupby(COL_ROUND)["parsed_value"].median().to_dict()
        for panelist, pgrp in qgrp.groupby(COL_PANELIST):
            pgrp = pgrp.sort_values(COL_ROUND)
            rounds = pgrp[COL_ROUND].tolist()
            vals = [None if pd.isna(v) else float(v) for v in pgrp["parsed_value"]]
            dist = [abs(v - round_median[r]) if (v is not None and not pd.isna(round_median[r])) else None
                    for v, r in zip(vals, rounds)]
            valid = [d for d in dist if d is not None]
            records.append({
                COL_PANEL: panel, COL_QUESTION: q, COL_PANELIST: panelist,
                "trajectory": json.dumps(list(zip(rounds, vals))),
                "initial_value": vals[0], "final_value": vals[-1],
                "dist_to_median": json.dumps(dist),
                "moved_toward_group": (valid[-1] < valid[0]) if len(valid) >= 2 else None,
                "n_rounds": len(rounds),
            })
    return pd.DataFrame(records)


# ── convergencia ──────────────────────────────────────────────────────────────

def convergence_class(delta, final_share):
    """delta = cambio de dispersión (entropía o rel_iqr): negativo = se concentró."""
    if pd.isna(delta):
        return "Insuficiente"
    if delta <= -ENTROPY_DELTA:
        return "Convergió"
    if delta >= ENTROPY_DELTA:
        return "Se dispersó"
    if not pd.isna(final_share) and final_share >= STRONG_AGREEMENT:
        return "Estable en acuerdo"
    return "Estable sin acuerdo"


def convergence_summary(cat_df, quant_df):
    records = []
    for (panel, q), grp in cat_df.groupby([COL_PANEL, COL_QUESTION]):
        grp = grp.sort_values(COL_ROUND)
        ok = grp[grp["consensus_label"] != "Insuficiente"]
        if len(ok) >= 2:
            e0, e1 = ok["norm_entropy"].iloc[0], ok["norm_entropy"].iloc[-1]
            records.append({
                COL_PANEL: panel, COL_QUESTION: q, "question_id": f"P{panel}_Q{q}", "type": "categorical",
                COL_QUESTION_TEXT: grp[COL_QUESTION_TEXT].iloc[0], "metric": "norm_entropy_K",
                "initial": e0, "final": e1, "delta": e1 - e0,
                "initial_modal_share": ok["modal_share"].iloc[0], "final_modal_share": ok["modal_share"].iloc[-1],
                "rounds_used": json.dumps([int(r) for r in ok[COL_ROUND]]),
                "final_label": ok["consensus_label"].iloc[-1],
                "convergence": convergence_class(e1 - e0, ok["modal_share"].iloc[-1]),
            })
        else:
            records.append({COL_PANEL: panel, COL_QUESTION: q, "question_id": f"P{panel}_Q{q}",
                            "type": "categorical", COL_QUESTION_TEXT: grp[COL_QUESTION_TEXT].iloc[0],
                            "metric": "norm_entropy_K", "convergence": "Insuficiente",
                            "final_label": grp["consensus_label"].iloc[-1]})
    for (panel, q), grp in quant_df.groupby([COL_PANEL, COL_QUESTION]):
        grp = grp.sort_values(COL_ROUND)
        ok = grp[grp["consensus_label"] != "Insuficiente"] if "consensus_label" in grp else grp.iloc[0:0]
        if len(ok) >= 2 and "rel_iqr" in ok:
            d0, d1 = ok["rel_iqr"].iloc[0], ok["rel_iqr"].iloc[-1]
            strong = 1.0 if ok["consensus_label"].iloc[-1] == "Consenso fuerte" else 0.0
            records.append({
                COL_PANEL: panel, COL_QUESTION: q, "question_id": f"P{panel}_Q{q}", "type": "quantitative",
                COL_QUESTION_TEXT: grp[COL_QUESTION_TEXT].iloc[0], "metric": "rel_iqr",
                "initial": d0, "final": d1, "delta": d1 - d0,
                "rounds_used": json.dumps([int(r) for r in ok[COL_ROUND]]),
                "final_label": ok["consensus_label"].iloc[-1],
                "convergence": convergence_class(d1 - d0, strong),
            })
        else:
            records.append({COL_PANEL: panel, COL_QUESTION: q, "question_id": f"P{panel}_Q{q}",
                            "type": "quantitative", COL_QUESTION_TEXT: grp[COL_QUESTION_TEXT].iloc[0],
                            "metric": "rel_iqr", "convergence": "Insuficiente",
                            "final_label": grp["consensus_label"].iloc[-1]})
    return pd.DataFrame(records)


def main():
    print("\n═══ CONSENSUS METRICS v2 ═══════════════════════════\n")
    ext_path = os.path.join(OUTPUT_DIR, "02_extracted.csv")
    if not os.path.exists(ext_path):
        raise FileNotFoundError("Run extract_arguments.py first.")
    df = pd.read_csv(ext_path)
    print(f"Loaded {len(df)} rows")

    cat_df = categorical_consensus(df)
    cat_df.to_csv(os.path.join(OUTPUT_DIR, "03_categorical_consensus.csv"), index=False)
    print(f"Categorical consensus: {len(cat_df)} question-rounds "
          f"({int((cat_df['consensus_label'] == 'Insuficiente').sum())} insufficient)")

    quant_df, quant_responses = quantitative_consensus(df)
    quant_df.to_csv(os.path.join(OUTPUT_DIR, "03_quantitative_consensus.csv"), index=False)
    print(f"Quantitative consensus: {len(quant_df)} question-rounds "
          f"({int(quant_df['n_other_unit'].sum())} responses in a non-convertible unit)")

    cat_traj = categorical_trajectories(df)
    cat_traj.to_csv(os.path.join(OUTPUT_DIR, "03_categorical_trajectories.csv"), index=False)
    quant_traj = quantitative_trajectories(quant_responses)
    quant_traj.to_csv(os.path.join(OUTPUT_DIR, "03_quantitative_trajectories.csv"), index=False)
    print(f"Trajectories: {len(cat_traj)} categorical + {len(quant_traj)} quantitative")

    conv = convergence_summary(cat_df, quant_df)
    conv.to_csv(os.path.join(OUTPUT_DIR, "03_convergence.csv"), index=False)

    print("\n── Convergence Summary ─────────────────────────────")
    if len(conv):
        for t, grp in conv.groupby("type"):
            print(f"   {t}: " + ", ".join(f"{k} {v}" for k, v in grp["convergence"].value_counts().items()))
    print("\n── Final-round labels ──────────────────────────────")
    fin = cat_df.loc[cat_df.groupby("question_id")[COL_ROUND].idxmax()]
    print("   categorical: " + ", ".join(f"{k} {v}" for k, v in fin["consensus_label"].value_counts().items()))
    finq = quant_df.loc[quant_df.groupby("question_id")[COL_ROUND].idxmax()]
    print("   quantitative: " + ", ".join(f"{k} {v}" for k, v in finq["consensus_label"].value_counts().items()))
    print("────────────────────────────────────────────────────\n")
    print("Step 4 complete. Run visualize.py next (network.py is on hold until the argument layer v2).\n")


if __name__ == "__main__":
    main()
