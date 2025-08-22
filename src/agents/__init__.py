"""
Agents package for the_board multi-agent system.

This package contains the agent implementations that will execute
strategic planning tasks.
"""

from .specialists import BaseAgent, agent_registry

__all__ = [
    "BaseAgent",
    "agent_registry",
]
