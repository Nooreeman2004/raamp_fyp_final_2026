from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from datetime import datetime
from infrastructure.database.database import get_database
from presentation.routers.auth_router import get_current_user_email
import logging

router = APIRouter(prefix="/api/activity", tags=["Activity"])
logger = logging.getLogger(__name__)

async def get_activity_collection():
    db = get_database()
    return db.activity_log

@router.get("/{business_id}", response_model=List[dict])
async def get_activity_feed(
    business_id: str,
    limit: int = Query(10, le=50),
    current_user: str = Depends(get_current_user_email)
):
    """
    Get the latest activity events for a business.
    Each event includes a type, title, subtitle, and timestamp.
    """
    try:
        collection = await get_activity_collection()
        # Find activities for this business, sort by newest first
        cursor = collection.find({"business_id": business_id}).sort("created_at", -1).limit(limit)
        activities = await cursor.to_list(length=limit)
        
        # Format the output (converting ObjectId to str)
        for activity in activities:
            activity["id"] = str(activity["_id"])
            del activity["_id"]
            if isinstance(activity.get("created_at"), datetime):
                activity["created_at"] = activity["created_at"].isoformat()
                
        return activities
    except Exception as e:
        logger.error(f"Error fetching activity feed: {e}")
        return []

async def log_activity(business_id: str, event_type: str, title: str, subtitle: str):
    """
    Helper function to log an activity event.
    Should be called via asyncio.create_task to be non-blocking.
    """
    try:
        db = get_database()
        collection = db.activity_log
        
        activity = {
            "business_id": business_id,
            "event_type": event_type,
            "title": title,
            "subtitle": subtitle,
            "created_at": datetime.utcnow()
        }
        
        await collection.insert_one(activity)
        logger.info(f"Activity logged: {event_type} for {business_id}")
    except Exception as e:
        logger.error(f"Failed to log activity: {e}")
