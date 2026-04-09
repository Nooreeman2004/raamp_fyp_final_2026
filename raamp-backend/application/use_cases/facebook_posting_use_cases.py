"""
Facebook Posting Use Cases
Business logic for posting to Facebook Pages
"""
import logging
from typing import Optional
from datetime import datetime

from application.services.facebook_graph_api_service import FacebookGraphAPIClient, FacebookAPIError
from infrastructure.repositories.facebook_post_repository import (
    FacebookPostRepository,
    ScheduledFacebookPostRepository
)
from infrastructure.repositories.facebook_repository import FacebookRepository
from infrastructure.database.models.facebook_post_model import FacebookPostModel, ScheduledFacebookPostModel
from infrastructure.database.models.posting_log_model import PostingLogModel


logger = logging.getLogger(__name__)


class PostNowToPageUseCase:
    """Use case for posting content immediately to Facebook Page"""
    
    def __init__(
        self,
        api_client: FacebookGraphAPIClient,
        post_repository: FacebookPostRepository,
        facebook_repository: FacebookRepository
    ):
        self.api_client = api_client
        self.post_repository = post_repository
        self.facebook_repository = facebook_repository
    
    async def execute(
        self,
        user_id: str,
        page_id: str,
        media_type: str,
        media_url: Optional[str],
        message: Optional[str],
        title: Optional[str]
    ) -> FacebookPostModel:
        """
        Execute immediate posting to Facebook Page.
        
        Args:
            user_id: User ID
            page_id: Facebook Page ID
            media_type: PHOTO, VIDEO, or TEXT
            media_url: Media URL (for photo/video)
            message: Post message/caption
            title: Video title (for videos)
            
        Returns:
            FacebookPostModel: Created post record
            
        Raises:
            ValueError: If Facebook connection not found or page access denied
            FacebookAPIError: If posting fails
        """
        # Get Facebook connection
        facebook_conn = await self.facebook_repository.get_connection_by_user_id(user_id)
        if not facebook_conn:
            raise ValueError("Facebook connection not found. Please connect your Facebook account first.")
        
        # Verify page access - FBPage is a Pydantic model, use attributes not .get()
        user_pages = [page.id for page in facebook_conn.fb_pages]
        if page_id not in user_pages:
            raise ValueError(f"You don't have access to page {page_id}. Please reconnect your Facebook account.")
        
        # Get page name
        page_name = next(
            (page.name for page in facebook_conn.fb_pages if page.id == page_id),
            None
        )
        
        # Create post record
        post = await self.post_repository.create_post(
            user_id=user_id,
            page_id=page_id,
            page_name=page_name,
            media_type=media_type,
            media_url=media_url,
            message=message,
            title=title,
            status="PROCESSING"
        )
        
        try:
            # Get page access token
            page_access_token = await self.api_client.get_page_access_token(
                facebook_conn.access_token,
                page_id
            )
            
            # Post to Facebook
            facebook_post_id = None
            
            if media_type == "PHOTO":
                facebook_post_id = await self.api_client.post_photo(
                    page_id=page_id,
                    page_access_token=page_access_token,
                    photo_url=media_url,
                    message=message
                )
            elif media_type == "VIDEO":
                facebook_post_id = await self.api_client.post_video(
                    page_id=page_id,
                    page_access_token=page_access_token,
                    video_url=media_url,
                    title=title,
                    description=message
                )
            elif media_type == "TEXT":
                facebook_post_id = await self.api_client.post_text(
                    page_id=page_id,
                    page_access_token=page_access_token,
                    message=message
                )
            
            # Update post as published
            await self.post_repository.update_post_status(
                post_id=str(post.id),
                status="PUBLISHED",
                facebook_post_id=facebook_post_id
            )

            # Persistent Posting Log (New)
            try:
                await PostingLogModel(
                    user_id=user_id,
                    platform="facebook",
                    post_id=str(facebook_post_id),
                    internal_id=str(post.id),
                    media_url=media_url,
                    caption=message,
                    status="PUBLISHED",
                    published_at=datetime.utcnow()
                ).insert()
            except Exception as log_err:
                logger.warning(f"Failed to save persistent Facebook posting log: {log_err}")

            
            logger.info(f"Successfully posted to Facebook Page {page_id}: {facebook_post_id}")
            
            # Refresh post
            post = await self.post_repository.get_post_by_id(str(post.id))
            return post
            
        except Exception as e:
            logger.error(f"Failed to post to Facebook: {e}")
            
            # Update post as failed
            await self.post_repository.update_post_status(
                post_id=str(post.id),
                status="FAILED",
                error=str(e)
            )

            # Persistent Posting Log - Failure (New)
            try:
                await PostingLogModel(
                    user_id=user_id,
                    platform="facebook",
                    internal_id=str(post.id),
                    media_url=media_url,
                    caption=message,
                    status="FAILED",
                    error_message=str(e)
                ).insert()
            except Exception as log_err:
                logger.warning(f"Failed to save persistent Facebook failure log: {log_err}")

            
            # Refresh post
            post = await self.post_repository.get_post_by_id(str(post.id))
            raise


class SchedulePagePostUseCase:
    """Use case for scheduling a post to Facebook Page"""
    
    def __init__(
        self,
        scheduled_post_repository: ScheduledFacebookPostRepository,
        facebook_repository: FacebookRepository
    ):
        self.scheduled_post_repository = scheduled_post_repository
        self.facebook_repository = facebook_repository
    
    async def execute(
        self,
        user_id: str,
        page_id: str,
        media_type: str,
        media_url: Optional[str],
        message: Optional[str],
        title: Optional[str],
        scheduled_time: datetime
    ) -> ScheduledFacebookPostModel:
        """
        Schedule a post for later publishing.
        
        Args:
            user_id: User ID
            page_id: Facebook Page ID
            media_type: PHOTO, VIDEO, or TEXT
            media_url: Media URL (for photo/video)
            message: Post message/caption
            title: Video title (for videos)
            scheduled_time: When to publish
            
        Returns:
            ScheduledFacebookPostModel: Created scheduled post record
            
        Raises:
            ValueError: If Facebook connection not found or page access denied
        """
        # Get Facebook connection
        facebook_conn = await self.facebook_repository.get_connection_by_user_id(user_id)
        if not facebook_conn:
            raise ValueError("Facebook connection not found. Please connect your Facebook account first.")
        
        # Verify page access - FBPage is a Pydantic model, use attributes not .get()
        user_pages = [page.id for page in facebook_conn.fb_pages]
        if page_id not in user_pages:
            raise ValueError(f"You don't have access to page {page_id}. Please reconnect your Facebook account.")
        
        # Get page name
        page_name = next(
            (page.name for page in facebook_conn.fb_pages if page.id == page_id),
            None
        )
        
        # Create scheduled post record
        scheduled_post = await self.scheduled_post_repository.create_scheduled_post(
            user_id=user_id,
            page_id=page_id,
            page_name=page_name,
            media_type=media_type,
            media_url=media_url,
            message=message,
            title=title,
            scheduled_time=scheduled_time
        )
        
        logger.info(f"Scheduled Facebook post for {scheduled_time}: {scheduled_post.id}")
        
        return scheduled_post
