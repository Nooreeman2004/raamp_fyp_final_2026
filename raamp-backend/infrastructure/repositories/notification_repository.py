"""
Notification Repository
Handles CRUD operations for notifications collection
"""
from typing import List, Optional
from datetime import datetime
from beanie import PydanticObjectId
from infrastructure.database.models.notification_model import NotificationModel, NotificationType


class NotificationRepository:
    """Repository for notification operations"""
    
    async def get_by_user_id(
        self, 
        user_id: str, 
        limit: int = 50, 
        offset: int = 0,
        unread_only: bool = False
    ) -> List[NotificationModel]:
        """Get notifications for a user with pagination"""
        query = NotificationModel.find(NotificationModel.user_id == user_id)
        
        if unread_only:
            query = query.find(NotificationModel.read == False)
            
        return await query.sort(-NotificationModel.created_at).skip(offset).limit(limit).to_list()
    
    async def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications"""
        return await NotificationModel.find(
            NotificationModel.user_id == user_id,
            NotificationModel.read == False
        ).count()
        
    async def mark_as_read(self, notification_id: str, user_id: str) -> Optional[NotificationModel]:
        """Mark a specific notification as read"""
        notification = await NotificationModel.get(PydanticObjectId(notification_id))
        if notification and notification.user_id == user_id:
            notification.read = True
            await notification.save()
            return notification
        return None
        
    async def mark_all_as_read(self, user_id: str) -> int:
        """Mark all notifications for a user as read"""
        result = await NotificationModel.find(
            NotificationModel.user_id == user_id,
            NotificationModel.read == False
        ).update({"$set": {"read": True}})
        return result.modified_count

    async def create(
        self,
        user_id: str,
        type: NotificationType,
        title: str,
        message: str,
        related_entity_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> NotificationModel:
        """Create a new notification"""
        # Extract social post specific fields from metadata if present
        platform = metadata.get("platform") if metadata else None
        post_id = metadata.get("post_id") if metadata else None
        status = metadata.get("status") if metadata else None
        error_code = metadata.get("error_code") if metadata else None
        campaign_id = metadata.get("campaign_id") if metadata else None
        
        notification = NotificationModel(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            read=False,
            platform=platform,
            post_id=post_id,
            status=status,
            error_code=error_code,
            related_entity_id=related_entity_id,
            campaign_id=campaign_id,
            metadata=metadata or {},
            created_at=datetime.utcnow()
        )
        await notification.insert()
        return notification

    async def create_notification(self, *args, **kwargs) -> NotificationModel:
        """Alias for create() to support legacy calls"""
        return await self.create(*args, **kwargs)

    async def delete_notification(self, notification_id: str, user_id: str) -> bool:
        """Delete a notification"""
        notification = await NotificationModel.get(PydanticObjectId(notification_id))
        if notification and notification.user_id == user_id:
            await notification.delete()
            return True
        return False
