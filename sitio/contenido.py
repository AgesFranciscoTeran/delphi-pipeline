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
 "La taxonomía es el documento «Posturas varias opciones» v4 de Emily (27-09-2026). La "
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
 "Las versiones v3 y v4 del documento de Emily cerraron cuatro de las ocho decisiones "
 "anteriores. <b>P4_Q8</b> tiene rama «No». Las <b>unidades</b> están declaradas en todas las "
 "preguntas de horas; la de <b>P3_Q1</b> la fijó el equipo en horas por día, porque aunque la "
 "encuesta preguntaba por semana, el panel respondió por día siguiendo la síntesis del "
 "facilitador. <b>P3_Q3</b> tiene «No specific number» para quien rechaza una cuota fija. Y "
 "<b>P2_Q1</b> ya tiene opciones de «No», así que deja de perder respuestas (sin ramas marcadas "
 "todavía no entra en la vista por postura). Además, las respuestas que no contestan la "
 "pregunta tienen su propia categoría, «fuera de tema», que no cuenta en el consenso."
)

# Qué decisión de taxonomía afecta a qué panel. Sirve para que cada página diga sólo lo
# que le toca, en vez de repetirlas todas en las cuatro.
#
# El número que ve el lector NO se escribe aquí: lo da la posición en esta lista (build.py).
# Antes iba a mano y al reordenar por prioridad quedaron numeradas 1, 9, 2, 3... Van en orden
# de urgencia, así que reordenar es una operación normal.
DECISIONES = [
 {"titulo": "Bordes y pisos de las bandas",
  "paneles": [1, 2, 3, 4],
  "hoy": "Con las unidades ya declaradas, es lo que falta para que la capa numérica sea "
         "reportable. Las bandas 3-5 / 6-8 / &gt;=9 dejan fuera 5,5 y 8,5, y además <b>1 y 2 "
         "horas</b>, que no caen en ninguna banda. En P4_Q1 y P4_Q2 el tope es «&gt;9», así que "
         "9 horas tampoco cae. Las de admisión tienen dos cortes (&lt;50 / &gt;=50), y el Panel 3 "
         "responde de 20 a 120.",
  "evidencia": "La solución ya está en el mismo documento: P3_Q5, P3_Q6 y P3_Q8 usan "
               "«&lt;=5», que cierra el piso. Basta con usarlo en todas.",
  "decision": "Hacer los bordes contiguos (y «&gt;=9» en el Panel 4) y revisar si dos bandas "
              "alcanzan para admisión."},
 {"titulo": "P1_Q7: ¿horas totales o horas de ABP?",
  "paneles": [1],
  "hoy": "La unidad está resuelta: el panel responde por semana, como pregunta el enunciado. "
         "Pero responde a dos cosas distintas. Unos dan el <b>total semanal</b> (20–30 horas) y "
         "otros sólo las <b>horas de ABP</b> (6–7 horas).",
  "evidencia": "Las bandas 3-5 / 6-8 / &gt;=9 sólo tienen sentido para lo segundo: cualquier "
               "total cae en «Intensive». La síntesis de la ronda 3 lo cierra hablando del "
               "sistema actual, «2 horas de ABP tres veces a la semana» más una o dos de "
               "complementarias.",
  "decision": "¿La pregunta mide las horas totales o las de ABP? Si son las totales, las bandas "
              "hay que reescalarlas."},
 {"titulo": "P3_Q7 y P4_Q6: revisar si se clasificaron o se forzaron",
  "paneles": [3, 4],
  "hoy": "Las dos ya no dejan respuestas sin clasificar y terminan con consenso fuerte, pero "
         "quedar clasificada no es quedar bien clasificada.",
  "evidencia": "Cuando alguien escribe «PBL 50 %, examen 20 %, práctica 20 %» y el sistema lo "
               "mete en una sola opción de prioridad, se perdió una distribución entera. En P4_Q6, "
               "«socrática sólo en ciencias básicas» encaja en «Yes, only in basic sciences», que "
               "puede ser un sí que el panelista no dijo — y es justo la opción que gana la ronda "
               "final.",
  "decision": "Revisar a mano las ~40 respuestas afectadas. Es lo que decide si estas dos "
              "preguntas se pueden reportar."},
 {"titulo": "Taxonomía de argumentos",
  "paneles": [1, 2, 3, 4],
  "hoy": "Se clasifica <b>qué</b> responde cada panelista, pero no <b>por qué</b>. Las razones "
         "están en el texto y no se usan.",
  "evidencia": "Es lo que haría falta para mapear qué argumentos sostienen cada postura, que "
               "es el análisis más rico que permiten estos datos.",
  "decision": "Es el trabajo más grande y conviene empezarlo antes que los otros, aunque se "
              "cierre después."},
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
 ("Resultados numéricos", "Preliminares", "wip",
  "La unidad ya está declarada en todas las preguntas de horas. Falta que los bordes de las "
  "bandas sean contiguos: hoy 1–2 horas, 5,5 y 8,5 no caen en ninguna.",
  "<b>Emily</b> · bordes de las bandas"),
 ("Definir qué cuenta como «consenso»", "Provisional", "wip",
  "Los umbrales actuales se fijaron mirando los datos. Hay que fijarlos con la literatura "
  "Delphi (acuerdo + estabilidad) <b>antes</b> de volver a mirar resultados.",
  "Pancho · 1 semana"),
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
