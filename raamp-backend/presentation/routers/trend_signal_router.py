# Presentation Layer - Trend Signal Router
from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from fastapi import Request
import logging
import os
from typing import List, Optional, Dict, Any
from fastapi.responses import StreamingResponse
from datetime import datetime, timedelta
import os

from presentation.schemas.trend_signal_schemas import (
    TrendFetchRequest,
    TrendFetchResponse,
    TrendSignalResponse,
    TrendSignalListResponse,
    TrendStatusResponse,
    ContentSuggestionRequest,
    ContentSuggestionResponse,
    ForecastResponse,
    TrendExplainRequest,
    TrendExplainResponse
)
from presentation.schemas.trend_analytics_schemas import (
    LiveTrendsResponse,
    HeatmapResponse,
    SpikeTimelineResponse,
    BubbleChartResponse,
    PlatformReachResponse,
    DataQuality,
    TrendingNowResponse,
    IndustryTrendsResponse,
)
from application.services.google_trends_service import GoogleTrendsService
from application.services.trend_analytics_service import TrendAnalyticsService
from application.services.trend_detection_service import TrendDetectionService
from application.services.trends_providers.trending_now_fetcher import TrendingNowFetcher
from application.services.trend_suggestion_metrics_resolver import (
    resolve_suggestion_metrics_from_detection,
)
from infrastructure.database.models.user_model import UserModel
from presentation.routers.auth_router import get_current_user_email
from infrastructure.database.models.trend_cache_model import TrendCacheModel
from infrastructure.database.models.trend_ai_analysis_model import TrendAIAnalysisModel
from application.services.trend_ai_analysis_service import TrendAIAnalysisService
from application.services.viral_audio_provider import ViralAudioProvider
import httpx
import re


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/trends", tags=["Trend Signals"])

# Simple per-user scan cooldown to prevent accidental quota drain in single-instance deployments.
# NOTE: For multi-instance production, replace with Redis/DB-backed rate limiting.
_LAST_SCAN_AT: dict[str, float] = {}


async def _ai_analysis_status_for_trend(*, trend_id: str, user_id: str) -> Optional[str]:
    try:
        doc = await TrendAIAnalysisModel.find_one({"trend_id": str(trend_id), "user_id": str(user_id)})
        if not doc:
            return None
        st = str(getattr(doc, "status", "") or "").lower()
        if st == "pending":
            return "pending"
        if st == "completed":
            return "ready"
        if st == "failed":
            return "failed"
        return None
    except Exception:
        return None


def _stream_text(text: str):
    async def gen():
        yield text

    return gen()


def _stream_openai_chat(*, system_prompt: str, user_prompt: str):
    """
    Stream plain text from OpenAI Chat Completions.
    Kept local to avoid introducing new infra clients.
    """
    async def gen():
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            yield "AI unavailable: OPENAI_API_KEY not configured."
            return

        model = os.getenv("OPENAI_GENERATION_MODEL", "gpt-4o")
        client = OpenAI(api_key=api_key)

        try:
            stream = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                stream=True,
            )
            for evt in stream:
                try:
                    delta = evt.choices[0].delta.content
                except Exception:
                    delta = None
                if delta:
                    yield delta
        except Exception as e:
            yield f"AI error: {type(e).__name__}: {str(e)[:200]}"

    return gen()


async def _cached_get(namespace: str, key: str):
    now = datetime.utcnow()
    doc = await TrendCacheModel.find_one(
        {
            "namespace": namespace,
            "key": key,
            "expires_at": {"$gt": now},
        }
    )
    if not doc:
        return None
    return doc.value


async def _cached_set(namespace: str, key: str, value: Any, ttl_seconds: int):
    now = datetime.utcnow()
    expires_at = now + timedelta(seconds=max(60, int(ttl_seconds or 0)))
    await TrendCacheModel.find_one(
        {"namespace": namespace, "key": key}
    ).upsert(
        {
            "$set": {
                "namespace": namespace,
                "key": key,
                "value": value,
                "meta": {"ttl_seconds": int(ttl_seconds)},
                "created_at": now,
                "expires_at": expires_at,
            }
        }
    )


def _is_admin_enabled() -> bool:
    import os
    return os.getenv("RAAMP_ADMIN_MODE", "").strip() in ("1", "true", "True", "yes", "YES")


def _require_admin(request: "Request") -> None:
    """
    Admin/dev guard for debug + destructive endpoints.

    - In production, these endpoints should be effectively disabled unless explicitly enabled.
    - In non-prod, allow if RAAMP_ADMIN_MODE is set OR a header token matches.
    """
    import os
    env = (os.getenv("ENV") or os.getenv("RAAMP_ENV") or "").strip().lower()
    is_prod = env in ("prod", "production")

    # Hard disable in prod by default (fail-closed). Can be overridden for emergency debugging.
    if is_prod and os.getenv("RAAMP_ALLOW_DEBUG_ENDPOINTS_IN_PROD", "").strip() not in ("1", "true", "True", "yes", "YES"):
        raise HTTPException(status_code=404, detail="Not Found")

    if _is_admin_enabled():
        return

    token = (os.getenv("RAAMP_ADMIN_TOKEN") or "").strip()
    header = (request.headers.get("x-raamp-admin-token") or "").strip()
    if token and header and header == token:
        return

    raise HTTPException(status_code=403, detail="Admin mode required")


def get_trends_service() -> GoogleTrendsService:
    """Dependency injection for GoogleTrendsService"""
    return GoogleTrendsService()


def get_analytics_service() -> TrendAnalyticsService:
    """Dependency injection for TrendAnalyticsService"""
    return TrendAnalyticsService()


def get_detection_service() -> TrendDetectionService:
    """Dependency injection for TrendDetectionService"""
    return TrendDetectionService()


@router.post(
    "/fetch",
    response_model=TrendFetchResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Fetch Google Trends data"
)
async def fetch_trends(
    request: TrendFetchRequest,
    background_tasks: BackgroundTasks,
    current_user_email: str = Depends(get_current_user_email),
    detection_service: TrendDetectionService = Depends(get_detection_service)
):
    """
    Fetch Googlel Trends data and run detection pipeline for the authenticated user.
    """
    # Get user model for internal settings
    user = await UserModel.find_one({"email": current_user_email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Pre-check: Trend scans require a configured location.
    # Location is locked from user.onboarding_location (preferred) or BusinessModel.country (fallback).
    try:
        from infrastructure.database.models.business_model import BusinessModel

        business = await BusinessModel.find_one({"user_id": current_user_email})
        has_location = bool(getattr(user, "onboarding_location", None)) or bool(getattr(business, "country", None))
        if not has_location:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Your business location is not set. Please complete your business profile before scanning trends."
                ),
            )
        # Pre-check: business specialties are mandatory for reliable trend detection.
        # We enforce this here (user-triggered scans) even though specialties can be edited later.
        specialties = list(getattr(business, "specialties", []) or []) if business else []
        specialties = [s for s in specialties if isinstance(s, str) and s.strip()]
        if len(specialties) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Business specialties are required to run a scan. Please go to Settings → Business Specialties and add at least one."
                ),
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Location pre-check failed (non-fatal). Proceeding to pipeline init. err=%s", str(e))

    # PART 1: Resolve niche parameter (handle ObjectID or plain string)
    from application.utils.trend_helpers import resolve_niche_name
    resolved_niche = await resolve_niche_name(request.niche)
    
    logger.info("🔍 TREND FETCH REQUEST - User: %s, Niche: %s → %s, Category: %s, Timeframe: %s", 
               current_user_email, request.niche, resolved_niche, request.category, request.timeframe or '30d')

    # Basic per-user cooldown (single instance). Defaults to 120 seconds.
    # UX improvement: if a scan is already running, return the in-flight trend_id instead of 429.
    try:
        import time
        from bson import ObjectId
        from infrastructure.database.models.trend_signal_model import TrendSignalModel

        cooldown_s = int(os.getenv("TREND_SCAN_COOLDOWN_SECONDS", "120") or "120")
        now = time.time()
        last = float(_LAST_SCAN_AT.get(current_user_email) or 0.0)
        if cooldown_s > 0 and (now - last) < cooldown_s:
            # If the user already has an in-flight scan, don't block the UI with 429.
            try:
                inflight = await TrendSignalModel.find_one(
                    {
                        "user_email": current_user_email,
                        "fetch_status": {"$in": ["pending", "processing"]},
                    }
                ).sort("-created_at")
                if inflight:
                    return TrendFetchResponse(
                        trend_id=str(inflight.id),
                        message="Scan already running. Returning current TrendID.",
                    )
            except Exception:
                pass

            retry_in = max(1, int(cooldown_s - (now - last)))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {retry_in} seconds before starting another scan.",
            )
        _LAST_SCAN_AT[current_user_email] = now
    except HTTPException:
        raise
    except Exception:
        # Never block scans due to cooldown bookkeeping bugs.
        pass

    # Process detection in background
    # Location is LOCKED from user.onboarding_location or BusinessModel.country
    try:
        trend_signal = await detection_service.initialize_detection_signal(
            user,
            resolved_niche,
            request.category
        )
    except ValueError as e:
        logger.warning("Location validation failed for user %s: %s", current_user_email, str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e
    except Exception as e:
        logger.error("Unexpected error initializing detection signal for user %s: %s", current_user_email, str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Trend analysis is temporarily unavailable. Please try again."
        ) from e
    
    # Persist user-defined custom keywords into the TrendSignal for this scan (reproducible scans).
    try:
        custom = list(getattr(request, "custom_keywords", None) or [])
        custom = [str(k).strip() for k in custom if str(k).strip()]
        if custom:
            existing = list(getattr(trend_signal, "keywords", None) or [])
            merged: list[str] = []
            seen = set()
            for k in (existing + custom):
                kk = (k or "").strip()
                if not kk:
                    continue
                lk = kk.lower()
                if lk in seen:
                    continue
                seen.add(lk)
                merged.append(kk)
            # trend_signal returned by service is a domain entity (no .save). Persist via DB model.
            try:
                from bson import ObjectId
                from infrastructure.database.models.trend_signal_model import TrendSignalModel

                model = await TrendSignalModel.get(ObjectId(str(trend_signal.id)))
                if model:
                    model.keywords = merged[:20]
                    await model.save()
                    logger.info("Persisted custom keywords for trend_id=%s: %s", trend_signal.id, custom[:20])
            except Exception as pe:
                logger.warning("Failed to persist custom keywords (non-fatal): %s", str(pe))
    except Exception as ke:
        logger.warning("Failed to persist custom keywords (non-fatal): %s", str(ke))

    # Optional discovery mode: seed keywords from SerpAPI trending-now and persist to this scan.
    # This makes scans reproducible (keywords are fixed per TrendSignal once created).
    if getattr(request, "discovery_mode", False):
        try:
            fetcher = TrendingNowFetcher()
            geo_code = detection_service.trends_service.convert_location_to_code(trend_signal.location)
            discovered = await fetcher.fetch_terms(
                geo=geo_code,
                category=request.category,
                limit=8,
                use_cache=True,
            )

            existing = list(getattr(trend_signal, "keywords", None) or [])
            merged: list[str] = []
            seen = set()
            for k in (discovered + existing):
                kk = (k or "").strip()
                if not kk:
                    continue
                lk = kk.lower()
                if lk in seen:
                    continue
                seen.add(lk)
                merged.append(kk)

            if merged:
                # Persist discovered keywords into TrendSignal for this scan.
                try:
                    from bson import ObjectId
                    from infrastructure.database.models.trend_signal_model import TrendSignalModel

                    model = await TrendSignalModel.get(ObjectId(str(trend_signal.id)))
                    if model:
                        model.keywords = merged[:20]
                        await model.save()
                    logger.info(
                        "Discovery mode seeded keywords for trend_id=%s geo=%s: %s",
                        trend_signal.id,
                        geo_code or "GLOBAL",
                        merged[:20],
                    )
                except Exception as se:
                    logger.warning("Failed to persist discovery keywords (non-fatal): %s", str(se))
            else:
                logger.info("Discovery mode returned 0 terms (non-fatal). Proceeding with existing keywords.")
        except Exception as de:
            logger.warning("Discovery mode failed (non-fatal). Proceeding without discovery. err=%s", str(de))

    logger.info("🚀 STEP 1: Initializing detection pipeline for user %s, niche %s", current_user_email, resolved_niche)
    background_tasks.add_task(
        detection_service.execute_detection_pipeline,
        trend_signal.id,
        request.timeframe or "30d"
    )
    
    logger.info("✅ STEP 2: Full detection pipeline triggered for user %s with trend_id %s", current_user_email, trend_signal.id)
    
    return TrendFetchResponse(
        trend_id=trend_signal.id,
        status="processing",
        message="Detection pipeline initiated. Signals will appear in the dashboard soon."
    )


@router.get(
    "/latest",
    response_model=TrendSignalListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get latest trend data"
)
async def get_latest_trends(
    limit: int = 10,
    current_user_email: str = Depends(get_current_user_email),
    trends_service: GoogleTrendsService = Depends(get_trends_service)
):
    """
    Get the latest trend data for the authenticated user.
    
    Returns a list of trend signals ordered by creation date (newest first).
    Only returns trends for the authenticated user.
    
    Args:
        limit: Maximum number of trends to return (default: 10, max: 50)
        current_user_email: Email of the authenticated user
        trends_service: Injected GoogleTrendsService instance
    
    Returns:
        TrendSignalListResponse containing list of trends and total count
    
    Raises:
        HTTPException: If fetching trends fails
    """
    try:
        # Validate limit
        if limit > 50:
            limit = 50
        if limit < 1:
            limit = 1
        
        logger.info("Fetching latest trends for user %s (limit=%d)", current_user_email, limit)
        
        # Get latest trends
        trends = await trends_service.get_latest_trends(current_user_email, limit)
        
        logger.info("Retrieved %d raw trends from database for user %s", len(trends), current_user_email)
        
        # Log niche information if trends exist
        if trends:
            niches = set(t.niche for t in trends if t.niche)
            niche_str = ', '.join(niches) if niches else 'N/A'
            logger.info("📊 User %s trends cover niches: %s", current_user_email, niche_str)
        
        # Convert to response models with ALL enhanced fields explicitly passed
        trend_responses: List[TrendSignalResponse] = []
        for trend in trends:
            ai_status = await _ai_analysis_status_for_trend(trend_id=str(trend.id), user_id=current_user_email)
            trend_responses.append(
                TrendSignalResponse(
                    id=trend.id,
                    user_email=trend.user_email,
                    niche=trend.niche,
                    category=trend.category,
                    location=trend.location,
                    radius=trend.radius,
                    keywords=trend.keywords,
                    search_interest=trend.search_interest,
                    geo_data=trend.geo_data,
                    related_queries=trend.related_queries,
                    rising_queries=trend.rising_queries,
                    provider=getattr(trend, "provider", None),
                    fallback_from=getattr(trend, "fallback_from", None),
                    geo_relaxed=bool(getattr(trend, "geo_relaxed", False)),
                    arbitrage_score=trend.arbitrage_score,
                    saturation_score=trend.saturation_score,
                    social_score=trend.social_score,
                    hashtags=trend.hashtags,
                    platform_bias=trend.platform_bias,
                    # ENHANCED FIELDS (explicit for production reliability)
                    lifecycle_stage=trend.lifecycle_stage,
                    predicted_growth_pct=trend.predicted_growth_pct,
                    breakout_probability=trend.breakout_probability,
                    profit_score=trend.profit_score,
                    forecast_series=trend.forecast_series,
                    timeframe=trend.timeframe,
                    ai_analysis_status=ai_status,
                    # Status fields
                    fetch_status=trend.fetch_status,
                    error_message=trend.error_message,
                    fetched_at=trend.fetched_at,
                    created_at=trend.created_at,
                    updated_at=trend.updated_at,
                )
            )
        
        logger.info("Returning %d enriched trend responses for user %s", len(trend_responses), current_user_email)
        
        # Debug log for first trend if available
        if trend_responses:
            first_trend = trend_responses[0]
            logger.info(
                "Sample trend data - ID: %s, Lifecycle: %s, Profit Score: %s, Status: %s", 
                first_trend.id, 
                first_trend.lifecycle_stage, 
                first_trend.profit_score,
                first_trend.fetch_status
            )
        else:
            logger.warning("No trends available for user %s", current_user_email)
        
        return TrendSignalListResponse(
            trends=trend_responses,
            total=len(trend_responses)
        )
        
    except Exception as e:
        logger.error("Error fetching latest trends for user %s: %s", current_user_email, str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to fetch trends at this time. Please try again."
        ) from e


# --- ANALYTICAL ENDPOINTS ---

@router.get("/industry_trends", summary="Get niche/industry trends (related/rising queries)", response_model=IndustryTrendsResponse)
async def get_industry_trends(
    niche: str,
    scope: str = "GLOBAL",
    timeframe: str = "7d",
    limit: int = 12,
    current_user_email: str = Depends(get_current_user_email),
):
    """
    Returns industry terms derived from Google Trends related/rising queries.

    This is different from /trends/trending_now:
    - trending_now: regional, newsy, "what's happening"
    - industry_trends: niche-specific, derived from related/rising queries for seed keywords
    """
    try:
        from infrastructure.database.models.business_model import BusinessModel

        business = await BusinessModel.find_one({"user_id": current_user_email})
        specialties = list(getattr(business, "specialties", []) or []) if business else []
        specialties = [str(s).strip() for s in specialties if str(s).strip()]

        svc = GoogleTrendsService()
        # Seed keywords: niche defaults + top specialties (cap)
        seed = svc._get_keywords_for_niche(niche, category="")  # type: ignore[attr-defined]
        for sp in specialties[:3]:
            if sp and sp.lower() not in [k.lower() for k in seed]:
                seed.append(sp)
        seed = seed[:6]

        # Scope geo: GLOBAL => "", else attempt to convert to ISO code.
        geo = ""
        scope_norm = (scope or "GLOBAL").strip()
        if scope_norm.upper() != "GLOBAL":
            try:
                geo = svc.convert_location_to_code(scope_norm)
            except Exception:
                geo = scope_norm.strip().upper()

        tf_map = {"24h": "now 1-d", "7d": "now 7-d", "30d": "today 1-m", "90d": "today 3-m"}
        tf = tf_map.get((timeframe or "7d").strip().lower(), "now 7-d")

        # Force pytrends for industry/related queries. SerpAPI is great for timelines, but
        # "industry trends" depends on related/rising queries which are most reliable via pytrends.
        try:
            import asyncio

            # Time-bound this call: pytrends can stall and we never want the UI to "hang".
            res = await asyncio.wait_for(
                svc._provider_selector.fetch_trends_data(  # type: ignore[attr-defined]
                    keywords=seed,
                    location=geo,
                    timeframe=tf,
                    provider_mode="pytrends",
                ),
                timeout=10.0,
            )
            data = {
                "provider": res.provider,
                "fallback_from": getattr(res, "fallback_from", None),
                "geo_relaxed": bool(getattr(res, "geo_relaxed", False)),
                "keywords": res.keywords,
                "search_interest": res.search_interest,
                "geo_data": res.geo_data,
                "related_queries": res.related_queries,
                "rising_queries": res.rising_queries,
                "success": res.success,
                "error": res.error,
                "retryable": res.retryable,
            }
        except Exception:
            # Fallback to service wrapper (may use cache/provider selector) but also time-bound it.
            import asyncio
            try:
                data = await asyncio.wait_for(
                    svc.fetch_trends_data(keywords=seed, location=geo, timeframe=tf, use_cache=True),
                    timeout=10.0,
                )
            except Exception as te:
                data = {"success": False, "provider": "timeout", "error": f"industry_trends_timeout:{type(te).__name__}"}

        if not (data or {}).get("success"):
            # Never return an empty UI surface: fall back to seed keywords so users can still
            # click-to-scan even when providers are down / rate-limited.
            seed_terms: list[str] = []
            seen_seed = set()
            for s in (seed or []):
                ss = str(s or "").strip()
                if not ss:
                    continue
                lk = ss.lower()
                if lk in seen_seed:
                    continue
                seen_seed.add(lk)
                seed_terms.append(ss)
            seed_terms = seed_terms[: max(1, min(int(limit or 12), 25))]
            return IndustryTrendsResponse(
                scope=(geo or "GLOBAL"),
                niche=niche,
                seed_keywords=seed,
                terms=seed_terms,
                count=len(seed_terms),
                data_quality=DataQuality(
                    is_real=False,
                    source=f"google_trends.related_queries:{(data or {}).get('provider') or 'unknown'}",
                    notes=(
                        ((data or {}).get("error") or "Industry trends provider unavailable.")
                        + " Showing seed keywords instead."
                    ),
                    flags={"timeframe": tf, "geo": geo or "", "provider": (data or {}).get("provider")},
                ),
            )

        # Extract terms from rising_queries/related_queries shapes (provider dependent)
        terms: list[str] = []
        seen = set()

        def add(t: str):
            tt = (t or "").strip()
            if not tt:
                return
            k = tt.lower()
            if k in seen:
                return
            seen.add(k)
            terms.append(tt)

        rq = (data or {}).get("rising_queries")
        rel = (data or {}).get("related_queries")

        # Common shapes:
        # - dict(keyword -> {"top":[...], "rising":[...]})
        # - dict with "rising"/"top" lists
        # - list of strings
        def extract(obj):
            if obj is None:
                return
            if isinstance(obj, list):
                for it in obj:
                    if isinstance(it, str):
                        add(it)
                return
            if isinstance(obj, dict):
                if "rising" in obj or "top" in obj:
                    for it in (obj.get("rising") or [])[:20]:
                        if isinstance(it, str):
                            add(it)
                        elif isinstance(it, dict) and isinstance(it.get("query"), str):
                            add(it["query"])
                    for it in (obj.get("top") or [])[:20]:
                        if isinstance(it, str):
                            add(it)
                        elif isinstance(it, dict) and isinstance(it.get("query"), str):
                            add(it["query"])
                    return
                # keyword keyed
                for _, v in obj.items():
                    extract(v)

        extract(rq)
        # If rising_queries empty, fall back to related queries
        if not terms:
            extract(rel)

        # If providers return no related/rising queries, fall back to seed keywords so the UI
        # never looks "broken" (and users can still click-to-scan).
        fallback_used = False
        if not terms:
            fallback_used = True
            for s in seed:
                add(str(s))

        terms = terms[: max(1, min(int(limit or 12), 25))]
        return IndustryTrendsResponse(
            scope=(geo or "GLOBAL"),
            niche=niche,
            seed_keywords=seed,
            terms=terms,
            count=len(terms),
            data_quality=DataQuality(
                is_real=bool(terms),
                source=f"google_trends.related_queries:{(data or {}).get('provider') or 'unknown'}",
                notes=(
                    "Provider returned no related/rising queries; showing seed keywords instead."
                    if fallback_used
                    else None
                ),
                flags={"timeframe": tf, "geo": geo or "", "provider": (data or {}).get("provider")},
            ),
        )
    except Exception as e:
        logger.warning("Industry trends endpoint failed (non-fatal): %s", str(e), exc_info=True)
        # Never return an empty UI surface: fall back to niche seed keywords.
        seed_terms: list[str] = []
        try:
            svc = GoogleTrendsService()
            seed = svc._get_keywords_for_niche(niche, category="")  # type: ignore[attr-defined]
            seen = set()
            for s in (seed or []):
                ss = str(s or "").strip()
                if not ss:
                    continue
                lk = ss.lower()
                if lk in seen:
                    continue
                seen.add(lk)
                seed_terms.append(ss)
            seed_terms = seed_terms[: max(1, min(int(limit or 12), 25))]
            return IndustryTrendsResponse(
                scope=(scope or "GLOBAL"),
                niche=niche,
                seed_keywords=seed,
                terms=seed_terms,
                count=len(seed_terms),
                data_quality=DataQuality(
                    is_real=False,
                    source="error",
                    notes="Failed to load industry trends. Showing seed keywords instead.",
                    flags={},
                ),
            )
        except Exception:
            pass
        return IndustryTrendsResponse(
            scope="GLOBAL",
            niche=niche,
            seed_keywords=[],
            terms=[],
            count=0,
            data_quality=DataQuality(is_real=False, source="error", notes="Failed to load industry trends.", flags={}),
        )


@router.get("/trending_now", summary="Get regional trending-now + business-relevant shortlist", response_model=TrendingNowResponse)
async def get_trending_now(
    location: str = None,
    category: str = "all",
    limit: int = 12,
    current_user_email: str = Depends(get_current_user_email),
):
    """
    Returns two lists:
    - `terms`: raw SerpAPI Trending Now terms for the geo
    - `relevant`: subset ranked by relevance to the user's business (niche + specialties)

    Notes:
    - This does not persist anything; it is a lightweight discovery endpoint for the UI.
    - If SerpAPI is not configured, returns empty lists (fail-closed).
    """
    try:
        from infrastructure.database.models.business_model import BusinessModel

        business = await BusinessModel.find_one({"user_id": current_user_email})
        specialties = list(getattr(business, "specialties", []) or []) if business else []
        specialties = [str(s).strip() for s in specialties if str(s).strip()]
        niche = str(getattr(business, "niche", "") or "").strip() if business else ""

        # Convert UI location to SerpAPI geo code best-effort.
        # We accept: ISO2 ("PK") or country name ("Pakistan").
        geo = ""
        if location and str(location).strip():
            try:
                geo = GoogleTrendsService().convert_location_to_code(str(location))
            except Exception:
                geo = str(location).strip().upper()

        fetcher = TrendingNowFetcher()
        terms = await fetcher.fetch_terms(
            geo=geo or "",
            category=category or "",
            limit=int(limit or 12),
            use_cache=True,
        )

        # --- business relevance scoring (simple + transparent) ---
        import re

        STOP = {
            "vs", "v", "and", "or", "the", "a", "an", "in", "of", "for", "to", "with",
            "on", "at", "by", "from", "today", "now", "live", "pakistan",
        }

        def tokenize(s: str) -> list[str]:
            raw = re.findall(r"[a-z0-9]+", (s or "").lower())
            toks = []
            for t in raw:
                if len(t) < 3:
                    continue
                if t in STOP:
                    continue
                toks.append(t)
            return toks

        business_tokens = set(tokenize(niche))
        for sp in specialties:
            business_tokens.update(tokenize(sp))

        relevant_items = []
        if business_tokens and terms:
            for term in terms:
                tt = tokenize(term)
                if not tt:
                    continue
                matches = sorted(set(tt).intersection(business_tokens))
                if not matches:
                    continue
                # score: overlap ratio with small boost for exact specialty phrase containment
                overlap = len(matches) / max(1, len(set(tt)))
                phrase_boost = 0.0
                term_l = (term or "").lower()
                for sp in specialties:
                    sp_l = (sp or "").strip().lower()
                    if sp_l and sp_l in term_l:
                        phrase_boost = max(phrase_boost, 0.25)
                score = round(min(1.0, overlap + phrase_boost), 4)
                relevant_items.append({"term": term, "score": score, "matched_terms": matches[:6]})

            relevant_items.sort(key=lambda x: float(x.get("score") or 0.0), reverse=True)
            relevant_items = relevant_items[: min(8, len(relevant_items))]

        return {
            "geo": geo or None,
            "terms": terms,
            "relevant": relevant_items,
            "count": len(terms),
            "data_quality": DataQuality(
                is_real=bool(terms),
                source="serpapi.trending_now",
                notes=None if terms else ("Trending Now unavailable (SerpAPI not configured or no terms returned)."),
                flags={"geo": geo or "", "category": category or "", "specialties_count": len(specialties)},
            ),
        }
    except Exception as e:
        logger.warning("Trending now endpoint failed (non-fatal): %s", str(e), exc_info=True)
        return {
            "geo": None,
            "terms": [],
            "relevant": [],
            "count": 0,
            "data_quality": DataQuality(
                is_real=False,
                source="error",
                notes="Failed to load trending-now feed.",
                flags={},
            ),
        }


@router.get("/live", summary="Get live trend feed for user", response_model=LiveTrendsResponse)
async def get_live_trends(
    location: str = None,
    limit: int = 20,
    scope: str = "business",
    current_user_email: str = Depends(get_current_user_email),
    analytics_service: TrendAnalyticsService = Depends(get_analytics_service)
):
    """Returns detected spikes for the user's live ticker/feed"""
    try:
        logger.info("📡 LIVE FEED REQUEST - User: %s, Location: %s, Limit: %s, Scope: %s", current_user_email, location, limit, scope)
        payload = await analytics_service.get_live_feed(current_user_email, location, limit, scope=scope)
        results = payload.get("trends", [])
        dq = payload.get("data_quality", {}) or {}
        logger.info("📡 LIVE FEED RESPONSE - Returned %d trends for %s", len(results), current_user_email)
        if results:
            sample_keyword = results[0].get('keyword', 'N/A') if isinstance(results[0], dict) else 'N/A'
            logger.info("📡 Sample trend: %s", sample_keyword)
        return {
            "trends": results,
            "count": len(results),
            "data_quality": DataQuality(**dq),
        }
    except Exception as e:
        logger.error("Error fetching live trends for user %s: %s", current_user_email, str(e), exc_info=True)
        # Return empty array instead of error for graceful degradation
        return {
            "trends": [],
            "count": 0,
            "data_quality": DataQuality(
                is_real=False,
                source="error",
                notes="Failed to load live trends.",
                flags={},
            ),
        }


@router.get("/heatmap", summary="Get trend geographic distribution", response_model=HeatmapResponse)
async def get_trend_heatmap(
    location: str = None,
    current_user_email: str = Depends(get_current_user_email),
    analytics_service: TrendAnalyticsService = Depends(get_analytics_service)
):
    """Returns trend intensity by region for heatmap visualization"""
    try:
        logger.info("🗺️ HEATMAP REQUEST - User: %s, Location: %s", current_user_email, location)
        results = await analytics_service.get_geo_heatmap(current_user_email, location)
        is_real_geo = bool(results)
        logger.info("🗺️ HEATMAP RESPONSE - Returned %d regions for %s", len(results), current_user_email)
        return {
            "regions": results,
            "count": len(results),
            "is_real_geo": is_real_geo,
            "data_quality": DataQuality(
                is_real=is_real_geo,
                source="trend_signals.geo_data" if is_real_geo else "empty_no_geo_data",
                notes=None if is_real_geo else "No geo distribution available yet. Run a scan that returns geo_data.",
                flags={},
            ),
        }
    except Exception as e:
        logger.error("Error fetching heatmap for user %s: %s", current_user_email, str(e), exc_info=True)
        return {
            "regions": [],
            "count": 0,
            "is_real_geo": False,
            "data_quality": DataQuality(is_real=False, source="error", notes="Failed to load heatmap.", flags={}),
        }


@router.get("/spike_timeline", summary="Get timeline of trend spikes", response_model=SpikeTimelineResponse)
async def get_spike_timeline(
    days: int = 30,
    location: str = None,
    current_user_email: str = Depends(get_current_user_email),
    analytics_service: TrendAnalyticsService = Depends(get_analytics_service)
):
    """Returns historical spike counts and scores for timeline chart"""
    try:
        logger.info("📈 SPIKE TIMELINE REQUEST - User: %s, Days: %d, Location: %s", current_user_email, days, location)
        results = await analytics_service.get_spike_timeline(current_user_email, days, location)
        last_scan = await analytics_service.get_last_successful_scan_at(current_user_email, location)
        last_iso = None
        if last_scan:
            last_iso = last_scan.isoformat() + "Z" if getattr(last_scan, "tzinfo", None) is None else last_scan.isoformat()
        logger.info("📈 SPIKE TIMELINE RESPONSE - Returned %d data points for %s", len(results), current_user_email)
        return {
            "timeline": results,
            "count": len(results),
            "last_successful_scan_at": last_iso,
            "data_quality": DataQuality(
                is_real=bool(results),
                source="trend_detections.timeline" if results else "empty_no_detections_in_window",
                notes=None if results else "No spikes detected in this time window yet.",
                flags={"days": days},
            ),
        }
    except Exception as e:
        logger.error("Error fetching spike timeline for user %s: %s", current_user_email, str(e), exc_info=True)
        return {
            "timeline": [],
            "count": 0,
            "last_successful_scan_at": None,
            "data_quality": DataQuality(is_real=False, source="error", notes="Failed to load spike timeline.", flags={}),
        }


@router.get("/bubble_chart", summary="Get market gap analytics", response_model=BubbleChartResponse)
async def get_bubble_chart(
    location: str = None,
    current_user_email: str = Depends(get_current_user_email),
    analytics_service: TrendAnalyticsService = Depends(get_analytics_service)
):
    """Returns growth, demand, and market gap data for bubble chart visualization"""
    try:
        logger.info("⚫ BUBBLE CHART REQUEST - User: %s, Location: %s", current_user_email, location)
        results = await analytics_service.get_market_gap_data(current_user_email, location)
        logger.info("⚫ BUBBLE CHART RESPONSE - Returned %d opportunities for %s", len(results), current_user_email)
        return {
            "opportunities": results,
            "count": len(results),
            "data_quality": DataQuality(
                is_real=bool(results),
                source="trend_detections.bubble_chart" if results else "empty_no_detections",
                notes=None if results else "Not enough real detections yet to populate the bubble chart.",
                flags={},
            ),
        }
    except Exception as e:
        logger.error("Error fetching bubble chart data for user %s: %s", current_user_email, str(e), exc_info=True)
        return {
            "opportunities": [],
            "count": 0,
            "data_quality": DataQuality(is_real=False, source="error", notes="Failed to load bubble chart.", flags={}),
        }


@router.get("/platform_reach", summary="Get platform-specific reach splits", response_model=PlatformReachResponse)
async def get_platform_reach(
    location: str = None,
    current_user_email: str = Depends(get_current_user_email),
    analytics_service: TrendAnalyticsService = Depends(get_analytics_service)
):
    """Returns TikTok, Instagram, and Google reach estimate for the user's trends"""
    try:
        logger.info("📱 PLATFORM REACH REQUEST - User: %s, Location: %s", current_user_email, location)
        results = await analytics_service.get_platform_reach(current_user_email, location)
        logger.info("📱 PLATFORM REACH RESPONSE - Google: %d, Instagram: %d, Facebook: %d", 
                   results.get('google', 0), results.get('instagram', 0), results.get('facebook', 0))
        return {
            **results,
            "data_quality": DataQuality(
                is_real=bool(results.get("is_real", False)),
                source=str(results.get("source") or "unknown"),
                notes=None if results.get("is_real", False) else "Platform reach is only available when real social metrics exist.",
                flags={},
            ),
        }
    except Exception as e:
        logger.error("Error fetching platform reach for user %s: %s", current_user_email, str(e), exc_info=True)
        return {
            "google": 0,
            "instagram": 0,
            "facebook": 0,
            "total_reach": "0%",
            "is_real": False,
            "source": "error",
            "data_quality": DataQuality(is_real=False, source="error", notes="Failed to load platform reach.", flags={}),
        }


@router.get(
    "/{trend_id}",
    response_model=TrendSignalResponse,
    status_code=status.HTTP_200_OK,
    summary="Get trend data by ID"
)
async def get_trend_by_id(
    trend_id: str,
    current_user_email: str = Depends(get_current_user_email),
    trends_service: GoogleTrendsService = Depends(get_trends_service)
):
    """
    Get a specific trend signal by its ID.
    
    Returns detailed trend data including search interest, geographic data,
    and related/rising queries.
    """
    try:
        # Get trend signal
        trend = await trends_service.get_trend_by_id(trend_id)
        
        if not trend:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trend signal with ID {trend_id} not found"
            )
        
        # Verify user has access to this trend
        if trend.user_email != current_user_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this trend signal"
            )
        
        return TrendSignalResponse(
            id=trend.id,
            user_email=trend.user_email,
            niche=trend.niche,
            category=trend.category,
            location=trend.location,
            radius=trend.radius,
            keywords=trend.keywords,
            search_interest=trend.search_interest,
            geo_data=trend.geo_data,
            related_queries=trend.related_queries,
            rising_queries=trend.rising_queries,
            arbitrage_score=trend.arbitrage_score,
            saturation_score=trend.saturation_score,
            social_score=trend.social_score,
            hashtags=trend.hashtags,
            platform_bias=trend.platform_bias,
            # ENHANCED FIELDS (explicit for production reliability)
            lifecycle_stage=trend.lifecycle_stage,
            predicted_growth_pct=trend.predicted_growth_pct,
            breakout_probability=trend.breakout_probability,
            profit_score=trend.profit_score,
            forecast_series=trend.forecast_series,
            timeframe=trend.timeframe,
            # Status fields
            fetch_status=trend.fetch_status,
            error_message=trend.error_message,
            fetched_at=trend.fetched_at,
            created_at=trend.created_at,
            updated_at=trend.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching trend %s for user %s: %s", trend_id, current_user_email, str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to fetch trend details. Please try again."
        ) from e


@router.get(
    "/{trend_id}/status",
    response_model=TrendStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get trend fetch status"
)
async def get_trend_status(
    trend_id: str,
    current_user_email: str = Depends(get_current_user_email),
    trends_service: GoogleTrendsService = Depends(get_trends_service)
):
    """
    Get the current status of a trend fetch operation.
    """
    try:
        # Get trend signal
        trend = await trends_service.get_trend_by_id(trend_id)
        
        if not trend:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trend signal with ID {trend_id} not found"
            )
        
        # Verify user has access to this trend
        if trend.user_email != current_user_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this trend signal"
            )
        
        return TrendStatusResponse(
            trend_id=trend.id,
            status=trend.fetch_status,
            error_message=trend.error_message,
            ai_analysis_status=await _ai_analysis_status_for_trend(trend_id=str(trend.id), user_id=current_user_email),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching trend status %s for user %s: %s", trend_id, current_user_email, str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to check trend status. Please try again."
        ) from e


# --- NEW ENHANCEMENT ENDPOINTS ---

@router.get(
    "/{trend_id}/ai-analysis",
    summary="Get stored AI analysis for a trend",
    status_code=status.HTTP_200_OK,
)
async def get_ai_analysis(
    trend_id: str,
    current_user_email: str = Depends(get_current_user_email),
):
    doc = await TrendAIAnalysisService().get_analysis(trend_id, current_user_email)
    if not doc:
        raise HTTPException(status_code=404, detail="AI analysis not found")
    return doc


@router.post(
    "/{trend_id}/ai-analysis/regenerate",
    summary="Regenerate AI analysis for a trend",
    status_code=status.HTTP_202_ACCEPTED,
)
async def regenerate_ai_analysis(
    trend_id: str,
    background_tasks: BackgroundTasks,
    current_user_email: str = Depends(get_current_user_email),
):
    # Non-blocking regeneration
    background_tasks.add_task(TrendAIAnalysisService().regenerate_analysis, trend_id, current_user_email)
    return {"success": True, "status": "pending"}


@router.post(
    "/{trend_id}/execute/draft-caption",
    summary="Stream a draft caption for this trend (no persistence)",
)
async def execute_draft_caption(
    trend_id: str,
    body: Dict[str, Any],
    current_user_email: str = Depends(get_current_user_email),
):
    tone_override = str((body or {}).get("tone_override") or "").strip() or None
    analysis = await TrendAIAnalysisService().get_analysis(trend_id, current_user_email)
    if not analysis:
        raise HTTPException(status_code=404, detail="AI analysis not found. Wait for analysis or regenerate.")

    brand = analysis.brand_voice_used or {}
    kw = analysis.trend_keyword

    system_prompt = "You are an elite social media copywriter. Return plain text only."
    user_prompt = (
        f"Write one high-performing social caption for trend '{kw}'.\n"
        f"Brand context: {brand}\n"
        f"Tone override: {tone_override or 'use brand default'}\n"
        "Constraints: 2-4 lines, strong hook, clear CTA, add 5-8 hashtags.\n"
        "Return plain text only."
    )
    return StreamingResponse(_stream_openai_chat(system_prompt=system_prompt, user_prompt=user_prompt), media_type="text/plain")


@router.post(
    "/{trend_id}/execute/generate-hooks",
    summary="Stream 3 opening hook lines for this trend (no persistence)",
)
async def execute_generate_hooks(
    trend_id: str,
    body: Dict[str, Any],
    current_user_email: str = Depends(get_current_user_email),
):
    tone_override = str((body or {}).get("tone_override") or "").strip() or None
    analysis = await TrendAIAnalysisService().get_analysis(trend_id, current_user_email)
    if not analysis:
        raise HTTPException(status_code=404, detail="AI analysis not found. Wait for analysis or regenerate.")

    brand = analysis.brand_voice_used or {}
    kw = analysis.trend_keyword
    system_prompt = "You are a viral hook writer. Return plain text only."
    user_prompt = (
        f"Generate 3 hook lines for trend '{kw}'.\n"
        f"Brand context: {brand}\n"
        f"Tone override: {tone_override or 'use brand default'}\n"
        "Return as 3 lines only, no numbering."
    )
    return StreamingResponse(_stream_openai_chat(system_prompt=system_prompt, user_prompt=user_prompt), media_type="text/plain")


@router.post(
    "/{trend_id}/execute/blog-outline",
    summary="Stream a blog outline for this trend (no persistence)",
)
async def execute_blog_outline(
    trend_id: str,
    body: Dict[str, Any],
    current_user_email: str = Depends(get_current_user_email),
):
    tone_override = str((body or {}).get("tone_override") or "").strip() or None
    analysis = await TrendAIAnalysisService().get_analysis(trend_id, current_user_email)
    if not analysis:
        raise HTTPException(status_code=404, detail="AI analysis not found. Wait for analysis or regenerate.")

    brand = analysis.brand_voice_used or {}
    kw = analysis.trend_keyword
    system_prompt = "You are a content strategist. Return plain text only."
    user_prompt = (
        f"Create a concise blog outline for '{kw}'.\n"
        f"Brand context: {brand}\n"
        f"Tone override: {tone_override or 'use brand default'}\n"
        "Return: Title, 5-7 headings with 1 bullet each, and a CTA section."
    )
    return StreamingResponse(_stream_openai_chat(system_prompt=system_prompt, user_prompt=user_prompt), media_type="text/plain")


@router.post(
    "/{trend_id}/execute/ad-copy",
    summary="Stream ad copy variants for this trend (no persistence)",
)
async def execute_ad_copy(
    trend_id: str,
    body: Dict[str, Any],
    current_user_email: str = Depends(get_current_user_email),
):
    tone_override = str((body or {}).get("tone_override") or "").strip() or None
    analysis = await TrendAIAnalysisService().get_analysis(trend_id, current_user_email)
    if not analysis:
        raise HTTPException(status_code=404, detail="AI analysis not found. Wait for analysis or regenerate.")

    brand = analysis.brand_voice_used or {}
    kw = analysis.trend_keyword
    system_prompt = "You are a performance ad copywriter. Return plain text only."
    user_prompt = (
        f"Write ad copy for trend '{kw}'.\n"
        f"Brand context: {brand}\n"
        f"Tone override: {tone_override or 'use brand default'}\n"
        "Return 3 variants: Primary text (max 120 chars), Headline (max 40), CTA."
    )
    return StreamingResponse(_stream_openai_chat(system_prompt=system_prompt, user_prompt=user_prompt), media_type="text/plain")


@router.get(
    "/viral-audio",
    summary="Get trending audio candidates (charting feed)",
)
async def get_viral_audio(
    platform: str = "instagram",
    geo: str = "PK",
    niche: str = "general",
    current_user_email: str = Depends(get_current_user_email),
):
    namespace = "viral_audio"
    key = f"v1:{platform.lower()}:{geo.upper()}:{niche.lower()}"
    cached = await _cached_get(namespace, key)
    if cached is not None:
        return {"source": "apple_music_rss", "label": "Trending Audio (charting)", "tracks": cached}

    tracks = await ViralAudioProvider().get_tracks(
        platform=platform,
        location=geo,
        niche=niche,
        trend_keyword=niche,
        limit=2,
    )
    await _cached_set(namespace, key, tracks, ttl_seconds=6 * 60 * 60)
    return {
        "source": "spotify_or_apple", 
        "label": "Trending Audio (charting)", 
        "recommended_tracks": tracks,
        "tracks": tracks # Backwards compatibility
    }


@router.get(
    "/influencer-radar",
    summary="Get competitor benchmarking data (Instagram real-time)",
)
async def competitor_radar(
    geo: str = "PK",
    niche: str = "general",
    keyword: Optional[str] = None,
    current_user_email: str = Depends(get_current_user_email),
):
    """
    Competitor Benchmarking: Identifies local players already using the trend.
    Analyzes recent Instagram activity for the given keyword/niche and 
    extracts handles, engagement heat, and proof-of-trend URLs.
    """
    namespace = "competitor_radar"
    search_term = (keyword or niche).replace("#", "").replace(" ", "")
    key = f"v3:{geo.upper()}:{search_term.lower()}"

    cached = await _cached_get(namespace, key)
    if cached is not None:
        return {"source": "serpapi_benchmarking", "influencers": cached}

    # Use config for consistency
    from config import config
    serp_key = config.SERPAPI_API_KEY
    competitors: List[Dict[str, Any]] = []

    if serp_key:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(
                    "https://serpapi.com/search",
                    params={
                        "engine": "google",
                        "q": f"site:instagram.com \"#{search_term}\" or \"{search_term}\" niche",
                        "api_key": serp_key,
                        "num": 10,
                        "gl": geo.lower(),
                    },
                )
                results = r.json().get("organic_results") or []
                seen = set()

                for item in results:
                    link = str(item.get("link") or "")
                    snippet = str(item.get("snippet") or "")

                    # Extract Instagram handle from URL
                    match = re.search(r"instagram\.com/([^/?#]+)", link)
                    if not match:
                        continue
                    handle = match.group(1).strip("/")
                    if not handle or handle in ("p", "reel", "explore", "tv", "stories"):
                        continue
                    if handle.lower() in seen:
                        continue
                    seen.add(handle.lower())

                    competitors.append({
                        "handle": handle,
                        "follower_count_formatted": "Recently active",
                        "engagement_rate": 85,
                        "niche_tags": [niche],
                        "url": link,
                        "snippet": snippet[:120],
                        "last_post_type": "IMAGE",
                    })

                    if len(competitors) >= 4:
                        break

        except Exception as e:
            logger.warning("SerpAPI competitor radar failed for %s: %s", search_term, str(e))
            competitors = []

    await _cached_set(namespace, key, competitors, ttl_seconds=12 * 60 * 60)
    return {"source": "serpapi_benchmarking", "influencers": competitors}

@router.post(
    "/suggest",
    response_model=ContentSuggestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate AI content suggestions"
)
async def generate_content_suggestions(
    request: ContentSuggestionRequest,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Generate AI-powered content and campaign suggestions for a trending keyword.
    Returns video ideas, hooks, hashtags, campaign angles, and influencer strategies.
    """
    from application.services.trend_content_suggestion_service import TrendContentSuggestionService
    from infrastructure.database.models.trend_detection_model import TrendDetectionModel
    from infrastructure.database.models.trend_signal_model import TrendSignalModel
    
    try:
        suggestion_service = TrendContentSuggestionService()
        
        # Find the most recent trend detection for this keyword
        detection = await TrendDetectionModel.find_one({
            "user_id": current_user_email,
            "keyword": {"$regex": f"^{request.keyword}$", "$options": "i"}
        }).sort("-detected_at")
        
        if not detection:
            # Try to find in TrendSignal
            signal = await TrendSignalModel.find_one({
                "user_email": current_user_email
            }).sort("-created_at")
            
            if not signal:
                raise HTTPException(
                    status_code=404,
                    detail="No trend data found for this keyword. Please run a trend scan first."
                )
            
            # Use signal data
            niche = signal.niche
            lifecycle_stage = signal.lifecycle_stage or "Mainstream"
            profit_score = signal.profit_score or 50.0
            social_score = signal.social_score or 50.0
            saturation_score = signal.saturation_score or 50.0
            platform_bias = signal.platform_bias or {}
        else:
            # Use detection record + matching TrendSignal metrics or derived scores
            niche = detection.niche
            lifecycle_stage = detection.lifecycle_stage or "Mainstream"
            profit_score, social_score, saturation_score, platform_bias = (
                await resolve_suggestion_metrics_from_detection(
                    current_user_email, request.keyword, detection
                )
            )

        # Generate suggestions (fail-closed: no templated fallback suggestions).
        try:
            logger.info("🤖 AI STEP: Generating content suggestions for keyword '%s'", request.keyword)
            suggestions = await suggestion_service.generate_content_suggestions(
                keyword=request.keyword,
                niche=niche,
                lifecycle_stage=lifecycle_stage,
                profit_score=profit_score,
                social_score=social_score,
                saturation_score=saturation_score,
                platform_bias=platform_bias,
            )
            logger.info("✅ AI STEP: Suggestions generated successfully for '%s'", request.keyword)
        except Exception as ai_err:
            logger.warning("⚠️ AI STEP FAILED: Content suggestions failed for '%s'. Using local fallback. err=%s", request.keyword, str(ai_err))
            # FALLBACK: Use local rule-based suggestions to avoid blocking the user
            suggestions = suggestion_service._generate_fallback_suggestions(request.keyword, niche)
        
        return ContentSuggestionResponse(
            keyword=request.keyword,
            video_ideas=suggestions["video_ideas"],
            hooks=suggestions["hooks"],
            hashtags=suggestions["hashtags"],
            campaign_angle=suggestions["campaign_angle"],
            influencer_strategy=suggestions["influencer_strategy"],
            lifecycle_stage=lifecycle_stage,
            profit_score=profit_score
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error generating content suggestions for user %s, keyword %s: %s", current_user_email, request.keyword, str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate content suggestions at this time. Please try again."
        ) from e


@router.post(
    "/explain",
    response_model=TrendExplainResponse,
    status_code=status.HTTP_200_OK,
    summary="Get plain-English AI explanation of a trend"
)
async def explain_trend(
    request: TrendExplainRequest,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Returns a plain-English AI explanation of why a trend is relevant to the user's business,
    a "why act now" sentence, and a ready-to-use campaign prompt for CreativeStudio.
    """
    from infrastructure.clients.llm_client import LLMClient

    system_prompt = (
        "You are a careful trend interpreter for small business owners.\n"
        "You MUST be honest and avoid guessing.\n"
        "- If the keyword is ambiguous (e.g. 'rr vs mi'), identify the most likely real-world meaning "
        "  and say it plainly.\n"
        "- If it looks like a sports matchup, treat it as sports context (not fashion/brands).\n"
        "- If you are not confident, say so and suggest 1-2 clarifying angles the user can scan next.\n"
        "Explain in simple, plain English — no jargon.\n"
        "Return ONLY valid JSON with exactly these keys: \"explanation\", \"why_now\", \"content_prompt\"."
    )

    metrics_parts = []
    if request.lifecycle_stage:
        metrics_parts.append(f"Stage: {request.lifecycle_stage}")
    if request.breakout_probability is not None:
        metrics_parts.append(f"Viral potential: {request.breakout_probability:.0f}%")
    if request.profit_score is not None:
        metrics_parts.append(f"Opportunity score: {request.profit_score:.0f}/100")
    if request.competition is not None:
        metrics_parts.append(f"Competition: {request.competition:.0f}%")
    if request.buzz is not None:
        metrics_parts.append(f"Buzz: {request.buzz:.0f}")
    metrics_text = ", ".join(metrics_parts) if metrics_parts else "no additional metrics"

    keyword = (request.keyword or "").strip()
    niche = (request.niche or "").strip()
    location = (request.location or "").strip()
    from application.utils.trend_keyword_context import resolve_matchup, classify_keyword

    matchup = resolve_matchup(keyword)
    looks_like_matchup = matchup.looks_like_matchup
    matchup_hint = matchup.matchup_hint
    entities = matchup.entities
    category, category_confidence = classify_keyword(keyword)

    user_prompt = (
        f"Trend keyword: \"{keyword}\"\n"
        f"Business niche: {niche}\n"
        f"Location: {location}\n"
        f"Metrics: {metrics_text}\n"
        f"Hint: looks_like_matchup={looks_like_matchup}\n\n"
        f"Hint: matchup_resolver={matchup_hint or 'unknown'}\n\n"
        "Write three things:\n"
        "1) \"explanation\": 2-4 sentences. First sentence: what this trend likely refers to.\n"
        "   - If this is a matchup keyword, interpret it as a sports matchup unless you have strong evidence otherwise.\n"
        "   - Do NOT invent fake fashion brands.\n"
        "   - If matchup_resolver is provided, you MUST use it.\n"
        "2) \"why_now\": 1 sentence. Tie to timing (match day / highlights / memes / fan activity) or say 'act when match chatter spikes'.\n"
        "3) \"content_prompt\": 1-2 sentences that explicitly mention the keyword AND connect it to the business niche/location (even if the trend is sports).\n"
        "Return ONLY JSON with keys: explanation, why_now, content_prompt."
    )

    try:
        llm = LLMClient()
        result = await llm.generate_structured_json(system_prompt, user_prompt)

        if not result or not isinstance(result, dict):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AI could not generate explanation. Please try again."
            )

        return TrendExplainResponse(
            keyword=request.keyword,
            explanation=result.get("explanation", ""),
            why_now=result.get("why_now", ""),
            content_prompt=result.get("content_prompt", ""),
            category=category,
            category_confidence=category_confidence,
            entities=entities,
            matchup_hint=matchup_hint or None,
            data_quality={
                "is_real": False,
                "source": "llm.explain_trend",
                "notes": None,
                "flags": {
                    "looks_like_matchup": looks_like_matchup,
                    "matchup_hint_provided": bool(matchup_hint),
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error explaining trend for user %s, keyword %s: %s", current_user_email, request.keyword, str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate trend explanation at this time. Please try again."
        ) from e


@router.get(
    "/forecast/{keyword}",
    response_model=ForecastResponse,
    status_code=status.HTTP_200_OK,
    summary="Get trend forecast"
)
async def get_trend_forecast(
    keyword: str,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Get 7-day forecast for a specific trending keyword.
    Returns historical series, forecast series, and breakout probability.
    """
    from infrastructure.database.models.trend_detection_model import TrendDetectionModel
    from infrastructure.database.models.trend_signal_model import TrendSignalModel
    
    try:
        # Find trend detection for this keyword
        detection = await TrendDetectionModel.find_one({
            "user_id": current_user_email,
            "keyword": {"$regex": f"^{keyword}$", "$options": "i"}
        }).sort("-detected_at")
        
        if detection:
            # Get historical data from TrendSignal
            signal = await TrendSignalModel.find_one({
                "user_email": current_user_email
            }).sort("-created_at")
            
            if signal and signal.search_interest:
                historical_values = signal.search_interest.get("data", {}).get(keyword, [])
            else:
                historical_values = []
            
            return ForecastResponse(
                keyword=keyword,
                historical_series=historical_values if historical_values else [detection.current_value],
                forecast_series=detection.forecast_series or [],
                predicted_growth_pct=detection.predicted_growth_pct or 0.0,
                breakout_probability=detection.breakout_probability or 0.0,
                lifecycle_stage=detection.lifecycle_stage,
                current_value=detection.current_value,
                z_score=detection.z_score
            )
        else:
            raise HTTPException(
                status_code=404,
                detail=f"No trend data found for keyword '{keyword}'. Please run a trend scan first."
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching forecast for keyword %s, user %s: %s", keyword, current_user_email, str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate trend forecast. Please try again."
        ) from e


@router.get(
    "/cache/status",
    summary="Get cache status",
    status_code=status.HTTP_200_OK
)
async def get_cache_status(
    current_user_email: str = Depends(get_current_user_email)
):
    """Get trends cache status (MongoDB-backed TTL cache)."""
    from datetime import datetime
    from infrastructure.database.models.trend_cache_model import TrendCacheModel

    now = datetime.utcnow()
    total_entries = await TrendCacheModel.find(TrendCacheModel.expires_at > now).count()

    # Return a small sample for diagnostics
    sample = (
        await TrendCacheModel.find(TrendCacheModel.expires_at > now)
        .sort("-created_at")
        .limit(10)
        .to_list()
    )

    entries = []
    for d in sample:
        try:
            age_minutes = (now - d.created_at).total_seconds() / 60
            ttl_minutes = max(0.0, (d.expires_at - now).total_seconds() / 60)
            entries.append({
                "namespace": d.namespace,
                "key": (d.key[:16] + "...") if isinstance(d.key, str) and len(d.key) > 16 else d.key,
                "age_minutes": round(age_minutes, 1),
                "ttl_remaining_minutes": round(ttl_minutes, 1),
                "expires_at": d.expires_at.isoformat() + "Z",
            })
        except Exception:
            continue

    return {"total_entries": total_entries, "entries": entries}


@router.post(
    "/cache/clear",
    summary="Clear Google Trends cache",
    status_code=status.HTTP_200_OK
)
async def clear_cache(
    request: Request,
    current_user_email: str = Depends(get_current_user_email)
):
    """Clear all trends cache entries (admin/dev only)."""
    _require_admin(request)
    from infrastructure.database.models.trend_cache_model import TrendCacheModel

    # NOTE: This is destructive. Keep endpoint restricted in production.
    count = await TrendCacheModel.find_all().count()
    await TrendCacheModel.find_all().delete()

    logger.info("Trends cache cleared by %s: %d entries removed", current_user_email, count)
    return {"success": True, "message": f"Cleared {count} cache entries", "cleared_count": count}


@router.get(
    "/debug/database-status",
    summary="Debug endpoint - Check database trends",
    status_code=status.HTTP_200_OK
)
async def debug_database_status(
    request: Request,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Debug endpoint to verify what's actually in the database.
    Returns raw database record counts and sample data.
    """
    _require_admin(request)
    try:
        from infrastructure.database.models.trend_signal_model import TrendSignalModel
        from infrastructure.database.models.trend_detection_model import TrendDetectionModel
        
        # Count total trends for this user
        total_trends = await TrendSignalModel.find(
            TrendSignalModel.user_email == current_user_email
        ).count()
        
        # Count completed trends
        completed_trends = await TrendSignalModel.find(
            TrendSignalModel.user_email == current_user_email,
            TrendSignalModel.fetch_status == "completed"
        ).count()
        
        # Count processing trends
        processing_trends = await TrendSignalModel.find(
            TrendSignalModel.user_email == current_user_email,
            TrendSignalModel.fetch_status == "processing"
        ).count()
        
        # Count failed trends
        failed_trends = await TrendSignalModel.find(
            TrendSignalModel.user_email == current_user_email,
            TrendSignalModel.fetch_status == "failed"
        ).count()
        
        # Get latest trend for inspection
        latest_trend = await TrendSignalModel.find(
            TrendSignalModel.user_email == current_user_email
        ).sort(-TrendSignalModel.created_at).first_or_none()
        
        # Count total detections
        total_detections = await TrendDetectionModel.find(
            TrendDetectionModel.user_id == current_user_email
        ).count()
        
        sample_data = None
        if latest_trend:
            sample_data = {
                "id": str(latest_trend.id),
                "niche": latest_trend.niche,
                "category": latest_trend.category,
                "location": latest_trend.location,
                "keywords": latest_trend.keywords[:3] if latest_trend.keywords else [],
                "fetch_status": latest_trend.fetch_status,
                "has_search_interest": bool(latest_trend.search_interest),
                "has_geo_data": bool(latest_trend.geo_data),
                "arbitrage_score": latest_trend.arbitrage_score,
                "saturation_score": latest_trend.saturation_score,
                "social_score": latest_trend.social_score,
                "lifecycle_stage": latest_trend.lifecycle_stage,
                "predicted_growth_pct": latest_trend.predicted_growth_pct,
                "breakout_probability": latest_trend.breakout_probability,
                "profit_score": latest_trend.profit_score,
                "timeframe": latest_trend.timeframe,
                "created_at": latest_trend.created_at.isoformat() if latest_trend.created_at else None,
                "fetched_at": latest_trend.fetched_at.isoformat() if latest_trend.fetched_at else None,
                "error_message": latest_trend.error_message
            }
        
        return {
            "user_email": current_user_email,
            "database_status": {
                "total_trends": total_trends,
                "completed_trends": completed_trends,
                "processing_trends": processing_trends,
                "failed_trends": failed_trends,
                "total_detections": total_detections
            },
            "latest_trend_sample": sample_data,
            "diagnosis": {
                "has_any_data": total_trends > 0,
                "has_completed_data": completed_trends > 0,
                "possible_issue": (
                    "No trends found - user needs to fetch trends first" if total_trends == 0
                    else "Trends are still processing" if processing_trends > 0 and completed_trends == 0
                    else "Trends failed - check error_message" if failed_trends > 0 and completed_trends == 0
                    else "Data available - check frontend API calls"
                )
            }
        }
        
    except Exception as e:
        logger.error("Error in debug endpoint for user %s: %s", current_user_email, str(e), exc_info=True)
        return {
            "error": "Failed to fetch debug information",
            "details": str(e)
        }


@router.get("/instagram/health", summary="Check Instagram token health", status_code=status.HTTP_200_OK)
async def instagram_health(
    current_user_email: str = Depends(get_current_user_email),
):
    """
    Lightweight health check to distinguish:
    - not connected
    - connected but token invalid/unreachable
    - reachable (token valid)
    """
    from application.services.onboarding_service import OnboardingService
    from application.services.instagram_graph_api_service import InstagramGraphAPIClient

    onboarding = OnboardingService()
    conn = await onboarding.get_instagram_connection(current_user_email)
    if not conn:
        return {"connected": False, "token_valid": False, "reason": "not_connected"}

    client = InstagramGraphAPIClient()
    ok = await client.validate_token_reachability(current_user_email)
    return {
        "connected": True,
        "token_valid": bool(ok),
        "reason": "ok" if ok else "token_unreachable",
    }


# --- TREND ACTIVITY & AUDIT ---

@router.post("/activity/log", summary="Log trend execution activity", status_code=status.HTTP_201_CREATED)
async def log_trend_activity(
    trend_keyword: str,
    trend_source: str,
    generated_prompt: str,
    niche: str,
    location: str,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Log an EXECUTE event for a trend.
    Stores the generated prompt and trend metadata for audit.
    """
    from infrastructure.database.models.trend_activity_model import TrendActivityModel
    try:
        activity = TrendActivityModel(
            user_email=current_user_email,
            trend_keyword=trend_keyword,
            trend_source=trend_source,
            generated_prompt=generated_prompt,
            niche=niche,
            location=location
        )
        await activity.insert()
        return {"success": True, "activity_id": str(activity.id)}
    except Exception as e:
        logger.error(f"Failed to log trend activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to log trend execution."
        )


@router.get("/activity/history", summary="Get trend execution history", response_model=List[dict])
async def get_trend_history(
    limit: int = 50,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Returns the history of all trend executions and their generated prompts.
    """
    from infrastructure.database.models.trend_activity_model import TrendActivityModel
    try:
        activities = await TrendActivityModel.find(
            TrendActivityModel.user_email == current_user_email
        ).sort("-timestamp").limit(limit).to_list()
        
        # Format for frontend
        return [
            {
                "id": str(a.id),
                "trend_keyword": a.trend_keyword,
                "trend_source": a.trend_source,
                "generated_prompt": a.generated_prompt,
                "niche": a.niche,
                "location": a.location,
                "timestamp": a.timestamp.isoformat()
            }
            for a in activities
        ]
    except Exception as e:
        logger.error(f"Error fetching trend history: {e}")
        return []
