"""
Pydantic schemas for Brand Alignment Settings
"""
from pydantic import BaseModel, Field, validator
import re


class BrandAlignmentRequest(BaseModel):
    """Request schema for brand alignment settings - ALL FIELDS REQUIRED"""
    
    primary_color: str = Field(..., description="Primary brand color (hex code)")
    secondary_color: str = Field(..., description="Secondary brand color (hex code)")
    tagline: str = Field(..., min_length=1, max_length=100, description="Restaurant tagline")
    tone_of_voice: str = Field(..., min_length=1, description="Tone of voice for AI content")
    restaurant_theme: str = Field(None, description="Restaurant theme/ambiance")
    
    @validator('primary_color', 'secondary_color')
    @classmethod
    def validate_hex_color(cls, v):
        """Validate hex color format"""
        if not re.match(r'^#[0-9A-Fa-f]{6}$', v):
            raise ValueError('Color must be in hex format (#RRGGBB)')
        return v.upper()
    
    @validator('tagline')
    @classmethod
    def validate_tagline(cls, v):
        """Validate tagline"""
        if not v or not v.strip():
            raise ValueError('Tagline cannot be empty')
        return v.strip()
    
    @validator('tone_of_voice')
    @classmethod
    def validate_tone(cls, v):
        """Validate tone of voice"""
        if not v or not v.strip():
            raise ValueError('Tone of voice cannot be empty')
        return v.strip()


class BrandAlignmentResponse(BaseModel):
    """Response schema for brand alignment settings"""
    
    brand_logo_url: str
    primary_color: str
    secondary_color: str
    tagline: str
    tone_of_voice: str
    restaurant_theme: str | None
    updated_at: str
    
    class Config:
        from_attributes = True
