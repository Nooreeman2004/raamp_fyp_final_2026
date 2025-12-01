from typing import Optional
from datetime import datetime
from infrastructure.database.models.profile_edit_verification_model import ProfileEditVerificationModel


class ProfileEditVerificationRepository:
    """Repository for profile-edit OTP entries"""

    async def create_or_update(
        self,
        email: str,
        code: str,
        expires_at: datetime,
        sent_at: datetime,
    ) -> ProfileEditVerificationModel:
        # Upsert behavior: if exists, update counters; otherwise create
        existing = await ProfileEditVerificationModel.find_one(ProfileEditVerificationModel.email == email.lower())
        if existing:
            # reset hourly/daily windows if necessary (kept simple)
            existing.verification_code = code
            existing.code_expires_at = expires_at
            existing.code_sent_at = sent_at
            existing.resend_count += 1
            existing.daily_resend_count += 1
            await existing.save()
            return existing

        entry = ProfileEditVerificationModel(
            email=email.lower(),
            verification_code=code,
            code_expires_at=expires_at,
            code_sent_at=sent_at,
            resend_count=1,
            daily_resend_count=1,
            created_at=datetime.utcnow()
        )
        await entry.insert()
        return entry

    async def find_by_email(self, email: str) -> Optional[ProfileEditVerificationModel]:
        return await ProfileEditVerificationModel.find_one(ProfileEditVerificationModel.email == email.lower())

    async def update_verification_code(self, email: str, code: str, expires_at: datetime, sent_at: datetime) -> bool:
        entry = await self.find_by_email(email)
        if not entry:
            return False
        entry.verification_code = code
        entry.code_expires_at = expires_at
        entry.code_sent_at = sent_at
        entry.resend_count += 1
        entry.daily_resend_count += 1
        await entry.save()
        return True

    async def delete_by_email(self, email: str) -> bool:
        entry = await self.find_by_email(email)
        if not entry:
            return False
        await entry.delete()
        return True

    async def set_verification_lock(self, email: str, locked: bool) -> bool:
        entry = await self.find_by_email(email)
        if not entry:
            return False
        entry.is_being_verified = locked
        await entry.save()
        return True

    async def is_locked(self, email: str) -> bool:
        entry = await self.find_by_email(email)
        if not entry:
            return False
        return entry.is_being_verified

    async def cleanup_expired(self) -> int:
        now = datetime.utcnow()
        expired = await ProfileEditVerificationModel.find(ProfileEditVerificationModel.code_expires_at < now).to_list()
        count = 0
        for e in expired:
            await e.delete()
            count += 1
        return count
