"""
Corrida completa SIN LLM (cliente simulado) para verificar que el pipeline v2 corre de punta a
punta. Las etiquetas que produce son heurísticas toscas: sirven para probar la mecánica, no
para leer resultados.

    python pipeline/run_smoke_offline.py
"""
import re
import json
import random
import shutil
import os

random.seed(0)
os.environ["DELPHI_SMOKE"] = "1"

import config
# Ruta anclada a la raíz del repositorio, igual que config.py: el script se puede llamar
# desde cualquier directorio sin dejar un Resultados_smoke/ perdido por ahí.
config.OUTPUT_DIR = os.path.join(config.RAIZ, "Resultados_smoke")
config.FIGURES_DIR = os.path.join(config.OUTPUT_DIR, "figures")
for mod in ("preprocess", "classify_questions", "extract_arguments", "consensus_metrics", "visualize"):
    m = __import__(mod)
    m.OUTPUT_DIR = config.OUTPUT_DIR
    if hasattr(m, "FIGURES_DIR"):
        m.FIGURES_DIR = config.FIGURES_DIR
import visualize
visualize.CAT_CSV = os.path.join(config.OUTPUT_DIR, "03_categorical_consensus.csv")
visualize.QUANT_CSV = os.path.join(config.OUTPUT_DIR, "03_quantitative_consensus.csv")
visualize.CONV_CSV = os.path.join(config.OUTPUT_DIR, "03_convergence.csv")

import extract_arguments as ea


class FakeLLM:
    """Responde al prompt con heurísticas: primer 'No'/'Yes' del texto, primer número, etc."""
    def __init__(self):
        self.chat = self; self.completions = self

    def create(self, **kwargs):
        prompt = kwargs["messages"][1]["content"]
        resp = re.search(r'"""(.*?)"""', prompt, re.S).group(1).strip()
        if "Predefined options" in prompt:
            opts = re.findall(r"\n  ([A-Z])\. (.+)", prompt)
            letter, text = "NONE", ""
            low = resp.lower()
            for L, o in opts:
                if o.lower() in ("no",) and re.match(r"^\s*no\b", low):
                    letter, text = L, o; break
                if o.lower() in ("yes",) and re.match(r"^\s*(yes|s[ií])\b", low):
                    letter, text = L, o; break
            if letter == "NONE" and random.random() < 0.8:
                L, o = random.choice(opts); letter, text = L, o
            out = {"option_letter": letter, "option_text": text,
                   "core_argument": f"The respondent argues: {resp[:60]}", "key_phrases": [resp[:20]]}
        elif "QUANTITATIVE" in prompt:
            m = re.search(r"\d+(?:[.,]\d+)?", resp)
            val = float(m.group(0).replace(",", ".")) if m else None
            unit = "hours/day" if re.search(r"\b(per day|a day|daily|diari)", resp, re.I) else \
                   "hours/week" if re.search(r"\b(per week|a week|weekly|semana)", resp, re.I) else "none"
            bands = re.findall(r"\n  - (\w+):", prompt)
            out = {"value": val, "unit": unit, "value_type": "exact" if val is not None else "none",
                   "value_raw": m.group(0) if m else "", "band": random.choice(bands) if val is not None else None,
                   "core_argument": f"The respondent argues: {resp[:60]}", "key_phrases": [resp[:20]]}
        else:
            out = {"proposed_approach": resp[:50], "core_argument": resp[:60], "key_phrases": []}
        content = "```json\n" + json.dumps(out) + "\n```"
        msg = type("M", (), {"content": content}); choice = type("C", (), {"message": msg})
        return type("R", (), {"choices": [choice]})


if __name__ == "__main__":
    shutil.rmtree(config.OUTPUT_DIR, ignore_errors=True)
    import preprocess, classify_questions, consensus_metrics
    preprocess.main()
    classify_questions.main()
    import pandas as pd
    ind = pd.read_csv(os.path.join(config.OUTPUT_DIR, "01_individual_clean.csv"))
    cache, jobs = ea.run_extraction(ind, client=FakeLLM())
    df = ea.build_extraction_df(ind, cache, jobs)
    df.to_csv(os.path.join(config.OUTPUT_DIR, "02_extracted.csv"), index=False)
    ea.print_summary(df)
    consensus_metrics.main()
    visualize.main()
    print("SMOKE RUN OK")
