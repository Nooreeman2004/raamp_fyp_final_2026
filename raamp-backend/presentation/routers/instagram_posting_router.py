"""
Instagram Posting API Router.
Presentation layer endpoints for Instagram auto-posting functionality.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import logging
import asyncio
from slowapi import Limiter
from slowapi.util import get_remote_address
from presentation.routers.activity_router import log_activity
from application.utils.background_tasks import create_background_task
from presentation.routers.auth_router import get_current_user_email
from presentation.schemas.instagram_posting_schemas import (
    InstagramPostRequest,
    InstagramPostResponse,
    PostModeEnum,
    ScheduledPostListResponse,
    ScheduledPostItem,
    CancelScheduledPostRequest,
    CancelScheduledPostResponse,
    PostHistoryResponse,
    PostHistoryItem
)
from domain.entities.instagram_post_entity import MediaType
from application.use_cases.instagram_posting_use_cases import (
    PostNowUseCase,
    SchedulePostUseCase,
    PostStoryUseCase
)
from application.services.instagram_graph_api_service import InstagramGraphAPIClient
from infrastructure.repositories.instagram_post_repository_impl import (
    InstagramPostRepository,
    ScheduledPostRepository,
    StoryPostRepository
)
from infrastructure.repositories.social_media_repository import SocialMediaRepository
from infrastructure.repositories.instagram_repository import InstagramRepository
from application.services.notification_service import NotificationService
from presentation.schemas.error_response import ErrorResponse, ErrorCode

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/instagram/posting", tags=["instagram-posting"])
limiter = Limiter(key_func=get_remote_address)

# Dependencies will be initialized on first use to avoid import-time errors
_api_client = None
_post_repo = None
_scheduled_repo = None
_story_repo = None
_social_media_repo = None
_instagram_repo = None
_notification_service = None

def get_api_client():
    global _api_client
    if _api_client is None:
        _api_client = InstagramGraphAPIClient()
    return _api_client

def get_post_repo():
    global _post_repo
    if _post_repo is None:
        _post_repo = InstagramPostRepository()
    return _post_repo

def get_scheduled_repo():
    global _scheduled_repo
    if _scheduled_repo is None:
        _scheduled_repo = ScheduledPostRepository()
    return _scheduled_repo

def get_story_repo():
    global _story_repo
    if _story_repo is None:
        _story_repo = StoryPostRepository()
    return _story_repo

def get_social_media_repo():
    global _social_media_repo
    if _social_media_repo is None:
        _social_media_repo = SocialMediaRepository()
    return _social_media_repo

def get_instagram_repo():
    global _instagram_repo
    if _instagram_repo is None:
        _instagram_repo = InstagramRepository()
    return _instagram_repo

def get_notification_service():
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service


@router.post("/post", response_model=InstagramPostResponse)
@limiter.limit("25/hour")
async def create_instagram_post(
    http_request: Request,
    request: InstagramPostRequest,
    background_tasks: BackgroundTasks,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Universal endpoint for Instagram posting.
    Supports three modes: post_now, schedule_post, post_story.
    
    **Authentication Required**: User must be authenticated and have Instagram connected.
    
    **Modes**:
    - `post_now`: Publish immediately to Instagram feed
    - `schedule_post`: Schedule for future publishing (requires scheduled_time)
    - `post_story`: Publish immediately to Instagram stories
    
    **Rate Limits**: Max 25 posts/hour per account (enforced)
    """
    try:
        # Verify Instagram connection exists
        ig_repo = get_instagram_repo()
        ig_account = await ig_repo.find_by_user_id(current_user_email)
        if not ig_account or not ig_account.ig_business_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
                    message="Instagram account not connected. Please connect Instagram first."
                ).model_dump()
            )
        
        ig_business_id = ig_account.ig_business_id
        
        # Route to appropriate use case based on mode
        logger.info(f"Instagram Post Request: user={current_user_email}, mode={request.mode}, has_media={bool(request.media_url)}")
        
        if request.mode == PostModeEnum.POST_NOW:
            use_case = PostNowUseCase(
                get_post_repo(), 
                get_api_client(),
                get_notification_service()  # Inject notification service
            )
            result = await use_case.execute(
                user_id=current_user_email,
                ig_business_id=ig_business_id,
                media_url=request.media_url,
                caption=request.caption,
                media_type=MediaType.IMAGE  # Could be enhanced to detect from URL
            )
            logger.info(f"Instagram Post Now Result: {result}")

            # Asset A/B tracking: link created post -> asset usage
            if result.get("status") == "published" and request.asset_id:
                from infrastructure.repositories.asset_repository import AssetRepository
                asset_repo = AssetRepository()
                asset = await asset_repo.get_by_asset_id(request.asset_id)
                if asset:
                    internal_post_id = result.get("post_id")  # the internal MongoDB ID
                    if internal_post_id and internal_post_id not in asset.instagram_post_ids:
                        asset.instagram_post_ids.append(internal_post_id)
                        asset.times_used += 1
                        asset.last_used_at = datetime.utcnow()
                        asset.updated_at = datetime.utcnow()
                        await asset.save()
            
            # Log Activity (Reliable Background Task)
            if result.get("status") == "published":
                background_tasks.add_task(
                    log_activity,
                    business_id=ig_business_id,
                    event_type="post_published",
                    title="Instagram Post Published",
                    subtitle="Feed post is now live"
                )
            
            return InstagramPostResponse(**result)
        
        elif request.mode == PostModeEnum.SCHEDULE_POST:
            if not request.scheduled_time:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ErrorResponse(
                        error_code=ErrorCode.VALIDATION_ERROR,
                        message="scheduled_time is required for schedule_post mode"
                    ).model_dump()
                )
            
            scheduled_dt = datetime.fromisoformat(request.scheduled_time.replace("Z", "+00:00"))
            use_case = SchedulePostUseCase(get_scheduled_repo())
            result = await use_case.execute(
                user_id=current_user_email,
                ig_business_id=ig_business_id,
                media_url=request.media_url,
                scheduled_time=scheduled_dt,
                caption=request.caption,
                media_type=MediaType.IMAGE
            )
            logger.info(f"Instagram Schedule Result: {result}")

            # Asset A/B tracking: link scheduled intent -> asset usage
            if result.get("status") == "scheduled" and request.asset_id:
                from infrastructure.repositories.asset_repository import AssetRepository
                asset_repo = AssetRepository()
                asset = await asset_repo.get_by_asset_id(request.asset_id)
                if asset:
                    internal_post_id = result.get("scheduled_post_id")  # internal MongoDB ID
                    if internal_post_id and internal_post_id not in asset.instagram_post_ids:
                        asset.instagram_post_ids.append(internal_post_id)
                        asset.times_used += 1
                        asset.last_used_at = datetime.utcnow()
                        asset.updated_at = datetime.utcnow()
                        await asset.save()
            
            # Log Activity (Non-blocking with error handling)
            if result.get("status") == "scheduled":
                create_background_task(
                    log_activity(
                        business_id=ig_business_id,
                        event_type="post_published",
                        title="Instagram Post Scheduled",
                        subtitle=f"Queued for {request.scheduled_time}"
                    ),
                    task_name="log_scheduled_post"
                )
            
            return InstagramPostResponse(
                status=result["status"],
                post_id=result.get("scheduled_post_id"),
                instagram_post_id=None,
                scheduled_time=result.get("scheduled_time"),
                error=result.get("error")
            )
        
        elif request.mode == PostModeEnum.POST_STORY:
            use_case = PostStoryUseCase(get_story_repo(), get_api_client())
            result = await use_case.execute(
                user_id=current_user_email,
                ig_business_id=ig_business_id,
                media_url=request.media_url,
                media_type=MediaType.STORIES
            )
            logger.info(f"Instagram Story Result: {result}")
            
            # Log Activity (Non-blocking with error handling)
            if result.get("status") == "published":
                create_background_task(
                    log_activity(
                        business_id=ig_business_id,
                        event_type="post_published",
                        title="Instagram Story Published",
                        subtitle="Story is now live"
                    ),
                    task_name="log_story_published"
                )
            
            return InstagramPostResponse(
                status=result["status"],
                post_id=result.get("story_id"),
                instagram_post_id=result.get("instagram_story_id"),
                scheduled_time=None,
                error=result.get("error")
            )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    error_code=ErrorCode.VALIDATION_ERROR,
                    message=f"Invalid mode: {request.mode}"
                ).model_dump()
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in create_instagram_post: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your request"
        )


@router.get("/scheduled", response_model=ScheduledPostListResponse)
async def list_scheduled_posts(
    current_user_email: str = Depends(get_current_user_email)
):
    """
    List all scheduled posts for the authenticated user.
    Shows pending, processing, and completed scheduled posts.
    """
    try:
        scheduled_posts = await get_scheduled_repo().get_by_user(current_user_email)
        
        items = [
            ScheduledPostItem(
                post_id=str(post.created_at.timestamp()),
                media_url=post.media_url,
                caption=post.caption,
                scheduled_time=post.scheduled_time.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
                status=post.status.value if hasattr(post.status, 'value') else post.status,
                created_at=post.created_at.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
                platform="instagram"
            )
            for post in scheduled_posts
        ]
        
        return ScheduledPostListResponse(
            posts=items,
            total=len(items)
        )
    
    except Exception as e:
        logger.exception(f"Error listing scheduled posts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve scheduled posts"
        )


@router.post("/scheduled/cancel", response_model=CancelScheduledPostResponse)
async def cancel_scheduled_post(
    request: CancelScheduledPostRequest,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Cancel a scheduled post before it executes.
    Can only cancel posts with status 'scheduled'.
    """
    try:
        logger.info(f"Cancel request for post {request.post_id} from user {current_user_email}")
        
        # Verify ownership
        scheduled_post = await get_scheduled_repo().get_by_id(request.post_id)
        if not scheduled_post:
            logger.warning(f"Post {request.post_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheduled post not found"
            )
        
        logger.info(f"Found post - user_id: {scheduled_post.user_id}, status: {scheduled_post.status}")
        
        if scheduled_post.user_id != current_user_email:
            logger.warning(f"Unauthorized cancel attempt - post owner: {scheduled_post.user_id}, requester: {current_user_email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to cancel this post"
            )
        
        # Cancel the post
        logger.info(f"Attempting to cancel post {request.post_id}")
        success = await get_scheduled_repo().cancel(request.post_id)
        logger.info(f"Cancel result: {success}")
        
        if success:
            return CancelScheduledPostResponse(
                success=True,
                message="Scheduled post cancelled successfully"
            )
        else:
            return CancelScheduledPostResponse(
                success=False,
                message="Failed to cancel scheduled post - it may have already been processed"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error cancelling scheduled post {request.post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel post"
        )


@router.get("/history", response_model=PostHistoryResponse)
async def get_post_history(
    limit: int = 50,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Get posting history for the authenticated user.
    Returns recent feed posts with their status and metadata.
    """
    try:
        posts = await get_post_repo().get_by_user(current_user_email, limit=limit)
        
        items = [
            PostHistoryItem(
                post_id=str(post.created_at.timestamp()),
                internal_id=str(post.id) if post.id else None,
                platform="instagram",
                media_url=post.media_url,
                caption=post.caption,
                status=post.status.value if hasattr(post.status, 'value') else post.status,
                instagram_post_id=post.instagram_post_id,
                created_at=post.created_at.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
                published_at=post.published_at.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z") if post.published_at else None,
                error_message=post.error_message
            )
            for post in posts
        ]
        
        return PostHistoryResponse(
            posts=items,
            total=len(items)
        )
    
    except Exception as e:
        logger.error(f"Error retrieving post history: {e}")
        # Return empty list instead of failing entire page
        return PostHistoryResponse(posts=[], total=0)


@router.get("/stories", response_model=PostHistoryResponse)
async def get_story_history(
    limit: int = 50,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Get story posting history for the authenticated user.
    Returns recent stories with their status and metadata.
    """
    try:
        stories = await get_story_repo().get_by_user(current_user_email, limit=limit)
        
        items = [
            PostHistoryItem(
                post_id=str(story.created_at.timestamp()),
                internal_id=str(story.id) if story.id else None,
                platform="instagram",
                media_url=story.media_url,
                caption=None,  # Stories don't have captions
                status=story.status.value if hasattr(story.status, 'value') else story.status,
                instagram_post_id=story.instagram_story_id,
                created_at=story.created_at.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
                published_at=story.published_at.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z") if story.published_at else None,
                error_message=story.error_message
            )
            for story in stories
        ]
        
        return PostHistoryResponse(
            posts=items,
            total=len(items)
        )
    
    except Exception as e:
        logger.error(f"Error retrieving story history: {e}")
        # Return empty list instead of failing entire page
        return PostHistoryResponse(posts=[], total=0)


@router.get("/connection-status")
async def get_connection_status(
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Check Instagram connection status and posting capability.
    Returns connection details and token validity.
    """
    try:
        ig_repo = get_instagram_repo()
        ig_account = await ig_repo.find_by_user_id(current_user_email)
        
        if not ig_account or not ig_account.ig_business_id:
            return {
                "connected": False,
                "can_post": False,
                "message": "Instagram not connected"
            }
        
        # Check token expiry (Instagram tokens typically last 60 days)
        token_valid = True
        expires_soon = False
        
        # Note: InstagramAccount doesn't have expires_at field like SocialMediaAccount
        # Instagram tokens are long-lived (60 days) and need manual refresh
        
        return {
            "connected": True,
            "can_post": token_valid,
            "ig_business_id": ig_account.ig_business_id,
            "username": ig_account.username,
            "token_valid": token_valid,
            "expires_soon": expires_soon,
            "expires_at": None  # Instagram tokens don't have built-in expiry tracking
        }
    
    except Exception as e:
        logger.exception(f"Error checking connection status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check connection status"
        )
