"""
Business Model for MongoDB - stores all business/restaurant information including brand alignment
"""
from beanie import Document
from pydantic import Field
from typing import Optional
from datetime import datetime


class BusinessModel(Document):
    """Business/Restaurant document stored in MongoDB"""
    
    # User reference
    user_id: str = Field(..., description="Reference to the user who owns this business")
    
    # Brand Alignment Settings - ALL REQUIRED
    brand_logo_url: str = Field(..., description="Firebase Storage URL for uploaded brand logo")
    primary_color: str = Field(..., description="Primary brand color (hex code)")
    secondary_color: str = Field(..., description="Secondary brand color (hex code)")
    tagline: str = Field(..., min_length=1, max_length=100, description="Restaurant tagline")
    tone_of_voice: str = Field(..., description="Tone of voice for AI-generated content")
    restaurant_theme: Optional[str] = Field(None, description="Restaurant theme/ambiance")
    
    # Google Business Location (from onboarding)
    business_name: Optional[str] = Field(None, description="Business name from Google")
    business_address: Optional[str] = Field(None, description="Business address")
    google_place_id: Optional[str] = Field(None, description="Google Place ID")
    latitude: Optional[float] = Field(None, description="Business latitude")
    longitude: Optional[float] = Field(None, description="Business longitude")
    
    # Hyperlocal Business Setup
    business_type: Optional[str] = Field(None, description="Business type/category for hyperlocal campaigns")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "businesses"
        indexes = [
            "user_id",
        ]
