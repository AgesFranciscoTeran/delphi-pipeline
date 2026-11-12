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

## Bitácora

**10-11-2026 — etapa 1, sin llamadas al GLM** (`tools/senales.py Resultados_v4f`, salida en
`Resultados_v4f/senales/`). Cambios al diseño, todos decididos mirando sólo el objetivo 1:

- Las señales se calculan sobre **una sola corrida (k1)**; el objetivo 1 es que la etiqueta del
  eje principal cambie entre k1, k2 y k3. Así la pregunta es práctica: ¿una corrida más alarmas
  baratas reemplaza a correr tres veces?
- **S0** (longitud de la respuesta) como línea base trivial.
- **S3p**: versión provisional de S3 con las `key_phrases` que ya devuelve la extracción
  (parecido aproximado, porque el modelo corrige erratas al citar). No es la cita que justifica
  la etiqueta; S3 completa sigue pendiente.
- **S4**: bge-m3 (huella `790764642607…`). Ollama devuelve NaN para algunos textos; regla fija:
  se prueban variantes sin cambio de contenido (sin puntuación final, espacio o salto al final);
  10 textos quedan sin vector.
- **R (reglas de código)**, nuevas tras mirar las 42 inestables: R1 = pregunta cuantitativa, el
  texto tiene un número y la corrida no asignó banda; R2 = la opción elegida tiene una versión
  general o específica en la taxonomía («No» / «No, subjective…»).

Resultado (775 respuestas, 42 inestables = 5,4 %; AUC y % de inestables detectadas revisando el
20 %): S0 0,50 / 17 %; S3p 0,53 / 19 %; S4 0,55 / 19 %; R 0,62 / 38 %; combinación con validación
cruzada 0,57 / 26 %. En categóricas (435, 21 inestables) R llega a 0,66 / 43 % y S4 a 0,57 / 29 %.

Lectura: la mitad de las inestables son números que alguna corrida no lee (problema del
pipeline, no de interpretación) y la otra mitad, dudas entre una opción general y su versión
específica (problema de la taxonomía). Los *embeddings* no ven ninguna de las dos. Límite de
fondo: con una sola corrida sólo se detecta el fallo de esa corrida, no el de las otras.

S2: la API de TI devuelve `logprobs` (con `top_logprobs`), pero incluye los tokens del
razonamiento; hay que tomar el de la letra dentro del JSON final.

**12-11-2026 — etapa 2, señales del GLM** (corrida `Resultados_v4f_k4`: mismo prompt que v4f,
con logprobs; S3 y S5 en llamadas aparte, k = 1; `tools/senales.py Resultados_v4f --corrida
Resultados_v4f_k4`, salida en `Resultados_v4f/senales_Resultados_v4f_k4/`). Terminó el 10-11 sin
fallos (775/775). Dos objetivos: *inestable* (la etiqueta cambia entre k1..k4; 52 = 6,7 %) y
*se aparta* (k4 no coincide con el voto de k1..k3; 24 = 3,1 %).

AUC / % detectado revisando el 20 % (todas las respuestas):

| Señal | inestable | se aparta |
|---|---|---|
| S0 longitud | 0,51 / 17 % | 0,50 / 12 % |
| S3p frases clave | 0,52 / 17 % | 0,53 / 21 % |
| S4 *embeddings* (sólo categóricas) | 0,60 / 41 % | 0,61 / 40 % |
| R reglas de código | 0,63 / 36 % | 0,60 / 42 % |
| S2 probabilidades | 0,61 / 36 % | 0,56 / 25 % |
| S3 cita verificada | 0,59 / 31 % | 0,56 / 29 % |
| S5 rasgos | 0,59 / 33 % | 0,58 / 29 % |
| Combinación (VC) | 0,68 / 44 % | 0,52 / 33 % |

- **S2 está saturada**: tras razonar, el margen de logprob nunca baja de 5 (p ≥ 0,99; mediana
  13). Ordena algo, pero no hay respuestas «dudosas» para el modelo.
- **S3**: en 36 respuestas el modelo dice que *nada* del texto sostiene la etiqueta asignada;
  10 son inestables (28 %, cuatro veces la tasa base). Es la alarma más explicable.
- **S5**: 75 alarmas (9,7 %), 14 inestables (19 %, casi tres veces la tasa base).
- Ninguna señal de una sola corrida reemplaza a las k corridas: la mejor combinación detecta
  menos de la mitad de las inestables revisando el 20 %. Con 24 positivos, *se aparta* es muy
  ruidoso (la combinación con validación cruzada cae a 0,52).

Pendiente: objetivo 2 (error contra las etiquetas de Emily), que es la prueba que cuenta.
