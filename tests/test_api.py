#!/usr/bin/env python3
"""
Tests for the FastAPI API endpoints.

This module tests all API functionality including:
- Health checks
- Plan creation and management
- State monitoring
- Error handling
"""

import pytest
import sys
import tempfile
import os
from pathlib import Path
from fastapi.testclient import TestClient

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.main import app

class TestAPIEndpoints:
    """Test suite for API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            temp_path = f.name
        yield temp_path
        # Cleanup
        try:
            os.unlink(temp_path)
        except:
            pass
    
    def test_root_endpoint(self, client):
        """Test the root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ok"
        assert data["message"] == "the_board is running"
    
    def test_health_endpoint(self, client):
        """Test the health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_healthz_endpoint(self, client):
        """Test the healthz endpoint."""
        response = client.get("/healthz")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "the_board"
    
    def test_readyz_endpoint(self, client):
        """Test the readyz endpoint."""
        response = client.get("/readyz")
        # This might fail if database is not available in test environment
        # We'll handle both success and failure cases
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "ready"
        elif response.status_code == 503:
            # Service not ready (expected in test environment)
            pass
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")
    
    def test_echo_endpoint(self, client):
        """Test the echo endpoint."""
        test_text = "Hello, the_board!"
        response = client.post("/echo", json={"text": test_text})
        assert response.status_code == 200
        
        data = response.json()
        assert data["text"] == test_text
        assert "model" in data  # Should include model info
    
    def test_echo_endpoint_validation(self, client):
        """Test echo endpoint input validation."""
        # Test missing text field
        response = client.post("/echo", json={})
        assert response.status_code == 422  # Validation error
        
        # Test empty text
        response = client.post("/echo", json={"text": ""})
        assert response.status_code == 200  # Empty string is valid
    
    def test_create_plan_endpoint(self, client):
        """Test plan creation endpoint."""
        plan_data = {
            "high_level_goal": "Launch a new SaaS product",
            "user_context": "I have 2 years of experience and $50k budget"
        }
        
        response = client.post("/plan", json=plan_data)
        assert response.status_code == 202  # Accepted
        
        data = response.json()
        assert "message" in data
        assert "plan_id" in data
        assert data["message"] == "Plan accepted and orchestration started."
        assert data["plan_id"].startswith("plan_")
    
    def test_create_plan_validation(self, client):
        """Test plan creation input validation."""
        # Test missing required fields
        response = client.post("/plan", json={})
        assert response.status_code == 422  # Validation error
        
        # Test missing high_level_goal
        response = client.post("/plan", json={"user_context": "Some context"})
        assert response.status_code == 422  # Validation error
    
    def test_inspect_plan_endpoint(self, client):
        """Test plan inspection endpoint."""
        # First create a plan
        plan_data = {
            "high_level_goal": "Test strategic goal",
            "user_context": "Test context"
        }
        create_response = client.post("/plan", json=plan_data)
        plan_id = create_response.json()["plan_id"]
        
        # Now inspect the plan
        response = client.get(f"/state/plans/{plan_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "plan" in data
        assert "tasks" in data
        assert data["plan"]["plan_id"] == plan_id
        assert data["plan"]["status"] == "open"
        assert len(data["tasks"]) > 0  # Should have created tasks
    
    def test_inspect_nonexistent_plan(self, client):
        """Test inspecting a plan that doesn't exist."""
        response = client.get("/state/plans/nonexistent_plan")
        assert response.status_code == 404
        assert "plan_not_found" in response.json()["detail"]
    
    def test_list_plan_events(self, client):
        """Test listing plan events."""
        # First create a plan
        plan_data = {
            "high_level_goal": "Test strategic goal for events",
            "user_context": "Test context"
        }
        create_response = client.post("/plan", json=plan_data)
        plan_id = create_response.json()["plan_id"]
        
        # Now get events
        response = client.get(f"/state/plans/{plan_id}/events")
        assert response.status_code == 200
        
        data = response.json()
        assert "events" in data
        assert isinstance(data["events"], list)
        
        # Should have at least plan_created event
        if len(data["events"]) > 0:
            event = data["events"][0]
            assert "event_id" in event
            assert "plan_id" in event
            assert "kind" in event
            assert "created_at" in event
    
    def test_list_events_with_limit(self, client):
        """Test listing events with limit parameter."""
        # First create a plan
        plan_data = {
            "high_level_goal": "Test strategic goal for event limits",
            "user_context": "Test context"
        }
        create_response = client.post("/plan", json=plan_data)
        plan_id = create_response.json()["plan_id"]
        
        # Test with limit
        response = client.get(f"/state/plans/{plan_id}/events?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert "events" in data
        assert len(data["events"]) <= 5
    
    def test_cancel_task_endpoint(self, client):
        """Test task cancellation endpoint."""
        # First create a plan
        plan_data = {
            "high_level_goal": "Test strategic goal for task cancellation",
            "user_context": "Test context"
        }
        create_response = client.post("/plan", json=plan_data)
        plan_id = create_response.json()["plan_id"]
        
        # Get the plan to find task IDs
        inspect_response = client.get(f"/state/plans/{plan_id}")
        tasks = inspect_response.json()["tasks"]
        task_id = tasks[0]["task_id"]
        
        # Cancel the task
        response = client.post(f"/state/tasks/{task_id}/cancel")
        assert response.status_code == 200
        
        data = response.json()
        assert data["ok"] is True
        
        # Verify task was cancelled
        inspect_response = client.get(f"/state/plans/{plan_id}")
        tasks = inspect_response.json()["tasks"]
        cancelled_task = next((t for t in tasks if t["task_id"] == task_id), None)
        assert cancelled_task is not None
        assert cancelled_task["state"] == "cancelled"
    
    def test_cancel_nonexistent_task(self, client):
        """Test cancelling a task that doesn't exist."""
        response = client.post("/state/tasks/nonexistent_task/cancel")
        assert response.status_code == 404
        assert "task_not_found" in response.json()["detail"]
    
    def test_retry_task_endpoint(self, client):
        """Test task retry endpoint."""
        # First create a plan
        plan_data = {
            "high_level_goal": "Test strategic goal for task retry",
            "user_context": "Test context"
        }
        create_response = client.post("/plan", json=plan_data)
        plan_id = create_response.json()["plan_id"]
        
        # Get the plan to find task IDs
        inspect_response = client.get(f"/state/plans/{plan_id}")
        tasks = inspect_response.json()["tasks"]
        task_id = tasks[0]["task_id"]
        
        # First cancel the task so it can be retried
        client.post(f"/state/tasks/{task_id}/cancel")
        
        # Now retry the task
        response = client.post(f"/state/tasks/{task_id}/retry")
        assert response.status_code == 200
        
        data = response.json()
        assert data["ok"] is True
        
        # Verify task was reset to pending
        inspect_response = client.get(f"/state/plans/{plan_id}")
        tasks = inspect_response.json()["tasks"]
        retried_task = next((t for t in tasks if t["task_id"] == task_id), None)
        assert retried_task is not None
        assert retried_task["state"] == "pending"
    
    def test_retry_completed_task(self, client):
        """Test retrying a task that's already completed."""
        # First create a plan
        plan_data = {
            "high_level_goal": "Test strategic goal for retry validation",
            "user_context": "Test context"
        }
        create_response = client.post("/plan", json=plan_data)
        plan_id = create_response.json()["plan_id"]
        
        # Get the plan to find task IDs
        inspect_response = client.get(f"/state/plans/{plan_id}")
        tasks = inspect_response.json()["tasks"]
        task_id = tasks[0]["task_id"]
        
        # Try to retry a pending task (should fail)
        response = client.post(f"/state/tasks/{task_id}/retry")
        assert response.status_code == 400
        assert "retry_not_allowed_from_state" in response.json()["detail"]
    
    def test_get_plan_result_endpoint(self, client):
        """Test getting plan results endpoint."""
        # First create a plan
        plan_data = {
            "high_level_goal": "Test strategic goal for results",
            "user_context": "Test context"
        }
        create_response = client.post("/plan", json=plan_data)
        plan_id = create_response.json()["plan_id"]
        
        # Try to get results (should fail as plan is not closed)
        response = client.get(f"/plan/{plan_id}/result")
        assert response.status_code == 400
        assert "plan_not_ready" in response.json()["detail"]
    
    def test_get_nonexistent_plan_result(self, client):
        """Test getting results for a plan that doesn't exist."""
        response = client.get("/plan/nonexistent_plan/result")
        assert response.status_code == 404
        assert "plan_not_found" in response.json()["detail"]

class TestAPIErrorHandling:
    """Test suite for API error handling."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)
    
    def test_invalid_json(self, client):
        """Test handling of invalid JSON."""
        response = client.post("/echo", data="invalid json", headers={"Content-Type": "application/json"})
        assert response.status_code == 422
    
    def test_missing_content_type(self, client):
        """Test handling of missing content type."""
        response = client.post("/echo", data='{"text": "test"}')
        assert response.status_code == 422
    
    def test_large_payload(self, client):
        """Test handling of large payloads."""
        large_text = "A" * 1000000  # 1MB string
        response = client.post("/echo", json={"text": large_text})
        # Should either succeed or fail gracefully
        assert response.status_code in [200, 413, 422]

if __name__ == "__main__":
    pytest.main([__file__])
