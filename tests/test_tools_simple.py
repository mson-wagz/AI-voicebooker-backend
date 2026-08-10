"""
Simple tests for AI tools that don't depend on database.
"""

import pytest
from src.core.ai.tools import ToolParameter


class TestToolParameter:
    """Test ToolParameter model."""
    
    def test_tool_parameter_creation(self):
        """Test creating a tool parameter."""
        param = ToolParameter(
            name="test_param",
            type="string",
            description="A test parameter",
            required=True,
            example="test_value"
        )
        
        assert param.name == "test_param"
        assert param.type == "string"
        assert param.description == "A test parameter"
        assert param.required is True
        assert param.example == "test_value"
        
    def test_tool_parameter_optional(self):
        """Test creating an optional tool parameter."""
        param = ToolParameter(
            name="optional_param",
            type="integer",
            description="An optional parameter",
            required=False
        )
        
        assert param.required is False
        assert param.example is None
