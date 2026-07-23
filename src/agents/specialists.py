"""The four specialist agents used by the planning workflow."""
from __future__ import annotations

from ..llm.ollama_client import generate_text
from ..models.dataModel import AgentResponse, AgentType

_PERSONAS = {
    AgentType.COO: "Focus on sequencing, owners, dependencies, and measurable execution steps.",
    AgentType.CFO: "Focus on cost, assumptions, return, cash needs, and financial risks.",
    AgentType.CTO: "Focus on feasibility, architecture, delivery effort, and technical risks.",
    AgentType.CMO: "Focus on audience, positioning, channels, launch, and market risks.",
}


class BaseAgent:
    def __init__(self, agent_type: AgentType) -> None:
        self.agent_type = agent_type

    def execute(self, task_description: str) -> AgentResponse:
        prompt = (
            f"You are the {self.agent_type.value} Agent on an executive board. "
            f"{_PERSONAS[self.agent_type]}\n\nTask: {task_description}\n\n"
            "Return a concise analysis with findings, risks, and recommendations."
        )
        analysis = generate_text(prompt)
        if analysis is None:
            analysis = (
                f"## Findings\n{task_description}\n\n## Risks\n"
                "Validate assumptions with the responsible owner before commitment.\n\n"
                "## Recommendations\nDefine an accountable owner, milestone, budget, and review date."
            )
        return AgentResponse(
            agent_id=self.agent_type.value,
            task_id="",
            response_data={"analysis": analysis},
            confidence=0.75 if analysis else 0.5,
            reasoning=f"{self.agent_type.value} specialist analysis",
        )


agent_registry = {
    agent.value: BaseAgent(agent)
    for agent in (AgentType.COO, AgentType.CFO, AgentType.CTO, AgentType.CMO)
}
