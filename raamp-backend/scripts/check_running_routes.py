"""Get routes from running server"""
import requests

try:
    response = requests.get("http://localhost:8000/openapi.json")
    openapi = response.json()
    
    print("=" * 80)
    print("ROUTES FROM RUNNING SERVER:")
    print("=" * 80)
    
    comment_routes = []
    for path, methods in openapi["paths"].items():
        if "comment" in path.lower():
            for method, details in methods.items():
                if method != "parameters":
                    print(f"{method.upper():8} {path}")
                    comment_routes.append(path)
    
    if not comment_routes:
        print("❌ No comment routes found in running server!")
        print("\nSearching all routes for '/api/comments'...")
        for path in openapi["paths"].keys():
            if "/api/comments" in path:
                print(f"  Found: {path}")
    
    print(f"\nTotal API routes: {len(openapi['paths'])}")
    
except Exception as e:
    print(f"Error: {e}")
