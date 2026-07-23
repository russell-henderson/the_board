# Architecture

## Runtime flow

1. `POST /plan` creates a SQLite plan and four specialist tasks.
2. A background worker executes COO, CFO, CTO, and CMO analyses.
3. Each response and lifecycle event is persisted in SQLite.
4. Odyssey synthesis combines the responses into a `FinalPlan`.
5. The Streamlit dashboard polls the API for plan status and the final result.

SQLite is the source of truth for plans, tasks, events, agent responses, and final plans. Task transitions are validated by `StateStore`.

## Components

| Path | Responsibility |
| --- | --- |
| `src/main.py` | FastAPI routes and background-plan start |
| `src/state/store.py` | SQLite schema and lifecycle transitions |
| `src/agents/specialists.py` | COO, CFO, CTO, and CMO analysis |
| `src/orchestration/` | task execution and final synthesis |
| `src/ui/streamlit_app.py` | local user interface |

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | service health |
| `GET` | `/readyz` | SQLite readiness |
| `POST` | `/plan` | create a strategic plan |
| `GET` | `/state/plans/{plan_id}` | inspect plan, tasks, and summary |
| `GET` | `/state/plans/{plan_id}/events` | inspect lifecycle events |
| `POST` | `/state/tasks/{task_id}/cancel` | cancel an eligible task |
| `POST` | `/state/tasks/{task_id}/retry` | retry a failed, escalated, or cancelled task |
| `GET` | `/plan/{plan_id}/result` | fetch the synthesized result |

## Ollama behavior

When `OLLAMA_BASE_URL` is reachable, agents request local model analyses. If it is unavailable or returns an invalid response, each agent produces a deterministic structured fallback, and synthesis still returns a plan. This keeps the application operable without a model service while clearly lowering the practical confidence of generated recommendations.
