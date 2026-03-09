"""
Test chatbot with a single query and longer timeout
"""
import requests
import json
import time

url = "http://localhost:8000/api/chatbot/chat"

test_questions = [
    "How do I create a campaign?",
    "What analytics are available?",
    "Tell me about targeting options"
]

headers = {"Content-Type": "application/json"}

print("Testing chatbot with longer timeout...")
print("=" * 60)

for question in test_questions:
    print(f"\n📤 Question: {question}")
    print("-" * 60)
    
    payload = {
        "message": question,
        "session_id": "test-session-123",
        "include_sources": True
    }
    
    try:
        start_time = time.time()
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get('answer', '')
            sources = data.get('sources', [])
            
            print(f"✅ Status: 200 OK ({elapsed:.1f}s)")
            print(f"\n📥 Answer:\n{answer}\n")
            print(f"🔗 Sources: {len(sources)}")
            
            if sources:
                for i, src in enumerate(sources[:2], 1):
                    print(f"   {i}. {src.get('question', 'N/A')[:60]}...")
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"Response: {response.text}")
    
    except requests.exceptions.Timeout:
        print(f"❌ Timeout (>60s) - Backend may be stuck")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()

print("=" * 60)
