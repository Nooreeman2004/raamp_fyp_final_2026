"""
Test the chatbot endpoint to diagnose the error
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_chatbot():
    """Test the chatbot endpoint"""
    print("🧪 Testing RAAMP Assistant Chatbot...")
    print("=" * 60)
    
    # Test data
    payload = {
        "message": "How do I get started?",
        "session_id": None,
        "include_sources": False
    }
    
    try:
        print(f"\n📤 Sending request to {BASE_URL}/chatbot/chat")
        print(f"Message: {payload['message']}")
        
        response = requests.post(
            f"{BASE_URL}/chatbot/chat",
            json=payload,
            timeout=30
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS!")
            print(f"\nAnswer: {data.get('answer', 'N/A')}")
            print(f"Session ID: {data.get('session_id', 'N/A')}")
            print(f"Timestamp: {data.get('timestamp', 'N/A')}")
        else:
            print("❌ ERROR!")
            print(f"\nResponse: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Backend server is not running!")
        print("Please start the server with: python main.py")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_chatbot()
