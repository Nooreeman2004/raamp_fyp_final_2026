# Application Layer - Password Validation
import re
from typing import List, Optional


class PasswordValidator:
    """Validates password against business rules"""
    
    MIN_LENGTH = 8
    
    @staticmethod
    def validate(password: str) -> tuple[bool, Optional[List[str]]]:
        """
        Validate password against requirements.
        Returns: (is_valid, list_of_errors)
        """
        errors = []
        
        if len(password) < PasswordValidator.MIN_LENGTH:
            errors.append(f"Password must be at least {PasswordValidator.MIN_LENGTH} characters long")
        
        if not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r"\d", password):
            errors.append("Password must contain at least one digit")
        
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            errors.append("Password must contain at least one special character")
        
        return (len(errors) == 0, errors if errors else None)
