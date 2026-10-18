"""
Taxonomía de argumentos — definida por Emily (experta de dominio).

El porqué de cada respuesta, no el qué: nueve perfiles de razonamiento sobre la formación
médica. Se aplican a todas las preguntas del estudio (no hay una lista por pregunta) y cada
respuesta se clasifica en UNO, o en «Sin argumento» si no da una razón.

Fuente: lista «Base de datos actual» que Emily envió a Pancho; adoptada como taxonomía de
argumentos el 16-10-2026. TEXTO LITERAL de Emily: nombres, descripciones y ejemplos tal cual,
con una sola corrección de errata («Defensores e estructura tradicional» -> «de»). No se
retoca la redacción: la taxonomía es suya.
"""
from collections import OrderedDict

ARGUMENTOS = OrderedDict([
    ("Formación clínica intensiva", (
        "Creen que el principal objetivo de la carrera es desarrollar habilidades clínicas mediante "
        "práctica temprana, guardias y contacto con pacientes.",
        "Los estudiantes aprenden medicina viendo a pacientes y practicando no solo estudiando la "
        "teoría")),
    ("Formación científica intensiva", (
        "Consideran que una base teórica fuerte es indispensable antes de aumentar la práctica "
        "clínica.",
        "Los estudiantes necesitan una amplia formación teórica para poder comprender lo que ocurre "
        "en cada paciente")),
    ("Equilibrio clínica-científica", (
        "Defienden una combinación balanceada entre conocimientos científicos y experiencia clínica.",
        "La práctica clínica y la teoría debe mezclarse en el estudio")),
    ("Defensores ABP", (
        "Favorecen el autoaprendizaje, discusión de casos y construcción activa del conocimiento en "
        "grupos que permitan resolver problemas comunes en la práctica médica.",
        "Los estudiantes deben desarrollar habilidades competentes que les permitan resolver "
        "problemas clínicos comunes.")),
    ("Defensores de estructura tradicional", (
        "Prefieren clases magistrales, contenidos organizados y guía constante por parte del "
        "profesor. Es responsabilidad del estudiante mantenerse al día de los temas impartidos en "
        "clase.",
        "Los temas complejos son mejor abordados cuando se lleva a cabo la estructura de explicación "
        "que cada profesor crea correspondiente al contenido.")),
    ("Flexibilidad y bienestar estudiantil", (
        "Priorizan horarios razonables, salud mental, reducción de sobrecarga académica y equilibrio "
        "personal. Esto lleva a un mejor rendimiento del estudiante y mejora su comprensión.",
        "Varias horas de estudio que no sean distribuidas a un horario con tiempo de ocio llevan a "
        "sobrecarga de un estudiante y a mal rendimiento")),
    ("Exigencia y excelencia académica", (
        "Favorecen altos estándares, evaluaciones frecuentes, filtros académicos y procesos "
        "selectivos que permitan filtrar a obtener los mejores resultados.",
        "Los estudiantes que demuestren méritos académicos son los que pueden continuar de año en "
        "año, el resto debe mejorar.")),
    ("Evaluación orientada al aprendizaje", (
        "Se enfocan en que las evaluaciones sean útiles para aprender, independientemente de que "
        "sean temas frecuentes o no.",
        "Los deberes y pruebas deben estar enfocados en identificar las debilidades de los "
        "estudiantes para mejorarlas.")),
    ("Formación integral del médico", (
        "Valoran artes liberales, ética, humanidades, comunicación y desarrollo personal además de "
        "la medicina.",
        "Un médico debe tener conocimiento amplio de culturas para tratar adecuadamente a sus "
        "pacientes no solo de conocimiento científico de medicina.")),
])

NINGUNO = "Sin argumento"     # la respuesta no da una razón, o ninguna categoría encaja
