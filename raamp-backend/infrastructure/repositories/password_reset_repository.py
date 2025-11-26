from typing import Optional
from datetime import datetime
from infrastructure.database.models.password_reset_model import PasswordResetModel


class PasswordResetRepository:
    """Repository for password reset entries"""

    async def create(
        self,
        email: str,
        reset_token: Optional[str] = None,
        otp_code: Optional[str] = None,
        expires_at: datetime = None,
    ) -> PasswordResetModel:
        """Create a new password reset entry"""
        entry = PasswordResetModel(
            email=email.lower(),
            reset_token=reset_token,
            otp_code=otp_code,
            expires_at=expires_at,
            used=False,
        )
        await entry.insert()
        return entry

    async def find_by_email(self, email: str) -> Optional[PasswordResetModel]:
        """Find the most recent unused reset entry for an email"""
        return await PasswordResetModel.find_one(
            PasswordResetModel.email == email.lower(),
            PasswordResetModel.used == False,
            PasswordResetModel.expires_at > datetime.utcnow()
        ).sort(-PasswordResetModel.created_at)

    async def find_by_token(self, reset_token: str) -> Optional[PasswordResetModel]:
        """Find reset entry by token"""
        return await PasswordResetModel.find_one(
            PasswordResetModel.reset_token == reset_token,
            PasswordResetModel.used == False,
            PasswordResetModel.expires_at > datetime.utcnow()
        )

    async def find_by_otp(self, email: str, otp_code: str) -> Optional[PasswordResetModel]:
        """Find reset entry by email and OTP code"""
        return await PasswordResetModel.find_one(
            PasswordResetModel.email == email.lower(),
            PasswordResetModel.otp_code == otp_code,
            PasswordResetModel.used == False,
            PasswordResetModel.expires_at > datetime.utcnow()
        )

    async def mark_as_used(self, entry_id: str) -> bool:
        """Mark a reset entry as used"""
        entry = await PasswordResetModel.get(entry_id)
        if not entry:
            return False
        entry.used = True
        entry.used_at = datetime.utcnow()
        await entry.save()
        return True

    async def cleanup_expired(self) -> int:
        """Delete expired reset entries"""
        now = datetime.utcnow()
        expired = await PasswordResetModel.find(
            PasswordResetModel.expires_at < now
        ).to_list()
        count = 0
        for e in expired:
            await e.delete()
            count += 1
        return count

