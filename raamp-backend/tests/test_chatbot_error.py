"""
Test script to debug chatbot error
"""
import requests
import json

# Test the chatbot endpoint
url = "http://localhost:8000/api/chatbot/chat"

payload = {
    "message": "How do I get started?",
    "session_id": None,
    "include_sources": False
}

headers = {
    "Content-Type": "application/json"
}

try:
    print("Testing chatbot endpoint...")
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
except requests.exceptions.Timeout:
    print("❌ Request timed out")
except requests.exceptions.RequestException as e:
    print(f"❌ Request error: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"Response status: {e.response.status_code}")
        print(f"Response body: {e.response.text}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
