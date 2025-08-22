"""
Core data models for the_board system.

This module defines the essential data structures used throughout the multi-agent
orchestration system.
"""

from enum import Enum
from typing import Any, Dict, List, Optional


class AgentType(str, Enum):
    """Enumeration of available agent types."""
    CEO = "CEO"
    COO = "COO"
    CFO = "CFO"
    CTO = "CTO"
    CMO = "CMO"


class TaskStatus(str, Enum):
    """Enumeration of task execution states."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"
    CANCELLED = "cancelled"


class AgentResponse:
    """Response from an agent after task execution."""
    
    def __init__(self, agent_id: str, task_id: str, response_data: Dict[str, Any] = None, 
                 confidence: float = 0.8, reasoning: str = "", citations: List[str] = None):
        self.agent_id = agent_id
        self.task_id = task_id
        self.response_data = response_data or {}
        self.confidence = max(0.0, min(1.0, confidence))  # Clamp between 0-1
        self.reasoning = reasoning
        self.citations = citations or []


class FinalPlan:
    """Final synthesized strategic plan."""
    
    def __init__(self, plan_id: str, synthesized_strategy: str, contributing_agents: List[str] = None,
                 identified_risks: List[str] = None, confidence_score: float = 0.8):
        self.plan_id = plan_id
        self.synthesized_strategy = synthesized_strategy
        self.contributing_agents = contributing_agents or []
        self.identified_risks = identified_risks or []
        self.confidence_score = max(0.0, min(1.0, confidence_score))  # Clamp between 0-1