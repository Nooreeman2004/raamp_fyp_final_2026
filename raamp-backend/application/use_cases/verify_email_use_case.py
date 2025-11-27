# Application Layer - New Verify Email Use Case (Creates User Account)
from typing import Optional, Dict, Tuple
from datetime import datetime
from domain.entities.user import User
from infrastructure.repositories.pending_verification_repository import PendingVerificationRepository
from infrastructure.repositories.user_repository_impl import UserRepository
from application.utils.otp_utils import OTPGenerator
from application.services.mailtrap_service import MailtrapService


class VerifyEmailUseCase:
    """
    New verify email flow: Validate OTP, create user account, send welcome email
    """
    
    def __init__(
        self, 
        pending_repo: PendingVerificationRepository,
        user_repository: UserRepository,
        email_service: MailtrapService
    ):
        self.pending_repo = pending_repo
        self.user_repository = user_repository
        self.email_service = email_service
    
    async def execute(self, email: str, code: str) -> Tuple[bool, Optional[Dict[str, str]]]:
        """
        Verify email with 6-digit OTP code and create user account
        
        Args:
            email: User's email address
            code: 6-digit OTP code from user
            
        Returns:
            Tuple of (success: bool, errors: Optional[Dict])
        """
        errors = {}
        
        # Find pending verification by email
        pending = await self.pending_repo.find_by_email(email.lower())
        
        if not pending:
            errors["email"] = "No pending verification found. Please sign up first."
            return False, errors
        
        # Validate OTP
        is_valid, error_message = OTPGenerator.is_otp_valid(
            otp_code=code,
            user_otp=pending.verification_code,
            expires_at=pending.code_expires_at
        )
        
        if not is_valid:
            errors["code"] = error_message
            return False, errors
        
        # Check if verification is already being processed (race condition protection)
        if await self.pending_repo.is_locked(email.lower()):
            errors["system"] = "Verification is already being processed. Please wait."
            return False, errors
        
        # Acquire verification lock
        await self.pending_repo.set_verification_lock(email.lower(), True)
        
        try:
            # Double-check if user already exists after acquiring lock
            existing_user = await self.user_repository.find_by_email(email.lower())
            if existing_user:
                errors["email"] = "User account already exists. Please sign in."
                return False, errors
            
            # Create user entity from pending verification
            user = User(
                id=None,
                username=pending.username,
                email=pending.email,
                password_hash=pending.password_hash,
                agreed_to_terms=pending.agreed_to_terms,
                is_verified=True,  # Already verified via OTP
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Create user in database
            created_user = await self.user_repository.create(user)
            
            if not created_user:
                errors["system"] = "Failed to create user account"
                return False, errors
            
            # Delete pending verification
            await self.pending_repo.delete_by_email(email.lower())
            
            # Send welcome email (do not fail the verification flow if email sending fails)
            try:
                await self.email_service.send_welcome_email(
                    to_email=created_user.email,
                    name=created_user.username
                )
            except Exception as e:
                # Log and continue - email failures should not block account creation
                print(f"❌ Failed to send welcome email for {created_user.email}: {e}")
            
            return True, None
        finally:
            # Always release lock, even if error occurred
            await self.pending_repo.set_verification_lock(email.lower(), False)
