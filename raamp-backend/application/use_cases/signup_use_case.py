# Application Layer - New Signup Use Case (OTP Generation Only)
from typing import Optional, Dict, Tuple
from datetime import datetime
from infrastructure.repositories.pending_verification_repository import PendingVerificationRepository
from infrastructure.repositories.user_repository_impl import UserRepository
from application.validators.password_validator import PasswordValidator
from application.services.password_service import PasswordHasher
from application.services.mailtrap_service import MailtrapService
from application.utils.otp_utils import OTPGenerator


class SignupUseCase:
    """
    New signup flow: Generate OTP and send verification email
    User account is NOT created until OTP is verified
    """
    
    def __init__(
        self, 
        pending_repo: PendingVerificationRepository,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        email_service: MailtrapService
    ):
        self.pending_repo = pending_repo
        self.user_repository = user_repository
        self.password_hasher = password_hasher
        self.email_service = email_service
    
    async def execute(
        self,
        username: str,
        email: str,
        password: str,
        agreed_to_terms: bool
    ) -> Tuple[bool, Optional[Dict[str, str]]]:
        """
        Execute signup use case: Validate, generate OTP, send email
        Does NOT create user account yet
        
        Returns: (success: bool, errors: Optional[Dict])
        """
        errors = {}
        
        # Validate terms agreement
        if not agreed_to_terms:
            errors["agreed_to_terms"] = "You must agree to the Terms & Conditions and Privacy Policy"
        
        # Validate password
        is_valid, password_errors = PasswordValidator.validate(password)
        if not is_valid:
            errors["password"] = password_errors
        
        # Check for duplicate email in BOTH pending and actual users
        if await self.user_repository.exists_by_email(email):
            errors["email"] = "Email is already registered"
        
        # If email has pending verification, update it instead of failing
        existing_pending = await self.pending_repo.find_by_email(email)
        if existing_pending:
            # Check if they can resend (60 second cooldown)
            can_resend, remaining = OTPGenerator.can_resend_otp(
                last_sent_at=existing_pending.code_sent_at,
                cooldown_seconds=60
            )
            
            if not can_resend:
                errors["email"] = f"Verification already in progress. Please wait {remaining} seconds before requesting a new code or check your email."
                return False, errors
            
            # Allow updating the pending verification with new OTP
            # This helps users who changed their mind about username/password
            # We'll update the existing record instead of creating a new one
        
        # Check for duplicate username in actual users
        if await self.user_repository.exists_by_username(username):
            errors["username"] = "Username is already taken"
        
        # Return errors if validation failed
        if errors:
            return False, errors
        
        # Hash password
        print(f"🔐 Hashing password for user: {username}")
        password_hash = self.password_hasher.hash_password(password)
        
        # Generate OTP with 24-hour expiry
        otp_code, expires_at = OTPGenerator.generate_otp_with_expiry(expiry_hours=24)
        sent_at = datetime.utcnow()
        print(f"🔢 Generated OTP: {otp_code} for {email}")
        
        # If pending verification exists, update it; otherwise create new
        if existing_pending:
            # Delete old pending verification
            print(f"🗑️ Deleting existing pending verification for {email}")
            await self.pending_repo.delete_by_email(email)
        
        # Store pending verification (NOT creating user yet)
        print(f"💾 Storing pending verification for {email}")
        await self.pending_repo.create(
            email=email,
            username=username,
            password_hash=password_hash,
            agreed_to_terms=agreed_to_terms,
            verification_code=otp_code,
            code_expires_at=expires_at,
            code_sent_at=sent_at
        )
        
        # Send verification email with OTP
        print(f"📨 Calling email service to send OTP to {email}")
        await self.email_service.send_verification_email(
            to_email=email.lower(),
            name=username,
            otp_code=otp_code
        )
        
        # ALWAYS print OTP to console for testing/debugging
        print("\n" + "="*70)
        print(f"🔑 OTP CODE FOR {email}: {otp_code}")
        print(f"👤 Username: {username}")
        print(f"⏰ Expires at: {expires_at}")
        print("="*70 + "\n")
        
        print(f"✅ Signup process completed for {email}")
        return True, None
