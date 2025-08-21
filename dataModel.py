"""
dataModel.py
---------------------
Core Pydantic models and enums for the the_board multi-agent system.
This version patches SynthesizedOutput to include:
  - identified_risks: Optional[List[str]]
  - plan_level_confidence_score: Optional[float] in [0.0, 1.0]
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


# ==============================
# Enums
# ==============================

class AgentType(str, Enum):
    CEO = "CEO"
    CTO = "CTO"
    CFO = "CFO"
    COO = "COO"
    CPO = "CPO"  # Product
    CMO = "CMO"  # Marketing
    CRO = "CRO"  # Revenue / Sales
    LEGAL = "LEGAL"
    SECURITY = "SECURITY"
    RESEARCH = "RESEARCH"
    ANALYST = "ANALYST"
    EDITOR = "EDITOR"
    UNKNOWN = "UNKNOWN"


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    PLANNING = "PLANNING"   # /plan contract in progress
    IN_PROGRESS = "IN_PROGRESS"
    WAITING = "WAITING"     # blocked on dependency or human input
    ESCALATED = "ESCALATED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


# ==============================
# Core Models
# ==============================

class UserQuery(BaseModel):
    """Inbound user request captured at the orchestration boundary."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    query: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_json(self) -> str:
        return self.json()

    @classmethod
    def from_json(cls, data: str) -> "UserQuery":
        return cls.parse_raw(data)


class AgentMessage(BaseModel):
    """Low-level message between agents over the bus."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender: AgentType
    recipient: AgentType
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None  # tie-back to task or query
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return json.loads(self.json())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMessage":
        return cls.parse_obj(data)


class AgentResponse(BaseModel):
    """Structured output from a single agent for a given prompt or task."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent: AgentType
    content: str
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    citations: List[str] = Field(default_factory=list)
    tokens_used: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    debug: Dict[str, Any] = Field(default_factory=dict)

    @validator("content")
    def content_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("AgentResponse.content must not be empty")
        return v

    def to_json(self) -> str:
        return self.json()

    @classmethod
    def from_json(cls, data: str) -> "AgentResponse":
        return cls.parse_raw(data)


class AgentTask(BaseModel):
    """Unit of work managed by the orchestrator and assigned to agents."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    owner: AgentType = AgentType.CEO
    assigned_to: Optional[AgentType] = None
    status: TaskStatus = TaskStatus.PENDING
    title: str
    instructions: str
    parent_task_id: Optional[str] = None
    depends_on: List[str] = Field(default_factory=list)
    outputs: List[AgentResponse] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator("title", "instructions")
    def non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Fields 'title' and 'instructions' must not be empty")
        return v

    def mark(self, new_status: TaskStatus) -> None:
        self.status = new_status
        self.updated_at = datetime.utcnow()

    def add_output(self, response: AgentResponse) -> None:
        self.outputs.append(response)
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return json.loads(self.json())


class SynthesizedOutput(BaseModel):
    """
    Final stitched answer produced by the CEO/orchestrator.
    PATCH: includes optional identified_risks and plan_level_confidence_score.
    """
    original_query: str
    analysis: str
    contributing_agents: List[AgentType]

    # Patched fields (Optional in MVP, enforceable later)
    identified_risks: Optional[List[str]] = None
    plan_level_confidence_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Overall confidence in the plan, 0.0..1.0"
    )

    # Optional trace fields
    decision_log: Optional[List[str]] = None
    citations: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    @validator("original_query", "analysis")
    def non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("original_query and analysis must not be empty")
        return v

    def to_json(self) -> str:
        return self.json()

    @classmethod
    def from_json(cls, data: str) -> "SynthesizedOutput":
        return cls.parse_raw(data)


# ============
# Utilities
# ============

class HealthCheck(BaseModel):
    status: str = "ok"
    time: datetime = Field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = Field(default_factory=dict)
