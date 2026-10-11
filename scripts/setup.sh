#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
source scripts/env.sh

PYTHON_BIN="${PYTHON_BIN:-python3.11}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python 3.11 is required. Set PYTHON_BIN to a compatible Python 3.11/3.12 executable." >&2
  exit 1
fi
if [[ ! -x .venv/bin/python ]]; then
  "$PYTHON_BIN" -m venv .venv
fi
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[dev]'
if command -v tesseract >/dev/null 2>&1 && [[ ! -f "$TESSDATA_PREFIX/eng.traineddata" ]]; then
  if ! command -v curl >/dev/null 2>&1; then
    echo "curl is required to download the local English OCR data." >&2
    exit 1
  fi
  echo "Downloading Tesseract English data to the project cache..."
  curl --fail --location --retry 3 \
    https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/4.1.0/eng.traineddata \
    --output "$TESSDATA_PREFIX/eng.traineddata"
fi
.venv/bin/python demo/make_synthetic_docs.py
.venv/bin/python scripts/build_demo_assets.py
echo "Setup complete. Run: scripts/run.sh"
