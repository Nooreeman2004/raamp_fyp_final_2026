"""
RAAMP Conversation Manager
==========================
Session-based conversation memory management for multi-user support.
Provides efficient storage and retrieval of conversation history.
"""

import os
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock
from collections import OrderedDict


@dataclass
class ConversationSession:
    """Represents a user conversation session."""
    session_id: str
    user_id: Optional[str]
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    messages: List[Dict[str, str]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.last_activity = datetime.utcnow()
    
    def get_messages(self, limit: int = None) -> List[Dict[str, str]]:
        """Get messages, optionally limited to the last N."""
        if limit:
            return self.messages[-limit:]
        return self.messages
    
    def get_message_count(self) -> int:
        """Get the number of messages in the conversation."""
        return len(self.messages)
    
    def clear(self):
        """Clear all messages from the conversation."""
        self.messages = []
        self.last_activity = datetime.utcnow()
    
    def is_expired(self, timeout_minutes: int = 60) -> bool:
        """Check if the session has expired."""
        expiry_time = self.last_activity + timedelta(minutes=timeout_minutes)
        return datetime.utcnow() > expiry_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "message_count": len(self.messages),
            "messages": self.messages,
            "metadata": self.metadata
        }


class ConversationManager:
    """
    Thread-safe conversation manager for multi-user chatbot sessions.
    Uses LRU cache to manage memory with automatic session expiry.
    """
    
    def __init__(self, 
                 max_sessions: int = 1000,
                 session_timeout_minutes: int = 60,
                 max_messages_per_session: int = 100):
        """
        Initialize the conversation manager.
        
        Args:
            max_sessions: Maximum number of concurrent sessions
            session_timeout_minutes: Session timeout in minutes
            max_messages_per_session: Maximum messages to keep per session
        """
        self.max_sessions = max_sessions
        self.session_timeout = session_timeout_minutes
        self.max_messages = max_messages_per_session
        
        # Thread-safe session storage (LRU-style)
        self._sessions: OrderedDict[str, ConversationSession] = OrderedDict()
        self._lock = Lock()
        
        # Cleanup interval tracking
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minutes
        
        print(f"✅ Conversation Manager initialized")
        print(f"   Max sessions: {max_sessions}")
        print(f"   Timeout: {session_timeout_minutes} minutes")
    
    def get_or_create_session(self, 
                               session_id: str, 
                               user_id: str = None) -> ConversationSession:
        """
        Get an existing session or create a new one.
        
        Args:
            session_id: Unique session identifier
            user_id: Optional user ID for tracking
            
        Returns:
            ConversationSession instance
        """
        with self._lock:
            # Periodic cleanup
            self._maybe_cleanup()
            
            if session_id in self._sessions:
                session = self._sessions[session_id]
                # Move to end (most recently used)
                self._sessions.move_to_end(session_id)
                return session
            
            # Create new session
            session = ConversationSession(
                session_id=session_id,
                user_id=user_id
            )
            
            # Enforce max sessions limit (remove oldest)
            while len(self._sessions) >= self.max_sessions:
                oldest_key = next(iter(self._sessions))
                del self._sessions[oldest_key]
            
            self._sessions[session_id] = session
            return session
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """
        Get an existing session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            ConversationSession or None if not found
        """
        with self._lock:
            return self._sessions.get(session_id)
    
    def add_message(self, 
                    session_id: str, 
                    role: str, 
                    content: str,
                    user_id: str = None) -> ConversationSession:
        """
        Add a message to a session's conversation.
        
        Args:
            session_id: Session identifier
            role: Message role ('user' or 'assistant')
            content: Message content
            user_id: Optional user ID
            
        Returns:
            Updated ConversationSession
        """
        session = self.get_or_create_session(session_id, user_id)
        session.add_message(role, content)
        
        # Enforce message limit (keep most recent)
        if len(session.messages) > self.max_messages:
            session.messages = session.messages[-self.max_messages:]
        
        return session
    
    def get_history(self, 
                    session_id: str, 
                    limit: int = None) -> List[Dict[str, str]]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            limit: Optional limit on number of messages
            
        Returns:
            List of message dictionaries
        """
        session = self.get_session(session_id)
        if session:
            return session.get_messages(limit)
        return []
    
    def get_history_for_llm(self, 
                            session_id: str, 
                            limit: int = 10) -> List[Dict[str, str]]:
        """
        Get conversation history formatted for LLM context.
        Returns only role and content fields.
        
        Args:
            session_id: Session identifier
            limit: Maximum messages to include
            
        Returns:
            List of {role, content} dictionaries
        """
        history = self.get_history(session_id, limit)
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in history
        ]
    
    def clear_session(self, session_id: str) -> bool:
        """
        Clear conversation history for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was found and cleared
        """
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id].clear()
                return True
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session entirely.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was found and deleted
        """
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False
    
    def get_session_count(self) -> int:
        """Get the current number of active sessions."""
        with self._lock:
            return len(self._sessions)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics."""
        with self._lock:
            total_messages = sum(
                session.get_message_count() 
                for session in self._sessions.values()
            )
            
            return {
                "active_sessions": len(self._sessions),
                "max_sessions": self.max_sessions,
                "total_messages": total_messages,
                "session_timeout_minutes": self.session_timeout,
                "max_messages_per_session": self.max_messages
            }
    
    def _maybe_cleanup(self):
        """Perform cleanup if enough time has passed."""
        current_time = time.time()
        if current_time - self._last_cleanup > self._cleanup_interval:
            self._cleanup_expired_sessions()
            self._last_cleanup = current_time
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions."""
        expired_ids = [
            session_id
            for session_id, session in self._sessions.items()
            if session.is_expired(self.session_timeout)
        ]
        
        for session_id in expired_ids:
            del self._sessions[session_id]
        
        if expired_ids:
            print(f"🧹 Cleaned up {len(expired_ids)} expired sessions")


# Global conversation manager instance
_conversation_manager: Optional[ConversationManager] = None


def get_conversation_manager() -> ConversationManager:
    """Get the global conversation manager instance."""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager(
            max_sessions=int(os.getenv("MAX_CHAT_SESSIONS", "1000")),
            session_timeout_minutes=int(os.getenv("CHAT_SESSION_TIMEOUT", "60")),
            max_messages_per_session=int(os.getenv("MAX_MESSAGES_PER_SESSION", "100"))
        )
    return _conversation_manager


def main():
    """Test the conversation manager."""
    print("🧪 Testing Conversation Manager...")
    print("=" * 50)
    
    manager = ConversationManager(max_sessions=5, session_timeout_minutes=1)
    
    # Test session creation
    session1 = manager.get_or_create_session("user-123", "test-user")
    print(f"✅ Created session: {session1.session_id}")
    
    # Test adding messages
    manager.add_message("user-123", "user", "Hello!")
    manager.add_message("user-123", "assistant", "Hi! How can I help?")
    manager.add_message("user-123", "user", "What is RAAMP?")
    
    # Get history
    history = manager.get_history_for_llm("user-123")
    print(f"📝 History ({len(history)} messages):")
    for msg in history:
        print(f"   {msg['role']}: {msg['content'][:50]}...")
    
    # Test multiple sessions
    for i in range(5):
        manager.get_or_create_session(f"session-{i}")
    
    print(f"\n📊 Stats: {manager.get_stats()}")
    
    # Test clearing
    manager.clear_session("user-123")
    cleared_history = manager.get_history("user-123")
    print(f"✅ Cleared session - messages: {len(cleared_history)}")
    
    print("\n✅ Conversation Manager test complete!")


if __name__ == "__main__":
    main()
