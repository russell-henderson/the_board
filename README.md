# the_board

the_board is a local-first strategic planning application. Submit a goal and the COO, CFO, CTO, and CMO Agents produce focused analyses that are synthesized into an executive plan.

The application runs with FastAPI and SQLite. Ollama is optional: when it is unavailable, the app still produces a structured fallback plan so the workflow remains usable offline.

## Run it

```bash
poetry install
poetry run dev
```

In a second terminal:

```bash
poetry run ui
```

Open the dashboard at `http://127.0.0.1:8501`, or use the API at `http://127.0.0.1:8000/docs`.

See [Quickstart](docs/QUICKSTART.md) for setup and [Architecture](docs/ARCHITECTURE.md) for the data flow and API reference.

## Verify

```bash
python -m pytest
```

## Repository layout

```text
src/            application code
tests/          automated tests
scripts/        API and dashboard launchers
docs/           current user and engineering documentation
_archive/       retired pre-consolidation artifacts retained for recovery
```
