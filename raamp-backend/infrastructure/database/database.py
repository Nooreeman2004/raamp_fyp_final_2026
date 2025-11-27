# Infrastructure Layer - MongoDB Configuration
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import certifi
from pymongo.errors import ConfigurationError

load_dotenv()

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = "raamp_db"

# Global client
client: AsyncIOMotorClient = None


async def connect_to_mongo():
    """Connect to MongoDB"""
    global client
    try:
        client = AsyncIOMotorClient(
            MONGODB_URL,
            tlsCAFile=certifi.where()  # Use certifi for SSL certificates
        )
        # perform a lightweight operation to validate connection details
        await client.server_info()
        print(f"✅ Connected to MongoDB: {DATABASE_NAME}")
    except ConfigurationError as e:
        print("❌ MongoDB configuration error:", str(e))
        print("Possible causes: DNS SRV lookup failure for mongodb+srv URI, network/DNS blocking, or invalid connection string.")
        print("Quick fixes:")
        print(" - For local testing, set environment variable `MONGODB_URL` to 'mongodb://localhost:27017' and start a local MongoDB.")
        print(" - If using Atlas (mongodb+srv), ensure your system DNS can resolve SRV records. Try changing your DNS server to 8.8.8.8 or 1.1.1.1.")
        print(" - Alternatively, use the standard connection string format (mongodb://host:port) instead of mongodb+srv://.")
        raise
    except Exception as e:
        print("❌ Failed to connect to MongoDB:", str(e))
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
        ]
    )
    print("✅ Beanie initialized with User, PendingVerification, ProfileEditVerification, and BusinessDomain models")
    
    # Seed business domains
    await seed_business_domains()


def get_database():
    """Get database instance"""
    return client[DATABASE_NAME]

