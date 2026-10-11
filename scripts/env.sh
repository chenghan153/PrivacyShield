#!/usr/bin/env bash
# Source this file: source scripts/env.sh
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export XDG_CACHE_HOME="$PROJECT_ROOT/.cache"
export PIP_CACHE_DIR="$PROJECT_ROOT/.cache/pip"
export HF_HOME="$PROJECT_ROOT/.cache/huggingface"
export TMPDIR="$PROJECT_ROOT/.tmp"
export TESSDATA_PREFIX="$PROJECT_ROOT/.cache/tessdata"
mkdir -p "$TMPDIR" "$PIP_CACHE_DIR" "$HF_HOME" "$TESSDATA_PREFIX"
