#!/usr/bin/env bash
# Espejo entre la H200 (copia principal: código, git, sitio, commits) y spark-adi (corre el GLM).
# Corre en el HOST de la H200, como fteran (no dentro del contenedor). Ver docs/RUNBOOK.md.
#
#   tools/espejo.sh subir   H200 -> spark: código, git, datos y documentos.
#                           No toca Resultados* en spark (lo que spark generó no se borra).
#   tools/espejo.sh traer   spark -> H200: sólo Resultados* (corridas hechas en spark).
#   Añadir -n después del subcomando para ver qué haría sin copiar nada.
set -euo pipefail
SPARK=${SPARK:-fteran@172.21.230.33}
cd "$(dirname "$0")/.."
modo=${1:-}; shift || true
case "$modo" in
  subir) rsync -a --delete "$@" --exclude 'Resultados*' --exclude '__pycache__' \
               --exclude '.pytest_cache' ./ "$SPARK:Delphi/" ;;
  traer) rsync -a "$@" --include 'Resultados*/***' --include 'Resultados*' --exclude '*' \
               "$SPARK:Delphi/" ./ ;;
  *) echo "uso: $0 subir|traer [-n]"; exit 1 ;;
esac
echo "espejo $modo: listo"
