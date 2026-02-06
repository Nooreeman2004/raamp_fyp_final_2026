from datetime import datetime
from typing import Optional, Dict
from infrastructure.database.models.chat_analytics_model import ChatAnalyticsModel

class ChatAnalyticsService:
    """
    Service for tracking chatbot usage and analytics.
    Logs interactions to MongoDB for future analysis.
    """
    
    async def log_interaction(self, 
                            session_id: str, 
                            event_type: str, 
                            content_summary: Optional[str] = None,
                            topic: Optional[str] = None,
                            sentiment_score: float = 0.0,
                            metadata: Dict = None,
                            user_id: Optional[str] = None):
        """
        Log a chat interaction event.
        """
        try:
            event = ChatAnalyticsModel(
                session_id=session_id,
                user_id=user_id,
                event_type=event_type,
                topic=topic,
                sentiment_score=sentiment_score,
                content_summary=content_summary,
                metadata=metadata or {},
                timestamp=datetime.utcnow()
            )
            await event.insert()
        except Exception as e:
            # We don't want analytics failures to break the actual chat
            print(f"⚠️ Stats logging failed: {e}")

    async def get_session_stats(self, session_id: str) -> Dict:
        """Get stats for a specific session"""
        count = await ChatAnalyticsModel.find(ChatAnalyticsModel.session_id == session_id).count()
        return {"event_count": count}
