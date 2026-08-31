"""
Paso 1 — limpieza y separación individual / síntesis.

Cambios v2:
  - Crea OUTPUT_DIR (la receta de "clean run" del README fallaba sin esto).
  - Una respuesta es válida si tiene texto (no vacía, no marcador tipo "N.A."). El umbral de
    15 caracteres de la v1 descartaba respuestas como "80", "15 hours" o "Yes"; ahora sólo se
    marca `is_short` como información.
"""
import os
import json
import pandas as pd
from config import *


def load_dataset(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)
    print(f"Loaded {len(df)} rows from {path}")
    return df


def validate_structure(df: pd.DataFrame) -> None:
    required = [COL_CATEGORY, COL_PANEL, COL_ROUND, COL_QUESTION,
                COL_QUESTION_TEXT, COL_RESPONSE_TYPE, COL_PANELIST, COL_RESPONSE]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    print(f"Structure valid — {df.shape[0]} rows × {df.shape[1]} cols")


def report_coverage(df: pd.DataFrame) -> dict:
    ind = df[df[COL_RESPONSE_TYPE] == RESPONSE_TYPE_INDIVIDUAL]
    syn = df[df[COL_RESPONSE_TYPE] == RESPONSE_TYPE_SYNTHESIS]
    stats = {
        "total_rows": int(len(df)),
        "individual_responses": int(len(ind)),
        "synthesis_rows": int(len(syn)),
        "panels": sorted(int(p) for p in df[COL_PANEL].unique()),
        "rounds": sorted(int(r) for r in df[COL_ROUND].unique()),
        "categories": df[COL_CATEGORY].unique().tolist(),
        "panelists_per_panel": {
            int(p): sorted(str(x) for x in ind[ind[COL_PANEL] == p][COL_PANELIST].unique())
            for p in df[COL_PANEL].unique()
        },
        "questions_per_panel": {
            int(p): int(ind[ind[COL_PANEL] == p][COL_QUESTION].nunique())
            for p in df[COL_PANEL].unique()
        },
    }
    print("\n── Coverage Report ─────────────────────────────────")
    print(f"   Total rows           : {stats['total_rows']}")
    print(f"   Individual responses : {stats['individual_responses']}")
    print(f"   Synthesis rows       : {stats['synthesis_rows']}")
    print(f"   Panels               : {stats['panels']}")
    print(f"   Rounds               : {stats['rounds']}")
    for p in stats["panels"]:
        print(f"   Panel {p}             : {len(stats['panelists_per_panel'][p])} panelists × "
              f"{stats['questions_per_panel'][p]} questions")
    print("────────────────────────────────────────────────────\n")
    return stats


def clean_responses(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    text = df[COL_RESPONSE].fillna("").astype(str).str.strip()
    df[COL_RESPONSE] = text
    is_empty = text.eq("") | text.str.lower().isin(EMPTY_MARKERS)
    df["is_valid_response"] = ~is_empty
    df["response_length"] = text.str.len()
    df["is_short"] = df["is_valid_response"] & (df["response_length"] < SHORT_RESPONSE_CHARS)
    print(f"Empty / marker responses : {int(is_empty.sum())}  (excluded)")
    print(f"Short but valid (<{SHORT_RESPONSE_CHARS}) : {int(df['is_short'].sum())}  (kept)")
    return df


def build_response_id(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["response_id"] = (
        "Pan" + df[COL_PANEL].astype(str) +
        "_R" + df[COL_ROUND].astype(str) +
        "_Q" + df[COL_QUESTION].astype(str) +
        "_" + df[COL_RESPONSE_TYPE].str[:3].str.upper() +
        "_P" + df[COL_PANELIST].astype(str)
    )
    return df


def split_individual_synthesis(df: pd.DataFrame):
    ind = df[df[COL_RESPONSE_TYPE] == RESPONSE_TYPE_INDIVIDUAL].copy()
    syn = df[df[COL_RESPONSE_TYPE] == RESPONSE_TYPE_SYNTHESIS].copy()
    print(f"Split → {len(ind)} individual | {len(syn)} synthesis")
    return ind, syn


def save_outputs(ind: pd.DataFrame, syn: pd.DataFrame, stats: dict) -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ind_path = os.path.join(OUTPUT_DIR, "01_individual_clean.csv")
    syn_path = os.path.join(OUTPUT_DIR, "01_synthesis_clean.csv")
    stat_path = os.path.join(OUTPUT_DIR, "01_coverage_stats.json")
    ind.to_csv(ind_path, index=False)
    syn.to_csv(syn_path, index=False)
    with open(stat_path, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"Files {ind_path}, {syn_path} and {stat_path} saved")


def main():
    print("\n═══ PREPROCESSING (v2) ══════════════════════\n")
    df = load_dataset(DATA_PATH)
    validate_structure(df)
    stats = report_coverage(df)
    df = clean_responses(df)
    df = build_response_id(df)
    ind, syn = split_individual_synthesis(df)
    save_outputs(ind, syn, stats)
    print("\nComplete")
    return ind, syn


if __name__ == "__main__":
    main()
