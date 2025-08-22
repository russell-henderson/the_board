#!/usr/bin/env python3
"""
Tests for the StateStore component.

This module tests all StateStore functionality including:
- Database initialization
- Plan management
- Task management
- Event recording
- Final plan storage
"""

import pytest
import tempfile
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.state.store import StateStore
from src.models.dataModel import FinalPlan

class TestStateStore:
    """Test suite for StateStore functionality."""
    
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
    
    @pytest.fixture
    def state_store(self, temp_db_path):
        """Create a StateStore instance with temporary database."""
        store = StateStore(db_path=temp_db_path)
        store.init_db()
        return store
    
    def test_init_db(self, state_store):
        """Test database initialization."""
        # Check that tables were created
        cursor = state_store._conn.cursor()
        
        # Check plans table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='plans'")
        assert cursor.fetchone() is not None
        
        # Check tasks table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
        assert cursor.fetchone() is not None
        
        # Check events table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
        assert cursor.fetchone() is not None
        
        # Check final_plans table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='final_plans'")
        assert cursor.fetchone() is not None
    
    def test_create_plan(self, state_store):
        """Test plan creation."""
        plan_id = "test_plan_001"
        original_query = "Test strategic goal"
        
        # Create plan
        state_store.create_plan(plan_id, original_query)
        
        # Retrieve and verify
        plan = state_store.get_plan_by_id(plan_id)
        assert plan is not None
        assert plan['plan_id'] == plan_id
        assert plan['original_query'] == original_query
        assert plan['status'] == 'open'
    
    def test_create_task(self, state_store):
        """Test task creation."""
        plan_id = "test_plan_002"
        task_id = "test_task_001"
        agent = "CFO"
        description = "Test task description"
        
        # Create plan first
        state_store.create_plan(plan_id, "Test goal")
        
        # Create task
        state_store.create_task(task_id, plan_id, agent, description)
        
        # Retrieve and verify
        task = state_store.get_task_by_id(task_id)
        assert task is not None
        assert task['task_id'] == task_id
        assert task['plan_id'] == plan_id
        assert task['agent'] == agent
        assert task['description'] == description
        assert task['state'] == 'pending'
    
    def test_update_task_status(self, state_store):
        """Test task status updates."""
        plan_id = "test_plan_003"
        task_id = "test_task_002"
        
        # Create plan and task
        state_store.create_plan(plan_id, "Test goal")
        state_store.create_task(task_id, plan_id, "CFO", "Test task")
        
        # Update status
        state_store.update_task_status(task_id, "in_progress")
        
        # Verify update
        task = state_store.get_task_by_id(task_id)
        assert task['state'] == 'in_progress'
    
    def test_record_event(self, state_store):
        """Test event recording."""
        plan_id = "test_plan_004"
        task_id = "test_task_003"
        event_kind = "task_started"
        payload = {"status": "started"}
        
        # Create plan and task
        state_store.create_plan(plan_id, "Test goal")
        state_store.create_task(task_id, plan_id, "CFO", "Test task")
        
        # Record event
        state_store.record_event(plan_id, task_id, event_kind, payload)
        
        # Verify event was recorded
        events = state_store.get_events_for_plan(plan_id)
        assert len(events) > 0
        
        # Find our event
        event = next((e for e in events if e['kind'] == event_kind), None)
        assert event is not None
        assert event['plan_id'] == plan_id
        assert event['task_id'] == task_id
    
    def test_get_pending_tasks(self, state_store):
        """Test retrieval of pending tasks."""
        plan_id = "test_plan_005"
        
        # Create plan with multiple tasks
        state_store.create_plan(plan_id, "Test goal")
        state_store.create_task("task1", plan_id, "CFO", "Task 1")
        state_store.create_task("task2", plan_id, "CTO", "Task 2")
        
        # Get pending tasks
        pending_tasks = state_store.get_pending_tasks(plan_id)
        assert len(pending_tasks) == 2
        
        # Mark one as completed
        state_store.update_task_status("task1", "completed")
        
        # Should now have only one pending task
        pending_tasks = state_store.get_pending_tasks(plan_id)
        assert len(pending_tasks) == 1
        assert pending_tasks[0]['task_id'] == "task2"
    
    def test_get_plan(self, state_store):
        """Test get_plan method returns dictionary format."""
        plan_id = "test_plan_006"
        original_query = "Test strategic goal"
        
        # Create plan
        state_store.create_plan(plan_id, original_query)
        
        # Get plan as dictionary
        plan_dict = state_store.get_plan(plan_id)
        assert isinstance(plan_dict, dict)
        assert plan_dict['plan_id'] == plan_id
        assert plan_dict['original_query'] == original_query
    
    def test_get_agent_responses_for_plan(self, state_store):
        """Test retrieval of agent responses for a plan."""
        plan_id = "test_plan_007"
        
        # Create plan and tasks
        state_store.create_plan(plan_id, "Test goal")
        state_store.create_task("task1", plan_id, "CFO", "CFO task")
        state_store.create_task("task2", plan_id, "CTO", "CTO task")
        
        # Mark tasks as completed and record completion events
        state_store.update_task_status("task1", "completed")
        state_store.update_task_status("task2", "completed")
        
        # Record completion events
        state_store.record_event(plan_id, "task1", "task_completed", "CFO analysis complete")
        state_store.record_event(plan_id, "task2", "task_completed", "CTO analysis complete")
        
        # Get agent responses
        responses = state_store.get_agent_responses_for_plan(plan_id)
        assert len(responses) == 2
        
        # Verify response structure
        for response in responses:
            assert 'agent' in response
            assert 'content' in response
            assert 'created_at' in response
    
    def test_save_final_plan(self, state_store):
        """Test saving final synthesized plan."""
        plan_id = "test_plan_008"
        
        # Create plan
        state_store.create_plan(plan_id, "Test goal")
        
        # Create final plan
        final_plan = FinalPlan(
            plan_id=plan_id,
            synthesized_strategy="Test strategy",
            contributing_agents=["CFO", "CTO"],
            identified_risks=["Test risk"],
            confidence_score=0.85
        )
        
        # Save final plan
        state_store.save_final_plan(plan_id, final_plan)
        
        # Verify it was saved
        cursor = state_store._conn.cursor()
        cursor.execute("SELECT * FROM final_plans WHERE plan_id = ?", (plan_id,))
        saved_plan = cursor.fetchone()
        assert saved_plan is not None
        assert saved_plan['plan_id'] == plan_id
    
    def test_update_plan_status(self, state_store):
        """Test plan status updates."""
        plan_id = "test_plan_009"
        
        # Create plan
        state_store.create_plan(plan_id, "Test goal")
        
        # Update status
        state_store.update_plan_status(plan_id, "closed")
        
        # Verify update
        plan = state_store.get_plan_by_id(plan_id)
        assert plan['status'] == 'closed'
    
    def test_get_plan_task_summary(self, state_store):
        """Test plan task summary retrieval."""
        plan_id = "test_plan_010"
        
        # Create plan with tasks
        state_store.create_plan(plan_id, "Test goal")
        state_store.create_task("task1", plan_id, "CFO", "Task 1")
        state_store.create_task("task2", plan_id, "CTO", "Task 2")
        
        # Get summary
        summary = state_store.get_plan_task_summary(plan_id)
        
        # Verify summary structure
        assert 'plan_id' in summary
        assert 'total_tasks' in summary
        assert 'completed_tasks' in summary
        assert 'pending_tasks' in summary
        assert 'failed_tasks' in summary
        assert summary['plan_id'] == plan_id
        assert summary['total_tasks'] == 2
        assert summary['pending_tasks'] == 2
    
    def test_increment_task_attempts(self, state_store):
        """Test task attempt incrementing."""
        plan_id = "test_plan_011"
        task_id = "test_task_004"
        
        # Create plan and task
        state_store.create_plan(plan_id, "Test goal")
        state_store.create_task(task_id, plan_id, "CFO", "Test task")
        
        # Increment attempts
        state_store.increment_task_attempts(task_id)
        
        # Verify increment
        task = state_store.get_task_by_id(task_id)
        assert task['attempts'] == 1
    
    def test_connection_management(self, state_store):
        """Test database connection management."""
        # Verify connection is working
        cursor = state_store._conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1
        
        # Test connection cleanup
        state_store.close()
        
        # Connection should be closed
        with pytest.raises(Exception):
            state_store._conn.execute("SELECT 1")

if __name__ == "__main__":
    pytest.main([__file__])
