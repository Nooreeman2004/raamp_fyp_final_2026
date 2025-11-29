"""
Test script to diagnose Google Maps API connectivity issues
Run: python test_google_maps.py
"""
import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

async def test_google_maps_api():
    print("=" * 60)
    print("GOOGLE MAPS API DIAGNOSTIC TEST")
    print("=" * 60)
    
    # Step 1: Check if API key is set
    print("\n[1] Checking API Key Configuration...")
    if not GOOGLE_MAPS_API_KEY:
        print("❌ ERROR: GOOGLE_MAPS_API_KEY not found in .env file")
        print("   Please add: GOOGLE_MAPS_API_KEY=your_key_here")
        return
    
    print(f"✅ API Key found: {GOOGLE_MAPS_API_KEY[:20]}...{GOOGLE_MAPS_API_KEY[-4:]}")
    
    # Step 2: Test Places API - Text Search
    print("\n[2] Testing Places API Text Search...")
    test_queries = [
        "Starbucks New York",
        "Empire State Building",
        "crusteez",  # User's actual search
        "pizza restaurant Manhattan"
    ]
    
    for query in test_queries:
        print(f"\n   Testing query: '{query}'")
        url = 'https://maps.googleapis.com/maps/api/place/textsearch/json'
        params = {'query': query, 'key': GOOGLE_MAPS_API_KEY}
        
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(url, params=params, timeout=10.0)
                data = r.json()
                
                status = data.get('status')
                print(f"   Status: {status}")
                
                if status == 'OK':
                    results_count = len(data.get('results', []))
                    print(f"   ✅ Found {results_count} results")
                    if results_count > 0:
                        first = data['results'][0]
                        print(f"   First result: {first.get('name')} - {first.get('formatted_address', 'N/A')}")
                elif status == 'ZERO_RESULTS':
                    print(f"   ⚠️  No results found (this is OK, just means no matches)")
                elif status == 'REQUEST_DENIED':
                    print(f"   ❌ REQUEST DENIED")
                    error_msg = data.get('error_message', 'No error message provided')
                    print(f"   Error: {error_msg}")
                    print("\n   Common causes:")
                    print("   - Places API not enabled in Google Cloud Console")
                    print("   - API key restrictions (HTTP referrer, IP address, etc.)")
                    print("   - Billing not enabled")
                elif status == 'OVER_QUERY_LIMIT':
                    print(f"   ❌ OVER QUERY LIMIT - You've exceeded your quota")
                elif status == 'INVALID_REQUEST':
                    print(f"   ❌ INVALID REQUEST")
                    error_msg = data.get('error_message', 'No error message provided')
                    print(f"   Error: {error_msg}")
                else:
                    print(f"   ❌ Unexpected status: {status}")
                    error_msg = data.get('error_message', 'No error message provided')
                    print(f"   Error: {error_msg}")
                    
        except httpx.HTTPStatusError as e:
            print(f"   ❌ HTTP Error: {e.response.status_code}")
            print(f"   Response: {e.response.text}")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    # Step 3: Test Places API - Place Details
    print("\n[3] Testing Places API Place Details...")
    # Use a well-known place_id
    test_place_id = "ChIJN1t_tDeuEmsRUsoyG83frY4"  # Google Sydney office
    url = 'https://maps.googleapis.com/maps/api/place/details/json'
    params = {
        'place_id': test_place_id,
        'fields': 'place_id,name,formatted_address,geometry',
        'key': GOOGLE_MAPS_API_KEY
    }
    
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url, params=params, timeout=10.0)
            data = r.json()
            
            status = data.get('status')
            print(f"   Status: {status}")
            
            if status == 'OK':
                result = data.get('result', {})
                print(f"   ✅ Place Details retrieved")
                print(f"   Name: {result.get('name')}")
                print(f"   Address: {result.get('formatted_address')}")
            else:
                print(f"   ❌ Failed: {status}")
                error_msg = data.get('error_message', 'No error message provided')
                print(f"   Error: {error_msg}")
                
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Step 4: Check API Key restrictions
    print("\n[4] API Key Restriction Check...")
    print("   If you're getting REQUEST_DENIED errors:")
    print("   1. Go to: https://console.cloud.google.com/apis/credentials")
    print("   2. Find your API key and click Edit")
    print("   3. Check 'Application restrictions':")
    print("      - For testing: Set to 'None'")
    print("      - For production: Add your domains/IPs")
    print("   4. Check 'API restrictions':")
    print("      - Ensure 'Places API' is in the allowed list")
    print("      - Also enable 'Maps JavaScript API' and 'Geocoding API'")
    
    print("\n[5] Verify APIs are enabled...")
    print("   Go to: https://console.cloud.google.com/apis/library")
    print("   Search and enable these APIs:")
    print("   ✓ Places API")
    print("   ✓ Maps JavaScript API")
    print("   ✓ Geocoding API")
    
    print("\n[6] Verify Billing...")
    print("   Go to: https://console.cloud.google.com/billing")
    print("   Ensure a billing account is linked to your project")
    print("   Note: Google provides $200/month free credit")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_google_maps_api())
