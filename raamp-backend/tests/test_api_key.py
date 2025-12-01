import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

print(f"Testing Google Maps API Key: {API_KEY[:20]}...{API_KEY[-4:]}")
print(f"Full key length: {len(API_KEY)} characters")

# Test with a simple text search
url = 'https://maps.googleapis.com/maps/api/place/textsearch/json'
params = {
    'query': 'Starbucks New York',
    'key': API_KEY
}

try:
    response = requests.get(url, params=params, timeout=10)
    data = response.json()
    
    print(f"\nAPI Response Status: {data.get('status')}")
    
    if data.get('status') == 'OK':
        print(f"✅ SUCCESS! Found {len(data.get('results', []))} results")
        if data.get('results'):
            first = data['results'][0]
            print(f"First result: {first.get('name')} - {first.get('formatted_address')}")
    elif data.get('status') == 'REQUEST_DENIED':
        print(f"❌ REQUEST DENIED")
        print(f"Error message: {data.get('error_message', 'No error message')}")
        print("\nPossible reasons:")
        print("1. API key is invalid")
        print("2. Places API is not enabled for this key")
        print("3. API key restrictions (HTTP referrers, IP addresses, or API restrictions)")
    else:
        print(f"❌ API Error: {data.get('status')}")
        print(f"Error message: {data.get('error_message', 'No error message')}")
        
except Exception as e:
    print(f"❌ Exception: {str(e)}")
