#!/usr/bin/env python3
"""
Tests for the agent tools.

This module tests all tool functionality including:
- Code interpreter tool
- Financial calculator tool
- Tool registry and execution
- Safety features
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.agents.tools import (
    BaseTool, CodeInterpreterTool, FinancialCalculatorTool,
    ToolResult, TOOL_REGISTRY, get_tool, list_available_tools, execute_tool
)

class TestBaseTool:
    """Test suite for BaseTool functionality."""
    
    def test_base_tool_creation(self):
        """Test basic tool creation."""
        tool = BaseTool(
            name="test_tool",
            description="A test tool",
            required_params=["param1", "param2"]
        )
        
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool.required_params == ["param1", "param2"]
    
    def test_can_execute(self):
        """Test can_execute method."""
        tool = BaseTool(
            name="test_tool",
            description="A test tool",
            required_params=["param1", "param2"]
        )
        
        # Should work with all required params
        assert tool.can_execute({"param1": "value1", "param2": "value2"}) is True
        
        # Should fail with missing params
        assert tool.can_execute({"param1": "value1"}) is False
        assert tool.can_execute({}) is False
    
    def test_get_usage_example(self):
        """Test usage example generation."""
        tool = BaseTool(
            name="test_tool",
            description="A test tool",
            required_params=["param1", "param2"]
        )
        
        example = tool.get_usage_example()
        assert "test_tool" in example
        assert "param1" in example
        assert "param2" in example

class TestCodeInterpreterTool:
    """Test suite for CodeInterpreterTool functionality."""
    
    @pytest.fixture
    def tool(self):
        """Create a CodeInterpreterTool instance."""
        return CodeInterpreterTool()
    
    def test_tool_creation(self, tool):
        """Test tool creation and properties."""
        assert tool.name == "code_interpreter"
        assert "Execute Python code" in tool.description
        assert tool.required_params == ["code"]
    
    def test_simple_calculations(self, tool):
        """Test simple mathematical calculations."""
        # Basic arithmetic
        result = tool.execute({"code": "2 + 3"})
        assert result.success is True
        assert result.result == 5
        
        # Multiplication
        result = tool.execute({"code": "4 * 5"})
        assert result.success is True
        assert result.result == 20
        
        # Division
        result = tool.execute({"code": "10 / 2"})
        assert result.success is True
        assert result.result == 5.0
    
    def test_math_functions(self, tool):
        """Test mathematical functions."""
        # Square root
        result = tool.execute({"code": "sqrt(16)"})
        assert result.success is True
        assert result.result == 4.0
        
        # Power
        result = tool.execute({"code": "pow(2, 3)"})
        assert result.success is True
        assert result.result == 8.0
        
        # Constants
        result = tool.execute({"code": "pi"})
        assert result.success is True
        assert abs(result.result - 3.14159) < 0.01
    
    def test_variable_assignment(self, tool):
        """Test variable assignment and retrieval."""
        result = tool.execute({"code": "x = 42; x"})
        assert result.success is True
        assert result.result == 42
        
        result = tool.execute({"code": "y = 10; z = 20; y + z"})
        assert result.success is True
        assert result.result == 30
    
    def test_list_operations(self, tool):
        """Test list operations."""
        result = tool.execute({"code": "[1, 2, 3, 4, 5]"})
        assert result.success is True
        assert result.result == [1, 2, 3, 4, 5]
        
        result = tool.execute({"code": "sum([1, 2, 3, 4, 5])"})
        assert result.success is True
        assert result.result == 15
        
        result = tool.execute({"code": "len([1, 2, 3])"})
        assert result.success is True
        assert result.result == 3
    
    def test_safety_features(self, tool):
        """Test safety features block dangerous operations."""
        dangerous_operations = [
            "import os",
            "from os import path",
            "exec('print(1)')",
            "eval('1+1')",
            "open('file.txt')",
            "__import__('os')",
            "globals()",
            "locals()",
            "input('Enter:')",
        ]
        
        for dangerous_code in dangerous_operations:
            result = tool.execute({"code": dangerous_code})
            assert result.success is False
            assert "unsafe operations" in result.error
    
    def test_error_handling(self, tool):
        """Test error handling for invalid code."""
        # Syntax error
        result = tool.execute({"code": "print("})
        assert result.success is False
        assert "Execution error" in result.error
        
        # Runtime error
        result = tool.execute({"code": "1 / 0"})
        assert result.success is False
        assert "Execution error" in result.error
    
    def test_empty_code(self, tool):
        """Test handling of empty code."""
        result = tool.execute({"code": ""})
        assert result.success is False
        assert "No code provided" in result.error
        
        result = tool.execute({"code": "   "})
        assert result.success is False
        assert "No code provided" in result.error

class TestFinancialCalculatorTool:
    """Test suite for FinancialCalculatorTool functionality."""
    
    @pytest.fixture
    def tool(self):
        """Create a FinancialCalculatorTool instance."""
        return FinancialCalculatorTool()
    
    def test_tool_creation(self, tool):
        """Test tool creation and properties."""
        assert tool.name == "financial_calculator"
        assert "financial calculations" in tool.description
        assert tool.required_params == ["calculation_type", "parameters"]
    
    def test_roi_calculation(self, tool):
        """Test ROI calculation."""
        params = {
            "calculation_type": "roi",
            "parameters": {
                "initial_investment": 1000,
                "final_value": 1500
            }
        }
        
        result = tool.execute(params)
        assert result.success is True
        assert result.result["roi_percentage"] == 50.0
        assert result.result["roi_decimal"] == 0.5
        assert result.result["profit"] == 500
        assert result.result["initial_investment"] == 1000
        assert result.result["final_value"] == 1500
    
    def test_npv_calculation(self, tool):
        """Test NPV calculation."""
        params = {
            "calculation_type": "npv",
            "parameters": {
                "discount_rate": 10,
                "cash_flows": [-1000, 300, 400, 500]
            }
        }
        
        result = tool.execute(params)
        assert result.success is True
        assert "npv" in result.result
        assert result.result["discount_rate_percentage"] == 10.0
        assert result.result["cash_flows"] == [-1000, 300, 400, 500]
        assert result.result["periods"] == 4
    
    def test_cagr_calculation(self, tool):
        """Test CAGR calculation."""
        params = {
            "calculation_type": "cagr",
            "parameters": {
                "initial_value": 1000,
                "final_value": 2000,
                "years": 5
            }
        }
        
        result = tool.execute(params)
        assert result.success is True
        assert "cagr_percentage" in result.result
        assert result.result["initial_value"] == 1000
        assert result.result["final_value"] == 2000
        assert result.result["years"] == 5
    
    def test_payback_period_calculation(self, tool):
        """Test payback period calculation."""
        params = {
            "calculation_type": "payback_period",
            "parameters": {
                "initial_investment": 10000,
                "annual_cash_flow": 2000
            }
        }
        
        result = tool.execute(params)
        assert result.success is True
        assert result.result["payback_period_years"] == 5.0
        assert result.result["initial_investment"] == 10000
        assert result.result["annual_cash_flow"] == 2000
    
    def test_invalid_calculation_type(self, tool):
        """Test handling of invalid calculation type."""
        params = {
            "calculation_type": "invalid_type",
            "parameters": {}
        }
        
        result = tool.execute(params)
        assert result.success is False
        assert "Unknown calculation type" in result.error
    
    def test_missing_parameters(self, tool):
        """Test handling of missing parameters."""
        params = {
            "calculation_type": "roi",
            "parameters": {}
        }
        
        result = tool.execute(params)
        assert result.success is False
        assert "calculation error" in result.error.lower()
    
    def test_invalid_parameters(self, tool):
        """Test handling of invalid parameters."""
        # ROI with zero initial investment
        params = {
            "calculation_type": "roi",
            "parameters": {
                "initial_investment": 0,
                "final_value": 1000
            }
        }
        
        result = tool.execute(params)
        assert result.success is False
        assert "calculation error" in result.error.lower()

class TestToolRegistry:
    """Test suite for tool registry functionality."""
    
    def test_tool_registry_contents(self):
        """Test that all expected tools are in the registry."""
        expected_tools = ["code_interpreter", "financial_calculator"]
        
        for tool_name in expected_tools:
            assert tool_name in TOOL_REGISTRY
            assert isinstance(TOOL_REGISTRY[tool_name], BaseTool)
    
    def test_get_tool(self):
        """Test getting tools by name."""
        # Test existing tools
        tool = get_tool("code_interpreter")
        assert tool is not None
        assert tool.name == "code_interpreter"
        
        tool = get_tool("financial_calculator")
        assert tool is not None
        assert tool.name == "financial_calculator"
        
        # Test non-existent tool
        tool = get_tool("nonexistent_tool")
        assert tool is None
    
    def test_list_available_tools(self):
        """Test listing available tools."""
        tools = list_available_tools()
        
        assert isinstance(tools, list)
        assert len(tools) >= 2
        
        for tool_info in tools:
            assert "name" in tool_info
            assert "description" in tool_info
            assert "required_params" in tool_info
            assert "usage_example" in tool_info
    
    def test_execute_tool(self):
        """Test tool execution through the registry."""
        # Test successful execution
        result = execute_tool("code_interpreter", {"code": "2 + 2"})
        assert result.success is True
        assert result.result == 4
        
        # Test tool not found
        result = execute_tool("nonexistent_tool", {})
        assert result.success is False
        assert "not found" in result.error
        
        # Test missing parameters
        result = execute_tool("code_interpreter", {})
        assert result.success is False
        assert "requires parameters" in result.error

class TestToolResult:
    """Test suite for ToolResult dataclass."""
    
    def test_tool_result_creation(self):
        """Test ToolResult creation."""
        result = ToolResult(
            success=True,
            result="test result",
            error=None,
            metadata={"key": "value"}
        )
        
        assert result.success is True
        assert result.result == "test result"
        assert result.error is None
        assert result.metadata == {"key": "value"}
    
    def test_tool_result_defaults(self):
        """Test ToolResult with default values."""
        result = ToolResult(
            success=False,
            result=None,
            error="test error"
        )
        
        assert result.success is False
        assert result.result is None
        assert result.error == "test error"
        assert result.metadata is None

if __name__ == "__main__":
    pytest.main([__file__])
