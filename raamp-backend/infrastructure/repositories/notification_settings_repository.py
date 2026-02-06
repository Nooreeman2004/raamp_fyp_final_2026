"""
Notification Settings Repository
Handles CRUD operations for notification_settings collection
"""
from typing import Optional
from datetime import datetime
from infrastructure.database.models.notification_settings_model import NotificationSettingsModel


class NotificationSettingsRepository:
    """Repository for notification settings operations"""
    
    async def get_by_user_id(self, user_id: str) -> Optional[NotificationSettingsModel]:
        """Get notification settings for a user"""
        return await NotificationSettingsModel.find_one(
            NotificationSettingsModel.user_id == user_id
        )
    
    async def create_or_update(
        self,
        user_id: str,
        email_alerts: bool,
        sms_alerts: bool,
        push_notifications: bool,
        marketing_alerts: bool,
        campaign_alerts: bool = True,
        performance_alerts: bool = True,
        trend_alerts: bool = True,
        billing_alerts: bool = True,
        message_alerts: bool = True,
        activity_alerts: bool = True
    ) -> NotificationSettingsModel:
        """Create or update notification settings for a user"""
        existing = await self.get_by_user_id(user_id)
        
        if existing:
            # Update existing settings
            existing.email_alerts = email_alerts
            existing.sms_alerts = sms_alerts
            existing.push_notifications = push_notifications
            existing.marketing_alerts = marketing_alerts
            existing.campaign_alerts = campaign_alerts
            existing.performance_alerts = performance_alerts
            existing.trend_alerts = trend_alerts
            existing.billing_alerts = billing_alerts
            existing.message_alerts = message_alerts
            existing.activity_alerts = activity_alerts
            existing.updated_at = datetime.utcnow()
            await existing.save()
            return existing
        else:
            # Create new settings
            settings = NotificationSettingsModel(
                user_id=user_id,
                email_alerts=email_alerts,
                sms_alerts=sms_alerts,
                push_notifications=push_notifications,
                marketing_alerts=marketing_alerts,
                campaign_alerts=campaign_alerts,
                performance_alerts=performance_alerts,
                trend_alerts=trend_alerts,
                billing_alerts=billing_alerts,
                message_alerts=message_alerts,
                activity_alerts=activity_alerts
            )
            await settings.insert()
            return settings
    
    async def delete_by_user_id(self, user_id: str) -> bool:
        """Delete notification settings for a user"""
        existing = await self.get_by_user_id(user_id)
        if existing:
            await existing.delete()
            return True
        return False
