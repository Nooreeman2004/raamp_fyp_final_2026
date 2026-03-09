# Application Configuration
import os
import hashlib
import base64


class Config:
    """Centralized application configuration"""
    
    # MongoDB Configuration - supports both MONGODB_URL and MONGO_URI for compatibility
    MONGO_URI: str = os.getenv("MONGODB_URL", os.getenv("MONGO_URI", "mongodb://localhost:27017/raamp_db"))
    
    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production-use-openssl-rand-hex-32")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_DAYS: int = int(os.getenv("JWT_EXPIRATION_DAYS", "7"))
    
    # Encryption Configuration (for encrypting sensitive data like OAuth tokens)
    # Auto-generate if not set (for development only - use proper key in production)
    @staticmethod
    def get_encryption_key() -> str:
        key = os.getenv("ENCRYPTION_KEY", "")
        if not key:
            # Development fallback: generate a stable key from JWT secret
            from cryptography.fernet import Fernet
            # Create stable key from JWT_SECRET for development
            jwt_secret = os.getenv("JWT_SECRET_KEY", "development-secret-key-32bytes")
            key_material = hashlib.sha256(jwt_secret.encode()).digest()
            key = base64.urlsafe_b64encode(key_material).decode()
        return key
    
    ENCRYPTION_KEY: str = get_encryption_key.__func__()
    
    # Mailtrap Email Configuration
    # SMTP Sandbox for Testing (emails go to Mailtrap inbox, not real recipients)
    MAILTRAP_SMTP_HOST: str = "sandbox.smtp.mailtrap.io"
    MAILTRAP_SMTP_PORT: int = int(os.getenv("MAILTRAP_SMTP_PORT", "2525"))
    MAILTRAP_SMTP_USERNAME: str = os.getenv("MAILTRAP_SMTP_USERNAME", "daaad2fab206e4")
    MAILTRAP_SMTP_PASSWORD: str = os.getenv("MAILTRAP_SMTP_PASSWORD", "08f05079b826ec")
    
    # Fallback API configuration (not used with SMTP)
    MAILTRAP_API_TOKEN: str = os.getenv("MAILTRAP_API_TOKEN", "78049356a1e16f8ffe78c57832a34eed")
    MAILTRAP_ENDPOINT: str = os.getenv("MAILTRAP_ENDPOINT", "https://send.api.mailtrap.io/api/send")
    
    SENDER_EMAIL: str = os.getenv("MAIL_FROM", "hello@demomailtrap.com")
    SENDER_NAME: str = os.getenv("MAIL_FROM_NAME", "RAAMP Team")
    
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
    # Include Instagram Graph API scopes (official names) since Instagram connection goes through Facebook
    FACEBOOK_OAUTH_SCOPES: str = os.getenv("FACEBOOK_OAUTH_SCOPES", "public_profile,email,pages_show_list,pages_read_engagement,pages_manage_metadata,instagram_basic,instagram_manage_comments,instagram_manage_messages,instagram_content_publish,business_management")
    
    # Instagram App (OAuth) - separate from Facebook
    INSTAGRAM_APP_ID: str = os.getenv("INSTAGRAM_APP_ID", "")
    INSTAGRAM_APP_SECRET: str = os.getenv("INSTAGRAM_APP_SECRET", "")
    INSTAGRAM_OAUTH_SCOPES: str = os.getenv("INSTAGRAM_OAUTH_SCOPES", "instagram_basic,instagram_manage_comments,instagram_manage_messages,instagram_manage_insights")

    # Backend public URL used for OAuth redirect URIs
    # IMPORTANT: Must be publicly accessible for Instagram/Facebook posting
    # Examples:
    #   - Production: "https://api.yourdomain.com"
    #   - Ngrok: "https://abc123.ngrok.io"
    #   - Localtunnel: "https://your-subdomain.loca.lt"
    #   - DO NOT USE: "http://localhost:8000" (Instagram API cannot access local URLs!)
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")
    # Frontend public URL used for post-OAuth redirects (SPA)
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    # Google Maps API Key (used for server-side Places requests if needed)
    GOOGLE_MAPS_API_KEY: str = os.getenv("GOOGLE_MAPS_API_KEY", "")
    
    # OpenAI API Configuration - Can use Google's Generative Language API endpoint
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE_URL: str = os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
    OPENAI_GENERATION_MODEL: str = os.getenv("OPENAI_GENERATION_MODEL", "gpt-4o-mini")
    
    # Google Gemini API Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Cloudinary Configuration
    CLOUDINARY_CLOUD_NAME: str = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY: str = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET: str = os.getenv("CLOUDINARY_API_SECRET", "")
    
    # Stripe Configuration
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "sk_test_dummy")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    PRO_PRODUCT_ID: str = os.getenv("PRO_PRODUCT_ID", "prod_dummy")
    PREMIUM_PRODUCT_ID: str = os.getenv("PREMIUM_PRODUCT_ID", "prod_dummy")
    # Price IDs are different from product IDs - get these from Stripe Dashboard → Products → Click product → Copy Price ID
    PRO_PRICE_ID: str = os.getenv("PRO_PRICE_ID", "price_dummy")
    PREMIUM_PRICE_ID: str = os.getenv("PREMIUM_PRICE_ID", "price_dummy")
    
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
