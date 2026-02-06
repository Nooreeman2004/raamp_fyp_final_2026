"""
Facebook Posting Router
Endpoints for posting content to Facebook Pages
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
import logging

from presentation.schemas.facebook_posting_schemas import (
    FacebookPostRequest,
    FacebookPostResponse,
    PostModeEnum,
    MediaTypeEnum,
    ScheduledPostsResponse,
    CancelScheduledPostRequest,
    CancelScheduledPostResponse
)
from application.services.facebook_graph_api_service import FacebookGraphAPIClient, FacebookAPIError
from application.use_cases.facebook_posting_use_cases import (
    PostNowToPageUseCase,
    SchedulePagePostUseCase
)
from infrastructure.repositories.facebook_post_repository import (
    FacebookPostRepository,
    ScheduledFacebookPostRepository
)
from infrastructure.repositories.facebook_repository import FacebookRepository
from infrastructure.repositories.social_media_repository import SocialMediaRepository
from infrastructure.database.models.user_model import UserModel
from presentation.routers.auth_router import get_current_user_email

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/facebook/posting", tags=["Facebook Posting"])


# Lazy dependency injection
async def get_facebook_api_client():
    async with FacebookGraphAPIClient() as client:
        yield client


async def get_post_repository():
    return FacebookPostRepository()


async def get_scheduled_post_repository():
    return ScheduledFacebookPostRepository()


async def get_facebook_repository():
    return FacebookRepository()


async def get_social_media_repository():
    return SocialMediaRepository()


@router.post("/post", response_model=FacebookPostResponse)
async def post_to_facebook(
    request: FacebookPostRequest,
    user_email: str = Depends(get_current_user_email),
    api_client: FacebookGraphAPIClient = Depends(get_facebook_api_client),
    post_repo: FacebookPostRepository = Depends(get_post_repository),
    scheduled_post_repo: ScheduledFacebookPostRepository = Depends(get_scheduled_post_repository),
    facebook_repo: FacebookRepository = Depends(get_facebook_repository),
    social_media_repo: SocialMediaRepository = Depends(get_social_media_repository)
):
    """
    Post content to Facebook Page.
    
    Supports three modes:
    - POST_NOW: Post immediately
    - SCHEDULE_POST: Schedule for later
    
    And three media types:
    - PHOTO: Post a photo with optional caption
    - VIDEO: Post a video with optional title and description
    - TEXT: Post text only
    """
    try:
        # Log the raw request for debugging
        logger.info(f"Facebook post request received - User: {user_email}")
        logger.info(f"Request data: mode={request.mode}, page_id={request.page_id}, media_type={request.media_type}")
        logger.info(f"media_url type: {type(request.media_url)}, value: {repr(request.media_url)}")
        logger.info(f"message: {request.message}")
        
        # Get user from UserModel
        user = await UserModel.find_one(UserModel.email == user_email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_id = user_email  # Use email as user_id for consistency
        
        # Verify Facebook connection exists
        facebook_conn = await facebook_repo.find_by_user_id(user_id)
        if not facebook_conn:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Facebook not connected. Please connect your Facebook account first."
            )
        
        # Log the request for debugging
        logger.info(f"Facebook post request - Mode: {request.mode}, Page: {request.page_id}, Media Type: {request.media_type}, Media URL: {request.media_url}")
        
        # Route to appropriate use case based on mode
        if request.mode == PostModeEnum.POST_NOW:
            # Post immediately
            use_case = PostNowToPageUseCase(
                api_client=api_client,
                post_repository=post_repo,
                facebook_repository=facebook_repo
            )
            
            post = await use_case.execute(
                user_id=user_id,
                page_id=request.page_id,
                media_type=request.media_type.value,
                media_url=request.media_url,
                message=request.message,
                title=request.title
            )
            
            return FacebookPostResponse(
                status=post.status,
                post_id=str(post.id),
                facebook_post_id=post.facebook_post_id,
                scheduled_time=None,
                error=post.error,
                page_id=post.page_id,
                page_name=post.page_name
            )
        
        elif request.mode == PostModeEnum.SCHEDULE_POST:
            # Schedule for later
            use_case = SchedulePagePostUseCase(
                scheduled_post_repository=scheduled_post_repo,
                facebook_repository=facebook_repo
            )
            
            scheduled_post = await use_case.execute(
                user_id=user_id,
                page_id=request.page_id,
                media_type=request.media_type.value,
                media_url=request.media_url,
                message=request.message,
                title=request.title,
                scheduled_time=request.scheduled_time
            )
            
            return FacebookPostResponse(
                status=scheduled_post.status,
                post_id=str(scheduled_post.id),
                facebook_post_id=None,
                scheduled_time=scheduled_post.scheduled_time,
                error=None,
                page_id=scheduled_post.page_id,
                page_name=scheduled_post.page_name
            )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FacebookAPIError as e:
        logger.error(f"Facebook API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Facebook API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in post_to_facebook: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to post to Facebook: {str(e)}"
        )


@router.get("/scheduled", response_model=ScheduledPostsResponse)
async def get_scheduled_posts(
    user_email: str = Depends(get_current_user_email),
    scheduled_post_repo: ScheduledFacebookPostRepository = Depends(get_scheduled_post_repository),
    social_media_repo: SocialMediaRepository = Depends(get_social_media_repository),
    limit: int = 50,
    skip: int = 0
):
    """Get all scheduled Facebook posts for the current user"""
    try:
        user = await UserModel.find_one(UserModel.email == user_email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_id = user_email  # Use email as user_id
        scheduled_posts = await scheduled_post_repo.get_scheduled_posts_by_user(
            user_id=user_id,
            limit=limit,
            skip=skip
        )
        
        # Convert to dict format
        posts_data = [
            {
                "post_id": str(post.id),
                "page_id": post.page_id,
                "page_name": post.page_name,
                "media_type": post.media_type,
                "message": post.message,
                "scheduled_time": post.scheduled_time.isoformat() if post.scheduled_time else None,
                "status": post.status,
                "created_at": post.created_at.isoformat()
            }
            for post in scheduled_posts
        ]
        
        return ScheduledPostsResponse(
            scheduled_posts=posts_data,
            total=len(posts_data)
        )
        
    except Exception as e:
        logger.error(f"Failed to get scheduled posts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve scheduled posts"
        )


@router.post("/scheduled/cancel", response_model=CancelScheduledPostResponse)
async def cancel_scheduled_post(
    request: CancelScheduledPostRequest,
    user_email: str = Depends(get_current_user_email),
    scheduled_post_repo: ScheduledFacebookPostRepository = Depends(get_scheduled_post_repository),
    social_media_repo: SocialMediaRepository = Depends(get_social_media_repository)
):
    """Cancel a scheduled Facebook post"""
    try:
        user = await UserModel.find_one(UserModel.email == user_email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_id = user_email  # Use email as user_id
        
        # Verify post belongs to user
        scheduled_post = await scheduled_post_repo.get_scheduled_post_by_id(request.post_id)
        if not scheduled_post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheduled post not found"
            )
        
        if scheduled_post.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to cancel this post"
            )
        
        # Cancel the post
        cancelled_post = await scheduled_post_repo.cancel_scheduled_post(request.post_id)
        
        if not cancelled_post:
            return CancelScheduledPostResponse(
                success=False,
                message="Failed to cancel post. It may have already been published or cancelled."
            )
        
        return CancelScheduledPostResponse(
            success=True,
            message="Scheduled post cancelled successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel scheduled post: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel scheduled post"
        )


@router.get("/history", response_model=list)
async def get_posting_history(
    user_email: str = Depends(get_current_user_email),
    post_repo: FacebookPostRepository = Depends(get_post_repository),
    social_media_repo: SocialMediaRepository = Depends(get_social_media_repository),
    limit: int = 50,
    skip: int = 0
):
    """Get posting history for the current user"""
    try:
        user = await UserModel.find_one(UserModel.email == user_email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_id = user_email  # Use email as user_id
        posts = await post_repo.get_posts_by_user(
            user_id=user_id,
            limit=limit,
            skip=skip
        )
        
        return [
            {
                "post_id": str(post.id),
                "page_id": post.page_id,
                "page_name": post.page_name,
                "media_type": post.media_type,
                "message": post.message,
                "facebook_post_id": post.facebook_post_id,
                "status": post.status,
                "error": post.error,
                "created_at": post.created_at.isoformat()
            }
            for post in posts
        ]
        
    except Exception as e:
        logger.error(f"Failed to get posting history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve posting history"
        )
