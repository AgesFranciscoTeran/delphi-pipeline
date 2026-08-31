"""
Vista por POSTURA (a favor / en contra / condicional) sobre la extracción existente.

No llama al LLM ni reextrae: mapea la opción ya clasificada a su postura con
stance_map.py (la estructura anidada de los documentos de Emily) y recalcula el
consenso a ese nivel. El consenso del paper se mide sobre la postura; los
calificadores se reportan como distribución.

    python stance_view.py                      # lee Resultados/02_extracted.csv
    python stance_view.py ruta/02_extracted.csv

Salida: Resultados/03b_stance_consensus.csv + tabla de ronda final en consola.
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from collections import Counter
from config import *
from stance_map import STANCE_MAP, STANCE_ES, stance_of
from consensus_metrics import (clean_labels, modal_share, normalized_entropy,
                               categorical_label)


def stance_consensus(df):
    cat = df[df["question_type"].isin(("nominal", "binary")) & df["is_valid_response"]].copy()
    cat["question_id"] = "P" + cat[COL_PANEL].astype(str) + "_Q" + cat[COL_QUESTION].astype(str)
    cat = cat[cat["question_id"].isin(STANCE_MAP)]
    mapped = [stance_of(q, o) for q, o in zip(cat["question_id"], cat["selected_option"])]
    cat["stance"] = [STANCE_ES.get(m[0]) for m in mapped]
    cat["qualifier"] = [m[1] for m in mapped]

    records = []
    for (qid, rnd), grp in cat.groupby(["question_id", COL_ROUND]):
        labels = grp["stance"].tolist()
        classified = clean_labels(labels)
        counts = Counter(classified)
        n_total = len(labels)
        n_cls = len(classified)
        pct_unc = (n_total - n_cls) / n_total * 100 if n_total else np.nan
        share = modal_share(labels)
        top = counts.most_common()
        is_tie = len(top) > 1 and top[0][1] == top[1][1]
        modal = None
        if top:
            tied = [o for o, c in top if c == top[0][1]]
            modal = top[0][0] if not is_tie else "Empate: " + " / ".join(sorted(tied))
        quals = Counter(q for q in grp["qualifier"] if q)
        records.append({
            "question_id": qid, COL_ROUND: rnd,
            COL_QUESTION_TEXT: grp[COL_QUESTION_TEXT].iloc[0],
            "n_responses": n_total, "n_classified": n_cls,
            "pct_unclassified": pct_unc,
            "modal_stance": modal, "is_tie": is_tie,
            "stance_share": share,
            "norm_entropy_3": normalized_entropy(labels, 3),
            "consensus_label": categorical_label(share, n_cls, pct_unc, is_tie),
            "stance_counts": json.dumps({s: counts.get(s, 0) for s in STANCE_ES.values()},
                                        ensure_ascii=False),
            "qualifier_counts": json.dumps(dict(quals.most_common()), ensure_ascii=False),
        })
    return pd.DataFrame(records).sort_values(["question_id", COL_ROUND])


def main(path=None):
    path = path or os.path.join(OUTPUT_DIR, "02_extracted.csv")
    df = pd.read_csv(path)
    out = stance_consensus(df)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "03b_stance_consensus.csv")
    out.to_csv(out_path, index=False)
    print(f"Saved: {out_path}  ({len(out)} pregunta-rondas, {out['question_id'].nunique()} preguntas sí/no/depende)\n")

    fin = out.loc[out.groupby("question_id")[COL_ROUND].idxmax()]
    print("Ronda final — consenso por POSTURA (vs. por opción):")
    for _, r in fin.iterrows():
        counts = json.loads(r["stance_counts"])
        dist = "  ".join(f"{k} {v}" for k, v in counts.items() if v)
        print(f"  {r['question_id']:7s} {r['consensus_label']:16s} {str(r['modal_stance']):22s} "
              f"({r['stance_share']*100:3.0f}% de n={int(r['n_classified'])})  | {dist}")
    return out


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
