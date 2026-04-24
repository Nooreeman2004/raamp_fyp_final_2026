"""
Log Activity Use Case
Application layer - Business logic for logging activity events
"""
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class LogActivityUseCase:
    """Use case for logging activity events."""
    
    def __init__(self, activity_collection):
        """
        Initialize use case with activity collection.
        
        Args:
            activity_collection: MongoDB collection for activity logs
        """
        self.activity_collection = activity_collection
    
    async def execute(
        self,
        business_id: str,
        event_type: str,
        title: str,
        subtitle: str
    ) -> bool:
        """
        Log an activity event.
        
        Args:
            business_id: Business identifier
            event_type: Type of event (e.g., "post_created", "campaign_launched")
            title: Event title
            subtitle: Event subtitle/description
            
        Returns:
            True if successful, False otherwise
        """
        try:
            activity = {
                "business_id": business_id,
                "event_type": event_type,
                "title": title,
                "subtitle": subtitle,
                "created_at": datetime.utcnow()
            }
            
            await self.activity_collection.insert_one(activity)
            logger.info(f"Activity logged: {event_type} for {business_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")
            return False
