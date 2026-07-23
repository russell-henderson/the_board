"""
Factory methods for creating common strategic scenarios.
"""

from typing import List, Optional

from .core import OdysseyGoalRequest
from .enums import GoalCategory, RiskTolerance, StrategicScope
from .constraints import StrategicConstraint
from .metrics import SuccessMetric


class OdysseyRequestFactory:
    """Factory for creating common types of strategic requests."""

    @staticmethod
    def growth_initiative(
        goal: str,
        target_metrics: Optional[List[SuccessMetric]] = None,
        **kwargs
    ) -> OdysseyGoalRequest:
        """Create a growth-focused initiative."""
        return OdysseyGoalRequest(
            high_level_goal=goal,
            goal_category=GoalCategory.GROWTH,
            strategic_scope=StrategicScope.STRATEGIC,
            success_metrics=target_metrics or [],
            **kwargs
        )

    @staticmethod
    def digital_transformation(
        goal: str,
        technology_constraints: Optional[List[str]] = None,
        **kwargs
    ) -> OdysseyGoalRequest:
        """Create a digital transformation initiative."""
        constraints = []
        if technology_constraints:
            constraints = [
                StrategicConstraint(
                    type="technology",
                    description=constraint,
                    severity="high"
                ) for constraint in technology_constraints
            ]

        return OdysseyGoalRequest(
            high_level_goal=goal,
            goal_category=GoalCategory.DIGITAL_TRANSFORMATION,
            strategic_scope=StrategicScope.TRANSFORMATIONAL,
            risk_tolerance=RiskTolerance.MODERATE,
            constraints=constraints,
            **kwargs
        )

    @staticmethod
    def market_entry(
        goal: str,
        target_market: str,
        competitive_analysis: Optional[str] = None,
        **kwargs
    ) -> OdysseyGoalRequest:
        """Create a market entry initiative."""
        return OdysseyGoalRequest(
            high_level_goal=goal,
            goal_category=GoalCategory.MARKET_ENTRY,
            strategic_scope=StrategicScope.STRATEGIC,
            risk_tolerance=RiskTolerance.AGGRESSIVE,
            user_context=f"Entering new market: {target_market}",
            **kwargs
        )

    @staticmethod
    def efficiency_initiative(
        goal: str,
        current_processes: List[str],
        target_savings: Optional[str] = None,
        **kwargs
    ) -> OdysseyGoalRequest:
        """Create an efficiency/optimization initiative."""
        metrics = []
        if target_savings:
            metrics.append(SuccessMetric(
                metric_name="Cost Savings",
                target_value=target_savings,
                is_primary=True
            ))
        
        return OdysseyGoalRequest(
            high_level_goal=goal,
            goal_category=GoalCategory.EFFICIENCY,
            strategic_scope=StrategicScope.TACTICAL,
            risk_tolerance=RiskTolerance.CONSERVATIVE,
            success_metrics=metrics,
            user_context=f"Optimizing processes: {', '.join(current_processes)}",
            **kwargs
        )

    @staticmethod
    def innovation_initiative(
        goal: str,
        innovation_type: str = "product",
        experimental_budget: Optional[float] = None,
        **kwargs
    ) -> OdysseyGoalRequest:
        """Create an innovation-focused initiative."""
        return OdysseyGoalRequest(
            high_level_goal=goal,
            goal_category=GoalCategory.INNOVATION,
            strategic_scope=StrategicScope.TRANSFORMATIONAL,
            risk_tolerance=RiskTolerance.EXPERIMENTAL,
            user_context=f"Innovation type: {innovation_type}",
            **kwargs
        )

    @staticmethod
    def crisis_response(
        goal: str,
        urgency_level: str = "high",
        stakeholders_affected: Optional[List[str]] = None,
        **kwargs
    ) -> OdysseyGoalRequest:
        """Create a crisis response initiative."""
        return OdysseyGoalRequest(
            high_level_goal=goal,
            goal_category=GoalCategory.COMPLIANCE,  # Often compliance-related
            strategic_scope=StrategicScope.CRISIS_RESPONSE,
            risk_tolerance=RiskTolerance.CONSERVATIVE,
            priority="urgent",
            user_context=f"Urgency: {urgency_level}",
            **kwargs
        )
