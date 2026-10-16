# Criterios de consenso

**Fijados el 15 de octubre de 2026**, en la reunión con Emily, sobre el documento «Decisiones para
la reunión» (preparado el 2 de octubre). Se eligieron desde la literatura Delphi y **antes** de
recalcular los resultados: el documento no mostraba cómo cambiaba cada pregunta con cada opción.
Si algún criterio cambia, se cambia esta fecha y se dice en el artículo.

Implementación: `pipeline/config.py` (constantes) y `pipeline/consensus_metrics.py`
(`agreement_label`, `cambio_neto`, `resultado`, `resultados`).

## Decisiones

| | Decisión | Fuente |
|---|---|---|
| Acuerdo | Porcentaje de las respuestas clasificadas en la etiqueta modal. Tres niveles: alto ≥ 70 %, moderado ≥ 60 %, bajo ≥ 50 %. | Diamond et al. 2014; Schifano y Niederberger 2025 |
| Consenso | Acuerdo alto (≥ 70 %). Un empate en el primer puesto no es acuerdo. | Ídem |
| Sobre qué | La postura (a favor / en contra / condicional) en las 11 preguntas de sí / no, con los calificadores como distribución; la opción en las demás; la banda en las numéricas, con mediana y RIC sólo como descripción. | — |
| Estabilidad | Cambio neto ≤ 15 % entre las dos últimas rondas: la mitad de la suma de las diferencias absolutas entre las proporciones de cada opción. Con paneles de 7 a 10 personas, como mucho una persona que cambia. | Scheibe, Skutsch y Schofer 1975 |
| Resultado | Consenso (acuerdo y estable) · Consenso no consolidado (acuerdo, no estable) · Disenso estable (sin acuerdo, estable) · Sin estabilizar. Exige dos rondas con datos suficientes. | Dajani et al. 1979; ACCORD (Gattrell et al. 2024) |
| Sensibilidad | Se reporta además el resultado con umbral de consenso de 75 % y 80 %. | — |
| Calidad de datos | Menos de 5 respuestas clasificadas, o más de 40 % sin clasificar: «Insuficiente». Las respuestas fuera de tema no cuentan en el denominador. | — |

## Taxonomía acordada el mismo día

- **Bandas contiguas**: ≤ 5 · > 5 y ≤ 8 · > 8 (P1_Q7, P2_Q3, P3_Q1, P3_Q5, P3_Q6, P3_Q8,
  P4_Q1, P4_Q2); P1_Q6: ≤ 2 · > 2 y ≤ 5 · > 5. Antes, 15 respuestas caían en huecos y se
  asignaban con una regla nuestra.
- **Admisión** (P3_Q2, P4_Q7): Few < 50 · More 50–80 · Many > 80.
- **P1_Q7**: se extraen las horas de ABP (sobre las que se mide el consenso) y, aparte, el total
  semanal (descriptivo).

Están en `tools/build_taxonomy.py` (`BANDAS_ACORDADAS`, `MEDIDA_ACORDADA`), no en el documento de
Emily: si llega una versión nueva del documento, los acuerdos se mantienen.

## Fuentes

- Dajani JS, Sincoff MZ, Talley WK (1979). Stability and agreement criteria for the termination of Delphi studies. *Technological Forecasting and Social Change* 13(1):83–90.
- Diamond IR, Grant RC, Feldman BM, et al. (2014). Defining consensus: a systematic review recommends methodologic criteria for reporting of Delphi studies. *Journal of Clinical Epidemiology* 67(4):401–409.
- Gattrell WT, Logullo P, van Zuuren EJ, et al. (2024). ACCORD (ACcurate COnsensus Reporting Document). *PLOS Medicine* 21(1):e1004326.
- Holey EA, Feeley JL, Dixon J, Whittaker VJ (2007). An exploration of the use of simple statistics to measure consensus and stability in Delphi studies. *BMC Medical Research Methodology* 7:52.
- Scheibe M, Skutsch M, Schofer J (1975). Experiments in Delphi methodology. En Linstone HA, Turoff M (eds.), *The Delphi Method: Techniques and Applications*. Addison-Wesley.
- Schifano J, Niederberger M (2025). How Delphi studies in the health sciences find consensus: a scoping review. *Systematic Reviews* 14:14.
- von der Gracht HA (2012). Consensus measurement in Delphi studies: review and implications for future quality assurance. *Technological Forecasting and Social Change* 79(8):1525–1536.
