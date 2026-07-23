"""
Contextual models for strategic decision-making.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class CompetitiveContext(BaseModel):
    """Information about competitive landscape."""
    primary_competitors: List[str] = Field(default_factory=list, description="Main competitors in the market")
    competitive_advantages: List[str] = Field(default_factory=list, description="Our key competitive strengths")
    market_threats: List[str] = Field(default_factory=list, description="Potential threats from competitors or market changes")
    market_opportunities: List[str] = Field(default_factory=list, description="Market opportunities we can capitalize on")
    market_position: Optional[str] = Field(None, description="Our current market position (leader, challenger, niche, etc.)")
    differentiation_strategy: Optional[str] = Field(None, description="How we differentiate from competitors")
    
    def get_competitive_intensity(self) -> str:
        """Assess competitive intensity based on number of competitors."""
        if len(self.primary_competitors) == 0:
            return "low"
        elif len(self.primary_competitors) <= 3:
            return "moderate"
        else:
            return "high"


class ResourceProfile(BaseModel):
    """Detailed resource availability and constraints."""
    budget_min: Optional[float] = Field(None, description="Minimum budget available")
    budget_max: Optional[float] = Field(None, description="Maximum budget available")
    team_current_size: Optional[int] = Field(None, description="Current team size")
    team_max_size: Optional[int] = Field(None, description="Maximum team size possible")
    key_skills_available: List[str] = Field(default_factory=list, description="Skills currently available in the team")
    key_skills_needed: List[str] = Field(default_factory=list, description="Skills needed but not currently available")
    technology_stack: List[str] = Field(default_factory=list, description="Current technology stack")
    external_dependencies: List[str] = Field(default_factory=list, description="External systems or services we depend on")
    resource_gaps: List[str] = Field(default_factory=list, description="Identified resource gaps")
    
    def get_budget_range(self) -> Optional[str]:
        """Get formatted budget range string."""
        if self.budget_min and self.budget_max:
            return f"${self.budget_min:,.0f} - ${self.budget_max:,.0f}"
        elif self.budget_min:
            return f"${self.budget_min:,.0f}+"
        elif self.budget_max:
            return f"Up to ${self.budget_max:,.0f}"
        return None
    
    def get_team_range(self) -> Optional[str]:
        """Get formatted team size range string."""
        if self.team_current_size and self.team_max_size:
            return f"{self.team_current_size} - {self.team_max_size}"
        elif self.team_current_size:
            return f"{self.team_current_size}+"
        elif self.team_max_size:
            return f"Up to {self.team_max_size}"
        return None


class StrategicContext(BaseModel):
    """Broader strategic context and environmental factors."""
    company_vision: Optional[str] = Field(None, description="Company's long-term vision and mission")
    current_strategic_priorities: List[str] = Field(default_factory=list, description="Current strategic priorities")
    organizational_maturity: Optional[str] = Field(None, description="Organization's maturity level (startup, growth, mature, etc.)")
    market_conditions: Optional[str] = Field(None, description="Current market conditions and trends")
    regulatory_environment: List[str] = Field(default_factory=list, description="Regulatory requirements and constraints")
    technology_trends: List[str] = Field(default_factory=list, description="Relevant technology trends")
    
    def get_strategic_alignment_score(self, initiative_goals: List[str]) -> float:
        """Calculate alignment score between initiative and strategic priorities."""
        if not self.current_strategic_priorities or not initiative_goals:
            return 0.0
        
        matches = sum(1 for goal in initiative_goals 
                     if any(priority.lower() in goal.lower() 
                           for priority in self.current_strategic_priorities))
        return matches / len(initiative_goals)
