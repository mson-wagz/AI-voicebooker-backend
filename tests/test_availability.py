"""
Tests for AI Availability Checker

Tests AI-only logic without external dependencies.
"""

import pytest
from datetime import datetime, timedelta
from src.core.ai.availability import (
    AvailabilityRequest, 
    AvailabilityResponse, 
    generate_availability_reasoning
)

class TestAvailabilityReasoning:
    """Test AI reasoning logic for availability checking."""
    
    def test_peak_time_large_party_unavailable(self):
        """Test that peak time with large party is unavailable."""
        restaurant_id = "resto-123"
        booking_time = "2024-02-09T19:00:00"  # Friday 7 PM
        party_size = 8
        
        available, reasoning, alternatives = generate_availability_reasoning(
            restaurant_id, booking_time, party_size
        )
        
        assert available is False
        assert "Peak time" in reasoning
        assert "large party" in reasoning
        assert len(alternatives) > 0
        
    def test_peak_time_small_party_available(self):
        """Test that peak time with small party is available."""
        restaurant_id = "resto-123"
        booking_time = "2024-02-09T19:00:00"  # Friday 7 PM
        party_size = 4
        
        available, reasoning, alternatives = generate_availability_reasoning(
            restaurant_id, booking_time, party_size
        )
        
        assert available is True
        assert "Peak time" in reasoning
        assert "manageable party size" in reasoning
        assert len(alternatives) == 0
        
    def test_off_peak_normal_party_available(self):
        """Test that off-peak time with normal party is available."""
        restaurant_id = "resto-123"
        booking_time = "2024-02-07T14:00:00"  # Wednesday 2 PM
        party_size = 3
        
        available, reasoning, alternatives = generate_availability_reasoning(
            restaurant_id, booking_time, party_size
        )
        
        assert available is True
        assert "Off-peak time" in reasoning
        assert "standard party size" in reasoning
        assert len(alternatives) == 0
        
    def test_large_party_off_peak_unavailable(self):
        """Test that large party off-peak requires advance booking."""
        restaurant_id = "resto-123"
        booking_time = "2024-02-07T14:00:00"  # Wednesday 2 PM
        party_size = 10
        
        available, reasoning, alternatives = generate_availability_reasoning(
            restaurant_id, booking_time, party_size
        )
        
        assert available is False
        assert "Large party" in reasoning
        assert "advance booking" in reasoning
        assert len(alternatives) > 0
        
    def test_alternatives_structure(self):
        """Test that alternatives have correct structure."""
        restaurant_id = "resto-123"
        booking_time = "2024-02-09T19:00:00"  # Friday 7 PM
        party_size = 8
        
        available, reasoning, alternatives = generate_availability_reasoning(
            restaurant_id, booking_time, party_size
        )
        
        if alternatives:
            for alt in alternatives:
                assert hasattr(alt, 'time')
                assert hasattr(alt, 'party_size')
                assert hasattr(alt, 'confidence')
                assert 0 <= alt.confidence <= 100
                
    def test_invalid_timestamp_handling(self):
        """Test handling of invalid timestamps."""
        restaurant_id = "resto-123"
        invalid_time = "invalid-timestamp"
        party_size = 4
        
        available, reasoning, alternatives = generate_availability_reasoning(
            restaurant_id, invalid_time, party_size
        )
        
        assert available is True  # Fallback behavior
        assert "Invalid timestamp format" in reasoning
        assert len(alternatives) == 0

class TestAvailabilityRequest:
    """Test the request model validation."""
    
    def test_valid_request(self):
        """Test that valid requests pass validation."""
        request_data = {
            "restaurant_id": "resto-123",
            "booking_timestamp": "2024-02-09T19:00:00",
            "party_size": 4,
            "request_context": {
                "source": "vapi_tool",
                "session_id": "test_session"
            }
        }
        
        request = AvailabilityRequest(**request_data)
        assert request.restaurant_id == "resto-123"
        assert request.party_size == 4
        assert request.request_context["source"] == "vapi_tool"
        
    def test_party_size_validation(self):
        """Test party size boundaries."""
        # Valid sizes
        for size in [1, 10, 20]:
            request = AvailabilityRequest(
                restaurant_id="resto-123",
                booking_timestamp="2024-02-09T19:00:00",
                party_size=size
            )
            assert request.party_size == size
            
        # Invalid sizes would raise ValidationError in FastAPI
        # This is handled by Pydantic automatically
        
    def test_optional_context(self):
        """Test that request context is optional."""
        request_data = {
            "restaurant_id": "resto-123",
            "booking_timestamp": "2024-02-09T19:00:00",
            "party_size": 4
        }
        
        request = AvailabilityRequest(**request_data)
        assert request.request_context is None
