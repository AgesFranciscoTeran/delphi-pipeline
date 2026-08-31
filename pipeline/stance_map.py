"""
Mapa opción → (postura, calificador), transcrito de los documentos de Emily
"Posturas pregunta por pregunta 2.0" / "Question by question" (PDFs, 30-08-2026).

En esos documentos las opciones están ANIDADAS: el nivel superior es la postura
(Sí / No / Depende) y el nivel inferior son calificadores. taxonomy.py las aplanó
("Depends" + "Quality of tutors" -> "Depends on quality of tutors"), y este módulo
recupera la estructura original sin reextraer nada: cada opción aplanada se mapea a
su postura y su calificador.

Posturas: "favor" | "against" | "conditional". Preguntas sin anidación (elección
entre alternativas, no sí/no) no tienen mapa y se analizan por opción, como hasta ahora.

Pendiente de Emily (Fase 1): confirmar dos rarezas del documento tal cual está:
  * P2_Q7 "Replaced by clinical cases" cuelga de Sí (¿no debería ser No o Depende?).
  * P4_Q8 "According to the subject" cuelga de Sí, pero en P2_Q4 la frase análoga
    cuelga de Depende.
"""

F, A, C = "favor", "against", "conditional"

STANCE_MAP = {
    "P1_Q3": {
        "Yes": (F, None),
        "Only if there are students with prior experience": (F, "prior experience"),
        "No": (A, None),
        "A professor must be present": (A, "professor must be present"),
        "Affects follow-up": (A, "affects follow-up"),
        "Depends on the type of community project": (C, "type of community project"),
        "Depends on the type of population (children, elderly)": (C, "type of population"),
    },
    "P1_Q4": {
        "Yes": (F, None),
        "Basic sciences only": (F, "basic sciences only"),
        "NBME preparation only": (F, "NBME preparation only"),
        "With passing exam": (F, "with passing exam"),
        "With prior experience": (F, "with prior experience"),
        "According to their academic performance": (F, "according to academic performance"),
        "No": (A, None),
    },
    "P1_Q5": {
        "No": (A, None),
        "Yes": (F, None),
        "With student representation": (F, "with student representation"),
        "Independent from Medicine": (F, "independent from Medicine"),
        "Supervised by a central university committee": (F, "supervised by central committee"),
    },
    "P2_Q1": {
        "Yes": (F, None),
        "Supplemented with lecture classes": (F, "supplemented with lectures"),
        "With increased clinical practice": (F, "more clinical practice"),
        "Only in certain years of the program": (F, "only certain years"),
        "Only in some subjects": (F, "only some subjects"),
        "No": (A, None),
        "Depends on quality of tutors": (C, "quality of tutors"),
    },
    "P2_Q4": {
        "Yes": (F, None),
        "No": (A, None),
        "Depends": (C, None),
        "Only in practical activities": (C, "only practical activities"),
        "Only in laboratories": (C, "only laboratories"),
        "Evaluate participation, not attendance": (C, "participation, not attendance"),
        "According to the subject": (C, "according to the subject"),
    },
    "P2_Q5": {"Yes": (F, None), "No": (A, None)},
    "P2_Q6": {
        "Yes": (F, None),
        "Only makeup classes": (F, "only makeup classes"),
        "Clinical practices": (F, "clinical practices"),
        "Only optional activities": (F, "only optional activities"),
        "Only in clinical years": (F, "only clinical years"),
        "No": (A, None),
    },
    "P2_Q7": {
        "Yes": (F, None),
        "With reduction of written evaluations": (F, "fewer written evaluations"),
        "Combined with practical evaluation": (F, "combined with practical"),
        "Only in certain modules": (F, "only certain modules"),
        "Replaced by clinical cases": (F, "replaced by clinical cases"),   # así en el doc; confirmar
        "According to learning objectives": (F, "according to objectives"),
        "No": (A, None),
    },
    "P3_Q4": {
        "Yes": (F, None),
        "No": (A, None),
        "Depends": (C, None),
        "Only as a complement": (C, "only as a complement"),
        "Only in clinical subjects": (C, "only clinical subjects"),
        "Only with trained tutors": (C, "trained tutors"),
        "Only in certain years": (C, "only certain years"),
        "According to the student's profile": (C, "student profile"),
    },
    "P3_Q9": {
        "Yes": (F, None),
        "Only with fewer class hours": (F, "fewer class hours"),
        "Only specific courses": (F, "specific courses"),
        "Only at the beginning of the program": (F, "beginning of program"),
        "No": (A, None),
        "Depends on course content": (C, "course content"),
        "Depends on relationship with medicine": (C, "relationship with medicine"),
    },
    "P4_Q3": {
        "Yes": (F, None),
        "With multiple attempts": (F, "multiple attempts"),
        "As a partial requirement": (F, "partial requirement"),
        "Together with clinical evaluation": (F, "with clinical evaluation"),
        "No": (A, None),
        "Depends on score required": (C, "score required"),
        "Depends on other academic metrics": (C, "other academic metrics"),
    },
    "P4_Q6": {
        "Yes": (F, None),
        "Only for complex topics": (F, "only complex topics"),
        "Combined with PBL": (F, "combined with PBL"),
        "Only in basic sciences": (F, "only basic sciences"),
        "According to year of training": (F, "according to year"),
        "No": (A, None),
    },
    "P4_Q8": {
        "Yes": (F, None),
        "With a low percentage": (F, "low percentage"),
        "Only in PBL": (F, "only in PBL"),
        "Only in practical activities": (F, "only practical activities"),
        "According to the subject": (F, "according to the subject"),      # así en el doc; confirmar (en P2_Q4 cuelga de Depende)
        "No": (A, None),
    },
}

STANCE_ES = {"favor": "A favor", "against": "En contra", "conditional": "Condicional"}


def stance_of(question_id, option):
    """(postura, calificador) para una opción aplanada; (None, None) si la pregunta no tiene mapa."""
    m = STANCE_MAP.get(question_id)
    if not m or not isinstance(option, str):
        return None, None
    return m.get(option, (None, None))
