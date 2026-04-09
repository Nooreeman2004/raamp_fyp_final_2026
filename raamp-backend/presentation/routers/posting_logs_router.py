"""
Posting Logs API Router
=======================
Handles retrieval and creation of social media posting logs.
Tracks success/failure of Instagram and Facebook posts.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import logging

from presentation.routers.auth_router import get_current_user_email
from infrastructure.database.models.posting_log_model import PostingLogModel

logger = logging.getLogger(__name__)

# Updated prefix to match requested /api/v1/posting-logs
# Note: main.py includes this router, so check if it adds another prefix
router = APIRouter(prefix="/api/v1/posting-logs", tags=["Posting Logs"])

# ==================== Request/Response Schemas ====================

class PostingLogCreate(BaseModel):
    """Schema for creating a new posting log"""
    platform: str
    post_id: Optional[str] = None
    internal_id: Optional[str] = None
    media_url: Optional[str] = None
    caption: Optional[str] = None
    status: str
    published_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

class PostingLogResponse(BaseModel):
    """Response schema for a single log entry formatted for the frontend"""
    id: str = Field(..., alias="_id")
    post_id: Optional[str] = None
    internal_id: Optional[str] = None
    platform: str
    media_url: Optional[str] = None
    caption: Optional[str] = None
    status: str
    created_at: datetime
    published_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        populate_by_name = True

class PostingLogsListResponse(BaseModel):
    """Response schema for a list of log entries"""
    logs: List[dict]
    total: int

# ==================== Endpoints ====================

@router.get("", response_model=List[dict])
async def get_posting_logs(
    platform: Optional[str] = Query(None, description="Filter by platform (instagram/facebook)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (PUBLISHED/FAILED/SCHEDULED)"),
    limit: int = Query(50, ge=1, le=200),
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Retrieve posting activity logs for the current user.
    Ordered by creation date descending.
    """
    try:
        # Build query
        query = {"user_id": current_user_email}
        if platform:
            query["platform"] = platform
        if status_filter:
            query["status"] = status_filter

        # Fetch from MongoDB
        logs = await PostingLogModel.find(query).sort("-created_at").limit(limit).to_list()
        
        # Format for frontend
        formatted_logs = []
        for log in logs:
            formatted_logs.append({
                "post_id": log.post_id,
                "internal_id": log.internal_id,
                "platform": log.platform,
                "media_url": log.media_url,
                "caption": log.caption,
                "status": log.status,
                "created_at": log.created_at,
                "published_at": log.published_at,
                "error_message": log.error_message,
                "id": str(log.id) # stringify ObjectId
            })
            
        return formatted_logs

    except Exception as e:
        logger.error(f"Error fetching posting logs for {current_user_email}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve posting logs"
        )

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_posting_log(
    log_data: PostingLogCreate,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Manually create a posting log entry (Internal use).
    """
    try:
        new_log = PostingLogModel(
            user_id=current_user_email,
            **log_data.model_dump()
        )
        await new_log.insert()
        return new_log

    except Exception as e:
        logger.error(f"Failed to create posting log: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save posting log"
        )

@router.delete("/{log_id}")
async def delete_posting_log(
    log_id: str,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Delete a specific posting log entry.
    """
    try:
        log = await PostingLogModel.get(log_id)
        
        if not log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Log entry not found"
            )
            
        if log.user_id != current_user_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this log"
            )
            
        await log.delete()
        return {"success": True, "message": "Log entry deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting log {log_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete log entry"
        )
