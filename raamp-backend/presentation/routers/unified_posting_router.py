"""
Unified Posting Router.
Provides a single endpoint for multi-platform posting.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import logging
from datetime import datetime

from presentation.routers.auth_router import get_current_user_email
from presentation.schemas.unified_posting_schemas import (
    UnifiedPostRequest,
    UnifiedPostResponse,
    PlatformResult,
    PlatformEnum,
    PostModeEnum
)
from presentation.schemas.instagram_posting_schemas import InstagramPostRequest, PostModeEnum as IGPostMode
from presentation.schemas.facebook_posting_schemas import FacebookPostRequest, PostModeEnum as FBPostMode, MediaTypeEnum
from presentation.routers.instagram_posting_router import create_instagram_post
from presentation.routers.facebook_posting_router import post_to_facebook
from infrastructure.repositories.facebook_repository import FacebookRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/social", tags=["Unified Posting"])

@router.post("/post", response_model=UnifiedPostResponse)
async def unified_post(
    request: UnifiedPostRequest,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Unified endpoint to post to Instagram, Facebook, or both.
    """
    results = []
    
    # Platform mapping
    target_platforms = []
    if request.platform == PlatformEnum.INSTAGRAM:
        target_platforms = ["instagram"]
    elif request.platform == PlatformEnum.FACEBOOK:
        target_platforms = ["facebook"]
    elif request.platform == PlatformEnum.BOTH:
        target_platforms = ["instagram", "facebook"]
    
    for platform in target_platforms:
        try:
            if platform == "instagram":
                # Convert unified request to Instagram request
                ig_request = InstagramPostRequest(
                    mode=IGPostMode.POST_NOW if request.mode == PostModeEnum.POST_NOW else
                         IGPostMode.SCHEDULE_POST if request.mode == PostModeEnum.SCHEDULE_POST else
                         IGPostMode.POST_STORY,
                    media_url=request.media_url,
                    caption=request.caption,
                    scheduled_time=request.scheduled_time
                )
                res = await create_instagram_post(ig_request, current_user_email)
                results.append(PlatformResult(
                    platform="instagram",
                    status=res.status,
                    post_id=res.post_id,
                    external_id=res.instagram_post_id,
                    error=res.error
                ))
            
            elif platform == "facebook":
                # For Facebook, we need the Page ID
                page_id = request.facebook_page_id
                if not page_id:
                    fb_repo = FacebookRepository()
                    fb_conn = await fb_repo.find_by_user_id(current_user_email)
                    if fb_conn:
                        page_id = fb_conn.page_id
                
                if not page_id:
                    results.append(PlatformResult(
                        platform="facebook",
                        status="failed",
                        error="Facebook Page ID unknown. Please reconnect Facebook in Integrations."
                    ))
                    continue
                
                # Facebook currently doesn't support stories in the router easily without a new use case
                if request.mode == PostModeEnum.POST_STORY:
                    results.append(PlatformResult(
                        platform="facebook",
                        status="failed",
                        error="Facebook Stories are not currently supported for automated posting. Please use Instagram Stories."
                    ))
                    continue

                fb_request = FacebookPostRequest(
                    mode=FBPostMode.POST_NOW if request.mode == PostModeEnum.POST_NOW else FBPostMode.SCHEDULE_POST,
                    page_id=page_id,
                    media_type=MediaTypeEnum.PHOTO, # Defaults to photo
                    media_url=request.media_url,
                    message=request.caption,
                    scheduled_time=datetime.fromisoformat(request.scheduled_time.replace("Z", "+00:00")) if request.scheduled_time else None
                )
                res = await post_to_facebook(fb_request, current_user_email)
                results.append(PlatformResult(
                    platform="facebook",
                    status=res.status,
                    post_id=res.post_id,
                    external_id=res.facebook_post_id,
                    error=res.error
                ))
        except HTTPException as e:
            logger.warning(f"Handled HTTPException for {platform}: {e.detail}")
            results.append(PlatformResult(
                platform=platform,
                status="failed",
                error=str(e.detail)
            ))
        except Exception as e:
            logger.error(f"Error posting to {platform}: {e}")
            results.append(PlatformResult(
                platform=platform,
                status="failed",
                error="Internal platform error. Please check connection and try again."
            ))
            
    success = any(r.status in ["published", "scheduled"] for r in results)
    
    return UnifiedPostResponse(
        success=success,
        results=results,
        message="Posting operation completed" if success else "Posting operation failed"
    )
