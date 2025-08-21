# src/state/store.py
from __future__ import annotations
import os
import enum
import hashlib
from datetime import datetime
from typing import List, Optional, Dict, Any, Protocol

from pydantic import BaseModel
from sqlalchemy import (
    create_engine, MetaData, Table, Column, String, Integer, Text, DateTime,
    Enum as SAEnum, ForeignKey, JSON
)
from sqlalchemy.engine import Engine
from sqlalchemy.sql import select, insert, update, func

# ---- Shared enums/models (kept local to avoid coupling) ----------------------

class TaskState(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"
    escalated = "escalated"
    cancelled = "cancelled"

class PlanRecord(BaseModel):
    plan_id: str
    original_query: str
    created_at: datetime
    status: str  # open | closed | cancelled

class TaskRecord(BaseModel):
    task_id: str
    plan_id: str
    agent: str
    description: str
    state: TaskState
    attempts: int
    last_error: Optional[str] = None
    updated_at: datetime
    created_at: datetime

class AgentResponseRecord(BaseModel):
    response_id: str
    task_id: str
    agent: str
    confidence: Optional[float] = None
    content: str
    citations: Optional[List[str]] = None
    created_at: datetime

class EventRecord(BaseModel):
    event_id: str
    plan_id: str
    task_id: Optional[str] = None
    kind: str
    payload: Dict[str, Any]
    created_at: datetime

# ---- Store interface ---------------------------------------------------------

class StateStore(Protocol):
    def create_plan(self, original_query: str, plan_id: Optional[str] = None) -> PlanRecord: ...
    def close_plan(self, plan_id: str) -> None: ...
    def cancel_plan(self, plan_id: str) -> None: ...
    def get_plan(self, plan_id: str) -> Optional[PlanRecord]: ...
    def list_plan_tasks(self, plan_id: str) -> List[TaskRecord]: ...
    def add_task(self, plan_id: str, agent: str, description: str, task_id: Optional[str] = None) -> TaskRecord: ...
    def set_task_state(self, task_id: str, state: TaskState, *, error: Optional[str] = None) -> None: ...
    def record_agent_response(self, task_id: str, agent: str, content: str, *, confidence: Optional[float] = None, citations: Optional[List[str]] = None) -> AgentResponseRecord: ...
    def get_task(self, task_id: str) -> Optional[TaskRecord]: ...
    def log_event(self, plan_id: str, kind: str, payload: Dict[str, Any], task_id: Optional[str] = None) -> EventRecord: ...
    def list_events(self, plan_id: str, task_id: Optional[str] = None, limit: int = 200) -> List[EventRecord]: ...
    def mark_retry(self, task_id: str) -> None: ...
    def cancel_task(self, task_id: str) -> None: ...

# ---- SQLite implementation ---------------------------------------------------

def _stable_id(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()[:24]

class SQLiteStateStore(StateStore):
    def __init__(self, db_path: Optional[str] = None):
        db_path = db_path or os.getenv("STATE_DB_PATH", "./state/the_board_state.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        # pool_pre_ping for stale connection recovery
        self.engine: Engine = create_engine(f"sqlite:///{db_path}", future=True, pool_pre_ping=True)
        with self.engine.connect() as c:
            c.exec_driver_sql("PRAGMA journal_mode=WAL;")
        self.meta = MetaData()

        self.plans = Table(
            "plans", self.meta,
            Column("plan_id", String(64), primary_key=True),
            Column("original_query", Text, nullable=False),
            Column("status", String(16), nullable=False, default="open"),
            Column("created_at", DateTime, server_default=func.now(), nullable=False),
        )

        self.tasks = Table(
            "tasks", self.meta,
            Column("task_id", String(64), primary_key=True),
            Column("plan_id", String(64), ForeignKey("plans.plan_id"), index=True, nullable=False),
            Column("agent", String(64), nullable=False),
            Column("description", Text, nullable=False),
            Column("state", SAEnum(TaskState), nullable=False, default=TaskState.pending),
            Column("attempts", Integer, nullable=False, default=0),
            Column("last_error", Text),
            Column("created_at", DateTime, server_default=func.now(), nullable=False),
            Column("updated_at", DateTime, server_default=func.now(), onupdate=func.now(), nullable=False),
        )

        self.responses = Table(
            "responses", self.meta,
            Column("response_id", String(64), primary_key=True),
            Column("task_id", String(64), ForeignKey("tasks.task_id"), index=True, nullable=False),
            Column("agent", String(64), nullable=False),
            Column("confidence", Integer),
            Column("content", Text, nullable=False),
            Column("citations", JSON),
            Column("created_at", DateTime, server_default=func.now(), nullable=False),
        )

        self.events = Table(
            "events", self.meta,
            Column("event_id", String(64), primary_key=True),
            Column("plan_id", String(64), ForeignKey("plans.plan_id"), index=True, nullable=False),
            Column("task_id", String(64), ForeignKey("tasks.task_id"), index=True, nullable=True),
            Column("kind", String(64), nullable=False),
            Column("payload", JSON, nullable=False),
            Column("created_at", DateTime, server_default=func.now(), nullable=False),
        )

        self.meta.create_all(self.engine)

    # ---- helpers
    def _row_to_plan(self, r) -> PlanRecord:
        return PlanRecord(
            plan_id=r.plan_id, original_query=r.original_query,
            created_at=r.created_at, status=r.status
        )

    def _row_to_task(self, r) -> TaskRecord:
        return TaskRecord(
            task_id=r.task_id, plan_id=r.plan_id, agent=r.agent, description=r.description,
            state=TaskState(r.state), attempts=r.attempts, last_error=r.last_error,
            created_at=r.created_at, updated_at=r.updated_at
        )

    def _row_to_resp(self, r) -> AgentResponseRecord:
        return AgentResponseRecord(
            response_id=r.response_id, task_id=r.task_id, agent=r.agent,
            confidence=r.confidence, content=r.content, citations=r.citations, created_at=r.created_at
        )

    def _row_to_event(self, r) -> EventRecord:
        return EventRecord(
            event_id=r.event_id, plan_id=r.plan_id, task_id=r.task_id, kind=r.kind,
            payload=r.payload, created_at=r.created_at
        )

    # ---- public API
    def create_plan(self, original_query: str, plan_id: Optional[str] = None) -> PlanRecord:
        pid = plan_id or _stable_id(original_query, datetime.utcnow().isoformat())
        with self.engine.begin() as conn:
            conn.execute(insert(self.plans).values(
                plan_id=pid, original_query=original_query, status="open"
            ))
            conn.execute(insert(self.events).values(
                event_id=_stable_id("evt", pid, "created"),
                plan_id=pid, kind="plan_created", payload={"original_query": original_query}
            ))
            r = conn.execute(select(self.plans).where(self.plans.c.plan_id == pid)).first()
        return self._row_to_plan(r)

    def close_plan(self, plan_id: str) -> None:
        with self.engine.begin() as conn:
            conn.execute(update(self.plans).where(self.plans.c.plan_id == plan_id).values(status="closed"))
            conn.execute(insert(self.events).values(
                event_id=_stable_id("evt", plan_id, "closed"),
                plan_id=plan_id, kind="plan_closed", payload={}
            ))

    def cancel_plan(self, plan_id: str) -> None:
        with self.engine.begin() as conn:
            conn.execute(update(self.plans).where(self.plans.c.plan_id == plan_id).values(status="cancelled"))
            conn.execute(update(self.tasks).where(self.tasks.c.plan_id == plan_id).values(state=TaskState.cancelled))
            conn.execute(insert(self.events).values(
                event_id=_stable_id("evt", plan_id, "cancelled"),
                plan_id=plan_id, kind="plan_cancelled", payload={}
            ))

    def get_plan(self, plan_id: str) -> Optional[PlanRecord]:
        with self.engine.begin() as conn:
            r = conn.execute(select(self.plans).where(self.plans.c.plan_id == plan_id)).first()
            return self._row_to_plan(r) if r else None

    def list_plan_tasks(self, plan_id: str) -> List[TaskRecord]:
        with self.engine.begin() as conn:
            rows = conn.execute(select(self.tasks).where(self.tasks.c.plan_id == plan_id).order_by(self.tasks.c.created_at)).all()
            return [self._row_to_task(r) for r in rows]

    def add_task(self, plan_id: str, agent: str, description: str, task_id: Optional[str] = None) -> TaskRecord:
        tid = task_id or _stable_id(plan_id, agent, description, datetime.utcnow().isoformat())
        with self.engine.begin() as conn:
            conn.execute(insert(self.tasks).values(
                task_id=tid, plan_id=plan_id, agent=agent, description=description,
                state=TaskState.pending, attempts=0
            ))
            conn.execute(insert(self.events).values(
                event_id=_stable_id("evt", plan_id, tid, "task_created"),
                plan_id=plan_id, task_id=tid, kind="task_created", payload={"agent": agent}
            ))
            r = conn.execute(select(self.tasks).where(self.tasks.c.task_id == tid)).first()
        return self._row_to_task(r)

    def set_task_state(self, task_id: str, state: TaskState, *, error: Optional[str] = None) -> None:
        with self.engine.begin() as conn:
            conn.execute(update(self.tasks).where(self.tasks.c.task_id == task_id).values(
                state=state, last_error=error
            ))
            # log event
            trow = conn.execute(select(self.tasks.c.plan_id).where(self.tasks.c.task_id == task_id)).first()
            pid = trow.plan_id if trow else "unknown"
            conn.execute(insert(self.events).values(
                event_id=_stable_id("evt", pid, task_id, f"state_{state}"),
                plan_id=pid, task_id=task_id, kind="task_state_changed",
                payload={"state": state, "error": error}
            ))

    def record_agent_response(self, task_id: str, agent: str, content: str, *, confidence: Optional[float] = None, citations: Optional[List[str]] = None) -> AgentResponseRecord:
        rid = _stable_id("resp", task_id, agent, content[:64], datetime.utcnow().isoformat())
        with self.engine.begin() as conn:
            conn.execute(insert(self.responses).values(
                response_id=rid, task_id=task_id, agent=agent,
                confidence=confidence, content=content, citations=citations
            ))
            # Guard: don't override terminal states failed/cancelled
            trow = conn.execute(select(self.tasks.c.state, self.tasks.c.plan_id).where(self.tasks.c.task_id == task_id)).first()
            if trow:
                current = trow.state
                if current not in (TaskState.failed, TaskState.cancelled):
                    conn.execute(update(self.tasks).where(self.tasks.c.task_id == task_id).values(state=TaskState.completed))
                    conn.execute(insert(self.events).values(
                        event_id=_stable_id("evt", trow.plan_id, task_id, "completed_on_response"),
                        plan_id=trow.plan_id, task_id=task_id, kind="task_completed_on_response", payload={}
                    ))
            row = conn.execute(select(self.responses).where(self.responses.c.response_id == rid)).first()
        return self._row_to_resp(row)

    def get_task(self, task_id: str) -> Optional[TaskRecord]:
        with self.engine.begin() as conn:
            r = conn.execute(select(self.tasks).where(self.tasks.c.task_id == task_id)).first()
            return self._row_to_task(r) if r else None

    def log_event(self, plan_id: str, kind: str, payload: Dict[str, Any], task_id: Optional[str] = None) -> EventRecord:
        eid = _stable_id("evt", plan_id, task_id or "", kind, str(payload)[:64], datetime.utcnow().isoformat())
        with self.engine.begin() as conn:
            conn.execute(insert(self.events).values(
                event_id=eid, plan_id=plan_id, task_id=task_id, kind=kind, payload=payload
            ))
            r = conn.execute(select(self.events).where(self.events.c.event_id == eid)).first()
        return self._row_to_event(r)

    def list_events(self, plan_id: str, task_id: Optional[str] = None, limit: int = 200) -> List[EventRecord]:
        with self.engine.begin() as conn:
            q = select(self.events).where(self.events.c.plan_id == plan_id)
            if task_id:
                q = q.where(self.events.c.task_id == task_id)
            rows = conn.execute(q.order_by(self.events.c.created_at.desc()).limit(limit)).all()
            return [self._row_to_event(r) for r in rows]

    def mark_retry(self, task_id: str) -> None:
        with self.engine.begin() as conn:
            # increment attempts, reset state and error
            conn.execute(update(self.tasks).where(self.tasks.c.task_id == task_id).values(
                attempts=self.tasks.c.attempts + 1, state=TaskState.pending, last_error=None
            ))
            trow = conn.execute(select(self.tasks.c.plan_id).where(self.tasks.c.task_id == task_id)).first()
            pid = trow.plan_id if trow else "unknown"
            conn.execute(insert(self.events).values(
                event_id=_stable_id("evt", pid, task_id, "retry"),
                plan_id=pid, task_id=task_id, kind="task_retry", payload={}
            ))

    def cancel_task(self, task_id: str) -> None:
        with self.engine.begin() as conn:
            conn.execute(update(self.tasks).where(self.tasks.c.task_id == task_id).values(state=TaskState.cancelled))
            trow = conn.execute(select(self.tasks.c.plan_id).where(self.tasks.c.task_id == task_id)).first()
            pid = trow.plan_id if trow else "unknown"
            conn.execute(insert(self.events).values(
                event_id=_stable_id("evt", pid, task_id, "cancel"),
                plan_id=pid, task_id=task_id, kind="task_cancelled", payload={}
            ))

# ---- factory ----------------------------------------------------------------

def state_store() -> StateStore:
    backend = os.getenv("STATE_BACKEND", "sqlite").lower()
    if backend == "sqlite":
        return SQLiteStateStore()
    # future: elif backend == "redis": return RedisStateStore(...)
    return SQLiteStateStore()
