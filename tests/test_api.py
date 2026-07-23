from fastapi.testclient import TestClient

from src.main import app


def test_health_and_readiness() -> None:
    client = TestClient(app)
    assert client.get("/health").json()["status"] == "healthy"
    assert client.get("/readyz").json()["status"] == "ready"


def test_create_and_inspect_plan(monkeypatch) -> None:
    monkeypatch.setattr("src.main.run_plan", lambda plan_id: None)
    client = TestClient(app)
    response = client.post("/plan", json={"high_level_goal": "Launch a new service", "user_context": "Six-month timeline"})
    assert response.status_code == 202
    plan_id = response.json()["plan_id"]
    plan = client.get(f"/state/plans/{plan_id}").json()
    assert plan["plan"]["original_query"] == "Launch a new service"
    assert len(plan["tasks"]) == 4
    assert {task["agent"] for task in plan["tasks"]} == {"COO", "CFO", "CTO", "CMO"}


def test_unknown_plan_and_result_not_ready(monkeypatch) -> None:
    monkeypatch.setattr("src.main.run_plan", lambda plan_id: None)
    client = TestClient(app)
    assert client.get("/state/plans/unknown").status_code == 404
    plan_id = client.post("/plan", json={"high_level_goal": "Validate a market"}).json()["plan_id"]
    assert client.get(f"/plan/{plan_id}/result").status_code == 409


def test_cancel_and_retry_task(monkeypatch) -> None:
    monkeypatch.setattr("src.main.run_plan", lambda plan_id: None)
    client = TestClient(app)
    plan_id = client.post("/plan", json={"high_level_goal": "Prepare an acquisition"}).json()["plan_id"]
    task_id = client.get(f"/state/plans/{plan_id}").json()["tasks"][0]["task_id"]
    assert client.post(f"/state/tasks/{task_id}/cancel").status_code == 200
    assert client.post(f"/state/tasks/{task_id}/retry").status_code == 200
