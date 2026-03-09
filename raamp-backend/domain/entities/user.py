# Domain Layer - User Entity
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict


@dataclass
class User:
    """User domain entity - represents the core business object"""
    id: Optional[str]  # MongoDB uses string ObjectId
    username: str
    email: str
    password_hash: str
    agreed_to_terms: bool
    is_verified: bool = False
    verification_code: Optional[str] = None
    code_expires_at: Optional[datetime] = None
    code_sent_at: Optional[datetime] = None
    
    # Profile fields - All required
    first_name: str = ""
    last_name: str = ""
    phone_number: str = ""
    company: str = ""
    role: str = ""
    bio: str = ""
    business_domain: Optional[str] = None  # ObjectId reference to BusinessDomain
    profile_completed: bool = False
    
    # Connection flags
    facebook_connected: bool = False
    instagram_connected: bool = False
    google_maps_connected: bool = False
    
    # Auto-generated fields
    profile_picture: Optional[str] = None  # URL or path to profile picture
    is_admin: bool = False
    subscription: Optional[Dict] = None  # {"type": "free", "credits": 5}
    last_login: Optional[datetime] = None
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Billing fields
    subscriptionTier: str = "free"
    adCreditsRemaining: int = 5
    subscriptionEndDate: Optional[datetime] = None
    stripeCustomerId: Optional[str] = None
    processed_stripe_events: list[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.subscription is None:
            self.subscription = {"type": "free", "credits": 5}
        if self.profile_picture is None:
            self.profile_picture = "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_960_720.png"
        if self.last_login is None:
            self.last_login = datetime.utcnow()
        if self.processed_stripe_events is None:
            self.processed_stripe_events = []
