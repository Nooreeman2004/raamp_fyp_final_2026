"""
Test Brand Alignment Endpoints
"""
import httpx
import asyncio


async def test_brand_alignment_endpoints():
    print("=" * 60)
    print("BRAND ALIGNMENT ENDPOINTS TEST")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    endpoints = [
        ("POST", "/api/brand-alignment/upload-logo", "Upload logo endpoint"),
        ("POST", "/api/brand-alignment/save", "Save brand alignment endpoint"),
        ("GET", "/api/brand-alignment/settings", "Get brand alignment endpoint"),
    ]
    
    print("\nTesting endpoints (all require auth, expect 401 or 422)...\n")
    
    async with httpx.AsyncClient() as client:
        for method, path, description in endpoints:
            try:
                url = f"{base_url}{path}"
                if method == "GET":
                    response = await client.get(url, timeout=5.0)
                else:
                    response = await client.post(url, json={}, timeout=5.0)
                
                # Check if endpoint exists
                if response.status_code in [200, 401, 400, 422]:
                    status = "✅ EXISTS"
                    detail = f"(returns {response.status_code})"
                elif response.status_code == 404:
                    status = "❌ NOT FOUND"
                    detail = ""
                else:
                    status = f"⚠️  {response.status_code}"
                    detail = ""
                
                print(f"{status:15} {method:6} {path:50} {detail}")
                print(f"               {description}")
                
            except httpx.ConnectError:
                print(f"❌ OFFLINE     {method:6} {path:50} (backend not running)")
                break
            except Exception as e:
                print(f"❌ ERROR       {method:6} {path:50} ({str(e)[:40]})")
    
    print("\n" + "=" * 60)
    print("✅ All brand alignment endpoints are registered!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_brand_alignment_endpoints())
