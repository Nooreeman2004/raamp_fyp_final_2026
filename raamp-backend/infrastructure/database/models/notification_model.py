"""
Notification Model for MongoDB
Collection: notifications
"""
from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class NotificationType(str, Enum):
    MESSAGE = "message"
    ALERT = "alert"
    REMINDER = "reminder"
    SYSTEM = "system"
    CAMPAIGN = "campaign"
    BILLING = "billing"
    SOCIAL_POST = "social_post"
    AI_CREATIVE = "ai_creative"


class NotificationStatus(str, Enum):
    """Status for social post notifications"""
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"
    REMINDER = "reminder"
    PENDING = "pending"


class NotificationModel(Document):
    """
    Notification entity stored in MongoDB.
    Represents a single notification event for a user.
    """
    user_id: str = Field(..., description="Reference to the user (email)")
    type: NotificationType = Field(..., description="Type of notification")
    title: str = Field(..., description="Short title/header")
    message: str = Field(..., description="Main content body")
    read: bool = Field(default=False, description="Read status")
    
    # Social Post Specific Fields
    platform: Optional[str] = Field(None, description="Platform: instagram / facebook / twitter")
    post_id: Optional[str] = Field(None, description="Scheduled post reference ID")
    status: Optional[NotificationStatus] = Field(None, description="Post status for social_post notifications")
    error_code: Optional[str] = Field(None, description="Internal error code for debugging")
    
    # General Context
    related_entity_id: Optional[str] = Field(None, description="ID of related object (e.g., campaign_id)")
    campaign_id: Optional[str] = Field(None, description="Campaign ID if applicable")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context data")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "notifications"
        indexes = [
            "user_id",
            "created_at",
            ("user_id", "read")  # Compound index for fetching unread
        ]
