from typing import Optional
from datetime import datetime
from infrastructure.database.models.account_deletion_verification_model import AccountDeletionVerificationModel


class AccountDeletionVerificationRepository:
    """Repository for account deletion OTP entries"""

    async def create_or_update(
        self,
        email: str,
        code: str,
        expires_at: datetime,
        sent_at: datetime,
    ) -> AccountDeletionVerificationModel:
        """Create or update a deletion verification entry"""
        existing = await AccountDeletionVerificationModel.find_one(
            AccountDeletionVerificationModel.email == email.lower()
        )
        if existing:
            existing.verification_code = code
            existing.code_expires_at = expires_at
            existing.code_sent_at = sent_at
            existing.resend_count += 1
            existing.is_being_verified = False
            await existing.save()
            return existing

        entry = AccountDeletionVerificationModel(
            email=email.lower(),
            verification_code=code,
            code_expires_at=expires_at,
            code_sent_at=sent_at,
            resend_count=1,
            is_being_verified=False,
            created_at=datetime.utcnow()
        )
        await entry.insert()
        return entry

    async def find_by_email(self, email: str) -> Optional[AccountDeletionVerificationModel]:
        """Find deletion verification entry by email"""
        return await AccountDeletionVerificationModel.find_one(
            AccountDeletionVerificationModel.email == email.lower()
        )

    async def verify_code(self, email: str, code: str) -> bool:
        """Verify the OTP code for account deletion"""
        entry = await self.find_by_email(email)
        if not entry:
            return False
        
        # Check if code matches and is not expired
        if entry.verification_code != code:
            return False
        
        if entry.code_expires_at < datetime.utcnow():
            return False
        
        return True

    async def delete_by_email(self, email: str) -> bool:
        """Delete the verification entry after successful deletion or expiry"""
        entry = await self.find_by_email(email)
        if not entry:
            return False
        await entry.delete()
        return True

    async def set_verification_lock(self, email: str, locked: bool) -> bool:
        """Set verification lock to prevent concurrent verifications"""
        entry = await self.find_by_email(email)
        if not entry:
            return False
        entry.is_being_verified = locked
        await entry.save()
        return True

    async def is_locked(self, email: str) -> bool:
        """Check if verification is in progress"""
        entry = await self.find_by_email(email)
        if not entry:
            return False
        return entry.is_being_verified

    async def cleanup_expired(self) -> int:
        """Remove expired deletion verification entries"""
        now = datetime.utcnow()
        expired = await AccountDeletionVerificationModel.find(
            AccountDeletionVerificationModel.code_expires_at < now
        ).to_list()
        count = 0
        for e in expired:
            await e.delete()
            count += 1
        return count
