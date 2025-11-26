from fastapi import APIRouter, Depends
from presentation.routers.auth_router import get_current_user_email
from application.services.onboarding_service import OnboardingService
from presentation.schemas.onboarding_schemas import (
    FacebookConnectionResponse,
    InstagramConnectionResponse,
    GoogleBusinessConnectionResponse,
    ConnectionStatus,
)

router = APIRouter(prefix="/api/profile/connections", tags=["profile-connections"])
service = OnboardingService()


@router.get("/facebook", response_model=ConnectionStatus)
async def get_facebook_connection(current_user_email: str = Depends(get_current_user_email)):
    conn = await service.get_facebook_connection(current_user_email)
    if not conn:
        return {"connected": False, "details": {}}
    # Don't expose access tokens; provide safe details only
    details = {
        "user_id": conn.get("user_id"),
        "fb_user_id": conn.get("fb_user_id"),
        "fb_pages": conn.get("fb_pages", []),
    }
    return {"connected": True, "details": details}


@router.get("/instagram", response_model=ConnectionStatus)
async def get_instagram_connection(current_user_email: str = Depends(get_current_user_email)):
    conn = await service.get_instagram_connection(current_user_email)
    if not conn:
        return {"connected": False, "details": {}}
    details = {
        "user_id": conn.get("user_id"),
        "ig_business_id": conn.get("ig_business_id"),
        "username": conn.get("username"),
        "profile_picture_url": conn.get("profile_picture_url"),
        "account_type": conn.get("account_type"),
        "linked_fb_page_id": conn.get("linked_fb_page_id"),
    }
    return {"connected": True, "details": details}


@router.get("/google-business", response_model=ConnectionStatus)
async def get_google_business_connection(current_user_email: str = Depends(get_current_user_email)):
    conn = await service.get_google_business_connection(current_user_email)
    if not conn:
        return {"connected": False, "details": {}}
    details = {
        "user_id": conn.get("user_id"),
        "business_name": conn.get("business_name"),
        "address": conn.get("address"),
        "latitude": conn.get("latitude"),
        "longitude": conn.get("longitude"),
        "place_id": conn.get("place_id"),
    }
    return {"connected": True, "details": details}


@router.get("/facebook/granted-scopes")
async def get_facebook_granted_scopes(current_user_email: str = Depends(get_current_user_email)):
    """Return granted_scopes array from the facebook_connections record for the current user."""
    fb = await service.facebook_repo.find_by_user_id(current_user_email)
    if not fb:
        return {"granted_scopes": []}
    return {"granted_scopes": getattr(fb, 'granted_scopes', [])}
