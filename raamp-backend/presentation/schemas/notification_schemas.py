from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List, Any, Annotated, Union
from datetime import datetime
from infrastructure.database.models.notification_model import NotificationType
from beanie import PydanticObjectId

# --- Notification Schemas ---

class NotificationResponse(BaseModel):
    id: str
    type: NotificationType
    title: str
    message: str
    read: bool
    created_at: datetime
    related_entity_id: Optional[str] = None
    metadata: Dict[str, Any] = {}

    @field_validator("id", mode="before")
    @classmethod
    def convert_id(cls, v: Any) -> str:
        if isinstance(v, PydanticObjectId) or hasattr(v, "__str__"):
            return str(v)
        return v

class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    unread_count: int

class NotificationCreateRequest(BaseModel):
    # Mostly used internally, but good to have
    user_id: str
    type: NotificationType
    title: str
    message: str
    related_entity_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}

# --- WebSocket ---
class WebSocketMessage(BaseModel):
    event: str  # e.g., "new_notification"
    data: NotificationResponse

# --- Preferences Update (Shared/Extend settings_schemas) ---
# We might reuse existing Settings logic but extend schemas here if needed
# For now, we will rely on settings_schemas for the Preferences logic, 
# or import them there.
