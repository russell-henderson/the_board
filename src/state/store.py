"""SQLite-backed source of truth for plans, tasks, events, and results."""
from __future__ import annotations

import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models.dataModel import AgentResponse, FinalPlan, TaskStatus

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DB_PATH = os.environ.get("STATE_DB_PATH", "state/the_board_state.db")
STATE_DB = REPO_ROOT / STATE_DB_PATH

_ALLOWED_TRANSITIONS = {
    TaskStatus.PENDING.value: {TaskStatus.IN_PROGRESS.value, TaskStatus.CANCELLED.value},
    TaskStatus.IN_PROGRESS.value: {TaskStatus.COMPLETED.value, TaskStatus.FAILED.value, TaskStatus.ESCALATED.value, TaskStatus.CANCELLED.value},
    TaskStatus.FAILED.value: {TaskStatus.PENDING.value},
    TaskStatus.ESCALATED.value: {TaskStatus.PENDING.value},
    TaskStatus.CANCELLED.value: {TaskStatus.PENDING.value},
    TaskStatus.COMPLETED.value: set(),
}


class StateTransitionError(ValueError):
    pass


class StateStore:
    def __init__(self, db_path: str | Path = STATE_DB):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = self._connect()
        self.init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def init_db(self) -> None:
        with self._lock, self._conn:
            self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS plans (
              plan_id TEXT PRIMARY KEY, status TEXT NOT NULL, original_query TEXT NOT NULL,
              user_context TEXT, created_at TEXT NOT NULL, closed_at TEXT
            );
            CREATE TABLE IF NOT EXISTS tasks (
              task_id TEXT PRIMARY KEY, plan_id TEXT NOT NULL REFERENCES plans(plan_id),
              agent TEXT NOT NULL, description TEXT NOT NULL, state TEXT NOT NULL,
              attempts INTEGER NOT NULL DEFAULT 0, last_error TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS events (
              event_id TEXT PRIMARY KEY, plan_id TEXT REFERENCES plans(plan_id), task_id TEXT REFERENCES tasks(task_id),
              kind TEXT NOT NULL, payload TEXT, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS agent_responses (
              task_id TEXT PRIMARY KEY REFERENCES tasks(task_id), agent_id TEXT NOT NULL,
              response_json TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS final_plans (
              plan_id TEXT PRIMARY KEY REFERENCES plans(plan_id), content TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_tasks_plan_state ON tasks(plan_id, state);
            CREATE INDEX IF NOT EXISTS idx_events_plan_created ON events(plan_id, created_at DESC);
            """)
            # Compatible upgrade for databases created before user_context existed.
            columns = {row["name"] for row in self._conn.execute("PRAGMA table_info(plans)")}
            if "user_context" not in columns:
                self._conn.execute("ALTER TABLE plans ADD COLUMN user_context TEXT")

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    @staticmethod
    def _id(prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:12]}"

    @staticmethod
    def _payload(value: Any) -> Optional[str]:
        return None if value is None else json.dumps(value, default=str)

    def create_plan(self, plan_id: str, original_query: str, user_context: Optional[str] = None) -> Dict[str, Any]:
        now = self._utc_now()
        with self._lock, self._conn:
            self._conn.execute("INSERT INTO plans(plan_id,status,original_query,user_context,created_at) VALUES (?,?,?,?,?)", (plan_id, "open", original_query, user_context, now))
            self._record_event_locked(plan_id, None, "plan_created", {"goal": original_query})
        return self.get_plan(plan_id) or {}

    def create_task(self, task_id: str, plan_id: str, agent: str, description: str) -> Dict[str, Any]:
        now = self._utc_now()
        with self._lock, self._conn:
            self._conn.execute("INSERT INTO tasks(task_id,plan_id,agent,description,state,attempts,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)", (task_id, plan_id, agent, description, TaskStatus.PENDING.value, 0, now, now))
            self._record_event_locked(plan_id, task_id, "task_created", {"agent": agent, "description": description})
        return dict(self.get_task_by_id(task_id) or {})

    def transition_task(self, task_id: str, new_state: str, error_message: Optional[str] = None) -> Dict[str, Any]:
        with self._lock, self._conn:
            task = self.get_task_by_id(task_id)
            if not task:
                raise KeyError("task_not_found")
            old_state = task["state"]
            if new_state not in _ALLOWED_TRANSITIONS.get(old_state, set()):
                raise StateTransitionError(f"cannot transition {old_state} to {new_state}")
            self._conn.execute("UPDATE tasks SET state=?, last_error=?, updated_at=? WHERE task_id=?", (new_state, error_message, self._utc_now(), task_id))
            self._record_event_locked(task["plan_id"], task_id, "task_state_changed", {"from": old_state, "to": new_state, "error": error_message})
        return dict(self.get_task_by_id(task_id) or {})

    def retry_task(self, task_id: str) -> Dict[str, Any]:
        with self._lock, self._conn:
            task = self.get_task_by_id(task_id)
            if not task:
                raise KeyError("task_not_found")
            if task["state"] not in {TaskStatus.FAILED.value, TaskStatus.ESCALATED.value, TaskStatus.CANCELLED.value}:
                raise StateTransitionError("retry_not_allowed_from_state")
            attempts = int(task["attempts"]) + 1
            self._conn.execute("UPDATE tasks SET state=?,attempts=?,last_error=NULL,updated_at=? WHERE task_id=?", (TaskStatus.PENDING.value, attempts, self._utc_now(), task_id))
            self._record_event_locked(task["plan_id"], task_id, "task_retry", {"attempts": attempts})
        return dict(self.get_task_by_id(task_id) or {})

    def save_agent_response(self, response: AgentResponse) -> None:
        with self._lock, self._conn:
            task = self.get_task_by_id(response.task_id)
            if not task:
                raise KeyError("task_not_found")
            self._conn.execute("INSERT OR REPLACE INTO agent_responses(task_id,agent_id,response_json,created_at) VALUES (?,?,?,?)", (response.task_id, response.agent_id, response.model_dump_json(), self._utc_now()))
            self._record_event_locked(task["plan_id"], response.task_id, "agent_response_recorded", response.model_dump())

    def save_final_plan(self, plan_id: str, final_plan: FinalPlan) -> None:
        with self._lock, self._conn:
            self._conn.execute("INSERT OR REPLACE INTO final_plans(plan_id,content,created_at) VALUES (?,?,?)", (plan_id, final_plan.model_dump_json(), self._utc_now()))
            self._record_event_locked(plan_id, None, "plan_synthesized", {"confidence_score": final_plan.confidence_score})

    def close_plan(self, plan_id: str, status: str = "closed") -> None:
        with self._lock, self._conn:
            self._conn.execute("UPDATE plans SET status=?, closed_at=? WHERE plan_id=?", (status, self._utc_now(), plan_id))

    def update_plan_status(self, plan_id: str, new_status: str, close_plan: bool = False) -> None:
        if close_plan or new_status in {"closed", "failed", "synthesis_failed"}:
            self.close_plan(plan_id, new_status)
        else:
            with self._lock, self._conn:
                self._conn.execute("UPDATE plans SET status=? WHERE plan_id=?", (new_status, plan_id))

    def get_plan_by_id(self, plan_id: str) -> Optional[sqlite3.Row]:
        with self._lock:
            return self._conn.execute("SELECT * FROM plans WHERE plan_id=?", (plan_id,)).fetchone()

    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        row = self.get_plan_by_id(plan_id)
        return dict(row) if row else None

    def get_task_by_id(self, task_id: str) -> Optional[sqlite3.Row]:
        with self._lock:
            return self._conn.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()

    def get_pending_tasks(self, plan_id: str) -> List[sqlite3.Row]:
        with self._lock:
            return self._conn.execute("SELECT * FROM tasks WHERE plan_id=? AND state='pending' ORDER BY created_at", (plan_id,)).fetchall()

    def get_all_tasks_for_plan(self, plan_id: str) -> List[sqlite3.Row]:
        with self._lock:
            return self._conn.execute("SELECT * FROM tasks WHERE plan_id=? ORDER BY created_at", (plan_id,)).fetchall()

    def record_event(self, plan_id: Optional[str], task_id: Optional[str], kind: str, payload: Any = None) -> None:
        with self._lock, self._conn:
            self._record_event_locked(plan_id, task_id, kind, payload)

    def _record_event_locked(self, plan_id: Optional[str], task_id: Optional[str], kind: str, payload: Any) -> None:
        self._conn.execute("INSERT INTO events(event_id,plan_id,task_id,kind,payload,created_at) VALUES (?,?,?,?,?,?)", (self._id("evt"), plan_id, task_id, kind, self._payload(payload), self._utc_now()))

    def get_events_for_plan(self, plan_id: str, task_id: Optional[str] = None, limit: int = 200) -> List[Dict[str, Any]]:
        query, values = "SELECT * FROM events WHERE plan_id=?", [plan_id]
        if task_id:
            query += " AND task_id=?"; values.append(task_id)
        query += " ORDER BY created_at DESC LIMIT ?"; values.append(limit)
        with self._lock:
            rows = self._conn.execute(query, values).fetchall()
        return [{**dict(row), "payload": json.loads(row["payload"]) if row["payload"] else None} for row in rows]

    def get_agent_responses_for_plan(self, plan_id: str) -> List[AgentResponse]:
        with self._lock:
            rows = self._conn.execute("SELECT response_json FROM agent_responses r JOIN tasks t ON t.task_id=r.task_id WHERE t.plan_id=? ORDER BY r.created_at", (plan_id,)).fetchall()
        return [AgentResponse.model_validate_json(row["response_json"]) for row in rows]

    def get_final_plan(self, plan_id: str) -> Optional[FinalPlan]:
        with self._lock:
            row = self._conn.execute("SELECT content FROM final_plans WHERE plan_id=?", (plan_id,)).fetchone()
        return FinalPlan.model_validate_json(row["content"]) if row else None

    def get_plan_task_summary(self, plan_id: str) -> Dict[str, Any]:
        plan = self.get_plan(plan_id)
        if not plan:
            return {"error": "Plan not found"}
        counts = {row["state"]: row["count"] for row in self._conn.execute("SELECT state,COUNT(*) count FROM tasks WHERE plan_id=? GROUP BY state", (plan_id,))}
        return {"plan_id": plan_id, "plan_status": plan["status"], "task_counts": counts, "total_tasks": sum(counts.values()), "completed_tasks": counts.get("completed", 0), "pending_tasks": counts.get("pending", 0), "failed_tasks": counts.get("failed", 0), "created_at": plan["created_at"], "closed_at": plan["closed_at"]}

    def close(self) -> None:
        self._conn.close()


state_store = StateStore()
