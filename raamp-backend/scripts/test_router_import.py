"""Test if the moderation endpoint can be imported without errors"""
import sys
sys.path.insert(0, "D:\\raamp-fyp-final\\raamp-backend")

try:
    print("Importing router module...")
    from presentation.routers import comment_analysis_router
    
    print(f"✅ Router imported")
    print(f"   Prefix: {comment_analysis_router.router.prefix}")
    print(f"   Routes: {len(comment_analysis_router.router.routes)}")
    
    print("\nRoute details:")
    for route in comment_analysis_router.router.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            methods = ','.join(route.methods) if route.methods else 'N/A'
            print(f"  {methods:8} {route.path}")
            if hasattr(route, 'endpoint'):
                print(f"           -> {route.endpoint.__name__}")
    
    print("\n✅ All routes loaded successfully!")
    
except Exception as e:
    print(f"\n❌ ERROR during import:")
    print(f"   Type: {type(e).__name__}")
    print(f"   Message: {str(e)}")
    import traceback
    traceback.print_exc()
