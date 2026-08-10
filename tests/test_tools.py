"""
Tests for AI Tool Discovery System

Tests LLM tool discovery and execution capabilities.
"""

import pytest
from src.core.ai.tools import AVAILABLE_TOOLS, Tool
from src.core.ai.availability import AvailabilityRequest


class TestToolRegistry:
    """Test the tool registry itself."""
    
    def test_available_tools_not_empty(self):
        """Test that there are registered tools."""
        assert len(AVAILABLE_TOOLS) > 0
        
    def test_availability_tool_structure(self):
        """Test that availability tool has correct structure."""
        tool = next((t for t in AVAILABLE_TOOLS if t.name == "check_availability"), None)
        
        assert tool is not None
        assert tool.name == "check_availability"
        assert tool.category == "restaurant_operations"
        assert len(tool.parameters) == 3
        assert tool.method == "POST"
        assert "/v1/ai/check-availability" in tool.endpoint

    def test_tool_parameter_structure(self):
        """Test that tool parameters have correct structure."""
        for tool in AVAILABLE_TOOLS:
            assert isinstance(tool, Tool)
            assert tool.name
            assert tool.description
            assert tool.category
            assert tool.endpoint
            assert tool.method
            
            for param in tool.parameters:
                assert "name" in param.model_dump()
                assert "type" in param.model_dump()
                assert "description" in param.model_dump()
                assert "required" in param.model_dump()
                assert isinstance(param.required, bool)


class TestAvailabilityRequest:
    """Test availability request functionality."""
    
    def test_availability_request_creation(self):
        """Test creating an availability request."""
        request = AvailabilityRequest(
            restaurant_id="resto-123",
            booking_timestamp="2024-02-06T19:00:00Z",
            party_size=4
        )
        
        assert request.restaurant_id == "resto-123"
        assert request.booking_timestamp == "2024-02-06T19:00:00Z"
        assert request.party_size == 4
        
    def test_availability_request_validation(self):
        """Test availability request validation."""
        # Valid request
        request = AvailabilityRequest(
            restaurant_id="resto-123",
            booking_timestamp="2024-02-06T19:00:00Z",
            party_size=4
        )
        assert request.party_size > 0
        assert request.party_size <= 20
        
    def test_tool_parameter_examples(self):
        """Test that tool parameters have valid examples."""
        tool = next((t for t in AVAILABLE_TOOLS if t.name == "check_availability"), None)
        
        for param in tool.parameters:
            if param.example:
                assert param.example is not None
                # Check that example matches the parameter type
                if param.type == "string":
                    assert isinstance(param.example, str)
                elif param.type == "integer":
                    assert isinstance(param.example, int)
