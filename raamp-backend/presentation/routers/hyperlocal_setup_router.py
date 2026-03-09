"""
Hyperlocal Business Setup Router - handles location and business details for geo-targeting
"""
from fastapi import APIRouter, Depends, HTTPException, status
from infrastructure.repositories.business_repository import BusinessRepository
from infrastructure.database.models.user_model import UserModel
from presentation.schemas.hyperlocal_setup_schema import (
    HyperlocalBusinessSetupRequest,
    HyperlocalBusinessSetupResponse,
    HyperlocalBusinessLocationResponse
)
from presentation.routers.auth_router import get_current_user_id


router = APIRouter(prefix="/api/hyperlocal-setup", tags=["Hyperlocal Setup"])


@router.get("/location", response_model=HyperlocalBusinessLocationResponse)
async def get_saved_location(
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get the user's saved location from previous onboarding step
    
    Returns location data from BusinessModel (Single Source of Truth)
    """
    try:
        # BusinessModel is now the single source of truth for location data
        business_repo = BusinessRepository()
        business = await business_repo.get_by_user_id(current_user_id)
        
        if business and business.latitude and business.longitude:
            return HyperlocalBusinessLocationResponse(
                has_location=True,
                business_name=business.business_name,
                formatted_address=business.business_address,
                latitude=business.latitude,
                longitude=business.longitude,
                place_id=business.google_place_id
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
    current_user_id: str = Depends(get_current_user_id)
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
            user_id=current_user_id,
            business_name=setup.business_name,
            business_type=setup.business_type,
            latitude=setup.latitude,
            longitude=setup.longitude,
            place_id=setup.place_id,
            formatted_address=setup.formatted_address,
            website=setup.website,
            phone_number=setup.phone,
            description=setup.description,
            city=setup.city,
            country=setup.country
        )
        
        # Update google_maps_connected flag and onboarding_location if coordinates are valid
        if setup.latitude and setup.longitude:
            from infrastructure.repositories.user_repository_impl import UserRepository
            from bson import ObjectId
            import logging
            user_repo = UserRepository()
            # Get user by id to find email (convert string ID to ObjectId)
            try:
                user = await UserModel.get(ObjectId(current_user_id))
            except Exception as e:
                logging.error("Failed to fetch user by ID %s: %s", current_user_id, str(e))
                user = None
            
            if user:
                logging.info("Updating google_maps_connected flag and onboarding_location for user %s", user.email)
                result = await user_repo.update_connection_flags(user.email, google_maps=True)
                logging.info("Flag update result: %s, user.google_maps_connected should now be True", result)
                
                # Set onboarding_location (locked for trend analysis) - use country code
                if setup.country:
                    user.onboarding_location = setup.country
                    await user.save()
                    logging.info("Set onboarding_location=%s for user %s", setup.country, user.email)
            else:
                logging.warning("User not found for ID: %s", current_user_id)
        
        return HyperlocalBusinessSetupResponse(
            business_name=business.business_name,
            business_type=business.business_type,
            latitude=business.latitude,
            longitude=business.longitude,
            place_id=business.google_place_id,
            formatted_address=business.business_address,
            website=business.website,
            phone=business.phone_number,
            description=business.description,
            city=business.city,
            country=business.country
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
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get current hyperlocal business setup.
    
    Returns saved hyperlocal setup from BusinessModel (Single Source of Truth).
    """
    business_repo = BusinessRepository()
    
    business = await business_repo.get_by_user_id(current_user_id)
    
    # If business exists with hyperlocal data (business_type set), return full setup
    if business and business.business_name and business.business_type:
        return {
            "business_name": business.business_name,
            "business_type": business.business_type,
            "latitude": business.latitude or 0.0,
            "longitude": business.longitude or 0.0,
            "place_id": business.google_place_id,
            "formatted_address": business.business_address,
            "city": business.city,
            "country": business.country,
            "website": business.website,
            "phone": business.phone_number,
            "description": business.description,
            "has_setup": True
        }
    
    # Business has location data but not full hyperlocal setup
    if business and business.latitude and business.longitude:
        return {
            "business_name": business.business_name or "",
            "business_type": business.business_type or "",
            "latitude": business.latitude,
            "longitude": business.longitude,
            "place_id": business.google_place_id,
            "formatted_address": business.business_address,
            "city": business.city,
            "country": business.country,
            "website": business.website,
            "phone": business.phone_number,
            "description": business.description,
            "has_setup": False
        }
    
    # No data found at all
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No location or hyperlocal setup found. Please complete onboarding first."
    )
