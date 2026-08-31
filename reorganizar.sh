#!/usr/bin/env bash
#
# Reorganiza el repositorio plano (todo suelto en la raíz) a la estructura por carpetas.
#
# Es idempotente: si un archivo ya está en su sitio, lo salta. Se puede correr dos veces.
# Usa `git mv` cuando hay repositorio, para no perder el historial de cada archivo.
#
#   bash reorganizar.sh --simulacro   # muestra qué haría, sin tocar nada
#   bash reorganizar.sh               # lo hace
#
# NO toca: dhub/  docs/ (su contenido previo)  Francisco/  Resultados/  Resultados_smoke/
# Esas carpetas no las conozco; se quedan donde están y hay que decidirlas a mano.

set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

SIMULACRO=0
[ "${1:-}" = "--simulacro" ] && SIMULACRO=1

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    MV="git mv"; echo "Repositorio git detectado: uso 'git mv' para conservar el historial."
else
    MV="mv"; echo "Sin repositorio git: uso 'mv'."
fi
if [ $SIMULACRO = 1 ]; then echo ">>> SIMULACRO: no se modifica nada."; fi
echo

mover() {  # mover <origen> <carpeta destino>
    local orig="$1" dest="$2"
    if [ ! -e "$orig" ]; then
        if [ -e "$dest/$(basename "$orig")" ]; then
            echo "  ya estaba: $dest/$(basename "$orig")"
        else
            echo "  NO EXISTE: $orig"
        fi
        return 0
    fi
    if [ -e "$dest/$(basename "$orig")" ]; then
        echo "  ⚠ destino ocupado, lo dejo: $orig  (ya hay $dest/$(basename "$orig"))"
        return 0
    fi
    echo "  $orig → $dest/"
    if [ $SIMULACRO = 0 ]; then mkdir -p "$dest"; $MV "$orig" "$dest/"; fi
    return 0
}

echo "── pipeline/ ──"
for f in config.py taxonomy.py stance_map.py preprocess.py classify_questions.py \
         extract_arguments.py consensus_metrics.py stance_view.py score_validation.py \
         compare_models.py make_validation_sample.py audit_vs_synthesis.py visualize.py \
         run_smoke_offline.py; do
    mover "$f" pipeline
done

echo
echo "── datos/ ──"
mover dataset_prueba.xlsx datos
mover Resultados/validation_emily_done.xlsx datos

echo
echo "── docs/ ──"
mover RUNBOOK_FASE0.md docs

echo
echo "── se quedan donde están ──"
for d in Resultados Resultados_smoke tests dhub docs Francisco; do
    if [ -e "$d" ]; then echo "  $d/"; fi
done
if [ -e run_all.sh ]; then echo "  run_all.sh  (lo sustituye ./run.sh en la raíz; borrar cuando confirmes)"; fi
if [ -e requirements.txt ]; then echo "  requirements.txt"; fi

echo
if [ $SIMULACRO = 1 ]; then
    echo "Simulacro terminado. Repetir sin --simulacro para aplicarlo."
else
    cat <<'FIN'
Hecho. Ahora:

  1. Copia encima los archivos nuevos del zip (README.md, run.sh, .gitignore,
     pipeline/config.py, sitio/, tests/test_phase0.py).
  2. Comprueba que nada se rompió:

       python3 -m pytest tests -q          # deben pasar 32
       ./run.sh --sin-llm                  # recalcula y regenera el sitio, sin llamar al LLM

  3. Si todo pasa, commit:

       git add -A && git commit -m "Reorganiza el repositorio en pipeline/ sitio/ datos/ docs/"

Nota: config.py cambia las rutas a absolutas respecto de la raíz del repositorio, así que los
scripts ya se pueden correr desde cualquier directorio. Si tenías rutas propias, mira las
variables DELPHI_DATOS y DELPHI_RESULTADOS en el README.
FIN
fi
