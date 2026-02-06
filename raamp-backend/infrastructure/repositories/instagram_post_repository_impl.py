"""
Concrete implementations of Instagram post repositories.
These adapt domain repository interfaces to Beanie/MongoDB persistence.
"""
from typing import Optional, List
from datetime import datetime, timezone
from domain.repositories.instagram_post_repository import (
    IInstagramPostRepository,
    IScheduledPostRepository,
    IStoryPostRepository
)
from domain.entities.instagram_post_entity import (
    InstagramPost,
    ScheduledPost,
    StoryPost,
    PostStatus
)
from infrastructure.database.models.instagram_post_model import (
    InstagramPostModel,
    ScheduledInstagramPostModel,
    InstagramStoryModel
)


class InstagramPostRepository(IInstagramPostRepository):
    """
    MongoDB implementation of Instagram post repository.
    Handles mapping between domain entities and database models.
    """

    async def create(self, post: InstagramPost) -> InstagramPost:
        """Create a new Instagram post record"""
        # Handle media_type - could be enum or string
        media_type_value = post.media_type.value if hasattr(post.media_type, 'value') else post.media_type
        status_value = post.status.value if hasattr(post.status, 'value') else post.status
        
        model = InstagramPostModel(
            user_id=post.user_id,
            ig_business_id=post.ig_business_id,
            media_url=post.media_url,
            caption=post.caption,
            media_type=media_type_value,
            status=status_value,
            instagram_media_id=post.instagram_media_id,
            instagram_post_id=post.instagram_post_id,
            error_message=post.error_message,
            retry_count=post.retry_count,
            published_at=post.published_at
        )
        await model.insert()
        post.created_at = model.created_at
        post.id = str(model.id)  # Store MongoDB document ID
        return post

    async def get_by_id(self, post_id: str) -> Optional[InstagramPost]:
        """Retrieve post by ID"""
        model = await InstagramPostModel.get(post_id)
        if not model:
            return None
        return self._to_entity(model)

    async def get_by_user(self, user_id: str, limit: int = 50) -> List[InstagramPost]:
        """Get posts by user ID"""
        models = await InstagramPostModel.find(
            InstagramPostModel.user_id == user_id
        ).sort(-InstagramPostModel.created_at).limit(limit).to_list()
        return [self._to_entity(m) for m in models]

    async def update_status(
        self,
        post_id: str,
        status: PostStatus,
        instagram_post_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """Update post status and related fields"""
        model = await InstagramPostModel.get(post_id)
        if not model:
            return False
        
        model.status = status.value
        model.updated_at = datetime.now(timezone.utc)
        
        if instagram_post_id:
            model.instagram_post_id = instagram_post_id
        if error_message:
            model.error_message = error_message
        if status == PostStatus.PUBLISHED:
            model.published_at = datetime.now(timezone.utc)
        
        await model.save()
        return True

    async def increment_retry_count(self, post_id: str) -> bool:
        """Increment retry counter for failed posts"""
        model = await InstagramPostModel.get(post_id)
        if not model:
            return False
        model.retry_count += 1
        model.updated_at = datetime.now(timezone.utc)
        await model.save()
        return True

    async def get_failed_posts(self, max_retries: int = 3) -> List[InstagramPost]:
        """Get failed posts that haven't exceeded retry limit"""
        models = await InstagramPostModel.find(
            InstagramPostModel.status == "failed",
            InstagramPostModel.retry_count < max_retries
        ).to_list()
        return [self._to_entity(m) for m in models]

    def _to_entity(self, model: InstagramPostModel) -> InstagramPost:
        """Convert database model to domain entity"""
        return InstagramPost(
            user_id=model.user_id,
            ig_business_id=model.ig_business_id,
            media_url=model.media_url,
            caption=model.caption,
            media_type=model.media_type,
            status=model.status,
            instagram_media_id=model.instagram_media_id,
            instagram_post_id=model.instagram_post_id,
            error_message=model.error_message,
            retry_count=model.retry_count,
            created_at=model.created_at,
            published_at=model.published_at
        )


class ScheduledPostRepository(IScheduledPostRepository):
    """
    MongoDB implementation of scheduled post repository.
    Manages deferred posting functionality.
    """

    async def create(self, scheduled_post: ScheduledPost) -> ScheduledPost:
        """Create a new scheduled post"""
        model = ScheduledInstagramPostModel(
            user_id=scheduled_post.user_id,
            ig_business_id=scheduled_post.ig_business_id,
            media_url=scheduled_post.media_url,
            caption=scheduled_post.caption,
            media_type=scheduled_post.media_type.value if hasattr(scheduled_post.media_type, 'value') else scheduled_post.media_type,
            scheduled_time=scheduled_post.scheduled_time,
            status=scheduled_post.status.value if hasattr(scheduled_post.status, 'value') else scheduled_post.status,
            instagram_post_id=scheduled_post.instagram_post_id,
            error_message=scheduled_post.error_message,
            retry_count=scheduled_post.retry_count,
            executed_at=scheduled_post.executed_at
        )
        await model.insert()
        scheduled_post.created_at = model.created_at
        return scheduled_post

    async def get_by_id(self, post_id: str) -> Optional[ScheduledPost]:
        """Retrieve scheduled post by ID"""
        model = await ScheduledInstagramPostModel.get(post_id)
        if not model:
            return None
        return self._to_entity(model)

    async def get_by_user(self, user_id: str) -> List[ScheduledPost]:
        """Get scheduled posts by user"""
        models = await ScheduledInstagramPostModel.find(
            ScheduledInstagramPostModel.user_id == user_id
        ).sort(-ScheduledInstagramPostModel.scheduled_time).to_list()
        return [self._to_entity(m) for m in models]

    async def get_pending_posts(self, before_time: datetime) -> List[ScheduledPost]:
        """Get scheduled posts that are due for execution"""
        models = await ScheduledInstagramPostModel.find(
            ScheduledInstagramPostModel.status == "scheduled",
            ScheduledInstagramPostModel.scheduled_time <= before_time
        ).sort(ScheduledInstagramPostModel.scheduled_time).to_list()
        return [self._to_entity(m) for m in models]

    async def update_status(
        self,
        post_id: str,
        status: PostStatus,
        instagram_post_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """Update scheduled post status"""
        model = await ScheduledInstagramPostModel.get(post_id)
        if not model:
            return False
        
        model.status = status.value
        model.updated_at = datetime.now(timezone.utc)
        
        if instagram_post_id:
            model.instagram_post_id = instagram_post_id
        if error_message:
            model.error_message = error_message
        if status in [PostStatus.PUBLISHED, PostStatus.FAILED]:
            model.executed_at = datetime.now(timezone.utc)
        
        await model.save()
        return True

    async def cancel(self, post_id: str) -> bool:
        """Cancel a scheduled post"""
        return await self.update_status(post_id, PostStatus.CANCELLED)

    async def delete(self, post_id: str) -> bool:
        """Delete a scheduled post"""
        # ... implementation ...
        model = await ScheduledInstagramPostModel.get(post_id)
        if not model:
            return False
        await model.delete()
        return True

    async def find_by_time_range(self, start_time: datetime, end_time: datetime) -> List[ScheduledPost]:
        """Get scheduled posts within a specific time range"""
        models = await ScheduledInstagramPostModel.find(
            ScheduledInstagramPostModel.status == "scheduled",
            ScheduledInstagramPostModel.scheduled_time >= start_time,
            ScheduledInstagramPostModel.scheduled_time <= end_time
        ).to_list()
        return [self._to_entity(m) for m in models]

    def _to_entity(self, model: ScheduledInstagramPostModel) -> ScheduledPost:
        """Convert database model to domain entity"""
        return ScheduledPost(
            user_id=model.user_id,
            ig_business_id=model.ig_business_id,
            media_url=model.media_url,
            caption=model.caption,
            media_type=model.media_type,
            scheduled_time=model.scheduled_time,
            status=model.status,
            instagram_post_id=model.instagram_post_id,
            error_message=model.error_message,
            retry_count=model.retry_count,
            created_at=model.created_at,
            executed_at=model.executed_at
        )


class StoryPostRepository(IStoryPostRepository):
    """
    MongoDB implementation of story post repository.
    Handles Instagram stories with their unique characteristics.
    """

    async def create(self, story: StoryPost) -> StoryPost:
        """Create a new story post record"""
        model = InstagramStoryModel(
            user_id=story.user_id,
            ig_business_id=story.ig_business_id,
            media_url=story.media_url,
            media_type=story.media_type.value if hasattr(story.media_type, 'value') else story.media_type,
            status=story.status.value if hasattr(story.status, 'value') else story.status,
            instagram_story_id=story.instagram_story_id,
            error_message=story.error_message,
            retry_count=story.retry_count,
            published_at=story.published_at
        )
        await model.insert()
        story.created_at = model.created_at
        story.id = str(model.id)  # Store MongoDB document ID
        return story

    async def get_by_id(self, story_id: str) -> Optional[StoryPost]:
        """Retrieve story by ID"""
        model = await InstagramStoryModel.get(story_id)
        if not model:
            return None
        return self._to_entity(model)

    async def get_by_user(self, user_id: str, limit: int = 50) -> List[StoryPost]:
        """Get stories by user"""
        models = await InstagramStoryModel.find(
            InstagramStoryModel.user_id == user_id
        ).sort(-InstagramStoryModel.created_at).limit(limit).to_list()
        return [self._to_entity(m) for m in models]

    async def update_status(
        self,
        story_id: str,
        status: PostStatus,
        instagram_story_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """Update story status"""
        model = await InstagramStoryModel.get(story_id)
        if not model:
            return False
        
        model.status = status.value
        model.updated_at = datetime.now(timezone.utc)
        
        if instagram_story_id:
            model.instagram_story_id = instagram_story_id
        if error_message:
            model.error_message = error_message
        if status == PostStatus.PUBLISHED:
            model.published_at = datetime.now(timezone.utc)
        
        await model.save()
        return True

    def _to_entity(self, model: InstagramStoryModel) -> StoryPost:
        """Convert database model to domain entity"""
        return StoryPost(
            user_id=model.user_id,
            ig_business_id=model.ig_business_id,
            media_url=model.media_url,
            media_type=model.media_type,
            status=model.status,
            instagram_story_id=model.instagram_story_id,
            error_message=model.error_message,
            retry_count=model.retry_count,
            created_at=model.created_at,
            published_at=model.published_at
        )
