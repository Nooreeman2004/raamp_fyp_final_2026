"""
Use Cases for Instagram posting feature.
These encapsulate business logic and orchestrate domain entities and services.
Following Single Responsibility Principle (SOLID).
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from domain.entities.instagram_post_entity import (
    InstagramPost,
    ScheduledPost,
    StoryPost,
    PostStatus,
    MediaType
)
from domain.repositories.instagram_post_repository import (
    IInstagramPostRepository,
    IScheduledPostRepository,
    IStoryPostRepository
)
from application.services.instagram_graph_api_service import (
    InstagramGraphAPIClient,
    InstagramAPIError
)
from application.utils.url_validator import URLValidator
from infrastructure.database.models.posting_log_model import PostingLogModel


logger = logging.getLogger(__name__)


def _get_friendly_error(technical_error: str) -> str:
    """Map raw Meta/Instagram API error strings to actionable user-facing messages."""
    error_map = {
        "session has been invalidated": "Your Instagram/Facebook session has expired. Please reconnect your account in Integrations.",
        "validating access token": "Your Instagram access token is no longer valid. Please reconnect your account in Integrations.",
        "changed their password": "Your Instagram/Facebook session was invalidated due to a password change. Please reconnect in Integrations.",
        "error code: 190": "Your Instagram session has expired. Please reconnect your account in Integrations.",
        "Media URL is not accessible": "Instagram was temporarily unable to reach your media. Please try again in a few moments.",
        "The media URL returned an HTML page": "There was an issue with the media link. Please try re-uploading.",
        "The user is not authorized": "Your Instagram connection has expired. Please go to Integrations and reconnect.",
        "OAuthException": "Your Instagram connection has expired. Please reconnect in Integrations.",
        "The image file is too large": "Your image is too large for Instagram. Please use a file smaller than 8 MB.",
        "Unsupported aspect ratio": "The image aspect ratio is not supported by Instagram. Please use 1:1, 4:5, or 1.91:1.",
        "rate limit": "Instagram rate limit reached. Please wait a few minutes before trying again.",
        "not connected": "Instagram is not connected. Please connect your account in Integrations.",
    }

    for tech, friendly in error_map.items():
        if tech.lower() in technical_error.lower():
            return friendly

    # Suppress any remaining stack-trace / internal noise
    if any(x in technical_error for x in ("Traceback", "object at", "\n  File")):
        return "An unexpected error occurred while posting. Please try again or contact support."

    return technical_error


class PostNowUseCase:
    """
    Use Case: Post content immediately to Instagram feed.
    Orchestrates the immediate posting workflow.
    """
    
    def __init__(
        self,
        post_repository: IInstagramPostRepository,
        api_client: InstagramGraphAPIClient,
        notification_service=None  # Optional dependency injection
    ):
        self.post_repository = post_repository
        self.api_client = api_client
        self.notification_service = notification_service

    def _get_friendly_error(self, technical_error: str) -> str:
        """Delegate to module-level helper for backward compat."""
        return _get_friendly_error(technical_error)
        self.post_repository = post_repository
        self.api_client = api_client
        self.notification_service = notification_service

    async def execute(
        self,
        user_id: str,
        ig_business_id: str,
        media_url: str,
        caption: Optional[str] = None,
        media_type: MediaType = MediaType.IMAGE
    ) -> Dict[str, Any]:
        """
        Execute immediate post to Instagram feed.
        
        Returns:
            Dict with status, post_id, instagram_post_id, error
        """
        # Validate URL is publicly accessible (not localhost)
        if "localhost" in media_url or "127.0.0.1" in media_url:
            return {
                "status": "failed",
                "post_id": None,
                "instagram_post_id": None,
                "error": "Media URL is not publicly accessible. Instagram requires public URLs (Cloudinary, ngrok, or deployed server). Localhost URLs will not work."
            }
        
        # Create domain entity
        post = InstagramPost(
            user_id=user_id,
            ig_business_id=ig_business_id,
            media_url=media_url,
            caption=caption,
            media_type=media_type,
            status=PostStatus.PENDING
        )
        
        # Persist to database
        post = await self.post_repository.create(post)
        post_id = post.id  # Use MongoDB document ID
        
        try:
            # Verify URL is accessible before posting to Instagram
            logger.info(f"🔍 Verifying media URL accessibility for post {post_id}...")
            is_accessible, error_msg = await URLValidator.verify_url_accessible(media_url)
            
            if not is_accessible:
                logger.error(f"❌ URL verification failed: {error_msg}")
                await self.post_repository.update_status(
                    post_id,
                    PostStatus.FAILED,
                    error_message=error_msg
                )
                return {
                    "status": "failed",
                    "post_id": post_id,
                    "instagram_post_id": None,
                    "error": error_msg
                }
            
            logger.info(f"✅ URL verified as accessible, proceeding with Instagram post...")
            
            # Update status to processing
            await self.post_repository.update_status(post_id, PostStatus.PROCESSING)
            
            # Step 1: Create media container
            logger.info(f"Creating media container for user {user_id}")
            creation_id = await self.api_client.create_media_container(
                user_id=user_id,
                media_url=media_url,
                caption=caption,
                is_story=False
            )
            
            # For videos, wait for processing
            if media_type == MediaType.VIDEO:
                logger.info(f"Waiting for video processing: {creation_id}")
                processing_success = await self.api_client.wait_for_media_processing(
                    user_id=user_id,
                    creation_id=creation_id
                )
                if not processing_success:
                    raise InstagramAPIError("Video processing failed or timed out")
            
            # Step 2: Publish media
            logger.info(f"Publishing media: {creation_id}")
            instagram_post_id = await self.api_client.publish_media(
                user_id=user_id,
                creation_id=creation_id
            )
            
            # Update status to published
            await self.post_repository.update_status(
                post_id=post_id,
                status=PostStatus.PUBLISHED,
                instagram_post_id=instagram_post_id
            )

            # Persistent Posting Log (New)
            try:
                await PostingLogModel(
                    user_id=user_id,
                    platform="instagram",
                    post_id=str(instagram_post_id),
                    internal_id=str(post_id),
                    media_url=media_url,
                    caption=caption,
                    status="PUBLISHED",
                    published_at=datetime.utcnow()
                ).insert()
            except Exception as log_err:
                logger.warning(f"Failed to save persistent posting log: {log_err}")

            
            logger.info(f"Post published successfully: {instagram_post_id}")
            
            # Send success notification
            if self.notification_service:
                try:
                    from infrastructure.database.models.notification_model import NotificationType
                    await self.notification_service.create_and_send(
                        user_id=user_id,
                        type=NotificationType.SOCIAL_POST,
                        title="Post Published Successfully",
                        message="Your Instagram post is now live!",
                        related_entity_id=post_id,
                        metadata={
                            "platform": "instagram",
                            "post_type": "feed",
                            "instagram_post_id": instagram_post_id,
                            "status": "success"
                        }
                    )
                except Exception as notif_error:
                    logger.warning(f"Failed to send success notification: {notif_error}")
            
            return {
                "status": "published",
                "post_id": post_id,
                "instagram_post_id": instagram_post_id,
                "error": None
            }
            
        except InstagramAPIError as e:
            logger.error(f"Instagram API error: {e.message}")
            # Update status to failed
            await self.post_repository.update_status(
                post_id=post_id,
                status=PostStatus.FAILED,
                error_message=e.message
            )
            await self.post_repository.increment_retry_count(post_id)

            # Persistent Posting Log - Failure (New)
            try:
                await PostingLogModel(
                    user_id=user_id,
                    platform="instagram",
                    internal_id=str(post_id),
                    media_url=media_url,
                    caption=caption,
                    status="FAILED",
                    error_message=e.message
                ).insert()
            except Exception as log_err:
                logger.warning(f"Failed to save persistent failure log: {log_err}")

            
            # Send failure notification
            if self.notification_service:
                try:
                    from infrastructure.database.models.notification_model import NotificationType
                    friendly_error = self._get_friendly_error(e.message)
                    await self.notification_service.create_and_send(
                        user_id=user_id,
                        type=NotificationType.SOCIAL_POST,
                        title="Post Failed",
                        message=f"Post failed: {friendly_error}",
                        related_entity_id=post_id,
                        metadata={
                            "platform": "instagram",
                            "post_type": "feed",
                            "error_reason": e.message,
                            "status": "failed"
                        }
                    )
                except Exception as notif_error:
                    logger.warning(f"Failed to send failure notification: {notif_error}")
            
            return {
                "status": "failed",
                "post_id": post_id,
                "instagram_post_id": None,
                "error": self._get_friendly_error(e.message)
            }
            
        except Exception as e:
            logger.exception(f"Unexpected error during post_now: {e}")
            await self.post_repository.update_status(
                post_id=post_id,
                status=PostStatus.FAILED,
                error_message=str(e)
            )
            
            return {
                "status": "failed",
                "post_id": post_id,
                "instagram_post_id": None,
                "error": str(e)
            }


class SchedulePostUseCase:
    """
    Use Case: Schedule content for future posting.
    Does NOT call Instagram API - only persists scheduling intent.
    Background worker will trigger PostNowUseCase at scheduled time.
    """
    
    def __init__(self, scheduled_repository: IScheduledPostRepository):
        self.scheduled_repository = scheduled_repository

    async def execute(
        self,
        user_id: str,
        ig_business_id: str,
        media_url: str,
        scheduled_time: datetime,
        caption: Optional[str] = None,
        media_type: MediaType = MediaType.IMAGE
    ) -> Dict[str, Any]:
        """
        Schedule a post for future publishing.
        
        Returns:
            Dict with status, scheduled_post_id, scheduled_time, error
        """
        try:
            # Validate scheduled time is in future
            if scheduled_time <= datetime.now(timezone.utc):
                return {
                    "status": "failed",
                    "scheduled_post_id": None,
                    "scheduled_time": None,
                    "error": "Scheduled time must be in the future"
                }
            
            # Create domain entity
            scheduled_post = ScheduledPost(
                user_id=user_id,
                ig_business_id=ig_business_id,
                media_url=media_url,
                caption=caption,
                media_type=media_type,
                scheduled_time=scheduled_time,
                status=PostStatus.SCHEDULED
            )
            
            # Persist to database
            scheduled_post = await self.scheduled_repository.create(scheduled_post)
            scheduled_post_id = str(scheduled_post.created_at.timestamp())
            
            logger.info(f"Post scheduled for {scheduled_time}: {scheduled_post_id}")
            
            return {
                "status": "scheduled",
                "scheduled_post_id": scheduled_post_id,
                "scheduled_time": scheduled_time.isoformat(),
                "error": None
            }
            
        except Exception as e:
            logger.exception(f"Error scheduling post: {e}")
            return {
                "status": "failed",
                "scheduled_post_id": None,
                "scheduled_time": None,
                "error": str(e)
            }


class PostStoryUseCase:
    """
    Use Case: Post content to Instagram stories.
    Stories have special requirements (24h lifecycle, no Meta scheduling).
    """
    
    def __init__(
        self,
        story_repository: IStoryPostRepository,
        api_client: InstagramGraphAPIClient
    ):
        self.story_repository = story_repository
        self.api_client = api_client

    async def execute(
        self,
        user_id: str,
        ig_business_id: str,
        media_url: str,
        media_type: MediaType = MediaType.STORIES
    ) -> Dict[str, Any]:
        """
        Post content immediately to Instagram stories.
        
        Returns:
            Dict with status, story_id, instagram_story_id, error
        """
        # Validate URL is publicly accessible (not localhost)
        if "localhost" in media_url or "127.0.0.1" in media_url:
            return {
                "status": "failed",
                "story_id": None,
                "instagram_story_id": None,
                "error": "Media URL is not publicly accessible. Instagram requires public URLs (Cloudinary, ngrok, or deployed server). Localhost URLs will not work."
            }
        
        # Check for recent duplicate story (within 5 minutes)
        # Only prevents re-posting of successful stories, allows retry of failures
        existing_story = await self.story_repository.check_recent_duplicate(
            user_id=user_id,
            media_url=media_url,
            minutes=5
        )
        
        if existing_story:
            logger.warning(f"Duplicate story detected for user {user_id} - story {existing_story.id} already {existing_story.status}")
            # Return the existing story to prevent duplicate posting
            return {
                "status": existing_story.status.value if hasattr(existing_story.status, 'value') else existing_story.status,
                "story_id": existing_story.id,
                "instagram_story_id": existing_story.instagram_story_id,
                "error": "This story was already posted recently. Please wait a few minutes before posting the same content again."
            }
        
        # Create domain entity
        story = StoryPost(
            user_id=user_id,
            ig_business_id=ig_business_id,
            media_url=media_url,
            media_type=MediaType.STORIES,
            status=PostStatus.PENDING
        )
        
        # Persist to database
        story = await self.story_repository.create(story)
        story_id = story.id  # Use MongoDB document ID
        
        try:
            # Verify URL is accessible before posting to Instagram
            logger.info(f"🔍 Verifying media URL accessibility for story {story_id}...")
            is_accessible, error_msg = await URLValidator.verify_url_accessible(media_url)
            
            if not is_accessible:
                logger.error(f"❌ URL verification failed: {error_msg}")
                await self.story_repository.update_status(
                    story_id,
                    PostStatus.FAILED,
                    error_message=error_msg
                )
                return {
                    "status": "failed",
                    "story_id": story_id,
                    "instagram_story_id": None,
                    "error": error_msg
                }
            
            logger.info(f"✅ URL verified as accessible, proceeding with Instagram story...")
            
            # Update status to processing - wrap in try to prevent db issues from blocking posting
            try:
                await self.story_repository.update_status(story_id, PostStatus.PROCESSING)
            except Exception as db_err:
                logger.warning(f"Failed to update story status to processing for {story_id}: {db_err}")
            
            # Create and publish story (stories use single-step process)
            logger.info(f"Starting story creation for user {user_id} with ID {story_id}")
            
            # Detect video for stories explicitly
            is_video = any(ext in media_url.lower() for ext in [".mp4", ".mov", ".avi", ".m4v"]) or "video" in media_url.lower()
            api_media_type = "VIDEO" if is_video else "IMAGE"
            
            logger.info(f"Detected media type: {api_media_type} for story {story_id}")
            
            creation_id = await self.api_client.create_media_container(
                user_id=user_id,
                media_url=media_url,
                is_story=True,
                media_type=api_media_type
            )
            
            if not creation_id:
                raise InstagramAPIError("Failed to create story container: No creation ID returned from Meta.")
            
            # For video stories, wait for processing (up to 2 minutes)
            if is_video:
                logger.info(f"Waiting for video story processing (max 120s): {creation_id}")
                processing_success = await self.api_client.wait_for_media_processing(
                    user_id=user_id,
                    creation_id=creation_id,
                    max_wait_seconds=120
                )
                if not processing_success:
                    raise InstagramAPIError("Video story processing timed out on Meta's servers. Please try again with a shorter video or different format.")
            
            # Publish story
            logger.info(f"Publishing story: {creation_id} for user {user_id}")
            try:
                instagram_story_id = await self.api_client.publish_media(
                    user_id=user_id,
                    creation_id=creation_id
                )
            except Exception as e:
                err_msg = str(e).lower()
                if "reset" in err_msg or "aborted" in err_msg:
                    raise InstagramAPIError("Meta's server dropped the connection. This usually happens if the file is still processing. Please wait a moment and try again.")
                if "unsupported" in err_msg:
                    raise InstagramAPIError("This media format is not supported for stories. Please use a standard JPG, PNG, or MP4.")
                raise e
            
            # Update status to published
            try:
                await self.story_repository.update_status(
                    story_id=story_id,
                    status=PostStatus.PUBLISHED,
                    instagram_story_id=instagram_story_id
                )
                
                # Persistent Posting Log (New)
                await PostingLogModel(
                    user_id=user_id,
                    platform="instagram",
                    post_id=str(instagram_story_id),
                    internal_id=str(story_id),
                    media_url=media_url,
                    caption="[Story - No Caption]",
                    status="PUBLISHED",
                    published_at=datetime.utcnow()
                ).insert()
            except Exception as log_err:
                logger.error(f"Post succeeded but logging/db failed for story {story_id}: {log_err}")

            
            logger.info(f"Story published successfully: {instagram_story_id}")
            
            return {
                "status": "published",
                "story_id": story_id,
                "instagram_story_id": instagram_story_id,
                "error": None
            }
            
        except InstagramAPIError as e:
            logger.error(f"Instagram API error for story {story_id}: {e.message}")
            try:
                await self.story_repository.update_status(
                    story_id=story_id,
                    status=PostStatus.FAILED,
                    error_message=e.message
                )
            except Exception as db_err:
                logger.warning(f"Failed to update error status for {story_id}: {db_err}")

            friendly = _get_friendly_error(e.message)
            return {
                "status": "failed",
                "story_id": story_id,
                "instagram_story_id": None,
                "error": friendly
            }
            
        except Exception as e:
            logger.exception(f"Unexpected error during post_story for {story_id}: {e}")
            try:
                await self.story_repository.update_status(
                    story_id=story_id,
                    status=PostStatus.FAILED,
                    error_message=str(e)
                )
            except Exception as db_err:
                logger.warning(f"Failed to update unexpected error status for {story_id}: {db_err}")
            
            return {
                "status": "failed",
                "story_id": story_id,
                "instagram_story_id": None,
                "error": f"An unexpected error occurred while posting your story: {str(e)}"
            }


class ExecuteScheduledPostUseCase:
    """
    Use Case: Execute a scheduled post.
    This is called by background worker when scheduled time arrives.
    Delegates actual posting to PostNowUseCase.
    """
    
    def __init__(
        self,
        scheduled_repository: IScheduledPostRepository,
        post_now_use_case: PostNowUseCase
    ):
        self.scheduled_repository = scheduled_repository
        self.post_now_use_case = post_now_use_case

    async def execute(self, scheduled_post_id: str) -> Dict[str, Any]:
        """
        Execute a scheduled post by ID.
        
        Returns:
            Dict with execution result
        """
        try:
            # Retrieve scheduled post
            scheduled_post = await self.scheduled_repository.get_by_id(scheduled_post_id)
            if not scheduled_post:
                return {
                    "status": "failed",
                    "error": "Scheduled post not found"
                }
            
            # Check if already executed or cancelled
            if scheduled_post.status != PostStatus.SCHEDULED:
                return {
                    "status": "skipped",
                    "error": f"Post status is {scheduled_post.status}, not scheduled"
                }
            
            # Update status to processing
            await self.scheduled_repository.update_status(
                scheduled_post_id,
                PostStatus.PROCESSING
            )
            
            # Execute immediate post
            result = await self.post_now_use_case.execute(
                user_id=scheduled_post.user_id,
                ig_business_id=scheduled_post.ig_business_id,
                media_url=scheduled_post.media_url,
                caption=scheduled_post.caption,
                media_type=MediaType(scheduled_post.media_type)
            )
            
            # Update scheduled post status based on result
            if result["status"] == "published":
                await self.scheduled_repository.update_status(
                    scheduled_post_id,
                    PostStatus.PUBLISHED,
                    instagram_post_id=result.get("instagram_post_id")
                )
            else:
                await self.scheduled_repository.update_status(
                    scheduled_post_id,
                    PostStatus.FAILED,
                    error_message=result.get("error")
                )
            
            logger.info(f"Scheduled post {scheduled_post_id} executed: {result['status']}")
            return result
            
        except Exception as e:
            logger.exception(f"Error executing scheduled post {scheduled_post_id}: {e}")
            await self.scheduled_repository.update_status(
                scheduled_post_id,
                PostStatus.FAILED,
                error_message=str(e)
            )
            return {
                "status": "failed",
                "error": str(e)
            }


class GetPendingScheduledPostsUseCase:
    """
    Use Case: Retrieve posts scheduled for execution.
    Used by background worker to find posts that need processing.
    """
    
    def __init__(self, scheduled_repository: IScheduledPostRepository):
        self.scheduled_repository = scheduled_repository

    async def execute(self, current_time: Optional[datetime] = None):
        """
        Get all scheduled posts that are due for execution.
        
        Returns:
            List of ScheduledPost entities
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        return await self.scheduled_repository.get_pending_posts(current_time)
