"""
Taxonomía de preguntas y opciones — definida y revisada por Emily (experta de dominio).

GENERADO por tools/build_taxonomy.py desde docs/emily_posturas_varias_opciones.json.
NO EDITAR A MANO: edita el documento de Emily, vuelve a extraer el JSON y regenera.

Fuente: «Posturas varias opciones» v2 (Emily, 14-09-2026).

Cómo se aplanó el árbol
-----------------------
El documento anida: la celda «- Yes» lleva sus calificadores y la celda «- No» los suyos.
El pipeline pide UNA opción de una lista cerrada, así que la postura va dentro del texto
de la opción ("Yes, only in clinical subjects"). Ventaja: el modelo no puede elegir un
calificador sin comprometerse con una postura — que era el fallo más común — y stance_map.py
se deriva del prefijo en vez de transcribirse a mano.

Tipos:
  - quantitative : pide un número; tiene 'bands'
  - nominal      : conjunto cerrado de opciones; tiene 'options'
  - hybrid       : número acoplado a una política; tiene 'bands' + 'band_policies'

'extra_axes' (sólo en preguntas cuantitativas) es lo que la v2 añade y esta corrida todavía
NO mide: convertir esas preguntas a nominal destruiría la capa numérica. Medir varios ejes a
la vez es la Fase 1 y necesita confirmación de Emily.

Numeración de Emily -> nuestros IDs:
  Panel 1 -> #1-7   (P1_Q1 .. P1_Q7)
  Panel 2 -> #8-14  (P2_Q1 .. P2_Q7)
  Panel 3 -> #15-24 (P3_Q1 .. P3_Q10)
  Panel 4 -> #25-32 (P4_Q1 .. P4_Q8)
"""

EMILY_TAXONOMY = {
    "P1_Q1": {
        "emily_num": 1,
        "text": "How many semesters of surgery training should medical students receive",
        "type": "quantitative",
        "bands": {
            "Minimum": "1-2",
            "Moderate": "3-5",
            "Intensive": ">=6",
        },
        "extra_axes": [
            {
                "tipo": "Nominal",
                "opciones": [
                    "Each semester",
                    "Depending on ABP",
                    "Follow international standard",
                ],
            },
        ],
        "unit": "semesters",
        "unit_assumed": True,
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
            "According on student competences",
        ],
    },
    "P1_Q3": {
        "emily_num": 3,
        "text": "How should Integral Community Development (DCI) be delivered to medical students?",
        "type": "nominal",
        "options": [
            "Should be optional",
            "Should contain work with kids",
            "Should contain work with elderly",
            "Should be in rural areas",
            "Only with students with prior experience",
            "Only if it does not affect follow up",
            "Up to 4 semesters",
            "More than 4 semesters",
        ],
    },
    "P1_Q4": {
        "emily_num": 4,
        "text": "Should recently graduated students give classes?",
        "type": "nominal",
        "options": [
            "Yes",
            "Yes, basic sciences only",
            "Yes, NBME preparation only",
            "Yes, with passing exam",
            "Yes, with prior experience",
            "Yes, according to their academic performance",
            "No",
            "No, lack of preparation",
        ],
    },
    "P1_Q5": {
        "emily_num": 5,
        "text": "Should we have an impartial regulatory organism that solves academic problems?",
        "type": "nominal",
        "options": [
            "Yes",
            "Yes, with student representation",
            "Yes, independent from medicine",
            "Yes, supervised by a central university committee",
            "No",
            "No, use the ones that already exist",
        ],
    },
    "P1_Q6": {
        "emily_num": 6,
        "text": "How many hours of clinical practice should a student receive per module?",
        "type": "quantitative",
        "bands": {
            "Minimal": "1-2",
            "Moderate": "3-5",
            "Intensive": ">=6",
        },
        "extra_axes": [
            {
                "tipo": "Nominal",
                "opciones": [
                    "Depends on the module",
                    "Depends on the practice",
                ],
            },
        ],
        "unit": "hours/week",
        "unit_assumed": False,
    },
    "P1_Q7": {
        "emily_num": 7,
        "text": "How many hours of teaching do you believe we should receive per week?",
        "type": "quantitative",
        "bands": {
            "Minimal": "3-5",
            "Moderate": "6-8",
            "Intensive": ">=9",
        },
        "extra_axes": [
            {
                "tipo": "Nominal",
                "opciones": [
                    "Depends on the number of practical hours",
                    "Depends on the schedule of the semester",
                ],
            },
        ],
        "unit": "hours/week",
        "unit_assumed": False,
    },
    "P2_Q1": {
        "emily_num": 8,
        "text": "Is PBL appropriate for medical education?",
        "type": "nominal",
        "options": [
            "Yes, supplemented with lecture classes",
            "Yes, with increased clinical practice",
            "Only certain year",
            "Only some subjects",
            "Depending on the quality of tutors",
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
        "text": "How many hours daily should medical students receive in presential classes?",
        "type": "quantitative",
        "bands": {
            "Minimal": "3-5",
            "Moderate": "6-8",
            "Intensive": ">=9",
        },
        "extra_axes": [
            {
                "tipo": "Nominal",
                "opciones": [
                    "Depends on the semester",
                    "Depends on the year",
                    "Depends on the clinical practice",
                ],
            },
        ],
        "unit": "hours/day",
        "unit_assumed": True,
    },
    "P2_Q4": {
        "emily_num": 11,
        "text": "Should presence in magistral classes be evaluated?",
        "type": "nominal",
        "options": [
            "Yes",
            "Yes, only in practical activities",
            "Yes, only in laboratories",
            "No",
            "No, according to the subject",
            "No, evaluate participation, not attendance",
        ],
    },
    "P2_Q5": {
        "emily_num": 12,
        "text": "Should medical students receive compulsory mental health assistance?",
        "type": "nominal",
        "options": [
            "Yes",
            "No",
            "Obligatory",
            "Depends on the availability of the student",
            "After practices",
            "Minimal: 1",
            "Moderate: 2-3",
            "Intensive: >=4",
        ],
    },
    "P2_Q6": {
        "emily_num": 13,
        "text": "Should medical students receive classes on weekends?",
        "type": "nominal",
        "options": [
            "Yes",
            "Yes, only makeup classes",
            "Yes, clinical practices",
            "Yes, only optional activities",
            "Yes, only in clinical years",
            "Yes, only for exams",
            "No",
            "No, respect free time",
        ],
    },
    "P2_Q7": {
        "emily_num": 14,
        "text": "Are written exams necessary for PBL classes?",
        "type": "nominal",
        "options": [
            "Yes",
            "Yes, with reduction of written evaluations",
            "Yes, combined with practical evaluation",
            "No",
            "No, only in certain modules",
            "No, according to learning objectives",
            "No, replaced by clinical cases",
            "Only once",
            "Only twice",
            "4 / Every week",
        ],
    },
    "P3_Q1": {
        "emily_num": 15,
        "text": "How many hours of theoretical teaching per week should medicine students receive?",
        "type": "quantitative",
        "bands": {
            "Minimal": "3-5",
            "Moderate": "6-8",
            "Intensive": ">=9",
        },
        "extra_axes": [
            {
                "tipo": "Nominal",
                "opciones": [
                    "Depends on the hours of practice",
                    "Depends in the year",
                    "Depends on the subject",
                ],
            },
        ],
        "unit": "hours/day",
        "unit_assumed": True,
    },
    "P3_Q2": {
        "emily_num": 16,
        "text": "How many students should be accepted in first year?",
        "type": "hybrid",
        "bands": {
            "Few": "<50",
            "More": ">=50",
        },
        "extra_axes": [
            {
                "tipo": "Nominal",
                "opciones": [
                    "Depends on admission exam",
                    "Depends on exam + high school grades",
                    "Depends on availability of classes",
                ],
            },
            {
                "tipo": "Numerical (exam grade)",
                "opciones": [
                    "More than 85/100",
                    "More than 90/100",
                    "More than 95/100",
                ],
            },
        ],
        "unit": "students",
        "unit_assumed": True,
    },
    "P3_Q3": {
        "emily_num": 17,
        "text": "How many students should be rejected in first year?",
        "type": "nominal",
        "options": [
            "Depend on grades",
            "Depends on passing all subjects",
            "Depends on overall GPA",
            "Should be rejected before first year",
            "Maximum 10%",
            "Maximum 20%",
            "Maximum 30%",
        ],
    },
    "P3_Q4": {
        "emily_num": 18,
        "text": "Is PBL model a good way of teaching medicine?",
        "type": "nominal",
        "options": [
            "Yes",
            "Yes, only as complement for other classes",
            "Yes, only in clinical subjects",
            "Yes, only with trained tutors",
            "Yes, only in certain years",
            "No",
        ],
    },
    "P3_Q5": {
        "emily_num": 19,
        "text": "How many hours of PBL should be dictated?",
        "type": "quantitative",
        "bands": {
            "Minimal": "<=5",
            "Moderate": "6-8",
            "Intensive": ">=9",
        },
        "extra_axes": [
            {
                "tipo": "Nominal",
                "opciones": [
                    "Depends on the credits",
                    "Depends on clinical hours",
                    "Depends on the subject",
                ],
            },
        ],
        "unit": "hours/week",
        "unit_assumed": False,
    },
    "P3_Q6": {
        "emily_num": 20,
        "text": "How many hours of practice should we have?",
        "type": "quantitative",
        "bands": {
            "Minimal": "<=5",
            "Moderate": "6-8",
            "Intensive": ">=9",
        },
        "extra_axes": [
            {
                "tipo": "Nominal",
                "opciones": [
                    "Depends on the subject",
                    "Depends on the availability of tutors",
                ],
            },
        ],
        "unit": "hours/week",
        "unit_assumed": False,
    },
    "P3_Q7": {
        "emily_num": 21,
        "text": "What weight should each subject have?",
        "type": "nominal",
        "options": [
            "Equality among subjects",
            "Priority to clinical subjects",
            "Priority to scientific subjects",
            "Based on participation",
            "Priority to PBL",
            "Depends on number of hours",
            "Priority to medicine subjects rather than general college",
        ],
    },
    "P3_Q8": {
        "emily_num": 22,
        "text": "How many hours of general college should be dictated?",
        "type": "quantitative",
        "bands": {
            "Minimal": "<=5",
            "Moderate": "6-8",
            "Intensive": ">=9",
        },
        "extra_axes": [
            {
                "tipo": "Nominal",
                "opciones": [
                    "Should be online",
                    "Should be optional",
                    "Same priority as medicine subjects",
                ],
            },
        ],
        "unit": "hours/week",
        "unit_assumed": False,
    },
    "P3_Q9": {
        "emily_num": 23,
        "text": "Does liberal arts bind with the medical education we receive at USFQ?",
        "type": "nominal",
        "options": [
            "Yes",
            "Yes, only with fewer class hours",
            "Yes, only specific courses",
            "Yes, only at the beginning of the program",
            "Depends on the course content",
            "Depends on the relation it has with medicine",
            "No",
        ],
    },
    "P3_Q10": {
        "emily_num": 24,
        "text": "When should the night shift start?",
        "type": "nominal",
        "options": [
            "First years (1-2)",
            "Preclinical years (3-4)",
            "Final years (5-6)",
        ],
    },
    "P4_Q1": {
        "emily_num": 25,
        "text": "How many hours of theoretical teaching per day should students receive?",
        "type": "quantitative",
        "bands": {
            "Minimal": "3-5",
            "Moderate": "6-8",
            "Intensive": ">9",
        },
        "extra_axes": [
            {
                "tipo": "Nominal",
                "opciones": [
                    "Depends on the subject",
                ],
            },
        ],
        "unit": "hours/day",
        "unit_assumed": True,
    },
    "P4_Q2": {
        "emily_num": 26,
        "text": "How many hours of practice teaching per day should students receive?",
        "type": "quantitative",
        "bands": {
            "Minimal": "3-5",
            "Moderate": "6-8",
            "Intensive": ">9",
        },
        "extra_axes": [
            {
                "tipo": "Nominal",
                "opciones": [
                    "Depends on the tutors",
                ],
            },
        ],
        "unit": "hours/day",
        "unit_assumed": True,
    },
    "P4_Q3": {
        "emily_num": 27,
        "text": "Should students pass NBME to graduate?",
        "type": "nominal",
        "options": [
            "Yes",
            "Yes, with multiple attempts",
            "Yes, as a partial requirement",
            "Yes, together with clinical evaluation",
            "No",
            "No, depends on the score required",
            "No, should depend on other academic metrics",
        ],
    },
    "P4_Q4": {
        "emily_num": 28,
        "text": "How often should students be evaluated?",
        "type": "nominal",
        "options": [
            "Daily",
            "Weekly",
            "Once in the semester",
            "Scheduled continuous evaluation",
            "Surprise continuous evaluation",
            "Limited evaluation",
            "Minimal evaluation",
            "Depends on the subject",
            "Depends on the credits",
        ],
    },
    "P4_Q5": {
        "emily_num": 29,
        "text": "What grading system should be used?",
        "type": "nominal",
        "options": [
            "Numeric system 0-100",
            "Letter system A-F",
            "Pass/Fail",
            "Combined",
            "First years: Numeric system / Last years: Pass-Fail",
            "First years: A-F / Last years: Pass-Fail",
        ],
    },
    "P4_Q6": {
        "emily_num": 30,
        "text": "Should students receive magistral classes?",
        "type": "nominal",
        "options": [
            "Yes",
            "Yes, only for complex topics",
            "Yes, combined with PBL",
            "Yes, only in basic sciences",
            "No",
            "No, according to year of training",
        ],
    },
    "P4_Q7": {
        "emily_num": 31,
        "text": "How many students should be accepted in first year?",
        "type": "hybrid",
        "bands": {
            "Few": "<50",
            "More": ">=50",
        },
        "extra_axes": [
            {
                "tipo": "Nominal",
                "opciones": [
                    "Depends on admission exam",
                    "Depends on exam + high school grades",
                    "Depends on availability of classes",
                ],
            },
            {
                "tipo": "Numerical (exam)",
                "opciones": [
                    "More than 85/100",
                    "More than 90/100",
                    "More than 95/100",
                ],
            },
        ],
        "unit": "students",
        "unit_assumed": True,
    },
    "P4_Q8": {
        "emily_num": 32,
        "text": "Should participation be part of evaluation?",
        "type": "nominal",
        "options": [
            "Yes",
            "Yes, with a low percentage",
            "Yes, only in PBL",
            "Yes, only in practical activities",
            "Yes, according to the subject",
        ],
    },
}


def taxonomy_hash():
    """SHA1 del contenido de la taxonomía: entra en la clave del caché y en el manifiesto."""
    import hashlib, json
    blob = json.dumps(EMILY_TAXONOMY, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:12]


def get_taxonomy(panel, question):
    """Look up the taxonomy entry for a (panel, question) pair."""
    q = str(question)
    return EMILY_TAXONOMY.get("P%s_Q%s" % (panel, q[1:] if q.upper().startswith("Q") else q))


if __name__ == "__main__":
    from collections import Counter
    tipos = Counter(v["type"] for v in EMILY_TAXONOMY.values())
    print("Preguntas: %d   hash: %s" % (len(EMILY_TAXONOMY), taxonomy_hash()))
    for t, n in sorted(tipos.items()):
        print("  %-14s %d" % (t, n))
    n_opts = [len(v["options"]) for v in EMILY_TAXONOMY.values() if "options" in v]
    print("Opciones por pregunta nominal: min %d / mediana %d / max %d"
          % (min(n_opts), sorted(n_opts)[len(n_opts) // 2], max(n_opts)))
