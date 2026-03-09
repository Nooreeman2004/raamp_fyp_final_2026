"""
Simple test script to check chatbot endpoint
Tests basic functionality and response format of the OpenAI-based RAG chatbot.
"""
import requests
import json
import time

# Test the chatbot endpoint
url = "http://localhost:8000/api/chatbot/chat"

# Test cases covering different scenarios
test_messages = [
    # Basic greeting
    {"message": "Hello", "description": "Basic greeting"},
    
    # Knowledge base query (should use RAG)
    {"message": "What is RAAMP?", "description": "Knowledge base query"},
    
    # Feature query (should use RAG)
    {"message": "How do I get started?", "description": "Getting started query"},
    
    # Campaign query (should use RAG)
    {"message": "How do I create a campaign?", "description": "Campaign creation query"},
    
    # Out of scope query
    {"message": "What is the capital of Mars?", "description": "Out of scope query"},
]

headers = {
    "Content-Type": "application/json"
}

print("=" * 70)
print("SIMPLE CHATBOT API TEST")
print("=" * 70)
print("\n🧪 Testing OpenAI-based RAG chatbot endpoint...")
print(f"📍 Endpoint: {url}\n")

# Statistics
total_tests = len(test_messages)
passed_tests = 0
failed_tests = 0
total_time = 0

for i, test_case in enumerate(test_messages, 1):
    message = test_case["message"]
    description = test_case["description"]
    
    print(f"\n{'='*70}")
    print(f"Test {i}/{total_tests}: {description}")
    print(f"{'='*70}")
    print(f"📤 Sending: {message}")
    print("-" * 70)
    
    payload = {
        "message": message,
        "session_id": None,
        "include_sources": True
    }
    
    try:
        start_time = time.time()
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        elapsed_time = time.time() - start_time
        total_time += elapsed_time
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            required_fields = ['answer', 'session_id', 'timestamp']
            missing_fields = [f for f in required_fields if f not in data]
            
            if missing_fields:
                print(f"⚠️  Warning: Missing fields: {missing_fields}")
            
            print(f"✅ Status: {response.status_code}")
            print(f"⏱️  Response time: {elapsed_time:.2f}s")
            print(f"📥 Answer: {data.get('answer', 'No answer')[:200]}...")
            
            if data.get('sources'):
                print(f"🔗 Sources: {len(data.get('sources', []))} documents retrieved")
            else:
                print(f"🔗 Sources: None (quick response or no retrieval needed)")
            
            # Check if response is appropriate
            answer_lower = data.get('answer', '').lower()
            if 'raamp' in message.lower() and 'raamp' not in answer_lower:
                print(f"⚠️  Warning: Query mentions RAAMP but answer doesn't")
            
            passed_tests += 1
            
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            failed_tests += 1
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Backend is not running")
        print("   Start the backend with: uvicorn main:app --reload")
        failed_tests += 1
        break
    except requests.exceptions.Timeout:
        print("❌ Request timed out (>30s)")
        failed_tests += 1
    except Exception as e:
        print(f"❌ Error: {e}")
        failed_tests += 1

# Summary
print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)
print(f"Total tests: {total_tests}")
print(f"✅ Passed: {passed_tests}")
print(f"❌ Failed: {failed_tests}")
print(f"⏱️  Total time: {total_time:.2f}s")
print(f"⏱️  Average time: {(total_time / passed_tests if passed_tests > 0 else 0):.2f}s")
print("=" * 70)

if passed_tests == total_tests:
    print("\n🎉 All tests passed! Chatbot API is working correctly.")
else:
    print(f"\n⚠️  {failed_tests} test(s) failed. Review the output above.")

