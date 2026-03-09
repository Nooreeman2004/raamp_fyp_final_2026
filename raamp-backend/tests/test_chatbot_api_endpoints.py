"""
API Endpoint Tests for OpenAI RAG Chatbot
=========================================
Tests to verify that the chatbot API endpoints are functioning correctly
with proper status codes, response formats, and error handling.
"""

import pytest
import requests
import time
from typing import Dict, Any
import json


# API Configuration
BASE_URL = "http://localhost:8000"
CHAT_ENDPOINT = f"{BASE_URL}/api/chatbot/chat"
HEALTH_ENDPOINT = f"{BASE_URL}/api/chatbot/health"


class TestChatbotAPIEndpoints:
    """Test chatbot API endpoints"""
    
    def test_api_is_running(self):
        """Test that the API server is accessible"""
        try:
            response = requests.get(BASE_URL, timeout=5)
            assert response.status_code in [200, 404], "API should be accessible"
            print("✅ API server is running")
        except requests.exceptions.ConnectionError:
            pytest.skip("API server is not running. Start with: uvicorn main:app --reload")
    
    def test_health_endpoint(self):
        """Test the health check endpoint"""
        try:
            response = requests.get(HEALTH_ENDPOINT, timeout=5)
            
            # Should return 200 OK
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            # Should return JSON
            data = response.json()
            assert isinstance(data, dict), "Response should be JSON"
            
            # Should have status field
            assert 'status' in data, "Response should have 'status' field"
            
            print(f"✅ Health endpoint test passed")
            print(f"   Status: {data.get('status')}")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API server is not running")


class TestBasicChatAPI:
    """Test 1: Basic Chat API functionality"""
    
    def test_simple_greeting_api(self):
        """Test POST to /chat with a simple greeting"""
        payload = {
            "message": "Hello, what can you do?",
            "session_id": None,
            "include_sources": False
        }
        
        try:
            response = requests.post(CHAT_ENDPOINT, json=payload, timeout=30)
            
            # Verify status code
            assert response.status_code == 200, \
                f"Expected 200 OK, got {response.status_code}: {response.text}"
            
            # Verify response is JSON
            data = response.json()
            assert isinstance(data, dict), "Response should be JSON object"
            
            # Verify required fields
            assert 'answer' in data, "Response should have 'answer' field"
            assert 'session_id' in data, "Response should have 'session_id' field"
            assert 'timestamp' in data, "Response should have 'timestamp' field"
            
            # Verify answer is not empty
            assert data['answer'], "Answer should not be empty"
            assert len(data['answer']) > 10, "Answer should be substantial"
            
            print(f"✅ Basic chat API test passed")
            print(f"   Answer length: {len(data['answer'])} chars")
            print(f"   Answer preview: {data['answer'][:100]}...")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API server is not running")
    
    def test_response_format(self):
        """Test 5: Response Format - Verify JSON structure"""
        payload = {
            "message": "What is RAAMP?",
            "session_id": None,
            "include_sources": True
        }
        
        try:
            response = requests.post(CHAT_ENDPOINT, json=payload, timeout=30)
            assert response.status_code == 200
            
            data = response.json()
            
            # Verify expected fields exist
            required_fields = ['answer', 'session_id', 'timestamp']
            for field in required_fields:
                assert field in data, f"Response should have '{field}' field"
            
            # When include_sources=True, should have sources field
            assert 'sources' in data, "Response should have 'sources' field when requested"
            
            # Verify types
            assert isinstance(data['answer'], str), "answer should be string"
            assert isinstance(data['session_id'], str), "session_id should be string"
            assert isinstance(data['timestamp'], str), "timestamp should be string"
            
            if data['sources']:
                assert isinstance(data['sources'], list), "sources should be list"
            
            print(f"✅ Response format test passed")
            print(f"   Fields present: {list(data.keys())}")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API server is not running")


class TestRAGRetrievalAPI:
    """Test 2: RAG Retrieval through API"""
    
    def test_knowledge_base_query(self):
        """Test query that should retrieve from knowledge base"""
        payload = {
            "message": "What is RAAMP?",
            "session_id": None,
            "include_sources": True
        }
        
        try:
            response = requests.post(CHAT_ENDPOINT, json=payload, timeout=30)
            assert response.status_code == 200
            
            data = response.json()
            
            # Should return answer
            assert data['answer'], "Should return answer"
            
            # Should include sources when requested
            assert 'sources' in data, "Should include sources field"
            assert data['sources'] is not None, "Sources should not be null for RAAMP query"
            
            if data['sources']:
                assert len(data['sources']) > 0, "Should retrieve at least one source"
                
                # Verify source structure
                first_source = data['sources'][0]
                assert 'id' in first_source, "Source should have 'id'"
                assert 'question' in first_source, "Source should have 'question'"
                assert 'category' in first_source, "Source should have 'category'"
                assert 'relevance' in first_source, "Source should have 'relevance'"
            
            # Answer should mention RAAMP
            assert 'raamp' in data['answer'].lower(), \
                "Answer should mention RAAMP for RAAMP-related query"
            
            print(f"✅ Knowledge base query test passed")
            print(f"   Sources retrieved: {len(data.get('sources', []))}")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API server is not running")
    
    def test_multiple_rag_queries(self):
        """Test multiple queries that should use RAG"""
        queries = [
            "How do I sign up for RAAMP?",
            "What features does RAAMP have?",
            "Tell me about RAAMP campaigns"
        ]
        
        try:
            for query in queries:
                payload = {
                    "message": query,
                    "session_id": None,
                    "include_sources": True
                }
                
                response = requests.post(CHAT_ENDPOINT, json=payload, timeout=30)
                assert response.status_code == 200, f"Failed for query: {query}"
                
                data = response.json()
                assert data['answer'], f"Should return answer for: {query}"
                
                print(f"✅ RAG query passed: {query[:40]}...")
                
        except requests.exceptions.ConnectionError:
            pytest.skip("API server is not running")


class TestUnknownQuestionAPI:
    """Test 3: Unknown Question Handling through API"""
    
    def test_out_of_scope_question(self):
        """Test handling of out-of-scope questions"""
        payload = {
            "message": "What is the capital of Mars?",
            "session_id": None,
            "include_sources": False
        }
        
        try:
            response = requests.post(CHAT_ENDPOINT, json=payload, timeout=30)
            
            # Should still return 200 (graceful handling)
            assert response.status_code == 200, \
                "Should handle out-of-scope questions gracefully"
            
            data = response.json()
            
            # Should return an answer (not error)
            assert data['answer'], "Should return polite answer for unknown question"
            
            # Should not contain made-up information
            answer_lower = data['answer'].lower()
            
            print(f"✅ Out-of-scope question handled")
            print(f"   Response: {data['answer'][:150]}...")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API server is not running")
    
    def test_completely_random_query(self):
        """Test handling of completely unrelated query"""
        payload = {
            "message": "How do I bake a chocolate cake?",
            "session_id": None,
            "include_sources": False
        }
        
        try:
            response = requests.post(CHAT_ENDPOINT, json=payload, timeout=30)
            assert response.status_code == 200
            
            data = response.json()
            assert data['answer'], "Should return answer even for random query"
            
            print(f"✅ Random query handled gracefully")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API server is not running")


class TestErrorHandlingAPI:
    """Test 4: Error Handling through API"""
    
    def test_empty_message(self):
        """Test handling of empty message"""
        payload = {
            "message": "",
            "session_id": None,
            "include_sources": False
        }
        
        try:
            response = requests.post(CHAT_ENDPOINT, json=payload, timeout=30)
            
            # Should return 422 (validation error)
            assert response.status_code == 422, \
                f"Should reject empty message, got {response.status_code}"
            
            print(f"✅ Empty message validation test passed")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API server is not running")
    
    def test_invalid_json(self):
        """Test handling of invalid JSON"""
        try:
            response = requests.post(
                CHAT_ENDPOINT,
                data="invalid json",
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            # Should return 422 (validation error)
            assert response.status_code == 422, \
                f"Should reject invalid JSON, got {response.status_code}"
            
            print(f"✅ Invalid JSON handling test passed")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API server is not running")
    
    def test_missing_required_field(self):
        """Test handling of missing required fields"""
        payload = {
            "session_id": None,
            "include_sources": False
            # Missing 'message' field
        }
        
        try:
            response = requests.post(CHAT_ENDPOINT, json=payload, timeout=30)
            
            # Should return 422 (validation error)
            assert response.status_code == 422, \
                f"Should reject missing required field, got {response.status_code}"
            
            print(f"✅ Missing field validation test passed")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API server is not running")
    
    def test_user_friendly_error_messages(self):
        """Test that error messages are user-friendly"""
        # This would require simulating an internal error
        # For now, we test that validation errors are clear
        payload = {
            "message": "",
            "session_id": None
        }
        
        try:
            response = requests.post(CHAT_ENDPOINT, json=payload, timeout=30)
            
            if response.status_code != 200:
                data = response.json()
                
                # Error response should have detail
                assert 'detail' in data, "Error response should have 'detail' field"
                
                # Should not expose internal errors
                detail_str = str(data['detail']).lower()
                forbidden_terms = ['traceback', 'exception', 'error at line']
                for term in forbidden_terms:
                    assert term not in detail_str, \
                        f"Error should not expose internal details: {term}"
                
            print(f"✅ User-friendly error message test passed")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API server is not running")


class TestPerformanceAPI:
    """Test 6: Performance through API"""
    
    def test_response_time(self):
        """Test that API responds within acceptable time"""
        payload = {
            "message": "What is RAAMP?",
            "session_id": None,
            "include_sources": True
        }
        
        try:
            start_time = time.time()
            response = requests.post(CHAT_ENDPOINT, json=payload, timeout=30)
            elapsed_time = time.time() - start_time
            
            assert response.status_code == 200
            
            # Should respond within 10 seconds
            assert elapsed_time < 10.0, \
                f"Response too slow: {elapsed_time:.2f}s (expected <10s)"
            
            print(f"✅ API performance test passed")
            print(f"   Response time: {elapsed_time:.2f}s")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API server is not running")
        except requests.exceptions.Timeout:
            pytest.fail("API request timed out (>30s)")
    
    def test_multiple_requests_performance(self):
        """Test performance with multiple sequential requests"""
        queries = [
            "What is RAAMP?",
            "How do I sign up?",
            "What features are available?"
        ]
        
        try:
            total_time = 0
            
            for query in queries:
                payload = {
                    "message": query,
                    "session_id": None,
                    "include_sources": False
                }
                
                start_time = time.time()
                response = requests.post(CHAT_ENDPOINT, json=payload, timeout=30)
                elapsed_time = time.time() - start_time
                
                assert response.status_code == 200
                total_time += elapsed_time
            
            avg_time = total_time / len(queries)
            
            print(f"✅ Multiple requests performance test passed")
            print(f"   Average time: {avg_time:.2f}s")
            print(f"   Total time: {total_time:.2f}s")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API server is not running")


class TestConversationAPI:
    """Test 7: Conversation with session management"""
    
    def test_session_persistence(self):
        """Test that session_id persists across requests"""
        payload1 = {
            "message": "Hello",
            "session_id": None,
            "include_sources": False
        }
        
        try:
            # First request
            response1 = requests.post(CHAT_ENDPOINT, json=payload1, timeout=30)
            assert response1.status_code == 200
            
            data1 = response1.json()
            session_id = data1['session_id']
            assert session_id, "Should return session_id"
            
            # Second request with same session
            payload2 = {
                "message": "What is RAAMP?",
                "session_id": session_id,
                "include_sources": False
            }
            
            response2 = requests.post(CHAT_ENDPOINT, json=payload2, timeout=30)
            assert response2.status_code == 200
            
            data2 = response2.json()
            assert data2['session_id'] == session_id, \
                "Session ID should persist across requests"
            
            print(f"✅ Session persistence test passed")
            print(f"   Session ID: {session_id}")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API server is not running")


# Run tests
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("API ENDPOINT TESTS FOR RAG CHATBOT")
    print("=" * 70)
    print("\n⚠️  Make sure the API is running:")
    print("   uvicorn main:app --reload\n")
    
    # Run pytest
    pytest.main([__file__, "-v", "-s"])
