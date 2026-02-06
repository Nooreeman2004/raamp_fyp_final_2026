"""
Billing Profile Model for MongoDB
Collection: billing_profiles
"""
from beanie import Document
from pydantic import Field
from datetime import datetime


class BillingProfileModel(Document):
    """User billing profile stored in MongoDB"""
    
    # User reference
    user_id: str = Field(..., description="Reference to the user")
    
    # Personal/Company Info
    full_name: str = Field(..., description="Full name on billing account")
    company_name: str = Field(..., description="Company/business name")
    email: str = Field(..., description="Billing email address")
    phone: str = Field(..., description="Billing phone number")
    
    # Address
    address_line1: str = Field(..., description="Street address line 1")
    address_line2: str = Field("", description="Street address line 2")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State/Province")
    postal_code: str = Field(..., description="Postal/ZIP code")
    country: str = Field(..., description="Country")
    
    # Tax Info
    tax_id: str = Field(..., description="Tax ID / VAT number")
    
    # Payment Method (stored securely - masked in production)
    payment_method_type: str = Field(..., description="Payment method type")
    card_last_four: str = Field(..., description="Last 4 digits of card")
    card_expiry_month: int = Field(..., description="Card expiry month")
    card_expiry_year: int = Field(..., description="Card expiry year")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "billing_profiles"
        indexes = [
            "user_id",
            "email",
        ]
