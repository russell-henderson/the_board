# Deployment & Local Development Guide

This guide provides the complete setup instructions for running **the_board** locally and preparing for production.

---

## 1. Prerequisites

Ensure the following are installed:

- **Python 3.11+** (use [`pyenv`](https://github.com/pyenv/pyenv) if possible)
- **Poetry** (Python dependency management)
- **Ollama** (local LLM server) → [Install Ollama](https://ollama.ai/)
- **Git** (for cloning and version control)

Optional but recommended:

- **Docker** (for containerized deployment)
- **Make** (for developer shortcuts)

---

## 2. Repository Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd the_board


Project structure (simplified):



/the_board
├── src/                  # Source code
│   ├── main.py           # FastAPI app entry point
│   ├── agents/           # Agent classes
│   ├── knowledge/        # RAG / ChromaDB integration
│   ├── state/            # State store
│   └── config/           # Agent personas & configs
├── prompts/              # System prompts for agents
├── chroma_db/            # Vector DB persistence
├── state/                # SQLite state persistence
├── .env                  # Environment variables
├── pyproject.toml        # Poetry dependencies
└── README.md
```

## 3. Environment Variables

Copy the example file:

```bash
cp example.env .env
```

Key variables in `.env`:

```bash
# Ollama
OLLAMA_BASE_URL=http://localhost:11434
PRIMARY_LLM=llama3.2
EMBEDDING_MODEL=mxbai-embed-large

# ChromaDB
CHROMA_PERSIST_DIRECTORY=./chroma_db

# State Layer
STATE_BACKEND=sqlite
STATE_DB_PATH=./state/the_board_state.db
```

**Notes:**

- Ensure `./state/` exists and is writable.
- SQLite runs in **WAL mode** by default.
- Add `/state/*` and `/chroma_db/*` to `.gitignore`.

---

## 4. Install Dependencies

```bash
# Install all dependencies
poetry install

# Enter the Poetry virtual environment
poetry shell
```

---

## 5. Model Setup (Ollama)

Start the Ollama server and pull required models:

```bash
# Start Ollama in another terminal
ollama serve

# Pull core models
ollama pull llama3.2
ollama pull mxbai-embed-large
```

---

## 6. Running the Application

From project root:

```bash
# Run FastAPI with auto-reload
poetry run fastapi dev src/main.py
```

Access:

- API: [http://localhost:8000](http://localhost:8000)
- Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 7. Knowledge Base (RAG) Ingestion

To add new documents:

```bash
# Place files in data/to_ingest/
poetry run python src/scripts/ingest_documents.py
```

This will:

- Chunk documents
- Generate embeddings with Ollama
- Persist to **ChromaDB** (`./chroma_db`)

---

## 8. State Layer

- Default: **SQLite** with WAL enabled
- Configurable via `.env`:

```bash
STATE_BACKEND=sqlite
STATE_DB_PATH=./state/the_board_state.db
```

- Supports retries, cancel, inspect via FastAPI `/state` endpoints
- In production, can be swapped for **Redis** or **Postgres**

---

## 9. Testing

Run tests:

```bash
poetry run pytest -v
```

Test workflows live in `tests/test_queries.json`.

---

## 10. Deployment Notes

- **Local-first**: Ollama + SQLite run entirely on-device
- **Persistence**: Ensure `chroma_db/` and `state/` are on persistent storage
- **Security**: Never commit `.env`, `/state/`, or `/chroma_db/` to Git
- **Production**: Use managed DB (Redis/Postgres), containerize with Docker

---

## 11. Quick Reference

```bash
# Setup
poetry install && cp example.env .env

# Run app
ollama serve &
poetry run fastapi dev src/main.py

# Ingest documents
poetry run python src/scripts/ingest_documents.py

# Run tests
poetry run pytest -v
```
