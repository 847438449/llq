#!/usr/bin/env bash
set -euo pipefail

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
RELOAD="${RELOAD:-1}"

if ! command -v uvicorn >/dev/null 2>&1; then
  echo "[ERROR] uvicorn 未安装，请先执行: pip install -r requirements.txt"
  exit 1
fi

if [[ "$RELOAD" == "1" ]]; then
  exec uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
else
  exec uvicorn app.main:app --host "$HOST" --port "$PORT"
fi
