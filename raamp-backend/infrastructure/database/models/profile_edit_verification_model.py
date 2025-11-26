from beanie import Document
from datetime import datetime
from typing import Optional


class ProfileEditVerificationModel(Document):
    """
    Temporary storage for OTPs used to verify identity before allowing profile edits
    """
    email: str
    verification_code: str
    code_expires_at: datetime
    code_sent_at: datetime
    resend_count: int = 0
    first_resend_at: Optional[datetime] = None
    daily_resend_count: int = 0
    daily_resend_reset_at: Optional[datetime] = None
    is_being_verified: bool = False
    created_at: datetime

    class Settings:
        name = "profile_edit_verifications"
        indexes = [
            "email",
            "code_expires_at",
        ]
