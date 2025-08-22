"""
Odyssey Core Models
------------------
Core strategic request and response models for the Odyssey agent.
This is the primary interface for all strategic planning requests.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator
from .enums import StrategicScope, GoalCategory, RiskTolerance, StakeholderImpact, Priority
from .constraints import StrategicConstraint
from .metrics import SuccessMetric
from .context import CompetitiveContext, ResourceProfile


class OdysseyGoalRequest(BaseModel):
    """
    Comprehensive strategic goal request for Odyssey's analysis.
    
    This model captures the full strategic context needed for Odyssey to:
    - Synthesize multi-agent analysis
    - Make informed strategic decisions  
    - Create actionable plans with proper risk assessment
    - Maintain decision logs and strategic continuity
    """
    
    model_config = ConfigDict(
        frozen=False,
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "high_level_goal": "Launch a SaaS for SMB accounting in Q2",
                "strategic_scope": "strategic",
                "goal_category": "market_entry",
                "user_context": "Solo founder, $50k budget, basic Rails + Postgres stack",
                "priority": "high",
                "deadline": "2025-09-30T00:00:00Z",
                "risk_tolerance": "moderate",
                "stakeholder_impact": "customers",
                "success_metrics": [
                    {
                        "metric_name": "Monthly Recurring Revenue",
                        "target_value": "$10,000 MRR",
                        "timeline": "Q4 2025",
                        "is_primary": True
                    }
                ],
                "resource_profile": {
                    "budget_min": 25000,
                    "budget_max": 75000,
                    "team_max_size": 3,
                    "key_skills_needed": ["Rails development", "UX design", "SMB sales"]
                }
            }
        }
    )

    # ==============================
    # Core Identification
    # ==============================
    
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), 
        description="Unique identifier for this strategic request"
    )
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Server-side creation timestamp (UTC)"
    )
    
    # ==============================
    # Strategic Goal Definition
    # ==============================
    
    high_level_goal: str = Field(
        ..., 
        description="Primary strategic objective - the 'what' we want to achieve"
    )
    
    strategic_scope: StrategicScope = Field(
        default=StrategicScope.STRATEGIC,  # Use enum value directly
        description="The strategic scope and timeline of this initiative"
    )
    
    goal_category: GoalCategory = Field(
        ...,
        description="High-level business category this goal falls into"
    )
    
    strategic_context: Optional[str] = Field(
        None,
        description="Broader strategic context - how this fits into company vision"
    )
    
    # ==============================
    # Business Context & Constraints  
    # ==============================
    
    user_context: Optional[str] = Field(
        None, 
        description="Current situation, background, and additional context"
    )
    
    constraints: List[StrategicConstraint] = Field(
        default_factory=list,
        description="Specific constraints and limitations to consider"
    )
    
    assumptions: List[str] = Field(
        default_factory=list,
        description="Key assumptions underlying this strategic initiative"
    )
    
    # ==============================
    # Planning Parameters
    # ==============================
    
    priority: Priority = Field(
        default=Priority.medium, 
        description="Strategic priority level"
    )
    
    deadline: Optional[datetime] = Field(
        None, 
        description="Target completion date (ISO8601)"
    )
    
    risk_tolerance: RiskTolerance = Field(
        default=RiskTolerance.MODERATE,  # Use enum value directly
        description="Organization's risk appetite for this initiative"
    )
    
    # ==============================
    # Stakeholder & Impact Analysis
    # ==============================
    
    stakeholder_impact: StakeholderImpact = Field(
        default=StakeholderImpact.ALL_STAKEHOLDERS,  # Use enum value directly
        description="Primary stakeholder groups that will be affected"
    )
    
    success_metrics: List[SuccessMetric] = Field(
        default_factory=list,
        description="How success will be measured and validated"
    )
    
    # ==============================
    # Resource & Capability Context
    # ==============================
    
    resource_profile: Optional[ResourceProfile] = Field(
        None,
        description="Detailed resource availability and constraints"
    )
    
    # Legacy fields (maintained for backward compatibility)
    budget_range: Optional[str] = Field(
        None, 
        description="Budget constraints or range (use resource_profile for detailed budgeting)"
    )
    
    team_size: Optional[str] = Field(
        None, 
        description="Available team resources (use resource_profile for detailed team planning)"
    )
    
    industry: Optional[str] = Field(
        None, 
        description="Industry or sector context"
    )
    
    # ==============================
    # Competitive & Market Context
    # ==============================
    
    competitive_context: Optional[CompetitiveContext] = Field(
        None,
        description="Competitive landscape and market positioning information"
    )
    
    # ==============================
    # Decision Support & Traceability
    # ==============================
    
    previous_attempts: List[str] = Field(
        default_factory=list,
        description="Previous attempts at similar goals and their outcomes"
    )
    
    related_initiatives: List[str] = Field(
        default_factory=list,
        description="Other ongoing initiatives that might impact or synergize"
    )
    
    decision_criteria: List[str] = Field(
        default_factory=list,
        description="Key criteria that should guide strategic decisions"
    )
    
    # ==============================
    # Metadata & Extensibility
    # ==============================
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Free-form structured metadata for extensibility"
    )

    # ==============================
    # Validators
    # ==============================

    @field_validator("deadline")
    @classmethod
    def ensure_deadline_utc(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure deadline is in UTC timezone."""
        if v is None:
            return v
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)

    @field_validator("high_level_goal")
    @classmethod
    def goal_not_empty(cls, v: str) -> str:
        """Ensure the strategic goal is meaningful."""
        if not v or not v.strip():
            raise ValueError("high_level_goal must not be empty")
        if len(v.strip()) < 10:
            raise ValueError("high_level_goal should be at least 10 characters for meaningful strategic context")
        return v.strip()

    @field_validator("success_metrics")
    @classmethod
    def validate_success_metrics(cls, v: List[SuccessMetric]) -> List[SuccessMetric]:
        """Ensure at least one primary metric is defined if metrics are provided."""
        if v and not any(metric.is_primary for metric in v):
            # Auto-promote first metric to primary if none specified
            v[0].is_primary = True
        return v

    # ==============================
    # Strategic Analysis Helpers
    # ==============================
    
    def get_primary_success_metrics(self) -> List[SuccessMetric]:
        """Return only the primary success metrics."""
        return [metric for metric in self.success_metrics if metric.is_primary]
    
    def get_critical_constraints(self) -> List[StrategicConstraint]:
        """Return only critical-severity constraints."""
        return [constraint for constraint in self.constraints if constraint.severity == "critical"]
    
    def is_high_risk_initiative(self) -> bool:
        """Determine if this is a high-risk strategic initiative."""
        return (
            self.risk_tolerance in [RiskTolerance.AGGRESSIVE, RiskTolerance.EXPERIMENTAL] or
            self.strategic_scope == StrategicScope.TRANSFORMATIONAL or
            len(self.get_critical_constraints()) > 0
        )
    
    def requires_board_consensus(self) -> bool:
        """Determine if this initiative requires full board consensus."""
        return (
            self.strategic_scope in [StrategicScope.STRATEGIC, StrategicScope.TRANSFORMATIONAL] or
            self.priority == Priority.urgent or
            self.is_high_risk_initiative()
        )

    # ==============================
    # Serialization
    # ==============================

    def to_json(self) -> str:
        """Convert to JSON string."""
        return self.model_dump_json()

    @classmethod
    def from_json(cls, data: str) -> "OdysseyGoalRequest":
        """Create instance from JSON string."""
        return cls.model_validate_json(data)

    def to_strategic_summary(self) -> str:
        """Generate a strategic summary for decision logging."""
        summary_parts = [
            f"STRATEGIC INITIATIVE: {self.high_level_goal}",
            f"Scope: {self.strategic_scope.value.title()}",
            f"Category: {self.goal_category.value.title()}",
            f"Priority: {self.priority.value.title()}",
            f"Risk Tolerance: {self.risk_tolerance.value.title()}"
        ]
        
        if self.deadline:
            summary_parts.append(f"Target Deadline: {self.deadline.strftime('%Y-%m-%d')}")
            
        if self.success_metrics:
            primary_metrics = self.get_primary_success_metrics()
            if primary_metrics:
                metrics_str = ", ".join([m.metric_name for m in primary_metrics])
                summary_parts.append(f"Primary Success Metrics: {metrics_str}")
        
        return "\n".join(summary_parts)


class OdysseyStrategicPlan(BaseModel):
    """
    Odyssey's comprehensive strategic plan output.
    This is what Odyssey produces after synthesizing all agent inputs.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str = Field(..., description="Reference to original OdysseyGoalRequest")

    # Strategic synthesis
    executive_summary: str = Field(..., description="High-level strategic summary")
    strategic_analysis: str = Field(..., description="Detailed strategic analysis")
    recommended_approach: str = Field(..., description="Recommended strategic approach")

    # Multi-agent synthesis
    agent_contributions: Dict[str, str] = Field(default_factory=dict)
    synthesis_confidence: float = Field(..., ge=0.0, le=1.0)
    consensus_level: str = Field(..., description="Level of agent consensus")

    # Risk and opportunity assessment
    risk_assessment: List[str] = Field(default_factory=list)
    opportunity_analysis: List[str] = Field(default_factory=list)
    mitigation_strategies: List[str] = Field(default_factory=list)

    # Implementation roadmap
    phase_breakdown: List[Dict[str, Any]] = Field(default_factory=list)
    resource_allocation: Dict[str, Any] = Field(default_factory=dict)
    timeline_milestones: List[Dict[str, Any]] = Field(default_factory=list)

    # Decision documentation
    key_decisions: List[str] = Field(default_factory=list)
    decision_rationale: Dict[str, str] = Field(default_factory=dict)
    assumptions_validated: List[str] = Field(default_factory=list)

    # Success framework
    success_criteria: List[SuccessMetric] = Field(default_factory=list)
    kpi_dashboard: Dict[str, Any] = Field(default_factory=dict)
    review_checkpoints: List[Dict[str, Any]] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)
