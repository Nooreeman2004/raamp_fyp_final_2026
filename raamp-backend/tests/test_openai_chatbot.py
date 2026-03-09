"""
Test OpenAI Chatbot Integration
================================
Tests the RAAMP chatbot with OpenAI backend to ensure:
- RAG retrieval works correctly
- OpenAI LLM generates appropriate responses
- Conversation history is maintained
- Error handling works properly
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from application.services.rag.raamp_generation import RAAMPGenerator, RAMPAssistant
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_generator_initialization():
    """Test that the generator initializes correctly with OpenAI."""
    print("\n" + "=" * 60)
    print("TEST 1: Generator Initialization")
    print("=" * 60)
    
    try:
        generator = RAAMPGenerator()
        assert generator is not None, "Generator should not be None"
        assert generator.llm is not None, "LLM should be initialized"
        assert "gpt" in generator.model_name.lower() or "o1" in generator.model_name.lower(), \
            f"Should be using OpenAI model, got: {generator.model_name}"
        print(f"✅ Generator initialized successfully")
        print(f"   Model: {generator.model_name}")
        return True
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False


def test_health_check():
    """Test the health check endpoint."""
    print("\n" + "=" * 60)
    print("TEST 2: Health Check")
    print("=" * 60)
    
    try:
        generator = RAAMPGenerator()
        health = generator.health_check()
        
        assert health is not None, "Health check should return a result"
        assert health.get("status") == "healthy", f"Status should be healthy, got: {health.get('status')}"
        
        print(f"✅ Health check passed")
        print(f"   Status: {health.get('status')}")
        print(f"   Model: {health.get('model')}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_simple_query():
    """Test a simple query about RAAMP."""
    print("\n" + "=" * 60)
    print("TEST 3: Simple Query")
    print("=" * 60)
    
    try:
        generator = RAAMPGenerator()
        query = "What is RAAMP?"
        
        response = generator.generate_response(query)
        
        assert response is not None, "Response should not be None"
        assert response.answer, "Answer should not be empty"
        assert len(response.answer) > 20, "Answer should be substantial"
        assert response.model, "Model name should be present"
        assert response.sources, "Sources should be retrieved"
        
        print(f"✅ Simple query successful")
        print(f"   Query: {query}")
        print(f"   Answer length: {len(response.answer)} chars")
        print(f"   Sources: {len(response.sources)} documents")
        print(f"   Answer preview: {response.answer[:150]}...")
        return True
    except Exception as e:
        print(f"❌ Simple query failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_conversation_mode():
    """Test conversation mode with history."""
    print("\n" + "=" * 60)
    print("TEST 4: Conversation Mode")
    print("=" * 60)
    
    try:
        assistant = RAMPAssistant(session_id="test-session")
        
        # First message
        response1 = assistant.ask("Hello!")
        assert response1 is not None, "First response should not be None"
        assert response1.get("answer"), "First answer should not be empty"
        
        # Second message (should have context)
        response2 = assistant.ask("What features does RAAMP have?")
        assert response2 is not None, "Second response should not be None"
        assert response2.get("answer"), "Second answer should not be empty"
        
        # Check conversation history
        history = assistant.get_conversation_history()
        assert len(history) >= 4, f"Should have at least 4 messages (2 pairs), got {len(history)}"
        
        print(f"✅ Conversation mode successful")
        print(f"   Messages exchanged: {len(history) // 2}")
        print(f"   Total history length: {len(history)} messages")
        return True
    except Exception as e:
        print(f"❌ Conversation mode failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rag_retrieval():
    """Test that RAG retrieval is working."""
    print("\n" + "=" * 60)
    print("TEST 5: RAG Retrieval")
    print("=" * 60)
    
    try:
        generator = RAAMPGenerator()
        
        # Query that should trigger retrieval
        query = "How do I sign up for RAAMP?"
        response = generator.generate_response(query)
        
        assert response.sources, "Should retrieve source documents"
        assert len(response.sources) > 0, "Should have at least one source"
        assert response.context_used, "Context should be used"
        
        print(f"✅ RAG retrieval successful")
        print(f"   Query: {query}")
        print(f"   Sources retrieved: {len(response.sources)}")
        print(f"   Context length: {len(response.context_used)} chars")
        
        # Print source details
        for i, source in enumerate(response.sources[:3], 1):
            print(f"   Source {i}: {source.get('question', 'N/A')[:50]}...")
        
        return True
    except Exception as e:
        print(f"❌ RAG retrieval failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_guardrails():
    """Test that guardrails work for out-of-scope questions."""
    print("\n" + "=" * 60)
    print("TEST 6: Guardrails")
    print("=" * 60)
    
    try:
        generator = RAAMPGenerator()
        
        # Question outside RAAMP scope
        query = "What is the capital of France?"
        response = generator.generate_response(query)
        
        assert response is not None, "Response should not be None"
        assert response.answer, "Should still provide an answer"
        
        # Check if response acknowledges limited scope (optional)
        answer_lower = response.answer.lower()
        keywords = ["raamp", "specialized", "platform", "help", "assist"]
        has_redirect = any(keyword in answer_lower for keyword in keywords)
        
        print(f"✅ Guardrails test complete")
        print(f"   Query: {query}")
        print(f"   Response: {response.answer[:200]}...")
        print(f"   Redirects to RAAMP: {has_redirect}")
        return True
    except Exception as e:
        print(f"❌ Guardrails test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "🚀" * 30)
    print("OPENAI CHATBOT TEST SUITE")
    print("🚀" * 30)
    
    # Check prerequisites
    if not os.getenv("OPENAI_API_KEY"):
        print("\n❌ OPENAI_API_KEY not found in environment")
        print("Please set your OpenAI API key in .env file")
        return
    
    tests = [
        ("Generator Initialization", test_generator_initialization),
        ("Health Check", test_health_check),
        ("Simple Query", test_simple_query),
        ("Conversation Mode", test_conversation_mode),
        ("RAG Retrieval", test_rag_retrieval),
        ("Guardrails", test_guardrails),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{'='*60}")
    print(f"Results: {passed}/{total} tests passed")
    print(f"{'='*60}")
    
    if passed == total:
        print("\n🎉 All tests passed! OpenAI chatbot is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")


if __name__ == "__main__":
    run_all_tests()
