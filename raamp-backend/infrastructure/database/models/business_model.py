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
    
    # Brand Alignment Settings - Optional until brand alignment step
    brand_logo_url: Optional[str] = Field(None, description="Firebase Storage URL for uploaded brand logo")
    primary_color: Optional[str] = Field(None, description="Primary brand color (hex code)")
    secondary_color: Optional[str] = Field(None, description="Secondary brand color (hex code)")
    tagline: Optional[str] = Field(None, max_length=100, description="Restaurant tagline")
    tone_of_voice: Optional[str] = Field(None, description="Tone of voice for AI-generated content")
    restaurant_theme: Optional[str] = Field(None, description="Restaurant theme/ambiance")
    brand_colors: list[str] = Field(default_factory=list, description="List of brand hex colors")
    palette_source: str = Field(default="custom", description="Source of the palette (template, logo, custom)")
    
    # Google Business Location (from onboarding)
    business_name: Optional[str] = Field(None, description="Business name from Google")
    business_address: Optional[str] = Field(None, description="Business address")
    city: Optional[str] = Field(None, description="Business city")
    country: Optional[str] = Field(None, description="Business country")
    google_place_id: Optional[str] = Field(None, description="Google Place ID")
    latitude: Optional[float] = Field(None, description="Business latitude")
    longitude: Optional[float] = Field(None, description="Business longitude")
    
    # Additional Details
    website: Optional[str] = Field(None, description="Business website URL")
    phone_number: Optional[str] = Field(None, description="Business contact number")
    description: Optional[str] = Field(None, description="Business description")

    # Hyperlocal Business Setup
    business_type: Optional[str] = Field(None, description="Business type/category for hyperlocal campaigns")
    
    # Business Specialties - Optional for enhanced trend detection
    specialties: list[str] = Field(default_factory=list, description="Business specialties for precise trend detection (e.g., ['bubble tea', 'matcha drinks'])")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "businesses"
        indexes = [
            "user_id",
            "google_place_id",  # Index for location lookups
        ]
