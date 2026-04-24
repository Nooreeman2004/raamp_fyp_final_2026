"""
Subscription Tier Restriction Utilities
========================================
FastAPI dependencies to enforce subscription tier requirements on endpoints.
"""

from typing import List
from fastapi import HTTPException, status, Depends
import logging

from infrastructure.database.models.user_model import UserModel
from presentation.routers.auth_router import get_current_user_email

logger = logging.getLogger(__name__)


async def get_current_user(current_user_email: str = Depends(get_current_user_email)) -> UserModel:
    """
    Fetch the current user from database.
    
    Args:
        current_user_email: Email from JWT token
        
    Returns:
        UserModel instance
        
    Raises:
        HTTPException: 404 if user not found
    """
    user = await UserModel.find_one(UserModel.email == current_user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def require_pro_or_premium(user: UserModel = Depends(get_current_user)) -> UserModel:
    """
    Require Pro or Premium subscription tier.
    Demo user (abdullah@gmail.com) is always granted access.
    
    Args:
        user: Current authenticated user
        
    Returns:
        UserModel if authorized
        
    Raises:
        HTTPException: 403 if user is on free tier
    """
    # Demo user override
    if user.email.lower() == "abdullah@gmail.com":
        logger.info("✨ DEMO BYPASS: %s granted Pro/Premium access", user.email)
        return user
    
    # Check subscription tier
    if user.subscriptionTier not in ["pro", "premium"]:
        logger.warning("🚫 User %s (%s) attempted to access Pro/Premium feature", user.email, user.subscriptionTier)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This feature requires a Pro or Premium subscription. Your current plan: {user.subscriptionTier}. Please upgrade to continue."
        )
    
    return user


async def require_premium(user: UserModel = Depends(get_current_user)) -> UserModel:
    """
    Require Premium subscription tier only.
    Demo user (abdullah@gmail.com) is always granted access.
    
    Args:
        user: Current authenticated user
        
    Returns:
        UserModel if authorized
        
    Raises:
        HTTPException: 403 if user is not on premium tier
    """
    # Demo user override
    if user.email.lower() == "abdullah@gmail.com":
        logger.info("✨ DEMO BYPASS: %s granted Premium access", user.email)
        return user
    
    # Check subscription tier
    if user.subscriptionTier != "premium":
        logger.warning("🚫 User %s (%s) attempted to access Premium-only feature", user.email, user.subscriptionTier)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This feature requires a Premium subscription. Your current plan: {user.subscriptionTier}. Please upgrade to continue."
        )
    
    return user


def check_tier_access(user: UserModel, required_tiers: List[str]) -> bool:
    """
    Check if user has access to a feature based on required tiers.
    Demo user (abdullah@gmail.com) always has access.
    
    Args:
        user: UserModel instance
        required_tiers: List of allowed tiers (e.g., ["pro", "premium"])
        
    Returns:
        True if user has access, False otherwise
    """
    # Demo user override
    if user.email.lower() == "abdullah@gmail.com":
        return True
    
    return user.subscriptionTier in required_tiers


async def validate_tier_for_feature(
    user: UserModel,
    feature_name: str,
    required_tiers: List[str]
) -> None:
    """
    Validate user's subscription tier for a specific feature.
    Raises HTTPException if unauthorized.
    
    Args:
        user: UserModel instance
        feature_name: Name of the feature being accessed
        required_tiers: List of allowed tiers
        
    Raises:
        HTTPException: 403 if user lacks required tier
    """
    if not check_tier_access(user, required_tiers):
        tier_list = ", ".join(required_tiers)
        logger.warning(
            "🚫 User %s (%s) attempted to access %s (requires: %s)",
            user.email, user.subscriptionTier, feature_name, tier_list
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{feature_name} requires {tier_list} subscription. Your current plan: {user.subscriptionTier}. Please upgrade to continue."
        )
