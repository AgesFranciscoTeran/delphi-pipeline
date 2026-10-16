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
 "La taxonomía es el documento «Posturas varias opciones» v4 de Emily (27-09-2026), con los acuerdos del 15-10-2026. La "
 "validación contra sus etiquetas (κ = 0,72) se midió con el modelo anterior y contra las "
 "opciones viejas, y hay que rehacerla."
)

# Aviso de la sección «Confiabilidad»: todo lo que hay ahí se midió con el modelo anterior.
# Se quita cuando las cuatro comprobaciones se rehagan con el modelo actual.
NOTA_CONFIANZA = (
 "<span class=\"ct\">Una de las cuatro comprobaciones está rehecha con el modelo actual</span>"
 "<p>La consistencia está medida con <code>zai-org/GLM-5.3-Flash</code> y la taxonomía v4. Las "
 "otras tres se midieron con <code>google/gemma-4-12B-it</code>, que el servidor ya no sirve, y "
 "contra una taxonomía anterior: describen cómo se comprueba el método, pero <b>no la corrida "
 "que produjo los números de arriba</b>. Debajo de cada una se dice qué falta para rehacerla.</p>"
)

# Estabilidad test-retest. Medido, no supuesto — y cambió al cambiar de modelo, así que el
# texto va aquí y no incrustado en la plantilla.
ESTABILIDAD = (
 "Tres corridas completas del mismo código sobre los mismos datos, a temperatura 0 y con "
 "semilla fija, difieren en <b>entre el 2,8 y el 4,1 % de las etiquetas</b> según el par que se "
 "compare, en proporciones parecidas en las categóricas y en las numéricas; 41 de las 775 "
 "respuestas no reciben la misma etiqueta en las tres. No es un fallo del pipeline — el "
 "servidor agrupa peticiones en lotes de composición variable y la aritmética en coma flotante "
 "no es asociativa, así que el mismo texto puede recibir distinta etiqueta según con qué otras "
 "respuestas le tocó viajar."
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
 "El 15-10-2026, con Emily, se cerraron los criterios de consenso (ver «Cómo funciona» en la "
 "portada) y la taxonomía numérica: bandas contiguas en todas las preguntas de horas (antes 15 "
 "respuestas caían en huecos), una tercera banda en admisión (más de 80) con el 50 dentro de "
 "«More», y en <b>P1_Q7</b> se separan las horas de ABP, sobre las que se mide el consenso, del "
 "total semanal. Antes, la v3 y la v4 del documento habían cerrado <b>P4_Q8</b> (rama «No»), las "
 "<b>unidades</b> (la de <b>P3_Q1</b> la fijó el equipo en horas por día, porque el panel respondió "
 "así siguiendo la síntesis del facilitador), <b>P3_Q3</b> («No specific number») y <b>P2_Q1</b> "
 "(opciones de «No»). Las respuestas que no contestan la pregunta son «fuera de tema» y no "
 "cuentan en el consenso."
)

# Qué decisión de taxonomía afecta a qué panel. Sirve para que cada página diga sólo lo
# que le toca, en vez de repetirlas todas en las cuatro.
#
# El número que ve el lector NO se escribe aquí: lo da la posición en esta lista (build.py).
# Antes iba a mano y al reordenar por prioridad quedaron numeradas 1, 9, 2, 3... Van en orden
# de urgencia, así que reordenar es una operación normal.
DECISIONES = [
 {'titulo': 'P3_Q7 y P4_Q6: revisar si se clasificaron o se forzaron',
  'paneles': [3, 4],
  'hoy': 'Las dos ya no dejan respuestas sin clasificar y terminan con consenso fuerte, pero quedar clasificada no es quedar bien clasificada.',
  'evidencia': 'Cuando alguien escribe «PBL 50 %, examen 20 %, práctica 20 %» y el sistema lo mete en una sola opción de prioridad, se perdió una distribución entera. En P4_Q6, «socrática sólo en ciencias básicas» encaja en «Yes, only in basic sciences», que puede ser un sí que el panelista no dijo — y es justo la opción que gana la ronda final.',
  'decision': 'Revisar a mano las ~40 respuestas afectadas. Es lo que decide si estas dos preguntas se pueden reportar.'},
 {'titulo': 'Taxonomía de argumentos',
  'paneles': [1, 2, 3, 4],
  'hoy': 'Se clasifica <b>qué</b> responde cada panelista, pero no <b>por qué</b>. Las razones están en el texto y no se usan.',
  'evidencia': 'Es lo que haría falta para mapear qué argumentos sostienen cada postura, que es el análisis más rico que permiten estos datos.',
  'decision': 'Es el trabajo más grande y conviene empezarlo antes que los otros, aunque se cierre después.'},
]

CAPAS = [
 ("Convertir las respuestas en etiquetas", "Listo", "ok",
  "La etiqueta de una respuesta no es determinista, pero las conclusiones sí: se publica el "
  "voto mayoritario de tres corridas, las respuestas sin mayoría quedan sin clasificar, y la "
  "sección «Confiabilidad» muestra cuántas conclusiones cambiarían con una corrida sola.",
  "—"),
 ("Calcular el consenso de cada pregunta", "Listo", "ok",
  "Mediana y rango para las numéricas, distribución y n para las de opción. Las respuestas "
  "fuera de tema se cuentan aparte y no entran en el denominador.", "—"),
 ("Resultados numéricos", "Listo", "ok",
  "Unidades declaradas y bandas contiguas (acordadas el 15-10-2026). El consenso se mide sobre "
  "la banda, con el mismo criterio que las preguntas de opción.", "—"),
 ("Definir qué cuenta como «consenso»", "Listo", "ok",
  "Fijado a priori el 15-10-2026 con la literatura Delphi: acuerdo alto (≥ 70 %) y estable "
  "(cambio neto ≤ 15 % entre las dos últimas rondas). Se reporta también con 75 y 80 %.",
  "—"),
 ("Saber si el sistema codifica tan bien como una persona", "A medias", "wip",
  "44 respuestas etiquetadas por una sola persona, repartidas entre los cuatro paneles: unas "
  "11 por panel, y contra las opciones anteriores a la v4. Las hojas para la validación formal "
  "ya están generadas: 244 respuestas estratificadas por pregunta y ronda, ciegas, una por "
  "codificador. Falta que dos personas las etiqueten.",
  "Emily + 2.º codificador"),
 ("Las razones que dan los panelistas", "Sin empezar", "todo",
  "Hay que construir una lista de argumentos —el porqué de cada postura— igual que se hizo "
  "con las opciones.", "Emily + Pancho · taxonomía de argumentos"),
]

# Lectura de la cuadrícula de cada panel. Descripciones internas: no comparan un panel con
# otro, porque son estudios distintos con distintas preguntas. Sustituyeron a las lecturas de
# la red de acuerdo, que se retiró (promediaba el acuerdo sobre 2–5 preguntas por par).
# «Parecido medio»: para cada par de panelistas, la fracción de preguntas de opción que
# ambos tienen clasificadas en las que eligen la misma opción; promedio sobre todos los
# pares. Medido sobre Resultados_v4 (voto mayoritario de v4_k1..k3).
LECTURA_RED = {
 1: "Con la v4 ya no quedan huecos: todas las preguntas de opción se clasifican. Las filas se "
    "parecen poco en las dos primeras rondas y se acercan en la última: el parecido medio entre "
    "panelistas pasa de 0,26 a 0,20 y termina en 0,43.",
 2: "Todas las preguntas se clasifican; los huecos de Q4 son respuestas fuera de tema, que no "
    "contestan si la asistencia debe evaluarse. Las filas no convergen: el parecido medio baja "
    "levemente a lo largo de las tres rondas (0,37 → 0,35 → 0,31).",
 3: "Sin huecos en ninguna ronda, salvo una respuesta fuera de tema en Q7. Las filas se van "
    "pareciendo ronda a ronda (0,30 → 0,44 → 0,54).",
 4: "El caso más claro de convergencia: las filas se parecen cada vez más entre rondas "
    "(0,27 → 0,51 → 0,62) y en la última varias columnas quedan de un solo color. El único hueco "
    "relevante es Q5 en la primera ronda, un cuarto sin clasificar, que desaparece después.",
}

NOTA_PANELES = (
 "Los cuatro paneles son <b>estudios independientes</b>: ningún panelista participa en más de "
 "uno, y de las 32 preguntas sólo una se repite entre paneles. Por eso cada uno tiene su "
 "página y no se agregan ni se comparan resultados entre ellos."
)


# Criterios de consenso fijados el 15-10-2026 (docs/criterios_consenso.md). Va en «Cómo se
# obtienen los números».
CRITERIOS = (
 "<b>Qué cuenta como consenso.</b> Los criterios se fijaron a priori, desde la literatura "
 "Delphi y antes de recalcular los resultados. El acuerdo es el porcentaje del panel en la "
 "postura (en las preguntas de sí / no), la opción o la banda mayoritaria: alto desde 70 %, "
 "moderado desde 60 %, bajo desde 50 %. Hay <b>consenso</b> cuando el acuerdo es alto en la "
 "última ronda y además es <b>estable</b>: entre las dos últimas rondas cambió de opción, en "
 "neto, como mucho el 15 % del panel. Si el acuerdo es alto pero todavía se mueve, es consenso "
 "no consolidado; si no hay acuerdo pero el panel ya no se mueve, es disenso estable, que "
 "también es un resultado del Delphi."
)
