from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class OnboardingStatusResponse(BaseModel):
    completed: bool
    missing: Dict[str, bool]
    redirect: Optional[str] = None


class FacebookPageDTO(BaseModel):
    id: str
    name: Optional[str]


class FacebookConnectionResponse(BaseModel):
    user_id: str
    access_token: str
    fb_user_id: Optional[str]
    fb_pages: Optional[list[FacebookPageDTO]] = []


class InstagramConnectionResponse(BaseModel):
    user_id: str
    ig_business_id: Optional[str]
    username: Optional[str]
    profile_picture_url: Optional[str]
    account_type: Optional[str]
    linked_fb_page_id: Optional[str]


class GoogleBusinessConnectionResponse(BaseModel):
    user_id: str
    business_name: Optional[str]
    address: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    place_id: Optional[str]


class OnboardingCompletedResponse(BaseModel):
    completed: bool = True
    redirect: str = "/business/setup"


class GoogleConnectRequest(BaseModel):
    business_name: str
    address: str
    latitude: float
    longitude: float
    google_place_id: str


# Maps / Onboarding - DTOs
class MapSearchRequest(BaseModel):
    query: str


class PlaceResultDTO(BaseModel):
    name: str
    address: Optional[str]
    place_id: str


class MapSearchResponse(BaseModel):
    places: list[PlaceResultDTO] = []


class MapConfirmRequest(BaseModel):
    place_id: str
    name: Optional[str]


class MapConfirmResponse(BaseModel):
    place_id: str
    name: Optional[str]
    address: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    preview_url: Optional[str]


class MapSaveRequest(BaseModel):
    place_id: str
    name: str
    address: str
    lat: Optional[float] = None
    lng: Optional[float] = None


class MapSaveResponse(BaseModel):
    message: str
    place_id: str
    name: str
    address: str


# Generic connection status shape returned to frontend to avoid exposing tokens
class ConnectionStatus(BaseModel):
    connected: bool
    details: Dict[str, Any] = Field(default_factory=dict)
