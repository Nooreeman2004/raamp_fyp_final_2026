# Application Layer - Firebase Service for Google OAuth
import firebase_admin
from firebase_admin import credentials, auth
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class FirebaseService:
    """Service for Firebase authentication verification"""
    
    _initialized = False
    
    @classmethod
    def initialize(cls):
        """Initialize Firebase Admin SDK with Storage"""
        if not cls._initialized:
            # Check if service account file exists
            cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "./firebase-service-account.json")
            storage_bucket = os.getenv("FIREBASE_STORAGE_BUCKET", "raamp-82bbe.firebasestorage.app")
            
            if os.path.exists(cred_path):
                try:
                    cred = credentials.Certificate(cred_path)
                    # Initialize with storage bucket from environment
                    # Note: Firebase Storage bucket name should be in format: project-id.appspot.com
                    firebase_admin.initialize_app(cred, {
                        'storageBucket': storage_bucket
                    })
                    cls._initialized = True
                    logger.info("Firebase Admin initialized successfully")
                    logger.info("Firebase Storage bucket: %s", storage_bucket)
                    logger.info("Firebase service account: %s", cred_path)
                except Exception as e:
                    logger.warning("Firebase Admin initialization failed: %s (%s)", str(e), type(e).__name__)
                    logger.warning("Falling back to local storage for uploads")
            else:
                logger.warning("Firebase service account not found at: %s", cred_path)
                logger.warning("Google OAuth and Storage will not work until credentials are provided")
    
    @staticmethod
    async def verify_id_token(id_token: str) -> Optional[dict]:
        """
        Verify Firebase ID token from client
        Returns user info if valid, None if invalid
        """
        try:
            decoded_token = auth.verify_id_token(id_token)
            return {
                "uid": decoded_token.get("uid"),
                "email": decoded_token.get("email"),
                "email_verified": decoded_token.get("email_verified", False),
                "name": decoded_token.get("name"),
                "picture": decoded_token.get("picture"),
            }
        except Exception as e:
            print(f"Token verification failed: {e}")
            return None


# Singleton instance
firebase_service = FirebaseService()
