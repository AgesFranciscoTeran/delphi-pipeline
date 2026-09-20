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
    # La letra se busca por posición, no se fija a mano: el orden de las opciones lo decide
    # el documento de Emily y cambia con cada versión suya.
    i = tax["options"].index("No")
    letra = ea.LETTERS[i]
    out = ea.postprocess({"option_letter": letra, "option_text": "No",
                          "core_argument": "x", "key_phrases": []}, tax)
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


def test_parse_band_range_admits_the_equal_operators():
    """Regresión: la v2 de Emily usa >= y <=, que la versión anterior no parseaba.

    El fallo era mudo — la banda no parseada se descartaba y sus valores caían en la vecina
    por el criterio de borde más cercano — así que vale la pena fijarlo aquí.
    """
    assert cm._parse_band_range(">=6") == (6.0, float("inf"), False, False)
    assert cm._parse_band_range(">6") == (6.0, float("inf"), True, False)
    assert cm._parse_band_range("<=5") == (float("-inf"), 5.0, False, False)
    assert cm._parse_band_range("<5") == (float("-inf"), 5.0, False, True)
    assert cm._parse_band_range("≥9") == (9.0, float("inf"), False, False)
    assert cm._parse_band_range("3-5") == (3.0, 5.0, False, False)
    assert cm._parse_band_range("depending on the student") is None
    # El borde cerrado pertenece a su banda, no a la siguiente.
    b = {"Minimal": "<=5", "Moderate": "6-8", "Intensive": ">=9"}
    assert cm.derive_band(5, b) == "Minimal" and cm.derive_band.last_gap is False
    assert cm.derive_band(9, b) == "Intensive" and cm.derive_band.last_gap is False


def test_derive_band_from_converted_value():
    b = get_taxonomy(1, 6)["bands"]          # Minimal 1-2 / Moderate 3-5 / Intensive >=6 (por semana)
    assert cm.derive_band(7.5, b) == "Intensive"        # "30 h/módulo" -> 7.5 h/semana (Emily: Intensive)
    b7 = get_taxonomy(1, 7)["bands"]         # Minimal 3-5 / Moderate 6-8 / Intensive >=9
    assert cm.derive_band(4, b7) == "Minimal"
    assert cm.derive_band(5.5, b7) == "Minimal" and cm.derive_band.last_gap is True
    # El piso de banda de la v2 empieza en 3: 1 y 2 horas no caen en ninguna banda.
    assert cm.derive_band(2, b7) == "Minimal" and cm.derive_band.last_gap is True
    bh = get_taxonomy(3, 2)["bands"]         # v2: Few <50 / More >=50
    assert cm.derive_band(40, bh) == "Few"
    assert cm.derive_band(50, bh) == "More"
    assert cm.derive_band(70, bh) == "More"
    assert cm.derive_band(None, bh) is None


def test_stance_map_is_a_subset_of_the_taxonomy_options():
    """Ya no es igualdad: la v2 añade ejes en paralelo (numéricos, calificadores sueltos) que
    son opciones válidas sin postura. Lo que sí debe cumplirse es que no haya claves huérfanas:
    toda opción del mapa tiene que existir en la taxonomía, o el aplanado se desincronizó."""
    from stance_map import STANCE_MAP
    for qid, m in STANCE_MAP.items():
        opciones = set(EMILY_TAXONOMY[qid]["options"])
        assert set(m) <= opciones, (qid, set(m) - opciones)
        assert "Yes" in m or "No" in m, qid


def test_two_branches_in_one_cell_keep_their_qualifiers():
    """Regresión de la v3: P1_Q4 mete «- Yes» y «- No» con sus calificadores en UNA celda.

    La regla vieja daba por paralelos los calificadores en cuanto veía las dos posturas juntas
    —se escribió para el eje «Binary» de P2_Q5, que es sólo ['Yes','No']—, así que los cinco del
    «Yes» salían sin prefijo. Consecuencia medible: P1_Q4 se quedaba sin postura en la ronda
    final (n = 0) y sus calificadores parecían hermanos de «Yes» en vez de hijos suyos, lo que
    además inflaba la clase «entre hermanas» del informe de inestabilidad.
    """
    from stance_map import STANCE_MAP, stance_of
    for opcion in ("Yes, with passing exam", "Yes, basic sciences only",
                   "Yes, with prior experience"):
        assert opcion in EMILY_TAXONOMY["P1_Q4"]["options"], opcion
        assert stance_of("P1_Q4", opcion)[0] == "favor", opcion
    assert stance_of("P1_Q4", "No, there is not pedagogical experience")[0] == "against"
    # ninguna opción de una pregunta con ramas debe quedar sin postura por accidente
    sin_postura = set(EMILY_TAXONOMY["P1_Q4"]["options"]) - set(STANCE_MAP["P1_Q4"])
    assert not sin_postura, sin_postura
    # y el eje de postura puro de P2_Q5 sigue sin arrastrar sus calificadores paralelos
    assert stance_of("P2_Q5", "Obligatory") == (None, None)


def test_stance_of_recovers_the_nested_structure():
    from stance_map import stance_of
    # La postura viaja en el texto de la opción, que es lo que cambia respecto de la v1.
    assert stance_of("P1_Q5", "Yes, with student representation") == ("favor", "With student representation")
    assert stance_of("P4_Q3", "No") == ("against", None)
    assert stance_of("P4_Q5", "Pass/Fail") == (None, None)     # pregunta sin posturas
    # "Depends on ..." fuera de rama se lee como condicional (regla del generador).
    assert stance_of("P3_Q9", "Depends on the course content")[0] == "conditional"
    # En la v2 este calificador cuelga de No, no de Depends: es un cambio del documento.
    assert stance_of("P2_Q4", "No, according to the subject")[0] == "against"


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


# ── la taxonomía es generada, no escrita ──────────────────────────────────────

def test_taxonomy_is_in_sync_with_emilys_document():
    """taxonomy.py y stance_map.py se generan con tools/build_taxonomy.py desde el JSON del
    documento de Emily. Si alguien los edita a mano, la próxima regeneración se lo lleva por
    delante en silencio. Este test regenera en un directorio aparte y compara."""
    import subprocess, shutil, tempfile, pathlib
    raiz = pathlib.Path(__file__).resolve().parent.parent
    with tempfile.TemporaryDirectory() as tmp:
        copia = pathlib.Path(tmp) / "Delphi"
        for sub in ("docs", "pipeline", "tools"):
            shutil.copytree(raiz / sub, copia / sub)
        r = subprocess.run([sys.executable, str(copia / "tools" / "build_taxonomy.py")],
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        for nombre in ("taxonomy.py", "stance_map.py"):
            generado = (copia / "pipeline" / nombre).read_text(encoding="utf-8")
            actual = (raiz / "pipeline" / nombre).read_text(encoding="utf-8")
            assert generado == actual, (
                "%s no coincide con lo que genera tools/build_taxonomy.py. "
                "Edita el documento de Emily y regenera; no edites el .py a mano." % nombre)


def test_generated_stance_map_keeps_its_public_interface():
    """Regresión: al generar stance_map.py se perdió STANCE_ES y stance_view.py dejó de
    importar. run.sh se lo traga ('stance_view falló; sigo'), así que el fallo era invisible:
    la capa de posturas simplemente no se calculaba. Lo que el resto del código importa de
    este módulo se fija aquí."""
    import stance_map
    for nombre in ("STANCE_MAP", "STANCE_ES", "stance_of"):
        assert hasattr(stance_map, nombre), nombre
    assert set(stance_map.STANCE_ES) == {"favor", "against", "conditional"}
    import stance_view  # noqa: F401  — importarlo es la prueba


def test_manifiesto_ausente_no_tumba_el_sitio():
    """Regresión: datos.manifiesto() pasaba por _ruta(), que aborta el proceso cuando falta el
    archivo. El manifiesto es opcional, así que una carpeta de resultados sin él hacía fallar
    la generación entera del sitio en vez de omitir la banda de la corrida."""
    import tempfile, importlib, pathlib
    raiz = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(raiz / "sitio"))
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["DELPHI_RESULTADOS"] = tmp
        import datos as _d
        importlib.reload(_d)
        assert _d.manifiesto() == {}          # antes: SystemExit
        json.dump([{"step": "extract_arguments", "model": "m", "taxonomy_hash": "h",
                    "timestamp": "2026-09-14T00:00:00", "n_failed": 0}],
                  open(os.path.join(tmp, "run_manifest.json"), "w"))
        assert _d.manifiesto()[0]["model"] == "m"
    os.environ.pop("DELPHI_RESULTADOS", None)


# ── preflight del modelo ──────────────────────────────────────────────────────

class _ClienteModelos:
    """Cliente falso que sólo responde models.list()."""
    def __init__(self, ids, revienta=False):
        self.revienta = revienta
        self.models = self
        self._ids = ids

    def list(self):
        if self.revienta:
            raise ConnectionError("connection refused")
        datos_ = [type("M", (), {"id": i}) for i in self._ids]
        return type("R", (), {"data": datos_})


def test_preflight_detecta_el_modelo_cambiado():
    """Regresión: cuando la universidad cambió el modelo servido, la corrida no fallaba —
    devolvía 706 extracciones 'failed' una por una y al final sobrescribía 02_extracted.csv
    con filas vacías. Ahora se corta antes de tocar nada."""
    ok, msg = ea.preflight(_ClienteModelos([ea.MODEL_LLM]))
    assert ok and ea.MODEL_LLM in msg

    ok, msg = ea.preflight(_ClienteModelos(["otro-org/otro-modelo"]))
    assert not ok
    assert "otro-org/otro-modelo" in msg          # dice qué SÍ hay
    assert ea.MODEL_LLM in msg                    # y qué se pidió
    assert "DELPHI_MODELO" in msg                 # y cómo arreglarlo

    ok, msg = ea.preflight(_ClienteModelos([], revienta=True))
    assert not ok and "no responde" in msg


def test_preflight_no_se_ejecuta_con_cliente_inyectado():
    """Los tests y run_smoke_offline.py pasan su propio cliente y no deben sondear la red."""
    import inspect
    src = inspect.getsource(ea.run_extraction)
    assert "propio = client is None" in src and "if propio" in src


def test_guardia_de_fallos_protege_la_corrida_anterior():
    """Regresión: la primera corrida con GLM falló el 28 % y aun así sobrescribió
    02_extracted.csv. El resultado no es un error, es una tabla que parece resultado pero está
    calculada sobre media muestra, con preguntas marcadas «Insuficiente» por falta de datos y
    no por falta de acuerdo."""
    def marco(n_ok, n_fail):
        return pd.DataFrame({
            "is_valid_response": [True] * (n_ok + n_fail),
            "extraction_status": ["ok"] * n_ok + ["failed"] * n_fail})

    ea.guardia_de_fallos(marco(100, 0))          # sin fallos: pasa
    ea.guardia_de_fallos(marco(96, 4))           # 4 %: por debajo del umbral, pasa
    with pytest.raises(SystemExit) as exc:
        ea.guardia_de_fallos(marco(72, 28))      # 28 %: el caso real
    msg = str(exc.value)
    assert "28 %" in msg and "No se sobrescribe" in msg
    assert "DELPHI_MAX_TOKENS" in msg            # dice la causa más probable
    assert "caché" in msg                        # y que no se pierde lo bueno

    os.environ["DELPHI_IGNORA_FALLOS"] = "1"     # escape explícito
    try:
        ea.guardia_de_fallos(marco(72, 28))
    finally:
        os.environ.pop("DELPHI_IGNORA_FALLOS", None)


def test_max_tokens_alcanza_para_un_modelo_de_razonamiento():
    """512 era un ajuste específico de Gemma. Con modelos de razonamiento trunca el JSON."""
    assert ea.MAX_TOKENS >= 2000


# ── canal de razonamiento (modelos que "piensan") ─────────────────────────────

def _respuesta(content=None, reasoning=None, finish="stop"):
    msg = type("M", (), {"content": content, "reasoning_content": reasoning})()
    return type("R", (), {"choices": [type("C", (), {"message": msg, "finish_reason": finish})()]})()


def test_texto_de_usa_el_canal_de_razonamiento_cuando_content_viene_vacio():
    """Regresión: GLM devuelve content=None cuando gasta el presupuesto pensando, y todo lo
    escrito queda en reasoning_content. Eso caía como 'json: no JSON object found', que suena
    a que el modelo contestó mal — no a que no llegó a contestar."""
    assert ea.texto_de(_respuesta(content='{"option_letter":"A"}')) == '{"option_letter":"A"}'
    # content vacío -> se lee el razonamiento, donde sí está el JSON
    assert ea.texto_de(_respuesta(content=None, reasoning='{"option_letter":"B"}')) \
        == '{"option_letter":"B"}'
    assert ea.texto_de(_respuesta(content="   ", reasoning='{"x":1}')) == '{"x":1}'


def test_texto_de_distingue_falta_de_presupuesto_de_respuesta_mala():
    with pytest.raises(ValueError) as e:
        ea.texto_de(_respuesta(content=None, reasoning=None, finish="length"))
    assert "sin presupuesto" in str(e.value) and "DELPHI_MAX_TOKENS" in str(e.value)

    with pytest.raises(ValueError) as e:
        ea.texto_de(_respuesta(content=None, reasoning=None, finish="stop"))
    assert "vacía" in str(e.value)


# ── escalada de presupuesto ───────────────────────────────────────────────────

class _ClienteSinPresupuesto:
    """Falla por falta de presupuesto hasta que max_tokens llega al umbral."""
    def __init__(self, umbral):
        self.umbral = umbral
        self.presupuestos = []
        self.chat = self
        self.completions = self

    def create(self, **kw):
        self.presupuestos.append(kw["max_tokens"])
        if kw["max_tokens"] < self.umbral:
            msg = type("M", (), {"content": None, "reasoning_content": None})()
            return type("R", (), {"choices": [
                type("C", (), {"message": msg, "finish_reason": "length"})()]})()
        msg = type("M", (), {"content": '{"option_letter":"A","option_text":"Yes",'
                                        '"core_argument":"c","key_phrases":[]}'})()
        return type("R", (), {"choices": [type("C", (), {"message": msg})()]})()


def test_el_presupuesto_escala_solo_ante_falta_de_presupuesto():
    """Reintentar con el mismo tope es repetir el mismo fallo. Subirlo a ciegas para las 775
    encarece la corrida entera por culpa de cinco. Escala sólo quien lo necesita, y con techo."""
    tax = get_taxonomy(2, 5)
    c = _ClienteSinPresupuesto(umbral=ea.MAX_TOKENS * 4)
    res = ea.extract_single(c, "rid", "Yes", tax["text"], 1, tax, retries=5)
    assert res["extraction_status"] == "ok"
    assert c.presupuestos == [ea.MAX_TOKENS, ea.MAX_TOKENS * 2, ea.MAX_TOKENS * 4]
    assert res["max_tokens_usados"] == ea.MAX_TOKENS * 4


def test_la_escalada_llega_al_techo_aunque_haya_pocos_reintentos():
    """Regresión: la escalada compartía cupo con los reintentos, así que con RETRIES=3 desde
    2500 la secuencia era 2500 -> 5000 -> 10000 y el techo de 16000 no se alcanzaba nunca en
    una corrida normal. Subir el tope no gasta reintento: son cosas distintas."""
    tax = get_taxonomy(2, 5)
    c = _ClienteSinPresupuesto(umbral=10 ** 9)          # nunca alcanza
    res = ea.extract_single(c, "rid", "Yes", tax["text"], 1, tax, retries=3)
    assert res["extraction_status"] == "failed"
    assert max(c.presupuestos) == ea.MAX_TOKENS_TECHO   # llega al techo…
    assert c.presupuestos.count(ea.MAX_TOKENS_TECHO) <= 3   # …y ahí sí se rinde

    # Y si el techo alcanza, la recupera en vez de darla por perdida.
    c2 = _ClienteSinPresupuesto(umbral=ea.MAX_TOKENS_TECHO)
    r2 = ea.extract_single(c2, "rid", "Yes", tax["text"], 1, tax, retries=3)
    assert r2["extraction_status"] == "ok"
    assert r2["max_tokens_usados"] == ea.MAX_TOKENS_TECHO


def test_un_fallo_que_no_es_de_presupuesto_no_escala():
    tax = get_taxonomy(2, 5)
    c = _FakeClient(["basura", "basura", "basura"])
    ea.extract_single(c, "rid", "Yes", tax["text"], 1, tax)
    assert {k["max_tokens"] for k in c.calls} == {ea.MAX_TOKENS}


# ── decodificación guiada ─────────────────────────────────────────────────────

def test_el_modo_de_decodificacion_entra_en_la_clave_del_cache():
    """Encender guided_json cambia CÓMO se produce la salida. Si no invalidara el caché, una
    corrida mezclaría 770 respuestas decodificadas libremente con 5 decodificadas por esquema
    en la misma tabla — lo que un artículo de métodos no puede tener."""
    import importlib
    hashes = {}
    for guiado in ("0", "1"):
        os.environ["DELPHI_GUIADO"] = guiado
        import config, extract_arguments
        importlib.reload(config)
        importlib.reload(extract_arguments)
        hashes[guiado] = extract_arguments.prompt_hash("el mismo prompt exacto")
    os.environ.pop("DELPHI_GUIADO", None)
    importlib.reload(config)
    importlib.reload(extract_arguments)
    assert hashes["0"] != hashes["1"], "el modo de decodificación no invalida el caché"


def test_los_esquemas_guiados_son_validos_para_las_32_preguntas():
    """guided_json era código muerto: estaba escrito pero nunca se había ejecutado. Antes de
    encenderlo, comprobar que produce un esquema válido para cada pregunta."""
    import jsonschema
    for qid, tax in EMILY_TAXONOMY.items():
        esquema = ea.guided_schema_for(tax)
        assert esquema, qid
        jsonschema.Draft7Validator.check_schema(esquema)
        json.dumps(esquema)                      # serializable para mandarlo al servidor
        if tax["type"] in ("nominal", "binary"):
            letras = esquema["properties"]["option_letter"]["enum"]
            assert len(letras) == len(tax["options"]) + 1   # +1 por NONE
            assert ea.NONE_TOKEN in letras
        else:
            bandas = esquema["properties"]["band"]["enum"]
            assert set(tax["bands"]) <= set(b for b in bandas if b)


def test_call_llm_manda_el_esquema_cuando_el_guiado_esta_activo():
    tax = get_taxonomy(2, 5)
    c = _FakeClient(['{"option_letter":"A","option_text":"Yes","core_argument":"c","key_phrases":[]}'])
    ea.extract_single(c, "rid", "Yes", tax["text"], 1, tax)
    extra = c.calls[0].get("extra_body") or {}
    if ea.USE_GUIDED_JSON:
        assert "guided_json" in extra and extra["guided_json"]["properties"]["option_letter"]
    assert "chat_template_kwargs" not in extra      # medido: con GLM empeora
