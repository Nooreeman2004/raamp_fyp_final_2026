# Infrastructure Layer - Pending Verification Model
from beanie import Document
from datetime import datetime
from typing import Optional


class PendingVerificationModel(Document):
    """
    Temporary storage for user data during email verification
    User account is created only after OTP verification
    """
    email: str
    username: str
    password_hash: str
    agreed_to_terms: bool
    
    # OTP fields
    verification_code: str
    code_expires_at: datetime
    code_sent_at: datetime
    resend_count: int = 0  # Track number of resends
    first_resend_at: Optional[datetime] = None  # Track hourly window
    daily_resend_count: int = 0  # Track daily resends
    daily_resend_reset_at: Optional[datetime] = None  # Track daily window
    
    # Race condition protection
    is_being_verified: bool = False  # Lock for verification process
    
    # Metadata
    created_at: datetime
    
    class Settings:
        name = "pending_verifications"
        indexes = [
            "email",  # For fast lookup by email
            "code_expires_at"  # For cleanup of expired entries
        ]
