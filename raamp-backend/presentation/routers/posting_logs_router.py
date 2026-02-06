"""
Instagram Posting Logs API Router
Tracks and retrieves posting activity logs
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import logging

from presentation.routers.auth_router import get_current_user_email

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/instagram/posting", tags=["instagram-logs"])

class PostingLogEntry(BaseModel):
    id: str
    user_id: str
    action: str  # "post_now", "schedule_post", "post_story", "cancel_scheduled"
    media_url: str
    caption: Optional[str] = None
    status: str  # "success", "failed", "pending"
    error_message: Optional[str] = None
    instagram_post_id: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None

class PostingLogCreate(BaseModel):
    action: str
    media_url: str
    status: str
    caption: Optional[str] = None
    error_message: Optional[str] = None
    instagram_post_id: Optional[str] = None

class PostingLogsResponse(BaseModel):
    logs: List[PostingLogEntry]
    total: int

@router.post("/logs")
async def create_posting_log(
    request: PostingLogCreate,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Create a new posting activity log entry.
    Called after each posting attempt to track success/failure.
    
    TODO: Implement actual log storage (MongoDB collection or PostgreSQL table)
    """
    try:
        log_entry = {
            "user_id": current_user_email,
            "action": request.action,
            "media_url": request.media_url,
            "caption": request.caption,
            "status": request.status,
            "error_message": request.error_message,
            "instagram_post_id": request.instagram_post_id,
            "created_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Posting log created: {log_entry}")
        
        # TODO: Store in database
        # await logs_repository.create(log_entry)
        
        return {"success": True, "message": "Log entry created"}
    
    except Exception as e:
        logger.exception(f"Error creating posting log: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create log entry"
        )

@router.get("/logs", response_model=PostingLogsResponse)
async def get_posting_logs(
    current_user_email: str = Depends(get_current_user_email),
    limit: int = Query(50, ge=1, le=200),
    status_filter: Optional[str] = Query(None, regex="^(success|failed|pending)$")
):
    """
    Retrieve posting activity logs for the current user.
    Shows history of all posting attempts with success/failure status.
    
    TODO: Implement actual log retrieval
    """
    try:
        logger.info(f"Fetching posting logs for user: {current_user_email}")
        
        # TODO: Implement actual log retrieval from database
        # logs = await logs_repository.get_by_user(current_user_email, limit, status_filter)
        
        # Placeholder response
        return PostingLogsResponse(
            logs=[],
            total=0
        )
    
    except Exception as e:
        logger.exception(f"Error fetching posting logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve posting logs"
        )
