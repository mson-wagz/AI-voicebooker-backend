#!/usr/bin/env python3
"""
Debug script to test auth routes in isolation
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.core.auth.routes import router
    print("✅ Auth router imported successfully")
    print(f"Router prefix: {router.prefix}")
    print(f"Routes: {[route.path for route in router.routes]}")
except Exception as e:
    print(f"❌ Error importing auth router: {e}")
    import traceback
    traceback.print_exc()

try:
    from src.core.auth.admin_routes import router as admin_router
    print("✅ Admin router imported successfully")
    print(f"Admin router prefix: {admin_router.prefix}")
    print(f"Admin routes: {[route.path for route in admin_router.routes]}")
except Exception as e:
    print(f"❌ Error importing admin router: {e}")
    import traceback
    traceback.print_exc()

try:
    from src.core.auth.restaurant_routes import router as restaurant_router
    print("✅ Restaurant router imported successfully")
    print(f"Restaurant router prefix: {restaurant_router.prefix}")
    print(f"Restaurant routes: {[route.path for route in restaurant_router.routes]}")
except Exception as e:
    print(f"❌ Error importing restaurant router: {e}")
    import traceback
    traceback.print_exc()
