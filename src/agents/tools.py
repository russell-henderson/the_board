#!/usr/bin/env python3
"""
Agent Tools for the_board

This module provides tools that agents can use to enhance their capabilities,
particularly for tasks requiring calculations, data analysis, or external interactions.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
import ast
import operator
import math

logger = logging.getLogger("the_board.agents.tools")

@dataclass
class ToolResult:
    """Result from a tool execution."""
    success: bool
    result: Any
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class BaseTool:
    """Base class for all agent tools."""
    
    def __init__(self, name: str, description: str, required_params: List[str]):
        self.name = name
        self.description = description
        self.required_params = required_params
    
    def can_execute(self, params: Dict[str, Any]) -> bool:
        """Check if the tool can execute with the given parameters."""
        return all(param in params for param in self.required_params)
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """Execute the tool with the given parameters."""
        raise NotImplementedError("Subclasses must implement execute method")
    
    def get_usage_example(self) -> str:
        """Get a usage example for the tool."""
        param_examples = ", ".join([f'"{param}": "value"' for param in self.required_params])
        return f'{{"tool": "{self.name}", "params": {{{param_examples}}}}}'

class CodeInterpreterTool(BaseTool):
    """Tool that allows agents to execute simple Python code for calculations."""
    
    def __init__(self):
        super().__init__(
            name="code_interpreter",
            description="Execute simple Python code for calculations and data analysis",
            required_params=["code"]
        )
        
        # Safe operations and functions
        self.safe_operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }
        
        self.safe_functions = {
            'abs': abs,
            'round': round,
            'min': min,
            'max': max,
            'sum': sum,
            'len': len,
            'int': int,
            'float': float,
            'str': str,
            'list': list,
            'dict': dict,
            'tuple': tuple,
            'set': set,
            'sorted': sorted,
            'reversed': reversed,
            'enumerate': enumerate,
            'zip': zip,
            'range': range,
            'math.sqrt': math.sqrt,
            'math.pow': math.pow,
            'math.exp': math.exp,
            'math.log': math.log,
            'math.log10': math.log10,
            'math.sin': math.sin,
            'math.cos': math.cos,
            'math.tan': math.tan,
            'math.pi': math.pi,
            'math.e': math.e,
        }
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """Execute Python code safely."""
        code = params.get("code", "").strip()
        
        if not code:
            return ToolResult(
                success=False,
                result=None,
                error="No code provided"
            )
        
        try:
            # Validate code safety
            if not self._is_safe_code(code):
                return ToolResult(
                    success=False,
                    result=None,
                    error="Code contains unsafe operations"
                )
            
            # Execute the code
            result = self._execute_safe_code(code)
            
            return ToolResult(
                success=True,
                result=result,
                metadata={
                    "code_executed": code,
                    "result_type": type(result).__name__
                }
            )
            
        except Exception as e:
            logger.warning(f"Code interpreter error: {e}")
            return ToolResult(
                success=False,
                result=None,
                error=f"Execution error: {str(e)}"
            )
    
    def _is_safe_code(self, code: str) -> bool:
        """Check if the code is safe to execute."""
        # Block potentially dangerous operations
        dangerous_patterns = [
            r'import\s+',
            r'from\s+',
            r'exec\s*\(',
            r'eval\s*\(',
            r'open\s*\(',
            r'file\s*\(',
            r'__\w+__',
            r'globals\s*\(',
            r'locals\s*\(',
            r'vars\s*\(',
            r'dir\s*\(',
            r'getattr\s*\(',
            r'setattr\s*\(',
            r'delattr\s*\(',
            r'hasattr\s*\(',
            r'input\s*\(',
            r'raw_input\s*\(',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                return False
        
        return True
    
    def _execute_safe_code(self, code: str) -> Any:
        """Execute safe Python code."""
        # Create a safe namespace
        safe_namespace = {
            '__builtins__': {
                'abs': abs,
                'round': round,
                'min': min,
                'max': max,
                'sum': sum,
                'len': len,
                'int': int,
                'float': float,
                'str': str,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'set': set,
                'sorted': sorted,
                'reversed': reversed,
                'enumerate': enumerate,
                'zip': zip,
                'range': range,
                'True': True,
                'False': False,
                'None': None,
            }
        }
        
        # Add math functions
        safe_namespace.update({
            'sqrt': math.sqrt,
            'pow': math.pow,
            'exp': math.exp,
            'log': math.log,
            'log10': math.log10,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'pi': math.pi,
            'e': math.e,
        })
        
        # Execute the code
        exec(code, safe_namespace)
        
        # Return the result (last expression or None)
        if code.strip().endswith(';'):
            # If code ends with semicolon, look for result variable
            lines = code.strip().split('\n')
            for line in reversed(lines):
                if '=' in line and not line.strip().startswith('#'):
                    var_name = line.split('=')[0].strip()
                    if var_name in safe_namespace:
                        return safe_namespace[var_name]
            return None
        else:
            # Try to evaluate the last expression
            try:
                # Parse the last line as an expression
                lines = [line.strip() for line in code.split('\n') if line.strip() and not line.strip().startswith('#')]
                if lines:
                    last_line = lines[-1]
                    # Remove trailing semicolon if present
                    if last_line.endswith(';'):
                        last_line = last_line[:-1]
                    
                    # Try to evaluate the last line
                    result = eval(last_line, safe_namespace)
                    return result
            except:
                pass
            
            return None

class FinancialCalculatorTool(BaseTool):
    """Tool for financial calculations commonly needed by CFO agents."""
    
    def __init__(self):
        super().__init__(
            name="financial_calculator",
            description="Perform financial calculations like ROI, NPV, CAGR, etc.",
            required_params=["calculation_type", "parameters"]
        )
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """Execute financial calculations."""
        calc_type = params.get("calculation_type", "").lower()
        calc_params = params.get("parameters", {})
        
        try:
            if calc_type == "roi":
                result = self._calculate_roi(calc_params)
            elif calc_type == "npv":
                result = self._calculate_npv(calc_params)
            elif calc_type == "cagr":
                result = self._calculate_cagr(calc_params)
            elif calc_type == "payback_period":
                result = self._calculate_payback_period(calc_params)
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Unknown calculation type: {calc_type}"
                )
            
            return ToolResult(
                success=True,
                result=result,
                metadata={
                    "calculation_type": calc_type,
                    "parameters": calc_params
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Calculation error: {str(e)}"
            )
    
    def _calculate_roi(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate Return on Investment."""
        initial_investment = float(params.get("initial_investment", 0))
        final_value = float(params.get("final_value", 0))
        
        if initial_investment == 0:
            raise ValueError("Initial investment cannot be zero")
        
        roi = ((final_value - initial_investment) / initial_investment) * 100
        
        return {
            "roi_percentage": round(roi, 2),
            "roi_decimal": round(roi / 100, 4),
            "profit": round(final_value - initial_investment, 2),
            "initial_investment": initial_investment,
            "final_value": final_value
        }
    
    def _calculate_npv(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate Net Present Value."""
        discount_rate = float(params.get("discount_rate", 0)) / 100
        cash_flows = params.get("cash_flows", [])
        
        if not cash_flows:
            raise ValueError("Cash flows list cannot be empty")
        
        npv = 0
        for i, cf in enumerate(cash_flows):
            npv += cf / ((1 + discount_rate) ** i)
        
        return {
            "npv": round(npv, 2),
            "discount_rate_percentage": round(discount_rate * 100, 2),
            "cash_flows": cash_flows,
            "periods": len(cash_flows)
        }
    
    def _calculate_cagr(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate Compound Annual Growth Rate."""
        initial_value = float(params.get("initial_value", 0))
        final_value = float(params.get("final_value", 0))
        years = float(params.get("years", 0))
        
        if initial_value <= 0 or years <= 0:
            raise ValueError("Initial value and years must be positive")
        
        cagr = ((final_value / initial_value) ** (1 / years) - 1) * 100
        
        return {
            "cagr_percentage": round(cagr, 2),
            "cagr_decimal": round(cagr / 100, 4),
            "initial_value": initial_value,
            "final_value": final_value,
            "years": years
        }
    
    def _calculate_payback_period(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate Payback Period."""
        initial_investment = float(params.get("initial_investment", 0))
        annual_cash_flow = float(params.get("annual_cash_flow", 0))
        
        if annual_cash_flow <= 0:
            raise ValueError("Annual cash flow must be positive")
        
        payback_period = initial_investment / annual_cash_flow
        
        return {
            "payback_period_years": round(payback_period, 2),
            "initial_investment": initial_investment,
            "annual_cash_flow": annual_cash_flow
        }

# Tool registry
TOOL_REGISTRY = {
    "code_interpreter": CodeInterpreterTool(),
    "financial_calculator": FinancialCalculatorTool(),
}

def get_tool(tool_name: str) -> Optional[BaseTool]:
    """Get a tool by name."""
    return TOOL_REGISTRY.get(tool_name)

def list_available_tools() -> List[Dict[str, Any]]:
    """List all available tools with their descriptions."""
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "required_params": tool.required_params,
            "usage_example": tool.get_usage_example()
        }
        for tool in TOOL_REGISTRY.values()
    ]

def execute_tool(tool_name: str, params: Dict[str, Any]) -> ToolResult:
    """Execute a tool by name with the given parameters."""
    tool = get_tool(tool_name)
    if not tool:
        return ToolResult(
            success=False,
            result=None,
            error=f"Tool '{tool_name}' not found"
        )
    
    if not tool.can_execute(params):
        return ToolResult(
            success=False,
            result=None,
            error=f"Tool '{tool_name}' requires parameters: {tool.required_params}"
        )
    
    return tool.execute(params)
