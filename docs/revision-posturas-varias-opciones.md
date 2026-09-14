# Revisión — «Posturas varias opciones» v2 (documento de Emily, 14-09-2026)

Contraste de la **segunda versión** contra la primera (8-09-2026) y contra la taxonomía que corre
hoy en `pipeline/taxonomy.py` y `pipeline/stance_map.py`. Las 32 preguntas emparejaron por texto en
las dos versiones, así que la comparación es completa.

| | v1 | v2 |
|---|---|---|
| Ejes declarados | 51 | **65** |
| Opciones | 175 | **205** |
| Preguntas que cambian | — | **17 de 32** |
| Preguntas de postura con Sí/No explícito | 3 de 13 | **11 de 13** |

---

## Lo principal: la estructura no es de ejes paralelos, es un árbol

En la v1 leí las preguntas como si tuvieran varios ejes **en paralelo**, y sobre eso pedí
confirmación. La v2 aclara que no es eso. Lo que hay es **anidación**: primero la postura, y los
calificadores cuelgan de una postura concreta.

Se ve limpio en P3_Q4 («¿es el ABP un buen método?»), donde la v1 tenía todo en una lista plana y
la v2 lo parte en dos celdas:

```
v1   Nominal: Yes | No | Only as complement | Only in clinical subjects |
              Only with trained tutors | Only in certain years

v2   - Yes → Only as complement | Only in clinical subjects |
             Only with trained tutors | Only in certain years
     - No  → (sin calificadores)
```

Esto importa mucho, y en la dirección buena: **es exactamente la estructura que
`pipeline/stance_map.py` ya reconstruye a mano.** Ese módulo existe porque los PDFs de agosto
tenían las opciones anidadas y `taxonomy.py` las aplanó; el mapa deshace el aplanamiento opción por
opción. Con la v2, la anidación viene declarada en el propio documento: el puente hecho a mano se
puede retirar y la taxonomía pasa a llevar la estructura.

También responde la pregunta bloqueante de la revisión anterior. Era (a): **el Sí/No no había
desaparecido**, faltaba escribirlo. Ahora está explícito en 11 de las 13 preguntas de postura
(antes en 3). La capa de postura —hoy el resultado más sólido que tenemos— no se pierde.

**Consecuencia para el código:** clasificar en dos pasos, no en uno. Primero la postura, después el
calificador *de esa rama*. Es más simple que la versión de ejes paralelos que había supuesto, y le
da al modelo una lista más corta en cada llamada, que es justo donde se equivoca hoy.

Un detalle de formato: las opciones vienen con guion inicial (`- Yes`, `- No`) y nueve celdas de
rama «No» quedaron sin etiqueta de tipo, porque son la continuación de la celda de arriba. Se
normaliza al leer; no es un problema de contenido.

---

## Lo que la v2 cierra

**Decisión 4 — sistemas de calificación mixtos (P4_Q5).** Resuelta. Aparece el eje que faltaba:
*Combined* → «First years: Numeric system / Last years: Pass-Fail» y «First years: A-F / Last years:
Pass-Fail». Coincide literalmente con lo que escribieron los panelistas, que era el 25 % sin
clasificar de esa pregunta.

**Los dos marcadores `mmmmm`.** Llenados: P4_Q1 → «Depends on the subject», P4_Q2 → «Depends on the
tutors».

**P2_Q7, la rareza pendiente en `stance_map.py`.** El docstring pedía confirmar si «Replaced by
clinical cases» colgaba de *Sí*. En la v2 cuelga de **No**, que es lo que tenía sentido. Queda
cerrado.

**P3_Q10 — turnos nocturnos.** Los tres momentos ahora llevan el rango de años escrito: First
years (1-2) / Preclinical (3-4) / Final (5-6). Deja de depender de que el modelo y el panelista
entiendan lo mismo por «preclinical».

**P2_Q5 — unidad explícita.** «Numerical per month» pasa a «Numerical **sessions** per month». Es un
cambio de una palabra y quita la ambigüedad entre sesiones y horas.

**P3_Q6** gana un eje nominal que faltaba (depende de la materia / de la disponibilidad de tutores).

---

## Lo que sigue abierto

### 1. P3_Q7 no cambió, y ahora es la peor (55 % sin clasificar)

«¿Qué peso debería tener cada materia?» conserva las siete opciones nominales de la v1, sin tocar.
El problema es que los panelistas **responden con números** —porcentajes y créditos— y no hay ningún
eje numérico donde ponerlos. Mientras siga así, más de la mitad de las respuestas de esa pregunta se
quedan fuera del análisis, hagamos lo que hagamos con el resto.

Es el punto más rentable del documento: un eje de porcentaje o de créditos recupera unas veinte
respuestas de golpe.

### 2. P1_Q3 y P2_Q1 se quedaron sin Sí/No

Las dos que faltan de las trece. En las dos el pipeline **sí** tiene Sí y No hoy (`stance_map.py`),
así que quitarlos es un retroceso respecto de lo que ya corre:

- **P2_Q1** («¿es el ABP apropiado?») tiene el «Yes» metido dentro del texto de dos opciones («Yes,
  supplemented with lecture classes») y no tiene «No» por ningún lado. Un panelista que responde
  que no, no tiene dónde caer.
- **P1_Q3** (DCI) es la pregunta que estaba al 86 % sin clasificar. La v1 le añadió los seis ejes
  nominales y el eje de semestres, que era lo que hacía falta, pero sin postura queda a medias.

### 3. Cuatro ejes de horas sin periodo declarado

P2_Q3 (pregunta por día), P3_Q1 (por semana), P4_Q1 y P4_Q2 (por día) dicen sólo «Numerical». Es la
decisión 5, la que hace que la capa numérica no sea reproducible: la misma respuesta puede valer 8 o
40 según cómo se interprete la unidad. El documento ya sabe cómo se arregla —P1_Q6, P1_Q7, P3_Q5,
P3_Q6, P3_Q8 y P2_Q5 lo llevan en el nombre del eje—, sólo falta aplicarlo en esas cuatro.

### 4. Las bandas siguen dejando huecos, y ahora también por abajo

`Minimal: 3-5 / Moderate: 6-8 / Intensive: >9` deja fuera 5,5 y 8,5 —y también **1 y 2 horas**, que
no caen en ninguna banda. Aparece así en P1_Q7, P2_Q3, P3_Q1, P4_Q1 y P4_Q2.

La solución ya está en el mismo documento: P3_Q5, P3_Q6 y P3_Q8 usan `<=5`, que cierra el piso.
Basta con usar `<=5 / 6-8 / >=9` en todas.

### 5. Dos cosas menores que conviene decidir

- **«4 / Every week»** sigue en P2_Q7, y ahora duplicado (el eje numérico se repite en las dos
  ramas). ¿Son dos opciones («4 veces» y «cada semana») o una?
- **«According to the subject»** cuelga de **No** en P2_Q4 y de **Sí** en P4_Q8. Los paneles son
  estudios independientes, así que puede ser deliberado, pero para quien codifica es una trampa.
  La segunda de las dos rarezas que anota `stance_map.py`, todavía abierta.
- **P4_Q8** sólo tiene rama «Sí»; falta la rama «No».
- **«Numeric system 0-100»** en P4_Q5: la taxonomía vieja decía 1-100. Cambia el rango real de la
  escala; conviene confirmar que es intencional.

---

## Qué implica para el trabajo

**Ya se puede codificar la estructura.** La duda que bloqueaba —si el Sí/No seguía existiendo— está
resuelta, y resuelta en el sentido que preserva la capa de postura. Lo que falta (P3_Q7, los cuatro
periodos, los pisos de banda) son arreglos puntuales del documento, no decisiones de modelo.

**Cuando se aplique, hay que reextraer todo.** Cambia el texto de las opciones en la mayoría de las
preguntas, así que el caché de extracción queda inservible y los números publicados hoy en el sitio
cambian por completo. Son unos 40 segundos de cómputo.

**La validación de Emily hay que rehacerla.** Las 44 etiquetas están hechas contra la taxonomía
vieja; con opciones nuevas dejan de ser un patrón válido para medir el acuerdo.

**El orden que propongo:** cerrar P3_Q7 y los cuatro periodos primero (es lo que más respuestas
recupera y lo que desbloquea la capa numérica), y dejar lo demás para la misma pasada de reextracción.

---

*La lectura estructurada de las dos versiones está en `docs/emily_posturas_varias_opciones.json`,
lista para codificar cuando se cierren los puntos de arriba.*
