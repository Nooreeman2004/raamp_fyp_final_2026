from fastapi import APIRouter, Depends, HTTPException, status
from presentation.schemas.onboarding_schemas import (
    MapSearchRequest,
    MapSearchResponse,
    MapConfirmRequest,
    MapConfirmResponse,
    MapSaveRequest,
    MapSaveResponse,
    PlaceResultDTO,
)
from application.use_cases.query_business_locations_usecase import query_business_locations_usecase
from application.use_cases.confirm_business_location_usecase import confirm_business_location_usecase
from application.use_cases.save_business_location_usecase import save_business_location_usecase
from presentation.routers.auth_router import get_current_user_email

router = APIRouter(prefix="/api/profile/onboarding/maps", tags=["onboarding-maps"])


@router.post('/search', response_model=MapSearchResponse)
async def maps_search(payload: MapSearchRequest, current_user_email: str = Depends(get_current_user_email)):
    try:
        places = await query_business_locations_usecase(payload.query)
        # convert to DTO list
        dto_list = [PlaceResultDTO(**p) for p in places]
        return {"places": dto_list}
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid search request")
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to search locations")


@router.post('/confirm', response_model=MapConfirmResponse)
async def maps_confirm(payload: MapConfirmRequest, current_user_email: str = Depends(get_current_user_email)):
    try:
        preview = await confirm_business_location_usecase(place_id=payload.place_id, name=payload.name)
        return MapConfirmResponse(**preview)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid confirm request")
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to confirm location")


@router.post('/save', response_model=MapSaveResponse)
async def maps_save(payload: MapSaveRequest, current_user_email: str = Depends(get_current_user_email)):
    try:
        res = await save_business_location_usecase(user_email=current_user_email, place_id=payload.place_id, name=payload.name, address=payload.address, latitude=payload.lat, longitude=payload.lng)
        return MapSaveResponse(**res)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid save request")
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save location")
