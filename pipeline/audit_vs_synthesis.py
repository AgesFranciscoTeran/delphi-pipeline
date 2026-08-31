"""
Auditoría rápida: distribución que produce el pipeline por pregunta-ronda, al lado de la
síntesis que escribió el facilitador para esa misma pregunta-ronda, y de las respuestas crudas.

No es validación formal (eso es la Fase 3 con Emily y un segundo codificador); es el chequeo de
plausibilidad que en el diagnóstico del 28-08-2026 destapó las inversiones. Genera un Excel con
una columna vacía "veredicto_humano" para anotar en minutos si la distribución es creíble.

    python audit_vs_synthesis.py            # -> Resultados/audit_vs_synthesis.xlsx
"""
import os
import json
import pandas as pd
from config import *


def main():
    ext = pd.read_csv(os.path.join(OUTPUT_DIR, "02_extracted.csv"))
    syn = pd.read_csv(os.path.join(OUTPUT_DIR, "01_synthesis_clean.csv"))
    cat = pd.read_csv(os.path.join(OUTPUT_DIR, "03_categorical_consensus.csv"))
    quant = pd.read_csv(os.path.join(OUTPUT_DIR, "03_quantitative_consensus.csv"))

    syn_map = {(int(r[COL_PANEL]), int(r[COL_QUESTION]), int(r[COL_ROUND])): str(r[COL_RESPONSE])
               for _, r in syn.iterrows()}

    def raw_block(panel, q, rnd):
        sub = ext[(ext[COL_PANEL] == panel) & (ext[COL_QUESTION] == q) & (ext[COL_ROUND] == rnd)
                  & ext["is_valid_response"]].sort_values(COL_PANELIST)
        lines = []
        for _, r in sub.iterrows():
            tag = r["selected_option"] if isinstance(r["selected_option"], str) else \
                  (f"{r['numeric_value']:g} {r['value_unit']}" if pd.notna(r["numeric_value"]) else "—")
            lines.append(f"P{r[COL_PANELIST]} [{tag}] {str(r[COL_RESPONSE])[:220]}")
        return "\n".join(lines)

    rows = []
    for _, r in cat.iterrows():
        key = (int(r[COL_PANEL]), int(r[COL_QUESTION]), int(r[COL_ROUND]))
        counts = {k: v for k, v in json.loads(r["option_counts"]).items() if v}
        rows.append({
            "question_id": r["question_id"], "round": key[2], "type": "categorical",
            "question": r[COL_QUESTION_TEXT],
            "pipeline": f"{r['consensus_label']}: {r['modal_option']}  |  n={int(r['n_classified'])}/{int(r['n_responses'])}  |  "
                        + ", ".join(f"{k}: {v}" for k, v in sorted(counts.items(), key=lambda kv: -kv[1])),
            "synthesis_facilitator": syn_map.get(key, ""),
            "raw_responses_with_labels": raw_block(*key),
            "veredicto_humano": "", "nota": "",
        })
    for _, r in quant.iterrows():
        key = (int(r[COL_PANEL]), int(r[COL_QUESTION]), int(r[COL_ROUND]))
        med = f"mediana {r['median']:.3g} (IQR {r['q1']:.3g}–{r['q3']:.3g}, mín {r['min']:.3g}, máx {r['max']:.3g})" \
              if pd.notna(r.get("median")) else "sin valores"
        rows.append({
            "question_id": r["question_id"], "round": key[2], "type": "quantitative",
            "question": r[COL_QUESTION_TEXT],
            "pipeline": f"{r['consensus_label']} | {med} | n={int(r['n_numeric'])}/{int(r['n_responses'])} "
                        f"| unidad {r['question_unit']} | unidades reportadas {r['unit_mix']}",
            "synthesis_facilitator": syn_map.get(key, ""),
            "raw_responses_with_labels": raw_block(*key),
            "veredicto_humano": "", "nota": "",
        })

    out = pd.DataFrame(rows).sort_values(["type", "question_id", "round"])
    path = os.path.join(OUTPUT_DIR, "audit_vs_synthesis.xlsx")
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        out.to_excel(xw, index=False, sheet_name="audit")
        ws = xw.sheets["audit"]
        for col, width in zip("ABCDEFGH", [10, 6, 12, 45, 60, 70, 90, 16]):
            ws.column_dimensions[col].width = width
        from openpyxl.styles import Alignment
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical="top")
    print(f"Saved: {path}  ({len(out)} question-rounds)")

    # resumen de ronda final en consola
    fin = cat.loc[cat.groupby("question_id")[COL_ROUND].idxmax()]
    print("\nRonda final — categóricas:")
    for _, r in fin.iterrows():
        print(f"  {r['question_id']:7s} {r['consensus_label']:22s} {str(r['modal_option'])[:40]:40s} "
              f"n={int(r['n_classified'])}/{int(r['n_responses'])}")


if __name__ == "__main__":
    main()
