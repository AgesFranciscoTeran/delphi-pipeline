import pandas as pd
import json
import os
from config import *
from taxonomy import EMILY_TAXONOMY


def get_unique_questions(ind):
    q = (ind[[COL_PANEL, COL_QUESTION, COL_QUESTION_TEXT]]
         .drop_duplicates().sort_values([COL_PANEL, COL_QUESTION]).reset_index(drop=True))
    q["question_id"] = "P" + q[COL_PANEL].astype(str) + "_Q" + q[COL_QUESTION].astype(str)
    return q


def main():
    print("\n═══ QUESTION TYPES (from Emily's taxonomy) ═══════════\n")

    ind_path = os.path.join(OUTPUT_DIR, "01_individual_clean.csv")
    if not os.path.exists(ind_path):
        raise FileNotFoundError("Run preprocess.py first.")
    ind = pd.read_csv(ind_path)
    questions = get_unique_questions(ind)
    print(f"{len(questions)} unique questions in the data")

    records = []
    missing = []
    for _, row in questions.iterrows():
        qid = row["question_id"]
        tax = EMILY_TAXONOMY.get(qid)
        if tax is None:
            missing.append(qid)
            records.append({
                "question_id": qid, COL_PANEL: row[COL_PANEL], COL_QUESTION: row[COL_QUESTION],
                COL_QUESTION_TEXT: row[COL_QUESTION_TEXT], "type": None, "n_options": 0,
            })
            continue
        n_opts = len(tax.get("options", [])) + len(tax.get("bands", {}))
        records.append({
            "question_id": qid, COL_PANEL: row[COL_PANEL], COL_QUESTION: row[COL_QUESTION],
            COL_QUESTION_TEXT: row[COL_QUESTION_TEXT],
            "type": tax["type"], "n_options": n_opts,
        })

    df = pd.DataFrame(records)
    out_path = os.path.join(OUTPUT_DIR, "02a_question_types.csv")
    df.to_csv(out_path, index=False)

    print("\nType distribution:")
    print(df["type"].value_counts())
    if missing:
        print(f"\n⚠ Questions in data NOT found in taxonomy: {missing}")
    else:
        print("\n✓ All questions matched to Emily's taxonomy")
    print(f"\nSaved: {out_path}\n")
    return df


if __name__ == "__main__":
    main()