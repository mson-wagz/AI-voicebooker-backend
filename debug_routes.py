"""
Debug script to check routes
"""
from src.main import app

print("All routes in the app:")
for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        print(f"{route.methods} {route.path}")
    elif hasattr(route, 'path'):
        print(f"ROUTE: {route.path}")

print("\nChecking auth router specifically:")
from src.core.auth.routes import router
for route in router.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        print(f"{route.methods} {route.path}")
    elif hasattr(route, 'path'):
        print(f"AUTH ROUTE: {route.path}")
