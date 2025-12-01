"""
Chatbot API Tests
=================
Tests for the RAAMP Assistant chatbot API endpoints.
Tests the FastAPI router, schemas, and integration with RAG components.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from main import app
    return TestClient(app)


class TestChatbotSchemas:
    """Tests for chatbot Pydantic schemas."""
    
    def test_chat_request_valid(self):
        """Test valid chat request schema."""
        from presentation.schemas.chatbot_schema import ChatRequest
        
        request = ChatRequest(
            message="What is RAAMP?",
            session_id="test-session",
            include_sources=True
        )
        
        assert request.message == "What is RAAMP?"
        assert request.session_id == "test-session"
        assert request.include_sources is True
    
    def test_chat_request_minimal(self):
        """Test minimal chat request (only required fields)."""
        from presentation.schemas.chatbot_schema import ChatRequest
        
        request = ChatRequest(message="Hello")
        
        assert request.message == "Hello"
        assert request.session_id is None
        assert request.include_sources is False
    
    def test_chat_request_empty_message_fails(self):
        """Test that empty message fails validation."""
        from presentation.schemas.chatbot_schema import ChatRequest
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            ChatRequest(message="")
    
    def test_chat_response_structure(self):
        """Test chat response schema structure."""
        from presentation.schemas.chatbot_schema import ChatResponse
        
        response = ChatResponse(
            answer="RAAMP is a marketing platform.",
            session_id="test-session"
        )
        
        assert response.answer == "RAAMP is a marketing platform."
        assert response.session_id == "test-session"
        assert response.timestamp is not None


class TestChatEndpoint:
    """Tests for the /api/chatbot/chat endpoint."""
    
    def test_chat_endpoint_success(self, client):
        """Test successful chat request."""
        response = client.post(
            "/api/chatbot/chat",
            json={
                "message": "What is RAAMP?",
                "session_id": "test-session-1"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "answer" in data
        assert "session_id" in data
        assert len(data["answer"]) > 0
    
    def test_chat_endpoint_generates_session_id(self, client):
        """Test that session_id is generated if not provided."""
        response = client.post(
            "/api/chatbot/chat",
            json={"message": "Hello!"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "session_id" in data
        assert data["session_id"].startswith("session-")
    
    def test_chat_endpoint_with_sources(self, client):
        """Test chat request with sources included."""
        response = client.post(
            "/api/chatbot/chat",
            json={
                "message": "What is RAAMP?",
                "include_sources": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "sources" in data
        # Sources may be None if no relevant docs found
        if data["sources"]:
            assert isinstance(data["sources"], list)
    
    def test_chat_endpoint_maintains_context(self, client):
        """Test that conversation context is maintained."""
        session_id = "context-test-session"
        
        # First message
        response1 = client.post(
            "/api/chatbot/chat",
            json={
                "message": "What is RAAMP?",
                "session_id": session_id
            }
        )
        assert response1.status_code == 200
        
        # Follow-up message
        response2 = client.post(
            "/api/chatbot/chat",
            json={
                "message": "Tell me more about it",
                "session_id": session_id
            }
        )
        assert response2.status_code == 200
        
        # Verify same session
        assert response1.json()["session_id"] == response2.json()["session_id"]
    
    def test_chat_endpoint_invalid_request(self, client):
        """Test chat with invalid request body."""
        response = client.post(
            "/api/chatbot/chat",
            json={}  # Missing required 'message' field
        )
        
        assert response.status_code == 422  # Validation error


class TestSessionEndpoints:
    """Tests for session management endpoints."""
    
    def test_reset_session(self, client):
        """Test resetting a chat session."""
        # First, create a session with some messages
        session_id = "reset-test-session"
        client.post(
            "/api/chatbot/chat",
            json={
                "message": "Hello!",
                "session_id": session_id
            }
        )
        
        # Reset the session
        response = client.post(
            "/api/chatbot/reset",
            json={"session_id": session_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["session_id"] == session_id
    
    def test_get_history(self, client):
        """Test getting conversation history."""
        session_id = "history-test-session"
        
        # Create some conversation
        client.post(
            "/api/chatbot/chat",
            json={
                "message": "What is RAAMP?",
                "session_id": session_id
            }
        )
        
        # Get history
        response = client.get(f"/api/chatbot/history/{session_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "messages" in data
        assert "message_count" in data
        assert data["session_id"] == session_id
    
    def test_delete_session(self, client):
        """Test deleting a session."""
        session_id = "delete-test-session"
        
        # Create session
        client.post(
            "/api/chatbot/chat",
            json={
                "message": "Hello!",
                "session_id": session_id
            }
        )
        
        # Delete session
        response = client.delete(f"/api/chatbot/session/{session_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True


class TestHealthAndStats:
    """Tests for health check and stats endpoints."""
    
    def test_health_check(self, client):
        """Test chatbot health check endpoint."""
        response = client.get("/api/chatbot/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
    
    def test_stats_endpoint(self, client):
        """Test chatbot stats endpoint."""
        response = client.get("/api/chatbot/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "active_sessions" in data
        assert "model" in data


class TestGuardrails:
    """Tests for chatbot guardrails and safety."""
    
    def test_off_topic_question_handled(self, client):
        """Test that off-topic questions are handled gracefully."""
        response = client.post(
            "/api/chatbot/chat",
            json={"message": "What is the capital of France?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have an answer (guardrail response)
        assert len(data["answer"]) > 0
        # Should politely decline or redirect
        answer_lower = data["answer"].lower()
        assert any(word in answer_lower for word in ["sorry", "cannot", "raamp", "documentation"])
    
    def test_greeting_handled(self, client):
        """Test that greetings are handled warmly."""
        response = client.post(
            "/api/chatbot/chat",
            json={"message": "Hi there!"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have a friendly response
        assert len(data["answer"]) > 0


class TestConcurrency:
    """Tests for concurrent request handling."""
    
    def test_multiple_sessions(self, client):
        """Test handling multiple concurrent sessions."""
        sessions = [f"concurrent-session-{i}" for i in range(5)]
        
        for session_id in sessions:
            response = client.post(
                "/api/chatbot/chat",
                json={
                    "message": "What is RAAMP?",
                    "session_id": session_id
                }
            )
            assert response.status_code == 200
        
        # Verify all sessions exist
        for session_id in sessions:
            response = client.get(f"/api/chatbot/history/{session_id}")
            assert response.status_code == 200


def test_integration_full_conversation(client):
    """Integration test for a full conversation flow."""
    session_id = "integration-test-session"
    
    # Start conversation
    messages = [
        "Hello!",
        "What is RAAMP?",
        "How do I get started?",
        "What are the main features?"
    ]
    
    for msg in messages:
        response = client.post(
            "/api/chatbot/chat",
            json={
                "message": msg,
                "session_id": session_id
            }
        )
        assert response.status_code == 200
        assert len(response.json()["answer"]) > 0
    
    # Check history
    history_response = client.get(f"/api/chatbot/history/{session_id}")
    assert history_response.status_code == 200
    
    history = history_response.json()
    assert history["message_count"] == len(messages) * 2  # User + Assistant messages
    
    # Cleanup
    client.delete(f"/api/chatbot/session/{session_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
