#!/usr/bin/env bash
# Tres corridas v4, secuenciales. Cada una parte del caché de su v3_kN: sólo se reextraen
# las preguntas cuyo prompt cambió con la taxonomía v4.
cd /home/fteran/Delphi
P=pipeline
for k in 1 2 3; do
  D=Resultados_v4_k$k
  rm -rf "$D"; cp -r Resultados_v3_k$k "$D"
  export DELPHI_RESULTADOS="$PWD/$D"
  {
    echo "== v4 k$k  $(date -Is)"
    python3 $P/preprocess.py && python3 $P/classify_questions.py && \
    python3 $P/extract_arguments.py && python3 $P/consensus_metrics.py && \
    (python3 $P/stance_view.py || echo "stance_view falló")
    echo "== fin k$k rc=$?  $(date -Is)"
  } > "$D/run.log" 2>&1
done
echo TERMINADO > /home/fteran/Delphi/Resultados_v4_k3/.hecho
