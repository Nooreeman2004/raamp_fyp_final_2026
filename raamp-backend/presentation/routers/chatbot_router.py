"""
Chatbot Router
==============
FastAPI router for the RAAMP Assistant chatbot endpoints.
Handles chat requests, session management, and health checks.
"""

import uuid
import re
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from datetime import datetime
import base64
import os
from openai import OpenAI

from presentation.schemas.chatbot_schema import (
    ChatRequest,
    ChatResponse,
    ChatSource,
    SessionResetRequest,
    SessionResetResponse,
    ConversationHistoryResponse,
    ChatMessage,
    ChatHealthResponse,
    ChatStatsResponse,
    DiagnosticRequest,
    DiagnosticResponse
)
from application.services.rag.raamp_generation import RAAMPGenerator
from application.services.rag.conversation_manager import (
    get_conversation_manager,
    ConversationManager
)
from application.services.diagnostics_service import DiagnosticsService

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

# Lazy initialization of generator (singleton)
_generator: Optional[RAAMPGenerator] = None
_diagnostics_service: Optional[DiagnosticsService] = None

# Quick responses for common greetings/phrases (no AI needed)
QUICK_RESPONSES = {
    # Greetings
    "greetings": {
        "patterns": [r"^(hi|hello|hey|hola|greetings|howdy|sup|yo)[\s!?.]*$"],
        "responses": [
            "Hello! 👋 I'm your RAAMP Assistant. How can I help you with your marketing campaigns today?",
            "Hi there! 👋 Ready to help with RAAMP or marketing questions. What would you like to know?",
            "Hey! 👋 Welcome to RAAMP Assistant. What can I assist you with?"
        ]
    },
    # Thank you
    "thanks": {
        "patterns": [r"^(thanks|thank you|thx|ty|thank u|cheers)[\s!?.]*$"],
        "responses": [
            "You're welcome! 😊 Let me know if you need anything else.",
            "Happy to help! 😊 Feel free to ask if you have more questions.",
            "Anytime! 😊 I'm here if you need more assistance."
        ]
    },
    # Goodbye
    "goodbye": {
        "patterns": [r"^(bye|goodbye|see ya|later|cya|ttyl)[\s!?.]*$"],
        "responses": [
            "Goodbye! 👋 Best of luck with your campaigns!",
            "Take care! 👋 Come back anytime you need help.",
            "See you later! 👋 Good luck with your marketing!"
        ]
    },
    # How are you
    "howru": {
        "patterns": [r"^(how are you|how r u|hru|how's it going|wassup|what's up)[\s!?.]*$"],
        "responses": [
            "I'm doing great, thanks for asking! 🌟 Ready to help with your RAAMP questions!",
            "All systems running smoothly! 🚀 How can I assist you today?",
            "Fantastic! 💫 What marketing challenges can I help you tackle?"
        ]
    },
    # What can you do
    "capabilities": {
        "patterns": [r"^(what can you do|help|what do you do|your capabilities)[\s!?.]*$"],
        "responses": [
            "I'm your RAAMP Assistant! 🎯 I can help you with:\n• Campaign optimization tips\n• Platform features & setup\n• Marketing strategy advice\n• Troubleshooting issues\n• Understanding analytics\n\nJust ask me anything!",
        ]
    },
    # What is RAAMP
    "whatisraamp": {
        "patterns": [r"^(what is raamp|what's raamp|whats raamp)[\s!?.]*$"],
        "responses": [
            "RAAMP stands for **Revolutionary AI-Powered Autonomous Marketing Platform**! 🚀\n\nIt's an intelligent marketing platform that helps SMBs automate their digital marketing using AI-driven insights, geo-intent targeting, and hyperlocal strategies.\n\nWant to know more about any specific feature?"
        ]
    }
}


def get_quick_response(message: str) -> Optional[str]:
    """Check if message matches a quick response pattern."""
    import random
    message_lower = message.lower().strip()
    
    for category, data in QUICK_RESPONSES.items():
        for pattern in data["patterns"]:
            if re.match(pattern, message_lower, re.IGNORECASE):
                return random.choice(data["responses"])
    return None

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

def get_diagnostics() -> DiagnosticsService:
    global _diagnostics_service
    if _diagnostics_service is None:
        _diagnostics_service = DiagnosticsService()
    return _diagnostics_service


def generate_session_id() -> str:
    """Generate a unique session ID."""
    return f"session-{uuid.uuid4().hex[:12]}"


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    manager: ConversationManager = Depends(get_manager),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    Send a message and receive a response from the RAAMP Assistant.
    """
    try:
        # Get or create session ID
        session_id = request.session_id or generate_session_id()

        # Check for quick response first (no AI needed for greetings)
        quick_answer = get_quick_response(request.message)

        # Try to fetch history, but don't fail chat if DB/session is unhappy
        history = []
        try:
            history = await manager.get_history_for_llm(session_id, limit=10)
        except Exception as history_err:
            print(f"⚠️ Failed to load chat history for session {session_id}: {history_err}")

        if quick_answer:
            # Store messages in session (best-effort only)
            try:
                await manager.add_message(session_id, "user", request.message, x_user_id)
                await manager.add_message(session_id, "assistant", quick_answer, x_user_id)
            except Exception as store_err:
                print(f"⚠️ Failed to store quick-response messages for session {session_id}: {store_err}")

            # 🎙️ GENERATE TTS for quick response
            audio_base64 = None
            try:
                client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                response_tts = client.audio.speech.create(
                    model="tts-1",
                    voice="alloy",
                    input=quick_answer
                )
                audio_base64 = base64.b64encode(response_tts.content).decode('utf-8')
            except Exception as tts_err:
                print(f"⚠️ TTS Error: {tts_err}")

            return ChatResponse(
                answer=quick_answer,
                session_id=session_id,
                sources=None,
                timestamp=datetime.utcnow().isoformat(),
                audio_content=audio_base64
            )

        # For complex questions, use RAG pipeline
        generator = get_generator()

        # PROMPT ENGINEERING WITH CONTEXT
        query = request.message
        if request.context:
            page = request.context.get("current_page", "unknown")
            query = f"[User Context: Current Page: {page}] {request.message}"

        # Generate response using RAG
        response = generator.chat(
            query=query,
            conversation_history=history,
            n_context=5
        )

        # Store messages in session (best-effort only)
        try:
            await manager.add_message(session_id, "user", request.message, x_user_id)
            await manager.add_message(session_id, "assistant", response["answer"], x_user_id)
        except Exception as store_err:
            print(f"⚠️ Failed to store messages for session {session_id}: {store_err}")
        
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
        
        # 🎙️ GENERATE TTS (Text-to-Speech)
        audio_base64 = None
        try:
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response_tts = client.audio.speech.create(
                model="tts-1",
                voice="alloy", # Options: alloy, echo, fable, onyx, nova, shimmer
                input=response["answer"][:4096] # OpenAI TTS limit
            )
            # Convert audio stream to base64
            audio_base64 = base64.b64encode(response_tts.content).decode('utf-8')
        except Exception as tts_err:
            print(f"⚠️ TTS Error: {tts_err}")
            # Non-critical error, just log and continue without audio

        return ChatResponse(
            answer=response["answer"],
            session_id=session_id,
            sources=sources,
            timestamp=datetime.utcnow().isoformat(),
            audio_content=audio_base64
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
    """
    success = await manager.clear_session(request.session_id)
    
    return SessionResetResponse(
        success=success,
        session_id=request.session_id,
        message="Session reset successfully" if success else "Session not found"
    )

@router.post("/diagnostics/run", response_model=DiagnosticResponse)
async def run_diagnostic(
    request: DiagnosticRequest,
    diagnostics: DiagnosticsService = Depends(get_diagnostics),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    Run a specific diagnostic check.
    """
    result = await diagnostics.run_check(request.check_id, x_user_id)
    
    return DiagnosticResponse(
        status=result.get("status", "failed"),
        message=result.get("message", "Check failed"),
        details=result.get("details", "")
    )


@router.get("/history/{session_id}", response_model=ConversationHistoryResponse)
async def get_history(
    session_id: str,
    limit: Optional[int] = None,
    manager: ConversationManager = Depends(get_manager)
):
    """
    Get the conversation history for a session.
    """
    messages = await manager.get_history(session_id, limit)
    
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
    """
    success = await manager.delete_session(session_id)
    
    return {
        "success": success,
        "session_id": session_id,
        "message": "Session deleted" if success else "Session not found"
    }
