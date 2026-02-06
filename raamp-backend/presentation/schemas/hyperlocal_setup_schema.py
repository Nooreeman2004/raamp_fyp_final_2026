"""
Pydantic schemas for Hyperlocal Business Setup
"""
from pydantic import BaseModel, Field, validator
from typing import Optional


class HyperlocalBusinessSetupRequest(BaseModel):
    """Request schema for hyperlocal business setup - ALL FIELDS REQUIRED"""
    
    business_name: str = Field(..., min_length=1, description="Business name (required)")
    business_type: str = Field(..., min_length=1, description="Business type/category (required)")
    latitude: float = Field(0.0, description="Business location latitude")
    longitude: float = Field(0.0, description="Business location longitude")
    place_id: Optional[str] = Field(None, description="Google Place ID")
    formatted_address: Optional[str] = Field(None, description="Formatted address from Google")
    website: Optional[str] = Field(None, description="Business website")
    phone: Optional[str] = Field(None, description="Business phone")
    description: Optional[str] = Field(None, description="Business description")
    city: Optional[str] = Field(None, description="Business city")
    country: Optional[str] = Field(None, description="Business country")
    
    @validator('business_name')
    @classmethod
    def validate_business_name(cls, v):
        """Validate business name"""
        if not v or not v.strip():
            raise ValueError('Business name cannot be empty')
        return v.strip()
    
    @validator('business_type')
    @classmethod
    def validate_business_type(cls, v):
        """Validate business type"""
        if not v or not v.strip():
            raise ValueError('Business type cannot be empty')
        return v.strip()
    
    @validator('latitude')
    @classmethod
    def validate_latitude(cls, v):
        """Validate latitude range"""
        if v < -90 or v > 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v
    
    @validator('longitude')
    @classmethod
    def validate_longitude(cls, v):
        """Validate longitude range"""
        if v < -180 or v > 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v


class HyperlocalBusinessLocationResponse(BaseModel):
    """Response schema for getting stored location"""
    
    has_location: bool = Field(..., description="Whether user has a stored location")
    business_name: Optional[str] = Field(None, description="Business name from Google")
    formatted_address: Optional[str] = Field(None, description="Formatted address")
    latitude: Optional[float] = Field(None, description="Latitude")
    longitude: Optional[float] = Field(None, description="Longitude")
    place_id: Optional[str] = Field(None, description="Google Place ID")


class HyperlocalBusinessSetupResponse(BaseModel):
    """Response schema for hyperlocal business setup"""
    
    success: bool = True
    message: str = "Hyperlocal business setup completed successfully"
    business_name: str
    business_type: str
    latitude: float
    longitude: float
    place_id: Optional[str] = None
    formatted_address: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
