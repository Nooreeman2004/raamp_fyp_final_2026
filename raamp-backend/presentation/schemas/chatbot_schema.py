"""
Chatbot Schemas
===============
Pydantic schemas for the RAAMP Assistant chatbot API endpoints.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ChatMessage(BaseModel):
    """A single chat message."""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = Field(None, description="ISO timestamp of message")


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""
    message: str = Field(
        ..., 
        min_length=1, 
        max_length=2000,
        description="User's message/question"
    )
    session_id: Optional[str] = Field(
        None, 
        description="Session ID for conversation continuity. Generated if not provided."
    )
    include_sources: bool = Field(
        False, 
        description="Whether to include source documents in response"
    )
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Client context (e.g., current page, user ID) to assist the AI."
    )
    trend_id: Optional[str] = Field(
        None,
        description="Optional trend ID to link to this conversation session"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What is RAAMP?",
                "session_id": "user-123-abc",
                "include_sources": False,
                "context": {"current_page": "/dashboard/performance"}
            }
        }


class ChatSource(BaseModel):
    """Source document used to generate response."""
    id: str = Field(..., description="Document ID")
    question: str = Field(..., description="FAQ question")
    category: str = Field(..., description="FAQ category")
    relevance: float = Field(..., description="Relevance score (0-1)")


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    answer: str = Field(..., description="Assistant's response")
    session_id: str = Field(..., description="Session ID for conversation continuity")
    sources: Optional[List[ChatSource]] = Field(
        None, 
        description="Source documents used (if include_sources=True)"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Response timestamp"
    )
    audio_content: Optional[str] = Field(
        None, 
        description="Base64 encoded TTS audio content"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "RAAMP stands for Revolutionary AI-Powered Autonomous Marketing Platform...",
                "session_id": "user-123-abc",
                "sources": [
                    {
                        "id": "FAQ001",
                        "question": "What is RAAMP?",
                        "category": "General",
                        "relevance": 0.95
                    }
                ],
                "timestamp": "2025-12-02T10:30:00.000Z"
            }
        }


class SessionResetRequest(BaseModel):
    """Request to reset a chat session."""
    session_id: str = Field(..., description="Session ID to reset")


class SessionResetResponse(BaseModel):
    """Response from session reset."""
    success: bool = Field(..., description="Whether reset was successful")
    session_id: str = Field(..., description="Session ID that was reset")
    message: str = Field(..., description="Status message")


class ConversationHistoryResponse(BaseModel):
    """Response with conversation history."""
    session_id: str = Field(..., description="Session ID")
    messages: List[ChatMessage] = Field(..., description="List of messages")
    message_count: int = Field(..., description="Total message count")


class ChatHealthResponse(BaseModel):
    """Health check response for chatbot service."""
    status: str = Field(..., description="Service status: 'healthy' or 'unhealthy'")
    model: Optional[str] = Field(None, description="LLM model being used")
    retriever_status: Optional[str] = Field(None, description="Retriever health status")
    document_count: Optional[int] = Field(None, description="Number of documents in knowledge base")
    active_sessions: Optional[int] = Field(None, description="Number of active chat sessions")
    error: Optional[str] = Field(None, description="Error message if unhealthy")


class ChatStatsResponse(BaseModel):
    """Statistics about the chatbot service."""
    active_sessions: int = Field(..., description="Number of active sessions")
    max_sessions: int = Field(..., description="Maximum allowed sessions")
    total_messages: int = Field(..., description="Total messages across all sessions")
    document_count: int = Field(..., description="Documents in knowledge base")
    model: str = Field(..., description="LLM model being used")

class DiagnosticRequest(BaseModel):
    """Request to run a specific diagnostic check."""
    check_id: str = Field(..., description="ID of the check to run")
    session_id: Optional[str] = None

class DiagnosticResponse(BaseModel):
    """Response from a diagnostic check."""
    status: str = Field(..., description="success, warning, or failed")
    message: str = Field(..., description="Short status message")
    details: str = Field(..., description="Detailed explanation")
