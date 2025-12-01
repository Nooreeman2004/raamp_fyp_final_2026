"""
RAG Pipeline Tests
==================
Tests for the RAAMP RAG (Retrieval-Augmented Generation) pipeline.
Tests chunking, vector store, retriever, and generator components.
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()


class TestFAQChunker:
    """Tests for the FAQ chunking component."""
    
    def test_chunker_initialization(self):
        """Test that chunker initializes correctly."""
        from application.services.rag.raamp_chunking import FAQChunker
        
        chunker = FAQChunker()
        assert chunker is not None
        assert chunker.faq_path is not None
    
    def test_chunk_faqs_returns_list(self):
        """Test that chunk_faqs returns a list of chunks."""
        from application.services.rag.raamp_chunking import FAQChunker
        
        chunker = FAQChunker()
        chunks = chunker.chunk_faqs()
        
        assert isinstance(chunks, list)
        assert len(chunks) > 0
    
    def test_chunk_has_required_fields(self):
        """Test that each chunk has required fields."""
        from application.services.rag.raamp_chunking import FAQChunker
        
        chunker = FAQChunker()
        chunks = chunker.chunk_faqs()
        
        required_fields = ["id", "question", "answer", "category"]
        
        for chunk in chunks[:5]:  # Check first 5
            for field in required_fields:
                assert field in chunk, f"Missing field: {field}"
    
    def test_save_and_load_chunks(self):
        """Test saving and loading chunks."""
        from application.services.rag.raamp_chunking import FAQChunker
        
        chunker = FAQChunker()
        chunks = chunker.chunk_faqs()
        output_path = chunker.save_chunks()
        
        assert os.path.exists(output_path)
        
        # Load and verify
        loaded = chunker.load_chunks()
        assert len(loaded) == len(chunks)
    
    def test_get_statistics(self):
        """Test statistics generation."""
        from application.services.rag.raamp_chunking import FAQChunker
        
        chunker = FAQChunker()
        chunker.chunk_faqs()
        stats = chunker.get_statistics()
        
        assert "total_chunks" in stats
        assert "categories" in stats
        assert stats["total_chunks"] > 0


class TestRAAMPRetriever:
    """Tests for the RAAMP retriever component."""
    
    @pytest.fixture
    def retriever(self):
        """Create a retriever instance for testing."""
        from application.services.rag.raamp_retriever import RAAMPRetriever
        return RAAMPRetriever()
    
    def test_retriever_initialization(self, retriever):
        """Test retriever initializes correctly."""
        assert retriever is not None
        assert retriever.collection_name == "raamp_faq_collection"
        assert retriever.n_results > 0
    
    def test_retrieve_returns_list(self, retriever):
        """Test that retrieve returns a list."""
        results = retriever.retrieve("What is RAAMP?", n_results=3)
        
        assert isinstance(results, list)
    
    def test_retrieve_with_context_returns_string(self, retriever):
        """Test that retrieve_with_context returns formatted string."""
        context = retriever.retrieve_with_context("What is RAAMP?", n_results=3)
        
        assert isinstance(context, str)
    
    def test_health_check(self, retriever):
        """Test health check functionality."""
        health = retriever.health_check()
        
        assert "status" in health
        assert health["status"] in ["healthy", "unhealthy"]
    
    def test_get_collection_stats(self, retriever):
        """Test collection stats retrieval."""
        stats = retriever.get_collection_stats()
        
        assert isinstance(stats, dict)


class TestRAAMPGenerator:
    """Tests for the RAAMP generator component."""
    
    @pytest.fixture
    def generator(self):
        """Create a generator instance for testing."""
        from application.services.rag.raamp_generation import RAAMPGenerator
        return RAAMPGenerator()
    
    def test_generator_initialization(self, generator):
        """Test generator initializes correctly."""
        assert generator is not None
        assert generator.model_name is not None
        assert generator.retriever is not None
    
    def test_generate_response_structure(self, generator):
        """Test response structure."""
        from application.services.rag.raamp_generation import RAGResponse
        
        response = generator.generate_response("What is RAAMP?")
        
        assert isinstance(response, RAGResponse)
        assert response.query == "What is RAAMP?"
        assert isinstance(response.answer, str)
        assert len(response.answer) > 0
    
    def test_generate_simple(self, generator):
        """Test simple generation interface."""
        answer = generator.generate_simple("What is RAAMP?")
        
        assert isinstance(answer, str)
        assert len(answer) > 0
    
    def test_chat_with_history(self, generator):
        """Test chat interface with history."""
        result = generator.chat("Hello!")
        
        assert "answer" in result
        assert "conversation_history" in result
        assert len(result["conversation_history"]) == 2  # User + Assistant
    
    def test_guardrail_for_off_topic(self, generator):
        """Test that off-topic questions trigger guardrail."""
        response = generator.generate_response("What is the capital of France?")
        
        # Should contain a polite refusal or redirect
        assert "sorry" in response.answer.lower() or "cannot" in response.answer.lower() or "RAAMP" in response.answer
    
    def test_health_check(self, generator):
        """Test health check functionality."""
        health = generator.health_check()
        
        assert "status" in health
        assert health["status"] in ["healthy", "unhealthy"]


class TestRAMPAssistant:
    """Tests for the high-level RAAMP Assistant interface."""
    
    @pytest.fixture
    def assistant(self):
        """Create an assistant instance for testing."""
        from application.services.rag.raamp_generation import RAMPAssistant
        return RAMPAssistant(session_id="test-session")
    
    def test_assistant_initialization(self, assistant):
        """Test assistant initializes correctly."""
        assert assistant is not None
        assert assistant.session_id == "test-session"
        assert assistant.generator is not None
    
    def test_ask_returns_dict(self, assistant):
        """Test that ask returns a dictionary with answer."""
        result = assistant.ask("What is RAAMP?")
        
        assert isinstance(result, dict)
        assert "answer" in result
        assert isinstance(result["answer"], str)
    
    def test_conversation_history_builds(self, assistant):
        """Test that conversation history builds correctly."""
        assistant.ask("Hello!")
        assistant.ask("What is RAAMP?")
        
        history = assistant.get_conversation_history()
        
        assert len(history) == 4  # 2 questions + 2 answers
    
    def test_reset_conversation(self, assistant):
        """Test conversation reset."""
        assistant.ask("Hello!")
        assistant.reset_conversation()
        
        assert assistant.get_conversation_length() == 0


class TestConversationManager:
    """Tests for the conversation manager."""
    
    @pytest.fixture
    def manager(self):
        """Create a conversation manager for testing."""
        from application.services.rag.conversation_manager import ConversationManager
        return ConversationManager(max_sessions=10, session_timeout_minutes=1)
    
    def test_manager_initialization(self, manager):
        """Test manager initializes correctly."""
        assert manager is not None
        assert manager.max_sessions == 10
    
    def test_create_session(self, manager):
        """Test session creation."""
        session = manager.get_or_create_session("test-user-1")
        
        assert session is not None
        assert session.session_id == "test-user-1"
    
    def test_add_message(self, manager):
        """Test adding messages to session."""
        manager.add_message("test-user-1", "user", "Hello!")
        manager.add_message("test-user-1", "assistant", "Hi there!")
        
        history = manager.get_history("test-user-1")
        
        assert len(history) == 2
    
    def test_clear_session(self, manager):
        """Test clearing a session."""
        manager.add_message("test-user-1", "user", "Hello!")
        manager.clear_session("test-user-1")
        
        history = manager.get_history("test-user-1")
        
        assert len(history) == 0
    
    def test_delete_session(self, manager):
        """Test deleting a session."""
        manager.get_or_create_session("test-user-1")
        success = manager.delete_session("test-user-1")
        
        assert success is True
        assert manager.get_session("test-user-1") is None
    
    def test_get_stats(self, manager):
        """Test getting manager stats."""
        manager.get_or_create_session("user-1")
        manager.get_or_create_session("user-2")
        
        stats = manager.get_stats()
        
        assert stats["active_sessions"] == 2
    
    def test_max_sessions_limit(self, manager):
        """Test that max sessions limit is enforced."""
        # Create more than max_sessions
        for i in range(15):
            manager.get_or_create_session(f"user-{i}")
        
        assert manager.get_session_count() <= manager.max_sessions


def test_integration_full_rag_flow():
    """Integration test for the complete RAG flow."""
    from application.services.rag.raamp_generation import RAMPAssistant
    
    assistant = RAMPAssistant(session_id="integration-test")
    
    # Test a series of questions
    questions = [
        "What is RAAMP?",
        "How do I get started?",
        "What features does it have?"
    ]
    
    for q in questions:
        result = assistant.ask(q)
        assert "answer" in result
        assert len(result["answer"]) > 0
    
    # Verify conversation built up
    assert assistant.get_conversation_length() == len(questions) * 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
