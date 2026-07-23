"""
Basic tests for the_board system functionality.

This module provides basic validation tests for the core system components
to ensure they work correctly.
"""

import sys
import os
from pathlib import Path

# Add the repository root to the Python path
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root))

def test_model_imports():
    """Test that all core models can be imported successfully."""
    try:
        from src.models.dataModel import AgentType, AgentResponse, TaskStatus, FinalPlan
        print("✓ Core models imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import models: {e}")
        return False


def test_agent_creation():
    """Test that agents can be created and respond correctly."""
    try:
        from src.models.dataModel import AgentType, AgentResponse
        from src.agents.specialists import BaseAgent, agent_registry
        
        # Test creating an agent
        cfo_agent = BaseAgent(AgentType.CFO)
        assert cfo_agent.agent_type == AgentType.CFO
        
        # Test agent execution
        response = cfo_agent.execute("Analyze Q3 budget projections")
        assert isinstance(response, AgentResponse)
        assert response.agent_id == AgentType.CFO.value
        assert response.confidence > 0
        
        # Test agent registry
        assert AgentType.CFO in agent_registry
        assert len(agent_registry) > 0
        
        print("✓ Agent creation and execution tests passed")
        return True
    except Exception as e:
        print(f"✗ Agent tests failed: {e}")
        return False


def test_orchestration_import():
    """Test that orchestration components can be imported."""
    try:
        from src.orchestration.runner import run_plan
        print("✓ Orchestration runner imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import orchestration: {e}")
        return False


def test_enum_values():
    """Test that enums have the expected values."""
    try:
        from src.models.dataModel import AgentType, TaskStatus
        
        # Test AgentType values
        expected_agents = {'CEO', 'COO', 'CFO', 'CTO', 'CMO'}
        actual_agents = {agent.value for agent in AgentType}
        assert expected_agents == actual_agents, f"Expected {expected_agents}, got {actual_agents}"
        
        # Test TaskStatus values
        expected_statuses = {'pending', 'in_progress', 'completed', 'failed', 'escalated', 'cancelled'}
        actual_statuses = {status.value for status in TaskStatus}
        assert expected_statuses == actual_statuses, f"Expected {expected_statuses}, got {actual_statuses}"
        
        print("✓ Enum values validation passed")
        return True
    except Exception as e:
        print(f"✗ Enum validation failed: {e}")
        return False


def test_data_model_creation():
    """Test that data models can be created with valid data."""
    try:
        from src.models.dataModel import AgentResponse, FinalPlan
        
        # Test AgentResponse creation
        response = AgentResponse(
            agent_id="CFO",
            task_id="task_123",
            response_data={"analysis": "Budget looks good"},
            confidence=0.85,
            reasoning="Based on historical data",
            citations=["source1.pdf"]
        )
        assert response.agent_id == "CFO"
        assert response.confidence == 0.85
        assert len(response.citations) == 1
        
        # Test FinalPlan creation
        plan = FinalPlan(
            plan_id="plan_456",
            synthesized_strategy="Expand into new markets",
            contributing_agents=["CFO", "CMO"],
            identified_risks=["Market volatility"],
            confidence_score=0.9
        )
        assert plan.plan_id == "plan_456"
        assert len(plan.contributing_agents) == 2
        assert plan.confidence_score == 0.9
        
        print("✓ Data model creation tests passed")
        return True
    except Exception as e:
        print(f"✗ Data model tests failed: {e}")
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("Running the_board system tests...")
    print("=" * 50)
    
    tests = [
        test_model_imports,
        test_agent_creation,
        test_orchestration_import,
        test_enum_values,
        test_data_model_creation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The core system is functional.")
        return True
    else:
        print(f"⚠️  {total - passed} tests failed. System needs attention.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)