"""
Repository interfaces for Instagram posting feature.
These define contracts that infrastructure layer must implement.
Following Dependency Inversion Principle (SOLID).
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime
from domain.entities.instagram_post_entity import InstagramPost, ScheduledPost, StoryPost, PostStatus


class IInstagramPostRepository(ABC):
    """
    Interface for Instagram post persistence.
    Defines contract without coupling to specific database implementation.
    """

    @abstractmethod
    async def create(self, post: InstagramPost) -> InstagramPost:
        """Create a new Instagram post record"""
        pass

    @abstractmethod
    async def get_by_id(self, post_id: str) -> Optional[InstagramPost]:
        """Retrieve post by ID"""
        pass

    @abstractmethod
    async def get_by_user(self, user_id: str, limit: int = 50) -> List[InstagramPost]:
        """Get posts by user ID"""
        pass

    @abstractmethod
    async def update_status(
        self,
        post_id: str,
        status: PostStatus,
        instagram_post_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """Update post status and related fields"""
        pass

    @abstractmethod
    async def increment_retry_count(self, post_id: str) -> bool:
        """Increment retry counter for failed posts"""
        pass

    @abstractmethod
    async def get_failed_posts(self, max_retries: int = 3) -> List[InstagramPost]:
        """Get failed posts that haven't exceeded retry limit"""
        pass


class IScheduledPostRepository(ABC):
    """
    Interface for scheduled post persistence.
    Separates scheduling logic from immediate posting.
    """

    @abstractmethod
    async def create(self, scheduled_post: ScheduledPost) -> ScheduledPost:
        """Create a new scheduled post"""
        pass

    @abstractmethod
    async def get_by_id(self, post_id: str) -> Optional[ScheduledPost]:
        """Retrieve scheduled post by ID"""
        pass

    @abstractmethod
    async def get_by_user(self, user_id: str) -> List[ScheduledPost]:
        """Get scheduled posts by user"""
        pass

    @abstractmethod
    async def get_pending_posts(self, before_time: datetime) -> List[ScheduledPost]:
        """Get scheduled posts that are due for execution"""
        pass

    @abstractmethod
    async def update_status(
        self,
        post_id: str,
        status: PostStatus,
        instagram_post_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """Update scheduled post status"""
        pass

    @abstractmethod
    async def cancel(self, post_id: str) -> bool:
        """Cancel a scheduled post"""
        pass

    @abstractmethod
    async def delete(self, post_id: str) -> bool:
        """Delete a scheduled post"""
        pass

    @abstractmethod
    async def find_by_time_range(self, start_time: datetime, end_time: datetime) -> List[ScheduledPost]:
        """Get scheduled posts within a specific time range"""
        pass


class IStoryPostRepository(ABC):
    """
    Interface for Instagram story persistence.
    Stories have different lifecycle than feed posts.
    """

    @abstractmethod
    async def create(self, story: StoryPost) -> StoryPost:
        """Create a new story post record"""
        pass

    @abstractmethod
    async def get_by_id(self, story_id: str) -> Optional[StoryPost]:
        """Retrieve story by ID"""
        pass

    @abstractmethod
    async def get_by_user(self, user_id: str, limit: int = 50) -> List[StoryPost]:
        """Get stories by user"""
        pass
    
    @abstractmethod
    async def check_recent_duplicate(self, user_id: str, media_url: str, minutes: int = 5) -> Optional[StoryPost]:
        """Check if a story with the same media_url was created recently"""
        pass

    @abstractmethod
    async def update_status(
        self,
        story_id: str,
        status: PostStatus,
        instagram_story_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """Update story status"""
        pass
