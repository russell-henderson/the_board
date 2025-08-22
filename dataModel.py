"""
dataModel.py
---------------------
Core Pydantic models and enums for the the_board multi-agent system.
This version includes the complete TECHSPEC contract with:
  - OdysseyGoalRequest: User goal submission
  - FinalPlan: Synthesized strategy output
  - ErrorReport: Structured error reporting
  - UserCorrection: Feedback loop support
  - Enhanced agent and task management models
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ==============================
# Enums
# ==============================

class AgentType(str, Enum):
    """Core agent types for the Essential Five and additional specialists."""
    # Essential Five (Core Agents)
    CEO = "CEO"           # Odyssey - Master orchestrator
    CFO = "CFO"           # Abacus - Financial modeling
    CTO = "CTO"           # Nexus - Technical architecture
    COO = "COO"           # Momentum - Execution and operations
    CMO = "CMO"           # Muse - Marketing strategy

    # Additional Specialists
    CISO = "CISO"         # Guardian - Security and compliance
    CHRO = "CHRO"         # Pulse - HR and organizational design
    CIO = "CIO"           # Insight - Data strategy and analytics
    RESEARCH = "RESEARCH"  # Curio - Knowledge base maintenance
    STRATEGY = "STRATEGY"  # Vision - Long-term strategic positioning
    ENGINEERING = "ENGINEERING"  # Forge - Prototyping and infrastructure
    ETHICS = "ETHICS"     # Beacon - Ethical safeguards
    INNOVATION = "INNOVATION"  # Flux - Innovation scouting
    LEGAL = "LEGAL"       # Anchor - Legal and compliance
    KNOWLEDGE = "KNOWLEDGE"  # Scribe - Documentation and structuring
    CREATIVE = "CREATIVE"  # Spark - Creative design and storytelling
    LOGISTICS = "LOGISTICS"  # Vector - Resource allocation
    COMMUNICATIONS = "COMMUNICATIONS"  # Echo - Public relations
    SUSTAINABILITY = "SUSTAINABILITY"  # Horizon - ESG and sustainability
    UNKNOWN = "UNKNOWN"


class TaskStatus(str, Enum):
    """Task execution status tracking."""
    PENDING = "PENDING"           # Task created, waiting for assignment
    PLANNING = "PLANNING"         # /plan contract in progress
    IN_PROGRESS = "IN_PROGRESS"   # Task actively being worked on
    WAITING = "WAITING"           # Blocked on dependency or human input
    ESCALATED = "ESCALATED"       # Requires human intervention
    COMPLETED = "COMPLETED"       # Task finished successfully
    FAILED = "FAILED"             # Task failed with error
    CANCELLED = "CANCELLED"       # Task cancelled by user or system


class ConfidenceLevel(str, Enum):
    """Confidence scoring for agent outputs and final plans."""
    HIGH = "high"                 # ≥ 0.80 - High confidence
    MODERATE = "moderate"         # 0.50-0.79 - Moderate confidence
    LOW = "low"                   # < 0.50 - Uncertain, human review advised


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)
# ==============================
# Core Models
# ==============================


class OdysseyGoalRequest(BaseModel):
    """User goal submission for strategic analysis by the Board."""
    model_config = ConfigDict(
        frozen=False,
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "high_level_goal": "Launch a SaaS for SMB accounting in Q2",
                "user_context": "Solo founder, $50k budget, basic Rails + Postgres stack",
                "priority": "high",
                "deadline": "2025-09-30T00:00:00Z",
                "budget_range": "$25k–$75k",
                "team_size": "1–3",
                "industry": "Fintech / SMB",
                "metadata": {"source": "cli-smoke-test", "env": "dev"},
            }
        },
    )

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Client-supplied or generated request id")
    high_level_goal: str = Field(..., description="Primary strategic objective")
    user_context: Optional[str] = Field(None, description="Additional context, constraints, or background")
    priority: Priority = Field(default=Priority.medium, description="Goal priority")
    deadline: Optional[datetime] = Field(None, description="Target completion date (ISO8601)")
    budget_range: Optional[str] = Field(None, description="Budget constraints or range")
    team_size: Optional[str] = Field(None, description="Available team resources")
    industry: Optional[str] = Field(None, description="Industry or sector context")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Server-side creation timestamp (UTC)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Free-form structured metadata")

# --- Validators ---

    @field_validator("deadline")
    @classmethod
    def ensure_deadline_utc(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is None:
            return v
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)

    @field_validator("high_level_goal")
    @classmethod
    def goal_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("high_level_goal must not be empty")
        return v.strip()

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(cls, data: str) -> "OdysseyGoalRequest":
        return cls.model_validate_json(data)
    
 # --- JSON helpers (Pydantic v2 style) ---
 
    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(cls, data: str) -> "OdysseyGoalRequest":
        return cls.model_validate_json(data)
 

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

    @field_validator("content")
    @classmethod
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

    @field_validator("title", "instructions")
    @classmethod
    def non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError(
                "Fields 'title' and 'instructions' must not be empty")
        return v

    def mark(self, new_status: TaskStatus) -> None:
        self.status = new_status
        self.updated_at = datetime.utcnow()

    def add_output(self, response: AgentResponse) -> None:
        self.outputs = self.outputs + [response]
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return json.loads(self.json())


class FinalPlan(BaseModel):
    """Synthesized strategic output from the Board with confidence scoring."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_goal: str = Field(...,
                               description="The user's original high-level goal")
    synthesized_strategy: str = Field(...,
                                      description="Markdown-formatted strategic plan")
    contributing_agents: List[AgentType] = Field(default_factory=list)
    identified_risks: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    confidence_score: float = Field(..., ge=0.0, le=1.0,
                                    description="Overall confidence in the plan")
    execution_timeline: Optional[str] = Field(
        None, description="Recommended timeline for execution")
    resource_requirements: Optional[str] = Field(
        None, description="Required resources and budget")
    success_metrics: List[str] = Field(
        default_factory=list, description="KPIs to measure success")
    citations: List[str] = Field(
        default_factory=list, description="Source materials and references")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("synthesized_strategy")
    @classmethod
    def strategy_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("synthesized_strategy must not be empty")
        return v

    @property
    def confidence_level(self) -> ConfidenceLevel:
        """Get the confidence level based on the confidence score."""
        if self.confidence_score >= 0.80:
            return ConfidenceLevel.HIGH
        elif self.confidence_score >= 0.50:
            return ConfidenceLevel.MODERATE
        else:
            return ConfidenceLevel.LOW

    def to_json(self) -> str:
        return self.json()

    @classmethod
    def from_json(cls, data: str) -> "FinalPlan":
        return cls.parse_raw(data)


class ErrorReport(BaseModel):
    """Structured error reporting for escalations and debugging."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    error_type: str = Field(...,
                            description="Type of error (e.g., 'agent_failure', 'system_error')")
    error_message: str = Field(...,
                               description="Human-readable error description")
    error_code: Optional[str] = Field(
        None, description="Machine-readable error code")
    severity: str = Field(
        "medium", description="Error severity: low, medium, high, critical")
    affected_components: List[str] = Field(
        default_factory=list, description="Components affected by the error")
    stack_trace: Optional[str] = Field(
        None, description="Technical stack trace if available")
    user_context: Optional[str] = Field(
        None, description="User context when error occurred")
    suggested_actions: List[str] = Field(
        default_factory=list, description="Recommended actions to resolve")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = Field(
        None, description="When the error was resolved")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("error_message")
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("error_message must not be empty")
        return v

    def mark_resolved(self) -> None:
        """Mark the error as resolved."""
        self.resolved_at = datetime.utcnow()

    def to_json(self) -> str:
        return self.json()

    @classmethod
    def from_json(cls, data: str) -> "ErrorReport":
        return cls.parse_raw(data)


class UserCorrection(BaseModel):
    """User feedback and corrections for continuous improvement."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_plan_id: str = Field(...,
                                  description="ID of the plan being corrected")
    correction_type: str = Field(
        ..., description="Type of correction (e.g., 'factual_error', 'missing_context')")
    description: str = Field(...,
                             description="Detailed description of the correction needed")
    suggested_fix: Optional[str] = Field(
        None, description="User's suggested correction")
    priority: str = Field(
        "medium", description="Correction priority: low, medium, high")
    affected_sections: List[str] = Field(
        default_factory=list, description="Sections of the plan that need updates")
    user_confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="User's confidence in the correction")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(
        "pending", description="Status: pending, in_progress, completed, rejected")
    agent_response: Optional[str] = Field(
        None, description="Response from the Board regarding the correction")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("description must not be empty")
        return v

    def to_json(self) -> str:
        return self.json()

    @classmethod
    def from_json(cls, data: str) -> "UserCorrection":
        return cls.parse_raw(data)


class SynthesizedOutput(BaseModel):
    """
    Final stitched answer produced by the CEO/orchestrator.
    LEGACY: This model is retained for backward compatibility.
    Use FinalPlan for new implementations.
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

    @field_validator("original_query", "analysis")
    @classmethod
    def non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("original_query and analysis must not be empty")
        return v

    def to_json(self) -> str:
        return self.json()

    @classmethod
    def from_json(cls, data: str) -> "SynthesizedOutput":
        return cls.parse_raw(data)


# ==============================
# Knowledge Layer Models
# ==============================

class KnowledgeDocument(BaseModel):
    """Document stored in the ChromaDB knowledge base."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content for embedding")
    source: str = Field(..., description="Source of the document")
    document_type: str = Field(
        ..., description="Type of document (e.g., 'research_paper', 'news_article')")
    tags: List[str] = Field(default_factory=list,
                            description="Categorization tags")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("title", "content", "source")
    @classmethod
    def required_fields_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("title, content, and source must not be empty")
        return v


class Citation(BaseModel):
    """Citation reference for knowledge sources."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(..., description="Cited work title")
    authors: List[str] = Field(
        default_factory=list, description="Author names")
    source: str = Field(..., description="Source URL or reference")
    publication_date: Optional[datetime] = Field(
        None, description="Publication date")
    document_type: str = Field(..., description="Type of source")
    relevance_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Relevance to the query")
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ==============================
# Utility Models
# ==============================

class HealthCheck(BaseModel):
    """System health check response."""
    status: str = "ok"
    time: datetime = Field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = Field(default_factory=dict)


class SystemStatus(BaseModel):
    """Comprehensive system status including all components."""
    overall_status: str = Field(..., description="Overall system health")
    components: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Status of individual components")
    last_check: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(..., description="System version")
    uptime: Optional[str] = Field(None, description="System uptime")


class AgentRegistry(BaseModel):
    """Registry of available agents and their capabilities."""
    agents: Dict[AgentType, Dict[str, Any]] = Field(
        default_factory=dict, description="Agent definitions")
    total_count: int = Field(
        0, description="Total number of registered agents")
    last_updated: datetime = Field(default_factory=datetime.utcnow)


# ==============================
# API Response Models
# ==============================

class PlanResponse(BaseModel):
    """Response to a plan creation request."""
    plan_id: str = Field(..., description="ID of the created plan")
    status: str = Field(..., description="Current plan status")
    estimated_completion: Optional[datetime] = Field(
        None, description="Estimated completion time")
    message: str = Field(..., description="Human-readable status message")


class TaskUpdateResponse(BaseModel):
    """Response to a task update request."""
    task_id: str = Field(..., description="ID of the updated task")
    new_status: TaskStatus = Field(..., description="New task status")
    message: str = Field(..., description="Update confirmation message")
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ==============================
# Legacy Support
# ==============================

# For backward compatibility, export the old names
__all__ = [
    # Core models
    "OdysseyGoalRequest",
    "AgentTask",
    "AgentResponse",
    "FinalPlan",
    "ErrorReport",
    "UserCorrection",

    # Legacy models
    "SynthesizedOutput",
    "UserQuery",
    "AgentMessage",

    # Knowledge models
    "KnowledgeDocument",
    "Citation",

    # Utility models
    "HealthCheck",
    "SystemStatus",
    "AgentRegistry",

    # API models
    "PlanResponse",
    "TaskUpdateResponse",

    # Enums
    "AgentType",
    "TaskStatus",
    "ConfidenceLevel",
]
