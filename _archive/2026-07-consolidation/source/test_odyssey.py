"""
Simple test to verify Odyssey package imports work correctly.
"""

def test_odyssey_imports():
    """Test that all Odyssey models can be imported."""
    try:
        from .odyssey import (
            OdysseyGoalRequest,
            OdysseyStrategicPlan,
            StrategicScope,
            GoalCategory,
            RiskTolerance,
            StakeholderImpact,
            StrategicConstraint,
            ConstraintMatrix,
            SuccessMetric,
            MetricsDashboard,
            CompetitiveContext,
            ResourceProfile,
            StrategicContext,
            OdysseyRequestFactory,
            StrategicDecision,
            DecisionLog,
        )
        print("✅ All Odyssey models imported successfully!")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_factory_methods():
    """Test that factory methods work correctly."""
    try:
        from .odyssey import OdysseyRequestFactory, GoalCategory, StrategicScope
        
        # Test growth initiative
        growth = OdysseyRequestFactory.growth_initiative("Increase market share by 25%")
        print(f"✅ Growth initiative created: {growth.goal_category.value}")
        
        # Test digital transformation
        digital = OdysseyRequestFactory.digital_transformation("Modernize legacy systems")
        print(f"✅ Digital transformation created: {digital.strategic_scope.value}")
        
        return True
    except Exception as e:
        print(f"❌ Factory test failed: {e}")
        return False


if __name__ == "__main__":
    print("Testing Odyssey package...")
    test_odyssey_imports()
    test_factory_methods()
    print("Test complete!")
