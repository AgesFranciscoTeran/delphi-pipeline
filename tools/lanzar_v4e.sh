#!/usr/bin/env bash
# Corridas multieje (v4e) en spark-adi: 3 corridas + consolidación + argumentos + sitio.
# Se lanza dentro de tmux; el log queda en ~/Delphi/Resultados_v4e.pipeline.log
source ~/.delphi_env
source ~/.venvs/delphi/bin/activate
cd ~/Delphi
{
  tools/correr_k.sh Resultados_v4r Resultados_v4e 3 \
  && mkdir -p Resultados_v4e/argumentos \
  && cp Resultados_v4r/argumentos/corridas.json Resultados_v4e/argumentos/ \
  && DELPHI_RESULTADOS=$HOME/Delphi/Resultados_v4e python -u tools/argumentos.py --k 3 \
  && DELPHI_RESULTADOS=$HOME/Delphi/Resultados_v4e ./run.sh --solo-sitio
  echo "FIN rc=$?"
} > ~/Delphi/Resultados_v4e.pipeline.log 2>&1
