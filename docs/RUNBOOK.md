# Runbook — corrida del pipeline

Cómo correr el análisis completo y qué mirar en cada paso. Actualizado para la estructura por
carpetas: **todas las órdenes se ejecutan desde la raíz del repositorio** (`~/Delphi`), y los
scripts resuelven sus rutas solos, así que da igual desde dónde se llamen.

> Si vienes del runbook viejo: los `.py` ya no están en la raíz sino en `pipeline/`. Donde antes
> decía `python preprocess.py`, ahora es `python3 pipeline/preprocess.py` — o directamente
> `./run.sh`, que encadena todo.

---

## 0. Antes de correr

```bash
cd ~/Delphi

# VPN activa; preguntar al servidor qué sirve hoy (la universidad los cambia sin aviso)
python3 tools/escanear_endpoints.py           # barre 12550-12570 y sugiere la línea de config.py
python3 tools/escanear_endpoints.py --probar  # además comprueba que genera, y mide latencia

pip install -r requirements.txt
python3 -m pytest tests -q                    # 48 passed
python3 pipeline/run_smoke_offline.py         # corrida completa con LLM simulado -> Resultados_smoke/
```

**Decodificación: libre, sin extras.** Se probaron las alternativas contra el servidor y
ninguna mejoró. La prueba se repite en cualquier momento:

```bash
python3 tools/escanear_endpoints.py --capacidades
```

Escala el presupuesto por variante e informa `finish_reason` y tamaño de salida, para poder
distinguir «no sabe» de «no le alcanzó» — que es donde se equivocaron dos versiones anteriores
de esa prueba. Medido con GLM-5.3-Flash el 14-09-2026, sobre el mismo ítem:

| variante | salida | corrida completa |
|---|---|---|
| sin extras (control) | 44 chars | **770/775** |
| `guided_json` | 44 chars | 767/775 en 795 s |
| `enable_thinking=false` | 713 chars | no probada en corrida completa |
| las dos juntas | 1259 chars | — |

Apagar el pensamiento **funciona pero no sirve**: no elimina la explicación, la mueve del canal
de razonamiento al de contenido, donde compite con el JSON por el mismo presupuesto. El guiado
tampoco ayuda porque el truncado ocurre antes de que el esquema aplique.

Lo que sí resuelve el truncado es la escalada de presupuesto en `extract_single`: sólo ante
`finish_reason=length`, duplicando hasta `MAX_TOKENS_TECHO`. La columna `max_tokens_usados`
del CSV dice cuánto necesitó cada respuesta.

El modo de decodificación entra en la clave del caché, así que cambiarlo obliga a reextraer
las 775. Es deliberado: una tabla no puede mezclar dos modos.

**Los puertos y modelos no se escriben en la documentación.** Se escribieron a mano en tres
sitios —`config.py`, `compare_models.py` y una página de Notion— y los tres se desactualizaron;
la última vez costó 706 extracciones fallidas contra un modelo que el servidor ya no tenía.
`escanear_endpoints.py` lo pregunta en el momento, así que no puede quedar viejo.

Si un modelo cambió, no hace falta editar nada para una corrida puntual:

```bash
DELPHI_MODELO="<el id exacto que devuelva el endpoint>" ./run.sh
```

Si el cambio es permanente, actualizar el valor por defecto de `MODEL_LLM` en
`pipeline/config.py` y `MODELS` en `pipeline/compare_models.py`. Ha pasado tres veces; una
costó una corrida entera de respuestas vacías antes de que se detectara.

El modelo entra en la clave del caché (`rid|modelo|hash`), así que cambiarlo **no mezcla
corridas**: invalida todo el caché y vuelve a extraer con un solo modelo. Cuál se usó queda en
`Resultados/run_manifest.json` y sale impreso en el sitio.

**Comprobar que están las entradas:**

```bash
ls datos/          # dataset_prueba.xlsx y validation_emily_done.xlsx
```

Si falta `validation_emily_done.xlsx`, buscarlo en la corrida anterior (`Resultados_v1_*/`) o
pedírselo a Emily. Sin él no se puede correr el paso 4.

---

## 1. La corrida

```bash
./run.sh                # todo: preprocesamiento + extracción con LLM + métricas + sitio
./run.sh --sin-llm      # recalcula métricas y sitio sobre la extracción que ya existe
./run.sh --solo-sitio   # sólo figuras e index.html
```

Antes de una corrida nueva, conservar la anterior — es la evidencia de lo que se reportó:

```bash
mv Resultados Resultados_$(date +%Y%m%d) && mkdir Resultados
```

Paso a paso, si se prefiere control fino:

```bash
python3 pipeline/preprocess.py
python3 pipeline/classify_questions.py
python3 pipeline/extract_arguments.py     # ~40 s con MAX_WORKERS=8
python3 pipeline/consensus_metrics.py
python3 pipeline/stance_view.py
python3 pipeline/audit_vs_synthesis.py
python3 sitio/figuras.py && python3 sitio/build.py
```

### Qué mirar en la salida de `extract_arguments.py`

| Señal | Esperado | Si no |
|---|---|---|
| `invalid_output` | ~0 | El modelo no sigue el formato. Probar `USE_GUIDED_JSON = True` en `config.py`; si el servidor devuelve HTTP 400, dejarlo en `False`. |
| `letter/text mismatch` | < 5 % | Casos donde el modelo dudó entre dos opciones. Revisarlos en el caché. |
| Units reported | mayoría `hours/day`, `hours/week`, `students`, `semesters`, `none` | `other` alto = falta una unidad en `UNIT_VOCAB`. |
| Fallos de conexión | 0 | Endpoint caído o modelo renombrado: volver al paso 0. |

---

## 2. Comprobación contra las síntesis

Abrir `Resultados/audit_vs_synthesis.xlsx` y, para las 20 preguntas categóricas de la ronda
final, anotar en `veredicto_humano` si la distribución del pipeline es coherente con las
respuestas crudas, que están en la misma fila.

Chequeos concretos que deberían salir bien: P3_Q10 mayoritariamente «Final years»; P2_Q4, P2_Q6 y
P4_Q3 mayoritariamente «No»; P3_Q7 **no** unánime en «Equality». Si alguno falla, hay un problema
de extracción, no de taxonomía.

---

## 3. Test-retest (gratis, y conviene reportarlo)

Panelistas que repitieron su texto entre rondas deben recibir la misma etiqueta.

```bash
python3 - <<'EOF'
import os, sys, pandas as pd
sys.path.insert(0, "pipeline"); import config
d = pd.read_csv(os.path.join(config.OUTPUT_DIR, "02_extracted.csv"))
d = d[d.is_valid_response]
d["norm"] = d.Response.str.strip().str.lower().str.replace(r"\s+", " ", regex=True)
k = ["Panel", "Question", "Panelist", "norm"]
g = d.groupby(k).selected_option.nunique(dropna=False)
g = g[d.groupby(k).size() > 1]
print(f"textos repetidos: {len(g)} | etiqueta idéntica: {(g==1).sum()} ({(g==1).mean()*100:.0f}%)")
EOF
```

Referencia: 30/30 (100 %) en la corrida del 30-08. Era 82 % antes de corregir la extracción.

---

## 4. Kappa contra las etiquetas de Emily

Los 44 `response_id` de la hoja están dentro del dataset, así que no hace falta volver a llamar al
modelo:

```bash
python3 pipeline/score_validation.py datos/validation_emily_done.xlsx Resultados/02_extracted.csv
```

Referencia de la corrida del 30-08: κ 0,72 global (IC 95 % 0,57–0,84), 0,69 en preguntas de
opción, 0,68 en banda. **Ese es el número que certifica los resultados publicados**, porque sale
de la corrida que los produjo.

---

## 5. Comparación de modelos (no hace falta repetirla)

**Desactualizada desde el 14-09-2026.** La comparación se hizo entre Gemma y DeepSeek y
concluyó a favor de Gemma por lo operativo (9× más rápido, latencia estable, 0 fallos de
formato) con exactitud indistinguible. La universidad dejó de servir Gemma y el modelo de
trabajo pasó a ser `zai-org/GLM-5.3-Flash`, así que esa decisión ya no describe lo que corre.

Rehacerla es parte de lo pendiente, pero **primero hay que cerrar la taxonomía**: el modo (a)
puntúa contra las 44 etiquetas de Emily, que están hechas contra las opciones anteriores y
dejan de ser un patrón válido con la v2.

```bash
# (a) DECIDE: los dos modelos sobre los MISMOS ítems que etiquetó Emily
python3 pipeline/compare_models.py datos/validation_emily_done.xlsx
python3 pipeline/score_validation.py datos/validation_emily_done.xlsx Resultados/model_comparison.csv

# (b) EXPLORA: muestra nueva de 128 (4 por pregunta), sin gold
python3 pipeline/compare_models.py
```

Las columnas `gemma` / `deepseek` traen la etiqueta comparable con el gold (la OPCIÓN en
categóricas, la BANDA en numéricas); el número crudo va aparte. Emily etiqueta bandas: comparar
«8 hours/day» contra «Moderate» daría un kappa de cero por comparar cosas distintas.

---

## 6. Publicar

```bash
git add -A && git commit -m "Corrida $(date +%F)" && git push
```

`Resultados/` está en `.gitignore` a propósito: se regenera, pesa, y contiene las respuestas del
panel. Lo que se publica es `sitio/index.html` y `sitio/figuras/*.svg`.

---

## 7. Dos trampas conocidas

**CSV viejos con código nuevo.** Si cambia `config.py` —por ejemplo al añadir una conversión de
unidades— los `Resultados/03_*.csv` de una corrida anterior dejan de corresponder al código, y
regenerar el sitio sobre ellos publica números desactualizados. `./run.sh --sin-llm` recalcula
sin volver a llamar al modelo. Ya pasó: P1_Q1 figuraba como «Insuficiente» porque sus CSV eran
previos a la conversión años↔semestres; con el código actual es «Convergencia moderada» con n=5.

**El servidor no es determinista entre corridas.** Con `temperature=0` y `seed` fijo, dos
ejecuciones cambiaron 3 etiquetas de 44 (el κ pasó de 0,72 a 0,79). El test-retest da 100 %
*dentro* de una corrida, pero vLLM con batching continuo no es idéntico bit a bit *entre*
corridas. Lo que hace reproducible un resultado es archivar `Resultados/02_extraction_cache.json`
y `Resultados/run_manifest.json`, no los parámetros. **Guardar esos dos archivos de la corrida
que se reporte en el artículo.**

---

## 8. Lo que esta corrida NO resuelve

- **La taxonomía** (contenido de Emily): postura + calificadores, umbrales de depuración, bandas
  contiguas, P1_Q3 como abierta, opción «mixto». Son las ocho decisiones de la Fase 1.
- **Los criterios de consenso**: los umbrales de `config.py` son provisionales. La Fase 2 los fija
  con la literatura Delphi (acuerdo + estabilidad entre rondas), y hay que fijarlos **antes** de
  volver a mirar los resultados.
- **La capa de argumentos y su red**: se rehace en la Fase 1 sobre la taxonomía de argumentos.
- **La validación formal**: 200–300 ítems y un segundo codificador. Fase 3.

El detalle de todo esto está en `docs/diagnostico_v2.md`.
