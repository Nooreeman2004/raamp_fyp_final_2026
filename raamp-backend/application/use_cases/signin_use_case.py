# Application Layer - Sign In Use Case
from typing import Optional, Tuple, Dict
from domain.entities.user import User
from domain.repositories.user_repository import IUserRepository
from application.services.password_service import PasswordVerifier
from application.services.jwt_service import JWTService


class SignInUseCase:
    """
    Use case for user sign-in authentication.
    Validates credentials and generates JWT token.
    """
    
    def __init__(
        self,
        user_repository: IUserRepository,
        password_verifier: PasswordVerifier,
        jwt_service: JWTService
    ):
        self.user_repository = user_repository
        self.password_verifier = password_verifier
        self.jwt_service = jwt_service
    
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
        user = await self.user_repository.find_by_email(email.lower())
        
        if not user:
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
