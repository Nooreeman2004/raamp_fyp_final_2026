import httpx
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from presentation.routers.auth_router import get_current_user_email
from application.services.onboarding_service import OnboardingService

router = APIRouter(prefix="/api/v1/meta", tags=["meta-ads"])
service = OnboardingService()

META_API = "https://graph.facebook.com/v22.0"


class DeployDraftRequest(BaseModel):
    ad_account_id: str        # e.g. "act_123456789"
    campaign_name: str
    objective: str            # e.g. "OUTCOME_TRAFFIC"
    daily_budget: int         # in cents, e.g. 1000 = $10.00
    caption: str
    latitude: float
    longitude: float
    radius_meters: int
    page_id: str              # Facebook Page ID required for ad creative


class DeployDraftResponse(BaseModel):
    campaign_id: str
    adset_id: str
    creative_id: str
    ad_id: str
    ads_manager_url: str


@router.post("/deploy-draft", response_model=DeployDraftResponse)
async def deploy_draft(
    payload: DeployDraftRequest,
    current_user_email: str = Depends(get_current_user_email)
):
    # get access token
    fb = await service.facebook_repo.find_by_user_id(current_user_email)
    if not fb or not getattr(fb, "access_token", None):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Facebook not connected")

    token = fb.access_token
    act = payload.ad_account_id
    if not act.startswith("act_"):
        act = f"act_{act}"

    async with httpx.AsyncClient(timeout=30) as client:
        # 1. Create campaign
        r = await client.post(f"{META_API}/{act}/campaigns", data={
            "name": payload.campaign_name,
            "objective": payload.objective,
            "status": "PAUSED",
            "special_ad_categories": "[]",
            "access_token": token,
        })
        _raise_if_meta_error(r, "campaign")
        campaign_id = r.json()["id"]

        # 2. Create ad set
        r = await client.post(f"{META_API}/{act}/adsets", data={
            "name": f"{payload.campaign_name} – Ad Set",
            "campaign_id": campaign_id,
            "billing_event": "IMPRESSIONS",
            "optimization_goal": "REACH",
            "daily_budget": str(payload.daily_budget),
            "status": "PAUSED",
            "targeting": str({
                "geo_locations": {
                    "custom_locations": [{
                        "latitude": payload.latitude,
                        "longitude": payload.longitude,
                        "radius": round(payload.radius_meters / 1000, 1),
                        "distance_unit": "kilometer"
                    }]
                }
            }),
            "access_token": token,
        })
        _raise_if_meta_error(r, "adset")
        adset_id = r.json()["id"]

        # 3. Create ad creative
        r = await client.post(f"{META_API}/{act}/adcreatives", data={
            "name": f"{payload.campaign_name} – Creative",
            "object_story_spec": str({
                "page_id": payload.page_id,
                "link_data": {
                    "message": payload.caption,
                    "link": "https://www.facebook.com",
                }
            }),
            "access_token": token,
        })
        _raise_if_meta_error(r, "creative")
        creative_id = r.json()["id"]

        # 4. Create ad
        r = await client.post(f"{META_API}/{act}/ads", data={
            "name": f"{payload.campaign_name} – Ad",
            "adset_id": adset_id,
            "creative": str({"creative_id": creative_id}),
            "status": "PAUSED",
            "access_token": token,
        })
        _raise_if_meta_error(r, "ad")
        ad_id = r.json()["id"]

    ads_manager_url = f"https://www.facebook.com/adsmanager/manage/ads?act={act}"

    return DeployDraftResponse(
        campaign_id=campaign_id,
        adset_id=adset_id,
        creative_id=creative_id,
        ad_id=ad_id,
        ads_manager_url=ads_manager_url
    )


def _raise_if_meta_error(r: httpx.Response, step: str):
    """Raise a safe 502 on Meta API failure, while logging details server-side."""
    try:
        r.raise_for_status()
    except Exception:
        # Log full response for debugging (server-side only)
        logging.error("Meta API error at %s: status=%s body=%s", step, getattr(r, "status_code", None), getattr(r, "text", ""))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Meta API request failed at step '{step}'. Please try again in a moment."
        )

