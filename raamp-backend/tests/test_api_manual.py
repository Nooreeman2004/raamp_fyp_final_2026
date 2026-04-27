"""
Manual API test for /api/trends/simplified endpoint
Run this AFTER starting the server and getting an auth token

Usage:
1. Start server: cd raamp-backend && uvicorn main:app --reload
2. Login and get token from browser/Postman
3. Run: python raamp-backend/tests/test_api_manual.py YOUR_TOKEN_HERE
"""
import sys
import requests
import json


def test_simplified_endpoint(token: str, base_url: str = "http://localhost:8000"):
    """Test the simplified trends endpoint"""
    
    print("\n" + "="*60)
    print("MANUAL API TEST: /api/trends/simplified")
    print("="*60)
    
    endpoint = f"{base_url}/api/trends/simplified"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test 1: Default request
    print("\n📡 Test 1: Default request (limit=5)")
    print(f"   GET {endpoint}?limit=5")
    
    try:
        response = requests.get(f"{endpoint}?limit=5", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success! Got {len(data.get('trends', []))} trends")
            
            # Show first trend in detail
            if data.get('trends'):
                first_trend = data['trends'][0]
                print(f"\n   📊 First Trend:")
                print(f"      Topic: {first_trend.get('topic')}")
                print(f"      Opportunity: {first_trend.get('opportunity_level')}")
                print(f"      Why: {first_trend.get('why_relevant')}")
                print(f"      Action: {first_trend.get('suggested_action')}")
                print(f"      Location: {first_trend.get('location')}")
                
                # Check for quality issues
                print(f"\n   🔍 Quality Checks:")
                why = first_trend.get('why_relevant', '')
                action = first_trend.get('suggested_action', '')
                
                if 'PK' in why or 'PK' in action:
                    print(f"      ⚠️  WARNING: Found 'PK' country code in text")
                else:
                    print(f"      ✅ No country codes in text")
                
                if 'starting to trend' in why.lower():
                    print(f"      ⚠️  WARNING: Generic template text detected")
                else:
                    print(f"      ✅ Text appears customized")
                
                if len(action) < 30:
                    print(f"      ⚠️  WARNING: Action text seems too short")
                else:
                    print(f"      ✅ Action text has good detail")
            
            # Show full response
            print(f"\n   📄 Full Response:")
            print(json.dumps(data, indent=2, default=str))
            
        elif response.status_code == 401:
            print(f"   ❌ Authentication failed - check your token")
        else:
            print(f"   ❌ Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connection failed - is the server running?")
        print(f"   Start with: cd raamp-backend && uvicorn main:app --reload")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: With location filter
    print("\n📡 Test 2: With location filter")
    print(f"   GET {endpoint}?limit=5&location=Pakistan")
    
    try:
        response = requests.get(f"{endpoint}?limit=5&location=Pakistan", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Got {len(data.get('trends', []))} trends for Pakistan")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n❌ Error: Missing auth token")
        print("\nUsage:")
        print("  python raamp-backend/tests/test_api_manual.py YOUR_TOKEN_HERE")
        print("\nHow to get a token:")
        print("  1. Start server: cd raamp-backend && uvicorn main:app --reload")
        print("  2. Login via browser or Postman to /api/auth/signin")
        print("  3. Copy the access_token from response")
        print("  4. Run this script with the token")
        sys.exit(1)
    
    token = sys.argv[1]
    test_simplified_endpoint(token)
