#!/usr/bin/env bash
# run_offline.sh — wrapper to start the app in offline mode
# Usage: ./run_offline.sh [PORT]

set -euo pipefail
PORT=${1:-5050}

# ensure conda env is activated by the caller; we don't activate inside the script
# but we print a helpful reminder if python isn't from the expected environment
PYTHON_BIN=$(which python || true)
if [[ -z "${PYTHON_BIN}" ]]; then
  echo "python not found in PATH — activate your conda env first: conda activate py311_nlp"
  exit 1
fi

export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export HF_HOME="$PWD/.hf_home"

echo "Starting app in offline mode on port ${PORT} (python: ${PYTHON_BIN})"
PORT=${PORT} python app.py
