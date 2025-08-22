"""
Odyssey-specific enums for strategic planning.
"""

from enum import Enum


class StrategicScope(str, Enum):
    """Defines the strategic scope of the goal."""
    TACTICAL = "tactical"           # Short-term, operational focus (weeks-months)
    STRATEGIC = "strategic"         # Medium-term strategic initiative (quarters)
    TRANSFORMATIONAL = "transformational"  # Long-term, company-changing (years)
    CRISIS_RESPONSE = "crisis_response"    # Urgent response to critical situation


class GoalCategory(str, Enum):
    """High-level categorization of business goals."""
    GROWTH = "growth"                    # Revenue, market expansion
    EFFICIENCY = "efficiency"            # Process optimization, cost reduction  
    INNOVATION = "innovation"            # New products, R&D, technology
    MARKET_ENTRY = "market_entry"        # New markets, customer segments
    DIGITAL_TRANSFORMATION = "digital_transformation"  # Tech modernization
    ORGANIZATIONAL = "organizational"     # Team building, culture, structure
    FINANCIAL = "financial"              # Funding, profitability, cash flow
    COMPLIANCE = "compliance"            # Regulatory, legal, governance
    SUSTAINABILITY = "sustainability"    # ESG, environmental initiatives
    COMPETITIVE = "competitive"          # Market positioning, differentiation


class RiskTolerance(str, Enum):
    """Risk appetite for the strategic initiative."""
    CONSERVATIVE = "conservative"        # Low risk, proven approaches
    MODERATE = "moderate"               # Balanced risk/reward
    AGGRESSIVE = "aggressive"           # High risk, high reward
    EXPERIMENTAL = "experimental"       # Innovation-focused, accept failures


class StakeholderImpact(str, Enum):
    """Primary stakeholder groups affected."""
    CUSTOMERS = "customers"
    EMPLOYEES = "employees" 
    INVESTORS = "investors"
    PARTNERS = "partners"
    COMMUNITY = "community"
    ALL_STAKEHOLDERS = "all_stakeholders"


class Priority(str, Enum):
    """Strategic priority levels."""
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"
