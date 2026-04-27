"""
Business Model for MongoDB - stores all business/restaurant information including brand alignment
"""
from beanie import Document
from pydantic import Field, BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class BusinessTypeEnum(str, Enum):
    """Business type categories for simplified UX"""
    RESTAURANT = "restaurant"
    CAFE = "cafe"
    BAKERY = "bakery"
    RETAIL = "retail"
    SERVICE = "service"
    OTHER = "other"


class ToneOfVoiceProfileModel(BaseModel):
    personality: str
    audience: str
    language_rules: str
    platforms: List[str] = []
    content_types: List[str] = []


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
    tone_profile: Optional[ToneOfVoiceProfileModel] = Field(
        None,
        description="Structured tone-of-voice profile (personality, audience, language rules, platforms, content types)",
    )
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
    business_type: Optional[BusinessTypeEnum] = Field(None, description="Business type category (restaurant, cafe, bakery, retail, service, other)")
    targeting_radius_m: Optional[float] = Field(5000.0, description="Targeting radius in meters for geo-intent campaigns")
    is_indoor: Optional[bool] = Field(True, description="Whether the business primarily operates indoors (for weather adjustments)")
    tracking_keywords: list[str] = Field(default_factory=list, description="Keywords to track for local trends/intent")
    
    # Business Specialties - Optional for enhanced trend detection
    specialties: list[str] = Field(default_factory=list, description="Business specialties for precise trend detection (e.g., ['bubble tea', 'matcha drinks'])")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('business_type', mode='before')
    @classmethod
    def normalize_business_type(cls, v):
        """Normalize business_type to lowercase for case-insensitive matching"""
        if v is None:
            return v
        if isinstance(v, str):
            # Convert to lowercase to match enum values
            v_lower = v.lower()
            # Map common variations
            type_map = {
                'restaurant': BusinessTypeEnum.RESTAURANT,
                'cafe': BusinessTypeEnum.CAFE,
                'bakery': BusinessTypeEnum.BAKERY,
                'retail': BusinessTypeEnum.RETAIL,
                'service': BusinessTypeEnum.SERVICE,
                'other': BusinessTypeEnum.OTHER,
                # Handle legacy capitalized values
                'general': BusinessTypeEnum.OTHER,
            }
            return type_map.get(v_lower, BusinessTypeEnum.OTHER)
        return v
    
    class Settings:
        name = "businesses"
        indexes = [
            [("user_id", 1)],  # Unique index on user_id
            [("google_place_id", 1)],  # Index for location lookups
        ]
        # Enforce unique constraint - one business per user
        unique_indexes = [
            "user_id"
        ]
