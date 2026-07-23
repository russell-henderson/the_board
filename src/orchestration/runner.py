"""Execution service for a plan's specialist tasks."""
import logging
from typing import Any, Dict

from ..agents.specialists import agent_registry
from ..models.dataModel import TaskStatus
from ..state.store import StateStore, state_store
from .synthesizer import synthesize_plan

logger = logging.getLogger("the_board.orchestration")


def run_plan(plan_id: str, store: StateStore = state_store) -> Dict[str, Any]:
    plan = store.get_plan(plan_id)
    if not plan:
        raise KeyError("plan_not_found")
    store.update_plan_status(plan_id, "in_progress")
    processed = succeeded = failed = 0
    for task in store.get_pending_tasks(plan_id):
        processed += 1
        task_id, agent_name = task["task_id"], task["agent"]
        try:
            store.transition_task(task_id, TaskStatus.IN_PROGRESS.value)
            agent = agent_registry.get(agent_name)
            if not agent:
                raise ValueError(f"unknown_agent:{agent_name}")
            response = agent.execute(task["description"])
            response.task_id = task_id
            store.save_agent_response(response)
            store.transition_task(task_id, TaskStatus.COMPLETED.value)
            store.record_event(plan_id, task_id, "task_completed", {"agent": agent_name, "confidence": response.confidence})
            succeeded += 1
        except Exception as exc:
            # A user may cancel or retry after this worker selected the task.
            # That is not an execution failure and must not overwrite their choice.
            current = store.get_task_by_id(task_id)
            if not current or current["state"] not in {TaskStatus.IN_PROGRESS.value, TaskStatus.PENDING.value}:
                continue
            logger.exception("Task %s failed", task_id)
            if current["state"] == TaskStatus.PENDING.value:
                store.transition_task(task_id, TaskStatus.IN_PROGRESS.value)
            store.transition_task(task_id, TaskStatus.FAILED.value, str(exc))
            store.record_event(plan_id, task_id, "task_failed", {"agent": agent_name, "error": str(exc)})
            failed += 1

    if failed:
        status = "partially_completed" if succeeded else "failed"
        store.update_plan_status(plan_id, status, close_plan=not succeeded)
        return {"plan_id": plan_id, "status": status, "tasks_processed": processed, "tasks_succeeded": succeeded, "tasks_failed": failed}

    final_plan = synthesize_plan(plan_id, store)
    store.save_final_plan(plan_id, final_plan)
    store.close_plan(plan_id)
    return {"plan_id": plan_id, "status": "closed", "tasks_processed": processed, "tasks_succeeded": succeeded, "tasks_failed": 0}


def get_plan_execution_status(plan_id: str) -> Dict[str, Any]:
    return state_store.get_plan_task_summary(plan_id)
