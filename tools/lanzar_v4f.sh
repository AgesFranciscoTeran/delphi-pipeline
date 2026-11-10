#!/usr/bin/env bash
# Corridas v4f en spark-adi: prompt numérico que no pierde la cifra + eje principal acordado
# en P1_Q3 y P3_Q3. Parten de las v4e (sólo se reextrae lo que cambió).
# Log: ~/Delphi/Resultados_v4f.pipeline.log
source ~/.delphi_env
source ~/.venvs/delphi/bin/activate
cd ~/Delphi
{
  tools/correr_k.sh Resultados_v4e Resultados_v4f 3 \
  && mkdir -p Resultados_v4f/argumentos \
  && cp Resultados_v4e/argumentos/corridas.json Resultados_v4f/argumentos/ \
  && DELPHI_RESULTADOS=$HOME/Delphi/Resultados_v4f python -u tools/argumentos.py --k 3 \
  && DELPHI_RESULTADOS=$HOME/Delphi/Resultados_v4f ./run.sh --solo-sitio
  echo "FIN rc=$?"
} > ~/Delphi/Resultados_v4f.pipeline.log 2>&1
