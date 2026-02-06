"""
Facebook Post Repositories
Handle database operations for Facebook posts
"""
from typing import List, Optional
from datetime import datetime
from beanie import PydanticObjectId
from infrastructure.database.models.facebook_post_model import FacebookPostModel, ScheduledFacebookPostModel
import logging

logger = logging.getLogger(__name__)


class FacebookPostRepository:
    """Repository for Facebook post operations"""
    
    async def create_post(
        self,
        user_id: str,
        page_id: str,
        page_name: Optional[str],
        media_type: str,
        media_url: Optional[str],
        message: Optional[str],
        title: Optional[str],
        status: str = "PENDING",
        facebook_post_id: Optional[str] = None
    ) -> FacebookPostModel:
        """Create a new Facebook post record"""
        post = FacebookPostModel(
            user_id=user_id,
            page_id=page_id,
            page_name=page_name,
            media_type=media_type,
            media_url=media_url,
            message=message,
            title=title,
            status=status,
            facebook_post_id=facebook_post_id
        )
        await post.insert()
        logger.info(f"Created Facebook post: {post.id}")
        return post
    
    async def update_post_status(
        self,
        post_id: str,
        status: str,
        facebook_post_id: Optional[str] = None,
        error: Optional[str] = None
    ) -> Optional[FacebookPostModel]:
        """Update post status"""
        post = await FacebookPostModel.get(PydanticObjectId(post_id))
        if not post:
            logger.warning(f"Post not found: {post_id}")
            return None
        
        post.status = status
        post.updated_at = datetime.now()
        
        if facebook_post_id:
            post.facebook_post_id = facebook_post_id
        if error:
            post.error = error
        
        await post.save()
        logger.info(f"Updated post {post_id} status to {status}")
        return post
    
    async def get_post_by_id(self, post_id: str) -> Optional[FacebookPostModel]:
        """Get post by ID"""
        return await FacebookPostModel.get(PydanticObjectId(post_id))
    
    async def get_posts_by_user(
        self,
        user_id: str,
        limit: int = 50,
        skip: int = 0
    ) -> List[FacebookPostModel]:
        """Get posts by user ID"""
        return await FacebookPostModel.find(
            FacebookPostModel.user_id == user_id
        ).sort(-FacebookPostModel.created_at).skip(skip).limit(limit).to_list()
    
    async def get_posts_by_page(
        self,
        page_id: str,
        limit: int = 50,
        skip: int = 0
    ) -> List[FacebookPostModel]:
        """Get posts by page ID"""
        return await FacebookPostModel.find(
            FacebookPostModel.page_id == page_id
        ).sort(-FacebookPostModel.created_at).skip(skip).limit(limit).to_list()


class ScheduledFacebookPostRepository:
    """Repository for scheduled Facebook post operations"""
    
    async def create_scheduled_post(
        self,
        user_id: str,
        page_id: str,
        page_name: Optional[str],
        media_type: str,
        media_url: Optional[str],
        message: Optional[str],
        title: Optional[str],
        scheduled_time: datetime
    ) -> ScheduledFacebookPostModel:
        """Create a new scheduled post record"""
        post = ScheduledFacebookPostModel(
            user_id=user_id,
            page_id=page_id,
            page_name=page_name,
            media_type=media_type,
            media_url=media_url,
            message=message,
            title=title,
            scheduled_time=scheduled_time,
            status="SCHEDULED"
        )
        await post.insert()
        logger.info(f"Created scheduled Facebook post: {post.id}")
        return post
    
    async def update_scheduled_post_status(
        self,
        post_id: str,
        status: str,
        facebook_post_id: Optional[str] = None,
        error: Optional[str] = None
    ) -> Optional[ScheduledFacebookPostModel]:
        """Update scheduled post status"""
        post = await ScheduledFacebookPostModel.get(PydanticObjectId(post_id))
        if not post:
            logger.warning(f"Scheduled post not found: {post_id}")
            return None
        
        post.status = status
        post.updated_at = datetime.now()
        
        if facebook_post_id:
            post.facebook_post_id = facebook_post_id
        if error:
            post.error = error
        if status == "PUBLISHED":
            post.published_at = datetime.now()
        
        await post.save()
        logger.info(f"Updated scheduled post {post_id} status to {status}")
        return post
    
    async def get_scheduled_post_by_id(self, post_id: str) -> Optional[ScheduledFacebookPostModel]:
        """Get scheduled post by ID"""
        return await ScheduledFacebookPostModel.get(PydanticObjectId(post_id))
    
    async def get_scheduled_posts_by_user(
        self,
        user_id: str,
        limit: int = 50,
        skip: int = 0
    ) -> List[ScheduledFacebookPostModel]:
        """Get scheduled posts by user ID"""
        return await ScheduledFacebookPostModel.find(
            ScheduledFacebookPostModel.user_id == user_id
        ).sort(ScheduledFacebookPostModel.scheduled_time).skip(skip).limit(limit).to_list()
    
    async def get_pending_scheduled_posts(
        self,
        before_time: datetime
    ) -> List[ScheduledFacebookPostModel]:
        """Get scheduled posts that are ready to be published"""
        return await ScheduledFacebookPostModel.find(
            ScheduledFacebookPostModel.status == "SCHEDULED",
            ScheduledFacebookPostModel.scheduled_time <= before_time
        ).to_list()
    
    async def cancel_scheduled_post(self, post_id: str) -> Optional[ScheduledFacebookPostModel]:
        """Cancel a scheduled post"""
        post = await ScheduledFacebookPostModel.get(PydanticObjectId(post_id))
        if not post:
            logger.warning(f"Scheduled post not found: {post_id}")
            return None
        
        if post.status != "SCHEDULED":
            logger.warning(f"Cannot cancel post with status {post.status}")
            return None
        
        post.status = "CANCELLED"
        post.updated_at = datetime.now()
        await post.save()
        logger.info(f"Cancelled scheduled post: {post_id}")
        return post
    
    async def delete_scheduled_post(self, post_id: str) -> bool:
        """Delete a scheduled post"""
        post = await ScheduledFacebookPostModel.get(PydanticObjectId(post_id))
        if not post:
            logger.warning(f"Scheduled post not found: {post_id}")
            return False
        
        await post.delete()
        logger.info(f"Deleted scheduled post: {post_id}")
        return True
