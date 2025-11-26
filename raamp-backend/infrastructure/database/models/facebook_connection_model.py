from beanie import Document, Indexed
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class FBPage(BaseModel):
    id: str
    name: Optional[str]


class FacebookConnectionModel(Document):
    user_id: str = Indexed()
    access_token: str
    fb_user_id: Optional[str]
    fb_pages: List[FBPage] = Field(default_factory=list)
    granted_scopes: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "facebook_connections"
