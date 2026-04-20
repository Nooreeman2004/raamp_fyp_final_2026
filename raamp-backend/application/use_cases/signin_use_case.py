# Application Layer - Sign In Use Case
from typing import Optional, Tuple, Dict
from domain.entities.user import User
from domain.repositories.user_repository import IUserRepository
from application.services.password_service import PasswordVerifier
from application.services.jwt_service import JWTService
from infrastructure.repositories.pending_verification_repository import (
    PendingVerificationRepository,
)


class SignInUseCase:
    """
    Use case for user sign-in authentication.
    Validates credentials and generates JWT token.
    """
    
    def __init__(
        self,
        user_repository: IUserRepository,
        password_verifier: PasswordVerifier,
        jwt_service: JWTService,
        pending_verification_repository: PendingVerificationRepository,
    ):
        self.user_repository = user_repository
        self.password_verifier = password_verifier
        self.jwt_service = jwt_service
        self._pending_repo = pending_verification_repository
    
    async def execute(
        self,
        email: str,
        password: str
    ) -> Tuple[Optional[User], Optional[str], Optional[Dict[str, str]]]:
        """
        Execute sign-in use case
        
        Args:
            email: User's email
            password: User's plain text password
            
        Returns:
            Tuple of (User entity, JWT token, errors dict)
            - If successful: (User, token, None)
            - If failed: (None, None, {"field": "error message"})
        """
        errors = {}
        
        # Find user by email
        email_lower = email.lower()
        user = await self.user_repository.find_by_email(email_lower)

        if not user:
            # Signed up but not finished OTP: account is only in pending_verifications
            pending = await self._pending_repo.find_by_email(email_lower)
            if pending:
                if not self.password_verifier.verify(password, pending.password_hash):
                    errors["password"] = "Invalid email or password"
                    return None, None, errors
                errors["email"] = (
                    "Please verify your email before signing in. "
                    "Enter the code we sent when you signed up."
                )
                errors["signup_state"] = "pending_otp"
                return None, None, errors

            errors["email"] = "Invalid email or password"
            return None, None, errors
        
        # Verify password
        if not self.password_verifier.verify(password, user.password_hash):
            errors["password"] = "Invalid email or password"
            return None, None, errors
        
        # Check if email is verified
        if not user.is_verified:
            errors["email"] = "Please verify your email before signing in"
            return None, None, errors
        
        # Generate JWT token
        token = self.jwt_service.create_access_token(
            user_id=user.id,
            email=user.email
        )
        
        return user, token, None
