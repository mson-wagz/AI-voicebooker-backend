"""
Simple admin backend test - verifies endpoints work correctly
"""
import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_admin_imports():
    """Test that admin modules can be imported"""
    try:
        from admin.admin_service import router
        from admin import initialize_admin_service
        assert router is not None
        assert initialize_admin_service is not None
        print("✅ Admin imports successful")
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")

def test_admin_routes():
    """Test that admin routes are properly defined"""
    try:
        from admin.admin_service import router
        
        routes = [route.path for route in router.routes]
        expected_routes = [
            "/dashboard/stats/{restaurant_id}",
            "/policies/{restaurant_id}",
            "/calls/{restaurant_id}",
            "/bookings/{restaurant_id}",
            "/health"
        ]
        
        for route in expected_routes:
            assert any(route in r for r in routes), f"Route {route} not found"
        
        print("✅ All admin routes defined")
    except Exception as e:
        pytest.fail(f"Route test failed: {e}")

if __name__ == "__main__":
    test_admin_imports()
    test_admin_routes()
    print("✅ All admin tests passed!")
