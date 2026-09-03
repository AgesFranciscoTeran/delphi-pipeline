# Sitio de resultados — Delphi Pipeline (USFQ)

Página estática con los resultados del estudio Delphi, la evolución del consenso ronda por ronda
y lo que falta para cerrar el artículo. **Se genera desde la salida del pipeline**, no a mano.

Título de trabajo del artículo: *Mapping the Evolution of Citizen Consensus: A Visual and Network
Analysis of Delphi Rounds*.

---

## Cómo funciona

```
Resultados/*.csv  →  datos.py     →  tablas por panel
       │             figuras.py   →  figuras/*.svg (una tanda por panel)
       │             contenido.py →  texto editorial
       └───────────────────────────→ build.py →  index.html + panel1..4.html
```

**Una página por panel.** Los cuatro paneles son estudios independientes: ningún panelista
participa en más de uno y, de las 32 preguntas, sólo una se repite entre paneles. Por eso no se
agregan resultados ni se comparan entre sí. `index.html` es la portada que enlaza los cuatro.

**Ningún número está escrito a mano.** Todas las tablas y todas las cifras del texto salen de
`Resultados/*.csv` a través de `datos.py`. Lo único editorial son los textos de las decisiones
pendientes y las lecturas de cada panel, y viven en `cabecera.py`, marcados como tales.

Esto no es purismo: una versión anterior tenía las tablas copiadas a mano y una de ellas quedó
desactualizada en cinco de doce filas cuando cambió el tratamiento de unidades. Con esta
estructura, volver a correr el pipeline y regenerar el sitio no puede producir esa
inconsistencia.

| Archivo | Qué hace |
|---|---|
| `datos.py` | Lee `Resultados/*.csv` y devuelve las tablas. Importa `stance_map.py` del pipeline para la capa de posturas. |
| `figuras.py` | Genera las figuras en SVG (y en PNG a 300 dpi con `--png`, para el manuscrito). Sustituye a `pipeline/visualize.py`. |
| `contenido.py` | El texto editorial: las decisiones de taxonomía y qué panel afecta cada una. Lo único no derivado de los CSV. |
| `estilos.py` | La hoja de estilos, compartida por la portada y las páginas de panel. |
| `build.py` | Ensambla la portada y las cuatro páginas de panel. |

| `figuras/` | SVG generados. Se versionan para que GitHub Pages funcione sin ejecutar nada. |
| `index.html`, `panel1–4.html` | El sitio. Autocontenidos: los SVG van incrustados, no enlazados. |

### Rutas

`datos.py` las toma de variables de entorno, con estos valores por defecto:

```bash
export DELPHI_PIPELINE=<raíz>/pipeline      # donde está stance_map.py
export DELPHI_RESULTADOS=<raíz>/Resultados  # donde están los 03_*.csv
```

Por defecto se resuelven respecto de la raíz del repositorio, así que normalmente no hay que
tocarlas. Sólo hacen falta para apuntar a los resultados de otra corrida.

### Requisitos

`pandas`, `numpy`, `matplotlib`, `networkx`. Ya están en el entorno del pipeline.

---

## El ciclo de trabajo en la H200

```bash
cd ~/Delphi
./run.sh                # pipeline completo + sitio
./run.sh --sin-llm      # recalcula y regenera el sitio sin volver a llamar al modelo
./run.sh --solo-sitio   # sólo figuras + index.html

git add -A && git commit -m "Actualiza resultados $(date +%F)" && git push
```

**Cuidado con los CSV viejos.** Si `config.py` cambia —por ejemplo al añadir una conversión de
unidades— los `Resultados/03_*.csv` de una corrida anterior dejan de corresponder al código.
Regenerar el sitio sobre ellos publica números desactualizados. `./run.sh --sin-llm` recalcula
las métricas sobre la extracción existente y evita justo eso. Ya pasó una vez: P1_Q1 figuraba
como «Insuficiente» porque sus CSV eran previos a la conversión años↔semestres.

GitHub Pages republica solo en un par de minutos. **No hace falta editar `index.html` nunca**:
si un número está mal, está mal en el CSV o en `datos.py`.

Para las figuras del manuscrito a 300 dpi: `./run.sh --png`.

---

## Publicarlo la primera vez

```bash
cd ~/delphi/sitio
git init
git config user.name  "Pancho"          # local al repo, no toca a otros usuarios del servidor
git config user.email "tu@correo"
git add -A
git commit -m "Sitio de resultados: estado del pipeline Delphi"
git branch -M main
git remote add origin https://github.com/<usuario>/<repo>.git
git push -u origin main
```

Luego: **Settings → Pages → Build and deployment** → *Source*: `Deploy from a branch` →
*Branch*: `main` / `/ (root)` → **Save**. Queda en `https://<usuario>.github.io/<repo>/`.

**Credenciales en un servidor compartido.** GitHub pide un token, no contraseña (Settings →
Developer settings → Personal access tokens → *Fine-grained* → **Contents: Read and write**).
No usar `credential.helper store`, que lo deja en texto plano en el home, ni meterlo en la URL
del remote, que queda en `.git/config`. Usar la caché en memoria y limpiarla al terminar:

```bash
git config --global credential.helper 'cache --timeout=900'
# ... push ...
git credential-cache exit
```

---

## ⚠ Pages gratis significa repositorio público

Con cuenta gratuita **Pages sólo funciona en repositorios públicos**, y esto contiene resultados
no publicados del panel y los desacuerdos con las síntesis de los facilitadores. Antes del primer
`push`, decidir:

1. **No usar Pages.** `index.html` es autocontenido: se manda por correo y se abre con doble
   clic. Si sólo lo van a leer Emily y Jonathan, es lo sensato.
2. **Repo privado con Pages**, que requiere GitHub Pro o **GitHub Education** — gratis con correo
   institucional. Es la buena opción si se quiere el enlace compartible.
3. **Repo público, decidido por Jonathan.** Es su estudio. La página lleva
   `robots: noindex, nofollow`, así que no la indexan los buscadores, pero eso no la hace
   privada: cualquiera con el enlace la ve.

---

## Notas

- **Las dos κ.** El 0,72 del titular es el de la corrida que produjo estos resultados; el 0,79 de
  la sección 8 es el mismo modelo sobre los mismos ítems en otra corrida. La diferencia es la
  no-determinación del servidor entre corridas, y está explicada en la página.
- **Los resultados numéricos son preliminares** hasta que se cierren las decisiones 5 y 6.
- **Las figuras de red son ilustrativas, no estadística.** Con 7–10 nodos, centralidad y
  modularidad son inestables y no deben reportarse como resultado. La red con tamaño suficiente
  es la del estudio de eutanasia.
- **Impresión:** hay reglas `@media print`; Ctrl/Cmd+P exporta a PDF sin el menú. Útil para
  llevar las secciones 3, 4 y 6 a la sesión con Emily.
- El diagnóstico técnico completo está en `claude/diagnostico-delphi-v2.md`, en el proyecto.
