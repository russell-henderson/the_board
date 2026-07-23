# Models Package - the_board

This package contains all data models for the the_board multi-agent system.

## Package Structure

```
src/models/
├── __init__.py              # Package initialization
├── dataModel.py             # Shared types used across all agents
├── odyssey/                 # Odyssey strategic planning models
│   ├── __init__.py         # Odyssey package exports
│   ├── core.py             # Core models (OdysseyGoalRequest, OdysseyStrategicPlan)
│   ├── enums.py            # Strategic enums (StrategicScope, GoalCategory, etc.)
│   ├── constraints.py      # Strategic constraints and limitations
│   ├── metrics.py          # Success metrics and measurement
│   ├── context.py          # Strategic context models
│   ├── factory.py          # Factory methods for common scenarios
│   └── decision_log.py     # Decision logging and audit trail
└── test_odyssey.py         # Simple test file for verification
```

## Migration from dataModel.py

### Before (Legacy)
```python
from dataModel import OdysseyGoalRequest, StrategicScope, GoalCategory
```

### After (New Structure)
```python
# Import from Odyssey package (recommended)
from models.odyssey import OdysseyGoalRequest, StrategicScope, GoalCategory

# Import shared types from dataModel
from models.dataModel import AgentType, TaskStatus, Priority
```

## Key Models

### Core Models
- **OdysseyGoalRequest**: Comprehensive strategic goal request
- **OdysseyStrategicPlan**: Strategic plan output from Odyssey

### Strategic Enums
- **StrategicScope**: tactical, strategic, transformational, crisis_response
- **GoalCategory**: growth, efficiency, innovation, market_entry, etc.
- **RiskTolerance**: conservative, moderate, aggressive, experimental
- **StakeholderImpact**: customers, employees, investors, etc.

### Supporting Models
- **StrategicConstraint**: Constraints and limitations
- **SuccessMetric**: How success is measured
- **CompetitiveContext**: Competitive landscape analysis
- **ResourceProfile**: Resource availability and constraints
- **StrategicContext**: Broader strategic context

### Utilities
- **OdysseyRequestFactory**: Factory methods for common scenarios
- **StrategicDecision**: Individual strategic decisions
- **DecisionLog**: Complete decision audit trail

## Factory Methods

The `OdysseyRequestFactory` provides convenient methods for creating common strategic scenarios:

```python
from models.odyssey import OdysseyRequestFactory

# Growth initiative
growth = OdysseyRequestFactory.growth_initiative("Increase market share by 25%")

# Digital transformation
digital = OdysseyRequestFactory.digital_transformation(
    "Modernize legacy systems",
    technology_constraints=["Must maintain 99.9% uptime"]
)

# Market entry
market = OdysseyRequestFactory.market_entry("Enter European market", "Germany")
```

## Backward Compatibility

**Note**: The old `dataModel.py` and `main.py` files have been removed to eliminate duplication. All imports now use the new package structure:

- **Odyssey models**: `from models.odyssey import ...`
- **Shared types**: `from models.dataModel import ...`

## Testing

Run the test file to verify the package works:

```bash
cd src/models
python test_odyssey.py
```

## Validation Features

The enhanced `OdysseyGoalRequest` includes:

- **Field validation**: Ensures goals are meaningful (min 10 chars)
- **Auto-primary metrics**: Automatically promotes first metric to primary if none specified
- **UTC deadline handling**: Ensures all deadlines are in UTC
- **Strategic analysis helpers**: Methods for risk assessment and consensus requirements

## Example Usage

```python
from models.odyssey import OdysseyGoalRequest, StrategicScope, GoalCategory, RiskTolerance
from models.odyssey import SuccessMetric, ResourceProfile

# Create a comprehensive strategic request
request = OdysseyGoalRequest(
    high_level_goal="Launch a SaaS platform for SMB accounting in Q2 2025",
    strategic_scope=StrategicScope.STRATEGIC,
    goal_category=GoalCategory.MARKET_ENTRY,
    risk_tolerance=RiskTolerance.MODERATE,
    success_metrics=[
        SuccessMetric(
            metric_name="Monthly Recurring Revenue",
            target_value="$10,000 MRR",
            timeline="Q4 2025",
            is_primary=True
        )
    ],
    resource_profile=ResourceProfile(
        budget_min=25000,
        budget_max=75000,
        team_max_size=3
    )
)

# Use strategic analysis helpers
print(f"High Risk: {request.is_high_risk_initiative()}")
print(f"Requires Board Consensus: {request.requires_board_consensus()}")
print(f"Strategic Summary:\n{request.to_strategic_summary()}")
```

## Next Steps

1. **Update imports** in existing code to use the new package structure
2. **Remove legacy imports** from the root `dataModel.py` once migration is complete
3. **Add comprehensive tests** for all models and validators
4. **Document API endpoints** that use these models
5. **Create migration scripts** for any stored data that needs updating
