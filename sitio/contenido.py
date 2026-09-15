# -*- coding: utf-8 -*-
"""
Texto editorial: lo único del sitio que no sale de Resultados/*.csv.

Todo lo demás —tablas, cifras, figuras— lo produce datos.py desde los CSV de la corrida.
Si un número aparece escrito aquí, es un bug.
"""

# Nota de contexto de la banda de corrida (build.py la pega después de los datos del
# manifiesto). Es temporal: cuando la corrida con GLM sea la referencia y no haya nada
# publicado de Gemma con qué confundirla, esta cadena se vacía y la banda queda sólo con los
# datos mecánicos.
NOTA_MODELO = (
 "La taxonomía es el documento «Posturas varias opciones» v2 de Emily. El modelo cambió: el "
 "servidor de la universidad dejó de servir Gemma, así que estos números <b>no son "
 "comparables</b> con las versiones anteriores de esta página, y la validación contra las "
 "etiquetas de Emily (κ = 0,72) se midió con el modelo anterior y hay que rehacerla."
)

# Aviso de la sección «Confiabilidad»: todo lo que hay ahí se midió con el modelo anterior.
# Se quita cuando las cuatro comprobaciones se rehagan con el modelo actual.
NOTA_CONFIANZA = (
 "<span class=\"ct\">Estas comprobaciones son del modelo anterior</span>"
 "<p>Las cuatro que siguen —acuerdo con la codificación manual, consistencia entre rondas, "
 "contraste con las síntesis y comparación entre modelos— se midieron con "
 "<code>google/gemma-4-12B-it</code>, que el servidor de la universidad ya no sirve, y contra "
 "la taxonomía anterior. Siguen describiendo cómo se comprueba el método, pero <b>no describen "
 "la corrida que produjo los números de arriba</b>. Rehacerlas con el modelo actual es parte "
 "de lo que falta, y en el caso del acuerdo con Emily hay que esperar además a que se cierren "
 "las decisiones de taxonomía: sus 44 etiquetas están hechas contra las opciones viejas.</p>"
)

# Estabilidad test-retest. Medido, no supuesto — y cambió al cambiar de modelo, así que el
# texto va aquí y no incrustado en la plantilla.
ESTABILIDAD = (
 "Dos corridas completas del mismo código sobre los mismos datos, a temperatura 0 y con semilla "
 "fija, difieren en el <b>5,8 % de las etiquetas</b>: 6 % de las categóricas, 5 % de las "
 "numéricas. No es un fallo del pipeline — el servidor agrupa peticiones en lotes de "
 "composición variable y la aritmética en coma flotante no es asociativa, así que el mismo "
 "texto puede recibir distinta etiqueta según con qué otras respuestas le tocó viajar."
)

ESTABILIDAD_CONSECUENCIA = (
 "Por eso <b>una corrida sola no es una medición</b>, sino una muestra de un clasificador "
 "estocástico. Lo que se publica aquí es el voto mayoritario de varias corridas, y cada "
 "respuesta lleva su grado de acuerdo entre ellas."
)

# Con el modelo anterior esto era distinto: las categóricas salían idénticas entre corridas y
# sólo se movían 4 de las 12 numéricas. Esa afirmación estuvo publicada y era correcta para
# Gemma; con GLM es falsa. Queda anotado para no volver a copiarla.

CERRADAS = (
 "La v2 del documento de posturas de Emily (14-09-2026) cerró cuatro de las ocho decisiones "
 "anteriores: la estructura anidada postura → calificador, que ahora viene declarada y ya no "
 "se reconstruye a mano; <b>P1_Q3</b>, retipificada en actividades más semestres; "
 "<b>P3_Q3</b>, con umbrales numéricos en vez de «alta / moderada / baja»; y <b>P4_Q5</b>, "
 "con la opción mixta por etapa. Esta corrida es la primera que usa esa taxonomía."
)

# Qué decisión de taxonomía afecta a qué panel. Sirve para que cada página diga sólo lo
# que le toca, en vez de repetirlas todas en las cuatro.
#
# El número que ve el lector NO se escribe aquí: lo da la posición en esta lista (build.py).
# Antes iba a mano y al reordenar por prioridad quedaron numeradas 1, 9, 2, 3... Van en orden
# de urgencia, así que reordenar es una operación normal.
DECISIONES = [
 {"titulo": "P4_Q8 se quedó sin rama «No»",
  "paneles": [4],
  "hoy": "«¿Debería la participación ser parte de la evaluación?» tiene «Yes» y cuatro "
         "calificadores, y nada más. Quien responde que no, no tiene dónde caer.",
  "evidencia": "Pasó de <b>0 % a 61 % sin clasificar</b> al aplicar la v2, y las catorce "
               "respuestas perdidas dicen lo mismo: «participation is too subjective», «it "
               "doesn't reflect the student's knowledge». Por el texto, el «no» parece ser la "
               "postura mayoritaria del panel — hoy la pregunta reporta consenso a favor "
               "construido sólo con los que dijeron que sí.",
  "decision": "Añadir la rama «No». Es una línea y recupera 14 de 23 respuestas: el cambio de "
              "mayor rendimiento del documento."},
 {"titulo": "P3_Q7 y P4_Q6: revisar si se clasificaron o se forzaron",
  "paneles": [3, 4],
  "hoy": "Las dos mejoraron mucho con la v2 —P3_Q7 de 55 % a 7 % sin clasificar, P4_Q6 de 25 % "
         "a 5 %—, pero quedar clasificada no es quedar bien clasificada.",
  "evidencia": "Cuando alguien escribe «PBL 50 %, examen 20 %, práctica 20 %» y el sistema lo "
               "mete en «Priority to PBL», se perdió una distribución entera. En P4_Q6, "
               "«socrática sólo en ciencias básicas» ahora encaja en «Yes, only in basic "
               "sciences», que puede ser un sí que el panelista no dijo.",
  "decision": "Revisar a mano las ~40 respuestas afectadas. Es lo que decide si estas dos "
              "preguntas se pueden reportar."},
 {"titulo": "Unidades: qué se asume cuando alguien dice «8 horas»",
  "paneles": [1, 2, 3, 4],
  "hoy": "Si el panelista declara «8 horas al día» en una pregunta medida por semana, el "
         "sistema convierte (<b>×5</b> → 40). Si escribe «8 horas» a secas, toma la unidad de "
         "la pregunta y deja 8. El mismo texto vale 8 o 40.",
  "evidencia": "En la corrida nueva, <b>25 respuestas</b> llegaron sin periodo declarado por el "
               "panelista. Donde el eje sí lo declara la ambigüedad se resuelve sola; donde no "
               "—<b>P3_Q1</b> (7 respuestas), <b>P2_Q3, P4_Q1 y P4_Q2</b>— el mismo texto puede "
               "valer 8 o 40. Es una fuente de irreproducibilidad que se suma a la del "
               "servidor, y a diferencia de aquélla no se arregla repitiendo la corrida: "
               "depende de una regla que sólo Emily puede escribir.",
  "decision": "Escribir el periodo en el nombre de esos cuatro ejes, como ya está hecho en los "
              "otros seis. <b>Sigue siendo lo más urgente de la capa numérica.</b>"},
 {"titulo": "P1_Q7: por día o por semana",
  "paneles": [1],
  "hoy": "La v2 declara el eje como «Numerical per week». La nota de Emily de agosto decía lo "
         "contrario: «calcular horas diarias con el promedio semanal, 20 h para 5 días».",
  "evidencia": "El enunciado de la pregunta dice «per week», así que esta corrida siguió a la "
               "v2. Cambia la mediana y la etiqueta de consenso de esa pregunta.",
  "decision": "Confirmar cuál de las dos vale. Es un conflicto entre dos fuentes de Emily, no "
              "una decisión de código."},
 {"titulo": "P1_Q3 y P2_Q1 se quedaron sin Sí/No",
  "paneles": [1, 2],
  "hoy": "La v2 puso el Sí/No explícito en once de las trece preguntas de postura, pero en "
         "estas dos no. En <b>P2_Q1</b> el «Yes» va dentro del texto de dos opciones y no hay "
         "ningún «No»: quien responde que no, no tiene dónde caer.",
  "evidencia": "En las dos, la taxonomía anterior sí tenía Sí y No, así que quitarlos es un "
               "retroceso respecto de lo que ya corría.",
  "decision": "¿Se añaden las ramas Sí/No, como en las otras once?"},
 {"titulo": "P3_Q3: falta «sin porcentaje fijo»",
  "paneles": [3],
  "hoy": "La v2 arregló los umbrales (máximo 10 / 20 / 30 %) y los criterios. Pero la respuesta "
         "más frecuente sigue sin existir como opción: varios panelistas dicen que no debería "
         "haber ninguna cuota —«is not a matter of rejecting them», «there should not be a "
         "mandatory or fixed amount»—.",
  "evidencia": "Es casi la mitad de las respuestas que hoy quedan fuera en esa pregunta.",
  "decision": "¿Se añade «Sin porcentaje fijo / según mérito»? Rechazar la premisa es una "
              "postura, no una respuesta inválida."},
 {"titulo": "Bordes y pisos de las bandas",
  "paneles": [1, 2, 3, 4],
  "hoy": "Las bandas 3-5 / 6-8 / &gt;=9 dejan fuera 5,5 y 8,5, y además <b>1 y 2 horas</b>, que "
         "no caen en ninguna banda. Las de admisión pasaron de tres cortes a dos "
         "(&lt;50 / &gt;=50), y el Panel 3 responde de 20 a 120.",
  "evidencia": "La solución ya está en el mismo documento: P3_Q5, P3_Q6 y P3_Q8 usan "
               "«&lt;=5», que cierra el piso. Basta con usarlo en todas.",
  "decision": "Hacer los bordes contiguos y revisar si dos bandas alcanzan para admisión."},
 {"titulo": "Taxonomía de argumentos",
  "paneles": [1, 2, 3, 4],
  "hoy": "Se clasifica <b>qué</b> responde cada panelista, pero no <b>por qué</b>. Las razones "
         "están en el texto y no se usan.",
  "evidencia": "Es lo que haría falta para mapear qué argumentos sostienen cada postura, que "
               "es el análisis más rico que permiten estos datos.",
  "decision": "Es el trabajo más grande y conviene empezarlo antes que los otros siete, "
              "aunque se cierre después."},
]

CAPAS = [
 ("Convertir las respuestas en etiquetas", "A medias", "wip",
  "El formato nunca falla, pero la etiqueta no es determinista: entre dos corridas idénticas "
  "cambia el 5,8 %. Se publica el voto mayoritario de varias corridas.", "Pancho · hecho"),
 ("Calcular el consenso de cada pregunta", "Listo", "ok",
  "Mediana y rango para las numéricas, distribución y n para las de opción.", "—"),
 ("Resultados numéricos", "No reportables", "block",
  "Dependen de qué se asume cuando el panelista no declara el periodo — una ambigüedad que "
  "repetir la corrida no resuelve, porque está en la taxonomía y no en el modelo.",
  "<b>Emily</b> · decisión 3"),
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

# Lectura de la cuadrícula de cada panel. Descripciones internas: no comparan un panel con
# otro, porque son estudios distintos con distintas preguntas. Sustituyeron a las lecturas de
# la red de acuerdo, que se retiró (promediaba el acuerdo sobre 2–5 preguntas por par).
LECTURA_RED = {
 1: "Lo primero que salta es la columna de Q3, casi entera en blanco: el 86 % de esas "
    "respuestas no encaja en ninguna opción de la taxonomía. Con las otras tres preguntas, "
    "las filas no llegan a parecerse: el parecido medio entre panelistas se queda entre 0,32 "
    "y 0,43 y no crece con las rondas.",
 2: "Es el panel con la taxonomía más limpia: casi no hay huecos y todas las preguntas se "
    "clasifican. Las filas se parecen entre sí de forma estable (0,45 → 0,46) sin acercarse "
    "ni separarse a lo largo de las tres rondas.",
 3: "Dos columnas con muchos huecos —Q7 al 55 % y Q3 al 45 % sin clasificar— y tres limpias. "
    "En las limpias las filas se van pareciendo: el parecido cae en la ronda 2 y termina más "
    "alto que al principio (0,49 → 0,40 → 0,54).",
 4: "El caso más claro de convergencia: las filas se parecen cada vez más entre rondas "
    "(0,36 → 0,55 → 0,61) y en la última varias columnas quedan de un solo color. Q5 y Q6 "
    "conservan un cuarto de huecos, que es lo que recogen las decisiones 4 y 1.",
}

NOTA_PANELES = (
 "Los cuatro paneles son <b>estudios independientes</b>: ningún panelista participa en más de "
 "uno, y de las 32 preguntas sólo una se repite entre paneles. Por eso cada uno tiene su "
 "página y no se agregan ni se comparan resultados entre ellos."
)
