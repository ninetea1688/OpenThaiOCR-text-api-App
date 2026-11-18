#!/usr/bin/env bash
# Start the API. Settings come from .env (see .env.example) or OCR_* variables.
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . ./.env && set +a
exec .venv/bin/uvicorn app.main:app --host "${OCR_HOST:-127.0.0.1}" --port "${OCR_PORT:-8091}" --workers 1 "$@"
