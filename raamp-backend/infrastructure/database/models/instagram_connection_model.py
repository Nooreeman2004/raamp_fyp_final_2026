from beanie import Document, Indexed
from pydantic import Field
from typing import Optional
from datetime import datetime


class InstagramConnectionModel(Document):
    user_id: str = Indexed()
    ig_business_id: Optional[str]
    username: Optional[str]
    profile_picture_url: Optional[str]
    account_type: Optional[str]
    linked_fb_page_id: Optional[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "instagram_connections"
