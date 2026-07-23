from src.models.dataModel import AgentResponse, AgentType, FinalPlan, TaskStatus


def test_agent_and_task_enums() -> None:
    assert {agent.value for agent in AgentType} == {"CEO", "COO", "CFO", "CTO", "CMO"}
    assert TaskStatus.COMPLETED.value == "completed"


def test_response_and_plan_serialization() -> None:
    response = AgentResponse(agent_id="CFO", task_id="task_1", response_data={"analysis": "Cost is acceptable"}, confidence=1.5)
    plan = FinalPlan(plan_id="plan_1", synthesized_strategy="Proceed", confidence_score=-1)
    assert response.confidence == 1.0
    assert plan.confidence_score == 0.0
    assert "plan_1" in plan.model_dump_json()
