from beanie import Document, Indexed
from pydantic import Field
from datetime import datetime, timedelta
from typing import Optional


class OAuthStateModel(Document):
    user_id: str = Indexed()
    state: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(minutes=10))

    class Settings:
        name = "oauth_states"
