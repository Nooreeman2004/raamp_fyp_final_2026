"""
RAAMP Conversation Manager
==========================
Session-based conversation memory management using Persistent MongoDB Storage.
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

# Repository Imports
from infrastructure.repositories.chat_repository_impl import ChatRepository
from application.services.chat_analytics_service import ChatAnalyticsService

class ConversationManager:
    """
    Persistent conversation manager.
    Delegates storage to ChatRepository (MongoDB) and logging to ChatAnalyticsService.
    """
    
    def __init__(self):
        """
        Initialize the conversation manager with persistent backend.
        """
        self.repository = ChatRepository()
        self.analytics = ChatAnalyticsService()
        
        print(f"✅ Persistent Conversation Manager initialized (MongoDB)")

    async def get_or_create_session(self, session_id: str, user_id: str = None) -> Dict:
        """
        Get existing session or create new one in DB.
        Note: This is now async.
        """
        session = await self.repository.get_session(session_id)
        if not session:
            session = await self.repository.create_session(session_id, user_id)
            
            # Log new session
            await self.analytics.log_interaction(
                session_id=session_id,
                event_type="session_start",
                user_id=user_id,
                content_summary="New session started"
            )
            
        return session

    async def add_message(self, session_id: str, role: str, content: str, user_id: str = None) -> Dict:
        """
        Add persistent message to database.
        """
        result = await self.repository.add_message(session_id, role, content)
        
        # Log analytics asynchronously (fire and forget)
        asyncio.create_task(self.analytics.log_interaction(
            session_id=session_id,
            user_id=user_id,
            event_type="message",
            content_summary=content[:50] + "..." if len(content) > 50 else content,
            metadata={"role": role}
        ))
        
        return result

    async def get_history(self, session_id: str, limit: int = None) -> List[Dict]:
        """
        Get history from DB.
        """
        history = await self.repository.get_history(session_id, limit)
        return history

    async def get_history_for_llm(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        Get formatted history for LLM context.
        """
        history = await self.repository.get_history(session_id, limit)
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in history
        ]

    async def clear_session(self, session_id: str) -> bool:
        """
        Clear messages from DB.
        """
        return await self.repository.clear_history(session_id)

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete session entirely.
        """
        return await self.repository.delete_session(session_id)

    async def link_trend(self, session_id: str, trend_id: str) -> bool:
        """
        Link a trend ID to a session.
        """
        return await self.repository.link_trend(session_id, trend_id)

    async def get_session(self, session_id: str):
        """
        Get the session document from the repository.
        """
        return await self.repository.get_session(session_id)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get stats (simplified for now since counting all DB records is expensive).
        """
        return {
            "storage": "persistent (MongoDB)",
            "status": "online"
        }

# Global instance
_conversation_manager: Optional[ConversationManager] = None

def get_conversation_manager() -> ConversationManager:
    """Get the global conversation manager instance."""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager
