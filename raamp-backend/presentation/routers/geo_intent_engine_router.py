# Presentation Layer - Geo-Intent Marketing Engine Router
# Mounts at /api/v1/geo  (registered in main.py)
import logging
import time

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
import asyncio
import json
import re
from urllib.parse import urlencode
from presentation.routers.activity_router import log_activity
from application.utils.background_tasks import create_background_task
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field

from presentation.routers.auth_router import get_current_user_email
from application.constants import TimeRangeDefaults
from application.services.credit_service import get_credit_service
from presentation.schemas.geo_intent_schemas import (
    CampaignHistoryResponse,
    CampaignLogEntry,
    GeoJSONFeature,
    GeoJSONGeometry,
    GeoJSONProperties,
    HeatScoreRequest,
    HeatScoreResponse,
    HeatmapResponse,
    SignalBreakdown,
)
from application.services.geo_intent_service import GeoIntentService
from infrastructure.repositories.business_repository import BusinessRepository
from infrastructure.database.models.user_model import UserModel

logger = logging.getLogger(__name__)


async def resolve_geo_campaign_business_id(
    user_email: str,
    explicit_business_id: Optional[str],
) -> str:
    """
    Align with client geo keys: explicit Google Place ID, else BusinessModel place_id,
    else stable onboarding coordinates, else user-scoped id.
    """
    if explicit_business_id and str(explicit_business_id).strip():
        return str(explicit_business_id).strip()

    user = await UserModel.find_one(UserModel.email == user_email)
    if not user:
        safe = user_email.replace("@", "_at_").replace(".", "_")
        return f"email_{safe}"

    business = await BusinessRepository().get_by_user_id(str(user.id))
    if business:
        pid = (business.google_place_id or "").strip()
        if pid:
            return pid
        lat, lng = business.latitude, business.longitude
        if lat is not None and lng is not None:
            return f"onboarding_{float(lat):.6f}_{float(lng):.6f}"

    return f"user_{user.id}"

router = APIRouter(prefix="/api/v1/geo", tags=["Geo-Intent Marketing Engine"])


class ZoneRecommendationRequest(BaseModel):
    business_id: str
    keywords: List[str]
    latitude: float
    longitude: float
    radius: int = Field(default=1000, ge=500, le=50000)
    is_indoor: bool = False


class ZoneResult(BaseModel):
    label: str
    latitude: float
    longitude: float
    score: int
    urgency: str
    reason: str
    signals: Dict[str, float]


class ZoneRecommendationResponse(BaseModel):
    zones: List[ZoneResult]
    center_lat: float
    center_lng: float
    radius_m: int
    timestamp: datetime


# ---------------------------------------------------------------------------
# Dependency injection
# ---------------------------------------------------------------------------

def get_geo_intent_service() -> GeoIntentService:
    """DI factory — returns a fresh GeoIntentService per request."""
    return GeoIntentService()


# ---------------------------------------------------------------------------
# POST /heat-score
# ---------------------------------------------------------------------------

@router.post(
    "/heat-score",
    response_model=HeatScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Compute geo-intent heat score",
    description=(
        "Fetches real-world signals (Google Trends, Google Places, Tomorrow.io Weather) "
        "in parallel, computes a weighted heat score (0–100), classifies urgency, "
        "and persists the run to MongoDB."
    ),
)
async def compute_heat_score(
    request: HeatScoreRequest,
    background_tasks: BackgroundTasks,
    current_user_email: str = Depends(get_current_user_email),
    service: GeoIntentService = Depends(get_geo_intent_service),
) -> HeatScoreResponse:
    """
    Compute a geo-intent heat score for a business location.

    **Weights**: Trends 35 % · Places 40 % · Weather 25 %

    **Urgency thresholds**: Low 0–30 · Medium 31–60 · High 61–89 · Critical 90–100
    """
    logger.info(
        "POST /api/v1/geo/heat-score — user=%s business_id=%s lat=%.4f lng=%.4f",
        current_user_email,
        request.business_id,
        request.latitude,
        request.longitude,
    )

    t_req = time.perf_counter()
    try:
        result = await service.compute(
            business_id=request.business_id,
            keywords=request.keywords,
            latitude=request.latitude,
            longitude=request.longitude,
            radius=request.radius,
            is_indoor=request.is_indoor,
            background_tasks=background_tasks,
            user_id=current_user_email,
        )
    except Exception as exc:
        logger.error(
            "Heat score computation failed for user=%s after %.2fs: %s",
            current_user_email,
            time.perf_counter() - t_req,
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Heat score computation failed. Please try again.",
        ) from exc

    logger.info(
        "POST /api/v1/geo/heat-score OK — user=%s total_request_time=%.2fs score=%s",
        current_user_email,
        time.perf_counter() - t_req,
        result.get("score"),
    )

    if result["urgency"] in ["High", "Critical"]:
        create_background_task(
            log_activity(
                business_id=request.business_id,
                event_type="heat_spike",
                title="Market Heat Spike",
                subtitle=f"Urgency: {result['urgency']} score detected"
            ),
            task_name="log_heat_spike"
        )

    return HeatScoreResponse(
        score=result["score"],
        urgency=result["urgency"],
        is_critical=result["is_critical"],
        signals=SignalBreakdown(
            trends_score=result["signals"]["trends_score"],
            places_score=result["signals"]["places_score"],
            weather_score=result["signals"]["weather_score"],
        ),
        signals_status=result["signals_status"],
        reasoning=result.get("reasoning"),
        persona_split=result.get("persona_split", []),
        radar_feed=result.get("radar_feed", []),
        latitude=result.get("latitude"),
        longitude=result.get("longitude"),
        radius_km=result.get("radius_km"),
        timestamp=result["timestamp"],
    )


@router.post(
    "/recommend-zones",
    response_model=ZoneRecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get top 3 nearby zones to run ads",
)
async def recommend_zones(
    request: ZoneRecommendationRequest,
    current_user_email: str = Depends(get_current_user_email),
    service: GeoIntentService = Depends(get_geo_intent_service),
) -> ZoneRecommendationResponse:
    """Score 8 compass zones around the business in parallel; return the top 3 by heat score."""
    credit_service = get_credit_service()
    await credit_service.check_and_deduct(current_user_email, "geo_radar_scan")

    logger.info(
        "POST /api/v1/geo/recommend-zones — user=%s business_id=%s lat=%.4f lng=%.4f",
        current_user_email,
        request.business_id,
        request.latitude,
        request.longitude,
    )

    t_req = time.perf_counter()
    try:
        zones = await service.recommend_zones(
            business_id=request.business_id,
            keywords=request.keywords,
            latitude=request.latitude,
            longitude=request.longitude,
            radius=request.radius,
            is_indoor=request.is_indoor,
            user_id=current_user_email,
        )
    except Exception as exc:
        logger.error(
            "Zone recommendation failed for user=%s after %.2fs: %s",
            current_user_email,
            time.perf_counter() - t_req,
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Zone recommendation failed. Please try again.",
        ) from exc

    logger.info(
        "POST /api/v1/geo/recommend-zones OK — user=%s total_request_time=%.2fs zones_returned=%d",
        current_user_email,
        time.perf_counter() - t_req,
        len(zones),
    )

    return ZoneRecommendationResponse(
        zones=[ZoneResult(**z) for z in zones],
        center_lat=request.latitude,
        center_lng=request.longitude,
        radius_m=request.radius,
        timestamp=datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
# GET /heatmap
# ---------------------------------------------------------------------------

@router.get(
    "/heatmap",
    response_model=HeatmapResponse,
    status_code=status.HTTP_200_OK,
    summary="Get GeoJSON heatmap of recent heat scores",
    description=(
        "Returns a GeoJSON FeatureCollection of recent heat score points "
        "compatible with Google Maps heatmap layers."
    ),
)
async def get_heatmap(
    business_id: str = None,
    limit: int = 100,
    current_user_email: str = Depends(get_current_user_email),
    service: GeoIntentService = Depends(get_geo_intent_service),
) -> HeatmapResponse:
    """
    Retrieve the latest heat score points as a GeoJSON FeatureCollection.

    Optionally filter by **business_id** to scope results to a single business.
    """
    logger.info(
        "GET /api/v1/geo/heatmap — user=%s business_id=%s limit=%d",
        current_user_email,
        business_id,
        limit,
    )

    try:
        raw_features = await service.get_heatmap(business_id=business_id, limit=min(limit, 500))
    except Exception as exc:
        logger.error(
            "Heatmap fetch failed for user=%s: %s",
            current_user_email,
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch heatmap data. Please try again.",
        ) from exc

    features = [
        GeoJSONFeature(
            geometry=GeoJSONGeometry(
                type=f["geometry"]["type"],
                coordinates=f["geometry"]["coordinates"],
            ),
            properties=GeoJSONProperties(
                score=f["properties"]["score"],
                urgency=f["properties"]["urgency"],
                zone=f["properties"]["zone"],
                timestamp=f["properties"]["timestamp"],
            ),
        )
        for f in raw_features
    ]

    return HeatmapResponse(type="FeatureCollection", features=features)


# ---------------------------------------------------------------------------
# GET /history/{business_id}
# ---------------------------------------------------------------------------

@router.get(
    "/history/{business_id}",
    response_model=CampaignHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get campaign log history for a business",
    description=(
        "Returns the most recent campaign log entries for the specified business, "
        "ordered newest first."
    ),
)
async def get_campaign_history(
    business_id: str,
    limit: int = 50,
    current_user_email: str = Depends(get_current_user_email),
    service: GeoIntentService = Depends(get_geo_intent_service),
) -> CampaignHistoryResponse:
    """
    Retrieve geo-intent campaign history for a specific business.

    Returns signal breakdowns, scores, and urgency for each past run.
    """
    logger.info(
        "GET /api/v1/geo/history/%s — user=%s limit=%d",
        business_id,
        current_user_email,
        limit,
    )

    try:
        logs = await service.get_campaign_history(
            business_id=business_id,
            limit=min(limit, 200),
        )
    except Exception as exc:
        logger.error(
            "Campaign history fetch failed for business_id=%s user=%s: %s",
            business_id,
            current_user_email,
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch campaign history. Please try again.",
        ) from exc

    return CampaignHistoryResponse(
        business_id=business_id,
        total=len(logs),
        logs=[CampaignLogEntry(**entry) for entry in logs],
    )

@router.get(
    "/heat-score/history/{business_id}",
    response_model=List[dict],
    status_code=status.HTTP_200_OK,
    summary="Get heat score history for the last X days"
)
async def get_heat_score_history(
    business_id: str,
    days: int = Query(TimeRangeDefaults.DEFAULT_DAYS_SHORT, le=TimeRangeDefaults.DEFAULT_DAYS_MEDIUM),
    current_user_email: str = Depends(get_current_user_email),
    service: GeoIntentService = Depends(get_geo_intent_service),
):
    """
    Get the maximum heat score per day for the specified number of days.
    """
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        # Fetch significant number of logs to cover requested days
        logs = await service.get_campaign_history(business_id=business_id, limit=days * 10)
        
        # Initialize the history map with default zero values for each requested day
        daily_max = {}
        for i in range(days):
            date_obj = (datetime.utcnow() - timedelta(days=i))
            date_str = date_obj.strftime("%Y-%m-%d")
            daily_max[date_str] = {"date": date_str, "max_score": 0, "urgency": "Low"}
            
        for log in logs:
            log_date = log.get("timestamp")
            if isinstance(log_date, datetime) and log_date >= start_date:
                date_str = log_date.strftime("%Y-%m-%d")
                if date_str in daily_max:
                    if log["final_score"] > daily_max[date_str]["max_score"]:
                        daily_max[date_str]["max_score"] = log["final_score"]
                        daily_max[date_str]["urgency"] = log["urgency"]
                        
        # Returns sorted from oldest to newest for Recharts
        return sorted(daily_max.values(), key=lambda x: x["date"])
    except Exception as e:
        logger.error(f"Error in get_heat_score_history: {e}")
        return []

@router.get(
    "/best-posting-time/{business_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Calculate optimal posting windows"
)
async def get_best_posting_time(
    business_id: str,
    current_user_email: str = Depends(get_current_user_email),
    service: GeoIntentService = Depends(get_geo_intent_service),
):
    """
    Analyzes historical heat scores to determine the best hours and day of the week for posting.
    """
    try:
        # Fetch historical logs for analysis
        logs = await service.get_campaign_history(business_id=business_id, limit=500)
        
        if not logs:
            return {"best_hours": [], "best_day": "N/A", "based_on_days": 0}
            
        hour_scores: Dict[int, List[int]] = {h: [] for h in range(24)}
        day_scores: Dict[int, List[int]] = {d: [] for d in range(7)}
        found_dates = set()
        
        for log in logs:
            ts = log.get("timestamp")
            if isinstance(ts, datetime):
                found_dates.add(ts.date())
                hour_scores[ts.hour].append(log["final_score"])
                day_scores[ts.weekday()].append(log["final_score"])
                
        # Calculate hourly averages
        avg_hours = []
        for h, scores in hour_scores.items():
            if scores:
                avg_hours.append({"hour": h, "avg_score": round(sum(scores) / len(scores), 1)})
        
        avg_hours.sort(key=lambda x: x["avg_score"], reverse=True)
        
        # Calculate daily averages
        best_day_idx = -1
        max_day_score = -1
        for d, scores in day_scores.items():
            if scores:
                avg = sum(scores) / len(scores)
                if avg > max_day_score:
                    max_day_score = avg
                    best_day_idx = d
                    
        days_map = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        return {
            "best_hours": avg_hours[:2],
            "best_day": days_map[best_day_idx] if best_day_idx != -1 else "N/A",
            "based_on_days": len(found_dates)
        }
    except Exception as e:
        logger.error(f"Error in get_best_posting_time: {e}")
        return {"best_hours": [], "best_day": "N/A", "based_on_days": 0}
# ---------------------------------------------------------------------------
# Campaign Brief Models & Endpoints
# ---------------------------------------------------------------------------

class GeoCampaignBriefRequest(BaseModel):
    lat: float
    lng: float
    radius_km: float
    heat_score: float
    urgency: str
    trends_score: float
    weather_score: float
    places_score: float
    reasoning: Optional[str] = None
    persona_split: List[Dict[str, Any]]  # Backend stores as list of dicts
    keywords: List[str] = []
    business_id: Optional[str] = Field(
        None,
        description="Google Place ID or onboarding_lat_lng key; if omitted, resolved from the user's Business profile.",
    )

class GeoCampaignBriefResponse(BaseModel):
    campaign_id: Optional[str] = None
    zone_label: str
    dominant_persona: str
    dominant_persona_pct: int
    best_time_window: str
    suggested_budget_min: int
    suggested_budget_max: int
    caption: str  # Default caption for backward compatibility
    caption_variants: Dict[str, str] = Field(default_factory=dict)
    hashtags: List[str]
    meta_objective: str
    meta_deep_link: str
    reasoning: str
    heat_score: float
    urgency: str
    coordinates_display: str

async def _generate_geo_strategy(
    request: GeoCampaignBriefRequest,
    dominant_persona: str,
    dominant_persona_pct: int
) -> Dict[str, Any]:
    """Call Gemini for hyper-local multi-variant captions; on failure, use scan-grounded copy."""
    try:
        from application.services.content_generation_service import ContentGenerationService
        generator = ContentGenerationService()
        
        system_prompt = """You are a hyper-local marketing director. 
Generate 3 distinct Instagram caption variants optimized for a specific 
local audience detected by a real-time geo-intelligence scan.

VARAINT TYPES:
1. Aggressive (High energy, direct focus, strong CTA)
2. Soft (Informative, community-focused, relaxed tone)
3. Urgency (FOMO-based, limited time focus)

Return JSON only: 
{
  "aggressive": "...", 
  "soft": "...", 
  "urgency": "...", 
  "hashtags": ["...", "..."],
  "strategy_rationale": "One sentence explaining why these variants work here."
}"""

        user_prompt = f"""
Local Intelligence Report:
- Heat Score: {request.heat_score}/100 ({request.urgency} urgency)
- Primary Audience: {dominant_persona} ({dominant_persona_pct}% 
  of local foot traffic)
- Signal Summary: {request.reasoning or 'Stable market conditions with moderate local activity.'}
- Weather Favorability: {request.weather_score:.0f}/100
- Search Trend Strength: {request.trends_score:.0f}/100
- Campaign Keywords: {', '.join(request.keywords) if 
  request.keywords else 'general promotion'}

Generate a caption that speaks directly to {dominant_persona} 
in this area right now. Make it feel timely and local.
Include a clear call to action.
"""
        # We use a lower level call or a mock if service is complex, 
        # but here we'll try to use the generator's underlying client safely
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        from google.genai import types as genai_types
        response = await asyncio.to_thread(
            lambda: generator.client.models.generate_content(
                model=generator.model,
                contents=full_prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=0.7,
                    response_mime_type="application/json",
                )
            )
        )
        data = json.loads(response.text)
        return data
        
    except Exception as e:
        logger.warning(f"Geo strategy generation failed: {e}")
        kw = ", ".join(request.keywords[:5]) if request.keywords else "local offers"
        persona = dominant_persona or "nearby audiences"
        zone = f"{float(request.radius_km):.1f}km"
        heat = int(round(request.heat_score))
        base = (
            f"📍 Heat {heat}/100 in a {zone} radius around "
            f"{request.lat:.4f}, {request.lng:.4f}. "
            f"Primary audience: {persona}. Focus: {kw}."
        )
        tag_list: List[str] = []
        for t in (request.keywords[:8] if request.keywords else ["local", "shop", "nearme"]):
            c = "".join(ch for ch in str(t).lower().replace(" ", "") if ch.isalnum())
            if c:
                tag_list.append(f"#{c}")
        for extra in ("geo", "localbiz"):
            if f"#{extra}" not in tag_list:
                tag_list.append(f"#{extra}")
        tag_list = list(dict.fromkeys(tag_list))[:12]
        return {
            "aggressive": f"🔥 High intent right now — {base} Tap in before the window closes.",
            "soft": f"✨ {base} We're here when you're ready — message or visit us today.",
            "urgency": f"⏰ Limited attention window for this zone — {base} Claim your spot today.",
            "hashtags": tag_list,
            "strategy_rationale": (
                f"LLM unavailable; copy grounded on heat {heat}, radius {zone}, and persona {persona}."
            ),
        }

@router.post(
    "/generate-campaign-brief",
    response_model=GeoCampaignBriefResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a geo-targeted campaign brief"
)
async def generate_campaign_brief(
    request: GeoCampaignBriefRequest,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Constructs a complete advertising strategy brief based on geo-intent signals.
    Involves AI-driven caption generation and budget allocation logic.
    """
    # 0. Check Credits
    from application.services.credit_service import get_credit_service
    credit_service = get_credit_service()
    await credit_service.check_and_deduct(current_user_email, "campaign_brief")

    # 1. Identify Dominant Persona
    dominant_persona = "General Audience"
    dominant_persona_pct = 0
    if request.persona_split:
        # Sort by pct descending
        sorted_personas = sorted(request.persona_split, key=lambda x: x.get("pct", 0), reverse=True)
        if sorted_personas:
            dominant_persona = sorted_personas[0].get("type", "General Audience")
            dominant_persona_pct = int(sorted_personas[0].get("pct", 0))

    # 2. Determine Best Time Window (UTC based)
    hour = datetime.utcnow().hour
    if 5 <= hour < 10:
        time_window = "Morning (6am–10am) — Commuter window active"
    elif 10 <= hour < 14:
        time_window = "Midday (11am–2pm) — Lunch traffic peak"
    elif 14 <= hour < 18:
        time_window = "Afternoon (2pm–6pm) — Post-work browsing"
    elif 18 <= hour < 22:
        time_window = "Evening (6pm–10pm) — Peak engagement window"
    else:
        time_window = "Late Night (10pm–5am) — Low traffic period"

    # 3. Budget Logic (PKR)
    budget_map = {
        "Low": (300, 700),
        "Medium": (700, 1500),
        "High": (1500, 3000),
        "Critical": (3000, 6000)
    }
    b_min, b_max = budget_map.get(request.urgency, (300, 700))

    # 4. Meta Objective
    if request.urgency in ["High", "Critical"]:
        objective = "REACH"
    elif request.trends_score >= 70:
        objective = "TRAFFIC"
    else:
        objective = "ENGAGEMENT"

    # 5. Deep Link
    base_url = "https://adsmanager.facebook.com/adsmanager/creation"
    params = {
        "objective": objective,
        "placement": "instagram_feed"
    }
    deep_link = f"{base_url}?{urlencode(params)}"

    # 6. AI Strategy (Multi-variant)
    ai_strategy = await _generate_geo_strategy(request, dominant_persona, dominant_persona_pct)
    captions = {
        "aggressive": ai_strategy.get("aggressive", ""),
        "soft": ai_strategy.get("soft", ""),
        "urgency": ai_strategy.get("urgency", "")
    }

    # 7. Coordinates Display
    lat_val = abs(request.lat)
    lat_dir = "N" if request.lat >= 0 else "S"
    lng_val = abs(request.lng)
    lng_dir = "E" if request.lng >= 0 else "W"
    coord_display = f"{lat_val:.4f}° {lat_dir}, {lng_val:.4f}° {lng_dir}"

    # 8. Assemble Full Blueprint for Persistence
    resolved_business_id = await resolve_geo_campaign_business_id(
        current_user_email, request.business_id
    )
    brief_data = {
        "user_email": current_user_email,
        "business_id": resolved_business_id,
        "location": {"type": "Point", "coordinates": [request.lng, request.lat]},
        "radius_km": request.radius_km,
        "coordinates_display": coord_display,
        "heat_score": request.heat_score,
        "urgency": request.urgency,
        "trends_score": request.trends_score,
        "weather_score": request.weather_score,
        "places_score": request.places_score,
        "persona_split": request.persona_split,
        "strategy_rationale": ai_strategy.get("strategy_rationale") or request.reasoning or "AI-driven geo strategy.",
        "captions": captions,
        "hashtags": ai_strategy.get("hashtags", []),
        "best_time_window": time_window,
        "suggested_budget": {"min": b_min, "max": b_max},
        "meta_objective": objective,
        "meta_deep_link": deep_link
    }

    # 9. Store in MongoDB
    service = GeoIntentService()
    campaign_id = await service.persist_strategic_brief(brief_data)

    # 10. Return Response
    return GeoCampaignBriefResponse(
        campaign_id=campaign_id,
        zone_label=f"High-Intent Zone ({request.radius_km}km radius)",
        dominant_persona=dominant_persona,
        dominant_persona_pct=dominant_persona_pct,
        best_time_window=time_window,
        suggested_budget_min=b_min,
        suggested_budget_max=b_max,
        caption=captions.get("aggressive", ""),  # Fallback to aggressive for default
        caption_variants=captions,
        hashtags=ai_strategy.get("hashtags", []),
        meta_objective=objective,
        meta_deep_link=deep_link,
        reasoning=brief_data["strategy_rationale"],
        heat_score=request.heat_score,
        urgency=request.urgency,
        coordinates_display=coord_display
    )

@router.get(
    "/campaign-briefs/{business_id}",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Get strategic brief history"
)
async def get_campaign_brief_history(
    business_id: str,
    limit: int = 20,
    current_user_email: str = Depends(get_current_user_email),
    service: GeoIntentService = Depends(get_geo_intent_service)
):
    """Returns a list of previously generated campaign strategies for this business."""
    # Align business_id resolution with brief persistence logic so history doesn't look empty
    # when the caller uses an alias (place_id vs onboarding coords vs user-scoped id).
    resolved_business_id = await resolve_geo_campaign_business_id(current_user_email, business_id)
    return await service.get_brief_history(resolved_business_id, user_email=current_user_email, limit=limit)

@router.get(
    "/campaign-brief/{brief_id}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get single strategic brief"
)
async def get_single_campaign_brief(
    brief_id: str,
    current_user_email: str = Depends(get_current_user_email),
    service: GeoIntentService = Depends(get_geo_intent_service)
):
    """Retrieves a specific strategic blueprint by its ID."""
    brief = await service.get_brief_by_id(brief_id)
    if not brief:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign brief {brief_id} not found."
        )
    return brief
