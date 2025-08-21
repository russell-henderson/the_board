# WORKFLOWS.md

Operational workflows for **the_board**. This document defines the end‑to‑end execution paths, task and plan lifecycles, state transitions, observability, and developer procedures. It is aligned with the current TECHSPEC and the SQLite‑first state layer.

---

## 0) Purpose and Scope

- Define how a user query becomes a durable plan with tasks.
- Specify agent selection, execution, synthesis, and escalation.
- Pin the task state machine and events that must be recorded.
- Describe cancel and retry flows that survive restarts.
- Provide concrete request and response examples for the `/state` API.
- Set developer rules so all lifecycle mutations go through the `StateStore`.

---

## 1) Key Concepts

### 1.1 Actors

- **User**: submits a goal or query.
- **FastAPI Backend**: receives requests, exposes `/state` and app endpoints.
- **CEO Agent (Odyssey)**: decomposes the goal into a plan and routes tasks.
- **Specialist Agents**: CFO, CTO, CMO, COO, and others.
- **Synthesis Layer**: validates, reconciles, and brands final output.
- **State Store**: durable persistence for plans, tasks, responses, and events.

### 1.2 Enums

`TaskState`:

- `pending`
- `in_progress`
- `completed`
- `failed`
- `escalated`
- `cancelled`

---

## 2) High‑Level Flow

```mermaid
sequenceDiagram
    participant U as User
    participant API as FastAPI
    participant CEO as CEO Agent (Odyssey)
    participant AG as Specialist Agents
    participant ST as StateStore (SQLite)
    participant SYN as Synthesis

    U->>API: POST /plan { high_level_goal }
    API->>ST: create_plan
    API->>CEO: orchestrate(plan)
    CEO->>ST: add_task(plan_id, agent, description)*
    par parallel or staged
        CEO->>ST: set_task_state(task_id, in_progress)
        CEO->>AG: run_task(task)
        AG-->>CEO: AgentResponse {analysis, confidence, citations}
        CEO->>ST: record_agent_response(task_id, ...)
    and on errors
        CEO->>ST: set_task_state(task_id, failed, error)
        CEO->>ST: mark_retry(task_id) [policy driven]
    end
    CEO->>SYN: synthesize(all task outputs)
    SYN-->>CEO: FinalPlan
    CEO->>ST: close_plan(plan_id)
    API-->>U: FinalPlan
````

---

## 3) End‑to‑End Execution Workflow

1. **Receive Goal**

   - Endpoint: `POST /plan` with `OdysseyGoalRequest`.
   - Validate payload and log an event `plan_created`.

2. **Create Plan**

   - `StateStore.create_plan(original_query)`.
   - Returns `plan_id`.

3. **Decompose Into Tasks**

   - CEO selects minimal relevant agents.
   - For each task: `StateStore.add_task(plan_id, agent, description)`.

4. **Execute Tasks**

   - For each task, CEO:

     - Sets `in_progress` with `set_task_state(task_id, in_progress)`.
     - Delegates to the target agent.
     - Agent returns `AgentResponse` or raises error.
     - On success: `record_agent_response(...)` which completes the task if not terminal.
     - On failure: `set_task_state(task_id, failed, error=str(e))` and consider retry policy.

5. **Synthesis**

   - Synthesis merges agent outputs, resolves conflicts, formats with brand rules, and returns `FinalPlan`.

6. **Close Plan**

   - `StateStore.close_plan(plan_id)`.

7. **Inspectability**

   - `/state/plans/{plan_id}` for live status.
   - `/state/plans/{plan_id}/events` for audit log.

---

## 4) Plan Lifecycle

States for a plan are a logical flag, not a strict FSM, and recorded as `status` in the `plans` table.

- `open` on creation.
- `closed` once final synthesis is emitted.
- `cancelled` when a user cancels the plan.
- Cancelling a plan sets all non‑terminal tasks to `cancelled`.

**Events**:

- `plan_created`
- `plan_closed`
- `plan_cancelled`

---

## 5) Task Lifecycle State Machine

### 5.1 State Diagram

stateDiagram-v2
    [*] --> pending
    pending --> in_progress: worker starts
    in_progress --> completed: success
    in_progress --> failed: exception or bad result
    in_progress --> escalated: confidence low or max attempts hit
    pending --> cancelled: manual cancel or plan cancel
    in_progress --> cancelled: manual cancel or plan cancel
    failed --> pending: retry
    escalated --> pending: human-approved retry
    cancelled --> pending: manual retry allowed
    completed --> [*]
    cancelled --> [*]

### 5.2 Transition Rules

- `pending -> in_progress`: must be set at agent start.
- `in_progress -> completed`: set automatically by `record_agent_response` unless the current state is `failed` or `cancelled`.
- `in_progress -> failed`: on exceptions or policy‑defined failure.
- `in_progress -> escalated`: when attempts exceed `MAX_ATTEMPTS` or confidence below threshold triggers escalation.
- `pending|in_progress -> cancelled`: manual cancel or plan cancel.
- `failed|escalated|cancelled -> pending`: retry resets state and clears `last_error`, increments `attempts`.

**Events**:

- `task_created`
- `task_state_changed`
- `task_retry`
- `task_cancelled`
- `task_completed_on_response`

---

## 6) Retry and Escalation Policy

- **Default `MAX_ATTEMPTS`**: 2
- **Confidence threshold**: 0.80 high, 0.50 to 0.79 moderate, below 0.50 uncertain.
- **Retry triggers**:

  - Transient tool or network error.
  - Moderate confidence output where an additional pass is likely to improve results.
- **Escalation triggers**:

  - `attempts >= MAX_ATTEMPTS`.
  - Confidence below threshold on the last allowed attempt.
  - Conflicting outputs that cannot be reconciled automatically.

**Flow**:

1. On failure: mark `failed` with `last_error`.
2. If attempts remain and policy allows: `mark_retry` which sets `pending` and increments `attempts`.
3. If attempts exhausted or confidence too low: set `escalated`. Human approval is required to `retry` from `escalated`.

---

## 7) Cancel Workflow

### 7.1 Cancel a Task

- Preconditions: task is `pending` or `in_progress`.
- Call: `POST /state/tasks/{task_id}/cancel`.
- Effects:

  - State becomes `cancelled`.
  - Event `task_cancelled` recorded.
  - Workers must check state periodically and abort safely.

### 7.2 Cancel a Plan

- Call: `StateStore.cancel_plan(plan_id)`.
- Effects:

  - Plan status `cancelled`.
  - All `pending` and `in_progress` tasks become `cancelled`.
  - Event `plan_cancelled` recorded.

---

## 8) Orchestrator Flow Pseudocode

`
from dataModel import AgentResponse, SynthesizedOutput
from state_manager import state_store, TaskState
from agents.ceo_agent import ceo
from synthesis import synthesis

MAX_ATTEMPTS = 3

def run_user_goal(user_goal: str) -> SynthesizedOutput:
    store = state_store()
    plan = store.create_plan(original_query=user_goal)
        # CEO decomposes into tasks
    tasks = ceo.decompose(user_goal)  # returns [{agent, description}, ...]
    for t in tasks:
        store.add_task(plan.plan_id, t["agent"], t["description"])
    for task in store.list_plan_tasks(plan.plan_id):
        current = store.get_task(task.task_id)
        # Skip if task already cancelled
        if current.state == TaskState.cancelled:
            continue
        store.set_task_state(task.task_id, TaskState.in_progress)
        try:
            resp: AgentResponse = run_agent_task(
                agent=current.agent, description=current.description
            )
            store.record_agent_response(
                task.task_id,
                agent=current.agent,
                content=resp.analysis,
                confidence=resp.confidence,
                citations=resp.citations,
            )
            store.set_task_state(task.task_id, TaskState.completed)
        except Exception as e:
            store.set_task_state(task.task_id, TaskState.failed, error=str(e))
            retry_task = store.get_task(task.task_id)
            if retry_task.attempts < MAX_ATTEMPTS:
                store.mark_retry(task.task_id)
            else:
                store.set_task_state(task.task_id, TaskState.escalated)
    # Build final synthesized output
    final = synthesis.build(plan_id=plan.plan_id)
    store.close_plan(plan.plan_id)
    return final`

---

## 9) Synthesis and Conflict Resolution

1. **Collect** all `completed` task outputs.
2. **Validate** content quality and citation presence where expected.
3. **Resolve Conflicts**:

   - Ask agents for counterpoints.
   - Compute consensus score.
   - If conflict remains, CEO adjudicates.
   - If still unresolved, escalate to user.
4. **Brand Formatting**:

   - Apply Brand Guidelines for tone and typography.
   - Confidence phrasing:

     - ≥ 0.80 high confidence
     - 0.50 to 0.79 moderate confidence
     - below 0.50 uncertain, human review advised

---

## 10) Knowledge Ingestion Workflow

1. **Add documents** to the ingest path.
2. **Curation** checks scope and sensitivity.
3. **Embed** with the configured embedding model.
4. **Upsert** vectors into ChromaDB with provenance metadata.
5. **Verify** retrieval quality on a small sample query set.

---

## 11) State Events: Required Logging

Every lifecycle change must produce an event. Examples:

{
  "event_id": "evt_xxxxxxxx",
  "plan_id": "plan_xxxxxxxx",
  "task_id": "task_xxxxxxxx",
  "kind": "task_state_changed",
  "payload": {
    "state": "in_progress",
    "error": null
  },
  "created_at": "2025-08-21T01:23:45Z"
}

Event kinds:

- `plan_created`, `plan_closed`, `plan_cancelled`
- `task_created`, `task_state_changed`, `task_retry`, `task_cancelled`
- `task_completed_on_response`
- Custom: `info`, `warning`, `error` for orchestration notes

---

## 12) `/state` API Workflows

### 12.1 Inspect a Plan

GET /api/state/plans/{plan_id}

## Response

`
{
  "plan": {
    "plan_id": "plan_xxxxxxxx",
    "status": "open",
    "created_at": "2025-08-21T01:23:45Z"
  },
  "tasks": [
    {
      "task_id": "task_xxxxxxxx",
      "plan_id": "plan_xxxxxxxx",
      "agent": "CTO",
      "description": "Evaluate model choices",
      "state": "in_progress",
      "attempts": 0,
      "last_error": null,
      "created_at": "2025-08-21T01:23:50Z",
      "updated_at": "2025-08-21T01:24:10Z"
    }
  ]
}
`

### 12.2 List Events

GET /api/state/plans/{plan_id}/events?task_id={task_id}&limit=200

## Response to api

{ "events": [ { "event_id": "...", "kind": "task_created", "payload": {...} } ] }

### 12.3 Cancel Task

POST /state/tasks/{task_id}/cancel

## Response to Post

{ "ok": true }

### 12.4 Retry Task

POST /state/tasks/{task_id}/retry

Rules:

- Allowed for `failed`, `escalated`, or `cancelled` tasks only.

## Response to Rules

{ "ok": true }

---

## 13) Observability

### 13.1 Logging

- Format: `[AGENT | icon | level] message`
- Include plan and task identifiers in each line.
- Log every transition and API call outcome.

### 13.2 Metrics

- Counters:

  - `plans_created`, `plans_closed`, `plans_cancelled`
  - `tasks_created`, `tasks_completed`, `tasks_failed`, `tasks_cancelled`
  - `task_retries`
- Gauges:

  - `open_plans`, `pending_tasks`, `in_progress_tasks`
- Latency histograms:

  - per agent execution, per plan total duration

---

## 14) Reliability and Recovery

- **Durability**: SQLite with WAL persists state across restarts.
- **Idempotency**:

  - `_stable_id` reduces duplicate inserts for identical operations.
  - For tasks that may share the same description for the same agent, include a nonce or timestamp when appropriate.
- **Recovery after crash**:

  1. On startup, read all tasks with `pending` and `in_progress`.
  2. Decide whether to resume or mark `failed` if a safe resume is not possible.
  3. Re‑enqueue or retry per policy.
- **Backups**:

  - Copy `the_board_state.db` plus WAL and SHM files during quiet hours.
  - Verify backup integrity by opening a read‑only connection.

---

## 15) Security and Privacy Gates

- Do not log raw sensitive user inputs in `events.payload`.
- Truncate or hash long payloads.
- Restrict `/state/*` endpoints to trusted users or a shared secret during development.
- Do not expose ChromaDB or state files over public networks.

---

## 16) Developer Workflow

- All lifecycle changes must go through `state_store()`:

  - `create_plan`, `add_task`, `set_task_state`, `record_agent_response`, `mark_retry`, `cancel_task`, `cancel_plan`, `list_events`.
- Do not mutate local dicts for plan or task state.
- Before long work, and at checkpoints, check the task state for cancel.
- Include citations in `AgentResponse` when a claim depends on sources.

---

## 17) Testing Workflow

### 17.1 Unit Tests

- Create plan, add tasks, move through each transition, ensure events logged.
- Record response from `failed` and `cancelled` states and confirm guard prevents auto complete.

### 17.2 Integration Tests

- Full run from `POST /plan` to synthesis and `close_plan`.
- Simulate process restart and verify persistence.
- Cancel tests:

  - Cancel in `pending` and `in_progress`.
- Retry tests:

  - Ensure `attempts` increments and state resets to `pending`.

### 17.3 Load and Concurrency

- Parallel tasks for different plans.
- Confirm WAL allows concurrent reads and writes.

---

## 18) Operational SOPs

- **Cancel**: call task cancel, or plan cancel for global stop.
- **Retry**: use API to mark retry, then orchestrator re‑queues work.
- **Hotfix**: if a task is stuck, set `failed`, then `retry`.
- **Migration**: new columns should be added with safe defaults. Consider Alembic once schema evolves.

---

## 19) Versioning

- This document is versioned with the codebase.
- Any change to the state machine, events, or API requires:

  1. TECHSPEC update
  2. WORKFLOWS update
  3. Minor version bump
  4. Tests updated to reflect new behavior

---

## 20) Quick Reference Snippets

### 20.1 Orchestrator Hooks

`
store.set_task_state(task_id, TaskState.in_progress)
store.record_agent_response(task_id, agent, content, confidence=0.82, citations=["..."])
store.set_task_state(task_id, TaskState.failed, error="Tool timeout")
store.mark_retry(task_id)
store.cancel_task(task_id)
store.close_plan(plan_id)`

### 20.2 cURL Examples

Inspect:

`
curl -s http://localhost:8000/state/plans/<PLAN_ID> | jq .
`

Events:

`
curl -s "http://localhost:8000/state/plans/<PLAN_ID>/events?limit=100" | jq .
`

Cancel:

`
curl -s -X POST http://localhost:8000/state/tasks/<TASK_ID>/cancel
`

Retry:

`
curl -s -X POST http://localhost:8000/state/tasks/<TASK_ID>/retry
`

## Appendix: Agent Glossary

When reading through workflows, it helps to know the executive personas:

- **Odyssey (CEO):** Central orchestrator; decomposes goals into tasks.  
- **Momentum (COO):** Turns plans into executional workflows.  
- **Abacus (CFO):** Handles financial modeling and risk assessment.  
- **Nexus (CTO):** Provides technical guidance and architecture.  
- **Curio (Chief Researcher):** Maintains and enriches the knowledge store.  
- **Muse (CMO):** Focused on marketing, campaigns, and outreach.  
- **Guardian (CISO):** Protects system integrity and security.  
- **Pulse (CHRO):** Manages people, culture, and team formation.  
- **Insight (CIO):** Ensures data flows and information pipelines.  
- **Envoy (Chief Diplomat):** Handles partnerships and negotiations.  
- **Vision (Chief Strategist):** Ensures long-term foresight and positioning.  
- **Forge (Chief Engineer):** Proposes technical builds and prototypes.  
- **Beacon (Chief Ethicist):** Validates ethical and fair outcomes.  
- **Flux (Chief Innovator):** Identifies disruptive opportunities.  
- **Anchor (Chief Legal Officer):** Legal and regulatory compliance.  
- **Scribe (Chief Knowledge Officer):** Records, synthesizes, and formats outputs.  
- **Spark (Chief Creative Officer):** Enhances storytelling and design.  
- **Vector (Chief Logistics Officer):** Aligns timing, resources, and supply chains.  
- **Echo (Chief Communications Officer):** Manages communication style and PR.  
- **Horizon (Chief Sustainability Officer):** Oversees ESG dimensions.  

**Status**: Current and aligned with the SQLite state layer, `/state` endpoints, and TECHSPEC v2.0. 08/21/2025
