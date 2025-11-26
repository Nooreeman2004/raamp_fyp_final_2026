# Application Layer - OTP Utility Functions
import secrets
from datetime import datetime, timedelta
from typing import Tuple


class OTPGenerator:
    """Utility class for generating and validating OTP codes"""
    
    @staticmethod
    def generate_otp() -> str:
        """
        Generate a 6-digit numeric OTP code
        
        Returns:
            6-digit string (e.g., "123456")
        """
        return str(secrets.randbelow(1000000)).zfill(6)
    
    @staticmethod
    def generate_otp_with_expiry(expiry_hours: int = 24) -> Tuple[str, datetime]:
        """
        Generate OTP code with expiration time
        
        Args:
            expiry_hours: Hours until OTP expires (default: 24)
            
        Returns:
            Tuple of (otp_code, expiry_datetime)
        """
        otp_code = OTPGenerator.generate_otp()
        expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)
        return otp_code, expires_at
    
    @staticmethod
    def is_otp_valid(otp_code: str, user_otp: str, expires_at: datetime) -> Tuple[bool, str]:
        """
        Validate OTP code against user's stored OTP
        
        Args:
            otp_code: Code provided by user
            user_otp: Code stored in database
            expires_at: Expiration datetime from database
            
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        # Check if OTP matches
        if otp_code != user_otp:
            return False, "Invalid verification code"
        
        # Check if OTP expired
        if datetime.utcnow() > expires_at:
            return False, "Verification code has expired. Please request a new one"
        
        return True, ""
    
    @staticmethod
    def can_resend_otp(last_sent_at: datetime, cooldown_seconds: int = 60) -> Tuple[bool, int]:
        """
        Check if user can request a new OTP (cooldown period)
        
        Args:
            last_sent_at: When the last OTP was sent
            cooldown_seconds: Cooldown period in seconds (default: 60)
            
        Returns:
            Tuple of (can_resend: bool, remaining_seconds: int)
        """
        if not last_sent_at:
            return True, 0
        
        time_since_last = (datetime.utcnow() - last_sent_at).total_seconds()
        
        if time_since_last >= cooldown_seconds:
            return True, 0
        
        remaining = int(cooldown_seconds - time_since_last)
        return False, remaining
