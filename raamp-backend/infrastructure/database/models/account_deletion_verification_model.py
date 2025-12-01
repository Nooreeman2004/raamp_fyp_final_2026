from beanie import Document
from datetime import datetime
from typing import Optional


class AccountDeletionVerificationModel(Document):
    """
    Temporary storage for OTPs used to verify identity before allowing account deletion.
    This is a high-security operation requiring dedicated verification.
    """
    email: str
    verification_code: str
    code_expires_at: datetime
    code_sent_at: datetime
    attempts: int = 0  # Track failed verification attempts
    max_attempts: int = 3  # Max allowed attempts before code invalidation
    is_used: bool = False  # Mark as used after successful verification
    created_at: datetime

    class Settings:
        name = "account_deletion_verifications"
        indexes = [
            "email",
            "code_expires_at",
        ]
