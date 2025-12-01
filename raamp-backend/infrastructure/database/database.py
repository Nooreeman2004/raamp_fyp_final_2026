# Infrastructure Layer - MongoDB Configuration
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys
from dotenv import load_dotenv
from pymongo.errors import ConfigurationError

load_dotenv()

# MongoDB connection - use MONGO_URI from config.py for consistency
MONGODB_URL = os.getenv("MONGODB_URL", os.getenv("MONGO_URI", "mongodb://localhost:27017"))
DATABASE_NAME = "raamp_db"

# Global client
client: AsyncIOMotorClient = None


async def connect_to_mongo():
    """Connect to MongoDB with fallback for Python 3.13 SSL issues"""
    global client
    
    # Check Python version
    python_version = sys.version_info
    if python_version >= (3, 13):
        print(f"⚠️  WARNING: Python {python_version.major}.{python_version.minor} detected")
        print("   Python 3.13 has known SSL/TLS compatibility issues with MongoDB Atlas")
        print("   Recommended: Downgrade to Python 3.11 or 3.12 for production use")
        print()
    
    try:
        print(f"🔄 Connecting to MongoDB...")
        
        # Try different connection approaches
        connection_attempts = [
            {
                "name": "Standard connection",
                "params": {}
            },
            {
                "name": "TLS disabled",
                "params": {"tls": False}
            }
        ]
        
        last_error = None
        for attempt in connection_attempts:
            try:
                print(f"   Trying: {attempt['name']}...")
                client = AsyncIOMotorClient(
                    MONGODB_URL,
                    serverSelectionTimeoutMS=10000,
                    connectTimeoutMS=10000,
                    socketTimeoutMS=10000,
                    **attempt["params"]
                )
                
                # Test the connection
                await client.server_info()
                print(f"✅ Connected to MongoDB: {DATABASE_NAME}")
                return
                
            except Exception as e:
                last_error = e
                print(f"   ❌ {attempt['name']} failed")
                if client:
                    client.close()
                    client = None
        
        # All attempts failed
        raise last_error
        
    except ConfigurationError as e:
        print("❌ MongoDB configuration error:", str(e))
        print("Possible causes: DNS SRV lookup failure for mongodb+srv URI, network/DNS blocking, or invalid connection string.")
        print("Quick fixes:")
        print(" - For local testing, set environment variable `MONGODB_URL` to 'mongodb://localhost:27017' and start a local MongoDB.")
        print(" - If using Atlas (mongodb+srv), ensure your system DNS can resolve SRV records. Try changing your DNS server to 8.8.8.8 or 1.1.1.1.")
        print(" - Alternatively, use the standard connection string format (mongodb://host:port) instead of mongodb+srv://.")
        raise
    except Exception as e:
        error_msg = str(e)
        print("❌ Failed to connect to MongoDB")
        
        if "SSL" in error_msg or "TLS" in error_msg:
            print("\n🔧 SSL/TLS Error Detected - Python 3.13 Issue")
            print("=" * 70)
            print("SOLUTION: Use Python 3.11 or 3.12 instead of Python 3.13")
            print()
            print("Python 3.13 has breaking changes in SSL/TLS handling that cause")
            print("compatibility issues with MongoDB Atlas and other cloud services.")
            print()
            print("Quick Fix:")
            print("1. Install Python 3.12:")
            print("   Download from: https://www.python.org/downloads/release/python-3120/")
            print()
            print("2. Create a new virtual environment:")
            print("   python3.12 -m venv venv")
            print("   .\\venv\\Scripts\\activate  (Windows)")
            print("   pip install -r requirements.txt")
            print()
            print("3. Restart your application")
            print("=" * 70)
        else:
            print("\nTroubleshooting:")
            print(" - Check if your IP is whitelisted in MongoDB Atlas Network Access")
            print(" - Verify the connection string in .env file")
            print(" - Ensure you have internet connectivity")
        
        print(f"\nError details: {error_msg}")
        raise


async def close_mongo_connection():
    """Close MongoDB connection"""
    global client
    if client:
        client.close()
        print("👋 Closed MongoDB connection")


async def init_db():
    """Initialize Beanie with document models"""
    from infrastructure.database.models.user_model import UserModel
    from infrastructure.database.models.pending_verification_model import PendingVerificationModel
    from infrastructure.database.models.profile_edit_verification_model import ProfileEditVerificationModel
    from infrastructure.database.models.business_domain_model import BusinessDomainModel
    from infrastructure.database.models.facebook_connection_model import FacebookConnectionModel
    from infrastructure.database.models.instagram_connection_model import InstagramConnectionModel
    from infrastructure.database.models.social_media_account_model import SocialMediaAccountModel
    from infrastructure.database.models.password_reset_model import PasswordResetModel
    from infrastructure.database.models.google_business_location_model import GoogleBusinessLocationModel
    from infrastructure.database.models.oauth_state_model import OAuthStateModel
    from infrastructure.database.models.business_model import BusinessModel
    from infrastructure.database.models.consultation_request_model import ConsultationRequestModel
    from infrastructure.database.models.account_deletion_verification_model import AccountDeletionVerificationModel
    from infrastructure.database.seed_data import seed_business_domains

    await init_beanie(
        database=client[DATABASE_NAME],
        document_models=[
            UserModel,
            PendingVerificationModel,
            ProfileEditVerificationModel,
            PasswordResetModel,
            BusinessDomainModel,
            FacebookConnectionModel,
            InstagramConnectionModel,
            SocialMediaAccountModel,
            GoogleBusinessLocationModel,
            OAuthStateModel,
            BusinessModel,
            ConsultationRequestModel,
            AccountDeletionVerificationModel,
        ]
    )
    print("✅ Beanie initialized with User, PendingVerification, ProfileEditVerification, AccountDeletionVerification, and BusinessDomain models")
    
    # Seed business domains
    await seed_business_domains()


def get_database():
    """Get database instance"""
    return client[DATABASE_NAME]

