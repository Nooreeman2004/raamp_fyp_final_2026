# Infrastructure Layer - User MongoDB Document
from beanie import Document
from datetime import datetime
from typing import Optional, Dict
from pydantic import EmailStr, Field


class UserModel(Document):
    """MongoDB document for User collection"""
    username: str = Field(..., min_length=7, max_length=20)
    email: EmailStr
    password_hash: str
    agreed_to_terms: bool = False
    is_verified: bool = False
    verification_code: Optional[str] = None
    code_expires_at: Optional[datetime] = None
    code_sent_at: Optional[datetime] = None
    
    # Profile fields - allow missing/null values from older records
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    phone_number: Optional[str] = ""
    company: Optional[str] = ""
    role: Optional[str] = ""
    bio: Optional[str] = ""
    business_domain: Optional[str] = None  # ObjectId reference to BusinessDomain
    profile_completed: bool = False
    
    # Geographic location (LOCKED after onboarding)
    onboarding_location: Optional[str] = Field(None, description="Geographic location set during onboarding - locked for trend analysis")
    
    # Connection flags
    facebook_connected: bool = False
    instagram_connected: bool = False
    google_maps_connected: bool = False
    # Note: Google Maps place details are now stored in BusinessModel (Single Source of Truth)
    
    # Auto-generated fields
    profile_picture: str = Field(default="https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_960_720.png")
    is_admin: bool = False
    subscription: Dict = Field(default_factory=lambda: {"type": "free", "credits": 5})
    last_login: datetime = Field(default_factory=datetime.utcnow)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Billing fields
    subscriptionTier: str = "free"
    adCreditsRemaining: int = 5
    subscriptionEndDate: Optional[datetime] = None
    stripeCustomerId: Optional[str] = None
    stripeSubscriptionId: Optional[str] = None
    subscriptionStatus: str = "inactive"  # inactive, active, canceled, past_due
    cancelAtPeriodEnd: bool = False
    currentPeriodEnd: Optional[datetime] = None
    processed_stripe_events: list[str] = Field(default_factory=list)
    
    class Settings:
        name = "users"  # Collection name
        indexes = [
            "username",  # Index on username
            "email",     # Index on email
        ]

