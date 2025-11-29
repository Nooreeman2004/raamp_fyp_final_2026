"""
Check which backend endpoints are available
Run: python check_endpoints.py
"""
import httpx
import asyncio

async def check_endpoints():
    print("=" * 60)
    print("BACKEND ENDPOINT AVAILABILITY CHECK")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # Endpoints the frontend is calling
    endpoints = [
        ("GET", "/api/profile/onboarding/status"),
        ("GET", "/api/profile/connections/facebook"),
        ("GET", "/api/profile/connections/instagram"),
        ("GET", "/api/profile/connections/google-business"),
        ("GET", "/api/profile/connections/facebook/granted-scopes"),
        ("GET", "/api/profile/onboarding/instagram/pages"),
        ("GET", "/api/profile/onboarding/instagram/accounts"),
        ("GET", "/api/profile/onboarding/facebook/auth"),
        ("POST", "/api/profile/onboarding/maps/search"),
        ("POST", "/api/profile/onboarding/maps/confirm"),
        ("POST", "/api/profile/onboarding/maps/save"),
    ]
    
    print("\nChecking endpoints (all require auth, expect 401 or 400)...\n")
    
    async with httpx.AsyncClient() as client:
        for method, path in endpoints:
            try:
                url = f"{base_url}{path}"
                if method == "GET":
                    response = await client.get(url, timeout=5.0)
                else:
                    response = await client.post(url, json={}, timeout=5.0)
                
                # Check if endpoint exists (200, 401, 400 all mean it exists)
                if response.status_code in [200, 401, 400, 422]:
                    status = "✅ EXISTS"
                    detail = f"(returns {response.status_code})"
                elif response.status_code == 404:
                    status = "❌ NOT FOUND"
                    detail = ""
                else:
                    status = f"⚠️  {response.status_code}"
                    detail = ""
                
                print(f"{status:15} {method:6} {path:60} {detail}")
                
            except httpx.ConnectError:
                print(f"❌ OFFLINE     {method:6} {path:60} (backend not running)")
                break
            except Exception as e:
                print(f"❌ ERROR       {method:6} {path:60} ({str(e)[:40]})")
    
    print("\n" + "=" * 60)
    print("Key:")
    print("✅ EXISTS     - Endpoint is registered (may return 401/400 without auth)")
    print("❌ NOT FOUND  - Endpoint does not exist (404)")
    print("❌ OFFLINE    - Backend server not running")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(check_endpoints())
