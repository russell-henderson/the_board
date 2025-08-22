"""
Agent specialists for the_board multi-agent system.

This module contains LLM-powered implementations of the core agents that
provide intelligent analysis and strategic insights using RAG workflows.
"""

from ..models.dataModel import AgentResponse, AgentType
from ..llm.ollama_client import generate_text
from ..knowledge.retriever import knowledge_retriever # Import the new retriever
from .tools import execute_tool, list_available_tools

# Define the personas for your agents with tool usage instructions
AGENT_SYSTEM_PROMPTS = {
    AgentType.CFO: """You are the Chief Financial Officer. Your response must be a concise, data-driven financial analysis.

AVAILABLE TOOLS:
- code_interpreter: Execute Python code for calculations (e.g., ROI, NPV, CAGR)
- financial_calculator: Perform financial calculations (ROI, NPV, CAGR, payback period)

When you need to perform calculations, use these tools. For example:
- For ROI calculations: Use financial_calculator with calculation_type="roi"
- For complex calculations: Use code_interpreter with Python code
- Always explain your calculations and reasoning""",
    
    AgentType.CTO: """You are the Chief Technology Officer. Your response must be a technical evaluation, focusing on feasibility, scalability, and security.

AVAILABLE TOOLS:
- code_interpreter: Execute Python code for technical calculations and analysis

When you need to perform technical calculations or analyze data, use the code_interpreter tool.
Always explain your technical reasoning and provide specific recommendations.""",
    
    AgentType.CMO: """You are the Chief Marketing Officer. Your response must focus on market positioning, customer acquisition, and brand strategy.

AVAILABLE TOOLS:
- code_interpreter: Execute Python code for market analysis and calculations

When you need to analyze market data or perform calculations, use the code_interpreter tool.
Always provide data-driven insights and actionable marketing recommendations.""",
    
    AgentType.COO: """You are the Chief Operations Officer. Your response must focus on operational efficiency, process optimization, and execution strategy.

AVAILABLE TOOLS:
- code_interpreter: Execute Python code for operational analysis and calculations

When you need to analyze operational data or perform calculations, use the code_interpreter tool.
Always provide practical, actionable operational recommendations.""",
}

class BaseAgent:
    """Base class for all agent specialists."""
    
    def __init__(self, agent_type: AgentType):
        self.agent_type = agent_type
        self.system_prompt = AGENT_SYSTEM_PROMPTS.get(agent_type, "You are a helpful assistant.")

    def execute(self, task_description: str) -> AgentResponse:
        """Performs a task using a Retrieval-Augmented Generation (RAG) workflow with tool support."""
        print(f"[{self.agent_type.value}] Executing RAG task with tools: {task_description}")
        
        # 1. RETRIEVE: Get relevant knowledge from ChromaDB
        relevant_context = knowledge_retriever.query(task_description)
        context_str = "\n".join([f"- {item}" for item in relevant_context])
        
        # 2. AUGMENT: Construct a detailed prompt with the retrieved context and tool instructions
        available_tools = list_available_tools()
        tools_info = "\n".join([
            f"- {tool['name']}: {tool['description']} (Params: {', '.join(tool['required_params'])})"
            for tool in available_tools
        ])
        
        if relevant_context:
            augmented_prompt = (
                f"{self.system_prompt}\n\n"
                f"TASK: {task_description}\n\n"
                f"Use the following relevant context from the knowledge base to inform your analysis:\n"
                f"CONTEXT:\n{context_str}\n\n"
                f"AVAILABLE TOOLS:\n{tools_info}\n\n"
                f"INSTRUCTIONS: If you need to perform calculations or analysis, use the appropriate tools. "
                f"Explain your reasoning and provide actionable insights.\n\n"
                f"ANALYSIS:"
            )
        else:
            # Fallback to non-RAG prompt if no context is found
            augmented_prompt = (
                f"{self.system_prompt}\n\n"
                f"TASK: {task_description}\n\n"
                f"AVAILABLE TOOLS:\n{tools_info}\n\n"
                f"INSTRUCTIONS: If you need to perform calculations or analysis, use the appropriate tools. "
                f"Explain your reasoning and provide actionable insights.\n\n"
                f"ANALYSIS:"
            )
        
        # 3. GENERATE: Call the LLM with the augmented prompt
        llm_output = generate_text(augmented_prompt)
        
        # 4. TOOL EXECUTION: Check if the LLM output contains tool requests
        tool_results = self._extract_and_execute_tools(llm_output)
        
        # 5. FINAL ANALYSIS: If tools were used, generate a final response incorporating results
        if tool_results:
            final_prompt = (
                f"{self.system_prompt}\n\n"
                f"TASK: {task_description}\n\n"
                f"TOOL RESULTS:\n{tool_results}\n\n"
                f"Based on these tool results, provide your final analysis and recommendations:"
            )
            final_output = generate_text(final_prompt)
        else:
            final_output = llm_output
        
        return AgentResponse(
            agent_id=self.agent_type.value,
            task_id="llm_task_id",  # Will be replaced with actual task ID
            response_data={
                "analysis": final_output, 
                "agent_type": self.agent_type.value,
                "tools_used": bool(tool_results),
                "tool_results": tool_results
            },
            confidence=0.90,  # Higher confidence as it's grounded in facts and tools
            reasoning=f"LLM-generated analysis from {self.agent_type.value} agent using RAG workflow and tools"
        )
    
    def _extract_and_execute_tools(self, llm_output: str) -> str:
        """Extract tool requests from LLM output and execute them."""
        tool_results = []
        
        # Simple pattern matching for tool requests (can be enhanced with more sophisticated parsing)
        import re
        
        # Look for tool usage patterns
        tool_patterns = [
            r'TOOL:\s*(\w+)\s*PARAMS:\s*({[^}]+})',
            r'Use tool (\w+) with params ({[^}]+})',
            r'Execute (\w+) tool: ({[^}]+})',
        ]
        
        for pattern in tool_patterns:
            matches = re.findall(pattern, llm_output, re.IGNORECASE)
            for tool_name, params_str in matches:
                try:
                    # Parse parameters (simple JSON-like parsing)
                    params = self._parse_tool_params(params_str)
                    if params:
                        result = execute_tool(tool_name, params)
                        if result.success:
                            tool_results.append(f"✅ {tool_name} executed successfully: {result.result}")
                        else:
                            tool_results.append(f"❌ {tool_name} failed: {result.error}")
                except Exception as e:
                    tool_results.append(f"❌ Error executing {tool_name}: {str(e)}")
        
        if tool_results:
            return "\n".join(tool_results)
        return ""
    
    def _parse_tool_params(self, params_str: str) -> dict:
        """Parse tool parameters from string representation."""
        try:
            # Simple parameter parsing - can be enhanced
            params = {}
            # Remove braces and split by commas
            clean_str = params_str.strip('{}')
            pairs = clean_str.split(',')
            
            for pair in pairs:
                if ':' in pair:
                    key, value = pair.split(':', 1)
                    key = key.strip().strip('"\'')
                    value = value.strip().strip('"\'')
                    
                    # Try to convert to appropriate type
                    try:
                        if value.lower() in ['true', 'false']:
                            params[key] = value.lower() == 'true'
                        elif '.' in value and value.replace('.', '').replace('-', '').isdigit():
                            params[key] = float(value)
                        elif value.replace('-', '').isdigit():
                            params[key] = int(value)
                        else:
                            params[key] = value
                    except:
                        params[key] = value
            
            return params
        except Exception as e:
            print(f"Error parsing tool parameters: {e}")
            return {}


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
