"""
Build a blind validation labeling sheet for Emily (domain-expert gold standard).

Uses the same responses that compare_models.py already ran (model_comparison.csv),
so no models need to be re-run. The sheet deliberately hides the model outputs so
Emily labels blind.
"""

import pandas as pd
import os
from config import *
from taxonomy import get_taxonomy
from extract_arguments import LETTERS


def options_for(tax):
    """The numbered list Emily chooses from."""
    if tax["type"] in ("nominal", "binary"):
        return list(tax["options"])
    if tax["type"] in ("quantitative", "hybrid"):
        return [f"{name} ({rng})" for name, rng in tax["bands"].items()]
    return []


def main():
    comp_path = os.path.join(OUTPUT_DIR, "model_comparison.csv")
    ind_path = os.path.join(OUTPUT_DIR, "01_individual_clean.csv")
    if not os.path.exists(comp_path):
        raise FileNotFoundError("Run compare_models.py first (needs model_comparison.csv).")

    comp = pd.read_csv(comp_path)
    ind = pd.read_csv(ind_path)
    sample = ind[ind["response_id"].isin(comp["response_id"])].copy()

    rows = []
    for _, r in sample.iterrows():
        tax = get_taxonomy(r[COL_PANEL], r[COL_QUESTION])
        opts = options_for(tax)
        rows.append({
            "response_id": r["response_id"],
            "question_type": tax["type"],
            "question": r[COL_QUESTION_TEXT],
            "response": r[COL_RESPONSE],
            "options": "\n".join(f"{LETTERS[i]}. {o}" for i, o in enumerate(opts)),
            "human_label": "",   # <- Emily writes the option LETTER here (NONE = none fits)
            "notes": "",
        })

    sheet = pd.DataFrame(rows)
    out_path = os.path.join(OUTPUT_DIR, "validation_emily.xlsx")
    sheet.to_excel(out_path, index=False)

    print(f"\n{len(sheet)} responses to label")
    print(sheet["question_type"].value_counts().to_string())
    print(f"\nSaved: {out_path}")
    print("\nInstructions for Emily:")
    print("  - In 'human_label', write the LETTER of the option that best fits the response")
    print("  - Write NONE if none of the options fits")
    print("  - For numeric questions, pick the matching band AND write the number + unit in 'notes'")
    print("  - Label blind — do not look at the model outputs\n")


if __name__ == "__main__":
    main()