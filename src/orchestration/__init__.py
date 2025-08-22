"""
Orchestration package for the_board multi-agent system.

This package contains the orchestration logic that coordinates
agent execution and manages the workflow.
"""

from .runner import run_plan

__all__ = [
    "run_plan",
]
