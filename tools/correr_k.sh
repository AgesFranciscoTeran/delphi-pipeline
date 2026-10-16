#!/usr/bin/env bash
# k corridas secuenciales que parten del caché de otras, y su consolidación.
#   tools/correr_k.sh <origen> <destino> [k]
#   tools/correr_k.sh Resultados_v4 Resultados_v4r 3
# Cada <destino>_kN parte de una copia de <origen>_kN: sólo se reextraen las respuestas cuyo
# prompt cambió (la clave del caché incluye el prompt). Al final consolida en <destino>.
set -uo pipefail
cd "$(dirname "$0")/.."
ORIGEN=$1; DESTINO=$2; K=${3:-3}; P=pipeline
for k in $(seq 1 "$K"); do
  D=${DESTINO}_k$k
  rm -rf "$D"; cp -r "${ORIGEN}_k$k" "$D"; rm -f "$D/02_extraction_errors.csv"
  export DELPHI_RESULTADOS="$PWD/$D"
  {
    echo "== $D  $(date -Is)"
    python3 $P/preprocess.py && python3 $P/classify_questions.py && \
    python3 $P/extract_arguments.py && python3 $P/consensus_metrics.py && \
    (python3 $P/stance_view.py || echo "stance_view falló")
    echo "== fin $D rc=$?  $(date -Is)"
  } > "$D/run.log" 2>&1
done
CARPETAS=$(for k in $(seq 1 "$K"); do printf "%s_k%s " "$DESTINO" "$k"; done)
python3 tools/consolidar.py $CARPETAS --salida "$DESTINO" > "$DESTINO.consolidar.log" 2>&1
export DELPHI_RESULTADOS="$PWD/$DESTINO"
./run.sh --sin-llm >> "$DESTINO.consolidar.log" 2>&1
echo TERMINADO > "$DESTINO/.hecho"
