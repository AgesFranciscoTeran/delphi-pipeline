"""
Mapa opción -> (postura, calificador).

GENERADO por tools/build_taxonomy.py desde la anidación del documento de Emily.
NO EDITAR A MANO.

Antes esto era una transcripción manual: el documento anidaba las opciones bajo la postura,
taxonomy.py las aplanaba perdiendo el nivel de arriba, y este módulo lo reconstruía opción por
opción. Dos transcripciones a mano del mismo documento, que podían desajustarse en silencio.
Ahora las dos salen de la misma fuente y el prefijo de la opción ("Yes, ...") determina la
postura sin que nadie decida nada.

Posturas: "favor" | "against" | "conditional". Las preguntas sin anidación (elección entre
alternativas, no sí/no) no aparecen aquí y se analizan por opción.
"""

F, A, C = "favor", "against", "conditional"

STANCE_MAP = {
    "P1_Q4": {
        "Yes": (F, None),
        "Yes, basic sciences only": (F, "Basic sciences only"),
        "Yes, NBME preparation only": (F, "NBME preparation only"),
        "Yes, with passing exam": (F, "With passing exam"),
        "Yes, with prior experience": (F, "With prior experience"),
        "Yes, according to their academic performance": (F, "According to their academic performance"),
        "No": (A, None),
        "No, lack of preparation": (A, "Lack of preparation"),
    },
    "P1_Q5": {
        "Yes": (F, None),
        "Yes, with student representation": (F, "With student representation"),
        "Yes, independent from medicine": (F, "Independent from medicine"),
        "Yes, supervised by a central university committee": (F, "Supervised by a central university committee"),
        "No": (A, None),
        "No, use the ones that already exist": (A, "Use the ones that already exist"),
    },
    "P2_Q4": {
        "Yes": (F, None),
        "Yes, only in practical activities": (F, "Only in practical activities"),
        "Yes, only in laboratories": (F, "Only in laboratories"),
        "No": (A, None),
        "No, according to the subject": (A, "According to the subject"),
        "No, evaluate participation, not attendance": (A, "Evaluate participation, not attendance"),
    },
    "P2_Q5": {
        "Yes": (F, None),
        "No": (A, None),
        "Depends on the availability of the student": (C, "Depends on the availability of the student"),
    },
    "P2_Q6": {
        "Yes": (F, None),
        "Yes, only makeup classes": (F, "Only makeup classes"),
        "Yes, clinical practices": (F, "Clinical practices"),
        "Yes, only optional activities": (F, "Only optional activities"),
        "Yes, only in clinical years": (F, "Only in clinical years"),
        "Yes, only for exams": (F, "Only for exams"),
        "No": (A, None),
        "No, respect free time": (A, "Respect free time"),
    },
    "P2_Q7": {
        "Yes": (F, None),
        "Yes, with reduction of written evaluations": (F, "With reduction of written evaluations"),
        "Yes, combined with practical evaluation": (F, "Combined with practical evaluation"),
        "No": (A, None),
        "No, only in certain modules": (A, "Only in certain modules"),
        "No, according to learning objectives": (A, "According to learning objectives"),
        "No, replaced by clinical cases": (A, "Replaced by clinical cases"),
    },
    "P3_Q4": {
        "Yes": (F, None),
        "Yes, only as complement for other classes": (F, "Only as complement for other classes"),
        "Yes, only in clinical subjects": (F, "Only in clinical subjects"),
        "Yes, only with trained tutors": (F, "Only with trained tutors"),
        "Yes, only in certain years": (F, "Only in certain years"),
        "No": (A, None),
    },
    "P3_Q9": {
        "Yes": (F, None),
        "Yes, only with fewer class hours": (F, "Only with fewer class hours"),
        "Yes, only specific courses": (F, "Only specific courses"),
        "Yes, only at the beginning of the program": (F, "Only at the beginning of the program"),
        "No": (A, None),
        "Depends on the course content": (C, "Depends on the course content"),
        "Depends on the relation it has with medicine": (C, "Depends on the relation it has with medicine"),
    },
    "P4_Q3": {
        "Yes": (F, None),
        "Yes, with multiple attempts": (F, "With multiple attempts"),
        "Yes, as a partial requirement": (F, "As a partial requirement"),
        "Yes, together with clinical evaluation": (F, "Together with clinical evaluation"),
        "No": (A, None),
        "No, depends on the score required": (A, "Depends on the score required"),
        "No, should depend on other academic metrics": (A, "Should depend on other academic metrics"),
    },
    "P4_Q6": {
        "Yes": (F, None),
        "Yes, only for complex topics": (F, "Only for complex topics"),
        "Yes, combined with PBL": (F, "Combined with PBL"),
        "Yes, only in basic sciences": (F, "Only in basic sciences"),
        "No": (A, None),
        "No, according to year of training": (A, "According to year of training"),
    },
    "P4_Q8": {
        "Yes": (F, None),
        "Yes, with a low percentage": (F, "With a low percentage"),
        "Yes, only in PBL": (F, "Only in PBL"),
        "Yes, only in practical activities": (F, "Only in practical activities"),
        "Yes, according to the subject": (F, "According to the subject"),
    },
}

STANCE_ES = {"favor": "A favor", "against": "En contra", "conditional": "Condicional"}


def stance_of(qid, option):
    """(postura, calificador) de una opción; (None, None) si la pregunta no tiene postura."""
    entrada = STANCE_MAP.get(qid)
    if not entrada:
        return None, None
    if option in entrada:
        return entrada[option]
    objetivo = " ".join(str(option).lower().split())
    for k, v in entrada.items():
        if " ".join(k.lower().split()) == objetivo:
            return v
    return None, None


if __name__ == "__main__":
    print("Preguntas con postura: %d" % len(STANCE_MAP))
    for q, m in STANCE_MAP.items():
        from collections import Counter
        c = Counter(p for p, _ in m.values())
        print("  %-7s %2d opciones  %s" % (q, len(m), dict(c)))
