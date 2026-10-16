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
  * Resultado por pregunta en cuatro categorías (acuerdo × estabilidad), con los criterios
    fijados a priori el 15-10-2026: ver config.py y docs/criterios_consenso.md.
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
    """Sólo etiquetas reales: fuera NaN, None, '', 'Unclassified' y 'Off-topic'."""
    return [l for l in labels if isinstance(l, str) and l
            and l not in ("Unclassified", OFF_TOPIC_LABEL)]


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


def agreement_label(share, n_classified, pct_unclassified, is_tie=False, min_n=None):
    """Nivel de acuerdo de una distribución (AGREEMENT_LEVELS en config.py).

    Un empate en el primer puesto es «Sin acuerdo»: dos opciones empatadas no son una mayoría.
    """
    min_n = MIN_N_CLASSIFIED if min_n is None else min_n
    if pd.isna(share) or n_classified < min_n or pct_unclassified > MAX_UNCLASSIFIED_PCT:
        return "Insuficiente"
    if is_tie:
        return "Sin acuerdo"
    for nombre, umbral in AGREEMENT_LEVELS:
        if share >= umbral - 1e-9:
            return nombre
    return "Sin acuerdo"


def categorical_consensus(df):
    cat = df[df["question_type"].isin(CATEGORICAL) & df["is_valid_response"]]
    records = []
    for (panel, q, rnd), grp in cat.groupby([COL_PANEL, COL_QUESTION, COL_ROUND]):
        # Las fuera de tema no entran en ningún denominador: no son ni postura ni fallo.
        fuera = grp["selected_option"].eq(OFF_TOPIC_LABEL)
        n_off = int(fuera.sum())
        grp = grp[~fuera]
        if grp.empty:
            continue
        labels = grp["selected_option"].tolist()
        classified = clean_labels(labels)
        counts = Counter(classified)
        tax = get_taxonomy(panel, q) or {}
        options = [o for o in tax.get("options", []) if o != OFF_TOPIC_OPTION]
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
            "n_off_topic": n_off,
            "pct_unclassified": pct_unc,
            "modal_option": modal,
            "is_tie": is_tie,
            "modal_share": share,                          # sobre clasificadas
            "modal_share_all": (max(counts.values()) / n_total) if counts else np.nan,  # sobre todas
            "norm_entropy": normalized_entropy(labels, len(options)),
            "n_distinct_options": len(counts),
            "k_options": len(options),
            "consensus_label": agreement_label(share, n_cls, pct_unc, is_tie),
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
    """'1-2' -> [1,2]; '>6' -> (6,inf); '>=6' -> [6,inf); '<=5' -> (-inf,5]; '50' -> [50,50].
    Texto no numérico -> None.  Devuelve (lo, hi, lo_abierto, hi_abierto).

    Los operadores con igual (>=, <=, ≥, ≤) NO son un adorno: el documento v2 de Emily los usa
    en la mayoría de las bandas ('Intensive: >=6', 'Minimal: <=5'). Antes esta función sólo
    reconocía '>' y '<', así que '>=6' no parseaba, la banda se descartaba entera y los valores
    que le correspondían caían en la banda vecina por el criterio de borde más cercano — sin
    ningún error visible. Cualquier cambio aquí necesita su test.
    """
    import re as _re
    rng = str(rng).strip().replace("≥", ">=").replace("≤", "<=")
    m = _re.match(r"^(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)", rng)
    if m:
        return float(m.group(1)), float(m.group(2)), False, False
    # «>5 and <=8»: intervalo con los dos bordes explícitos (bandas contiguas, 15-10-2026)
    m = _re.match(r"^(>=?)\s*(\d+\.?\d*)\s*(?:and|y|&|,)\s*(<=?)\s*(\d+\.?\d*)$", rng)
    if m:
        return float(m.group(2)), float(m.group(4)), m.group(1) == ">", m.group(3) == "<"
    m = _re.match(r"^(>=?)\s*(\d+\.?\d*)", rng)
    if m:
        return float(m.group(2)), float("inf"), m.group(1) == ">", False
    m = _re.match(r"^(<=?)\s*(\d+\.?\d*)", rng)
    if m:
        return float("-inf"), float(m.group(2)), False, m.group(1) == "<"
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


def separar_medida(response, value, secondary, keywords):
    """(valor, secundario) aplicando la regla de la cantidad medida (P1_Q7).

    Aunque el prompt lo pide, el modelo pone a veces un total («20 hours») como horas de ABP.
    Regla fija sobre el texto crudo, igual que unit_from_raw: si la respuesta no nombra la
    cantidad medida, el número no es esa cantidad y pasa a ser el secundario.
    """
    if not keywords or value is None or (isinstance(value, float) and pd.isna(value)):
        return value, secondary
    texto = str(response or "")
    if any(re.search(r"\b%s\b" % re.escape(k), texto, re.I) for k in keywords):
        return value, secondary
    sec = secondary if secondary is not None and not (isinstance(secondary, float)
                                                      and pd.isna(secondary)) else value
    return np.nan, sec


def _modal(cuenta):
    """(etiqueta modal, proporción, empate) de un Counter; (None, nan, False) si está vacío."""
    n = sum(cuenta.values())
    if not n:
        return None, np.nan, False
    top = cuenta.most_common()
    tie = len(top) > 1 and top[0][1] == top[1][1]
    modal = top[0][0] if not tie else "Empate: " + " / ".join(
        sorted(o for o, c in top if c == top[0][1]))
    return modal, top[0][1] / n, tie


def _distribucion_bandas(grp, tax):
    """(Counter de bandas, n con banda, % sin banda) de un grupo de respuestas numéricas."""
    bandas = list(tax.get("bands", {}))
    b = grp["band_final"].where(grp["band_final"].isin(bandas)).dropna()
    total = len(grp)
    return Counter(b), len(b), ((total - len(b)) / total * 100 if total else np.nan)


def quantitative_consensus(df):
    quant = df[df["question_type"].isin(NUMERIC) & df["is_valid_response"]].copy()
    for col in ("value_unit", "band"):          # tolerar CSVs de la v1
        if col not in quant.columns:
            quant[col] = None
    if "value_secondary" not in quant.columns:
        quant["value_secondary"] = np.nan
    for i, r in quant.iterrows():
        kw = (get_taxonomy(r[COL_PANEL], r[COL_QUESTION]) or {}).get("measure_keywords")
        if kw:
            v, s2 = separar_medida(r.get(COL_RESPONSE), r["numeric_value"], r["value_secondary"], kw)
            if pd.isna(v) and not pd.isna(r["numeric_value"]):
                quant.at[i, "band"] = None      # la banda del modelo era la del total
            quant.at[i, "numeric_value"], quant.at[i, "value_secondary"] = v, s2
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
                        "rel_range": rel_range, "rel_iqr": rel_iqr})
        # El consenso numérico se mide igual que el categórico, sobre la BANDA (criterio del
        # 15-10-2026); mediana y RIC quedan como descripción.
        cuenta, n_b, pct_b = _distribucion_bandas(grp, tax)
        modal, share_b, tie_b = _modal(cuenta)
        rec.update({"n_banded": n_b, "modal_band": modal, "band_share": share_b, "band_tie": tie_b,
                    "pct_unclassified": pct_b,
                    "consensus_label": agreement_label(share_b, n_b, pct_b, tie_b,
                                                       min_n=MIN_N_NUMERIC)})
        if "value_secondary" in grp:
            sec = pd.to_numeric(grp["value_secondary"], errors="coerce").dropna()
            if len(sec):
                rec.update({"secondary_n": len(sec), "secondary_median": sec.median(),
                            "secondary_q1": sec.quantile(.25), "secondary_q3": sec.quantile(.75)})
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
        real = clean_labels(opts)
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


# ── resultado por pregunta: acuerdo × estabilidad ─────────────────────────────

RESULTADOS = ("Consenso", "Consenso no consolidado", "Disenso estable", "Sin estabilizar",
              "Insuficiente")


def cambio_neto(antes, despues):
    """Cambio neto entre dos distribuciones (Scheibe, Skutsch y Schofer, 1975).

    La mitad de la suma de las diferencias absolutas entre proporciones: la fracción del panel
    que, en neto, cambió de opción. Proporciones y no conteos, porque el número de respuestas
    clasificadas puede cambiar de una ronda a otra.
    """
    n1, n2 = sum(antes.values()), sum(despues.values())
    if not n1 or not n2:
        return np.nan
    return 0.5 * sum(abs(antes.get(k, 0) / n1 - despues.get(k, 0) / n2)
                     for k in set(antes) | set(despues))


def resultado(share, tie, cambio, umbral=None):
    """Una de cuatro categorías (Dajani et al., 1979; ACCORD, 2024), o «Insuficiente»."""
    umbral = CONSENSUS_THRESHOLD if umbral is None else umbral
    if pd.isna(share) or pd.isna(cambio):
        return "Insuficiente"
    acuerdo = (not tie) and share >= umbral - 1e-9
    estable = cambio <= STABILITY_MAX_CHANGE + 1e-9
    return {(True, True): "Consenso", (True, False): "Consenso no consolidado",
            (False, True): "Disenso estable", (False, False): "Sin estabilizar"}[(acuerdo, estable)]


def _etiquetas_base(qid, opciones):
    """Sobre qué se mide el consenso (criterio 1.2): la postura en las preguntas de sí / no,
    la opción en las demás. None = sin clasificar."""
    from stance_map import STANCE_MAP, STANCE_ES, stance_of
    if qid in STANCE_MAP:
        return "postura", [STANCE_ES.get(stance_of(qid, o)[0]) if isinstance(o, str) else None
                           for o in opciones]
    return "opción", [o if isinstance(o, str) and o not in ("Unclassified", OFF_TOPIC_LABEL)
                      else None for o in opciones]


def _por_ronda(grp, min_n):
    rondas = {}
    for rnd, g in grp.groupby(COL_ROUND):
        cuenta = Counter(x for x in g["_e"] if isinstance(x, str) and x)
        n_cls, total = sum(cuenta.values()), len(g)
        pct = (total - n_cls) / total * 100 if total else np.nan
        modal, share, tie = _modal(cuenta)
        rondas[int(rnd)] = {"cuenta": cuenta, "n": n_cls, "total": total, "modal": modal,
                            "share": share, "tie": tie,
                            "label": agreement_label(share, n_cls, pct, tie, min_n=min_n)}
    return rondas


def _registro(panel, q, tipo, base, texto, rondas):
    orden = sorted(rondas)
    fin = rondas[orden[-1]]
    prev = rondas[orden[-2]] if len(orden) > 1 else None
    # Hacen falta dos rondas con datos suficientes: sin la anterior no hay estabilidad que medir.
    ok = fin["label"] != "Insuficiente" and prev is not None and prev["label"] != "Insuficiente"
    cambio = cambio_neto(prev["cuenta"], fin["cuenta"]) if ok else np.nan
    share = fin["share"] if ok else np.nan
    rec = {COL_PANEL: panel, COL_QUESTION: q, "question_id": f"P{panel}_Q{q}", "type": tipo,
           "base": base, COL_QUESTION_TEXT: texto, "rounds": json.dumps(orden),
           "shares": json.dumps({str(r): (None if pd.isna(rondas[r]["share"])
                                          else round(float(rondas[r]["share"]), 4)) for r in orden}),
           "modal_final": fin["modal"], "share_final": fin["share"], "n_final": fin["n"],
           "total_final": fin["total"], "agreement_final": fin["label"], "change_last": cambio,
           "stable": (bool(cambio <= STABILITY_MAX_CHANGE + 1e-9) if not pd.isna(cambio) else None),
           "resultado": resultado(share, fin["tie"], cambio)}
    for u in SENSITIVITY_THRESHOLDS:
        rec[f"resultado_{int(round(u * 100))}"] = resultado(share, fin["tie"], cambio, u)
    return rec


def resultados(df, quant):
    """Una fila por pregunta con el resultado de la ronda final (acuerdo × estabilidad)."""
    records = []
    cat = df[df["question_type"].isin(CATEGORICAL) & df["is_valid_response"]]
    cat = cat[cat["selected_option"] != OFF_TOPIC_LABEL]      # fuera de tema: fuera del denominador
    for (panel, q), grp in cat.groupby([COL_PANEL, COL_QUESTION]):
        base, et = _etiquetas_base(f"P{panel}_Q{q}", grp["selected_option"].tolist())
        rondas = _por_ronda(grp.assign(_e=et), MIN_N_CLASSIFIED)
        records.append(_registro(panel, q, "categorical", base,
                                 grp[COL_QUESTION_TEXT].iloc[0], rondas))
    for (panel, q), grp in quant.groupby([COL_PANEL, COL_QUESTION]):
        bandas = list((get_taxonomy(panel, q) or {}).get("bands", {}))
        et = [b if b in bandas else None for b in grp["band_final"]]
        rondas = _por_ronda(grp.assign(_e=et), MIN_N_NUMERIC)
        records.append(_registro(panel, q, "quantitative", "banda",
                                 grp[COL_QUESTION_TEXT].iloc[0], rondas))
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

    conv = resultados(df, quant_responses)
    conv.to_csv(os.path.join(OUTPUT_DIR, "03_convergence.csv"), index=False)

    print("\n── Resultado por pregunta (acuerdo × estabilidad) ──")
    if len(conv):
        for t, grp in conv.groupby("type"):
            print(f"   {t}: " + ", ".join(f"{k} {v}" for k, v in grp["resultado"].value_counts().items()))
    print("\n── Final-round labels ──────────────────────────────")
    fin = cat_df.loc[cat_df.groupby("question_id")[COL_ROUND].idxmax()]
    print("   categorical: " + ", ".join(f"{k} {v}" for k, v in fin["consensus_label"].value_counts().items()))
    finq = quant_df.loc[quant_df.groupby("question_id")[COL_ROUND].idxmax()]
    print("   quantitative: " + ", ".join(f"{k} {v}" for k, v in finq["consensus_label"].value_counts().items()))
    print("────────────────────────────────────────────────────\n")
    print("Step 4 complete. Run visualize.py next (network.py is on hold until the argument layer v2).\n")


if __name__ == "__main__":
    main()
