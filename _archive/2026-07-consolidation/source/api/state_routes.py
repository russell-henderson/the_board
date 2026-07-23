# src/api/state_routes.py
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from src.state.store import state_store, TaskState

router = APIRouter(prefix="/state", tags=["state"])
store = state_store()

@router.get("/plans/{plan_id}")
def get_plan(plan_id: str):
    p = store.get_plan(plan_id)
    if not p:
        raise HTTPException(404, "plan not found")
    return {"plan": p.dict(), "tasks": [t.dict() for t in store.list_plan_tasks(plan_id)]}

@router.post("/tasks/{task_id}/retry")
def retry_task(task_id: str):
    t = store.get_task(task_id)
    if not t:
        raise HTTPException(404, "task not found")
    if t.state not in {TaskState.failed, TaskState.escalated, TaskState.cancelled}:
        raise HTTPException(400, "only failed/escalated/cancelled tasks can be retried")
    store.mark_retry(task_id)
    return {"ok": True}

@router.post("/tasks/{task_id}/cancel")
def cancel_task(task_id: str):
    t = store.get_task(task_id)
    if not t:
        raise HTTPException(404, "task not found")
    if t.state in {TaskState.completed, TaskState.cancelled}:
        raise HTTPException(400, "task already finished")
    store.cancel_task(task_id)
    return {"ok": True}

@router.get("/plans/{plan_id}/events")
def plan_events(plan_id: str, task_id: Optional[str] = None, limit: int = Query(200, ge=1, le=1000)):
    return {"events": [e.dict() for e in store.list_events(plan_id, task_id, limit)]}
