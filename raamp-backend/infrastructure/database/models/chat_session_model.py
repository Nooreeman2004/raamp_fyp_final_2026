from beanie import Document
from datetime import datetime
from typing import List, Optional, Dict
from pydantic import Field

class ChatMessageModel(Document):
    """
    Sub-document for individual chat messages.
    Note: Usually embedded, but defining as Pydantic model structure within session.
    """
    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatSessionModel(Document):
    """
    MongoDB document for storing Chat Sessions.
    """
    session_id: str
    user_id: Optional[str] = None
    title: Optional[str] = "New Conversation"
    
    messages: List[Dict] = Field(default_factory=list)  # List of {role, content, timestamp}
    trend_ids: List[str] = Field(default_factory=list) # IDs of trends discussed in this session
    metadata: Dict = Field(default_factory=dict)
    
    is_active: bool = True
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "chat_sessions"
        indexes = [
            "session_id",
            "user_id",
            "last_activity",
            "trend_ids"
        ]
