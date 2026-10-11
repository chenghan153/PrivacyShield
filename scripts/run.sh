#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
source scripts/env.sh
exec .venv/bin/streamlit run app.py --server.address 127.0.0.1 --server.port "${PORT:-8501}" --browser.gatherUsageStats false
