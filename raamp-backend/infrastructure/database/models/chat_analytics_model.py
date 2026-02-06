from beanie import Document
from datetime import datetime
from typing import Optional, Dict
from pydantic import Field

class ChatAnalyticsModel(Document):
    """
    MongoDB document for storing Chat Analytics events.
    Every significant user interaction is logged here for analysis.
    """
    session_id: str
    user_id: Optional[str] = None
    
    event_type: str = "message"  # message, tool_use, diagnostic_check
    topic: Optional[str] = None  # e.g., "campaign_optimization", "technical_issue"
    sentiment_score: Optional[float] = 0.0
    
    content_summary: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "chat_analytics"
        indexes = [
            "timestamp",
            "event_type",
            "topic"
        ]
