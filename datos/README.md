# datos/

Entradas del pipeline. **Los `.xlsx` no se versionan** (ver `.gitignore`): son las respuestas
crudas del panel y las etiquetas de la codificadora, y el repositorio puede ser público.

| Archivo | Qué es | De dónde sale |
|---|---|---|
| `dataset_prueba.xlsx` | Las 786 respuestas del estudio de currículo médico, 4 paneles × 3 rondas. | El equipo del estudio. |
| `validation_emily_done.xlsx` | Los 44 ítems etiquetados a ciegas por Emily. Necesario para `score_validation.py`. | Emily. |

Sin estos archivos el pipeline no arranca: `preprocess.py` falla con `FileNotFoundError`.
Se pueden poner en otra ruta con `DELPHI_DATOS`.
