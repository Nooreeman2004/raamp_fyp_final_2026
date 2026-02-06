"""
Notification Service
Handles business logic for notifications, including:
- Saving to DB
- Checking user preferences
- Real-time delivery via WebSockets
- Social post lifecycle notifications (success, failure, retry)
"""
import logging
from datetime import datetime
from typing import Dict, List, Set, Optional
from fastapi import WebSocket
from infrastructure.repositories.notification_repository import NotificationRepository
from infrastructure.repositories.notification_settings_repository import NotificationSettingsRepository
from infrastructure.database.models.notification_model import NotificationType, NotificationStatus
from presentation.schemas.notification_schemas import NotificationResponse

# Connection Manager for WebSockets
class ConnectionManager:
    def __init__(self):
        # user_id -> List of active WebSockets (support multiple tabs/devices)
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logging.info(f"User {user_id} connected via WebSocket. Total connections: {len(self.active_connections[user_id])}")

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logging.info(f"User {user_id} disconnected WebSocket.")

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            # Broadcast to all open tabs for this user
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logging.error(f"Error sending WebSocket message to user {user_id}: {e}")
                    # Likely disconnected, handled by cleanup/disconnect usually
                    pass

# Singleton instance
manager = ConnectionManager()

class NotificationService:
    def __init__(self):
        self.repo = NotificationRepository()
        self.settings_repo = NotificationSettingsRepository()
    
    async def create_and_send(
        self,
        user_id: str,
        type: NotificationType,
        title: str,
        message: str,
        related_entity_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ):
        """
        Main entry point:
        1. Check user preferences
        2. Save to DB (if permitted)
        3. Push via WebSocket (if permitted + connected)
        """
        
        # 1. Check Preferences
        settings = await self.settings_repo.get_by_user_id(user_id)
        
        # Default allow if no settings exist yet
        allowed = True 
        if settings:
            # Global push check (interpretation: Does user want ANY on-screen/push alerts?)
            # Or granular checks:
            if type == NotificationType.MESSAGE and not settings.message_alerts:
                allowed = False
            elif type == NotificationType.BILLING and not getattr(settings, "billing_alerts", True):
                allowed = False
            elif type == NotificationType.CAMPAIGN and not getattr(settings, "campaign_alerts", True):
                allowed = False
            # Fallback for generic types
            elif type in (NotificationType.SYSTEM, NotificationType.ALERT, NotificationType.REMINDER) and not settings.activity_alerts:
                allowed = False
            # Check for specific metadata flags if needed (e.g. Trend Alerts which might come as SYSTEM or ALERT type)
            elif metadata and metadata.get("sub_type") == "trend" and not getattr(settings, "trend_alerts", True):
                allowed = False
            elif metadata and metadata.get("sub_type") == "performance" and not getattr(settings, "performance_alerts", True):
                 allowed = False

        if not allowed:
            logging.info(f"Notification suppressed by preferences: User={user_id}, Type={type}")
            return None

        # 2. Persist to Database
        notification = await self.repo.create(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            related_entity_id=related_entity_id,
            metadata=metadata
        )
        
        # 3. Real-time Push
        # We assume "push_notifications" in settings implies real-time UI updates
        # If settings exist and push_notifications is False, maybe we DO save it but DON'T push it?
        # Requirement: "Store all notifications... Deliver real-time... Preferences enforced before sending"
        # Usually, you still save "unread" in the inbox even if push is disabled, so the user sees it later.
        # But if the user disabled "Message Alerts", maybe they don't want it at all?
        # Standard practice: Preference controls PUSH/Email. Inbox usually receives everything unless "Blocked".
        # I will adhere to: Save always (so history exists), Push only if allowed.
        
        push_allowed = True
        if settings and not settings.push_notifications:
             push_allowed = False
             
        if push_allowed:
            payload = NotificationResponse(
                id=str(notification.id),
                type=notification.type,
                title=notification.title,
                message=notification.message,
                read=notification.read,
                created_at=notification.created_at,
                related_entity_id=notification.related_entity_id,
                metadata=notification.metadata
            ).dict()
            # Serialize dates
            payload['created_at'] = payload['created_at'].isoformat()
            
            await manager.send_personal_message(
                {"event": "new_notification", "data": payload},
                user_id
            )
            
        return notification

    async def get_user_notifications(self, user_id: str, limit: int = 50, offset: int = 0, unread_only: bool = False):
        return await self.repo.get_by_user_id(user_id, limit, offset, unread_only)

    async def get_unread_count(self, user_id: str):
        return await self.repo.get_unread_count(user_id)

    async def mark_read(self, notification_id: str, user_id: str):
        return await self.repo.mark_as_read(notification_id, user_id)

    async def mark_all_read(self, user_id: str):
        return await self.repo.mark_all_as_read(user_id)
    
    async def delete(self, notification_id: str, user_id: str):
        return await self.repo.delete_notification(notification_id, user_id)    
    # ===============================================
    # SOCIAL POST LIFECYCLE NOTIFICATIONS
    # ===============================================
    
    async def create_scheduled_post_success(
        self,
        user_id: str,
        platform: str,
        post_type: str,
        scheduled_time: datetime,
        actual_publish_time: datetime,
        post_id: str,
        instagram_post_id: Optional[str] = None,
        campaign_id: Optional[str] = None
    ):
        """Notification: Scheduled post published successfully"""
        platform_name = "Instagram" if platform == "instagram" else "Facebook"
        
        title = "Post Published Successfully"
        message = f"Your scheduled {platform_name} {post_type} was published successfully."
        
        delay = (actual_publish_time - scheduled_time).total_seconds()
        metadata = {
            "platform": platform,
            "post_type": post_type,
            "scheduled_time": scheduled_time.isoformat(),
            "actual_publish_time": actual_publish_time.isoformat(),
            "instagram_post_id": instagram_post_id,
            "campaign_id": campaign_id,
            "delay_seconds": delay,
            "status": NotificationStatus.SUCCESS.value
        }
        
        await self.create_and_send(
            user_id=user_id,
            type=NotificationType.SOCIAL_POST,
            title=title,
            message=message,
            related_entity_id=post_id,
            metadata=metadata
        )
        
        logging.info(f"✅ Created success notification: user={user_id}, post={post_id}")
    
    async def create_scheduled_post_failure(
        self,
        user_id: str,
        platform: str,
        post_type: str,
        scheduled_time: datetime,
        post_id: str,
        error_reason: str,
        error_code: Optional[str] = None,
        suggested_fix: Optional[str] = None,
        campaign_id: Optional[str] = None
    ):
        """Notification: Scheduled post failed to publish"""
        platform_name = "Instagram" if platform == "instagram" else "Facebook"
        
        # Human-readable error messages
        human_errors = {
            "token_expired": "Access token expired",
            "permission_missing": "Missing publish permissions",
            "media_upload_failed": "Media file upload failed",
            "meta_api_error": f"{platform_name} API error",
            "rate_limit": "Rate limit exceeded",
            "network_timeout": "Network timeout",
            "invalid_media": "Invalid media format",
            "job_crash": "System error occurred"
        }
        
        error_message = human_errors.get(error_code, error_reason)
        suggested_action = suggested_fix or self._get_suggested_fix(error_code)
        
        title = "Scheduled Post Failed"
        message = f"{platform_name} {post_type} failed: {error_message}. {suggested_action}"
        
        metadata = {
            "platform": platform,
            "post_type": post_type,
            "scheduled_time": scheduled_time.isoformat(),
            "error_reason": error_reason,
            "error_code": error_code,
            "suggested_fix": suggested_action,
            "campaign_id": campaign_id,
            "status": NotificationStatus.FAILED.value
        }
        
        await self.create_and_send(
            user_id=user_id,
            type=NotificationType.SOCIAL_POST,
            title=title,
            message=message,
            related_entity_id=post_id,
            metadata=metadata
        )
        
        logging.warning(f"❌ Created failure notification: user={user_id}, post={post_id}, error={error_reason}")
    
    async def create_retry_started(
        self,
        user_id: str,
        platform: str,
        post_id: str,
        retry_attempt: int,
        next_retry_time: Optional[datetime] = None
    ):
        """Notification: System is retrying a failed post"""
        platform_name = "Instagram" if platform == "instagram" else "Facebook"
        
        title = "Retrying Scheduled Post"
        message = f"Retrying {platform_name} scheduled post after failure (Attempt {retry_attempt})."
        
        if next_retry_time:
            message += f" Next attempt at {next_retry_time.strftime('%I:%M %p')}."
        
        metadata = {
            "platform": platform,
            "retry_attempt": retry_attempt,
            "next_retry_time": next_retry_time.isoformat() if next_retry_time else None,
            "status": NotificationStatus.RETRY.value
        }
        
        await self.create_and_send(
            user_id=user_id,
            type=NotificationType.SOCIAL_POST,
            title=title,
            message=message,
            related_entity_id=post_id,
            metadata=metadata
        )
    
    async def create_retry_success(
        self,
        user_id: str,
        platform: str,
        post_id: str,
        retry_attempt: int,
        instagram_post_id: Optional[str] = None
    ):
        """Notification: Retry succeeded"""
        platform_name = "Instagram" if platform == "instagram" else "Facebook"
        
        title = "Post Published After Retry"
        message = f"Your {platform_name} post was successfully published after {retry_attempt} retry attempt(s)."
        
        metadata = {
            "platform": platform,
            "retry_attempt": retry_attempt,
            "instagram_post_id": instagram_post_id,
            "status": NotificationStatus.SUCCESS.value
        }
        
        await self.create_and_send(
            user_id=user_id,
            type=NotificationType.SOCIAL_POST,
            title=title,
            message=message,
            related_entity_id=post_id,
            metadata=metadata
        )
    
    async def create_retry_failed_permanently(
        self,
        user_id: str,
        platform: str,
        post_id: str,
        max_retries: int,
        final_error: str
    ):
        """Notification: All retry attempts exhausted"""
        platform_name = "Instagram" if platform == "instagram" else "Facebook"
        
        title = "Post Failed Permanently"
        message = f"Your {platform_name} post failed after {max_retries} retry attempts. Error: {final_error}"
        
        metadata = {
            "platform": platform,
            "max_retries": max_retries,
            "final_error": final_error,
            "status": NotificationStatus.FAILED.value
        }
        
        await self.create_and_send(
            user_id=user_id,
            type=NotificationType.SOCIAL_POST,
            title=title,
            message=message,
            related_entity_id=post_id,
            metadata=metadata
        )
    
    async def create_reminder_10min_before(
        self,
        user_id: str,
        platform: str,
        post_type: str,
        scheduled_time: datetime,
        post_id: str,
        caption_preview: Optional[str] = None
    ):
        """Notification: Reminder 10 minutes before scheduled publish"""
        platform_name = "Instagram" if platform == "instagram" else "Facebook"
        
        title = "Scheduled Post Going Live Soon"
        message = f"Your {platform_name} {post_type} will go live in 10 minutes at {scheduled_time.strftime('%I:%M %p')}."
        
        if caption_preview:
            preview = caption_preview[:100]
            message += f"\\n\\nPreview: {preview}..."
        
        metadata = {
            "platform": platform,
            "scheduled_time": scheduled_time.isoformat(),
            "post_type": post_type,
            "status": NotificationStatus.REMINDER.value
        }
        
        await self.create_and_send(
            user_id=user_id,
            type=NotificationType.SOCIAL_POST,
            title=title,
            message=message,
            related_entity_id=post_id,
            metadata=metadata
        )
    
    async def create_token_expiry_warning(
        self,
        user_id: str,
        platform: str,
        expires_at: datetime,
        days_remaining: int
    ):
        """Notification: Access token expiring soon"""
        platform_name = "Instagram" if platform == "instagram" else "Facebook"
        
        title = f"{platform_name} Token Expiring Soon"
        message = f"Your {platform_name} access token expires in {days_remaining} days. Reconnect your account to avoid posting failures."
        
        metadata = {
            "platform": platform,
            "expires_at": expires_at.isoformat(),
            "days_remaining": days_remaining,
            "action_required": "reconnect_account"
        }
        
        await self.create_and_send(
            user_id=user_id,
            type=NotificationType.ALERT,
            title=title,
            message=message,
            metadata=metadata
        )
    
    async def create_job_health_alert(
        self,
        user_id: str,
        alert_type: str,
        message: str,
        metadata_extra: Optional[Dict] = None
    ):
        """Notification: System health alerts (cron job issues, etc.)"""
        title_map = {
            "job_crash": "Scheduler Job Crashed",
            "duplicate_execution": "Duplicate Job Detected",
            "time_drift": "Time Drift Detected"
        }
        
        title = title_map.get(alert_type, "System Alert")
        
        metadata = {
            "alert_type": alert_type,
            **(metadata_extra or {})
        }
        
        await self.create_and_send(
            user_id=user_id,
            type=NotificationType.SYSTEM,
            title=title,
            message=message,
            metadata=metadata
        )
    
    def _get_suggested_fix(self, error_code: Optional[str]) -> str:
        """Get suggested fix based on error code"""
        fixes = {
            "token_expired": "Reconnect your account in Settings → Connections.",
            "permission_missing": "Reconnect with proper publishing permissions.",
            "media_upload_failed": "Check media file format and size (Max 10MB).",
            "invalid_media": "Use JPG, PNG for images or MP4 for videos.",
            "rate_limit": "Post will retry automatically.",
            "network_timeout": "Post will retry automatically.",
            "job_crash": "Our team has been notified. Post will retry."
        }
        return fixes.get(error_code, "Contact support if issue persists.")