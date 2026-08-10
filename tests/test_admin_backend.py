"""
Comprehensive tests for Admin Backend API
Tests dashboard stats, policy management, call logs, and booking logs
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date, timedelta
import json
import uuid

# Import models and app
from src.main import app
from src.core.database.models import Base, Restaurant, Policy, OpeningHour, DepositRule, CallRecord, Booking, BookingStatus
from src.core.database.connection import get_db_session

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_admin.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override database dependency for testing
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db_session] = override_get_db

# Create test client
client = TestClient(app)

# Setup test database
@pytest.fixture(scope="module")
def setup_test_db():
    """Create test database tables and sample data"""
    Base.metadata.create_all(bind=engine)
    
    # Create sample restaurant
    db = TestingSessionLocal()
    
    restaurant = Restaurant(
        id="test-restaurant-1",
        name="Test Restaurant",
        phone_number="+1234567890",
        timezone="UTC"
    )
    db.add(restaurant)
    
    # Create sample policy
    policy = Policy(
        id="test-policy-1",
        restaurant_id="test-restaurant-1",
        deposit_required=True,
        deposit_amount=500,  # $5.00 in cents
        max_party_size=12
    )
    db.add(policy)
    
    # Create opening hours
    for day in range(7):  # 0-6 (Sunday-Saturday)
        opening_hour = OpeningHour(
            policy_id="test-policy-1",
            day_of_week=day,
            open_time="09:00",
            close_time="22:00",
            is_closed=(day == 0)  # Closed on Sunday
        )
        db.add(opening_hour)
    
    # Create deposit rules
    deposit_rule = DepositRule(
        policy_id="test-policy-1",
        day_of_week=5,  # Friday
        min_party=6,
        start_time="18:00",
        end_time="22:00"
    )
    db.add(deposit_rule)
    
    # Create sample call records
    for i in range(15):
        call_record = CallRecord(
            id=f"call-{i}",
            restaurant_id="test-restaurant-1",
            customer_phone=f"+123456789{i}",
            call_id=f"vapi-call-{i}",
            status="completed" if i % 3 != 0 else "failed",
            duration=120 + i * 10,
            transcript=f"Sample transcript {i}: Customer wants to make a reservation...",
            booking_id=f"booking-{i}" if i % 3 != 0 else None,
            created_at=datetime.utcnow() - timedelta(hours=i)
        )
        db.add(call_record)
    
    # Create sample bookings
    statuses = [BookingStatus.CONFIRMED, BookingStatus.FAILED, BookingStatus.CANCELLED, BookingStatus.PENDING]
    for i in range(12):
        booking = Booking(
            id=f"booking-{i}",
            restaurant_id="test-restaurant-1",
            customer_name=f"Customer {i}",
            customer_phone=f"+123456789{i}",
            party_size=2 + i % 4,
            booking_time=datetime.utcnow() + timedelta(days=i % 7, hours=19),
            status=statuses[i % len(statuses)],
            call_confidence=0.8 + (i % 3) * 0.1,
            created_at=datetime.utcnow() - timedelta(hours=i)
        )
        db.add(booking)
    
    db.commit()
    db.close()
    
    yield
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)

class TestDashboardStats:
    """Test dashboard statistics endpoints"""
    
    def test_get_dashboard_stats_success(self, setup_test_db):
        """Test successful dashboard stats retrieval"""
        response = client.get("/admin/dashboard/stats/test-restaurant-1")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "total_calls" in data
        assert "successful_bookings" in data
        assert "failed_bookings" in data
        assert "total_calls_today" in data
        assert "total_bookings_today" in data
        assert "success_rate" in data
        assert "recent_calls" in data
        assert "recent_bookings" in data
        
        # Verify data types
        assert isinstance(data["total_calls"], int)
        assert isinstance(data["successful_bookings"], int)
        assert isinstance(data["failed_bookings"], int)
        assert isinstance(data["success_rate"], float)
        assert isinstance(data["recent_calls"], list)
        assert isinstance(data["recent_bookings"], list)
        
        # Verify expected values
        assert data["total_calls"] == 15
        assert data["successful_bookings"] >= 0
        assert data["failed_bookings"] >= 0
        assert len(data["recent_calls"]) <= 10
        assert len(data["recent_bookings"]) <= 10
        
        # Verify recent call structure
        if data["recent_calls"]:
            call = data["recent_calls"][0]
            assert "id" in call
            assert "customer_phone" in call
            assert "status" in call
            assert "duration" in call
            assert "created_at" in call
            assert "transcript" in call
        
        # Verify recent booking structure
        if data["recent_bookings"]:
            booking = data["recent_bookings"][0]
            assert "id" in booking
            assert "customer_name" in booking
            assert "customer_phone" in booking
            assert "party_size" in booking
            assert "booking_time" in booking
            assert "status" in booking
            assert "created_at" in booking
    
    def test_get_dashboard_stats_restaurant_not_found(self, setup_test_db):
        """Test dashboard stats with non-existent restaurant"""
        response = client.get("/admin/dashboard/stats/non-existent")
        
        assert response.status_code == 404
        assert "Restaurant not found" in response.json()["detail"]

class TestPolicyManagement:
    """Test policy management endpoints"""
    
    def test_get_policy_success(self, setup_test_db):
        """Test successful policy retrieval"""
        response = client.get("/admin/policies/test-restaurant-1")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "id" in data
        assert "restaurant_id" in data
        assert "deposit_required" in data
        assert "deposit_amount" in data
        assert "max_party_size" in data
        assert "opening_hours" in data
        assert "deposit_rules" in data
        
        # Verify values
        assert data["restaurant_id"] == "test-restaurant-1"
        assert data["deposit_required"] == True
        assert data["deposit_amount"] == 500
        assert data["max_party_size"] == 12
        assert len(data["opening_hours"]) == 7  # One for each day
        assert len(data["deposit_rules"]) == 1
        
        # Verify opening hours structure
        for oh in data["opening_hours"]:
            assert "day_of_week" in oh
            assert "open_time" in oh
            assert "close_time" in oh
            assert "is_closed" in oh
        
        # Verify deposit rules structure
        for dr in data["deposit_rules"]:
            assert "day_of_week" in dr
            assert "min_party" in dr
            assert "start_time" in dr
            assert "end_time" in dr
    
    def test_create_policy_success(self, setup_test_db):
        """Test successful policy creation"""
        policy_data = {
            "deposit_required": True,
            "deposit_amount": 1000,
            "max_party_size": 15,
            "opening_hours": [
                {
                    "day_of_week": 0,
                    "open_time": "10:00",
                    "close_time": "23:00",
                    "is_closed": True
                },
                {
                    "day_of_week": 1,
                    "open_time": "10:00",
                    "close_time": "23:00",
                    "is_closed": False
                }
            ],
            "deposit_rules": [
                {
                    "day_of_week": 6,
                    "min_party": 8,
                    "start_time": "18:00",
                    "end_time": "22:00"
                }
            ]
        }
        
        response = client.post("/admin/policies/test-restaurant-1", json=policy_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify created policy
        assert data["restaurant_id"] == "test-restaurant-1"
        assert data["deposit_required"] == True
        assert data["deposit_amount"] == 1000
        assert data["max_party_size"] == 15
        assert len(data["opening_hours"]) == 2
        assert len(data["deposit_rules"]) == 1
    
    def test_update_policy_success(self, setup_test_db):
        """Test successful policy update"""
        update_data = {
            "deposit_required": False,
            "max_party_size": 20
        }
        
        response = client.put("/admin/policies/test-restaurant-1", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify updated fields
        assert data["deposit_required"] == False
        assert data["max_party_size"] == 20
        # Original fields should remain
        assert data["deposit_amount"] == 500  # Unchanged
    
    def test_policy_restaurant_not_found(self, setup_test_db):
        """Test policy operations with non-existent restaurant"""
        response = client.get("/admin/policies/non-existent")
        
        assert response.status_code == 404
        assert "Restaurant not found" in response.json()["detail"]

class TestCallLogs:
    """Test call logs endpoints"""
    
    def test_get_call_logs_success(self, setup_test_db):
        """Test successful call logs retrieval"""
        response = client.get("/admin/calls/test-restaurant-1")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "calls" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        
        # Verify values
        assert isinstance(data["calls"], list)
        assert isinstance(data["total"], int)
        assert data["total"] == 15
        assert len(data["calls"]) <= 50  # Default limit
        
        # Verify call structure
        if data["calls"]:
            call = data["calls"][0]
            assert "id" in call
            assert "call_id" in call
            assert "customer_phone" in call
            assert "status" in call
            assert "duration" in call
            assert "transcript" in call
            assert "audio_url" in call
            assert "booking_id" in call
            assert "created_at" in call
            assert "updated_at" in call
    
    def test_get_call_logs_with_pagination(self, setup_test_db):
        """Test call logs with pagination"""
        response = client.get("/admin/calls/test-restaurant-1?limit=5&offset=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["limit"] == 5
        assert data["offset"] == 10
        assert len(data["calls"]) <= 5
    
    def test_get_call_logs_restaurant_not_found(self, setup_test_db):
        """Test call logs with non-existent restaurant"""
        response = client.get("/admin/calls/non-existent")
        
        assert response.status_code == 404
        assert "Restaurant not found" in response.json()["detail"]

class TestBookingLogs:
    """Test booking logs endpoints"""
    
    def test_get_booking_logs_success(self, setup_test_db):
        """Test successful booking logs retrieval"""
        response = client.get("/admin/bookings/test-restaurant-1")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "bookings" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "status_filter" in data
        
        # Verify values
        assert isinstance(data["bookings"], list)
        assert isinstance(data["total"], int)
        assert data["total"] == 12
        assert len(data["bookings"]) <= 50  # Default limit
        
        # Verify booking structure
        if data["bookings"]:
            booking = data["bookings"][0]
            assert "id" in booking
            assert "customer_name" in booking
            assert "customer_phone" in booking
            assert "party_size" in booking
            assert "booking_time" in booking
            assert "status" in booking
            assert "stripe_payment_id" in booking
            assert "external_ref_id" in booking
            assert "call_confidence" in booking
            assert "created_at" in booking
    
    def test_get_booking_logs_with_status_filter(self, setup_test_db):
        """Test booking logs with status filter"""
        response = client.get("/admin/bookings/test-restaurant-1?status=CONFIRMED")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status_filter"] == "CONFIRMED"
        
        # Verify all bookings have the requested status
        for booking in data["bookings"]:
            assert booking["status"] == "CONFIRMED"
    
    def test_get_booking_logs_with_pagination(self, setup_test_db):
        """Test booking logs with pagination"""
        response = client.get("/admin/bookings/test-restaurant-1?limit=3&offset=5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["limit"] == 3
        assert data["offset"] == 5
        assert len(data["bookings"]) <= 3
    
    def test_get_booking_logs_restaurant_not_found(self, setup_test_db):
        """Test booking logs with non-existent restaurant"""
        response = client.get("/admin/bookings/non-existent")
        
        assert response.status_code == 404
        assert "Restaurant not found" in response.json()["detail"]

class TestAdminHealth:
    """Test admin health check"""
    
    def test_admin_health_check(self, setup_test_db):
        """Test admin service health check"""
        response = client.get("/admin/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "admin"
        assert "version" in data
        assert "features" in data
        assert isinstance(data["features"], list)

# Performance and load testing
class TestPerformance:
    """Performance and edge case tests"""
    
    def test_large_dataset_performance(self, setup_test_db):
        """Test performance with larger dataset"""
        # Create additional test data
        db = TestingSessionLocal()
        
        # Add 100 more calls
        for i in range(100):
            call_record = CallRecord(
                id=f"perf-call-{i}",
                restaurant_id="test-restaurant-1",
                customer_phone=f"+12345678{i:03d}",
                call_id=f"vapi-perf-{i}",
                status="completed",
                duration=120,
                transcript=f"Performance test transcript {i}",
                created_at=datetime.utcnow() - timedelta(minutes=i)
            )
            db.add(call_record)
        
        db.commit()
        db.close()
        
        # Test dashboard stats performance
        import time
        start_time = time.time()
        response = client.get("/admin/dashboard/stats/test-restaurant-1")
        end_time = time.time()
        
        assert response.status_code == 200
        assert end_time - start_time < 2.0  # Should respond within 2 seconds
        assert response.json()["total_calls"] >= 115  # Original 15 + 100 new
    
    def test_invalid_data_handling(self, setup_test_db):
        """Test handling of invalid data"""
        # Test invalid restaurant ID format
        response = client.get("/admin/dashboard/stats/invalid-id-with-special-chars!")
        assert response.status_code == 404
        
        # Test invalid policy data
        invalid_policy = {
            "deposit_required": "not_boolean",
            "max_party_size": -5,
            "opening_hours": "not_array"
        }
        response = client.post("/admin/policies/test-restaurant-1", json=invalid_policy)
        assert response.status_code == 422  # Validation error

# Integration tests
class TestIntegration:
    """Integration tests between different endpoints"""
    
    def test_policy_to_booking_integration(self, setup_test_db):
        """Test that policy changes affect booking validation"""
        # Get initial policy
        response = client.get("/admin/policies/test-restaurant-1")
        initial_policy = response.json()
        initial_max_party = initial_policy["max_party_size"]
        
        # Update max party size
        new_max_party = 4
        response = client.put("/admin/policies/test-restaurant-1", json={
            "max_party_size": new_max_party
        })
        assert response.status_code == 200
        
        # Verify the change
        response = client.get("/admin/policies/test-restaurant-1")
        updated_policy = response.json()
        assert updated_policy["max_party_size"] == new_max_party
        
        # Note: In a real application, you would test that new bookings
        # respect the updated policy, but that would require additional
        # booking creation endpoints which are beyond the scope of this admin API

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
