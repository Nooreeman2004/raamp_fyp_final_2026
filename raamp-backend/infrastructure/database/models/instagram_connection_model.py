from beanie import Document, Indexed
from pydantic import Field
from typing import Optional
from datetime import datetime


class InstagramConnectionModel(Document):
    user_id: str = Indexed()
    ig_business_id: Optional[str] = None
    page_access_token: Optional[str] = None  # Encrypted Facebook Page access token
    user_access_token: Optional[str] = None  # Encrypted Instagram User access token
    username: Optional[str] = None
    profile_picture_url: Optional[str] = None
    account_type: Optional[str] = None
    linked_fb_page_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    last_refreshed_at: Optional[datetime] = None
    token_valid: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "instagram_connections"
