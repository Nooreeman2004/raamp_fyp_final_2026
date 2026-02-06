"""
Security Settings Model for MongoDB
Collection: security_settings
"""
from beanie import Document
from pydantic import Field
from datetime import datetime


class SecuritySettingsModel(Document):
    """User security settings stored in MongoDB"""
    
    # User reference
    user_id: str = Field(..., description="Reference to the user")
    
    # Security settings - all required
    two_factor_enabled: bool = Field(..., description="Enable two-factor authentication")
    login_alerts: bool = Field(..., description="Receive alerts on new login attempts")
    session_timeout_minutes: int = Field(..., ge=5, le=1440, description="Session timeout in minutes")
    trusted_devices_only: bool = Field(..., description="Allow login only from trusted devices")
    password_change_required: bool = Field(..., description="Require periodic password changes")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "security_settings"
        indexes = [
            "user_id",
        ]
