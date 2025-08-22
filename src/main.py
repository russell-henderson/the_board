from __future__ import annotations

import json
import logging
import os
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# =============================================================
# Minimal .env loader to avoid extra deps
# =============================================================
# Repo root is one level up from this file: the_board/src/main.py
REPO_ROOT = Path(__file__).resolve().parents[1]
ENVFILE = os.environ.get("ENVFILE", str(REPO_ROOT / ".env"))


def load_env_file(path: str) -> None:
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


load_env_file(ENVFILE)

# Allow importing from the models package
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# =============================================================
# Try to import the project's data models. If unavailable, fall back
# to small inline versions that satisfy the API contracts.
# =============================================================
try:  # project-defined models (preferred)
    from src.models.odyssey.core import OdysseyGoalRequest
    from src.models.dataModel import (
        AgentType,
        AgentResponse,
        FinalPlan,
    )
    from src.orchestration.runner import run_plan
except Exception:

    class AgentType(str):  # very small fallback for docs
        CEO = "CEO"
        COO = "COO"
        CFO = "CFO"
        CTO = "CTO"
        CMO = "CMO"

    class AgentResponse(BaseModel):
        agent_type: str
        analysis: str
        confidence: float = 0.8
        citations: List[str] = []

    # OdysseyGoalRequest is now imported from src.models.odyssey.core
    pass

    class FinalPlan(BaseModel):
        plan_id: str
        synthesized_strategy: str
        contributing_agents: List[str]
        identified_risks: List[str] = []
        confidence_score: float = 0.8

# =============================================================
# Pydantic response helpers used by /state endpoints
# =============================================================


class PlanSummary(BaseModel):
    plan_id: str
    status: str
    created_at: str
    closed_at: Optional[str] = None


class TaskSummary(BaseModel):
    task_id: str
    plan_id: str
    agent: str
    description: str
    state: str
    attempts: int
    last_error: Optional[str] = None
    created_at: str
    updated_at: str


class PlanInspectResponse(BaseModel):
    plan: PlanSummary
    tasks: List[TaskSummary]


class OkResponse(BaseModel):
    ok: bool = True


# =============================================================
# SQLite state store - default backend
# =============================================================
STATE_DB_PATH = os.environ.get("STATE_DB_PATH", "./state/the_board_state.db")
STATE_DB = (REPO_ROOT / STATE_DB_PATH).resolve()
STATE_DB.parent.mkdir(parents=True, exist_ok=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(STATE_DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


with _connect() as c:
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS plans (
            plan_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            original_query TEXT,
            created_at TEXT NOT NULL,
            closed_at TEXT
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            plan_id TEXT NOT NULL,
            agent TEXT NOT NULL,
            description TEXT NOT NULL,
            state TEXT NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            last_error TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY,
            plan_id TEXT,
            task_id TEXT,
            kind TEXT NOT NULL,
            payload TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    c.commit()


# =============================================================
# Logging - follow brand tone in developer logs
# =============================================================
logger = logging.getLogger("the_board")
if not logger.handlers:
    level = getattr(logging, os.environ.get(
        "LOG_LEVEL", "INFO").upper(), logging.INFO)
    logger.setLevel(level)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[the_board | %(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


# =============================================================
# FastAPI app
# =============================================================
app = FastAPI(
    title="the_board API", 
    version="2.0.0",
    description="""
    🎯 **the_board** - Multi-Agent Strategic Planning System
    
    A sophisticated orchestration platform that leverages specialized AI agents 
    to provide comprehensive strategic analysis and planning.
    
    ## Features
    
    * **Multi-Agent Analysis**: CFO, CTO, CMO, and COO agents provide specialized insights
    * **Task Orchestration**: Intelligent task management and execution
    * **State Management**: Persistent tracking of plans and task execution
    * **Real-time Monitoring**: Health checks and status reporting
    
    ## Getting Started
    
    1. Create a strategic plan using `POST /plan`
    2. Monitor progress with `GET /state/plans/{plan_id}`
    3. Retrieve comprehensive analysis and recommendations
    
    ## Health Checks
    
    * `/health` - Basic service health
    * `/readyz` - Service readiness (includes database connectivity)
    """,
    contact={
        "name": "the_board Support",
        "url": "https://github.com/russell-henderson/the_board",
    },
    license_info={
        "name": "MIT",
    },
)


# -------------------------------------------------------------
# Health and readiness
# -------------------------------------------------------------
class Health(BaseModel):
    status: str = "ok"
    message: str = "the_board is running"


@app.get("/", response_model=Health, tags=["system"])
def root() -> Health:
    return Health()


@app.get("/health", tags=["system"])
def health() -> JSONResponse:
    return JSONResponse({"status": "healthy"})


@app.get("/healthz", tags=["system"])
def healthz() -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "the_board"})


@app.get("/readyz", tags=["system"])
def readyz() -> JSONResponse:
    try:
        with _connect() as conn:
            conn.execute("PRAGMA wal_checkpoint(PASSIVE);")
        return JSONResponse({"status": "ready"})
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"not_ready: {e}")


# -------------------------------------------------------------
# Demo echo
# -------------------------------------------------------------
class EchoIn(BaseModel):
    text: str


class EchoOut(BaseModel):
    text: str
    model: Optional[str] = os.environ.get("PRIMARY_LLM")


@app.post("/echo", response_model=EchoOut, tags=["demo"])
def echo(body: EchoIn) -> EchoOut:
    return EchoOut(text=body.text)


# -------------------------------------------------------------
# Planning entrypoint - POST /plan
# -------------------------------------------------------------
MAX_ATTEMPTS = int(os.environ.get("MAX_ATTEMPTS", "2"))
ESSENTIAL_FIVE = ["COO", "CFO", "CTO", "CMO"]  # CEO is the orchestrator


@app.post("/plan", status_code=202, tags=["plan"])
def create_and_run_plan(
    req: OdysseyGoalRequest,
    background_tasks: BackgroundTasks
):
    """Accepts a strategic goal, creates a plan, and starts the
    orchestration in the background.
    """
    plan_id = f"plan_{uuid.uuid4().hex[:12]}"
    created = utc_now()
    logger.info(f"[CEO] plan_created id={plan_id}")

    with _connect() as conn:
        conn.execute(
            "INSERT INTO plans(plan_id, status, original_query, created_at) VALUES (?, ?, ?, ?)",
            (plan_id, "open", req.high_level_goal, created),
        )
        _record_event(conn, plan_id, None, "plan_created",
                      {"goal": req.high_level_goal})

        # naive task decomposition into the Essential Four (ex CEO)
        for agent in ESSENTIAL_FIVE:
            task_id = f"task_{uuid.uuid4().hex[:12]}"
            now = utc_now()
            description = _default_task_description(agent, req.high_level_goal)
            conn.execute(
                """
                INSERT INTO tasks(task_id, plan_id, agent, description, state, attempts, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 0, ?, ?)
                """,
                (task_id, plan_id, agent, description, "pending", now, now),
            )
            _record_event(
                conn,
                plan_id,
                task_id,
                "task_created",
                {"agent": agent, "description": description},
            )
        conn.commit()

    # Instead of returning a FinalPlan, start the background task
    background_tasks.add_task(run_plan, plan_id)
    
    # Return an immediate response so the user isn't waiting
    return {
        "message": "Plan accepted and orchestration started.",
        "plan_id": plan_id
    }


def _default_task_description(agent: str, goal: str) -> str:
    if agent == "COO":
        return f"Translate goal into operations, timeline, and owners for: {goal}"
    if agent == "CFO":
        return f"Draft a budget and ROI framing for: {goal}"
    if agent == "CTO":
        return f"Evaluate technical options, risks, and a recommended stack for: {goal}"
    if agent == "CMO":
        return f"Outline positioning, channels, and launch messaging for: {goal}"
    return f"Contribute domain analysis for: {goal}"


def _bootstrap_synth(goal: str) -> str:
    return (
        "# Executive Plan\n\n"
        f"**Goal**: {goal}\n\n"
        "## Findings\n\n- Tasks initialized for COO, CFO, CTO, and CMO.\n"
        "- State is durable in SQLite with WAL.\n\n"
        "## Risks\n\n- Agent execution is stubbed in this skeleton.\n"
        "- Clarify inputs and constraints early.\n\n"
        "## Opportunities\n\n- Parallelize agent work once the bus is added.\n"
        "- Brand adapter can export to PDF or DOCX.\n\n"
        "## Recommendations\n\n- Wire agents and message bus next.\n"
        "- Add retrieval checks for ChromaDB.\n"
    )


# -------------------------------------------------------------
# /state API - inspect, events, cancel, retry
# -------------------------------------------------------------
@app.get("/state/plans/{plan_id}", response_model=PlanInspectResponse, tags=["state"])
def inspect_plan(plan_id: str) -> PlanInspectResponse:
    with _connect() as conn:
        p = conn.execute(
            "SELECT * FROM plans WHERE plan_id = ?", (plan_id,)).fetchone()
        if not p:
            raise HTTPException(status_code=404, detail="plan_not_found")
        tasks = conn.execute(
            "SELECT * FROM tasks WHERE plan_id = ? ORDER BY created_at",
            (plan_id,),
        ).fetchall()

    plan = PlanSummary(
        plan_id=p["plan_id"],
        status=p["status"],
        created_at=p["created_at"],
        closed_at=p["closed_at"],
    )
    items = [
        TaskSummary(
            task_id=t["task_id"],
            plan_id=t["plan_id"],
            agent=t["agent"],
            description=t["description"],
            state=t["state"],
            attempts=int(t["attempts"] or 0),
            last_error=t["last_error"],
            created_at=t["created_at"],
            updated_at=t["updated_at"],
        )
        for t in tasks
    ]
    return PlanInspectResponse(plan=plan, tasks=items)


@app.get(
    "/state/plans/{plan_id}/events",
    tags=["state"],
)
def list_events(
    plan_id: str,
    task_id: Optional[str] = Query(None),
    limit: int = Query(200, le=1000),
) -> Dict[str, Any]:
    q = "SELECT * FROM events WHERE plan_id = ?"
    args: List[Any] = [plan_id]
    if task_id:
        q += " AND task_id = ?"
        args.append(task_id)
    q += " ORDER BY created_at DESC LIMIT ?"
    args.append(limit)

    with _connect() as conn:
        rows = conn.execute(q, tuple(args)).fetchall()

    events = [
        {
            "event_id": r["event_id"],
            "plan_id": r["plan_id"],
            "task_id": r["task_id"],
            "kind": r["kind"],
            "payload": _safe_json_loads(r["payload"]),
            "created_at": r["created_at"],
        }
        for r in rows
    ]
    return {"events": events}


@app.post("/state/tasks/{task_id}/cancel", response_model=OkResponse, tags=["state"])
def cancel_task(task_id: str) -> OkResponse:
    with _connect() as conn:
        t = conn.execute(
            "SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
        if not t:
            raise HTTPException(status_code=404, detail="task_not_found")
        if t["state"] in ("completed",):
            raise HTTPException(
                status_code=400, detail="task_already_terminal")
        now = utc_now()
        conn.execute(
            "UPDATE tasks SET state = ?, updated_at = ? WHERE task_id = ?",
            ("cancelled", now, task_id),
        )
        _record_event(conn, t["plan_id"], task_id, "task_cancelled", None)
        conn.commit()
    return OkResponse()


@app.post("/state/tasks/{task_id}/retry", response_model=OkResponse, tags=["state"])
def retry_task(task_id: str) -> OkResponse:
    with _connect() as conn:
        t = conn.execute(
            "SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
        if not t:
            raise HTTPException(status_code=404, detail="task_not_found")
        if t["state"] not in ("failed", "escalated", "cancelled"):
            raise HTTPException(
                status_code=400, detail="retry_not_allowed_from_state")
        attempts = int(t["attempts"] or 0) + 1
        now = utc_now()
        conn.execute(
            "UPDATE tasks SET state = ?, attempts = ?, last_error = NULL, updated_at = ? WHERE task_id = ?",
            ("pending", attempts, now, task_id),
        )
        _record_event(conn, t["plan_id"], task_id,
                      "task_retry", {"attempts": attempts})
        conn.commit()
    return OkResponse()


# -------------------------------------------------------------
# Helpers
# -------------------------------------------------------------

def _record_event(conn: sqlite3.Connection, plan_id: Optional[str], task_id: Optional[str], kind: str, payload: Optional[dict]) -> None:
    evt = {
        "event_id": f"evt_{uuid.uuid4().hex[:12]}",
        "plan_id": plan_id,
        "task_id": task_id,
        "kind": kind,
        "payload": json.dumps(payload) if payload is not None else None,
        "created_at": utc_now(),
    }
    conn.execute(
        """
        INSERT INTO events(event_id, plan_id, task_id, kind, payload, created_at)
        VALUES (:event_id, :plan_id, :task_id, :kind, :payload, :created_at)
        """,
        evt,
    )


def _safe_json_loads(s: Optional[str]) -> Any:
    if not s:
        return None
    try:
        return json.loads(s)
    except Exception:
        return {"raw": s}
