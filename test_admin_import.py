# Test admin service import and registration
import sys
import os

# Add the admin directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    print("Testing admin service import...")
    
    # Test basic import
    from admin import initialize_admin_service
    print("initialize_admin_service imported successfully")
    
    # Test router import
    from admin.admin_service import router
    print("admin router imported successfully")
    
    # Test routes
    routes = [route.path for route in router.routes]
    print(f"Found {len(routes)} routes:")
    for route in routes:
        print(f"  - {route}")
    
    # Create a mock FastAPI app
    from fastapi import FastAPI
    app = FastAPI()
    
    # Test initialization
    result = initialize_admin_service(app)
    if result:
        print("Admin service initialized successfully")
    else:
        print("Admin service initialization failed")
    
    # Check if routes were added
    admin_routes = [route for route in app.routes if hasattr(route, 'path') and '/admin' in route.path]
    print(f"Found {len(admin_routes)} admin routes in app:")
    for route in admin_routes:
        print(f"  - {route.path} ({route.methods})")
    
    print("\nAdmin service test completed successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
