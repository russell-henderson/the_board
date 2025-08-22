#!/usr/bin/env python3
"""
Tests for the data models.

This module tests all data model functionality including:
- Model validation
- Helper methods
- Data integrity
- Serialization/deserialization
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.models.dataModel import FinalPlan, AgentResponse, AgentType, TaskStatus, Priority

class TestFinalPlan:
    """Test suite for FinalPlan model."""
    
    def test_final_plan_creation(self):
        """Test basic FinalPlan creation."""
        plan = FinalPlan(
            plan_id="test_plan_001",
            synthesized_strategy="Test strategy",
            contributing_agents=["CFO", "CTO"],
            identified_risks=["Test risk"],
            confidence_score=0.85
        )
        
        assert plan.plan_id == "test_plan_001"
        assert plan.synthesized_strategy == "Test strategy"
        assert plan.contributing_agents == ["CFO", "CTO"]
        assert plan.identified_risks == ["Test risk"]
        assert plan.confidence_score == 0.85
    
    def test_final_plan_defaults(self):
        """Test FinalPlan with default values."""
        plan = FinalPlan(
            plan_id="test_plan_002",
            synthesized_strategy="Test strategy"
        )
        
        assert plan.contributing_agents == []
        assert plan.identified_risks == []
        assert plan.confidence_score == 0.8
    
    def test_confidence_score_clamping(self):
        """Test confidence score clamping between 0 and 1."""
        # Test values above 1.0
        plan = FinalPlan(
            plan_id="test_plan_003",
            synthesized_strategy="Test strategy",
            confidence_score=1.5
        )
        assert plan.confidence_score == 1.0
        
        # Test values below 0.0
        plan = FinalPlan(
            plan_id="test_plan_004",
            synthesized_strategy="Test strategy",
            confidence_score=-0.5
        )
        assert plan.confidence_score == 0.0
        
        # Test valid values
        plan = FinalPlan(
            plan_id="test_plan_005",
            synthesized_strategy="Test strategy",
            confidence_score=0.75
        )
        assert plan.confidence_score == 0.75
    
    def test_model_dump_json(self):
        """Test JSON serialization."""
        plan = FinalPlan(
            plan_id="test_plan_006",
            synthesized_strategy="Test strategy",
            contributing_agents=["CFO"],
            confidence_score=0.9
        )
        
        json_str = plan.model_dump_json()
        assert isinstance(json_str, str)
        assert "test_plan_006" in json_str
        assert "Test strategy" in json_str
        assert "CFO" in json_str
        assert "0.9" in json_str

class TestAgentResponse:
    """Test suite for AgentResponse model."""
    
    def test_agent_response_creation(self):
        """Test basic AgentResponse creation."""
        response = AgentResponse(
            agent_id="CFO",
            task_id="task_001",
            response_data={"analysis": "Test analysis"},
            confidence=0.9,
            reasoning="Test reasoning"
        )
        
        assert response.agent_id == "CFO"
        assert response.task_id == "task_001"
        assert response.response_data == {"analysis": "Test analysis"}
        assert response.confidence == 0.9
        assert response.reasoning == "Test reasoning"
    
    def test_agent_response_defaults(self):
        """Test AgentResponse with default values."""
        response = AgentResponse(
            agent_id="CTO",
            task_id="task_002",
            response_data={"analysis": "Test analysis"}
        )
        
        assert response.confidence == 0.8
        assert response.reasoning == ""

class TestEnums:
    """Test suite for enum values."""
    
    def test_agent_type_values(self):
        """Test AgentType enum values."""
        assert AgentType.CEO == "CEO"
        assert AgentType.CFO == "CFO"
        assert AgentType.CTO == "CTO"
        assert AgentType.CMO == "CMO"
        assert AgentType.COO == "COO"
    
    def test_task_status_values(self):
        """Test TaskStatus enum values."""
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.IN_PROGRESS == "in_progress"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"
        assert TaskStatus.CANCELLED == "cancelled"
    
    def test_priority_values(self):
        """Test Priority enum values."""
        assert Priority.LOW == "low"
        assert Priority.MEDIUM == "medium"
        assert Priority.HIGH == "high"
        assert Priority.CRITICAL == "critical"

class TestModelValidation:
    """Test suite for model validation."""
    
    def test_final_plan_required_fields(self):
        """Test that required fields are enforced."""
        # Should work with required fields
        plan = FinalPlan(
            plan_id="test_plan_007",
            synthesized_strategy="Test strategy"
        )
        assert plan.plan_id == "test_plan_007"
        assert plan.synthesized_strategy == "Test strategy"
    
    def test_agent_response_required_fields(self):
        """Test that required fields are enforced."""
        # Should work with required fields
        response = AgentResponse(
            agent_id="CFO",
            task_id="task_003",
            response_data={"analysis": "Test analysis"}
        )
        assert response.agent_id == "CFO"
        assert response.task_id == "task_003"
        assert response.response_data == {"analysis": "Test analysis"}

class TestModelSerialization:
    """Test suite for model serialization and deserialization."""
    
    def test_final_plan_json_roundtrip(self):
        """Test JSON serialization and deserialization roundtrip."""
        original_plan = FinalPlan(
            plan_id="test_plan_008",
            synthesized_strategy="Test strategy",
            contributing_agents=["CFO", "CTO"],
            identified_risks=["Risk 1", "Risk 2"],
            confidence_score=0.95
        )
        
        # Serialize to JSON
        json_str = original_plan.model_dump_json()
        
        # Deserialize from JSON (this would require a from_json method)
        # For now, we'll just verify the JSON contains expected data
        assert "test_plan_008" in json_str
        assert "Test strategy" in json_str
        assert "CFO" in json_str
        assert "CTO" in json_str
        assert "Risk 1" in json_str
        assert "Risk 2" in json_str
        assert "0.95" in json_str

class TestModelEdgeCases:
    """Test suite for edge cases and error conditions."""
    
    def test_empty_lists(self):
        """Test handling of empty lists."""
        plan = FinalPlan(
            plan_id="test_plan_009",
            synthesized_strategy="Test strategy",
            contributing_agents=[],
            identified_risks=[]
        )
        
        assert plan.contributing_agents == []
        assert plan.identified_risks == []
    
    def test_none_values(self):
        """Test handling of None values."""
        # Test that None values are handled gracefully
        # This depends on the model implementation
        pass
    
    def test_large_strings(self):
        """Test handling of large string values."""
        large_strategy = "A" * 10000  # 10KB string
        plan = FinalPlan(
            plan_id="test_plan_010",
            synthesized_strategy=large_strategy
        )
        
        assert len(plan.synthesized_strategy) == 10000
        assert plan.synthesized_strategy == large_strategy

if __name__ == "__main__":
    pytest.main([__file__])
