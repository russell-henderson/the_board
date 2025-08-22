"""
Agent specialists for the_board multi-agent system.

This module contains stub implementations of the core agents that will
eventually be replaced with actual LLM-powered logic.
"""

from ..models.dataModel import AgentResponse, AgentType


class BaseAgent:
    """Base class for all agent specialists."""
    
    def __init__(self, agent_type: AgentType):
        self.agent_type = agent_type

    def execute(self, task_description: str) -> AgentResponse:
        """
        Simulates the agent performing a task.
        
        Args:
            task_description: Description of the task to execute
            
        Returns:
            AgentResponse: The agent's analysis and findings
            
        Raises:
            ValueError: If task_description is empty or invalid
        """
        if not task_description or not task_description.strip():
            raise ValueError("Task description cannot be empty")
            
        print(f"[{self.agent_type.value}] Executing task: {task_description}")
        
        # This is the "stub" logic. It just returns a placeholder response.
        try:
            analysis = f"This is a placeholder analysis from the {self.agent_type.value} agent for the task: '{task_description}'."
            
            # Simulate different confidence levels based on task complexity
            confidence = 0.85 if len(task_description.split()) > 3 else 0.75
            
            return AgentResponse(
                agent_id=self.agent_type.value,
                task_id="stub_task_id",  # Will be replaced with actual task ID
                response_data={"analysis": analysis, "task_complexity": len(task_description.split())},
                confidence=confidence,
                reasoning=f"Stub response from {self.agent_type.value} agent based on task analysis"
            )
        except Exception as e:
            # Return a low-confidence error response instead of crashing
            return AgentResponse(
                agent_id=self.agent_type.value,
                task_id="stub_task_id",
                response_data={"error": str(e), "analysis": "Failed to process task"},
                confidence=0.1,
                reasoning=f"Error occurred during task execution: {e}"
            )


# Instantiate your core agents
cfo_agent = BaseAgent(AgentType.CFO)
cto_agent = BaseAgent(AgentType.CTO)
cmo_agent = BaseAgent(AgentType.CMO)
coo_agent = BaseAgent(AgentType.COO)

# A simple way to access them
agent_registry = {
    AgentType.CFO: cfo_agent,
    AgentType.CTO: cto_agent,
    AgentType.CMO: cmo_agent,
    AgentType.COO: coo_agent,
}
