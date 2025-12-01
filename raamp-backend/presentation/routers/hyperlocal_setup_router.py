"""
Hyperlocal Business Setup Router - handles location and business details for geo-targeting
"""
from fastapi import APIRouter, Depends, HTTPException, status
from infrastructure.repositories.business_repository import BusinessRepository
from infrastructure.repositories.google_business_repository import GoogleBusinessRepository
from presentation.schemas.hyperlocal_setup_schema import (
    HyperlocalBusinessSetupRequest,
    HyperlocalBusinessSetupResponse,
    HyperlocalBusinessLocationResponse
)
from presentation.routers.auth_router import get_current_user_email


router = APIRouter(prefix="/api/hyperlocal-setup", tags=["Hyperlocal Setup"])


@router.get("/location", response_model=HyperlocalBusinessLocationResponse)
async def get_saved_location(
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Get the user's saved location from previous onboarding step
    
    Returns location data from Google Business connection or BusinessModel
    """
    try:
        # First check BusinessModel for any saved hyperlocal data
        business_repo = BusinessRepository()
        business = await business_repo.get_by_user_id(current_user_email)
        
        if business and business.latitude and business.longitude:
            return HyperlocalBusinessLocationResponse(
                has_location=True,
                business_name=business.business_name,
                formatted_address=business.business_address,
                latitude=business.latitude,
                longitude=business.longitude,
                place_id=business.google_place_id
            )
        
        # Fallback to Google Business Location from onboarding
        google_repo = GoogleBusinessRepository()
        google_location = await google_repo.find_by_user_id(current_user_email)
        
        if google_location and google_location.latitude and google_location.longitude:
            return HyperlocalBusinessLocationResponse(
                has_location=True,
                business_name=google_location.business_name,
                formatted_address=google_location.address,
                latitude=google_location.latitude,
                longitude=google_location.longitude,
                place_id=google_location.place_id
            )
        
        # No location found
        return HyperlocalBusinessLocationResponse(
            has_location=False
        )
    
    except Exception as e:
        print(f"Error fetching saved location: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch saved location"
        ) from e


@router.post("/save", response_model=HyperlocalBusinessSetupResponse)
async def save_hyperlocal_setup(
    setup: HyperlocalBusinessSetupRequest,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Save hyperlocal business setup (all fields required)
    
    Stores business name, type, and precise location for geo-targeting campaigns
    """
    try:
        # Create repository instance
        business_repo = BusinessRepository()
        
        # Save to database
        business = await business_repo.update_hyperlocal_setup(
            user_id=current_user_email,
            business_name=setup.business_name,
            business_type=setup.business_type,
            latitude=setup.latitude,
            longitude=setup.longitude,
            place_id=setup.place_id,
            formatted_address=setup.formatted_address
        )
        
        return HyperlocalBusinessSetupResponse(
            business_name=business.business_name,
            business_type=business.business_type,
            latitude=business.latitude,
            longitude=business.longitude,
            place_id=business.google_place_id,
            formatted_address=business.business_address
        )
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        print(f"Error saving hyperlocal setup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save hyperlocal business setup"
        ) from e


@router.get("/current")
async def get_current_setup(
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Get current hyperlocal business setup.
    
    Returns saved hyperlocal setup if available, otherwise returns location from onboarding
    with empty business fields. This ensures the location is always shown if available.
    """
    business_repo = BusinessRepository()
    google_repo = GoogleBusinessRepository()
    
    business = await business_repo.get_by_user_id(current_user_email)
    
    # If business exists with hyperlocal data, return it
    if business and business.business_name and business.business_type:
        return {
            "business_name": business.business_name,
            "business_type": business.business_type,
            "latitude": business.latitude or 0.0,
            "longitude": business.longitude or 0.0,
            "place_id": business.google_place_id,
            "formatted_address": business.business_address,
            "has_setup": True
        }
    
    # Check for location from onboarding (Google Business)
    google_location = await google_repo.find_by_user_id(current_user_email)
    
    if google_location and google_location.latitude and google_location.longitude:
        return {
            "business_name": google_location.business_name or "",
            "business_type": "",
            "latitude": google_location.latitude,
            "longitude": google_location.longitude,
            "place_id": google_location.place_id,
            "formatted_address": google_location.address,
            "has_setup": False
        }
    
    # Check if business has partial data (location from onboarding saved to business)
    if business and business.latitude and business.longitude:
        return {
            "business_name": business.business_name or "",
            "business_type": business.business_type or "",
            "latitude": business.latitude,
            "longitude": business.longitude,
            "place_id": business.google_place_id,
            "formatted_address": business.business_address,
            "has_setup": False
        }
    
    # No data found at all
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No location or hyperlocal setup found. Please complete onboarding first."
    )
