# Application Layer - Email Validation
import re
from typing import Optional


class EmailValidator:
    """Validates email addresses using regex pattern matching"""
    
    # RFC 5322 compliant email regex pattern (simplified)
    EMAIL_REGEX = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    @staticmethod
    def is_valid(email: str) -> bool:
        """
        Validate email format using regex pattern matching.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if email is valid, False otherwise
        """
        if not email or not isinstance(email, str):
            return False
        
        return bool(EmailValidator.EMAIL_REGEX.match(email.strip()))
    
    @staticmethod
    def validate(email: str) -> tuple[bool, Optional[str]]:
        """
        Validate email and return detailed result.
        
        Args:
            email: Email address to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not email or not isinstance(email, str):
            return (False, "Email cannot be empty")
        
        email = email.strip()
        
        if not email:
            return (False, "Email cannot be empty")
        
        if not EmailValidator.EMAIL_REGEX.match(email):
            return (False, "Invalid email format")
        
        return (True, None)
