#!/usr/bin/env bash
set -euo pipefail

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
RELOAD="${RELOAD:-1}"

if ! command -v python >/dev/null 2>&1; then
  echo "[ERROR] python 未找到，请先激活虚拟环境"
  exit 1
fi

if [[ "$RELOAD" == "1" ]]; then
  exec python -m uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
else
  exec python -m uvicorn app.main:app --host "$HOST" --port "$PORT"
fi
