import pytest

from src.models.dataModel import AgentResponse, FinalPlan
from src.state.store import StateStore, StateTransitionError


@pytest.fixture
def store(tmp_path):
    instance = StateStore(tmp_path / "state.db")
    yield instance
    instance.close()


def create_task(store: StateStore) -> str:
    store.create_plan("plan_1", "Test the workflow")
    store.create_task("task_1", "plan_1", "CFO", "Assess the financial case")
    return "task_1"


def test_state_transitions_are_enforced(store: StateStore) -> None:
    task_id = create_task(store)
    with pytest.raises(StateTransitionError):
        store.transition_task(task_id, "completed")
    store.transition_task(task_id, "in_progress")
    task = store.transition_task(task_id, "completed")
    assert task["state"] == "completed"


def test_retry_and_events(store: StateStore) -> None:
    task_id = create_task(store)
    store.transition_task(task_id, "cancelled")
    retried = store.retry_task(task_id)
    assert retried["state"] == "pending"
    assert retried["attempts"] == 1
    assert {event["kind"] for event in store.get_events_for_plan("plan_1")} >= {"plan_created", "task_created", "task_retry"}


def test_responses_and_final_plan_are_persisted(store: StateStore) -> None:
    task_id = create_task(store)
    store.transition_task(task_id, "in_progress")
    store.save_agent_response(AgentResponse(agent_id="CFO", task_id=task_id, response_data={"analysis": "Sound economics"}))
    store.transition_task(task_id, "completed")
    store.save_final_plan("plan_1", FinalPlan(plan_id="plan_1", synthesized_strategy="Proceed", contributing_agents=["CFO"]))
    assert store.get_agent_responses_for_plan("plan_1")[0].agent_id == "CFO"
    assert store.get_final_plan("plan_1").synthesized_strategy == "Proceed"
