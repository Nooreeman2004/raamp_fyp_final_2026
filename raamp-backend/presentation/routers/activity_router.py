from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List
from infrastructure.database.database import get_database
from presentation.routers.auth_router import get_current_user_email
from application.use_cases.activity.get_activity_feed import GetActivityFeedUseCase
from application.use_cases.activity.log_activity import LogActivityUseCase
from application.constants import PaginationDefaults
import logging

router = APIRouter(prefix="/api/activity", tags=["Activity"])
logger = logging.getLogger(__name__)


async def get_activity_collection():
    """Dependency to get activity collection."""
    db = get_database()
    return db.activity_log


async def get_activity_feed_use_case():
    """Dependency to get GetActivityFeedUseCase instance."""
    collection = await get_activity_collection()
    return GetActivityFeedUseCase(collection)


async def get_log_activity_use_case():
    """Dependency to get LogActivityUseCase instance."""
    collection = await get_activity_collection()
    return LogActivityUseCase(collection)


@router.get("/{business_id}")
async def get_activity_feed(
    business_id: str,
    skip: int = Query(PaginationDefaults.DEFAULT_SKIP, ge=0, description="Number of records to skip"),
    limit: int = Query(PaginationDefaults.DEFAULT_LIMIT_SMALL, ge=1, le=PaginationDefaults.MAX_LIMIT_SMALL, description="Maximum records to return"),
    current_user: str = Depends(get_current_user_email),
    use_case: GetActivityFeedUseCase = Depends(get_activity_feed_use_case)
):
    """
    Get the latest activity events for a business, with pagination support.

    Returns a paginated envelope:
    - data: list of activity events
    - pagination.skip: records skipped
    - pagination.limit: page size
    - pagination.total: total matching records
    - pagination.has_more: whether more pages exist
    """
    try:
        activities, total_count = await use_case.execute_paginated(business_id, skip, limit)
        return {
            "data": activities,
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total_count,
                "has_more": skip + limit < total_count,
            },
        }
    except Exception as e:
        logger.error(f"Error in activity feed endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch activity feed")



async def log_activity(business_id: str, event_type: str, title: str, subtitle: str):
    """
    Helper function to log an activity event.
    Should be called via asyncio.create_task to be non-blocking.
    """
    try:
        collection = await get_activity_collection()
        use_case = LogActivityUseCase(collection)
        await use_case.execute(business_id, event_type, title, subtitle)
    except Exception as e:
        logger.error(f"Failed to log activity: {e}")
