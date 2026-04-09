from beanie import Document
from datetime import datetime
from typing import Optional
from pydantic import Field
from pymongo import IndexModel, DESCENDING

class PostingLogModel(Document):
    user_id: str
    platform: str                    # "instagram" or "facebook"
    post_id: Optional[str] = None    # platform-returned post ID
    internal_id: Optional[str] = None  # RAAMP asset or caption ID
    media_url: Optional[str] = None  # URL to the image/video
    caption: Optional[str] = None    # text content of the post
    status: str                      # "PUBLISHED", "FAILED", "SCHEDULED"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Settings:
        name = "posting_logs"
        indexes = [
            IndexModel([("user_id", DESCENDING)]),
            IndexModel([("created_at", DESCENDING)]),
            IndexModel([("platform", DESCENDING)]),
        ]
