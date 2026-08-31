"""
Paso 3 — extracción supervisada con LLM (v2).

Cambios respecto a la v1 (todos motivados por el diagnóstico del 28-08-2026):
  * Opciones identificadas por LETRA (A, B, C…) y no por índice numérico. Gemma devolvía
    índices base 0 la mayoría de las veces y el código los leía base 1: la primera opción se
    volvía "Unclassified" y las demás se corrían una posición. Con letras no hay convención
    que confundir; además se pide el texto de la opción como comprobación cruzada.
  * "NONE" explícito para "ninguna opción encaja" (antes era el 0, ambiguo).
  * temperature=0 y seed fijos.
  * Extracción JSON robusta (antes sólo en compare_models.py) y, opcionalmente, JSON guiado
    por esquema (vLLM `guided_json`) que hace imposible un formato inválido.
  * Cuantitativas: se extrae la UNIDAD tal como la dice el panelista, sin convertir. La
    conversión (sólo día<->semana) se hace en consensus_metrics.py de forma explícita.
  * Caché con clave (response_id, modelo, hash del prompt): cambiar de modelo, de prompt o de
    taxonomía invalida la entrada automáticamente. El caché v1 mezclaba modelos.
  * Concurrencia (ThreadPool) — el dataset real son 22 000 respuestas.
  * Manifiesto por corrida (modelo, temperatura, hash de taxonomía y prompts, versiones).
  * Se eliminan los campos `certainty` y `references_synthesis`: el diagnóstico mostró que el
    modelo los rellena sin evidencia (52 % "yes" en ronda 1, donde no había síntesis).
"""
import os
import re
import json
import time
import hashlib
import threading
import platform
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from config import *
from taxonomy import get_taxonomy, taxonomy_hash

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
NONE_TOKEN = "NONE"

SYSTEM_PROMPT = (
    "You are an expert qualitative researcher analyzing responses from a Delphi consensus "
    "study. Be precise, neutral, and base your analysis strictly on what the text says — do "
    "not infer beyond the text. Responses may be in English or Spanish."
)


# ── prompts ──────────────────────────────────────────────────────────────────

def _prev_round_note(round_num):
    return (f"This is Round {round_num}; the panelist may have seen a synthesis of "
            f"Round {round_num - 1}.") if round_num > 1 else ""


def build_categorical_prompt(question_text, response_text, round_num, options):
    """Nominal / binary: elegir UNA opción por letra (o NONE)."""
    opts = "\n".join(f"  {LETTERS[i]}. {opt}" for i, opt in enumerate(options))
    last = LETTERS[len(options) - 1]
    return f"""Classify this Delphi response into ONE of the predefined options.

Question: {question_text}
Round: {round_num}
{_prev_round_note(round_num)}

Response:
\"\"\"{response_text}\"\"\"

Predefined options (each has a letter):
{opts}

Choose the SINGLE option whose meaning best matches the panelist's position.
If the panelist's position is not covered by any option, answer "{NONE_TOKEN}".
Do not choose an option just because it shares a word with the response.

Respond ONLY with valid JSON (no preamble, no markdown):
{{
  "option_letter": "<one letter from A to {last}, or {NONE_TOKEN}>",
  "option_text": "<the exact text of the chosen option, or empty string if {NONE_TOKEN}>",
  "core_argument": "<1-2 sentence paraphrase of the panelist's reasoning, in English>",
  "key_phrases": ["<up to 3 short phrases quoted from the response>"]
}}
"""


def build_quantitative_prompt(question_text, response_text, round_num, bands, unit):
    band_str = "\n".join(f"  - {name}: {rng}" for name, rng in bands.items())
    band_names = " | ".join(bands.keys())
    units = " | ".join(UNIT_VOCAB)
    return f"""Analyze this response to a QUANTITATIVE Delphi question (it asks for a number).

Question: {question_text}
The question asks for a value in this unit: {unit}
Round: {round_num}
{_prev_round_note(round_num)}

Response:
\"\"\"{response_text}\"\"\"

Reference bands (in the question's unit):
{band_str}

Respond ONLY with valid JSON (no preamble, no markdown):
{{
  "value": <the main number the panelist proposes, as a number; null if none>,
  "unit": "<the unit the panelist actually uses, one of: {units}>",
  "value_type": "<exact|range|minimum|maximum|none>",
  "value_raw": "<the value exactly as written in the response>",
  "band": "<one of: {band_names}; or null if no number is given>",
  "core_argument": "<1-2 sentence paraphrase of the panelist's reasoning, in English>",
  "key_phrases": ["<up to 3 short phrases quoted from the response>"]
}}

Rules:
- Report the number EXACTLY as the panelist states it. Do NOT convert between units
  (e.g. do not turn "5 hours per day" into hours per week). Put the panelist's own unit in "unit".
- "unit" must be the unit WRITTEN in the response. If the response gives a number without
  stating a unit or period, use "none" — do NOT infer the unit from the question.
- If the panelist states the value in more than one unit, report the one matching "{unit}".
- If a range is given, put the midpoint in "value" and set value_type to "range".
- "band" must be judged in the question's unit; if the panelist's unit differs, set band to null.
- core_argument must be YOUR paraphrase, not a quote.
"""


def build_open_prompt(question_text, response_text, round_num):
    """Tipo 'open' (todavía no existe en la taxonomía; P1_Q3 es candidata en la Fase 1)."""
    return f"""Analyze this response to an OPEN Delphi question (asks for a method/approach).

Question: {question_text}
Round: {round_num}
{_prev_round_note(round_num)}

Response:
\"\"\"{response_text}\"\"\"

Respond ONLY with valid JSON (no preamble, no markdown):
{{
  "proposed_approach": "<1-2 sentence paraphrase of the method they propose>",
  "core_argument": "<1-2 sentence paraphrase of why>",
  "key_phrases": ["<up to 3 short phrases quoted from the response>"]
}}
"""


def build_prompt_for_type(tax, question_text, response_text, round_num):
    qtype = tax["type"]
    if qtype in ("quantitative", "hybrid"):
        return build_quantitative_prompt(question_text, response_text, round_num,
                                         tax["bands"], tax.get("unit", "as asked"))
    if qtype in ("nominal", "binary"):
        return build_categorical_prompt(question_text, response_text, round_num, tax["options"])
    return build_open_prompt(question_text, response_text, round_num)


def guided_schema_for(tax):
    """Esquema JSON para decodificación guiada (vLLM `guided_json`)."""
    qtype = tax["type"]
    common = {
        "core_argument": {"type": "string"},
        "key_phrases": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
    }
    if qtype in ("nominal", "binary"):
        letters = [LETTERS[i] for i in range(len(tax["options"]))] + [NONE_TOKEN]
        return {"type": "object",
                "properties": {"option_letter": {"type": "string", "enum": letters},
                               "option_text": {"type": "string"}, **common},
                "required": ["option_letter", "option_text", "core_argument", "key_phrases"]}
    if qtype in ("quantitative", "hybrid"):
        return {"type": "object",
                "properties": {"value": {"type": ["number", "null"]},
                               "unit": {"type": "string", "enum": UNIT_VOCAB},
                               "value_type": {"type": "string",
                                              "enum": ["exact", "range", "minimum", "maximum", "none"]},
                               "value_raw": {"type": "string"},
                               "band": {"type": ["string", "null"],
                                        "enum": list(tax["bands"].keys()) + [None]},
                               **common},
                "required": ["value", "unit", "value_type", "value_raw", "band",
                             "core_argument", "key_phrases"]}
    return {"type": "object",
            "properties": {"proposed_approach": {"type": "string"}, **common},
            "required": ["proposed_approach", "core_argument", "key_phrases"]}


# ── parsing / normalización ─────────────────────────────────────────────────

def extract_json(raw):
    """JSON robusto: tolera fences ```json, preámbulos de razonamiento y texto posterior."""
    raw = (raw or "").strip()
    if "```" in raw:
        for part in raw.split("```"):
            part = part.strip()
            if part.lower().startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                raw = part
                break
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no JSON object found")
    return json.loads(raw[start:end + 1])


def _norm(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def resolve_letter(letter, option_text, options):
    """
    Devuelve (selected_option, status, letter_text_mismatch).
      status: 'classified' | 'none_fits' | 'invalid_output'
    La letra manda; el texto sirve de comprobación. Si la letra es inválida se intenta
    el texto (coincidencia exacta normalizada).
    """
    letter = str(letter or "").strip().upper()
    text = str(option_text or "").strip()
    if letter == NONE_TOKEN or letter == "":
        if letter == "" and text:
            match = _match_text(text, options)
            if match is not None:
                return match, "classified", False
        return "Unclassified", "none_fits" if letter == NONE_TOKEN else "invalid_output", False
    letter = letter[0]
    idx = LETTERS.find(letter)
    if 0 <= idx < len(options):
        chosen = options[idx]
        mismatch = bool(text) and _norm(text) != _norm(chosen)
        return chosen, "classified", mismatch
    match = _match_text(text, options)
    if match is not None:
        return match, "classified", False
    return "Unclassified", "invalid_output", False


def _match_text(text, options):
    t = _norm(text)
    for opt in options:
        if _norm(opt) == t:
            return opt
    return None


def canonical_band(band, bands):
    if band is None or (isinstance(band, float) and pd.isna(band)):
        return None
    b = str(band).strip().lower()
    for name in bands:
        if name.lower() == b:
            return name
    return None


def canonical_unit(unit):
    u = str(unit or "").strip().lower().replace(" per ", "/").replace(" ", "")
    aliases = {"hoursperday": "hours/day", "h/day": "hours/day", "hours/daily": "hours/day",
               "hoursperweek": "hours/week", "h/week": "hours/week", "hours/wk": "hours/week",
               "semester": "semesters", "year": "years", "student": "students", "%": "percent",
               "null": "none", "": "none"}
    u = aliases.get(u, u)
    return u if u in UNIT_VOCAB else "other"


def _to_number(x):
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    if isinstance(x, (int, float)):
        return float(x)
    m = re.search(r"-?\d+(?:[.,]\d+)?", str(x))
    return float(m.group(0).replace(",", ".")) if m else None


def prompt_hash(prompt):
    return hashlib.sha1((PROMPT_VERSION + "\n" + prompt).encode("utf-8")).hexdigest()[:12]


def cache_key(rid, model, phash):
    return f"{rid}|{model}|{phash}"


# ── llamada al modelo ────────────────────────────────────────────────────────

def call_llm(client, prompt, tax, model=None, max_tokens=None):
    kwargs = dict(
        model=model or MODEL_LLM,
        max_tokens=max_tokens or MAX_TOKENS,
        temperature=TEMPERATURE,
        seed=SEED,
        timeout=REQUEST_TIMEOUT,
        messages=[{"role": "system", "content": SYSTEM_PROMPT},
                  {"role": "user", "content": prompt}],
    )
    if USE_GUIDED_JSON:
        kwargs["extra_body"] = {"guided_json": guided_schema_for(tax)}
    resp = client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content


def postprocess(parsed, tax):
    """Normaliza la salida del modelo al esquema de columnas del pipeline."""
    qtype = tax["type"]
    out = {"core_argument": parsed.get("core_argument"),
           "key_phrases": parsed.get("key_phrases") or []}
    if qtype in ("nominal", "binary"):
        sel, status, mismatch = resolve_letter(parsed.get("option_letter"),
                                               parsed.get("option_text"), tax["options"])
        out.update(selected_option=sel, option_letter=str(parsed.get("option_letter") or ""),
                   option_text=str(parsed.get("option_text") or ""),
                   classification_status=status, letter_text_mismatch=mismatch)
    elif qtype in ("quantitative", "hybrid"):
        value = _to_number(parsed.get("value"))
        raw = str(parsed.get("value_raw") or "")
        # El modelo etiqueta mal la unidad en parte de los casos (manda a "other" cosas como
        # "8 hours a day"). El periodo está escrito en el texto: se resuelve con una regla fija.
        from consensus_metrics import unit_from_raw
        unit, unit_src = unit_from_raw(raw, canonical_unit(parsed.get("unit")))
        band = canonical_band(parsed.get("band"), tax["bands"])
        out.update(unit_source=unit_src)
        out.update(numeric_value=value, value_unit=unit,
                   value_type=str(parsed.get("value_type") or "none"),
                   value_raw=str(parsed.get("value_raw") or ""),
                   band=band,
                   classification_status="classified" if value is not None else "none_fits")
        if qtype == "hybrid":
            out["band_policy"] = tax.get("band_policies", {}).get(band)
    else:
        out.update(proposed_approach=parsed.get("proposed_approach"),
                   classification_status="classified")
    return out


def extract_single(client, response_id, response_text, question_text, round_num, tax,
                   model=None, retries=None, max_tokens=None):
    prompt = build_prompt_for_type(tax, question_text, response_text, round_num)
    phash = prompt_hash(prompt)
    last_error = None
    for attempt in range(retries or RETRIES):
        try:
            raw = call_llm(client, prompt, tax, model=model, max_tokens=max_tokens)
            parsed = extract_json(raw)
            out = postprocess(parsed, tax)
            out.update(response_id=response_id, question_type=tax["type"],
                       extraction_model=model or MODEL_LLM, prompt_hash=phash,
                       prompt_version=PROMPT_VERSION, raw_output=str(raw)[:2000],
                       extraction_status="ok")
            return out
        except (json.JSONDecodeError, ValueError) as e:
            last_error = f"json: {e}"
            time.sleep(0.5)
        except Exception as e:
            last_error = f"{type(e).__name__}: {str(e)[:120]}"
            time.sleep(2)
    return {"response_id": response_id, "question_type": tax["type"],
            "extraction_model": model or MODEL_LLM, "prompt_hash": phash,
            "prompt_version": PROMPT_VERSION, "extraction_status": "failed",
            "error": last_error}


# ── caché, manifiesto, corrida ───────────────────────────────────────────────

def load_cache(cache_path):
    if os.path.exists(cache_path) and CACHE_RESULTS:
        with open(cache_path) as f:
            cache = json.load(f)
        print(f"Loaded cache: {len(cache)} extractions")
        return cache
    return {}


def save_cache(cache, cache_path):
    tmp = cache_path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(cache, f, indent=1, ensure_ascii=False)
    os.replace(tmp, cache_path)


def write_manifest(n_total, n_processed, n_failed, elapsed_s):
    manifest_path = os.path.join(OUTPUT_DIR, "run_manifest.json")
    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "step": "extract_arguments",
        "model": MODEL_LLM, "url": URL_LLM,
        "temperature": TEMPERATURE, "seed": SEED, "max_tokens": MAX_TOKENS,
        "guided_json": USE_GUIDED_JSON, "prompt_version": PROMPT_VERSION,
        "taxonomy_hash": taxonomy_hash(),
        "n_valid_responses": int(n_total), "n_processed_now": int(n_processed),
        "n_failed": int(n_failed), "elapsed_s": round(elapsed_s, 1),
        "python": platform.python_version(),
        "pandas": pd.__version__,
    }
    try:
        import openai
        entry["openai_sdk"] = openai.__version__
    except Exception:
        pass
    runs = []
    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            runs = json.load(f)
    runs.append(entry)
    with open(manifest_path, "w") as f:
        json.dump(runs, f, indent=2)
    print(f"Manifest updated: {manifest_path}")


def plan_jobs(ind):
    """Para cada respuesta válida: prompt, hash y clave de caché."""
    jobs = []
    for _, row in ind[ind["is_valid_response"]].iterrows():
        tax = get_taxonomy(row[COL_PANEL], row[COL_QUESTION])
        if tax is None:
            continue
        prompt = build_prompt_for_type(tax, row[COL_QUESTION_TEXT], row[COL_RESPONSE],
                                       int(row[COL_ROUND]))
        phash = prompt_hash(prompt)
        jobs.append({"rid": row["response_id"], "key": cache_key(row["response_id"], MODEL_LLM, phash),
                     "text": row[COL_RESPONSE], "question_text": row[COL_QUESTION_TEXT],
                     "round": int(row[COL_ROUND]), "tax": tax})
    return jobs


def run_extraction(ind, client=None):
    from openai import OpenAI
    client = client or OpenAI(base_url=URL_LLM, api_key=API_KEY)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    cache_path = os.path.join(OUTPUT_DIR, "02_extraction_cache.json")
    cache = load_cache(cache_path)

    jobs = plan_jobs(ind)
    todo = [j for j in jobs if j["key"] not in cache or cache[j["key"]].get("extraction_status") != "ok"]
    print(f"\n   Valid responses: {len(jobs)} | cached: {len(jobs) - len(todo)} | to process: {len(todo)}\n")

    lock = threading.Lock()
    done = 0
    t0 = time.time()

    def work(job):
        return job["key"], extract_single(client, job["rid"], job["text"], job["question_text"],
                                          job["round"], job["tax"])

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = [pool.submit(work, j) for j in todo]
        for fut in as_completed(futures):
            key, res = fut.result()
            with lock:
                cache[key] = res
                done += 1
                tag = (res.get("selected_option") or res.get("band") or res.get("numeric_value")
                       or res.get("extraction_status"))
                print(f"  [{done}/{len(todo)}] {res['response_id']} ({res['question_type']}) -> {tag}", flush=True)
                if done % 25 == 0:
                    save_cache(cache, cache_path)
    save_cache(cache, cache_path)

    failed = [k for j in jobs for k in [j["key"]] if cache.get(k, {}).get("extraction_status") != "ok"]
    if failed:
        pd.DataFrame({"cache_key": failed,
                      "error": [cache.get(k, {}).get("error") for k in failed]}
                     ).to_csv(os.path.join(OUTPUT_DIR, "02_extraction_errors.csv"), index=False)
    print(f"\nDone: {len(jobs) - len(failed)} ok, {len(failed)} failed  ({time.time() - t0:.0f}s)")
    write_manifest(len(jobs), len(todo), len(failed), time.time() - t0)
    return cache, jobs


EXTRACTION_COLUMNS = [
    "question_type", "selected_option", "option_letter", "option_text", "classification_status",
    "letter_text_mismatch", "numeric_value", "value_unit", "unit_source", "value_type", "value_raw", "band",
    "band_policy", "proposed_approach", "core_argument", "key_phrases", "extraction_model",
    "prompt_hash", "prompt_version", "extraction_status",
]


def build_extraction_df(ind, cache, jobs):
    key_by_rid = {j["rid"]: j["key"] for j in jobs}
    records = []
    for _, row in ind.iterrows():
        rid = row["response_id"]
        ext = cache.get(key_by_rid.get(rid, ""), {}) if row["is_valid_response"] else {}
        rec = {
            "response_id": rid,
            COL_PANEL: row[COL_PANEL], COL_ROUND: row[COL_ROUND],
            COL_QUESTION: row[COL_QUESTION], COL_QUESTION_TEXT: row[COL_QUESTION_TEXT],
            COL_CATEGORY: row[COL_CATEGORY], COL_PANELIST: row[COL_PANELIST],
            COL_RESPONSE: row[COL_RESPONSE],
            "is_valid_response": bool(row["is_valid_response"]),
            "is_short": bool(row.get("is_short", False)),
            "response_length": row["response_length"],
        }
        for c in EXTRACTION_COLUMNS:
            rec[c] = ext.get(c)
        rec["key_phrases"] = json.dumps(ext.get("key_phrases") or [], ensure_ascii=False)
        if not row["is_valid_response"]:
            rec["extraction_status"] = "skipped_invalid"
        records.append(rec)
    return pd.DataFrame(records)


def print_summary(df):
    ok = df[df["extraction_status"] == "ok"]
    print("\n── Extraction Summary ──────────────────────────────")
    print(f"   Extracted OK: {len(ok)} / {int(df['is_valid_response'].sum())} valid "
          f"({(df['extraction_status'] == 'failed').sum()} failed)")
    print("\n   By question type:")
    print(ok["question_type"].value_counts().to_string())
    cat = ok[ok["question_type"].isin(["nominal", "binary"])]
    if len(cat):
        st = cat["classification_status"].value_counts()
        print(f"\n   Categorical: {len(cat)} | none_fits: {st.get('none_fits', 0)} | "
              f"invalid_output: {st.get('invalid_output', 0)} | "
              f"letter/text mismatch: {int((cat['letter_text_mismatch'] == True).sum())}")
        by_q = cat.assign(unc=cat["selected_option"].eq("Unclassified")).groupby(
            [COL_PANEL, COL_QUESTION])["unc"].mean().mul(100).round(0)
        print("   Unclassified % by question (top 5):")
        print(by_q.sort_values(ascending=False).head(5).to_string())
    quant = ok[ok["question_type"].isin(["quantitative", "hybrid"])]
    if len(quant):
        print(f"\n   Quantitative: {len(quant)} | with number: {int(quant['numeric_value'].notna().sum())}")
        print("   Units reported:", quant["value_unit"].value_counts().to_dict())
    print("────────────────────────────────────────────────────\n")


def main():
    print("\n═══ SUPERVISED EXTRACTION v2 (letters, temperature 0, hashed cache) ═══\n")
    ind_path = os.path.join(OUTPUT_DIR, "01_individual_clean.csv")
    if not os.path.exists(ind_path):
        raise FileNotFoundError("Run preprocess.py first.")
    ind = pd.read_csv(ind_path)
    print(f"Loaded {len(ind)} individual responses")
    cache, jobs = run_extraction(ind)
    df = build_extraction_df(ind, cache, jobs)
    out_path = os.path.join(OUTPUT_DIR, "02_extracted.csv")
    df.to_csv(out_path, index=False)
    print_summary(df)
    print(f"Saved: {out_path}\n")
    return df


if __name__ == "__main__":
    main()
