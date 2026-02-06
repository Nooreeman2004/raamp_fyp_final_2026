from fastapi import APIRouter, Depends, HTTPException, status
from presentation.routers.auth_router import get_current_user_email
from application.services.maps_local import query_places, show_on_map
from infrastructure.repositories.google_business_repository import GoogleBusinessRepository
from infrastructure.repositories.user_repository_impl import UserRepository
from pydantic import BaseModel, Field
from typing import Optional, List

router = APIRouter(prefix="/api/maps", tags=["maps"])


class MapSearchResult(BaseModel):
    place_id: str
    name: str
    formatted_address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


class MapDetailsResponse(BaseModel):
    place_id: str
    name: Optional[str]
    formatted_address: Optional[str]
    lat: Optional[float]
    lng: Optional[float]


class MapConnectRequest(BaseModel):
    business_id: Optional[str]
    place_id: str
    name: str
    formatted_address: Optional[str]
    lat: Optional[float]
    lng: Optional[float]


class MapConnectResponse(BaseModel):
    message: str
    place_id: str
    name: str
    formatted_address: Optional[str]


@router.get('/search', response_model=List[MapSearchResult])
async def maps_search(query: str, type: Optional[str] = None):
    """Return top 5 places matching query. Uses built-in maps_local service."""
    if not query or not query.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="query parameter is required")
    places = await query_places(query=query, limit=5, type=type)
    # map to response format
    out = []
    for p in places:
        out.append(MapSearchResult(
            place_id=p.get('place_id'),
            name=p.get('name'),
            formatted_address=p.get('address'),
            lat=p.get('latitude'),
            lng=p.get('longitude'),
        ))
    return out


@router.get('/details', response_model=MapDetailsResponse)
async def maps_details(place_id: str):
    if not place_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="place_id is required")
    preview = await show_on_map(place_id=place_id)
    return MapDetailsResponse(
        place_id=preview.get('place_id'),
        name=preview.get('name'),
        formatted_address=preview.get('address'),
        lat=preview.get('latitude'),
        lng=preview.get('longitude'),
    )


@router.post('/connect', response_model=MapConnectResponse)
async def maps_connect(payload: MapConnectRequest, current_user_email: str = Depends(get_current_user_email)):
    """Persist selected place for the user's business and mark google connected."""
    if not payload.place_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="place_id is required")

    # Persist into google business repository (now uses BusinessModel)
    g_repo = GoogleBusinessRepository()
    # Use current_user_email as user_id for now (business_id optional)
    user_id = current_user_email
    doc = await g_repo.create_or_update(user_id, business_name=payload.name, address=payload.formatted_address, latitude=payload.lat, longitude=payload.lng, place_id=payload.place_id)

    # Update user connection flag (Google place details now stored in BusinessModel)
    user_repo = UserRepository()
    await user_repo.update_connection_flags(current_user_email, google_maps=True)

    return MapConnectResponse(message="Google Maps place connected", place_id=doc.google_place_id, name=doc.business_name, formatted_address=doc.business_address)
