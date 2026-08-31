"""
Tests de la Fase 0. Corren sin LLM ni red:  python -m pytest tests -q
Cada test corresponde a un hallazgo del diagnóstico del 28-08-2026.
"""
import json
import math
import sys, os
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pipeline"))

import numpy as np
import pandas as pd
import pytest

import extract_arguments as ea
import consensus_metrics as cm
from taxonomy import EMILY_TAXONOMY, get_taxonomy

OPTS = ["Yes", "No", "Depends", "Only in practical activities"]


# ── índices / letras (hallazgo principal) ─────────────────────────────────────

def test_letter_resolution_is_unambiguous():
    assert ea.resolve_letter("A", "Yes", OPTS)[0] == "Yes"
    assert ea.resolve_letter("B", "No", OPTS)[0] == "No"
    assert ea.resolve_letter("D", "", OPTS)[0] == "Only in practical activities"
    assert ea.resolve_letter("d", None, OPTS)[0] == "Only in practical activities"   # minúscula


def test_none_token_is_explicit_none_fits():
    sel, status, mismatch = ea.resolve_letter("NONE", "", OPTS)
    assert sel == "Unclassified" and status == "none_fits" and mismatch is False


def test_zero_or_invalid_letter_is_flagged_not_silently_shifted():
    sel, status, _ = ea.resolve_letter("0", "", OPTS)
    assert sel == "Unclassified" and status == "invalid_output"
    sel, status, _ = ea.resolve_letter("Z", "", OPTS)
    assert sel == "Unclassified" and status == "invalid_output"


def test_invalid_letter_but_exact_text_recovers():
    sel, status, _ = ea.resolve_letter("", "Depends", OPTS)
    assert sel == "Depends" and status == "classified"


def test_letter_text_mismatch_is_reported_and_letter_wins():
    sel, status, mismatch = ea.resolve_letter("A", "No", OPTS)
    assert sel == "Yes" and mismatch is True


def test_categorical_prompt_uses_letters_not_numbers():
    tax = get_taxonomy(2, 4)
    p = ea.build_categorical_prompt(tax["text"], "some response", 2, tax["options"])
    assert "  A. " in p and "  1. " not in p and "NONE" in p


def test_every_categorical_question_fits_in_the_alphabet():
    for qid, tax in EMILY_TAXONOMY.items():
        if tax["type"] in ("nominal", "binary"):
            assert len(tax["options"]) <= len(ea.LETTERS)


# ── JSON robusto ─────────────────────────────────────────────────────────────

def test_extract_json_handles_fences_and_preamble():
    raw = 'Sure, here is the analysis:\n```json\n{"option_letter": "B", "option_text": "No"}\n```\nDone.'
    assert ea.extract_json(raw)["option_letter"] == "B"
    raw = 'Let me think... The answer is {"option_letter": "NONE", "option_text": ""} thanks'
    assert ea.extract_json(raw)["option_letter"] == "NONE"


def test_extract_json_raises_on_garbage():
    with pytest.raises(ValueError):
        ea.extract_json("no json here")


# ── bandas y unidades ─────────────────────────────────────────────────────────

def test_band_is_canonicalized_case_insensitively():
    bands = get_taxonomy(1, 6)["bands"]
    assert ea.canonical_band("minimal", bands) == "Minimal"
    assert ea.canonical_band("HIGH", {"Low": "", "High": ""}) == "High"
    assert ea.canonical_band("Extreme", bands) is None


def test_unit_vocab_and_conversion():
    assert ea.canonical_unit("hours per day") == "hours/day"
    assert ea.canonical_unit("hours/week") == "hours/week"
    assert ea.canonical_unit("fortnights") == "other"
    v, st = cm.to_question_unit(5, "hours/day", "hours/week")
    assert v == 25 and st == "converted"
    v, st = cm.to_question_unit(20, "hours/week", "hours/week")
    assert v == 20 and st == "same"
    v, st = cm.to_question_unit(30, "hours/module", "hours/week")
    assert v == 7.5 and st == "converted"       # Emily: un módulo ≈ 1 mes ≈ 4 semanas
    v, st = cm.to_question_unit(2, "semesters", "hours/week")
    assert v is None and st == "other"          # sin conversión definida: no entra al consenso


def test_quantitative_prompt_forbids_unit_conversion():
    tax = get_taxonomy(3, 1)
    p = ea.build_prompt_for_type(tax, tax["text"], "5 hours per day", 1)
    assert "Do NOT convert" in p and tax["unit"] in p


# ── postproceso end-to-end con salida simulada del modelo ─────────────────────

def test_postprocess_categorical_and_quantitative():
    tax = get_taxonomy(2, 4)
    out = ea.postprocess({"option_letter": "B", "option_text": "No", "core_argument": "x", "key_phrases": []}, tax)
    assert out["selected_option"] == "No" and out["classification_status"] == "classified"
    taxq = get_taxonomy(3, 1)
    out = ea.postprocess({"value": "5", "unit": "hours per day", "value_type": "exact", "value_raw": "5 hours per day",
                          "band": "minimal", "core_argument": "x", "key_phrases": []}, taxq)
    assert out["numeric_value"] == 5.0 and out["value_unit"] == "hours/day" and out["band"] == "Minimal"


class _FakeClient:
    """Cliente OpenAI simulado: devuelve lo que se le programe, con fences y preámbulo."""
    def __init__(self, payloads):
        self.payloads = list(payloads); self.calls = []
        self.chat = self; self.completions = self
    def create(self, **kwargs):
        self.calls.append(kwargs)
        content = self.payloads.pop(0)
        msg = type("M", (), {"content": content})
        choice = type("C", (), {"message": msg})
        return type("R", (), {"choices": [choice]})


def test_extract_single_is_deterministic_config_and_retries_on_bad_json():
    tax = get_taxonomy(2, 5)   # binary Yes/No
    client = _FakeClient(["garbage", '```json\n{"option_letter":"A","option_text":"Yes","core_argument":"c","key_phrases":["k"]}\n```'])
    res = ea.extract_single(client, "rid", "Yes, definitely", tax["text"], 1, tax)
    assert res["selected_option"] == "Yes" and res["extraction_status"] == "ok"
    assert len(client.calls) == 2
    assert client.calls[0]["temperature"] == 0.0 and client.calls[0]["seed"] == ea.SEED


def test_cache_key_changes_with_model_and_prompt():
    k1 = ea.cache_key("rid", "modelA", ea.prompt_hash("p"))
    k2 = ea.cache_key("rid", "modelB", ea.prompt_hash("p"))
    k3 = ea.cache_key("rid", "modelA", ea.prompt_hash("p2"))
    assert len({k1, k2, k3}) == 3


# ── métricas de consenso ──────────────────────────────────────────────────────

def test_entropy_normalized_by_K_is_monotone_in_concentration():
    r1 = ["A"] * 5 + ["B", "C"]
    r2 = ["A"] * 5 + ["B"] * 2
    assert cm.normalized_entropy(r2, 7) < cm.normalized_entropy(r1, 7)   # la v1 daba lo contrario
    assert cm.normalized_entropy(["A"] * 7, 7) == 0.0
    assert math.isclose(cm.normalized_entropy(list("ABCDEFG"), 7), 1.0)


def test_nan_is_not_a_category():
    labels = ["Yes", "Yes", "Yes", np.nan, None, ""]
    assert cm.modal_share(labels) == 1.0
    assert cm.normalized_entropy(labels, 2) == 0.0


def test_small_n_never_gets_a_consensus_label():
    assert cm.categorical_label(1.0, 1, 87.5) == "Insuficiente"
    assert cm.categorical_label(1.0, 7, 0.0) == "Consenso fuerte"
    assert cm.quantitative_label(0.0, 0.0, 0.0, 1) == "Insuficiente"
    assert cm.quantitative_label(0.0, 0.0, 0.0, 8) == "Consenso fuerte"


def test_convergence_has_four_classes():
    assert cm.convergence_class(0.0, 1.0) == "Estable en acuerdo"
    assert cm.convergence_class(0.0, 0.4) == "Estable sin acuerdo"
    assert cm.convergence_class(-0.3, 0.9) == "Convergió"
    assert cm.convergence_class(+0.3, 0.4) == "Se dispersó"


def test_categorical_consensus_counts_failed_extractions_as_unclassified(tmp_path):
    df = pd.DataFrame({
        "question_type": ["nominal"] * 4, "is_valid_response": [True] * 4,
        "Panel": [2] * 4, "Question": [4] * 4, "Round": [1] * 4, "Question Text": ["q"] * 4,
        "selected_option": ["Yes", "Yes", np.nan, "Unclassified"],
        "extraction_status": ["ok", "ok", "failed", "ok"],
    })
    out = cm.categorical_consensus(df)
    r = out.iloc[0]
    assert r["n_classified"] == 2 and r["n_unclassified"] == 2 and r["modal_share"] == 1.0
    assert r["consensus_label"] == "Insuficiente"
    assert json.loads(r["option_counts"])["Yes"] == 2


def test_tie_is_not_a_dominant_option():
    df = pd.DataFrame({
        "question_type": ["nominal"] * 8, "is_valid_response": [True] * 8,
        "Panel": [4] * 8, "Question": [8] * 8, "Round": [3] * 8, "Question Text": ["q"] * 8,
        "selected_option": ["Yes"] * 4 + ["No"] * 4,
        "extraction_status": ["ok"] * 8,
    })
    r = cm.categorical_consensus(df).iloc[0]
    assert bool(r["is_tie"]) is True
    assert r["consensus_label"] == "Sin consenso"
    assert r["modal_option"] == "Empate: No / Yes"


def test_derive_band_from_converted_value():
    b = get_taxonomy(1, 6)["bands"]          # Minimal 1-2 / Moderate 3-5 / Intensive >6 (por semana)
    assert cm.derive_band(7.5, b) == "Intensive"        # "30 h/módulo" -> 7.5 h/semana (Emily: Intensive)
    b7 = get_taxonomy(1, 7)["bands"]         # Minimal 3-5 / Moderate 6-8 / Intensive >9 (por día)
    assert cm.derive_band(4, b7) == "Minimal"           # "20 h/semana" -> 4 h/día (Emily: Minimal)
    assert cm.derive_band(5.5, b7) == "Minimal" and cm.derive_band.last_gap is True
    bh = get_taxonomy(3, 2)["bands"]         # <50 / 50 / >50
    assert cm.derive_band(40, bh) == "Low"
    assert cm.derive_band(50, bh) == "Medium"
    assert cm.derive_band(70, bh) == "High"
    assert cm.derive_band(None, bh) is None


def test_stance_map_covers_exactly_the_taxonomy_options():
    from stance_map import STANCE_MAP
    for qid, m in STANCE_MAP.items():
        assert set(m) == set(EMILY_TAXONOMY[qid]["options"]), qid


def test_stance_of_recovers_the_nested_structure():
    from stance_map import stance_of
    assert stance_of("P1_Q5", "With student representation") == ("favor", "with student representation")
    assert stance_of("P2_Q4", "According to the subject")[0] == "conditional"
    assert stance_of("P4_Q3", "No") == ("against", None)
    assert stance_of("P4_Q5", "Pass/Fail") == (None, None)     # pregunta sin posturas


def test_unstated_unit_rule_is_in_the_prompt():
    tax = get_taxonomy(3, 1)
    p = ea.build_prompt_for_type(tax, tax["text"], "4 to 5 hours", 1)
    assert "do NOT infer the unit from the question" in p


# ── unidad deducida del texto crudo (regresión del 30-08-2026) ────────────────

def test_unit_from_raw_recovers_the_period_the_model_dropped():
    # casos reales de la corrida: el modelo mandó todo esto a "other"
    assert cm.unit_from_raw("8 hours a day", "other")[0] == "hours/day"
    assert cm.unit_from_raw("6 hours daily", "other")[0] == "hours/day"
    assert cm.unit_from_raw("an hour per week", "other")[0] == "hours/week"
    assert cm.unit_from_raw("8 hour/week", "other")[0] == "hours/week"
    assert cm.unit_from_raw("5 to 6 hours daily", "other")[0] == "hours/day"


def test_unit_from_raw_keeps_non_time_answers_out():
    # "10 patients per week" tiene periodo pero NO son horas: no debe volverse hours/week
    assert cm.unit_from_raw("10 patients per week", "other")[0] == "other"
    assert cm.unit_from_raw("20 cardiovascular patients", "other")[0] == "other"


def test_hours_without_period_only_counts_for_hour_questions():
    u, _ = cm.unit_from_raw("5 hours", "other")
    assert u == cm.UNIT_HOURS_ANY
    assert cm.to_question_unit(5.0, u, "hours/day") == (5.0, "assumed")
    assert cm.to_question_unit(5.0, u, "semesters") == (None, "other")


def test_model_unit_wins_when_it_is_valid():
    assert cm.unit_from_raw("5 hours per day", "hours/day") == ("hours/day", "model")


def test_hours_answer_never_counts_as_semesters_or_students():
    # el error concreto: "an hour per week" entró como 1 semestre en P1_Q1
    u, _ = cm.unit_from_raw("an hour per week", "other")
    assert cm.to_question_unit(1.0, u, "semesters") == (None, "other")
    assert cm.to_question_unit(10.0, cm.unit_from_raw("10 patients per week", "other")[0], "students") == (None, "other")


def test_years_convert_to_semesters():
    # P1_Q1 pregunta en semestres y un panelista responde en años: es una equivalencia, no un juicio
    assert cm.to_question_unit(1, "years", "semesters") == (2.0, "converted")
    assert cm.to_question_unit(2, "semesters", "years") == (1.0, "converted")


def test_max_tokens_is_per_call_not_global():
    """DeepSeek necesita presupuesto para razonar; con el MAX_TOKENS de Gemma no llega al JSON."""
    tax = get_taxonomy(2, 5)
    ok = '{"option_letter":"A","option_text":"Yes","core_argument":"c","key_phrases":[]}'
    c = _FakeClient([ok]); ea.extract_single(c, "r", "Yes", tax["text"], 1, tax, max_tokens=2500)
    assert c.calls[0]["max_tokens"] == 2500
    c = _FakeClient([ok]); ea.extract_single(c, "r", "Yes", tax["text"], 1, tax)
    assert c.calls[0]["max_tokens"] == ea.MAX_TOKENS
