# in src/orchestration/synthesizer.py
from src.state.store import state_store
from src.llm.ollama_client import generate_text
from src.models.dataModel import FinalPlan # You might need more models here
import json

def synthesize_plan(plan_id: str) -> FinalPlan:
    """
    Takes all completed agent responses for a plan and synthesizes them
    into a final, cohesive strategic plan.
    """
    print(f"Starting synthesis for plan_id: {plan_id}")
    
    # 1. Fetch all completed agent responses for the plan from the StateStore
    agent_responses = state_store.get_agent_responses_for_plan(plan_id) # You'll need to create this method in StateStore
    original_goal = state_store.get_plan(plan_id)['original_query']

    if not agent_responses:
        print("No agent responses to synthesize.")
        # Handle this case appropriately
        return None

    # 2. Construct the synthesis prompt for the CEO agent
    synthesis_prompt = f"You are Odyssey, the CEO. Your task is to synthesize the following analyses from your executive team into a single, cohesive strategic plan. The original goal was: '{original_goal}'.\n\n"
    
    for resp in agent_responses:
        synthesis_prompt += f"--- ANALYSIS FROM {resp['agent']} ---\n{resp['content']}\n\n"
        
    synthesis_prompt += (
        "---\n\n"
        "Synthesize these reports into a final plan. Provide an executive summary, identify cross-functional risks, and create a list of actionable recommendations. The output should be a JSON object with the following structure:\n"
        "{\n"
        "  \"plan_id\": \"<plan_id>\",\n"
        "  \"synthesized_strategy\": \"<executive summary and strategy>\",\n"
        "  \"contributing_agents\": [\"<list of agent names>\"],\n"
        "  \"identified_risks\": [\"<list of identified risks>\"],\n"
        "  \"confidence_score\": <0.0-1.0>\n"
        "}"
    )

    # 3. Call the LLM to generate the synthesized plan
    # NOTE: You may need to ask the LLM to produce a JSON output.
    # This can be tricky and might require a few attempts to get the prompt right.
    final_plan_json_str = generate_text(synthesis_prompt)
    
    # 4. Parse the JSON and create a FinalPlan object
    # You'll need robust error handling here in case the LLM output isn't valid JSON
    try:
        final_plan_data = json.loads(final_plan_json_str)
        # Ensure plan_id is set correctly
        final_plan_data['plan_id'] = plan_id
        final_plan = FinalPlan(**final_plan_data)
        return final_plan
    except Exception as e:
        print(f"Error parsing FinalPlan from LLM output: {e}")
        print(f"LLM output was: {final_plan_json_str}")
        return None
