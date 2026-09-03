# Delphi Pipeline — USFQ

Marco computacional para analizar estudios Delphi a gran escala: clasifica respuestas de texto
libre contra una taxonomía definida por el equipo clínico, mide el consenso ronda por ronda y se
valida contra codificación humana.

Artículo en preparación: *Mapping the Evolution of Citizen Consensus: A Visual and Network
Analysis of Delphi Rounds*.

| | |
|---|---|
| **Conjunto de prueba** | Currículo médico USFQ — 786 respuestas, 32 preguntas, 4 paneles, 3 rondas |
| **Conjunto real** | Eutanasia, ~22 000 respuestas (Fase 4, pendiente) |
| **Equipo** | Pancho (implementación) · Emily (marco clínico) · Jonathan Guillemot (supervisión) |

---

## Estructura

```
Delphi/
├── pipeline/          el análisis
├── sitio/             la página de resultados (GitHub Pages)
├── datos/             entradas: el .xlsx del estudio y las etiquetas de validación
├── Resultados/        salidas del pipeline (no se versiona)
├── tests/             32 pruebas, una por hallazgo cerrado del diagnóstico
└── docs/              RUNBOOK.md (cómo se corre) y diagnostico_v2.md (estado y plan)
```

Antes todo esto estaba suelto en la raíz y las rutas eran relativas al directorio de trabajo, así
que un `cd` mal puesto creaba un `Resultados/` nuevo en otro sitio sin avisar. Ahora
`pipeline/config.py` ancla las rutas a la raíz del repositorio: **los scripts se pueden ejecutar
desde donde sea**.

Se pueden redirigir con variables de entorno:

```bash
export DELPHI_DATOS=/ruta/al/dataset.xlsx
export DELPHI_RESULTADOS=/ruta/a/Resultados
```

---

## Cómo se corre

```bash
pip install -r requirements.txt
python -m pytest tests -q          # 32 pruebas, sin LLM ni red

./run.sh                           # pipeline completo + sitio
./run.sh --sin-llm                 # salta la extracción y recalcula sobre 02_extracted.csv
./run.sh --solo-sitio              # sólo regenera figuras e index.html
```

Antes de una corrida con LLM, comprobar que la universidad no cambió los modelos:

```bash
for p in 12555 12559; do echo -n "  $p -> "; \
  curl -s --max-time 5 http://172.28.230.10:$p/v1/models \
  | python -c "import sys,json;print(', '.join(m['id'] for m in json.load(sys.stdin)['data']))"; done
```

Si cambiaron, actualizar `MODEL_LLM` en `pipeline/config.py` y `MODELS` en
`pipeline/compare_models.py`. Ha pasado ya dos veces.

---

## Qué hace cada cosa

### `pipeline/`

| Archivo | |
|---|---|
| `config.py` | Rutas, endpoints, umbrales de consenso (**provisionales**, ver Fase 2) y conversiones de unidades. |
| `taxonomy.py` | La taxonomía de Emily + la unidad de cada pregunta numérica + su hash. |
| `stance_map.py` | Estructura anidada postura → calificadores, de los documentos de Emily. |
| `preprocess.py` | Limpieza y separación de respuestas individuales y síntesis. |
| `classify_questions.py` | Tipo de cada pregunta: nominal / binary / quantitative / hybrid. |
| `extract_arguments.py` | **El núcleo.** Clasificación por letra + `NONE`, caché con clave (id, modelo, hash del prompt), concurrencia, manifiesto de corrida. |
| `consensus_metrics.py` | Entropía por K, mediana/IQR, resolución determinista de unidades, empates, convergencia en 4 clases. |
| `stance_view.py` | Recalcula el consenso a nivel de postura sobre una extracción existente. |
| `score_validation.py` | Acuerdo y κ de Cohen con IC bootstrap contra las etiquetas humanas. |
| `compare_models.py` | Dos modelos sobre los mismos ítems etiquetados. |
| `make_validation_sample.py` | Genera la hoja de validación para la codificadora. |
| `audit_vs_synthesis.py` | Cruce: distribución del pipeline × síntesis del facilitador × respuestas crudas. |
| `run_smoke_offline.py` | Corrida completa con un LLM simulado: prueba todo el encadenado sin red ni servidor. |
| `visualize.py` | **Superado** por `sitio/figuras.py`, que hace las mismas figuras mejor y en SVG. Se conserva sólo para comparar; se puede borrar. |

### `sitio/`

Genera el sitio desde `Resultados/*.csv`: una portada y **una página por panel**. Los cuatro
paneles son estudios independientes —sin panelistas ni preguntas en común—, así que no se
agregan ni se comparan entre sí. **Ningún número está escrito a mano.**
Ver `sitio/README.md` para el detalle y las instrucciones de publicación.

---

## Estado

La Fase 0 está cerrada: extracción, métricas y reproducibilidad corregidas y comprobadas
(κ 0,72 contra la codificación de Emily, consistencia interna 100 %, coherencia con las síntesis
de los facilitadores en las 20 preguntas categóricas).

El procedimiento paso a paso está en `docs/RUNBOOK.md`. Lo que falta está en `docs/diagnostico_v2.md`, y lo que bloquea todo son ocho decisiones de
taxonomía que sólo puede tomar el equipo clínico.

### Advertencia sobre reproducibilidad

El servidor vLLM **no garantiza resultados idénticos entre corridas**, aun fijando
`temperature=0` y `seed`: entre dos ejecuciones cambiaron 3 etiquetas de 44. Lo que hace
reproducible un resultado es archivar `Resultados/02_extraction_cache.json` y
`Resultados/run_manifest.json`, no los parámetros. Decirlo así en la sección de métodos.

Lo mismo aplica al propio código: los CSV de una corrida vieja pueden no coincidir con lo que
produce el código de hoy. Si `config.py` cambia (por ejemplo, al añadir una conversión de
unidades), hay que **recalcular** las métricas antes de regenerar el sitio; `./run.sh --sin-llm`
lo hace sin volver a llamar al modelo.
