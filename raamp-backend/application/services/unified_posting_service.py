"""
Unified Posting Service
======================
Application-layer orchestration for multi-platform posting.

This is the clean-architecture home for the logic previously hosted in the router.
Routers should be thin wrappers that delegate here.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, List

from fastapi import HTTPException, status

from presentation.schemas.unified_posting_schemas import (
    UnifiedPostRequest,
    UnifiedPostResponse,
    PlatformResult,
    PlatformEnum,
    PostModeEnum,
)
from presentation.schemas.instagram_posting_schemas import InstagramPostRequest, PostModeEnum as IGPostMode
from presentation.schemas.facebook_posting_schemas import FacebookPostRequest, PostModeEnum as FBPostMode, MediaTypeEnum

from domain.entities.instagram_post_entity import MediaType
from application.use_cases.instagram_posting_use_cases import PostNowUseCase, SchedulePostUseCase, PostStoryUseCase
from application.use_cases.facebook_posting_use_cases import PostNowToPageUseCase, SchedulePagePostUseCase

from application.services.instagram_graph_api_service import InstagramGraphAPIClient
from application.services.facebook_graph_api_service import FacebookGraphAPIClient, FacebookAPIError
from application.services.notification_service import NotificationService

from infrastructure.repositories.instagram_post_repository_impl import (
    InstagramPostRepository,
    ScheduledPostRepository,
    StoryPostRepository,
)
from infrastructure.repositories.instagram_repository import InstagramRepository
from infrastructure.repositories.facebook_post_repository import FacebookPostRepository, ScheduledFacebookPostRepository
from infrastructure.repositories.facebook_repository import FacebookRepository
from infrastructure.repositories.social_media_repository import SocialMediaRepository

logger = logging.getLogger(__name__)


class UnifiedPostingService:
    async def unified_post(self, request: UnifiedPostRequest, current_user_email: str) -> UnifiedPostResponse:
        """
        Unified orchestration to post to Instagram, Facebook, or both.
        Mirrors the existing router behavior, but lives in the application layer.
        """
        results: List[PlatformResult] = []

        # Platform mapping
        target_platforms: List[str] = []
        if request.platform == PlatformEnum.INSTAGRAM:
            target_platforms = ["instagram"]
        elif request.platform == PlatformEnum.FACEBOOK:
            target_platforms = ["facebook"]
        elif request.platform == PlatformEnum.BOTH:
            target_platforms = ["instagram", "facebook"]

        for platform in target_platforms:
            try:
                if platform == "instagram":
                    res = await self._post_instagram(request, current_user_email)
                    results.append(
                        PlatformResult(
                            platform="instagram",
                            status=res.status,
                            post_id=res.post_id,
                            external_id=res.instagram_post_id,
                            error=res.error,
                        )
                    )

                elif platform == "facebook":
                    res = await self._post_facebook(request, current_user_email)
                    results.append(
                        PlatformResult(
                            platform="facebook",
                            status=(res.status or "").lower(),
                            post_id=res.post_id,
                            external_id=res.facebook_post_id,
                            error=res.error,
                        )
                    )
            except HTTPException as e:
                logger.warning("Handled HTTPException for %s: %s", platform, e.detail)
                results.append(PlatformResult(platform=platform, status="failed", error=str(e.detail)))
            except Exception as e:
                logger.error("Error posting to %s: %s", platform, e)
                results.append(
                    PlatformResult(
                        platform=platform,
                        status="failed",
                        error="Internal platform error. Please check connection and try again.",
                    )
                )

        success = any(r.status in ["published", "scheduled"] for r in results)
        return UnifiedPostResponse(
            success=success,
            results=results,
            message="Posting operation completed" if success else "Posting operation failed",
        )

    async def _post_instagram(self, request: UnifiedPostRequest, current_user_email: str):
        # Verify Instagram connection exists
        ig_repo = InstagramRepository()
        ig_account = await ig_repo.find_by_user_id(current_user_email)
        if not ig_account or not ig_account.ig_business_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Instagram account not connected. Please connect Instagram first.",
            )

        ig_business_id = ig_account.ig_business_id

        ig_request = InstagramPostRequest(
            mode=IGPostMode.POST_NOW
            if request.mode == PostModeEnum.POST_NOW
            else IGPostMode.SCHEDULE_POST
            if request.mode == PostModeEnum.SCHEDULE_POST
            else IGPostMode.POST_STORY,
            media_url=request.media_url,
            caption=request.caption,
            scheduled_time=request.scheduled_time,
        )

        api_client = InstagramGraphAPIClient()
        post_repo = InstagramPostRepository()
        scheduled_repo = ScheduledPostRepository()
        story_repo = StoryPostRepository()
        notification_service = NotificationService()

        if ig_request.mode == IGPostMode.POST_NOW:
            use_case = PostNowUseCase(post_repo, api_client, notification_service)
            result = await use_case.execute(
                user_id=current_user_email,
                ig_business_id=ig_business_id,
                media_url=ig_request.media_url,
                caption=ig_request.caption,
                media_type=MediaType.IMAGE,
            )
            from presentation.schemas.instagram_posting_schemas import InstagramPostResponse

            return InstagramPostResponse(**result)

        if ig_request.mode == IGPostMode.SCHEDULE_POST:
            if not ig_request.scheduled_time:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="scheduled_time is required")
            scheduled_dt = datetime.fromisoformat(ig_request.scheduled_time.replace("Z", "+00:00"))
            use_case = SchedulePostUseCase(scheduled_repo)
            result = await use_case.execute(
                user_id=current_user_email,
                ig_business_id=ig_business_id,
                media_url=ig_request.media_url,
                scheduled_time=scheduled_dt,
                caption=ig_request.caption,
                media_type=MediaType.IMAGE,
            )
            from presentation.schemas.instagram_posting_schemas import InstagramPostResponse

            return InstagramPostResponse(
                status=result["status"],
                post_id=result.get("scheduled_post_id"),
                instagram_post_id=None,
                scheduled_time=result.get("scheduled_time"),
                error=result.get("error"),
            )

        # story
        use_case = PostStoryUseCase(story_repo, api_client)
        result = await use_case.execute(
            user_id=current_user_email,
            ig_business_id=ig_business_id,
            media_url=ig_request.media_url,
            media_type=MediaType.STORIES,
        )
        from presentation.schemas.instagram_posting_schemas import InstagramPostResponse

        return InstagramPostResponse(
            status=result["status"],
            post_id=result.get("story_id"),
            instagram_post_id=result.get("instagram_story_id"),
            scheduled_time=None,
            error=result.get("error"),
        )

    async def _post_facebook(self, request: UnifiedPostRequest, current_user_email: str):
        # Resolve page_id if not provided
        page_id: Optional[str] = request.facebook_page_id
        if not page_id:
            fb_repo = FacebookRepository()
            fb_conn = await fb_repo.find_by_user_id(current_user_email)
            if fb_conn:
                page_id = fb_conn.page_id

        if not page_id:
            from presentation.schemas.facebook_posting_schemas import FacebookPostResponse

            return FacebookPostResponse(
                status="failed",
                post_id=None,
                facebook_post_id=None,
                scheduled_time=None,
                error="Facebook Page ID unknown. Please reconnect Facebook in Integrations.",
                page_id=None,
                page_name=None,
            )

        if request.mode == PostModeEnum.POST_STORY:
            from presentation.schemas.facebook_posting_schemas import FacebookPostResponse

            return FacebookPostResponse(
                status="failed",
                post_id=None,
                facebook_post_id=None,
                scheduled_time=None,
                error="Facebook Stories are not currently supported for automated posting. Please use Instagram Stories.",
                page_id=page_id,
                page_name=None,
            )

        fb_request = FacebookPostRequest(
            mode=FBPostMode.POST_NOW if request.mode == PostModeEnum.POST_NOW else FBPostMode.SCHEDULE_POST,
            page_id=page_id,
            media_type=MediaTypeEnum.PHOTO,
            media_url=request.media_url,
            message=request.caption,
            scheduled_time=datetime.fromisoformat(request.scheduled_time.replace("Z", "+00:00")) if request.scheduled_time else None,
        )

        post_repo = FacebookPostRepository()
        scheduled_repo = ScheduledFacebookPostRepository()
        facebook_repo = FacebookRepository()
        social_media_repo = SocialMediaRepository()

        try:
            async with FacebookGraphAPIClient() as api_client:
                if fb_request.mode == FBPostMode.POST_NOW:
                    use_case = PostNowToPageUseCase(
                        api_client=api_client, post_repository=post_repo, facebook_repository=facebook_repo
                    )
                    post = await use_case.execute(
                        user_id=current_user_email,
                        page_id=fb_request.page_id,
                        media_type=fb_request.media_type.value,
                        media_url=fb_request.media_url,
                        message=fb_request.message,
                        title=fb_request.title,
                    )
                    from presentation.schemas.facebook_posting_schemas import FacebookPostResponse

                    return FacebookPostResponse(
                        status=post.status,
                        post_id=str(post.id),
                        facebook_post_id=post.facebook_post_id,
                        scheduled_time=None,
                        error=post.error,
                        page_id=post.page_id,
                        page_name=post.page_name,
                    )

                use_case = SchedulePagePostUseCase(
                    scheduled_post_repository=scheduled_repo, facebook_repository=facebook_repo
                )
                scheduled_post = await use_case.execute(
                    user_id=current_user_email,
                    page_id=fb_request.page_id,
                    media_type=fb_request.media_type.value,
                    media_url=fb_request.media_url,
                    message=fb_request.message,
                    title=fb_request.title,
                    scheduled_time=fb_request.scheduled_time,
                )
                from presentation.schemas.facebook_posting_schemas import FacebookPostResponse

                return FacebookPostResponse(
                    status=scheduled_post.status,
                    post_id=str(scheduled_post.id),
                    facebook_post_id=None,
                    scheduled_time=scheduled_post.scheduled_time,
                    error=None,
                    page_id=scheduled_post.page_id,
                    page_name=scheduled_post.page_name,
                )
        except FacebookAPIError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Facebook API error: {str(e)}",
            ) from e

