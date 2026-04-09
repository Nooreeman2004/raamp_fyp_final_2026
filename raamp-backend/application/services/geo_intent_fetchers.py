# Application Layer - Geo-Intent Data Fetchers
# Three independent async signal fetchers: Google Trends, Google Places, Tomorrow.io Weather.
# Each fetcher:
#   - is fully async (httpx + asyncio)
#   - is timeout-protected
#   - logs via the module logger
#   - returns a normalised float (0.0–1.0)
#   - NEVER raises — returns 0.5 (neutral) on any failure so the engine always responds.
import asyncio
import logging
from functools import partial
from typing import List, Tuple

import httpx

from application.services.geo_intent_cache import geo_intent_cache, GeoIntentTTLCache
from config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_NEUTRAL_SCORE: float = 0.5          # returned when a fetcher fails
_HTTP_TIMEOUT: float = 8.0           # seconds per external request


# ---------------------------------------------------------------------------
# Helper: safely clamp + normalise a raw value to [0, 1]
# ---------------------------------------------------------------------------

def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


# ===========================================================================
# 1. Google Trends Fetcher
# ===========================================================================

async def fetch_trends_score(
    keywords: List[str],
    geo: str,
    latitude: float,
    longitude: float,
    radius: int,
) -> Tuple[float, str]:
    """
    Return a normalised (0–1) Google Trends keyword-velocity score.

    Uses the existing GoogleTrendsService so we reuse its retry / rate-limit
    logic. Runs the blocking PyTrends call in a thread pool.

    Falls back to 0.5 on any error.
    """
    cache_key = geo_intent_cache.build_key(latitude, longitude, keywords, radius) + ":trends"
    cached = geo_intent_cache.get(cache_key)
    if cached is not None:
        logger.debug("Trends cache hit for %s", cache_key)
        return cached, "ok"

    try:
        # Import here to avoid circular imports at module level
        from application.services.google_trends_service import GoogleTrendsService

        svc = GoogleTrendsService()
        # Convert geo code from env or derive from lat/lng context
        location_code = settings.GOOGLE_TRENDS_GEO or "PK"

        result = await svc.fetch_trends_data(
            keywords=keywords[:5],
            location=location_code,
            timeframe="now 7-d",
            use_cache=True,
        )

        if not result.get("success"):
            logger.warning(
                "Trends fetch unsuccessful for keywords=%s: %s",
                keywords,
                result.get("error"),
            )
            return _NEUTRAL_SCORE, "failed"

        # Extract average interest from the time series
        search_interest = result.get("search_interest", {})
        data_dict = search_interest.get("data", {})

        values: List[float] = []
        for kw_data in data_dict.values():
            if isinstance(kw_data, list):
                values.extend(float(v) for v in kw_data if v is not None)

        if not values:
            logger.info("Trends returned no data points — using neutral score")
            return _NEUTRAL_SCORE, "failed"

        raw_avg = sum(values) / len(values)          # Google Trends: 0–100
        normalised = _clamp01(raw_avg / 100.0)

        geo_intent_cache.set(cache_key, normalised, GeoIntentTTLCache.TRENDS_TTL)
        logger.info(
            "✅ [DEBUG] Trends search successful. keywords=%s, raw_avg=%.2f, normalised=%.3f",
            keywords,
            raw_avg,
            normalised
        )
        return normalised, "ok"

    except Exception as exc:
        logger.error("❌ [DEBUG] fetch_trends_score failed critically: %s", exc, exc_info=True)
        return _NEUTRAL_SCORE, "failed"


# ===========================================================================
# 2. Google Places Nearby Fetcher
# ===========================================================================

async def fetch_places_score(
    latitude: float,
    longitude: float,
    radius: int,
) -> Tuple[float, str]:
    """
    Return a normalised (0–1) venue-density score from the Google Places
    Nearby Search API.

    Venue density proxy: number of results returned (up to 3 pages of max 20).
    More nearby businesses → higher commercial density → higher score.

    Falls back to 0.5 on any error.
    """
    cache_key = geo_intent_cache.build_key(latitude, longitude, [], radius) + ":places"
    cached = geo_intent_cache.get(cache_key)
    if cached is not None:
        logger.debug("Places cache hit for %s", cache_key)
        return cached, "ok"

    api_key = getattr(settings, "GOOGLE_MAPS_API_KEY", None)
    if not api_key:
        logger.warning("GOOGLE_MAPS_API_KEY not set — using neutral places score")
        return _NEUTRAL_SCORE, "failed", []

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{latitude},{longitude}",
        "radius": radius,
        "key": api_key,
    }

    try:
        count = 0
        pages_fetched = 0
        max_pages = 2  # Reduced to 2 for performance in live radar
        place_types = []

        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            while pages_fetched < max_pages:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                status = data.get("status", "UNKNOWN")
                if status not in ("OK", "ZERO_RESULTS"):
                    logger.warning("Places API returned status=%s on page %d", status, pages_fetched + 1)
                    # Do not fabricate POI data: callers must surface real API status to the user.
                    if status == "REQUEST_DENIED":
                        logger.error(
                            "Places API REQUEST_DENIED (check API key, billing, Places API enabled). "
                            "lat=%.4f lng=%.4f",
                            latitude,
                            longitude,
                        )
                        return _NEUTRAL_SCORE, "request_denied", []
                    if pages_fetched == 0:
                        return _NEUTRAL_SCORE, "failed", []
                    break

                results = data.get("results", [])
                count += len(results)
                for r in results:
                    place_types.extend(r.get("types", []))
                
                pages_fetched += 1

                next_page_token = data.get("next_page_token")
                if not next_page_token or pages_fetched >= max_pages:
                    break
                
                # Google requires a short delay before next_page_token is valid
                await asyncio.sleep(1.0)
                
                # Update params for next page retrieval
                params = {"key": api_key, "pagetoken": next_page_token}

        # Scale: 0 places → 0, 40 places (2 pages) → 1.0
        normalised = _clamp01(count / 40.0)

        geo_intent_cache.set(cache_key, normalised, GeoIntentTTLCache.PLACES_TTL)
        logger.info(
            "✅ [DEBUG] Places density fetched. count=%d, radius=%dm, score=%.3f, types=%d",
            count,
            radius,
            normalised,
            len(place_types)
        )
        return normalised, "ok", place_types

    except httpx.TimeoutException:
        logger.error("❌ [DEBUG] Places API request timed out after %.1fs", _HTTP_TIMEOUT)
        return _NEUTRAL_SCORE, "failed", []
    except Exception as exc:
        logger.error("❌ [DEBUG] fetch_places_score failed critically: %s", exc, exc_info=True)
        return _NEUTRAL_SCORE, "failed", []


# ===========================================================================
# 3. Tomorrow.io Weather Fetcher
# ===========================================================================

async def fetch_weather_score(
    latitude: float,
    longitude: float,
    is_indoor: bool,
) -> Tuple[float, str]:
    """
    Return a normalised (0–1) weather-impact score from Tomorrow.io.

    Business-impact logic:
      - Indoor business: rain *increases* likelihood of walk-in customers
        (people shelter in cafes, malls, etc.) → rain BOOSTS score.
      - Outdoor business: rain *reduces* foot traffic → rain LOWERS score.
    Temperature comfort range (15 – 30 °C) also contributes positively.

    Falls back to 0.5 on any error.
    """
    cache_key = geo_intent_cache.build_key(latitude, longitude, [], 0) + ":weather"
    cached = geo_intent_cache.get(cache_key)
    if cached is not None:
        logger.debug("Weather cache hit for %s", cache_key)
        return cached, "ok"

    api_key = getattr(settings, "TOMORROW_API_KEY", None)
    if not api_key:
        logger.warning("TOMORROW_API_KEY not set — using neutral weather score")
        return _NEUTRAL_SCORE, "failed"

    url = "https://api.tomorrow.io/v4/weather/realtime"
    params = {
        "location": f"{latitude},{longitude}",
        "apikey": api_key,
        "units": "metric",
        "fields": "temperature,weatherCode,precipitationIntensity",
    }

    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        values = data.get("data", {}).get("values", {})
        temperature: float = float(values.get("temperature", 22.0))
        precip: float = float(values.get("precipitationIntensity", 0.0))
        weather_code: int = int(values.get("weatherCode", 1000))

        is_raining = precip > 0.1 or weather_code in (
            4000, 4001, 4200, 4201,          # drizzle / rain codes
            6000, 6001, 6200, 6201,          # freezing rain codes
        )

        # Temperature comfort: peak at 22 °C, penalty for extreme heat/cold
        temp_comfort = _clamp01(1.0 - abs(temperature - 22.0) / 30.0)

        # Rain effect — flipped depending on indoor/outdoor
        rain_effect = 0.15 if is_raining else 0.0
        if is_indoor:
            weather_raw = temp_comfort + rain_effect        # rain helps indoors
        else:
            weather_raw = temp_comfort - rain_effect        # rain hurts outdoors

        normalised = _clamp01(weather_raw)

        geo_intent_cache.set(cache_key, normalised, GeoIntentTTLCache.WEATHER_TTL)
        logger.info(
            "✅ [DEBUG] Weather signal processed. temp=%.1f°C, rain=%s, indoor=%s, score=%.3f",
            temperature,
            is_raining,
            is_indoor,
            normalised
        )
        return normalised, "ok"

    except httpx.TimeoutException:
        logger.error("❌ [DEBUG] Weather API request timed out after %.1fs", _HTTP_TIMEOUT)
        return _NEUTRAL_SCORE, "failed"
    except Exception as exc:
        logger.error("❌ [DEBUG] fetch_weather_score failed: %s", exc, exc_info=True)
        return _NEUTRAL_SCORE, "failed"


# ===========================================================================
# Parallel Ingestion Entry Point
# ===========================================================================

async def ingest_all_signals(
    keywords: List[str],
    latitude: float,
    longitude: float,
    radius: int,
    is_indoor: bool,
    geo_code: str = "PK",
    user_tier: str = "free",
) -> dict:
    """
    Run all three fetchers concurrently via asyncio.gather.

    Failures are isolated — each fetcher returns 0.5 on error.
    Always returns a dict with keys: trends, places, weather.
    """
    trends_task = fetch_trends_score(keywords, geo_code, latitude, longitude, radius)
    places_task = fetch_places_score(latitude, longitude, radius)
    weather_task = fetch_weather_score(latitude, longitude, is_indoor)

    # ── Tier Enforcement: Free users only get Google Places ───────────
    if user_tier == "free":
        logger.info("🆓 Free Tier detected: Filtering to Google Maps signal only.")
        trends_result = (_NEUTRAL_SCORE, "limited")
        weather_result = (_NEUTRAL_SCORE, "limited")
        # Run only places task
        places_result = await places_task
    else:
        trends_result, places_result, weather_result = await asyncio.gather(
            trends_task,
            places_task,
            weather_task,
            return_exceptions=False,
        )

    return {
        "trends": trends_result[0],
        "places": places_result[0],
        "weather": weather_result[0],
        "status": {
            "trends": trends_result[1],
            "places": places_result[1],
            "weather": weather_result[1],
        },
        "place_types": places_result[2] if len(places_result) > 2 else []
    }
