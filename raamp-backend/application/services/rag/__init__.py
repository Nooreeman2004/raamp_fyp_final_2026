"""
RAAMP RAG Module
================
Complete RAG (Retrieval-Augmented Generation) pipeline for the RAAMP Assistant.
Built with LangChain for optimized retrieval and generation.

Components:
- raamp_chunking: Processes FAQ data into chunks
- raamp_embeddings: Generates embeddings using OpenAI
- raamp_vector_store: ChromaDB vector storage
- raamp_retriever: LangChain-based semantic search and retrieval
- raamp_generation: LangChain-based LLM response generation
- conversation_manager: Multi-user session management
- raamp_pipeline: Full pipeline execution

Usage:
    from application.services.rag import RAMPAssistant
    
    assistant = RAMPAssistant(session_id="user-123")
    result = assistant.ask("What is RAAMP?")
    print(result["answer"])
"""

from .raamp_chunking import FAQChunker, FAQChunk
from .raamp_vector_store import ChromaVectorStore
from .raamp_embeddings import RAAMPEmbeddingGenerator, generate_query_embedding
from .raamp_retriever import RAAMPRetriever, RetrievedDocument
from .raamp_generation import RAAMPGenerator, RAMPAssistant, RAGResponse
from .conversation_manager import (
    ConversationManager, 
    ConversationSession,
    get_conversation_manager
)

__all__ = [
    # Chunking
    "FAQChunker",
    "FAQChunk",
    # Vector Store
    "ChromaVectorStore",
    # Embeddings
    "RAAMPEmbeddingGenerator",
    "generate_query_embedding",
    # Retriever
    "RAAMPRetriever",
    "RetrievedDocument",
    # Generation
    "RAAMPGenerator",
    "RAMPAssistant",
    "RAGResponse",
    # Conversation Management
    "ConversationManager",
    "ConversationSession",
    "get_conversation_manager",
]
