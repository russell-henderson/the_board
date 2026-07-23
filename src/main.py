"""FastAPI entry point for the_board."""
from __future__ import annotations

import threading
import uuid
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from .orchestration.runner import run_plan
from .state.store import StateTransitionError, state_store

app = FastAPI(title="the_board API", version="2.1.0", description="Local-first multi-agent strategic planning.")
ESSENTIAL_FOUR = ("COO", "CFO", "CTO", "CMO")


class GoalRequest(BaseModel):
    high_level_goal: str = Field(min_length=3, max_length=10000)
    user_context: Optional[str] = Field(default=None, max_length=20000)


class AcceptedPlan(BaseModel):
    plan_id: str
    status: str = "accepted"
    message: str = "Plan accepted and orchestration started."


def _task_description(agent: str, goal: str) -> str:
    templates = {"COO": "Translate the goal into an operating plan, timeline, and owners", "CFO": "Assess budget, assumptions, ROI, and financial risks", "CTO": "Assess technical feasibility, architecture, and delivery risks", "CMO": "Define positioning, audience, channels, and launch messaging"}
    return f"{templates[agent]}: {goal}"


@app.get("/")
def root() -> Dict[str, str]:
    return {"status": "ok", "message": "the_board is running"}


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "healthy", "service": "the_board"}


@app.get("/healthz")
def healthz() -> Dict[str, str]:
    return {"status": "ok", "service": "the_board"}


@app.get("/readyz")
def readyz() -> Dict[str, str]:
    try:
        state_store._conn.execute("SELECT 1")
    except Exception as exc:
        raise HTTPException(503, "state_store_unavailable") from exc
    return {"status": "ready"}


@app.post("/plan", response_model=AcceptedPlan, status_code=202)
def create_plan(request: GoalRequest) -> AcceptedPlan:
    plan_id = f"plan_{uuid.uuid4().hex[:12]}"
    state_store.create_plan(plan_id, request.high_level_goal, request.user_context)
    for agent in ESSENTIAL_FOUR:
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        state_store.create_task(task_id, plan_id, agent, _task_description(agent, request.high_level_goal))
    # A daemon thread keeps the accepted response non-blocking even in local clients.
    threading.Thread(target=run_plan, args=(plan_id,), daemon=True).start()
    return AcceptedPlan(plan_id=plan_id)


@app.get("/state/plans/{plan_id}")
def inspect_plan(plan_id: str) -> Dict[str, Any]:
    plan = state_store.get_plan(plan_id)
    if not plan:
        raise HTTPException(404, "plan_not_found")
    return {"plan": plan, "tasks": [dict(task) for task in state_store.get_all_tasks_for_plan(plan_id)], "summary": state_store.get_plan_task_summary(plan_id)}


@app.get("/state/plans/{plan_id}/events")
def list_events(plan_id: str, task_id: Optional[str] = None, limit: int = Query(200, ge=1, le=1000)) -> Dict[str, List[Dict[str, Any]]]:
    if not state_store.get_plan(plan_id):
        raise HTTPException(404, "plan_not_found")
    return {"events": state_store.get_events_for_plan(plan_id, task_id, limit)}


@app.post("/state/tasks/{task_id}/cancel")
def cancel_task(task_id: str) -> Dict[str, bool]:
    try:
        task = state_store.transition_task(task_id, "cancelled")
    except KeyError:
        raise HTTPException(404, "task_not_found")
    except StateTransitionError as exc:
        raise HTTPException(400, "task_already_terminal") from exc
    return {"ok": True}


@app.post("/state/tasks/{task_id}/retry")
def retry_task(task_id: str) -> Dict[str, bool]:
    try:
        task = state_store.retry_task(task_id)
    except KeyError:
        raise HTTPException(404, "task_not_found")
    except StateTransitionError as exc:
        raise HTTPException(400, str(exc)) from exc
    threading.Thread(target=run_plan, args=(task["plan_id"],), daemon=True).start()
    return {"ok": True}


@app.get("/plan/{plan_id}/result")
def get_plan_result(plan_id: str) -> Dict[str, Any]:
    plan = state_store.get_plan(plan_id)
    if not plan:
        raise HTTPException(404, "plan_not_found")
    result = state_store.get_final_plan(plan_id)
    if not result:
        raise HTTPException(409, f"plan_not_ready: current status is {plan['status']}")
    return {"plan_id": plan_id, "status": "completed", "plan_data": result.model_dump()}
