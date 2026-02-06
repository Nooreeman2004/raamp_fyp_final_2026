"""
Notification Settings Model for MongoDB
Collection: notification_settings
"""
from beanie import Document
from pydantic import Field
from datetime import datetime


class NotificationSettingsModel(Document):
    """User notification preferences stored in MongoDB"""
    
    # User reference
    user_id: str = Field(..., description="Reference to the user")
    
    # Notification preferences - all required
    email_alerts: bool = Field(..., description="Enable email notifications")
    sms_alerts: bool = Field(..., description="Enable SMS notifications")
    push_notifications: bool = Field(..., description="Enable push notifications")
    marketing_alerts: bool = Field(..., description="Enable marketing/promotional notifications")
    
    # Granular Alerts
    campaign_alerts: bool = Field(default=True, description="Enable campaign performance alerts")
    performance_alerts: bool = Field(default=True, description="Enable performance report alerts")
    trend_alerts: bool = Field(default=True, description="Enable trend detection alerts")
    billing_alerts: bool = Field(default=True, description="Enable billing/payment alerts")
    
    message_alerts: bool = Field(default=True, description="Enable new message notifications")
    activity_alerts: bool = Field(default=True, description="Enable activity/system notifications")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "notification_settings"
        indexes = [
            "user_id",
        ]
