from beanie import Document, Indexed
from pydantic import Field
from typing import Optional
from datetime import datetime


class GoogleBusinessLocationModel(Document):
    user_id: str = Indexed()
    business_name: Optional[str]
    address: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    place_id: Optional[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "google_business_locations"
