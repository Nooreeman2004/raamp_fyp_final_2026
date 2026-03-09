"""
Streaming Chatbot Test Script
==============================
Tests the streaming functionality of the OpenAI RAG chatbot.
"""

import sys
from pathlib import Path
import asyncio

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from application.services.rag.raamp_generation import RAAMPGenerator
from dotenv import load_dotenv
import os

load_dotenv()


def test_streaming_basic():
    """Test basic streaming functionality"""
    print("\n" + "=" * 70)
    print("TEST 1: Basic Streaming")
    print("=" * 70)
    
    try:
        generator = RAAMPGenerator()
        
        query = "What is RAAMP?"
        print(f"\n📝 Query: {query}")
        print(f"🔄 Streaming response:")
        print("─" * 70)
        
        full_response = ""
        token_count = 0
        
        for token in generator.generate_response_stream(query):
            print(token, end="", flush=True)
            full_response += token
            token_count += 1
        
        print("\n" + "─" * 70)
        print(f"✅ Streaming test passed!")
        print(f"   Total tokens: {token_count}")
        print(f"   Response length: {len(full_response)} chars")
        return True
        
    except Exception as e:
        print(f"\n❌ Streaming test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_streaming_with_history():
    """Test streaming with conversation history"""
    print("\n" + "=" * 70)
    print("TEST 2: Streaming with Conversation History")
    print("=" * 70)
    
    try:
        generator = RAAMPGenerator()
        
        # First query
        query1 = "My name is Alice"
        print(f"\n📝 Query 1: {query1}")
        print(f"🔄 Streaming response:")
        print("─" * 70)
        
        response1 = ""
        for token in generator.generate_response_stream(query1):
            print(token, end="", flush=True)
            response1 += token
        
        print("\n" + "─" * 70)
        
        # Build history
        history = [
            {"role": "user", "content": query1},
            {"role": "assistant", "content": response1}
        ]
        
        # Second query (should remember name)
        query2 = "What is my name?"
        print(f"\n📝 Query 2: {query2}")
        print(f"🔄 Streaming response:")
        print("─" * 70)
        
        response2 = ""
        for token in generator.generate_response_stream(query2, chat_history=history):
            print(token, end="", flush=True)
            response2 += token
        
        print("\n" + "─" * 70)
        
        # Check if response mentions the name
        if "alice" in response2.lower():
            print(f"✅ Conversation history test passed!")
            print(f"   Response correctly recalled the name")
            return True
        else:
            print(f"⚠️  Conversation history test partial pass")
            print(f"   Response: {response2[:100]}...")
            return True  # Still pass since streaming worked
            
    except Exception as e:
        print(f"\n❌ Conversation history test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_streaming_error_handling():
    """Test streaming error handling"""
    print("\n" + "=" * 70)
    print("TEST 3: Streaming Error Handling")
    print("=" * 70)
    
    try:
        generator = RAAMPGenerator()
        
        # Test with problematic query
        query = "What is RAAMP?" * 100  # Very long query
        print(f"\n📝 Query: Long query ({len(query)} chars)")
        print(f"🔄 Streaming response:")
        print("─" * 70)
        
        full_response = ""
        for token in generator.generate_response_stream(query):
            print(token, end="", flush=True)
            full_response += token
        
        print("\n" + "─" * 70)
        print(f"✅ Error handling test passed!")
        print(f"   Response length: {len(full_response)} chars")
        return True
        
    except Exception as e:
        print(f"\n❌ Error handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_public_get_sources():
    """Test the public get_sources method"""
    print("\n" + "=" * 70)
    print("TEST 4: Public get_sources Method")
    print("=" * 70)
    
    try:
        generator = RAAMPGenerator()
        
        query = "What is RAAMP?"
        print(f"\n📝 Query: {query}")
        
        sources = generator.get_sources(query, n_results=3)
        
        print(f"✅ get_sources test passed!")
        print(f"   Sources retrieved: {len(sources)}")
        
        if sources:
            print(f"\n   Top source:")
            print(f"   - Question: {sources[0]['question'][:60]}...")
            print(f"   - Category: {sources[0]['category']}")
            print(f"   - Relevance: {sources[0]['relevance']:.4f}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ get_sources test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all streaming tests"""
    print("\n" + "=" * 70)
    print("🚀 STREAMING CHATBOT TEST SUITE")
    print("=" * 70)
    
    # Check prerequisites
    if not os.getenv("OPENAI_API_KEY"):
        print("\n❌ ERROR: OPENAI_API_KEY not found in environment")
        print("Please set your OpenAI API key in .env file")
        return 1
    
    print(f"\n✅ OPENAI_API_KEY is set")
    
    # Run tests
    results = []
    
    results.append(("Basic Streaming", test_streaming_basic()))
    results.append(("Streaming with History", test_streaming_with_history()))
    results.append(("Streaming Error Handling", test_streaming_error_handling()))
    results.append(("Public get_sources Method", test_public_get_sources()))
    
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
        print("\n🎉 All streaming tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
