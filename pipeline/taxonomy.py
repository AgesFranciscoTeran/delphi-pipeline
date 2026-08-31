"""
Question and response-option taxonomy — defined and reviewed by Emily (domain expert).
Source: "Question by question" (Emily's English version).

Design note: options nested under "Depends" in Emily's document have been FLATTENED into
self-contained options (e.g. "Depends" + "Quality of tutors" -> "Depends on quality of tutors")
so that every response falls into exactly one mutually exclusive category. All other labels
use Emily's exact wording.

Types:
  - quantitative : asks for a number; has 'bands'
  - nominal      : fixed set of structured options; has 'options'
  - binary       : two options only; has 'options'
  - hybrid       : number coupled with an associated policy; has 'bands' + 'band_policies'

Mapping from Emily's numbering -> our IDs:
  Panel 1 -> #1-7   (P1_Q1 .. P1_Q7)
  Panel 2 -> #8-14  (P2_Q1 .. P2_Q7)
  Panel 3 -> #15-24 (P3_Q1 .. P3_Q10)
  Panel 4 -> #25-32 (P4_Q1 .. P4_Q8)
"""

EMILY_TAXONOMY = {
    # ── Panel 1 ───────────────────────────────────────────────────────────────
    "P1_Q1": {
        "emily_num": 1,
        "text": "How many semesters of surgery training should medical students receive?",
        "type": "quantitative",
        "bands": {
            "Minimal": "1-2 semesters",
            "Moderate": "3-5 semesters",
            "Intensive": ">6 semesters",
            "Individualized": "depending on each student's needs",
        },
    },
    "P1_Q2": {
        "emily_num": 2,
        "text": "Should specialization be delivered based on academic education or clinical practice?",
        "type": "nominal",
        "options": [
            "Academic education",
            "Clinical practice",
            "Balanced",
            "Supervised practice",
            "According to student competencies",
        ],
    },
    "P1_Q3": {
        "emily_num": 3,
        "text": "How should Integral Community Development (DCI) be delivered to medical students?",
        "type": "nominal",
        "options": [
            "Yes",
            "Only if there are students with prior experience",
            "No",
            "A professor must be present",
            "Affects follow-up",
            "Depends on the type of community project",
            "Depends on the type of population (children, elderly)",
        ],
    },
    "P1_Q4": {
        "emily_num": 4,
        "text": "Should recently graduated students give classes?",
        "type": "nominal",
        "options": [
            "Yes",
            "Basic sciences only",
            "NBME preparation only",
            "With passing exam",
            "With prior experience",
            "According to their academic performance",
            "No",
        ],
    },
    "P1_Q5": {
        "emily_num": 5,
        "text": "Should we have an impartial regulatory organism that solves academic problems?",
        "type": "nominal",
        "options": [
            "No",
            "Yes",
            "With student representation",
            "Independent from Medicine",
            "Supervised by a central university committee",
        ],
    },
    "P1_Q6": {
        "emily_num": 6,
        "text": "How many hours of clinical practice should a student receive per module?",
        "type": "quantitative",
        "bands": {"Minimal": "1-2", "Moderate": "3-5", "Intensive": ">6"},
    },
    "P1_Q7": {
        "emily_num": 7,
        "text": "How many hours of teaching do you believe we should receive per week?",
        "type": "quantitative",
        "bands": {"Minimal": "3-5", "Moderate": "6-8", "Intensive": ">9"},
    },

    # ── Panel 2 ───────────────────────────────────────────────────────────────
    "P2_Q1": {
        "emily_num": 8,
        "text": "Is PBL appropriate for medical education?",
        "type": "nominal",
        "options": [
            "Yes",
            "Supplemented with lecture classes",
            "With increased clinical practice",
            "Only in certain years of the program",
            "Only in some subjects",
            "No",
            "Depends on quality of tutors",
        ],
    },
    "P2_Q2": {
        "emily_num": 9,
        "text": "What distribution of practice and theory should medical students receive?",
        "type": "nominal",
        "options": [
            "More practice, less theory",
            "More theory, less practice",
            "Balanced",
            "Based on student need",
        ],
    },
    "P2_Q3": {
        "emily_num": 10,
        "text": "How many hours daily should medical students receive in-person classes?",
        "type": "quantitative",
        "bands": {"Minimal": "3-5", "Moderate": "6-8", "Intensive": ">9"},
    },
    "P2_Q4": {
        "emily_num": 11,
        "text": "Should presence in magistral classes be evaluated?",
        "type": "nominal",
        "options": [
            "Yes",
            "No",
            "Depends",
            "Only in practical activities",
            "Only in laboratories",
            "Evaluate participation, not attendance",
            "According to the subject",
        ],
    },
    "P2_Q5": {
        "emily_num": 12,
        "text": "Should medical students receive compulsory mental health assistance?",
        "type": "binary",
        "options": ["Yes", "No"],
    },
    "P2_Q6": {
        "emily_num": 13,
        "text": "Should medical students receive classes on weekends?",
        "type": "nominal",
        "options": [
            "Yes",
            "Only makeup classes",
            "Clinical practices",
            "Only optional activities",
            "Only in clinical years",
            "No",
        ],
    },
    "P2_Q7": {
        "emily_num": 14,
        "text": "Are written exams necessary for PBL classes?",
        "type": "nominal",
        "options": [
            "Yes",
            "With reduction of written evaluations",
            "Combined with practical evaluation",
            "Only in certain modules",
            "Replaced by clinical cases",
            "According to learning objectives",
            "No",
        ],
    },

    # ── Panel 3 ───────────────────────────────────────────────────────────────
    "P3_Q1": {
        "emily_num": 15,
        "text": "How many hours of theoretical teaching per week should medicine students receive?",
        "type": "quantitative",
        "bands": {"Minimal": "3-5", "Moderate": "6-8", "Intensive": ">9"},
    },
    "P3_Q2": {
        "emily_num": 16,
        "text": "How many students should be accepted in first year?",
        "type": "hybrid",
        "bands": {"Low": "<50", "Medium": "50", "High": ">50"},
        "band_policies": {
            "Low": "Depends on admission exam",
            "Medium": "Depends on exam + high school grades",
            "High": "Depends on class availability",
        },
    },
    "P3_Q3": {
        "emily_num": 17,
        "text": "How many students should be rejected in first year?",
        "type": "nominal",
        "options": ["High attrition", "Moderate attrition", "Low attrition"],
    },
    "P3_Q4": {
        "emily_num": 18,
        "text": "Is PBL model a good way of teaching medicine?",
        "type": "nominal",
        "options": [
            "Yes",
            "No",
            "Depends",
            "Only as a complement",
            "Only in clinical subjects",
            "Only with trained tutors",
            "Only in certain years",
            "According to the student's profile",
        ],
    },
    "P3_Q5": {
        "emily_num": 19,
        "text": "How many hours of PBL should be dictated?",
        "type": "quantitative",
        "bands": {"Minimal": "3-5", "Moderate": "6-8", "Intensive": ">9"},
    },
    "P3_Q6": {
        "emily_num": 20,
        "text": "How many hours of practice should we have?",
        "type": "quantitative",
        "bands": {"Minimal": "3-5", "Moderate": "6-8", "Intensive": ">9"},
    },
    "P3_Q7": {
        "emily_num": 21,
        "text": "What weight should each subject have?",
        "type": "nominal",
        "options": [
            "Equality among subjects",
            "Priority to clinical subjects",
            "Priority to scientific subjects",
        ],
    },
    "P3_Q8": {
        "emily_num": 22,
        "text": "How many hours of general college should be dictated?",
        "type": "quantitative",
        "bands": {"Minimal": "3-5", "Moderate": "6-8", "Intensive": ">9"},
    },
    "P3_Q9": {
        "emily_num": 23,
        "text": "Does liberal arts bind with the medical education we receive at USFQ?",
        "type": "nominal",
        "options": [
            "Yes",
            "Only with fewer class hours",
            "Only specific courses",
            "Only at the beginning of the program",
            "No",
            "Depends on course content",
            "Depends on relationship with medicine",
        ],
    },
    "P3_Q10": {
        "emily_num": 24,
        "text": "When should the night shift start?",
        "type": "nominal",
        "options": ["First years", "Preclinical years", "Final years"],
    },

    # ── Panel 4 ───────────────────────────────────────────────────────────────
    "P4_Q1": {
        "emily_num": 25,
        "text": "How many hours of theoretical teaching per day should students receive?",
        "type": "quantitative",
        "bands": {"Minimal": "3-5", "Moderate": "6-8", "Intensive": ">9"},
    },
    "P4_Q2": {
        "emily_num": 26,
        "text": "How many hours of practice teaching per day should students receive?",
        "type": "quantitative",
        "bands": {"Minimal": "3-5", "Moderate": "6-8", "Intensive": ">9"},
    },
    "P4_Q3": {
        "emily_num": 27,
        "text": "Should students pass NBME to graduate?",
        "type": "nominal",
        "options": [
            "Yes",
            "With multiple attempts",
            "As a partial requirement",
            "Together with clinical evaluation",
            "No",
            "Depends on score required",
            "Depends on other academic metrics",
        ],
    },
    "P4_Q4": {
        "emily_num": 28,
        "text": "How often should students be evaluated?",
        "type": "nominal",
        "options": [
            "Scheduled continuous evaluation",
            "Surprise continuous evaluation",
            "Limited evaluation",
            "Minimal evaluation",
            "Depends on the subject",
        ],
    },
    "P4_Q5": {
        "emily_num": 29,
        "text": "What grading system should be used?",
        "type": "nominal",
        "options": ["Numeric system (1-100)", "Letter system (A-F)", "Pass/Fail"],
    },
    "P4_Q6": {
        "emily_num": 30,
        "text": "Should students receive magistral classes?",
        "type": "nominal",
        "options": [
            "Yes",
            "Only for complex topics",
            "Combined with PBL",
            "Only in basic sciences",
            "According to year of training",
            "No",
        ],
    },
    "P4_Q7": {
        "emily_num": 31,
        "text": "How many students should be accepted in the first year?",
        "type": "hybrid",
        "bands": {"Low": "<50", "Medium": "50", "High": ">50"},
        "band_policies": {
            "Low": "Depends on admission exam",
            "Medium": "Depends on exam + high school grades",
            "High": "Depends on class availability",
        },
    },
    "P4_Q8": {
        "emily_num": 32,
        "text": "Should participation be part of evaluation?",
        "type": "nominal",
        "options": [
            "Yes",
            "With a low percentage",
            "Only in PBL",
            "Only in practical activities",
            "According to the subject",
            "No",
        ],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Unidad canónica de cada pregunta cuantitativa / híbrida (Fase 0).
# "assumed": no hay confirmación explícita de Emily; revisar en la Fase 1.
# Ojo: la unidad de las bandas puede diferir de la unidad con la que se formuló la pregunta
# (P1_Q7 pregunta por semana pero las bandas son por día; P1_Q6 pregunta por módulo pero las
# bandas son por semana). La conversión la hace consensus_metrics.py con UNIT_CONVERSIONS.
# ─────────────────────────────────────────────────────────────────────────────
QUESTION_UNITS = {
    # Unidad en la que están definidas las BANDAS de Emily (= unidad del consenso numérico).
    # Fuente: notas de Emily en validation_emily_done.xlsx (28-08-2026) donde las hay.
    "P1_Q1": {"unit": "semesters",    "assumed": False},
    "P1_Q6": {"unit": "hours/week",   "assumed": False},  # Emily: "cada módulo dura aprox 1 mes, la clasificación está hecha por semana"
    "P1_Q7": {"unit": "hours/day",    "assumed": False},  # Emily: "calcular horas diarias con el promedio semanal, 20h para 5 días"
    "P2_Q3": {"unit": "hours/day",    "assumed": False},
    "P3_Q1": {"unit": "hours/day",    "assumed": True},   # misma lógica que P1_Q7 (bandas 3-5/6-8/>9); confirmar con Emily
    "P3_Q2": {"unit": "students",     "assumed": False},
    "P3_Q5": {"unit": "hours/week",   "assumed": False},  # Emily: "la clasificación está hecha para calcular las horas por semana"
    "P3_Q6": {"unit": "hours/week",   "assumed": True},
    "P3_Q8": {"unit": "hours/week",   "assumed": False},  # Emily: ídem P3_Q5
    "P4_Q1": {"unit": "hours/day",    "assumed": False},
    "P4_Q2": {"unit": "hours/day",    "assumed": False},
    "P4_Q7": {"unit": "students",     "assumed": False},
}

for _qid, _u in QUESTION_UNITS.items():
    EMILY_TAXONOMY[_qid]["unit"] = _u["unit"]
    EMILY_TAXONOMY[_qid]["unit_assumed"] = _u["assumed"]


def taxonomy_hash():
    """SHA1 del contenido de la taxonomía: entra en la clave del caché y en el manifiesto."""
    import hashlib, json
    blob = json.dumps(EMILY_TAXONOMY, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:12]


def get_taxonomy(panel, question):
    """Look up the taxonomy entry for a (panel, question) pair."""
    return EMILY_TAXONOMY.get(f"P{panel}_Q{question}")


if __name__ == "__main__":
    from collections import Counter
    types = Counter(v["type"] for v in EMILY_TAXONOMY.values())
    print(f"Total questions: {len(EMILY_TAXONOMY)}")
    print("By type:")
    for t, n in sorted(types.items()):
        print(f"  {t:14s}: {n}")
    n_opts = [len(v["options"]) for v in EMILY_TAXONOMY.values() if "options" in v]
    print(f"\nNominal/binary options per question: min={min(n_opts)}, max={max(n_opts)}")