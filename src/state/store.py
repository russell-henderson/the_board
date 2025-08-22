# src/state/store.py
from __future__ import annotations
import sqlite3
import os
from pathlib import Path
from typing import List, Optional, Dict, Any

# Define path relative to this file's location
REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DB_PATH = os.environ.get("STATE_DB_PATH", "state/the_board_state.db")
STATE_DB = REPO_ROOT / STATE_DB_PATH

class StateStore:
    def __init__(self, db_path: str = STATE_DB):
        self.db_path = db_path
        os.makedirs(Path(db_path).parent, exist_ok=True)
        self._conn = self._connect()
        self.init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def init_db(self):
        # Your CREATE TABLE statements from main.py go here
        self._conn.execute(
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
        self._conn.execute(
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
        self._conn.execute(
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
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS final_plans (
                plan_id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    # Core task management methods
    def get_pending_tasks(self, plan_id: str) -> List[sqlite3.Row]:
        """Get all pending tasks for a specific plan."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE plan_id = ? AND state = 'pending'", (plan_id,))
        return cursor.fetchall()

    def get_all_tasks_for_plan(self, plan_id: str) -> List[sqlite3.Row]:
        """Get all tasks for a specific plan regardless of status."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE plan_id = ? ORDER BY created_at", (plan_id,))
        return cursor.fetchall()

    def get_task_by_id(self, task_id: str) -> Optional[sqlite3.Row]:
        """Get a specific task by its ID."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
        return cursor.fetchone()

    def update_task_status(self, task_id: str, new_status: str, error_message: Optional[str] = None):
        """Update task status and optionally set error message."""
        cursor = self._conn.cursor()
        if error_message:
            cursor.execute(
                "UPDATE tasks SET state = ?, last_error = ?, updated_at = ? WHERE task_id = ?",
                (new_status, error_message, self._utc_now(), task_id)
            )
        else:
            cursor.execute(
                "UPDATE tasks SET state = ?, updated_at = ? WHERE task_id = ?",
                (new_status, self._utc_now(), task_id)
            )
        self._conn.commit()

    def increment_task_attempts(self, task_id: str):
        """Increment the attempt counter for a task."""
        cursor = self._conn.cursor()
        cursor.execute(
            "UPDATE tasks SET attempts = attempts + 1, updated_at = ? WHERE task_id = ?",
            (self._utc_now(), task_id)
        )
        self._conn.commit()

    # Plan management methods
    def get_plan_by_id(self, plan_id: str) -> Optional[sqlite3.Row]:
        """Get a specific plan by its ID."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM plans WHERE plan_id = ?", (plan_id,))
        return cursor.fetchone()
    
    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get a plan and convert to dictionary format."""
        plan = self.get_plan_by_id(plan_id)
        if plan:
            return dict(plan)
        return None

    def update_plan_status(self, plan_id: str, new_status: str, close_plan: bool = False):
        """Update plan status and optionally close it."""
        cursor = self._conn.cursor()
        if close_plan:
            cursor.execute(
                "UPDATE plans SET status = ?, closed_at = ? WHERE plan_id = ?",
                (new_status, self._utc_now(), plan_id)
            )
        else:
            cursor.execute(
                "UPDATE plans SET status = ? WHERE plan_id = ?",
                (new_status, plan_id)
            )
        self._conn.commit()

    def get_plan_task_summary(self, plan_id: str) -> Dict[str, Any]:
        """Get a summary of task counts by status for a plan."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            SELECT state, COUNT(*) as count 
            FROM tasks 
            WHERE plan_id = ? 
            GROUP BY state
            """,
            (plan_id,)
        )
        task_counts = {row['state']: row['count'] for row in cursor.fetchall()}
        
        # Get plan info
        plan = self.get_plan_by_id(plan_id)
        if not plan:
            return {"error": "Plan not found"}
        
        return {
            "plan_id": plan_id,
            "plan_status": plan['status'],
            "task_counts": task_counts,
            "total_tasks": sum(task_counts.values()),
            "created_at": plan['created_at'],
            "closed_at": plan.get('closed_at')
        }

    # Event management methods
    def record_event(self, plan_id: Optional[str], task_id: Optional[str], 
                    kind: str, payload: Optional[str] = None):
        """Record an event in the events table."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT INTO events(event_id, plan_id, task_id, kind, payload, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                f"evt_{self._generate_id()}",
                plan_id,
                task_id,
                kind,
                payload,
                self._utc_now()
            )
        )
        self._conn.commit()

    def get_events_for_plan(self, plan_id: str, task_id: Optional[str] = None, 
                           limit: int = 200) -> List[sqlite3.Row]:
        """Get events for a plan, optionally filtered by task."""
        cursor = self._conn.cursor()
        if task_id:
            cursor.execute(
                "SELECT * FROM events WHERE plan_id = ? AND task_id = ? ORDER BY created_at DESC LIMIT ?",
                (plan_id, task_id, limit)
            )
        else:
            cursor.execute(
                "SELECT * FROM events WHERE plan_id = ? ORDER BY created_at DESC LIMIT ?",
                (plan_id, limit)
            )
        return cursor.fetchall()
    
    def get_agent_responses_for_plan(self, plan_id: str) -> List[Dict[str, Any]]:
        """Get all completed agent responses for a plan."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            SELECT t.agent, e.payload as content, e.created_at
            FROM events e
            JOIN tasks t ON e.task_id = t.task_id
            WHERE e.plan_id = ? AND e.kind = 'task_completed' AND t.state = 'completed'
            ORDER BY e.created_at
            """,
            (plan_id,)
        )
        responses = []
        for row in cursor.fetchall():
            responses.append({
                'agent': row['agent'],
                'content': row['content'],
                'created_at': row['created_at']
            })
        return responses
    
    def save_final_plan(self, plan_id: str, final_plan: 'FinalPlan'):
        """Save the final synthesized plan."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO final_plans (plan_id, content, created_at)
            VALUES (?, ?, ?)
            """,
            (plan_id, final_plan.model_dump_json(), self._utc_now())
        )
        self._conn.commit()

    # Utility methods
    def _utc_now(self) -> str:
        """Get current UTC time as ISO string."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    def _generate_id(self) -> str:
        """Generate a short unique ID."""
        import uuid
        return uuid.uuid4().hex[:12]

    def close(self):
        """Close the database connection."""
        if hasattr(self, '_conn') and self._conn:
            self._conn.close()

# Create a singleton instance to be used across the app
state_store = StateStore()
