# Infrastructure Layer - Password Reset MongoDB Document
from beanie import Document, Indexed
from datetime import datetime
from typing import Optional
from pydantic import EmailStr, Field


class PasswordResetModel(Document):
    """MongoDB document for password reset tokens/OTPs"""
    email: EmailStr = Indexed()
    reset_token: Optional[str] = None  # For link-based reset
    otp_code: Optional[str] = None  # For OTP-based reset
    expires_at: datetime
    used: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    used_at: Optional[datetime] = None

    class Settings:
        name = "password_resets"
        indexes = [
            "email",
            "reset_token",
        ]

