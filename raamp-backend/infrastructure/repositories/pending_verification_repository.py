# Infrastructure Layer - Pending Verification Repository
from typing import Optional
from datetime import datetime
from infrastructure.database.models.pending_verification_model import PendingVerificationModel


class PendingVerificationRepository:
    """Repository for pending email verifications"""
    
    async def create(
        self,
        email: str,
        username: str,
        password_hash: str,
        agreed_to_terms: bool,
        verification_code: str,
        code_expires_at: datetime,
        code_sent_at: datetime
    ) -> PendingVerificationModel:
        """Create a new pending verification entry"""
        pending = PendingVerificationModel(
            email=email.lower(),
            username=username,
            password_hash=password_hash,
            agreed_to_terms=agreed_to_terms,
            verification_code=verification_code,
            code_expires_at=code_expires_at,
            code_sent_at=code_sent_at,
            created_at=datetime.utcnow()
        )
        await pending.insert()
        return pending
    
    async def find_by_email(self, email: str) -> Optional[PendingVerificationModel]:
        """Find pending verification by email"""
        return await PendingVerificationModel.find_one(
            PendingVerificationModel.email == email.lower()
        )
    
    async def update_verification_code(
        self,
        email: str,
        code: str,
        expires_at: datetime,
        sent_at: datetime
    ) -> bool:
        """Update verification code for resend with rate limit tracking"""
        pending = await self.find_by_email(email)
        if not pending:
            return False
        
        now = datetime.utcnow()
        
        # Reset hourly counter if more than 1 hour has passed
        if pending.first_resend_at:
            if (now - pending.first_resend_at).total_seconds() > 3600:
                pending.resend_count = 0
                pending.first_resend_at = now
        else:
            pending.first_resend_at = now
        
        # Reset daily counter if more than 24 hours has passed
        if pending.daily_resend_reset_at:
            if (now - pending.daily_resend_reset_at).total_seconds() > 86400:
                pending.daily_resend_count = 0
                pending.daily_resend_reset_at = now
        else:
            pending.daily_resend_reset_at = now
        
        # Increment counters
        pending.resend_count += 1
        pending.daily_resend_count += 1
        
        pending.verification_code = code
        pending.code_expires_at = expires_at
        pending.code_sent_at = sent_at
        await pending.save()
        return True
    
    async def set_verification_lock(self, email: str, locked: bool) -> bool:
        """Set/unset verification lock to prevent race conditions"""
        pending = await self.find_by_email(email)
        if not pending:
            return False
        
        pending.is_being_verified = locked
        await pending.save()
        return True
    
    async def is_locked(self, email: str) -> bool:
        """Check if verification is locked (being processed)"""
        pending = await self.find_by_email(email)
        if not pending:
            return False
        return pending.is_being_verified
    
    async def delete_by_email(self, email: str) -> bool:
        """Delete pending verification after successful verification"""
        pending = await self.find_by_email(email)
        if not pending:
            return False
        
        await pending.delete()
        return True
    
    async def exists_by_email(self, email: str) -> bool:
        """Check if pending verification exists for email"""
        count = await PendingVerificationModel.find(
            PendingVerificationModel.email == email.lower()
        ).count()
        return count > 0
    
    async def cleanup_expired(self) -> int:
        """Remove expired pending verifications (for maintenance)"""
        now = datetime.utcnow()
        expired = await PendingVerificationModel.find(
            PendingVerificationModel.code_expires_at < now
        ).to_list()
        
        count = 0
        for pending in expired:
            await pending.delete()
            count += 1
        
        return count
