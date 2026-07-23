"""Shared, validated contracts for the_board's execution lifecycle."""

from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel, Field, field_validator


class AgentType(str, Enum):
    CEO = "CEO"
    COO = "COO"
    CFO = "CFO"
    CTO = "CTO"
    CMO = "CMO"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"
    CANCELLED = "cancelled"


class AgentResponse(BaseModel):
    agent_id: str
    task_id: str
    response_data: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.8
    reasoning: str = ""
    citations: List[str] = Field(default_factory=list)

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, value: float) -> float:
        return max(0.0, min(1.0, value))


class FinalPlan(BaseModel):
    plan_id: str
    synthesized_strategy: str
    contributing_agents: List[str] = Field(default_factory=list)
    identified_risks: List[str] = Field(default_factory=list)
    confidence_score: float = 0.8

    @field_validator("confidence_score")
    @classmethod
    def clamp_confidence(cls, value: float) -> float:
        return max(0.0, min(1.0, value))
