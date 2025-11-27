from beanie import Document, Indexed
from pydantic import Field
from typing import Optional
from datetime import datetime


class SocialMediaAccountModel(Document):
    user_id: str = Indexed()
    fb_long_lived_token: Optional[str]
    page_id: Optional[str]
    page_name: Optional[str]
    page_access_token: Optional[str]
    ig_business_id: Optional[str]
    expires_at: Optional[datetime]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "social_media_accounts"
