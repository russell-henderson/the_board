#!/usr/bin/env bash
set -euo pipefail

if [[ -f .env ]]; then
  set -a; source .env; set +a
fi

export STATE_BACKEND="${STATE_BACKEND:-sqlite}"
export STATE_DB_PATH="${STATE_DB_PATH:-./state/the_board_state.db}"
mkdir -p "$(dirname "$STATE_DB_PATH")"
export CHROMA_PERSIST_DIRECTORY="${CHROMA_PERSIST_DIRECTORY:-./chroma_db}"
mkdir -p "$CHROMA_PERSIST_DIRECTORY"
export OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"

# Ensure poetry env is ready
poetry install --no-interaction --no-ansi

# Expect Ollama already running under a process manager in prod
poetry run uvicorn src.main:app --host "0.0.0.0" --port "${PORT:-8000}" --workers "${WORKERS:-2}"
