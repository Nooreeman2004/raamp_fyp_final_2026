"""
Settings Schemas - Pydantic models for notification, security, billing, and geo-intent endpoints
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import re


# ============================================
# NOTIFICATION SETTINGS SCHEMAS
# ============================================

class NotificationSettingsRequest(BaseModel):
    """Request model for saving/updating notification settings - ALL fields required"""
    email_alerts: bool = Field(..., description="Enable email notifications")
    sms_alerts: bool = Field(..., description="Enable SMS notifications")
    push_notifications: bool = Field(..., description="Enable push notifications")
    marketing_alerts: bool = Field(..., description="Enable marketing/promotional notifications")
    campaign_alerts: bool = Field(default=True, description="Enable campaign performance alerts")
    performance_alerts: bool = Field(default=True, description="Enable performance report alerts")
    trend_alerts: bool = Field(default=True, description="Enable trend detection alerts")
    billing_alerts: bool = Field(default=True, description="Enable billing/payment alerts")


class NotificationSettingsResponse(BaseModel):
    """Response model for notification settings"""
    success: bool = True
    message: str = "Notification settings saved successfully"
    data: dict = Field(..., description="Saved notification settings")
    updated_at: str = Field(..., description="Timestamp of last update")


class NotificationSettingsGetResponse(BaseModel):
    """Response model for fetching notification settings"""
    success: bool = True
    email_alerts: bool
    sms_alerts: bool
    push_notifications: bool
    marketing_alerts: bool
    campaign_alerts: bool
    performance_alerts: bool
    trend_alerts: bool
    billing_alerts: bool
    updated_at: str


# ============================================
# SECURITY SETTINGS SCHEMAS
# ============================================

class SecuritySettingsRequest(BaseModel):
    """Request model for saving/updating security settings - ALL fields required"""
    two_factor_enabled: bool = Field(..., description="Enable two-factor authentication")
    login_alerts: bool = Field(..., description="Receive alerts on new login attempts")
    session_timeout_minutes: int = Field(..., ge=5, le=1440, description="Session timeout in minutes (5-1440)")
    trusted_devices_only: bool = Field(..., description="Allow login only from trusted devices")
    password_change_required: bool = Field(..., description="Require periodic password changes")


class SecuritySettingsResponse(BaseModel):
    """Response model for security settings"""
    success: bool = True
    message: str = "Security settings saved successfully"
    data: dict = Field(..., description="Saved security settings")
    updated_at: str = Field(..., description="Timestamp of last update")


class SecuritySettingsGetResponse(BaseModel):
    """Response model for fetching security settings"""
    success: bool = True
    two_factor_enabled: bool
    login_alerts: bool
    session_timeout_minutes: int
    trusted_devices_only: bool
    password_change_required: bool
    updated_at: str


# ============================================
# BILLING PROFILE SCHEMAS
# ============================================

class BillingProfileRequest(BaseModel):
    """Request model for saving/updating billing profile - ALL fields required"""
    # Personal/Company Info
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name on billing account")
    company_name: str = Field(..., min_length=2, max_length=100, description="Company/business name")
    email: str = Field(..., description="Billing email address")
    phone: str = Field(..., min_length=10, max_length=20, description="Billing phone number")
    
    # Address
    address_line1: str = Field(..., min_length=5, max_length=200, description="Street address line 1")
    address_line2: str = Field(..., max_length=200, description="Street address line 2 (optional but required to send)")
    city: str = Field(..., min_length=2, max_length=100, description="City")
    state: str = Field(..., min_length=2, max_length=100, description="State/Province")
    postal_code: str = Field(..., min_length=3, max_length=20, description="Postal/ZIP code")
    country: str = Field(..., min_length=2, max_length=100, description="Country")
    
    # Tax Info
    tax_id: str = Field(..., min_length=5, max_length=50, description="Tax ID / VAT number")
    
    # Payment Method (stored securely - no actual card numbers in production)
    payment_method_type: str = Field(..., pattern="^(credit_card|debit_card|bank_transfer|paypal)$", description="Payment method type")
    card_last_four: str = Field(..., min_length=4, max_length=4, description="Last 4 digits of card")
    card_expiry_month: int = Field(..., ge=1, le=12, description="Card expiry month")
    card_expiry_year: int = Field(..., ge=2024, le=2050, description="Card expiry year")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()
    
    @field_validator('card_last_four')
    @classmethod
    def validate_card_last_four(cls, v):
        if not v.isdigit():
            raise ValueError('Card last four must be digits only')
        return v


class BillingProfileResponse(BaseModel):
    """Response model for billing profile operations"""
    success: bool = True
    message: str = "Billing profile saved successfully"
    data: dict = Field(..., description="Saved billing profile (sensitive data masked)")
    updated_at: str = Field(..., description="Timestamp of last update")


class BillingProfileGetResponse(BaseModel):
    """Response model for fetching billing profile"""
    success: bool = True
    full_name: str
    company_name: str
    email: str
    phone: str
    address_line1: str
    address_line2: str
    city: str
    state: str
    postal_code: str
    country: str
    tax_id: str
    payment_method_type: str
    card_last_four: str
    card_expiry_month: int
    card_expiry_year: int
    updated_at: str


# ============================================
# WALLET / ADD FUNDS SCHEMAS
# ============================================

class AddFundsRequest(BaseModel):
    """Request model for adding funds to wallet"""
    amount: float = Field(..., gt=0, le=10000, description="Amount to add (must be positive, max 10000)")


class AddFundsResponse(BaseModel):
    """Response model for add funds operation"""
    success: bool = True
    message: str = "Funds added successfully"
    transaction_id: str = Field(..., description="Mock transaction ID")
    amount_added: float = Field(..., description="Amount that was added")
    previous_balance: float = Field(..., description="Balance before transaction")
    new_balance: float = Field(..., description="Updated wallet balance")
    processing_time_ms: int = Field(..., description="Simulated processing time")
    breadcrumbs: list = Field(..., description="Transaction processing steps")
    timestamp: str = Field(..., description="Transaction timestamp")


class WalletBalanceResponse(BaseModel):
    """Response model for wallet balance"""
    success: bool = True
    balance: float = Field(..., description="Current wallet balance")
    currency: str = "USD"
    last_transaction_at: Optional[str] = Field(None, description="Timestamp of last transaction")


# ============================================
# GEO-INTENT SCHEMAS
# ============================================

class HotRegion(BaseModel):
    """Model for a hot region with high ad intent"""
    region_name: str = Field(..., description="Name of the region/area")
    coordinates: dict = Field(..., description="Lat/lng coordinates")
    heat_score: int = Field(..., ge=0, le=100, description="Heat score 0-100")
    predicted_high_intent_customers: int = Field(..., description="Predicted number of high-intent customers")
    peak_hours: list = Field(..., description="Peak activity hours")
    dominant_demographics: list = Field(..., description="Top demographic groups")


class GeoIntentResponse(BaseModel):
    """Response model for geo-intent simulation"""
    success: bool = True
    request_id: str = Field(..., description="Unique request identifier")
    timestamp: str = Field(..., description="Response timestamp")
    total_regions: int = Field(..., description="Number of hot regions found")
    hot_regions: list[HotRegion] = Field(..., description="List of hot regions for ads")
    analysis_metadata: dict = Field(..., description="Additional analysis info")


# ============================================
# BUSINESS SPECIALTIES SCHEMAS
# ============================================

class SpecialtiesUpdateRequest(BaseModel):
    """Request model for updating business specialties"""
    specialties: list[str] = Field(
        ..., 
        description="List of business specialties for enhanced trend detection",
        max_length=10,
        examples=[["bubble tea", "matcha", "vegan"], ["streetwear", "vintage", "sustainable"]]
    )

    @field_validator("specialties")
    @classmethod
    def validate_specialties(cls, v):
        """Validate specialties list"""
        if len(v) > 10:
            raise ValueError("Maximum 10 specialties allowed")
        
        for specialty in v:
            if len(specialty) > 50:
                raise ValueError(f"Specialty '{specialty}' exceeds 50 character limit")
        
        return v


class SpecialtiesUpdateResponse(BaseModel):
    """Response model for business specialties operations"""
    success: bool = True
    message: str = Field(..., description="Operation result message")
    specialties: list[str] = Field(..., description="Current business specialties")


# ============================================
# ERROR RESPONSE
# ============================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
