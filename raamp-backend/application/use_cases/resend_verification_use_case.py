# Application Layer - New Resend Verification Code Use Case
from typing import Optional, Dict, Tuple
from datetime import datetime
from infrastructure.repositories.pending_verification_repository import PendingVerificationRepository
from infrastructure.repositories.user_repository_impl import UserRepository
from application.utils.otp_utils import OTPGenerator
from application.services.mailtrap_service import MailtrapService
from config import OTP_MAX_RESENDS_PER_HOUR, OTP_MAX_RESENDS_PER_DAY, Config


class ResendVerificationUseCase:
    """Use case for resending OTP verification code from pending verifications"""
    
    def __init__(
        self, 
        pending_repo: PendingVerificationRepository,
        email_service: MailtrapService
    ):
        self.pending_repo = pending_repo
        self.email_service = email_service
    
    async def execute(self, email: str) -> Tuple[bool, Optional[Dict[str, str]], Optional[int]]:
        """
        Resend OTP verification code
        
        Args:
            email: User's email address
            
        Returns:
            Tuple of (success: bool, errors: Optional[Dict], remaining_seconds: Optional[int])
        """
        errors = {}
        
        # If a real user exists and is already verified, do not resend
        user_repo = UserRepository()
        existing_user = await user_repo.find_by_email(email.lower())
        if existing_user and getattr(existing_user, 'is_verified', False):
            errors['email'] = 'Email is already verified. Please sign in.'
            return False, errors, None

        # Find pending verification by email
        pending = await self.pending_repo.find_by_email(email.lower())
        
        if not pending:
            errors["email"] = "No pending verification found. Please sign up first."
            return False, errors, None
        
        # Check cooldown period (60 seconds)
        can_resend, remaining = OTPGenerator.can_resend_otp(
            last_sent_at=pending.code_sent_at,
            cooldown_seconds=60
        )
        
        if not can_resend:
            errors["cooldown"] = f"Please wait {remaining} seconds before requesting a new code"
            return False, errors, remaining
        
        # Check hourly resend limit
        if pending.resend_count >= OTP_MAX_RESENDS_PER_HOUR:
            errors["rate_limit"] = f"Maximum {OTP_MAX_RESENDS_PER_HOUR} resends per hour exceeded. Please try again later."
            return False, errors, None
        
        # Check daily resend limit
        if pending.daily_resend_count >= OTP_MAX_RESENDS_PER_DAY:
            errors["rate_limit"] = f"Maximum {OTP_MAX_RESENDS_PER_DAY} resends per day exceeded. Please try again tomorrow."
            return False, errors, None
        
        # Generate new OTP with 24-hour expiry
        otp_code, expires_at = OTPGenerator.generate_otp_with_expiry(expiry_hours=24)
        sent_at = datetime.utcnow()
        
        # Update pending verification with new OTP
        success = await self.pending_repo.update_verification_code(
            email=pending.email,
            code=otp_code,
            expires_at=expires_at,
            sent_at=sent_at
        )
        
        if not success:
            errors["system"] = "Failed to update verification code"
            return False, errors, None
        
        # Send verification email
        await self.email_service.send_verification_email(
            to_email=pending.email,
            name=pending.username,
            otp_code=otp_code
        )
        
        # Print OTP to console ONLY in development mode for testing/debugging
        if Config.ENVIRONMENT != "production":
            print("\n" + "="*70)
            print(f"🔁 RESENT OTP CODE FOR {pending.email}: {otp_code}")
            print(f"👤 Username: {pending.username}")
            print(f"⏰ Expires at: {expires_at}")
            print(f"📊 Resend count: {pending.resend_count + 1}/{OTP_MAX_RESENDS_PER_HOUR} (hourly)")
            print("="*70 + "\n")
        
        return True, None, None
