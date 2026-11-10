# Experimento: señales para decidir qué revisa una persona

**Diseño fijado el 9 de noviembre de 2026, antes de calcular ninguna señal.** Si algo cambia, se
anota aquí con fecha y motivo. Es una de las figuras centrales del artículo de método.

## Problema

El modelo generativo es una caja negra: dos corridas idénticas difieren en el 3-5 % de las
etiquetas, y cambiar de modelo cambia las etiquetas. Revisar a mano todo un Delphi anula la
ventaja del método. La pregunta es **qué señal (o combinación) identifica las respuestas en las
que el modelo probablemente se equivoca**, para que una persona revise sólo esas.

## Señales

| | Señal | Qué se calcula | Qué aporta | Límite conocido |
|---|---|---|---|---|
| S1 | Desacuerdo entre corridas (referencia) | cuántas de las k = 3 corridas coinciden | ya existe; independiente del modelo como procedimiento | depende del modelo; sólo 3 votos |
| S2 | Probabilidades del GLM | probabilidad de la opción elegida y margen sobre la segunda (logprobs) | alarma desde el mismo modelo que decide | no explica; hay que ver si la API las devuelve |
| S3 | Cita verificada | el modelo devuelve el fragmento literal que justifica la etiqueta; se comprueba que exista en el texto | explicatividad: una persona juzga la decisión en segundos | prueba que la cita existe, no que esté bien interpretada |
| S4 | *Embeddings* | ancla por opción (vector del texto de la opción); parecido de la respuesta con cada opción; si la etiqueta del GLM está entre las 2 más parecidas, y el margen | determinista y reproducible (modelo con versión fija) | mide el tema, no la postura: confunde «sí» y «no» sobre lo mismo |
| S5 | Rasgos atómicos | preguntas simples: ¿toma postura (sí / no / depende / ninguna)?, ¿da un número?, ¿dice «depende de…»?, ¿habla del tema de la pregunta? Alarma si la etiqueta contradice los rasgos | cada alarma se explica como una regla legible | más llamadas; las reglas hay que validarlas |

Descartadas por ahora: un segundo modelo generativo (mediría discrepancia entre modelos, sin
explicación) y NLI (requiere instalar un modelo; se retoma si S1-S5 no alcanzan).

## Qué deben predecir

1. **Inestabilidad entre corridas** (disponible ya): respuestas cuya etiqueta difiere entre las
   3 corridas de `Resultados_v4f`.
2. **Error contra personas** (cuando estén las hojas `validacion_v4_*`): respuestas en las que el
   voto del modelo difiere de la etiqueta humana. Es la prueba que cuenta para el artículo.

Ninguna señal se ajusta mirando el objetivo 2: los umbrales y la combinación se eligen con el
objetivo 1 o por validación cruzada.

## Figura

Curva de **esfuerzo contra error**, una por señal y una para la mejor combinación: eje
horizontal, % de respuestas revisadas (ordenadas de más a menos sospechosas); eje vertical, % de
errores detectados. Se reporta en la forma «revisando el X % se detecta el Y % de los errores»,
con el área bajo la curva y la curva de una revisión al azar como referencia.

## Dónde corre cada cosa

- S2, S3 y S5: llamadas al GLM desde spark-adi (API de TI).
- S4: `bge-m3` en el Ollama de la H200 (ya instalado; se registra la huella de versión del modelo).
- Análisis y figura: spark-adi.

## Para el texto del artículo

La auditabilidad no la da el *embedding*: es otra medición, más pobre, y sólo sirve como alarma.
La dan tres cosas verificables por cualquiera: (1) cada etiqueta con su cita textual, (2) una
regla medida que decide qué se revisa, (3) una persona que revisa esos casos.
