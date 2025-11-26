# Application Layer - Password Hashing Service
import bcrypt


class PasswordHasher:
    """Handles password hashing and verification using bcrypt directly"""
    
    def hash_password(self, plain_password: str) -> str:
        """Hash a plain text password"""
        # Generate salt and hash the password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception:
            return False


class PasswordVerifier:
    """Handles password verification for sign-in use case"""
    
    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception:
            return False
