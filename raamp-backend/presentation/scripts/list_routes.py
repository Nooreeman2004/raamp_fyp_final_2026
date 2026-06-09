"""List all registered routes"""
import sys
sys.path.insert(0, "D:\\raamp-fyp-final\\raamp-backend")

from main import app

print("=" * 80)
print("REGISTERED ROUTES:")
print("=" * 80)

for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        methods = ','.join(route.methods) if route.methods else 'N/A'
        print(f"{methods:8} {route.path}")
    elif hasattr(route, 'path'):
        print(f"{'MOUNT':8} {route.path}")

print("=" * 80)
print(f"Total routes: {len(app.routes)}")

# Search for comment-related routes
print("\n" + "=" * 80)
print("COMMENT-RELATED ROUTES:")
print("=" * 80)
comment_routes = [r for r in app.routes if hasattr(r, 'path') and 'comment' in r.path.lower()]
if comment_routes:
    for route in comment_routes:
        methods = ','.join(route.methods) if hasattr(route, 'methods') and route.methods else 'N/A'
        print(f"{methods:8} {route.path}")
else:
    print("❌ No comment-related routes found!")
