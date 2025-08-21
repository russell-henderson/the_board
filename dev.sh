#!/usr/bin/env bash
set -euo pipefail

# ---- Config ----
APP_MODULE="src/main.py"         # FastAPI entry
HOST="127.0.0.1"
PORT="${PORT:-8000}"

# ---- Load .env if present (export all) ----
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

# ---- State layer defaults (safe even if set in .env) ----
export STATE_BACKEND="${STATE_BACKEND:-sqlite}"
export STATE_DB_PATH="${STATE_DB_PATH:-./state/the_board_state.db}"
mkdir -p "$(dirname "$STATE_DB_PATH")"

# ---- ChromaDB persistence dir ----
export CHROMA_PERSIST_DIRECTORY="${CHROMA_PERSIST_DIRECTORY:-./chroma_db}"
mkdir -p "$CHROMA_PERSIST_DIRECTORY"

# ---- Ollama defaults ----
export OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"

# ---- Pre-flight checks ----
command -v poetry >/dev/null 2>&1 || { echo "❌ poetry not found"; exit 1; }
command -v ollama >/dev/null 2>&1 || { echo "❌ ollama not found"; exit 1; }

# ---- Install deps if needed ----
poetry install --no-interaction --no-ansi

# ---- Start Ollama (background) if not already running ----
if ! curl -fsS "${OLLAMA_BASE_URL}/api/tags" >/dev/null 2>&1; then
  echo "▶ Starting Ollama..."
  (ollama serve >/tmp/ollama.log 2>&1 & echo $! > /tmp/ollama.pid)
  sleep 2
fi

# ---- Ensure models are present (idempotent) ----
ollama pull "${PRIMARY_LLM:-llama3.1:8b}" || true
ollama pull "${EMBEDDING_MODEL:-mxbai-embed-large}" || true

# ---- Start FastAPI with auto-reload ----
echo "🚀 Starting FastAPI on http://${HOST}:${PORT} ..."
exec poetry run fastapi dev "${APP_MODULE}" --host "${HOST}" --port "${PORT}"
