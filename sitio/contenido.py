# -*- coding: utf-8 -*-
"""
Texto editorial: lo único del sitio que no sale de Resultados/*.csv.

Todo lo demás —tablas, cifras, figuras— lo produce datos.py desde los CSV de la corrida.
Si un número aparece escrito aquí, es un bug.
"""

# Qué decisión de taxonomía afecta a qué panel. Sirve para que cada página diga sólo lo
# que le toca, en vez de repetir las ocho en las cuatro.
DECISIONES = [
 {"n": 1, "titulo": "Separar postura de calificadores",
  "paneles": [1, 2, 3, 4],
  "hoy": "Cada pregunta tiene una lista única de opciones excluyentes que mezcla la postura "
         "con sus condiciones. «Sí, pero sólo en ciencias básicas» encaja en tres a la vez.",
  "evidencia": "El documento de posturas de Emily ya trae la estructura anidada y ya está "
               "codificada; leído así, el acuerdo con sus etiquetas sube de 18/24 a 21/24.",
  "decision": "Confirmar dos casos: «Replaced by clinical cases» cuelga de <em>Sí</em> en "
              "P2_Q7, y «According to the subject» cuelga de <em>Sí</em> en P4_Q8 pero de "
              "<em>Depende</em> en P2_Q4."},
 {"n": 2, "titulo": "P1_Q3 (DCI): volver a tipificar",
  "paneles": [1],
  "hoy": "El 86 % de las respuestas queda sin clasificar: los panelistas no eligen una "
         "postura, describen cómo debería ser el DCI.",
  "evidencia": "Al validar, Emily creó una categoría que no existía («Less semesters»).",
  "decision": "¿Dividirla en dos capas —cuántos semestres y qué actividades— o dejarla como "
              "una sola pregunta abierta?"},
 {"n": 3, "titulo": "P3_Q3: umbrales de depuración",
  "paneles": [3],
  "hoy": "«Alta / Moderada / Baja depuración» no tienen números. En los datos aparecen 20 %, "
         "15 %, «menos del 10 %», «20 estudiantes», y tres personas que dicen que no debe "
         "haber porcentaje fijo.",
  "evidencia": "Sin umbral, ni el modelo ni una persona clasifican igual dos veces. Los dos "
               "modelos que probamos fallan este ítem.",
  "decision": "Fijar los cortes y decidir si se añade «Sin porcentaje fijo / según mérito», "
              "que hoy es la respuesta más frecuente y no existe como opción."},
 {"n": 4, "titulo": "P4_Q5: opción «mixto»",
  "paneles": [4],
  "hoy": "Dos panelistas proponen letras los primeros años y aprobado/reprobado los últimos.",
  "evidencia": "Emily los etiquetó «Both: letter system, Pass/Fail», una categoría que la "
               "taxonomía no tiene.",
  "decision": "¿Se añade «Mixto (letras + aprobado/reprobado por etapa)»?"},
 {"n": 5, "titulo": "Unidades: qué se asume cuando alguien dice «8 horas»",
  "paneles": [1, 2, 3, 4],
  "hoy": "Si el panelista declara «8 horas al día» en una pregunta medida por semana, el "
         "sistema convierte (<b>×5</b> → 40). Si escribe «8 horas» a secas, toma la unidad de "
         "la pregunta y deja 8. El mismo texto vale 8 o 40.",
  "evidencia": "Es la causa de que los resultados numéricos no sean reproducibles: entre dos "
               "corridas del mismo código sobre los mismos datos, 4 de 12 preguntas numéricas "
               "cambiaron de etiqueta. Las categóricas no cambiaron ninguna.",
  "decision": "Escribir la regla: ante «8 horas» sin periodo, ¿se asume la unidad de la "
              "pregunta, se descarta la respuesta, o se vuelve a preguntar? <b>Es la decisión "
              "más urgente de las ocho.</b>"},
 {"n": 6, "titulo": "¿Puede asignarse banda sin número?",
  "paneles": [1, 3],
  "hoy": "Emily asignó bandas a respuestas que no dan ninguna cifra («restringir las prácticas "
         "a internos» → Mínima). El modelo lo tiene prohibido.",
  "evidencia": "Son 3 de los 9 desacuerdos que quedan con sus etiquetas.",
  "decision": "¿Se permite, y con qué regla escrita?"},
 {"n": 7, "titulo": "Bordes de las bandas",
  "paneles": [1, 3, 4],
  "hoy": "Las bandas 3-5 / 6-8 / &gt;9 dejan fuera valores como 5,5 y 8,5. Las de admisión "
         "(&lt;50 / 50 / &gt;50) mandan a «Alta» casi todo el Panel 3, cuyas respuestas van "
         "de 20 a 120.",
  "evidencia": "Ya se incorporó lo que Emily aclaró en sus notas para P1_Q6, P1_Q7, P3_Q5 y "
               "P3_Q8. Faltan P3_Q1 y P3_Q6, hoy asumidos por nosotros.",
  "decision": "Hacer los bordes contiguos y revisar las bandas de admisión."},
 {"n": 8, "titulo": "Taxonomía de argumentos",
  "paneles": [1, 2, 3, 4],
  "hoy": "Se clasifica <b>qué</b> responde cada panelista, pero no <b>por qué</b>. Las razones "
         "están en el texto y no se usan.",
  "evidencia": "Es lo que haría falta para mapear qué argumentos sostienen cada postura, que "
               "es el análisis más rico que permiten estos datos.",
  "decision": "Es el trabajo más grande y conviene empezarlo antes que los otros siete, "
              "aunque se cierre después."},
]

CAPAS = [
 ("Convertir las respuestas en etiquetas", "Listo", "ok",
  "Sin fallos de formato ni inconsistencias en toda la corrida.", "—"),
 ("Calcular el consenso de cada pregunta", "Listo", "ok",
  "Mediana y rango para las numéricas, distribución y n para las de opción.", "—"),
 ("Resultados numéricos", "No reportables", "block",
  "Dependen de qué se asume cuando el panelista no declara el periodo. Entre dos corridas "
  "idénticas, 4 de 12 cambiaron de etiqueta.", "<b>Emily</b> · decisión 5"),
 ("Definir qué cuenta como «consenso»", "Provisional", "wip",
  "Los umbrales actuales se fijaron mirando los datos. Hay que fijarlos con la literatura "
  "Delphi (acuerdo + estabilidad) <b>antes</b> de volver a mirar resultados.",
  "Pancho · 1 semana"),
 ("Saber si el sistema codifica tan bien como una persona", "A medias", "wip",
  "44 respuestas etiquetadas por una sola persona, repartidas entre los cuatro paneles: unas "
  "11 por panel. Si cada panel es un artículo, hace falta validar cada uno por separado.",
  "Emily + 2.º codificador"),
 ("Las razones que dan los panelistas", "Sin empezar", "todo",
  "Hay que construir una lista de argumentos —el porqué de cada postura— igual que se hizo "
  "con las opciones.", "Emily + Pancho · decisión 8"),
 ("El estudio real (eutanasia)", "Pendiente", "todo",
  "Confirmar el manejo de datos sensibles y definir la taxonomía del nuevo tema.",
  "<b>Jonathan</b>"),
]

# Lectura de la red de cada panel. Descripciones internas: no comparan un panel con otro,
# porque son estudios distintos con distintas preguntas.
LECTURA_RED = {
 1: "El grafo se mantiene ralo las tres rondas: los acuerdos fuertes no llegan a formarse. "
    "Conviene leerlo con cautela, porque es el panel donde más respuestas quedan sin "
    "clasificar (P1_Q3 al 86 %), así que parte de la falta de vínculos es de la taxonomía.",
 2: "El grafo pierde densidad entre la primera ronda y la última: el panel termina algo más "
    "repartido de lo que empezó.",
 3: "Se rompe y se rehace. En la ronda 2 el grupo inicial se deshace y en la 3 se reconstruye "
    "más denso que al principio. Esa forma no aparece en la tabla por pregunta.",
 4: "De un grafo casi vacío a uno denso: los vínculos fuertes aparecen ronda a ronda y los "
    "pares en desacuerdo desaparecen.",
}

NOTA_PANELES = (
 "Los cuatro paneles son <b>estudios independientes</b>: ningún panelista participa en más de "
 "uno, y de las 32 preguntas sólo una se repite entre paneles. Por eso cada uno tiene su "
 "página y no se agregan ni se comparan resultados entre ellos."
)
