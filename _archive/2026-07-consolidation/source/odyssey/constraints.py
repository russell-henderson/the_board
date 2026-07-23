"""
Strategic constraints and limitation models for Odyssey.
"""

from typing import List

from pydantic import BaseModel, Field


class StrategicConstraint(BaseModel):
    """Represents a constraint or limitation on the strategic initiative."""
    type: str = Field(..., description="Type of constraint (budget, time, regulatory, etc.)")
    description: str = Field(..., description="Detailed description of the constraint")
    severity: str = Field("medium", description="Impact level: low, medium, high, critical")
    negotiable: bool = Field(True, description="Whether this constraint can be adjusted")
    mitigation_options: List[str] = Field(default_factory=list, description="Possible ways to address this constraint")


class ConstraintMatrix(BaseModel):
    """Collection of constraints organized by type and priority."""
    critical_constraints: List[StrategicConstraint] = Field(default_factory=list)
    high_priority_constraints: List[StrategicConstraint] = Field(default_factory=list)
    moderate_constraints: List[StrategicConstraint] = Field(default_factory=list)

    def get_all_constraints(self) -> List[StrategicConstraint]:
        """Return all constraints combined."""
        return self.critical_constraints + self.high_priority_constraints + self.moderate_constraints
    
    def get_constraints_by_type(self, constraint_type: str) -> List[StrategicConstraint]:
        """Return constraints filtered by type."""
        all_constraints = self.get_all_constraints()
        return [c for c in all_constraints if c.type == constraint_type]
    
    def get_constraints_by_severity(self, severity: str) -> List[StrategicConstraint]:
        """Return constraints filtered by severity."""
        all_constraints = self.get_all_constraints()
        return [c for c in all_constraints if c.severity == severity]
