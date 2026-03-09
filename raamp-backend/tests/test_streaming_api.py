"""
Test Streaming API Endpoint
============================
Tests the /api/chatbot/chat/stream endpoint
"""

import requests
import json


def test_streaming_endpoint():
    """Test the streaming endpoint with SSE"""
    print("\n" + "=" * 70)
    print("🧪 TESTING STREAMING API ENDPOINT")
    print("=" * 70)
    
    url = "http://localhost:8000/api/chatbot/chat/stream"
    
    payload = {
        "message": "What is RAAMP?",
        "session_id": "test-stream-001",
        "include_sources": True
    }
    
    print(f"\n📤 POST {url}")
    print(f"   Payload: {json.dumps(payload, indent=2)}")
    print("\n🔄 Streaming response:")
    print("─" * 70)
    
    try:
        # Stream the response
        with requests.post(url, json=payload, stream=True, timeout=60) as response:
            response.raise_for_status()
            
            # Check headers
            content_type = response.headers.get('content-type', '')
            if 'text/event-stream' not in content_type:
                print(f"\n⚠️  WARNING: Expected 'text/event-stream', got '{content_type}'")
            
            token_count = 0
            full_content = ""
            sources = None
            session_id = None
            
            # Process SSE stream
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    # SSE format: "data: {json}"
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix
                        
                        try:
                            data = json.loads(data_str)
                            event_type = data.get("type")
                            
                            if event_type == "token":
                                # Print token
                                content = data.get("content", "")
                                print(content, end="", flush=True)
                                full_content += content
                                token_count += 1
                            
                            elif event_type == "done":
                                # Stream completed
                                session_id = data.get("session_id")
                                sources = data.get("sources", [])
                                print("\n" + "─" * 70)
                                print(f"\n✅ Stream completed!")
                                print(f"   Session ID: {session_id}")
                                print(f"   Total tokens: {token_count}")
                                print(f"   Response length: {len(full_content)} chars")
                                print(f"   Sources: {len(sources)}")
                                
                                if sources:
                                    print(f"\n   Top source:")
                                    top_source = sources[0]
                                    print(f"   - Question: {top_source.get('question', 'N/A')[:50]}...")
                                    print(f"   - Category: {top_source.get('category', 'N/A')}")
                                    print(f"   - Relevance: {top_source.get('relevance', 0):.4f}")
                            
                            elif event_type == "error":
                                # Error occurred
                                error_msg = data.get("content", "Unknown error")
                                print(f"\n❌ Error: {error_msg}")
                                return False
                                
                        except json.JSONDecodeError as e:
                            print(f"\n⚠️  Warning: Failed to parse JSON: {data_str[:50]}")
            
            return True
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_streaming_quick_response():
    """Test streaming with a quick response query"""
    print("\n" + "=" * 70)
    print("🧪 TESTING QUICK RESPONSE (Word-by-Word)")
    print("=" * 70)
    
    url = "http://localhost:8000/api/chatbot/chat/stream"
    
    payload = {
        "message": "hello",
        "session_id": "test-stream-002",
        "include_sources": False
    }
    
    print(f"\n📤 POST {url}")
    print(f"   Payload: {json.dumps(payload, indent=2)}")
    print("\n🔄 Streaming response:")
    print("─" * 70)
    
    try:
        with requests.post(url, json=payload, stream=True, timeout=30) as response:
            response.raise_for_status()
            
            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith("data: "):
                    data_str = line[6:]
                    
                    try:
                        data = json.loads(data_str)
                        event_type = data.get("type")
                        
                        if event_type == "token":
                            content = data.get("content", "")
                            print(content, end="", flush=True)
                        
                        elif event_type == "done":
                            print("\n" + "─" * 70)
                            print(f"\n✅ Quick response stream completed!")
                            return True
                        
                        elif event_type == "error":
                            print(f"\n❌ Error: {data.get('content')}")
                            return False
                            
                    except json.JSONDecodeError:
                        pass
            
            return True
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False


def main():
    """Run all API streaming tests"""
    print("\n" + "=" * 70)
    print("🚀 STREAMING API TEST SUITE")
    print("=" * 70)
    
    results = []
    
    results.append(("Streaming Endpoint", test_streaming_endpoint()))
    results.append(("Quick Response", test_streaming_quick_response()))
    
    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All API streaming tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
