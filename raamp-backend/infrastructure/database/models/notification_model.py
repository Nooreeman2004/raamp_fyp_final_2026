"""
Notification Model for MongoDB
Collection: notifications
"""
from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from pymongo import IndexModel


class NotificationType(str, Enum):
    MESSAGE = "message"
    ALERT = "alert"
    REMINDER = "reminder"
    SYSTEM = "system"
    CAMPAIGN = "campaign"
    BILLING = "billing"
    SOCIAL_POST = "social_post"
    AI_CREATIVE = "ai_creative"
    TREND_SPIKE = "trend_spike"
    TREND_DISCOVERED = "trend_discovered"


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

    # UI ordering / importance (higher appears first)
    # Convention: 10=high (spike/opportunity), 1=low (discovery), 0=default.
    priority: int = Field(default=0, description="Notification priority for UI ordering (higher = more important)")
    
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
            "priority",
            ("user_id", "read"),  # Compound index for fetching unread
            # NOTE:
            # A TTL index on created_at is useful in production, but can conflict with
            # pre-existing non-TTL indexes (IndexOptionsConflict) in existing databases.
            # If you want retention, add it via a controlled migration (drop/recreate index),
            # or switch to an explicit `expires_at` field with a TTL index on that field.
        ]
