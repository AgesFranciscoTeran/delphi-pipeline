#!/usr/bin/env bash
# Experimento de señales en spark-adi: 4.ª corrida (mismo prompt que v4f, con logprobs = S2)
# desde cero, y luego S3 (cita) + S5 (rasgos) sobre sus etiquetas.
# Log: ~/Delphi/Resultados_v4f_k4.log
source ~/.delphi_env
source ~/.venvs/delphi/bin/activate
cd ~/Delphi
{
  D=$HOME/Delphi/Resultados_v4f_k4
  [ -d "$D" ] || mkdir -p "$D"          # si existe, se reanuda desde su caché
  export DELPHI_RESULTADOS=$D DELPHI_WORKERS=${DELPHI_WORKERS:-12}
  echo "== inicio $(date -Is)"
  python3 pipeline/preprocess.py && python3 pipeline/classify_questions.py \
  && DELPHI_SENALES=1 python3 -u pipeline/extract_arguments.py \
  && python3 pipeline/consensus_metrics.py \
  && python3 -u tools/senales_llm.py "$D"
  echo "FIN rc=$?  $(date -Is)"
} >> ~/Delphi/Resultados_v4f_k4.log 2>&1
