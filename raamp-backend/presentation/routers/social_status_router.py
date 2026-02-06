"""
Social Media Connection Status API Router
Provides connection status for Instagram and Facebook
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import logging

from presentation.routers.auth_router import get_current_user_email
from infrastructure.repositories.social_media_repository import SocialMediaRepository
from infrastructure.repositories.facebook_repository import FacebookRepository
from infrastructure.repositories.instagram_repository import InstagramRepository
from infrastructure.database.models.user_model import UserModel

from application.services.instagram_graph_api_service import InstagramGraphAPIClient

logger = logging.getLogger(__name__)
# Initialize API client for reachability checks
api_client = InstagramGraphAPIClient()
router = APIRouter(prefix="/api/social", tags=["social-status"])

class SocialConnectionStatus(BaseModel):
    instagram_connected: bool
    facebook_connected: bool
    instagram_details: dict | None = None
    facebook_details: dict | None = None

@router.get("/facebook/permissions", response_model=dict)
async def get_facebook_permissions(
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Get current Facebook permissions/scopes granted to the app.
    Useful for debugging permission issues.
    """
    try:
        fb_repo = FacebookRepository()
        fb_account = await fb_repo.find_by_user_id(current_user_email)
        
        if not fb_account:
            return {
                "connected": False,
                "granted_scopes": [],
                "message": "Facebook not connected"
            }
        
        return {
            "connected": True,
            "granted_scopes": fb_account.granted_scopes,
            "has_pages_manage_posts": "pages_manage_posts" in fb_account.granted_scopes,
            "has_instagram_content_publish": "instagram_content_publish" in fb_account.granted_scopes,
            "total_scopes": len(fb_account.granted_scopes)
        }
    
    except Exception as e:
        logger.exception(f"Error fetching Facebook permissions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve Facebook permissions"
        )

@router.get("/status", response_model=SocialConnectionStatus)
async def get_social_connection_status(
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Get connection status for Instagram and Facebook accounts.
    Returns whether each platform is connected and additional details.
    """
    try:
        # First check User model for connection flags
        user = await UserModel.find_one(UserModel.email == current_user_email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Initial flags from User model
        instagram_connected = user.instagram_connected
        facebook_connected = user.facebook_connected
        
        instagram_details = None
        facebook_details = None
        
        logger.info(f"Checking social status for user: {current_user_email}")
        
        # Get Instagram details from InstagramConnectionModel (Primary Source)
        ig_repo = InstagramRepository()
        ig_account = await ig_repo.find_by_user_id(current_user_email)
        
        # Get Instagram details from SocialMediaAccountModel (Legacy Source)
        repo = SocialMediaRepository()
        account = await repo.find_by_user_id(current_user_email)
        
        # Get Facebook details from FacebookConnectionModel
        fb_repo = FacebookRepository()
        fb_account = await fb_repo.find_by_user_id(current_user_email)
        
        # 1. Process Instagram account data
        token_reachable = False
        if ig_account and ig_account.ig_business_id:
            logger.info(f"Instagram account found - ID: {ig_account.ig_business_id}")
            instagram_connected = True 
            
            # Perform reachability check
            token_reachable = await api_client.validate_token_reachability(current_user_email)
            
            instagram_details = {
                "ig_business_id": ig_account.ig_business_id,
                "instagram_user_id": ig_account.ig_business_id, # Backward compatibility
                "username": ig_account.username,
                "connected_at": ig_account.created_at.isoformat() if hasattr(ig_account, 'created_at') else None,
                "token_valid": token_reachable,
                "reachability": "verified" if token_reachable else "failed"
            }
        elif account and account.ig_business_id:
            logger.info(f"Legacy social account found - ID: {account.ig_business_id}")
            instagram_connected = True
            
            # Perform reachability check
            token_reachable = await api_client.validate_token_reachability(current_user_email)
            
            instagram_details = {
                "ig_business_id": account.ig_business_id,
                "instagram_user_id": account.ig_business_id, # Backward compatibility
                "page_id": account.page_id,
                "connected_at": account.created_at.isoformat() if hasattr(account, 'created_at') else None,
                "token_valid": token_reachable,
                "reachability": "verified" if token_reachable else "failed"
            }
        
        # Sync User model flag if mismatch found (Repairing stale flags)
        if instagram_connected != user.instagram_connected:
            logger.info(f"Syncing user.instagram_connected: {user.instagram_connected} -> {instagram_connected}")
            from infrastructure.repositories.user_repository_impl import UserRepository
            user_repo = UserRepository()
            await user_repo.update_connection_flags(current_user_email, instagram=instagram_connected)

        # 2. Process Facebook account data
        if fb_account and fb_account.fb_user_id:
            facebook_connected = True
            if fb_account.fb_pages:
                primary_page = fb_account.fb_pages[0]
                facebook_details = {
                    "page_id": primary_page.id,
                    "page_name": primary_page.name,
                    "fb_user_id": fb_account.fb_user_id,
                    "connected_at": fb_account.created_at.isoformat() if hasattr(fb_account, 'created_at') else None,
                    "token_valid": True # Facebook token usually valid if we have the record
                }
        
        # Sync User model flag for Facebook
        if facebook_connected != user.facebook_connected:
             from infrastructure.repositories.user_repository_impl import UserRepository
             user_repo = UserRepository()
             await user_repo.update_connection_flags(current_user_email, facebook=facebook_connected)

        result = SocialConnectionStatus(
            instagram_connected=instagram_connected,
            facebook_connected=facebook_connected,
            instagram_details=instagram_details,
            facebook_details=facebook_details
        )
        
        logger.info(f"Final status: IG={instagram_connected}(valid={token_reachable}), FB={facebook_connected}")
        return result
    
    except Exception as e:
        logger.exception(f"Error fetching social connection status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve connection status"
        )
