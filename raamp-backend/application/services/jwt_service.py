# Application Layer - JWT Service
from datetime import datetime, timedelta
from typing import Optional
import os
from jose import jwt, JWTError

from config import Config


class JWTService:
    """Service for JWT token generation and validation"""
    
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
        self.algorithm = "HS256"
    
    def create_access_token(self, user_id: str, email: str) -> str:
        """
        Create JWT access token
        
        Args:
            user_id: User's unique identifier
            email: User's email
            
        Returns:
            Encoded JWT token string
        """
        expire = datetime.utcnow() + timedelta(days=Config.JWT_EXPIRATION_DAYS)
        
        to_encode = {
            "sub": user_id,  # Subject (user_id)
            "email": email,
            "exp": expire,  # Expiration time
            "iat": datetime.utcnow(),  # Issued at
        }
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[dict]:
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded payload if valid, None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            print(f"JWT verification failed: {e}")
            return None
