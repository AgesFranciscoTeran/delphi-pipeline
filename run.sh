#!/usr/bin/env bash
# Pipeline completo + sitio. Se puede llamar desde cualquier directorio.
set -euo pipefail
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
P="$RAIZ/pipeline"; S="$RAIZ/sitio"

MODO="${1:-todo}"

case "$MODO" in
  --solo-sitio) ;;
  *)
    echo "── preprocesamiento ──"
    python3 "$P/preprocess.py"
    python3 "$P/classify_questions.py"
    if [ "$MODO" != "--sin-llm" ]; then
      echo "── extracción (LLM) ──"
      python3 "$P/extract_arguments.py"
    else
      echo "── extracción: SALTADA (--sin-llm), se reutiliza 02_extracted.csv ──"
    fi
    echo "── métricas ──"
    python3 "$P/consensus_metrics.py"
    python3 "$P/stance_view.py" || echo "  (stance_view falló; sigo)"
    ;;
esac

echo "── sitio ──"
python3 "$S/figuras.py"
python3 "$S/build.py"

echo
echo "Listo. Revisar sitio/index.html y hacer commit."
