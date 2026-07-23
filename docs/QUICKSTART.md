# Quickstart

## Requirements

- Python 3.11–3.13
- Poetry
- Optional: [Ollama](https://ollama.com) and a local model such as `llama3.2`

## Install and start

```bash
poetry install
poetry run dev
```

The API listens on `http://127.0.0.1:8000`. Start the dashboard separately:

```bash
poetry run ui
```

Open `http://127.0.0.1:8501` and create a plan. The dashboard displays its task status and final executive plan.

## API example

```bash
curl -X POST http://127.0.0.1:8000/plan \
  -H "Content-Type: application/json" \
  -d '{"high_level_goal":"Launch a service for independent retailers","user_context":"Budget is $50,000; launch within six months."}'
```

Use the returned `plan_id` with `GET /state/plans/{plan_id}`. When complete, retrieve `GET /plan/{plan_id}/result`.

## Configuration

Copy `example.env` to `.env` if you want to customize the SQLite path or Ollama connection. The current runtime reads environment variables directly; exporting them in your shell is sufficient.

## Tests

```bash
python -m pytest
```
