# Delphi Pipeline — Diagnóstico v2 (consolidado)

*Estado del análisis al 31 de agosto de 2026. Reemplaza al diagnóstico del 28 de agosto.*

*Aquel documento describía un sistema roto y proponía arreglarlo. El arreglo se hizo y se
comprobó; este documento describe el sistema arreglado. Lo que era la mitad del texto —el error
de índices y sus consecuencias— pasa a ser historia (§5) y anexo (§A), porque ya no es el estado
actual sino el motivo por el que ahora hay un procedimiento de control.*

*Evidencia: corrida completa del 30-08-2026 contra el H200 (`dataset_prueba.xlsx`, 786
respuestas, 32 preguntas, 4 paneles, 3 rondas), las 44 etiquetas ciegas de Emily,
`model_comparison.csv` con los dos modelos sobre esos mismos ítems, `run_manifest.json` y las
síntesis de los facilitadores. Todo lo cuantitativo aquí sale de esos archivos. Los juicios sobre
respuestas individuales son míos y no sustituyen la lectura de Emily.*

---

## 1. Veredicto

**La capa de medición ya es reportable.** La extracción, las métricas de consenso y la
reproducibilidad se reescribieron y pasaron los cuatro controles independientes de §3.3: acuerdo
κ 0,72 con la codificación manual de Emily, consistencia interna 100 %, coherencia con las
síntesis escritas por los facilitadores en las 20 preguntas categóricas, y equivalencia entre dos
modelos de familias distintas. Las cinco conclusiones invertidas del diagnóstico anterior
desaparecieron y ninguna nueva apareció.

**El cuello de botella ya no es técnico, es de taxonomía.** En la comparación cabeza a cabeza,
7 de los 8 errores del modelo elegido son exactamente los mismos ítems donde falla el otro modelo. Dos sistemas
distintos equivocándose en las mismas respuestas no es un problema de modelo: es que esas
respuestas son ambiguas frente a la taxonomía actual. Los 7 corresponden, uno a uno, a las ocho
decisiones que Emily tiene pendientes (§6). Ningún cambio de software los mueve.

**El título de trabajo apunta a un artículo visual y de redes, y eso cambia prioridades** (§8bis): la red que ese título pide —panelistas, no respuestas— sí se puede construir con lo que hay, y ya se construyó; muestra convergencia en dos de los cuatro paneles y un hallazgo sobre movimiento frente a convergencia. Lo visual, en cambio, está sin hacer.

**Dos capas siguen sin resolver y no dependen de Emily**: los criterios de consenso todavía son
provisionales, fijados por inspección y no a priori con la literatura Delphi (§7); y la capa de
argumentos —el "mapa" no supervisado— sigue mal planteada y hay que reconstruirla entera sobre
una taxonomía de argumentos (§8). Ninguna de las dos bloquea a la otra.

**El plan sigue siendo una v2 dirigida, no un proyecto nuevo.** Se conservó la infraestructura y
se reescribió lo que medía. La Fase 0 está cerrada; la Fase 1 está bloqueada por Emily; las
Fases 2 y 3 pueden empezar en paralelo.

---

## 2. Estado por capa

| Capa | Antes (28-08) | Ahora | Qué falta |
|---|---|---|---|
| Datos y preprocesamiento | 🟢 con parches | 🟢 | — 775 de 786 respuestas extraídas; las 11 restantes son vacías o de una palabra. Ya no se descartan respuestas por longitud. |
| Extracción LLM | 🔴 inválida | 🟢 | — 0 salidas con formato inválido en 775, 0 inconsistencias letra/texto, caché con clave (id, modelo, hash del prompt), manifiesto por corrida. |
| Consenso — cómputo | 🔴 no reportable | 🟢 | — entropía por K de la taxonomía, `pd.notna`, n mínimo, un solo denominador, mediana/IQR, unidades resueltas por regla. |
| Consenso — criterios | 🔴 sin definir | 🟡 provisionales | Fijar umbrales a priori con literatura Delphi (acuerdo + estabilidad entre rondas), y hacer `MIN_N` proporcional al tamaño del panel. **Fase 2.** |
| Taxonomía | 🟡 revisar con Emily | 🟡 sin cambios | Es ahora el cuello de botella. Ocho decisiones, §6. **Fase 1.** |
| Validación | 🟡 empezada | 🟡 suficiente para decidir, no para publicar | 44 ítems y un solo codificador. Faltan 200–300 ítems y un segundo codificador. **Fase 3.** |
| Capa de argumentos / red | 🔴 mal planteada | 🔴 sin tocar | Se retiró del pipeline en vez de arreglarse. Hay que rehacerla supervisada sobre taxonomía de argumentos. §8. |
| Figuras | 🟡 rediseñar | 🟢 las cuatro que quedan | fig1–fig4 rediseñadas; fig5–fig7 retiradas con las capas que las producían. |
| Reproducibilidad | 🔴 | 🟢 con matiz documentado | El determinismo no se puede afirmar; lo que hace reproducible el resultado es el caché archivado + manifiesto. §9. |

---

## 3. Lo que ya es reportable

### 3.1 Preguntas categóricas y posturas

Ronda final, 20 preguntas categóricas: 9 con consenso fuerte, 2 con mayoría clara, 7 con opción
dominante, 1 sin consenso (empate real 4/4 en P4_Q8) y 1 insuficiente (P1_Q3, con 1 de 7
respuestas clasificables). Cada etiqueta lleva su n y ninguna se emite por debajo del mínimo.

Sobre las 13 preguntas de sí/no/depende hay además una **lectura por postura**, recuperada de los
documentos "Posturas pregunta por pregunta 2.0" de Emily: esos PDFs traen las opciones anidadas
—nivel 1 la postura, nivel 2 los calificadores— y `taxonomy.py` las había aplanado en una lista
única. `stance_map.py` restituye la jerarquía y `stance_view.py` recalcula el consenso a ese
nivel, sin reextraer nada. Resultado: **8 de 13 con consenso fuerte de postura**, y varios casos
que a nivel de opción salían "sin consenso" resultan ser acuerdo de postura con desacuerdo de
matiz. El más claro es P2_Q7 (exámenes escritos en ABP): las 6 respuestas se reparten entre
calificadores distintos pero las 6 están a favor. El acuerdo con las etiquetas de Emily sube de
18/24 a 21/24 al leerlo así.

Esto es la evidencia empírica del punto 1 de la agenda de Emily: la estructura anidada mide mejor
que la lista plana, y ella ya la tiene escrita.

### 3.2 Preguntas cuantitativas

3 con consenso fuerte (P4_Q1, P4_Q2, P4_Q7), 4 con convergencia moderada, 4 sin consenso y 1
insuficiente. Se reportan mediana e IQR, no media y desviación: con paneles de 7 a 10 personas un
solo valor extremo mueve la media.

Tres advertencias que hay que mantener a la vista:

- **El Panel 1 responde estas preguntas de forma narrativa.** De 7 panelistas sólo 4 o 5 dan una
  cifra; el resto contesta con un criterio ("las horas necesarias para cubrir el programa"). Por
  eso P1_Q1 no alcanza el mínimo y P1_Q6 y P1_Q7 quedan justo en el límite (n=5). No es un fallo
  del análisis sino del instrumento, y es una pregunta para Emily: ¿esas tres preguntas son
  realmente numéricas?
- **En P3_Q1 y P3_Q6 la unidad la asumimos nosotros**, no está declarada. La "convergencia
  moderada" de P3_Q6 se apoya en ese supuesto: si la unidad fuera otra, el resultado cambia. Es
  el punto 5 de la agenda y la razón principal por la que esta tabla es preliminar.
- **Los "sin consenso" son dispersión real**, ya con las unidades convertidas — no el artefacto
  de unidades de la v1.

Los resultados numéricos son **preliminares** hasta que se cierren los puntos 5 y 6 de la agenda
(unidades y bordes de banda): las bandas actuales dejan huecos (3-5 / 6-8 / >9 no cubre 5,5 ni
8,5) y las de admisión (<50 / 50 / >50) mandan a "Alta" casi todo el Panel 3.

*(Estas cifras salen de `03_quantitative_consensus.csv` de la corrida del 30-08. Una versión
anterior de este documento y del sitio traía la tabla de una corrida intermedia, previa a la
resolución determinista de unidades; quedaba desactualizada en cinco de las doce filas.)*

### 3.3 Las cuatro comprobaciones

Ninguna es concluyente por sí sola. Juntas son la razón por la que §3.1 y §3.2 se pueden
reportar.

**1. Acuerdo con codificación manual ciega.** Emily etiquetó 44 respuestas sin ver la salida del
sistema. Sobre **la corrida que produjo los resultados de §3.1 y §3.2**: κ de Cohen = **0,72**
(IC 95 % bootstrap 0,57–0,84), acuerdo 75 %; 0,69 en preguntas de opción y 0,68 en banda
numérica. Está en el rango habitual de acuerdo entre codificadores en investigación cualitativa.
Con 44 ítems el intervalo es ancho: sirve para decidir, no para publicar.

Leyendo las mismas preguntas **a nivel de postura** (§3.1) el acuerdo sube de 18/24 a 21/24: tres
de los seis desacuerdos categóricos son de calificador dentro de la misma postura, no de fondo
("With passing exam" vs "With prior experience", "Yes" vs "Independent from Medicine", "Depends"
vs "According to the subject").

**Cuidado con qué κ se cita.** El 0,72 de arriba es el de la corrida principal. El 0,79 que
aparece en §4 es **el mismo modelo sobre los mismos 44 ítems, con el mismo prompt y los mismos
parámetros, en otra corrida**: difieren en 3 respuestas de 44. La diferencia no es un error de
cálculo, es la no-determinación entre corridas de §9, y es mayor de lo que parecía cuando se
estimó en 2 ítems. Para el paper: **el κ que certifica un resultado publicado es el de la corrida
que lo produjo**, y hay que decir de qué corrida sale cada cifra. Conviene además reportar la
dispersión entre corridas como una limitación medida, no descubrirla en revisión.

**2. Consistencia interna.** 30 panelistas repitieron su texto palabra por palabra entre rondas;
el sistema les asignó la misma etiqueta en los 30 casos (era 82 % en la v1). Es una prueba
gratuita que el diseño del estudio regala y que conviene reportar en el paper.

**3. Contraste con las síntesis de los facilitadores.** Las conclusiones coinciden con las
síntesis escritas a mano en las 20 preguntas categóricas. En dos casos la que se equivoca es la
síntesis humana: la de P4_Q3 afirma que el NBME debería ser requisito cuando las 8 respuestas
dicen lo contrario, y la de P4_Q8 declara acuerdo donde hay empate 4/4. Es, en sí mismo, un
argumento a favor de tener un registro auditable respuesta por respuesta, y probablemente el
mejor argumento de venta del paper.

**4. Dos modelos independientes.** Detalle en §4.

---

## 4. Decisión de modelo: Gemma

Los dos modelos sobre **los mismos 44 ítems que etiquetó Emily**, mismo prompt, `max_tokens`
ajustado por modelo.

| | Gemma 12B | DeepSeek-V4-Flash-0731 |
|---|---|---|
| **Todos (44)** | acuerdo 82 %, **κ 0,79** [0,66–0,92] | acuerdo 80 %, **κ 0,77** [0,62–0,89] |
| Nominal + binary (24) | 79 %, κ 0,74 [0,54–0,94] | 83 %, κ 0,79 [0,59–0,95] |
| Bandas (20) | 85 %, κ 0,80 [0,58–1,00] | 75 %, κ 0,68 [0,47–0,87] |
| Sin JSON válido | 0/44 | 1/44 |
| Latencia media | **0,3 s** | 2,7 s (rango 0,5–27 s) |
| Acuerdo entre modelos | 86,4 % | |

**En exactitud no hay diferencia detectable.** El patrón por tipo reproduce la intuición del
README v1 (DeepSeek algo mejor en opción, Gemma en banda), pero con n=24 y n=20 los intervalos se
solapan casi por completo. No sostiene una decisión y **menos aún el "routing híbrido" que se
barajaba**: duplicaría complejidad y coste por una diferencia que no se mide. Queda descartado
salvo que la muestra grande de la Fase 3 muestre una brecha real.

**La decisión es Gemma por lo operativo, que sí es concluyente:** 9× más rápido, latencia estable
(0,2–0,4 s frente a 0,5–27 s) y cero fallos de formato. Sobre el conjunto real (~22 000
respuestas, 8 workers) son ~15 minutos por pasada frente a ~2 horas, y la cola larga de DeepSeek
es un riesgo operativo en sí misma.

Nota sobre un mito heredado: la "inestabilidad de JSON de DeepSeek" que el README v1 daba por
característica del modelo era **presupuesto de tokens**. Es un modelo de razonamiento; con
`max_tokens=512` se queda sin margen a mitad del razonamiento y nunca llega a emitir el JSON. Con
2500 falla 1 de 44. No era el modelo.

**El hallazgo que más importa de esta comparación:** de los 8 errores de Gemma, **7 son
exactamente los mismos ítems que falla DeepSeek** (y 7 de los 9 de DeepSeek). Ahí está el techo
actual, y no es de software:

| Ítem | Qué pasa | Punto de la agenda |
|---|---|---|
| P1_Q1 "an hour per week" | respuesta en horas a una pregunta en semestres | 5 (unidad de pregunta vs. banda) |
| P1_Q1 "2do, 3ro, 4to y 5to año" | describe la duración sin dar cifra | 6 (banda sin número) |
| P1_Q4 "evaluar habilidades pedagógicas" | Emily quiere "con examen", pero de habilidades | 1 (calificadores) |
| P1_Q5 "Yes" vs "Independent from Medicine" | postura vs. calificador | 1 |
| P2_Q4 "Depends" vs "According to the subject" | opciones casi sinónimas | 1 |
| P3_Q3 "20 estudiantes rechazados" | sin umbrales de depuración | 3 |
| P3_Q6 "restringir a internos" | banda sin número | 6 |

---

## 5. Historia: el error de índices y cómo se encontró

Esta sección ya no describe el estado del sistema. Se conserva porque el episodio determina dos
cosas del paper: por qué existe el procedimiento de control de §3.3 y qué se puede afirmar
honestamente en la sección de métodos.

**El error.** El prompt enumeraba las opciones `1. … n.` y pedía un `option_index`. Gemma
respondía contando desde cero la mayoría de las veces; el código leía desde uno. La primera
opción se convertía en "sin clasificar" y todas las demás se corrían un lugar.

**Por qué era peligroso.** No producía ruido aleatorio ni errores visibles: producía un sesgo
sistemático con resultados de apariencia perfectamente razonable. Cinco conclusiones quedaron
invertidas —el panel decía "no" y el sistema reportaba "consenso fuerte: sí"— y las figuras se
veían bien. De los 10 "consenso fuerte" de la figura principal, 5 eran artefactos.

**Cómo se detectó.** Comparando la salida con las síntesis que los facilitadores habían escrito a
mano en su momento. Cuatro evidencias independientes convergieron: la última opción no aparecía
nunca en las preguntas de tres opciones (0 de 111); 7 de los 12 desacuerdos entre modelos eran un
corrimiento de exactamente −1; una auditoría manual de 36 clasificaciones daba 16 erróneas y 15
de ellas explicadas por el corrimiento; y 6 de los 12 errores de Gemma contra las etiquetas de
Emily eran exactamente su opción leída desde cero.

**El arreglo.** Se dejó de pedir números: las opciones se identifican por letra y el modelo
devuelve además el texto de la opción, que se verifica contra la lista. Si no encaja ninguna,
devuelve `NONE` explícito. En la corrida de control no hubo un solo caso de formato inválido ni
una sola inconsistencia entre letra y texto en 775 respuestas. El corrimiento no era uniforme —a
veces Gemma sí contaba desde uno—, así que no se podía corregir a posteriori: hubo que reextraer.

**Las cinco inversiones, antes y ahora:**

| Pregunta | v1 (con el error) | v2 (corrida de control) |
|---|---|---|
| P2_Q4 evaluar asistencia | Consenso fuerte: Sí | Opción dominante: No |
| P2_Q6 clases en fin de semana | Sólo en años clínicos | Mayoría clara: No |
| P4_Q3 NBME para graduarse | Junto con evaluación clínica | Consenso fuerte: No (8/8) |
| P3_Q10 turnos nocturnos | Años preclínicos (100 %) | Consenso fuerte: Años finales |
| P3_Q7 peso de cada materia | Igualdad entre materias (100 %) | Consenso fuerte: Prioridad a clínicas |

**La lección metodológica, que vale la pena escribir en el paper.** El contraste con las síntesis
humanas no formaba parte del plan original; ahora es un paso fijo del procedimiento. Un sistema
de codificación automática sin contraste humano sistemático puede estar equivocado de forma
consistente y verse impecable. Ése es exactamente el riesgo que un methods paper sobre
codificación asistida por LLM debería abordar de frente, y aquí hay un caso documentado con
evidencia.

**Un segundo episodio, más corto, con la misma moraleja.** Al arreglar las unidades se intentó
resolverlas por prompt ("no infieras el periodo"). Salió peor: el modelo mandó 93 respuestas a
`other`, incluidas muchas que sí declaraban periodo, y como el código asumía `other` en silencio,
"an hour per week" llegó a contar como **1 semestre** en P1_Q1. La solución final no le pregunta
la unidad al modelo: la deduce del texto crudo con una regla fija (`unit_from_raw`), y `other`
pasó a excluirse del consenso numérico en vez de asumirse. Se rescataron ~30 respuestas del texto
y 19 quedaron correctamente fuera. El κ no se movió (0,79), lo que confirma que el arreglo limpió
la contabilidad sin tocar lo que ya funcionaba. **Regla general que queda del episodio: lo que se
puede resolver con una regla determinista no se le pide al modelo.**

---

## 6. Abierto — taxonomía (bloquea la Fase 1; depende de Emily)

Ocho decisiones. Ninguna requiere saber programación; todas son sobre cómo debe estar definida la
taxonomía. El detalle con evidencia está en `claude/agenda-emily-fase1.md` y presentado para ella
en el sitio de resultados. Resumen:

1. **Separar postura de calificadores.** Hoy una sola lista excluyente mezcla ambas cosas. Ya
   está codificada la versión anidada de su propio documento y mide mejor (§3.1). Falta confirmar
   dos casos: "Replaced by clinical cases" cuelga de *Sí* en P2_Q7, y "According to the subject"
   cuelga de *Sí* en P4_Q8 pero de *Depende* en P2_Q4.
2. **P1_Q3 (DCI): volver a tipificar.** 86 % sin clasificar; los panelistas describen actividades
   en vez de elegir postura. ¿Dos capas (semestres + actividades) o una pregunta abierta?
3. **P3_Q3: umbrales de depuración.** "Alta / Moderada / Baja" sin números. En los datos hay
   20 %, 15 %, "menos del 10 %", "20 estudiantes" y tres personas que dicen que no debe haber
   porcentaje fijo — categoría que no existe y es la respuesta más frecuente.
4. **P4_Q5: opción "mixto".** Dos panelistas proponen letras los primeros años y
   aprobado/reprobado los últimos; Emily lo etiquetó como categoría nueva.
5. **Unidades y bordes de banda.** Bandas con huecos, bandas de admisión degeneradas, y P3_Q1 y
   P3_Q6 con unidad asumida por nosotros, no declarada por ella.
6. **¿Puede asignarse banda sin número?** Emily lo hace ("restringir las prácticas a internos" →
   Mínima); el modelo lo tiene prohibido. Son 3 de los 9 desacuerdos restantes.
7. **Panel 1: ¿son preguntas numéricas?** §3.2.
8. **Taxonomía de argumentos.** Es la entrada de §8 y la de más trabajo; conviene empezarla ya
   aunque las otras siete se cierren antes.

**Versiones.** Los PDFs 2.0 coinciden con lo codificado, pero la hoja de validación muestra que
el documento de trabajo de Emily ya fue más allá: para P1_Q3 usó una lista nueva y menciona "otra
mejor clasificación" para P3_Q3. Falta pedirle esos cambios; el resto está sincronizado.

---

## 7. Abierto — criterios de consenso (Fase 2; no depende de nadie)

Los umbrales actuales (`STRONG_AGREEMENT = 0,75`, `CLEAR_MAJORITY = 0,60`,
`DOMINANT_OPTION = 0,40`, `ENTROPY_DELTA = 0,05`) son **provisionales y se fijaron por
inspección**. Para el paper hay que fijarlos a priori con la literatura Delphi, y hay que
fijarlos **antes** de volver a mirar los resultados, no después: la crítica evidente es que se
eligieron los umbrales que daban las conclusiones deseadas, y la única defensa es el orden
cronológico.

Tres cosas concretas para esa fase:

- **Acuerdo + estabilidad.** El criterio CREDES no es sólo cuánta gente coincide en la ronda
  final, sino que la distribución se haya estabilizado entre rondas. Hoy se reporta la
  convergencia en cuatro clases pero no entra en la etiqueta de consenso.
- **`MIN_N` proporcional.** `MIN_N_CLASSIFIED = 5` es absoluto: exige 71 % de respuesta al Panel 1
  (n=7) y sólo 50 % al Panel 3 (n=10). Debe ser una proporción del panel.
- **Un solo criterio para tablas y figuras.** Ya se cumple en la v2, pero conviene dejarlo escrito
  como invariante y que un test lo verifique.

---

## 8. Abierto — capa de argumentos (Fase 1–2; el trabajo más grande)

Esta capa **se retiró del pipeline, no se arregló**. El diagnóstico anterior sigue vigente palabra
por palabra: el "mapa de argumentos" no supervisado no mapeaba argumentos, recuperaba el
cuestionario. NMI(cluster, pregunta) = 0,76; de 16 clusters, 10 eran ≥88 % una sola pregunta y el
mayor (31 % de los puntos) era "todas las preguntas de horas". El barrido de modularidad era
monótono, así que "máxima modularidad con grafo conexo" elegía el k más pequeño por construcción.
Las tres figuras que salían de ahí se retiraron con ella.

Lo que hay que construir en su lugar: una **taxonomía de argumentos** —las razones que dan los
panelistas, no las posturas— definida con Emily, y clasificación supervisada contra ella, igual
que la capa de opciones. El clustering *dentro de cada pregunta* con etiquetas del LLM sirve como
propuesta inductiva para construir ese codebook, es decir como herramienta de trabajo de Emily, no
como resultado publicable.

Es el punto 8 de la agenda y el que más calendario consume. Conviene arrancarlo antes de que se
cierren los otros siete.

---

---

## 8bis. El título de trabajo y la capa de red (31-08-2026)

El equipo apunta a **«Mapping the Evolution of Citizen Consensus: A Visual and Network Analysis
of Delphi Rounds»**. Contrastado con lo que hay:

| Pieza del título | Estado |
|---|---|
| Delphi Rounds | ✅ 3 rondas, panel estable — los 32 panelistas responden las tres |
| Consensus | ✅ medido y validado, por opción y por postura |
| Evolution | 🟡 calculado (10 de 20 preguntas convergieron, 2 se dispersaron) pero no era el sujeto del análisis |
| Network Analysis | ❌ retirada — pero ver abajo |
| Visual | ❌ fig1–fig4 son barras y tablas |
| Citizen | ❌ el conjunto de prueba son docentes y estudiantes de medicina |

**Rectificación sobre la capa de red.** §8 recomienda reconstruirla y, de facto, se había
retirado. Esa recomendación era correcta *sobre el objeto que construía la v1* —un grafo de
respuestas cuya estructura era la del cuestionario, NMI 0,76— pero es la recomendación
equivocada si la red está en el título. El error de la v1 no fue usar redes: fue elegir mal los
nodos. La pregunta «¿qué respuestas se parecen?» tiene una respuesta trivial. La pregunta que el
título hace es otra: **¿quién coincide con quién, y cómo cambia eso entre rondas?** Nodos =
panelistas, aristas = acuerdo. Es un objeto distinto y **no requiere la taxonomía de argumentos**:
se construye con lo que ya hay.

**Construida y medida** (`site/redes.py`, acuerdo = fracción de preguntas con la misma opción,
mínimo 3 preguntas en común por par):

| Panel | n | R1 | R2 | R3 | Trayectorias que cambian R1→R3 |
|---|---|---|---|---|---|
| 1 | 7 | 0,37 | 0,42 | 0,40 | 53 % |
| 2 | 7 | 0,55 | 0,52 | 0,49 | 42 % |
| 3 | 10 | 0,59 | **0,48** | 0,72 | 35 % |
| 4 | 8 | 0,43 | 0,67 | **0,75** | 19 % |

Tres lecturas, y la tercera es un hallazgo, no una figura:

1. **Panel 4 converge de manual** y los pares en desacuerdo fuerte pasan de 10 a 0.
2. **Panel 3 se parte y se reagrupa**: cae en la ronda 2 y sube por encima del inicio en la 3.
   Esa forma no aparece en ninguna tabla por pregunta — es exactamente el tipo de resultado que
   justifica el enfoque longitudinal del título.
3. **Moverse no es converger.** El 36 % de las trayectorias individuales cambia de opción entre
   R1 y R3, pero la relación con la convergencia es **inversa**: el panel que más se mueve
   (Panel 1, 53 %) no converge, y el que menos se mueve (Panel 4, 19 %) es el que más converge.
   Movimiento sin convergencia es rotación, no deliberación productiva. Distinguir las dos cosas
   requiere datos por panelista y por ronda, que es justo lo que este pipeline produce y lo que
   una síntesis de facilitador no puede dar.

**La limitación, y qué implica para la estructura del artículo.** Con 7–10 nodos por panel esto
es una demostración legible a ojo, no estadística de redes: centralidad y modularidad son
inestables a ese tamaño y no deben reportarse como resultado. La red con tamaño suficiente es la
del conjunto de eutanasia. La estructura natural queda entonces: **currículo médico como banco de
pruebas del método, eutanasia como la aplicación ciudadana** — que es lo que el proyecto ya era,
y ahora además es lo que el título exige.

**Consecuencia sobre las prioridades de §7 y §8.** La capa de argumentos (§8) sigue siendo el
trabajo más grande y sigue dependiendo de Emily, pero **ya no bloquea la parte de red del
artículo**: hay una red publicable sin ella. Eso cambia el orden: las figuras de evolución y la
red de panelistas pueden hacerse ahora, en paralelo con la Fase 1, en vez de esperar a que se
cierre la taxonomía de argumentos.

**Menú de análisis propuesto** (presentado a Emily y Jonathan en la sección 4 del sitio, porque
lo que pidieron fue ideas):

| Análisis | Estado |
|---|---|
| Red de panelistas por ronda | hecha |
| Flujo de opiniones entre rondas (alluvial por pregunta) | se puede ya — 36 % de movimiento |
| Trayectoria de consenso por pregunta | se puede ya — calculado, falta la figura |
| Movimiento frente a convergencia | se puede ya — es el hallazgo 3 |
| Red de posturas que viajan juntas | requiere la decisión 1 |
| Red de argumentos | requiere la decisión 8 |
| Panelistas que arrastran al panel | posible pero no fiable con n=7–10 |

## 9. Reproducibilidad y escala

**Lo que se puede afirmar.** El pipeline archiva el caché de extracción y un manifiesto por
corrida (modelo e id exacto, hash de la taxonomía, versión del prompt, fecha, parámetros). Con
esos dos archivos cualquiera reproduce las tablas y figuras exactamente.

**Lo que no se puede afirmar: determinismo.** Entre la corrida principal y la de comparación, con
el mismo prompt, `temperature=0` y `seed` fijo, Gemma cambió de etiqueta en **3 de 44 ítems
(~7 %)**, lo que mueve el κ de 0,72 a 0,79 (§3.3). El test-retest da 100 % *dentro* de una
corrida, pero vLLM con batching continuo no es determinista bit a bit *entre* corridas: la
composición del lote altera el orden de reducción en coma flotante. **En métodos hay que decir
esto explícitamente** y apoyar la reproducibilidad en los artefactos archivados, no en afirmar
`temperature=0`. Afirmar determinismo es una objeción regalada a un revisor que sepa cómo
funciona vLLM.

Y hay una consecuencia práctica para la Fase 3, no sólo de redacción: con 44 ítems, 3 cambios
mueven el κ 0,07 puntos — más que la diferencia entre los dos modelos (0,02). **La variación
entre corridas es hoy mayor que el efecto que se quería medir.** El diseño de la validación
formal debería, o bien correr cada condición varias veces y reportar la dispersión, o bien fijar
la comparación sobre una única corrida archivada por modelo y decirlo. Con 200–300 ítems el ruido
relativo baja, pero no desaparece.

**Escala.** Las 775 respuestas se extrajeron en 38 segundos con 8 workers. Sobre 22 000
respuestas eso son ~15 minutos por pasada, lo que hace barato reprocesar el conjunto entero cada
vez que cambie la taxonomía — que es justo lo que va a pasar varias veces en la Fase 1. La
restricción real del conjunto de eutanasia no es cómputo sino manejo de datos sensibles: todo
tiene que quedarse en infraestructura institucional, cosa que ya se cumple, pero conviene
confirmarla formalmente con Jonathan antes de empezar y no después.

---

## 10. Plan y criterios de salida

| Fase | Estado | Contenido | Criterio de salida |
|---|---|---|---|
| **0 — Integridad** | ✅ **Cerrada** (30-08) | Extracción, métricas, unidades, reproducibilidad. | Cumplido: 20/20 veredictos coherentes y 0 invertidos (meta ≥16); κ nominal 0,69 (meta ≥0,65); test-retest 100 % (meta ≥95 %). |
| **1 — Taxonomía v2** | 🔒 Bloqueada por Emily | Las ocho decisiones de §6 + taxonomía de argumentos (§8). | Taxonomía v2 firmada; sin clasificar residual < 10 % y explicado. |
| **2 — Criterios y figuras** | Puede empezar ya | §7. Umbrales a priori con literatura Delphi, `MIN_N` proporcional, figuras finales. | Criterios fijados y escritos **antes** de mirar resultados; ninguna etiqueta por debajo del n mínimo. |
| **3 — Validación formal** | Depende de un 2.º codificador | 200–300 respuestas estratificadas, dos codificadores ciegos, acuerdo humano–humano como techo, validación agregada además de por ítem. | κ LLM–humano dentro del intervalo humano–humano; veredictos de consenso idénticos en ≥90 % de preguntas-ronda. |
| **4 — Conjunto real** | Pendiente | Eutanasia, ~22 000 respuestas. | Manejo de datos confirmado con Jonathan; taxonomía del nuevo dominio. |

Las Fases 1, 2 y 3 no son secuenciales: la 2 no depende de nadie y la 3 sólo depende de conseguir
el segundo codificador. Lo único estrictamente encadenado es que la validación formal debe
hacerse sobre la taxonomía v2, no sobre la actual.

---

## 11. Riesgos

**El segundo codificador.** Sin acuerdo entre dos personas no hay techo contra el cual juzgar al
sistema, y κ 0,72 contra una sola codificadora no responde la pregunta "¿es esto tan bueno como
un humano?". Es la dependencia externa que conviene resolver antes; un revisor la va a pedir.

**Potencia de la validación.** 44 ítems dan intervalos de ±0,13. Sirven para decidir el modelo,
no para publicar. La Fase 3 lo resuelve.

**Afirmar determinismo.** §9. Es un riesgo de redacción, no de código, y se elimina escribiendo
bien la sección de métodos.

**Paneles pequeños.** De 7 a 10 personas: cada panelista mueve entre 10 y 14 puntos porcentuales.
Por eso se reporta el n junto a cada resultado y no se etiqueta consenso por debajo de un mínimo.
Es una limitación del estudio, no del análisis, pero debe estar dicha.

**Datos sensibles.** El conjunto de eutanasia exige que todo se quede en infraestructura
institucional. Ya se trabaja así; falta confirmarlo formalmente.

**Publicar sin la Fase 1.** Los resultados numéricos y varias etiquetas categóricas cambiarán
cuando se cierren las decisiones de taxonomía. Nada de §3 debería ir a un manuscrito como
definitivo antes de eso; sirve para presentar el estado del método, no para reportar las
conclusiones del panel.

---

## Anexo A — Hallazgos de la v1 ya cerrados

Se listan para que quede el registro de qué se arregló y no haya que volver a diagnosticarlo.

| Hallazgo v1 | Cómo se cerró |
|---|---|
| Índices base 0 vs base 1 | Opciones por letra + `NONE` + verificación cruzada del texto. 0 fallos en 775. §5 |
| Caché contaminado (750 extracciones de un modelo, 17 de otro, misma clave) | Clave = (response_id, modelo, hash del prompt). |
| Sin `temperature` ni `seed` | Fijados; y documentado que no bastan (§9). |
| Unidades convertidas por el modelo de forma inconsistente | Resueltas por regla determinista sobre el texto crudo; `other` excluido. §5 |
| Entropía normalizada por opciones *usadas* | Normalizada por K opciones de la taxonomía. |
| `NaN` contado como categoría | `pd.notna`. |
| Sin n mínimo (una etiqueta "consenso fuerte" con n=1) | `MIN_N_CLASSIFIED` y `MIN_N_NUMERIC`, con la etiqueta "Insuficiente". |
| Dos denominadores distintos entre tabla y figura | Uno solo, y el n visible en cada fila. |
| Empates reportados como opción dominante | Detección de empate: "Sin consenso — Empate: A / B". |
| Campos `certainty` y `references_synthesis` inventados por el modelo | Eliminados del esquema. Quedan como anécdota de diagnóstico: `references_synthesis = "yes"` en el 52 % de la ronda 1, cuando aún no existía ninguna síntesis. |
| `preprocess.py` no creaba `Resultados/` | `makedirs`. |
| Filtro de longitud descartaba respuestas válidas ("80", "8 per week") | Retirado; válida = tiene texto. |
| Extracción secuencial (~5 h estimadas para el conjunto real) | 8 workers; 38 s para 775 respuestas. |
| `python-louvain` no compila | La capa que lo usaba se retiró (§8); la dependencia desaparece. |
| `score_validation.py` citado en el README pero inexistente | Escrito. Es lo que produce los κ de §3.3 y §4. |
| fig5–fig7 (barrido de modularidad, mapa de argumentos, diversidad por ronda) | Retiradas con la capa que las producía. |

---

## Anexo B — Qué corre hoy

```
v2/
  config.py              parámetros y criterios (los de consenso, provisionales — §7)
  taxonomy.py            taxonomía de Emily + unidades por pregunta + hash
  preprocess.py          limpieza; 775 de 786 respuestas válidas
  classify_questions.py  tipo de pregunta (nominal / binary / quantitative / hybrid)
  extract_arguments.py   extracción por letras + NONE, caché, concurrencia, manifiesto
  consensus_metrics.py   entropía por K, mediana/IQR, unidades por regla, empates, convergencia
  stance_map.py          estructura anidada postura → calificadores (13 preguntas)
  stance_view.py         consenso a nivel de postura sobre la extracción existente
  visualize.py           fig1–fig4
  audit_vs_synthesis.py  cruce pipeline × síntesis del facilitador × respuestas crudas
  compare_models.py      dos modelos sobre los mismos ítems etiquetados
  score_validation.py    κ con IC bootstrap contra las etiquetas humanas
  tests/test_phase0.py   32 tests, uno por hallazgo cerrado del Anexo A
  RUNBOOK_FASE0.md       procedimiento de corrida
```

El sitio de resultados para Emily y Jonathan se genera con `site/build.py`.

*Fuera del pipeline:* `network.py` (v1) queda archivado como evidencia del diagnóstico; no se
migró y no debe volver tal como está (§8).
