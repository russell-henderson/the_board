"""
Decision logging and audit trail models for Odyssey.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class StrategicDecision(BaseModel):
    """Individual strategic decision made by Odyssey."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    decision_point: str = Field(..., description="What decision was made")
    rationale: str = Field(..., description="Why this decision was made")
    alternatives_considered: List[str] = Field(default_factory=list, description="Alternative options that were considered")
    risk_assessment: Optional[str] = Field(None, description="Risk assessment for this decision")
    expected_outcome: Optional[str] = Field(None, description="Expected outcome of this decision")
    decision_maker: str = Field(default="Odyssey", description="Who made this decision")
    contributing_agents: List[str] = Field(default_factory=list, description="Agents that contributed to this decision")
    confidence_level: float = Field(..., ge=0.0, le=1.0, description="Confidence level in this decision (0.0-1.0)")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    def get_confidence_description(self) -> str:
        """Get human-readable confidence level description."""
        if self.confidence_level >= 0.8:
            return "High"
        elif self.confidence_level >= 0.6:
            return "Moderate"
        elif self.confidence_level >= 0.4:
            return "Low"
        else:
            return "Very Low"
    
    def is_high_confidence(self) -> bool:
        """Check if this is a high-confidence decision."""
        return self.confidence_level >= 0.8


class DecisionLog(BaseModel):
    """Complete decision audit trail for a strategic initiative."""
    request_id: str = Field(..., description="Reference to OdysseyGoalRequest")
    initiative_name: str = Field(..., description="Name of the initiative")
    decisions: List[StrategicDecision] = Field(default_factory=list, description="All decisions made for this initiative")
    decision_timeline: List[Dict[str, Any]] = Field(default_factory=list, description="Timeline of decision points")
    key_turning_points: List[str] = Field(default_factory=list, description="Critical decision points that changed direction")
    lessons_learned: List[str] = Field(default_factory=list, description="Key lessons learned from decisions")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    def add_decision(self, decision: StrategicDecision) -> None:
        """Add a new decision to the log."""
        self.decisions.append(decision)
        self.last_updated = datetime.now(timezone.utc)
        
        # Update timeline
        self.decision_timeline.append({
            "timestamp": decision.created_at.isoformat(),
            "decision_id": decision.id,
            "decision_point": decision.decision_point,
            "confidence": decision.confidence_level
        })
    
    def get_decisions_by_confidence(self, min_confidence: float = 0.0) -> List[StrategicDecision]:
        """Get decisions filtered by minimum confidence level."""
        return [d for d in self.decisions if d.confidence_level >= min_confidence]
    
    def get_high_impact_decisions(self) -> List[StrategicDecision]:
        """Get decisions that are likely high-impact based on confidence and context."""
        return [d for d in self.decisions if d.is_high_confidence() and d.risk_assessment]
    
    def get_decision_summary(self) -> str:
        """Generate a summary of all decisions made."""
        if not self.decisions:
            return f"No decisions recorded for {self.initiative_name}"
        
        summary_parts = [f"Decision Summary for {self.initiative_name}:"]
        summary_parts.append(f"Total Decisions: {len(self.decisions)}")
        
        high_confidence = len([d for d in self.decisions if d.is_high_confidence()])
        summary_parts.append(f"High Confidence Decisions: {high_confidence}")
        
        if self.key_turning_points:
            summary_parts.append(f"Key Turning Points: {len(self.key_turning_points)}")
        
        if self.lessons_learned:
            summary_parts.append(f"Lessons Learned: {len(self.lessons_learned)}")
        
        return "\n".join(summary_parts)
