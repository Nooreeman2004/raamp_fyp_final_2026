# Application Configuration
import os
from typing import Optional


class Config:
    """Centralized application configuration"""
    
    # MongoDB Configuration - supports both MONGODB_URL and MONGO_URI for compatibility
    MONGO_URI: str = os.getenv("MONGODB_URL", os.getenv("MONGO_URI", "mongodb://localhost:27017/raamp_db"))
    
    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production-use-openssl-rand-hex-32")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_DAYS: int = int(os.getenv("JWT_EXPIRATION_DAYS", "7"))
    
    # Mailtrap Email Configuration
    # SMTP Sandbox for Testing (emails go to Mailtrap inbox, not real recipients)
    MAILTRAP_SMTP_HOST: str = "sandbox.smtp.mailtrap.io"
    MAILTRAP_SMTP_PORT: int = int(os.getenv("MAILTRAP_SMTP_PORT", "2525"))
    MAILTRAP_SMTP_USERNAME: str = os.getenv("MAILTRAP_SMTP_USERNAME", "7d75862a2e985a")
    MAILTRAP_SMTP_PASSWORD: str = os.getenv("MAILTRAP_SMTP_PASSWORD", "9a3b0f07864cb2")
    
    # Fallback API configuration (not used with SMTP)
    MAILTRAP_API_TOKEN: str = os.getenv("MAILTRAP_API_TOKEN", "78049356a1e16f8ffe78c57832a34eed")
    MAILTRAP_ENDPOINT: str = os.getenv("MAILTRAP_ENDPOINT", "https://send.api.mailtrap.io/api/send")
    
    SENDER_EMAIL: str = "hello@demomailtrap.com"
    SENDER_NAME: str = "RAAMP Team"
    
    # Email delivery method: 'smtp' or 'api'
    # Use API by default for sandbox/testing to avoid local SMTP TLS issues
    EMAIL_METHOD: str = os.getenv("EMAIL_METHOD", "api")
    
    # OTP Configuration
    OTP_LENGTH: int = 6
    OTP_EXPIRY_HOURS: int = 24
    OTP_RESEND_COOLDOWN_SECONDS: int = 60
    OTP_MAX_RESENDS_PER_HOUR: int = 5
    OTP_MAX_RESENDS_PER_DAY: int = 10
    OTP_CLEANUP_INTERVAL_HOURS: int = 6  # Run cleanup every 6 hours
    
    # Firebase Configuration
    FIREBASE_CREDENTIALS_PATH: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-admin-sdk.json")
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    # Facebook App (OAuth)
    FACEBOOK_APP_ID: str = os.getenv("FACEBOOK_APP_ID", "")
    FACEBOOK_APP_SECRET: str = os.getenv("FACEBOOK_APP_SECRET", "")

    # Backend public URL used for OAuth redirect URIs
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")
    # Frontend public URL used for post-OAuth redirects (SPA)
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    # Facebook OAuth scopes (comma-separated string). Configure per-environment.
    FACEBOOK_OAUTH_SCOPES: str = os.getenv("FACEBOOK_OAUTH_SCOPES", "public_profile,pages_show_list,pages_read_engagement,pages_read_user_content")
    # Google Maps API Key (used for server-side Places requests if needed)
    GOOGLE_MAPS_API_KEY: str = os.getenv("GOOGLE_MAPS_API_KEY", "")
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production"""
        return cls.ENVIRONMENT == "production"
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development"""
        return cls.ENVIRONMENT == "development"


# Singleton instance
config = Config()

# Backwards-compatible alias expected by some modules
settings = config

# Export OTP constants for direct import
OTP_LENGTH = Config.OTP_LENGTH
OTP_EXPIRY_HOURS = Config.OTP_EXPIRY_HOURS
OTP_RESEND_COOLDOWN_SECONDS = Config.OTP_RESEND_COOLDOWN_SECONDS
OTP_MAX_RESENDS_PER_HOUR = Config.OTP_MAX_RESENDS_PER_HOUR
OTP_MAX_RESENDS_PER_DAY = Config.OTP_MAX_RESENDS_PER_DAY
OTP_CLEANUP_INTERVAL_HOURS = Config.OTP_CLEANUP_INTERVAL_HOURS
