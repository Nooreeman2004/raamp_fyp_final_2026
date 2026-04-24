from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
import logging
from typing import List, Optional
from bson import ObjectId

from presentation.routers.auth_router import get_current_user_email
from application.constants import PaginationDefaults, TimeRangeDefaults
from presentation.schemas.instagram_roi_schemas import (
    ROIMetricsResponse,
    ROISummaryResponse,
    BestPerformingPost
)
from application.services.instagram_roi_service import refresh_post_roi
from infrastructure.database.models.instagram_post_model import (
    InstagramPostModel,
    ScheduledInstagramPostModel,
    InstagramStoryModel
)
from presentation.utils.validation import validate_object_id
from presentation.schemas.error_response import ErrorResponse, ErrorCode
import asyncio

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/instagram/roi", tags=["Instagram ROI"])


@router.post("/refresh/{post_id}", response_model=ROIMetricsResponse, status_code=202)
async def refresh_post_metrics(
    post_id: str,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Manually trigger a metrics refresh for a single Instagram post.
    Returns 202 Accepted since the refresh is async.
    """
    validate_object_id(post_id, "post ID")  # Validate before hitting the DB
    metrics = await refresh_post_roi(post_id)
    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                error_code=ErrorCode.NOT_FOUND,
                message="Post not found or ROI fetch failed"
            ).model_dump()
        )
    return metrics


@router.get("/{post_id}", response_model=ROIMetricsResponse)
async def get_post_metrics(
    post_id: str,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Returns stored ROI metrics for a specific post.
    """
    validate_object_id(post_id, "post ID")  # Validate before hitting the DB
    post = await InstagramPostModel.get(post_id) or \
           await ScheduledInstagramPostModel.get(post_id) or \
           await InstagramStoryModel.get(post_id)

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                error_code=ErrorCode.NOT_FOUND,
                message="Post not found"
            ).model_dump()
        )

    return post.roi_metrics


@router.get("/summary/{business_id}", response_model=ROISummaryResponse)
async def get_business_roi_summary(
    business_id: str,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Returns aggregated ROI analytics for a business account.
    """
    # Pull all relevant documents for this business concurrently (avoids sequential N+1)
    tasks = [
        InstagramPostModel.find(InstagramPostModel.ig_business_id == business_id).to_list(),
        ScheduledInstagramPostModel.find(ScheduledInstagramPostModel.ig_business_id == business_id).to_list(),
        InstagramStoryModel.find(InstagramStoryModel.ig_business_id == business_id).to_list()
    ]
    results = await asyncio.gather(*tasks)
    posts, scheduled, stories = results
    
    all_content = posts + scheduled + stories
    
    if not all_content:
        return ROISummaryResponse(
            total_posts=0,
            total_reach=0,
            total_impressions=0,
            avg_engagement_rate=0.0,
            posts_pending=0,
            posts_failed=0
        )
        
    total_reach = sum(p.roi_metrics.reach for p in all_content)
    total_impressions = sum(p.roi_metrics.impressions for p in all_content)
    total_engagement_rate = sum(p.roi_metrics.engagement_rate for p in all_content)
    
    pending = sum(1 for p in all_content if p.roi_metrics.fetch_status == "pending")
    failed = sum(1 for p in all_content if p.roi_metrics.fetch_status == "failed")
    success_posts = [p for p in all_content if p.roi_metrics.fetch_status == "success"]
    
    avg_er = 0.0
    if success_posts:
        avg_er = total_engagement_rate / len(success_posts)
        
    best_p = None
    worst_p = None
    
    if success_posts:
        # Sort by engagement_rate
        sorted_posts = sorted(success_posts, key=lambda x: x.roi_metrics.engagement_rate, reverse=True)
        best_post = sorted_posts[0]
        worst_post = sorted_posts[-1]
        
        best_p = BestPerformingPost(
            post_id=str(best_post.id),
            reach=best_post.roi_metrics.reach,
            engagement_rate=best_post.roi_metrics.engagement_rate
        )
        worst_p = BestPerformingPost(
            post_id=str(worst_post.id),
            reach=worst_post.roi_metrics.reach,
            engagement_rate=worst_post.roi_metrics.engagement_rate
        )
        
    # Calculate prev_week_reach
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    fourteen_days_ago = datetime.utcnow() - timedelta(days=14)
    
    # Filter only published posts that fall in the previous week window
    prev_week_posts = [
        p for p in all_content 
        if hasattr(p, 'published_at') and p.published_at and fourteen_days_ago <= p.published_at < seven_days_ago
    ]
    prev_week_reach = sum(p.roi_metrics.reach for p in prev_week_posts)
        
    return ROISummaryResponse(
        total_posts=len(all_content),
        total_reach=total_reach,
        prev_week_reach=prev_week_reach,
        total_impressions=total_impressions,
        avg_engagement_rate=round(avg_er, 2),
        best_performing_post=best_p,
        worst_performing_post=worst_p,
        posts_pending=pending,
        posts_failed=failed
    )

@router.get("/timeseries/{business_id}", response_model=List[dict])
async def get_instagram_roi_timeseries(
    business_id: str,
    days: int = Query(TimeRangeDefaults.DEFAULT_DAYS_MEDIUM, le=TimeRangeDefaults.MAX_DAYS_MEDIUM),
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Returns daily aggregated ROI metrics (reach, impressions) for the last X days.
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Fetch all published posts within the range
    posts = await InstagramPostModel.find(
        InstagramPostModel.ig_business_id == business_id,
        InstagramPostModel.published_at >= start_date
    ).to_list()
    
    # Also include stories if they have ROI metrics
    stories = await InstagramStoryModel.find(
        InstagramStoryModel.ig_business_id == business_id,
        InstagramStoryModel.published_at >= start_date
    ).to_list()
    
    all_content = posts + stories
    
    # Aggregate by date
    daily_stats = {}
    for i in range(days):
        date_obj = (datetime.utcnow() - timedelta(days=i))
        date_str = date_obj.strftime("%Y-%m-%d")
        daily_stats[date_str] = {"date": date_str, "reach": 0, "impressions": 0}
        
    for item in all_content:
        if not item.published_at: continue
        date_str = item.published_at.strftime("%Y-%m-%d")
        if date_str in daily_stats:
            daily_stats[date_str]["reach"] += item.roi_metrics.reach
            daily_stats[date_str]["impressions"] += item.roi_metrics.impressions
            
    # Return sorted by date
    return sorted(daily_stats.values(), key=lambda x: x["date"])
