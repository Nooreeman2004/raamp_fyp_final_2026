# Application Layer - Firebase Service for Google OAuth
import firebase_admin
from firebase_admin import credentials, auth
import os
from typing import Optional


class FirebaseService:
    """Service for Firebase authentication verification"""
    
    _initialized = False
    
    @classmethod
    def initialize(cls):
        """Initialize Firebase Admin SDK"""
        if not cls._initialized:
            # Check if service account file exists
            cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "./firebase-service-account.json")
            
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                cls._initialized = True
                print("✅ Firebase Admin initialized")
            else:
                print(f"⚠️  Firebase service account not found at: {cred_path}")
                print("   Google OAuth will not work until you add the service account JSON")
    
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
