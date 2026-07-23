"""Odyssey synthesis with a deterministic safe fallback."""
import json
from typing import List

from ..llm.ollama_client import generate_text
from ..models.dataModel import FinalPlan
from ..state.store import StateStore, state_store


def synthesize_plan(plan_id: str, store: StateStore = state_store) -> FinalPlan:
    plan = store.get_plan(plan_id)
    responses = store.get_agent_responses_for_plan(plan_id)
    if not plan or not responses:
        raise ValueError("cannot_synthesize_without_plan_and_responses")
    reports = "\n\n".join(f"[{response.agent_id}]\n{response.response_data.get('analysis', '')}" for response in responses)
    prompt = ("You are Odyssey, the CEO. Return JSON only with synthesized_strategy, "
              "contributing_agents, identified_risks, and confidence_score.\n"
              f"Goal: {plan['original_query']}\nReports:\n{reports}")
    raw = generate_text(prompt)
    try:
        data = json.loads(raw or "")
        data["plan_id"] = plan_id
        return FinalPlan.model_validate(data)
    except (json.JSONDecodeError, ValueError, TypeError):
        analyses = "\n\n".join(f"### {r.agent_id} Agent\n{r.response_data.get('analysis', '')}" for r in responses)
        return FinalPlan(plan_id=plan_id, synthesized_strategy=f"# Executive Plan\n\n## Findings\n\n{analyses}\n\n## Recommendations\n\nReview the specialist analyses, validate assumptions, and assign owners before execution.", contributing_agents=[r.agent_id for r in responses], identified_risks=["Model synthesis was unavailable; review the specialist analyses before acting."], confidence_score=min(r.confidence for r in responses))
