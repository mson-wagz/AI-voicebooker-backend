"""
Simple test to verify admin backend functionality
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_admin_service_import():
    """Test that admin service can be imported"""
    try:
        from admin.admin_service import router
        print("Admin service router imported successfully")
        
        # Check routes
        routes = [route.path for route in router.routes]
        expected_routes = [
            "/dashboard/stats/{restaurant_id}",
            "/policies/{restaurant_id}",
            "/calls/{restaurant_id}",
            "/bookings/{restaurant_id}",
            "/health"
        ]
        
        for route in expected_routes:
            if any(route in r for r in routes):
                print(f"Route found: {route}")
            else:
                print(f"Route missing: {route}")
        
        return True
    except ImportError as e:
        print(f"Failed to import admin service: {e}")
        return False

def test_admin_models():
    """Test that admin models are defined"""
    try:
        from admin.admin_service import DashboardStats, PolicyCreate, PolicyUpdate, PolicyResponse
        print("Admin models imported successfully")
        return True
    except ImportError as e:
        print(f"Failed to import admin models: {e}")
        return False

def test_admin_init():
    """Test that admin init works"""
    try:
        from admin import initialize_admin_service
        print("Admin initialize function imported successfully")
        return True
    except ImportError as e:
        print(f"Failed to import admin init: {e}")
        return False

if __name__ == "__main__":
    print("Testing Admin Backend...")
    print("=" * 50)
    
    success = True
    success &= test_admin_service_import()
    success &= test_admin_models()
    success &= test_admin_init()
    
    print("=" * 50)
    if success:
        print("All admin backend tests passed!")
    else:
        print("Some admin backend tests failed!")
        sys.exit(1)
