# Infrastructure Layer - MongoDB Configuration
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys
import certifi
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
        print(f"[WARN] Python {python_version.major}.{python_version.minor} detected")
        print("   Python 3.13 has known SSL/TLS compatibility issues with MongoDB Atlas")
        print("   Recommended: Downgrade to Python 3.11 or 3.12 for production use")
        print()
    
    try:
        print("[INFO] Connecting to MongoDB...")
        
        # Try different connection approaches
        connection_attempts = [
            {
                "name": "Standard connection",
                "params": {"tlsCAFile": certifi.where()}
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
                print(f"[OK] Connected to MongoDB: {DATABASE_NAME}")
                return
                
            except Exception as e:
                last_error = e
                print(f"   [ERROR] {attempt['name']} failed")
                if client:
                    client.close()
                    client = None
        
        # All attempts failed
        raise last_error
        
    except ConfigurationError as e:
        print("[ERROR] MongoDB configuration error:", str(e))
        print("Possible causes: DNS SRV lookup failure for mongodb+srv URI, network/DNS blocking, or invalid connection string.")
        print("Quick fixes:")
        print(" - For local testing, set environment variable `MONGODB_URL` to 'mongodb://localhost:27017' and start a local MongoDB.")
        print(" - If using Atlas (mongodb+srv), ensure your system DNS can resolve SRV records. Try changing your DNS server to 8.8.8.8 or 1.1.1.1.")
        print(" - Alternatively, use the standard connection string format (mongodb://host:port) instead of mongodb+srv://.")
        raise
    except Exception as e:
        error_msg = str(e)
        print("[ERROR] Failed to connect to MongoDB")
        
        if "SSL" in error_msg or "TLS" in error_msg:
            print("\n[INFO] SSL/TLS Error Detected - Python 3.13 Issue")
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
        print("[INFO] Closed MongoDB connection")


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
    from infrastructure.database.models.oauth_state_model import OAuthStateModel
    from infrastructure.database.models.business_model import BusinessModel
    from infrastructure.database.models.consultation_request_model import ConsultationRequestModel
    from infrastructure.database.models.complaint_model import ComplaintModel
    from infrastructure.database.models.account_deletion_verification_model import AccountDeletionVerificationModel
    # New settings/billing/geo-intent models
    from infrastructure.database.models.notification_settings_model import NotificationSettingsModel
    from infrastructure.database.models.security_settings_model import SecuritySettingsModel
    from infrastructure.database.models.billing_profile_model import BillingProfileModel
    from infrastructure.database.models.wallet_model import WalletModel
    from infrastructure.database.models.instagram_post_model import (
        InstagramPostModel,
        ScheduledInstagramPostModel,
        InstagramStoryModel
    )
    from infrastructure.database.models.facebook_post_model import (
        FacebookPostModel,
        ScheduledFacebookPostModel
    )
    from infrastructure.database.models.notification_model import NotificationModel
    from application.services.job_health_monitor_service import JobExecutionLogModel
    from infrastructure.database.models.trend_signal_model import TrendSignalModel
    from infrastructure.database.models.trend_detection_model import TrendDetectionModel
    from infrastructure.database.models.trend_watchlist_model import TrendWatchlistModel
    from infrastructure.database.models.trend_retry_job_model import TrendRetryJobModel
    from infrastructure.database.models.trend_cache_model import TrendCacheModel
    from infrastructure.database.models.trend_ai_analysis_model import TrendAIAnalysisModel
    from infrastructure.database.models.campaign_launch_request_model import CampaignLaunchRequestModel
    from infrastructure.database.models.asset_model import AssetModel
    from infrastructure.database.models.caption_log_model import CaptionLogModel
    from infrastructure.database.models.heat_score_model import HeatScoreModel
    from infrastructure.database.models.campaign_log_model import CampaignLogModel
    from infrastructure.database.models.campaign_brief_model import CampaignBriefModel
    from infrastructure.database.models.posting_log_model import PostingLogModel
    from infrastructure.database.models.trend_activity_model import TrendActivityModel
    from infrastructure.database.models.campaign_draft_model import CampaignDraftModel
    from infrastructure.database.models.chat_session_model import ChatSessionModel
    from infrastructure.database.models.chat_interaction_model import ChatInteractionModel
    from infrastructure.database.models.performance_analytics_model import (
        ConversionEventModel,
        CampaignPerformanceModel,
    )
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
            OAuthStateModel,
            BusinessModel,
            ComplaintModel,
            ConsultationRequestModel,
            AccountDeletionVerificationModel,
            # New models
            NotificationSettingsModel,
            SecuritySettingsModel,
            BillingProfileModel,
            WalletModel,
            # Instagram posting models
            InstagramPostModel,
            ScheduledInstagramPostModel,
            InstagramStoryModel,
            # Facebook posting models
            FacebookPostModel,
            ScheduledFacebookPostModel,
            # Notification model
            NotificationModel,
            # Job health monitoring
            JobExecutionLogModel,
            # Trend models
            TrendSignalModel,
            TrendDetectionModel,
            TrendWatchlistModel,
            TrendRetryJobModel,
            TrendCacheModel,
            TrendAIAnalysisModel,
            CampaignLaunchRequestModel,
            # Activity logs
            TrendActivityModel,
            # Asset management
            AssetModel,
            CaptionLogModel,
            # Geo-Intent Engine
            HeatScoreModel,
            CampaignLogModel,
            CampaignBriefModel,
            # Dashboard / performance analytics
            ConversionEventModel,
            CampaignPerformanceModel,
            # Social Tracking
            PostingLogModel,
            # Drafts (Create Pack)
            CampaignDraftModel,
            # Chatbot Sessions & Interactions
            ChatSessionModel,
            ChatInteractionModel,
        ]
    )
    print("[OK] Beanie initialized with document models (settings, billing, geo-intent, posting, assets, logs)")
    
    # Seed business domains
    await seed_business_domains()


def get_database():
    """Get database instance"""
    return client[DATABASE_NAME]

