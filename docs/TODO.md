# ✅ the_board — TODO

> Working backlog for the next implementation pass. Organized by priority. Check items as you complete them.

---

## 🔥 Immediate (Today)
- [ ] **Create `WELCOME.md`** — greeting from creators (intro, mission, how to begin)
- [ ] **Add Dashboard LED strip (A)** — 5 agent LEDs (CEO, CFO, CTO, COO, CMO) that light on activity
- [ ] **Add “Direct Chat — All Agents” panel (B)** — broadcast input + scrollable log, wired to backend
- [ ] **Wire FastAPI WebSockets** — `/ws/agent-activity` and `/ws/chat` endpoints
- [ ] **Simulate activity endpoint** — `POST /realtime/simulate-activity` for UI testing
- [ ] **Brand pass** — apply palette & tone from `BRAND_GUIDELINES.md`

---

## 🧠 Strategic Goal Submission (MVP)
- [ ] UI: “Submit Strategic Goal” form (goal + context)
- [ ] API: `POST /plan` → `OdysseyGoalRequest` (see `dataModel.py`)
- [ ] CEO stub: decompose into mock tasks and persist via `StateStore`
- [ ] UI: display Plan summary + live Task list

---

## 🧩 Backend & State Layer
- [ ] Implement `StateStore` CRUD for: plans, tasks, events (SQLite WAL)
- [ ] Define Task FSM per `WORKFLOWS.md` (`pending → in_progress → completed/failed/...`)
- [ ] Events: `plan_created`, `task_state_changed`, `task_retry`, `task_cancelled`, etc.
- [ ] Add `/state` routes: inspect plan, list events, cancel, retry
- [ ] Orchestrator hooks: broadcast LED activity on task start/done/error

---

## 🖥️ Frontend (Dashboard)
- [ ] LED component with auto-dim pulse for active agent
- [ ] Chat panel with send box, timestamps, and auto-scroll
- [ ] Recent Activity feed bound to `/state` events
- [ ] Metrics tiles: Active Agents, Plans Created, Success Rate, Avg Response
- [ ] Error toasts (connection lost, WS retry)
- [ ] **UI Idea A:** Animated flow indicator showing agent hand-off sequence
- [ ] **UI Idea B:** Dedicated “Direct Chat to All Agents” section with broadcast-style UI
- [ ] **UI Idea C:** Visual timeline (Gantt-style) of tasks per agent as they execute
- [ ] **UI Idea D:** Collapsible side panel with quick insights and brand-styled recommendations

---

## 🗂️ Knowledge Layer
- [ ] Ingestion job: drop markdown/PDFs in `knowledge/` → embed into ChromaDB
- [ ] Provenance metadata (source, tags, timestamp)
- [ ] Simple search endpoint `/kb/search?q=` returning citations

---

## 🤖 Agents (Essentials)
- [ ] CEO (Odyssey): task routing & synthesis skeleton
- [ ] CFO (Abacus): finance analysis stub
- [ ] CTO (Nexus): technical feasibility stub
- [ ] CMO (Muse): market positioning stub
- [ ] COO (Momentum): ops & execution stub

---

## 🧱 Data Models (align with `TECHSPEC.md`)
- [ ] `OdysseyGoalRequest`
- [ ] `AgentTask` (task_id, agent, description, state, attempts, last_error)
- [ ] `AgentResponse` (analysis, confidence, citations[])
- [ ] `FinalPlan` (synthesized_strategy, contributing_agents[], risks[], confidence_score)

---

## 🔐 Security & Settings
- [ ] `.env` config (OLLAMA, PRIMARY_LLM, CHROMA_PERSIST_DIRECTORY, STATE_DB_PATH)
- [ ] Gate `/state/*` with shared secret for dev
- [ ] Redact sensitive payloads in events

---

## 🧪 Testing
- [ ] Unit tests for StateStore transitions
- [ ] WS tests (activity + chat)
- [ ] Integration: submit goal → tasks → synthesis → close

---

## 🚀 DevOps & Runbooks
- [ ] `poetry run dev` and `poetry run start` scripts
- [ ] Windows service (NSSM) per `DEPLOYMENT.md`
- [ ] Health endpoints: `/health`, `/healthz`, `/readyz`
- [ ] Log rotation + basic metrics

---

## ✨ Nice-to-Have (Post‑MVP)
- [ ] HTMX/SSE stream for events instead of polling
- [ ] Export final plan to PDF/DOCX/Markdown templates
- [ ] Agent icons & subtle animations on the LED strip
- [ ] Feedback loop (`UserCorrection`) → adjust routing heuristics
- [ ] Role-based access control (RBAC)

---

### Notes
- Keep brand voice authoritative & clear (see `docs/BRAND_GUIDELINES.md`).
- All lifecycle mutations must go through `StateStore` (see `docs/WORKFLOWS.md`).
- Use `src/main.py` as the canonical entry point (see `docs/DEPLOYMENT.md`).

