from beanie import Document
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import Field

class ChatInteractionModel(Document):
    """
    Flat log of every user query and assistant response.
    Used for audit trails and analytics.
    """
    session_id: str
    user_id: Optional[str] = None
    
    query: str
    response: str
    
    # Metadata like trend_ids discussed and sources used
    trend_ids: List[str] = Field(default_factory=list)
    sources: List[Dict] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "chat_interactions"
        indexes = [
            "user_id",
            "session_id",
            "created_at"
        ]
