"""
Chatbot Router
==============
FastAPI router for the RAAMP Assistant chatbot endpoints.
Handles chat requests, session management, and health checks.
"""

import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from datetime import datetime

from presentation.schemas.chatbot_schema import (
    ChatRequest,
    ChatResponse,
    ChatSource,
    SessionResetRequest,
    SessionResetResponse,
    ConversationHistoryResponse,
    ChatMessage,
    ChatHealthResponse,
    ChatStatsResponse
)
from application.services.rag.raamp_generation import RAAMPGenerator
from application.services.rag.conversation_manager import (
    get_conversation_manager,
    ConversationManager
)

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

# Lazy initialization of generator (singleton)
_generator: Optional[RAAMPGenerator] = None


def get_generator() -> RAAMPGenerator:
    """Get or create the RAG generator instance."""
    global _generator
    if _generator is None:
        try:
            _generator = RAAMPGenerator()
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Chatbot service unavailable: {str(e)}"
            )
    return _generator


def get_manager() -> ConversationManager:
    """Get the conversation manager instance."""
    return get_conversation_manager()


def generate_session_id() -> str:
    """Generate a unique session ID."""
    return f"session-{uuid.uuid4().hex[:12]}"


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    generator: RAAMPGenerator = Depends(get_generator),
    manager: ConversationManager = Depends(get_manager),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    Send a message and receive a response from the RAAMP Assistant.
    
    The chatbot uses RAG (Retrieval-Augmented Generation) to provide
    accurate answers based on the RAAMP FAQ knowledge base.
    
    - **message**: The user's question or message
    - **session_id**: Optional session ID for conversation continuity
    - **include_sources**: Whether to include source documents in response
    
    Returns the assistant's response with optional source documents.
    """
    try:
        # Get or create session ID
        session_id = request.session_id or generate_session_id()
        
        # Get conversation history for context
        history = manager.get_history_for_llm(session_id, limit=10)
        
        # Generate response using RAG
        response = generator.chat(
            query=request.message,
            conversation_history=history,
            n_context=5
        )
        
        # Store messages in session
        manager.add_message(session_id, "user", request.message, x_user_id)
        manager.add_message(session_id, "assistant", response["answer"], x_user_id)
        
        # Build response
        sources = None
        if request.include_sources and response.get("sources"):
            sources = [
                ChatSource(
                    id=src["id"],
                    question=src["question"],
                    category=src["category"],
                    relevance=src["relevance"]
                )
                for src in response["sources"]
            ]
        
        return ChatResponse(
            answer=response["answer"],
            session_id=session_id,
            sources=sources,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        print(f"❌ Chat error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(e)}"
        )


@router.post("/reset", response_model=SessionResetResponse)
async def reset_session(
    request: SessionResetRequest,
    manager: ConversationManager = Depends(get_manager)
):
    """
    Reset a chat session, clearing all conversation history.
    
    Use this when starting a new conversation topic or when
    the user wants to start fresh.
    """
    success = manager.clear_session(request.session_id)
    
    return SessionResetResponse(
        success=success,
        session_id=request.session_id,
        message="Session reset successfully" if success else "Session not found"
    )


@router.get("/history/{session_id}", response_model=ConversationHistoryResponse)
async def get_history(
    session_id: str,
    limit: Optional[int] = None,
    manager: ConversationManager = Depends(get_manager)
):
    """
    Get the conversation history for a session.
    
    - **session_id**: The session ID to retrieve history for
    - **limit**: Optional limit on number of messages to return
    """
    messages = manager.get_history(session_id, limit)
    
    return ConversationHistoryResponse(
        session_id=session_id,
        messages=[
            ChatMessage(
                role=msg["role"],
                content=msg["content"],
                timestamp=msg.get("timestamp")
            )
            for msg in messages
        ],
        message_count=len(messages)
    )


@router.get("/health", response_model=ChatHealthResponse)
async def health_check():
    """
    Check the health of the chatbot service.
    
    Returns the status of the RAG pipeline including:
    - LLM model availability
    - Vector store status
    - Number of documents in knowledge base
    - Active session count
    """
    try:
        generator = get_generator()
        manager = get_manager()
        
        health = generator.health_check()
        stats = manager.get_stats()
        
        retriever_stats = health.get("retriever", {})
        collection_stats = retriever_stats.get("collection_stats", {})
        
        return ChatHealthResponse(
            status=health.get("status", "unknown"),
            model=health.get("model"),
            retriever_status=retriever_stats.get("status", "unknown"),
            document_count=collection_stats.get("count", 0),
            active_sessions=stats.get("active_sessions", 0)
        )
        
    except Exception as e:
        return ChatHealthResponse(
            status="unhealthy",
            error=str(e)
        )


@router.get("/stats", response_model=ChatStatsResponse)
async def get_stats(
    generator: RAAMPGenerator = Depends(get_generator),
    manager: ConversationManager = Depends(get_manager)
):
    """
    Get statistics about the chatbot service.
    
    Returns metrics including active sessions, total messages,
    and knowledge base size.
    """
    try:
        manager_stats = manager.get_stats()
        retriever_health = generator.retriever.health_check()
        collection_stats = retriever_health.get("collection_stats", {})
        
        return ChatStatsResponse(
            active_sessions=manager_stats.get("active_sessions", 0),
            max_sessions=manager_stats.get("max_sessions", 1000),
            total_messages=manager_stats.get("total_messages", 0),
            document_count=collection_stats.get("count", 0),
            model=generator.model_name
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting stats: {str(e)}"
        )


@router.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    manager: ConversationManager = Depends(get_manager)
):
    """
    Delete a chat session entirely.
    
    Use this for cleanup or when a user logs out.
    """
    success = manager.delete_session(session_id)
    
    return {
        "success": success,
        "session_id": session_id,
        "message": "Session deleted" if success else "Session not found"
    }
