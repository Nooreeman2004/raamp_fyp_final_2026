"""
Comprehensive Test Suite for OpenAI-based RAG Chatbot
=====================================================
Tests to verify that the OpenAI + LangChain chatbot is functioning correctly
with proper RAG retrieval, error handling, and response formatting.
"""

import pytest
import time
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from application.services.rag.raamp_generation import RAAMPGenerator, RAMPAssistant
from dotenv import load_dotenv
import os

load_dotenv()


class TestBasicChatFunctionality:
    """Test 1: Basic Chat Test - Verify chatbot returns valid responses"""
    
    def test_simple_greeting(self):
        """Test that chatbot responds to a simple greeting"""
        generator = RAAMPGenerator()
        
        query = "Hello, what can you do?"
        response = generator.generate_response(query)
        
        # Verify response structure
        assert response is not None, "Response should not be None"
        assert hasattr(response, 'answer'), "Response should have 'answer' attribute"
        assert hasattr(response, 'model'), "Response should have 'model' attribute"
        
        # Verify answer content
        assert response.answer, "Answer should not be empty"
        assert len(response.answer) > 10, "Answer should be substantial"
        assert isinstance(response.answer, str), "Answer should be a string"
        
        # Verify model is OpenAI
        assert 'gpt' in response.model.lower() or 'o1' in response.model.lower(), \
            f"Should be using OpenAI model, got: {response.model}"
        
        print(f"✅ Basic greeting test passed")
        print(f"   Model: {response.model}")
        print(f"   Response: {response.answer[:100]}...")
    
    def test_capabilities_question(self):
        """Test that chatbot can describe its capabilities"""
        generator = RAAMPGenerator()
        
        query = "What can you help me with?"
        response = generator.generate_response(query)
        
        assert response is not None
        assert response.answer
        assert len(response.answer) > 20
        
        # Should mention RAAMP or assistance
        answer_lower = response.answer.lower()
        assert 'raamp' in answer_lower or 'help' in answer_lower or 'assist' in answer_lower, \
            "Response should mention RAAMP or assistance capabilities"
        
        print(f"✅ Capabilities question test passed")


class TestRAGRetrieval:
    """Test 2: RAG Retrieval Test - Verify knowledge base retrieval"""
    
    def test_raamp_knowledge_retrieval(self):
        """Test retrieval of RAAMP-specific information"""
        generator = RAAMPGenerator()
        
        # Question that should be in the knowledge base
        query = "What is RAAMP?"
        response = generator.generate_response(query)
        
        # Verify response
        assert response is not None
        assert response.answer
        
        # Verify sources were retrieved
        assert response.sources is not None, "Sources should be retrieved"
        assert len(response.sources) > 0, "Should have at least one source document"
        
        # Verify context was used
        assert response.context_used, "Context should be used from retrieval"
        assert len(response.context_used) > 0, "Context should not be empty"
        
        # Verify answer mentions RAAMP
        answer_lower = response.answer.lower()
        assert 'raamp' in answer_lower, "Answer should mention RAAMP"
        
        print(f"✅ RAAMP knowledge retrieval test passed")
        print(f"   Sources retrieved: {len(response.sources)}")
        print(f"   Context length: {len(response.context_used)} chars")
        print(f"   Top source: {response.sources[0].get('question', 'N/A')[:50]}...")
    
    def test_feature_specific_retrieval(self):
        """Test retrieval of specific feature information"""
        generator = RAAMPGenerator()
        
        # Test different RAAMP-related queries
        test_queries = [
            "How do I sign up for RAAMP?",
            "What features does RAAMP have?",
            "Tell me about RAAMP campaigns"
        ]
        
        for query in test_queries:
            response = generator.generate_response(query)
            
            assert response is not None
            assert response.answer
            assert response.sources and len(response.sources) > 0, \
                f"Should retrieve sources for: {query}"
            
            print(f"✅ Retrieved {len(response.sources)} sources for: {query[:40]}...")
    
    def test_retrieval_relevance(self):
        """Test that retrieved sources are relevant"""
        generator = RAAMPGenerator()
        
        query = "What is RAAMP?"
        response = generator.generate_response(query)
        
        # Check that sources have relevance scores
        for source in response.sources:
            assert 'relevance' in source, "Source should have relevance score"
            assert isinstance(source['relevance'], (int, float)), "Relevance should be numeric"
            
        # Sources should be ordered by relevance (highest first)
        if len(response.sources) > 1:
            relevances = [s.get('relevance', 0) for s in response.sources]
            assert relevances[0] >= relevances[-1], "Sources should be ordered by relevance"
        
        print(f"✅ Retrieval relevance test passed")


class TestUnknownQuestionHandling:
    """Test 3: Unknown Question Handling - Verify graceful handling of out-of-scope queries"""
    
    def test_out_of_scope_question(self):
        """Test handling of questions outside RAAMP knowledge"""
        generator = RAAMPGenerator()
        
        # Questions that should NOT be in the knowledge base
        out_of_scope_queries = [
            "What is the capital of Mars?",
            "How do I bake a chocolate cake?",
            "Who won the World Cup in 2024?"
        ]
        
        for query in out_of_scope_queries:
            response = generator.generate_response(query)
            
            assert response is not None, f"Should return response for: {query}"
            assert response.answer, f"Should have answer for: {query}"
            
            # Should not hallucinate - should acknowledge limited scope
            answer_lower = response.answer.lower()
            
            # Check if response indicates it's out of scope (optional check)
            scope_indicators = ['raamp', 'specialized', 'platform', 'help with', 'assist']
            has_scope_indicator = any(indicator in answer_lower for indicator in scope_indicators)
            
            print(f"✅ Out-of-scope query handled: {query[:40]}...")
            print(f"   Redirects to RAAMP: {has_scope_indicator}")
            print(f"   Response: {response.answer[:100]}...")
    
    def test_no_hallucination(self):
        """Test that chatbot doesn't hallucinate answers"""
        generator = RAAMPGenerator()
        
        query = "What is the capital of Mars?"
        response = generator.generate_response(query)
        
        # Should not confidently state a false answer
        answer_lower = response.answer.lower()
        
        # Should not contain made-up capital cities
        false_capitals = ['olympus', 'marsland', 'redville', 'martian city']
        for false_capital in false_capitals:
            assert false_capital not in answer_lower, \
                f"Should not hallucinate answer containing: {false_capital}"
        
        print(f"✅ No hallucination test passed")


class TestErrorHandling:
    """Test 4: Error Handling - Verify graceful error handling"""
    
    def test_api_key_missing(self):
        """Test handling when OpenAI API key is missing"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': ''}):
            with pytest.raises(ValueError) as exc_info:
                generator = RAAMPGenerator()
            
            # Should raise clear error
            assert 'OPENAI_API_KEY' in str(exc_info.value)
            
        print(f"✅ Missing API key handling test passed")
    
    def test_llm_failure_handling(self):
        """Test handling when LLM call fails"""
        generator = RAAMPGenerator()
        
        # Mock the OpenAI client's chat.completions.create method to simulate API failure
        with patch('langchain_openai.ChatOpenAI.invoke', side_effect=Exception("API Error")):
            response = generator.generate_response("Test query")
            
            # Should return user-friendly error message
            assert response is not None
            assert response.answer
            
            # Should NOT expose technical error details
            assert 'API Error' not in response.answer, \
                "Should not expose internal error details"
            assert 'exception' not in response.answer.lower(), \
                "Should not mention exceptions to user"
            
            # Should contain friendly message
            friendly_terms = ['apologize', 'trouble', 'try again', 'moment', 'technical', 'difficulties']
            assert any(term in response.answer.lower() for term in friendly_terms), \
                "Should provide user-friendly error message"
        
        print(f"✅ LLM failure handling test passed")
    
    def test_retriever_failure_handling(self):
        """Test handling when retriever fails"""
        generator = RAAMPGenerator()
        
        # Mock retriever to raise an exception
        with patch.object(generator.retriever, 'retrieve', side_effect=Exception("Retrieval Error")):
            # Should either handle gracefully or raise appropriate error
            try:
                response = generator.generate_response("Test query")
                # If it returns a response, it should be user-friendly
                assert response.answer
                assert 'Retrieval Error' not in response.answer
                print(f"✅ Retriever failure handled gracefully")
            except Exception as e:
                # If it raises, should be a clean error
                assert 'Retrieval Error' in str(e)
                print(f"✅ Retriever failure raises clean error")


class TestResponseFormat:
    """Test 5: Response Format Test - Verify response structure"""
    
    def test_response_structure(self):
        """Test that response has expected structure"""
        generator = RAAMPGenerator()
        
        response = generator.generate_response("What is RAAMP?")
        
        # Check all expected attributes
        assert hasattr(response, 'query'), "Response should have 'query'"
        assert hasattr(response, 'answer'), "Response should have 'answer'"
        assert hasattr(response, 'context_used'), "Response should have 'context_used'"
        assert hasattr(response, 'sources'), "Response should have 'sources'"
        assert hasattr(response, 'model'), "Response should have 'model'"
        assert hasattr(response, 'created_at'), "Response should have 'created_at'"
        
        # Check types
        assert isinstance(response.query, str)
        assert isinstance(response.answer, str)
        assert isinstance(response.context_used, str)
        assert isinstance(response.sources, list)
        assert isinstance(response.model, str)
        assert isinstance(response.created_at, str)
        
        print(f"✅ Response structure test passed")
    
    def test_to_dict_method(self):
        """Test response can be converted to dictionary"""
        generator = RAAMPGenerator()
        
        response = generator.generate_response("What is RAAMP?")
        response_dict = response.to_dict()
        
        # Should be a dictionary
        assert isinstance(response_dict, dict)
        
        # Should contain expected keys
        expected_keys = ['query', 'answer', 'context_used', 'sources', 'model', 'created_at']
        for key in expected_keys:
            assert key in response_dict, f"Dictionary should contain '{key}'"
        
        print(f"✅ to_dict method test passed")
    
    def test_sources_format(self):
        """Test that sources have correct format"""
        generator = RAAMPGenerator()
        
        response = generator.generate_response("What is RAAMP?")
        
        if response.sources:
            for source in response.sources:
                # Each source should be a dictionary
                assert isinstance(source, dict)
                
                # Should have expected keys
                assert 'id' in source, "Source should have 'id'"
                assert 'question' in source, "Source should have 'question'"
                assert 'category' in source, "Source should have 'category'"
                assert 'relevance' in source, "Source should have 'relevance'"
        
        print(f"✅ Sources format test passed")


class TestPerformance:
    """Test 6: Performance Test - Verify response time"""
    
    def test_simple_query_performance(self):
        """Test response time for simple query"""
        generator = RAAMPGenerator()
        
        query = "What is RAAMP?"
        
        start_time = time.time()
        response = generator.generate_response(query)
        elapsed_time = time.time() - start_time
        
        assert response is not None
        assert response.answer
        
        # Should respond within 10 seconds (generous limit for API calls)
        assert elapsed_time < 10.0, \
            f"Response took too long: {elapsed_time:.2f}s (expected <10s)"
        
        print(f"✅ Performance test passed")
        print(f"   Response time: {elapsed_time:.2f}s")
    
    def test_retrieval_performance(self):
        """Test retrieval performance"""
        generator = RAAMPGenerator()
        
        start_time = time.time()
        docs = generator.retriever.retrieve("What is RAAMP?", n_results=5)
        elapsed_time = time.time() - start_time
        
        assert docs is not None
        assert len(docs) > 0
        
        # Retrieval should be reasonably fast (under 8 seconds accounting for network variability)
        assert elapsed_time < 8.0, \
            f"Retrieval took too long: {elapsed_time:.2f}s (expected <8s)"
        
        print(f"✅ Retrieval performance test passed")
        print(f"   Retrieval time: {elapsed_time:.2f}s")
    
    def test_conversation_performance(self):
        """Test conversation mode performance"""
        assistant = RAMPAssistant(session_id="perf-test")
        
        queries = [
            "Hello",
            "What is RAAMP?",
            "Tell me more"
        ]
        
        total_time = 0
        for query in queries:
            start_time = time.time()
            response = assistant.ask(query)
            elapsed_time = time.time() - start_time
            total_time += elapsed_time
            
            assert response
            assert response.get('answer')
        
        avg_time = total_time / len(queries)
        
        print(f"✅ Conversation performance test passed")
        print(f"   Average response time: {avg_time:.2f}s")
        print(f"   Total time: {total_time:.2f}s")


class TestConversationContext:
    """Test 7: Conversation Context - Verify history management"""
    
    def test_conversation_history(self):
        """Test that conversation history is maintained"""
        assistant = RAMPAssistant(session_id="history-test")
        
        # First message
        response1 = assistant.ask("My name is John")
        assert response1.get('answer')
        
        # Second message referring to first
        response2 = assistant.ask("What is my name?")
        assert response2.get('answer')
        
        # Check history length
        history = assistant.get_conversation_history()
        assert len(history) >= 4, "Should have at least 4 messages (2 exchanges)"
        
        print(f"✅ Conversation history test passed")
        print(f"   History length: {len(history)} messages")
    
    def test_history_reset(self):
        """Test conversation history can be reset"""
        assistant = RAMPAssistant(session_id="reset-test")
        
        # Add some messages
        assistant.ask("Hello")
        assistant.ask("What is RAAMP?")
        
        # Check history exists
        history_before = assistant.get_conversation_history()
        assert len(history_before) > 0
        
        # Reset
        assistant.reset_conversation()
        
        # Check history is cleared
        history_after = assistant.get_conversation_history()
        assert len(history_after) == 0, "History should be empty after reset"
        
        print(f"✅ History reset test passed")


# Optional: Run tests directly
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("COMPREHENSIVE RAG CHATBOT TEST SUITE")
    print("=" * 70)
    
    # Check prerequisites
    if not os.getenv("OPENAI_API_KEY"):
        print("\n❌ ERROR: OPENAI_API_KEY not found in environment")
        print("Please set your OpenAI API key in .env file")
        exit(1)
    
    print("\n🧪 Running tests...\n")
    
    # Run pytest
    pytest.main([__file__, "-v", "-s"])
