# Presentation Layer - Trend Signal Router
from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
import logging

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
from application.services.google_trends_service import GoogleTrendsService
from application.services.trend_analytics_service import TrendAnalyticsService
from application.services.trend_detection_service import TrendDetectionService
from infrastructure.database.models.user_model import UserModel
from presentation.routers.auth_router import get_current_user_email


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/trends", tags=["Trend Signals"])


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

    # PART 1: Resolve niche parameter (handle ObjectID or plain string)
    from application.utils.trend_helpers import resolve_niche_name
    resolved_niche = await resolve_niche_name(request.niche)
    
    logger.info("🔍 TREND FETCH REQUEST - User: %s, Niche: %s → %s, Category: %s, Timeframe: %s", 
               current_user_email, request.niche, resolved_niche, request.category, request.timeframe or '30d')

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
    
    background_tasks.add_task(
        detection_service.execute_detection_pipeline,
        trend_signal.id,
        request.timeframe or "30d"
    )
    
    logger.info("Full detection pipeline initiated for user %s with trend_id %s", current_user_email, trend_signal.id)
    
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
        trend_responses = [
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
            for trend in trends
        ]
        
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

@router.get("/live", summary="Get live trend feed for user")
async def get_live_trends(
    location: str = None,
    limit: int = 20,
    current_user_email: str = Depends(get_current_user_email),
    analytics_service: TrendAnalyticsService = Depends(get_analytics_service)
):
    """Returns detected spikes for the user's live ticker/feed"""
    try:
        logger.info("📡 LIVE FEED REQUEST - User: %s, Location: %s, Limit: %s", current_user_email, location, limit)
        results = await analytics_service.get_live_feed(current_user_email, location, limit)
        logger.info("📡 LIVE FEED RESPONSE - Returned %d trends for %s", len(results), current_user_email)
        if results:
            sample_keyword = results[0].get('keyword', 'N/A') if isinstance(results[0], dict) else 'N/A'
            logger.info("📡 Sample trend: %s", sample_keyword)
        return {"trends": results, "count": len(results)}
    except Exception as e:
        logger.error("Error fetching live trends for user %s: %s", current_user_email, str(e), exc_info=True)
        # Return empty array instead of error for graceful degradation
        return {"trends": [], "count": 0}


@router.get("/heatmap", summary="Get trend geographic distribution")
async def get_trend_heatmap(
    location: str = None,
    current_user_email: str = Depends(get_current_user_email),
    analytics_service: TrendAnalyticsService = Depends(get_analytics_service)
):
    """Returns trend intensity by region for heatmap visualization"""
    try:
        logger.info("🗺️ HEATMAP REQUEST - User: %s, Location: %s", current_user_email, location)
        results = await analytics_service.get_geo_heatmap(current_user_email, location)
        logger.info("🗺️ HEATMAP RESPONSE - Returned %d regions for %s", len(results), current_user_email)
        return {"regions": results, "count": len(results)}
    except Exception as e:
        logger.error("Error fetching heatmap for user %s: %s", current_user_email, str(e), exc_info=True)
        return {"regions": [], "count": 0}


@router.get("/spike_timeline", summary="Get timeline of trend spikes")
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
        logger.info("📈 SPIKE TIMELINE RESPONSE - Returned %d data points for %s", len(results), current_user_email)
        return {"timeline": results, "count": len(results)}
    except Exception as e:
        logger.error("Error fetching spike timeline for user %s: %s", current_user_email, str(e), exc_info=True)
        return {"timeline": [], "count": 0}


@router.get("/bubble_chart", summary="Get market gap analytics")
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
        return {"opportunities": results, "count": len(results)}
    except Exception as e:
        logger.error("Error fetching bubble chart data for user %s: %s", current_user_email, str(e), exc_info=True)
        return {"opportunities": [], "count": 0}


@router.get("/platform_reach", summary="Get platform-specific reach splits")
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
        return results
    except Exception as e:
        logger.error("Error fetching platform reach for user %s: %s", current_user_email, str(e), exc_info=True)
        return {"google": 0, "instagram": 0, "facebook": 0, "total_reach": "0%"}


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
            error_message=trend.error_message
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
            # Use detection data
            niche = detection.niche
            lifecycle_stage = detection.lifecycle_stage or "Mainstream"
            profit_score = detection.profit_score or 50.0
            social_score = 50.0  # Fallback
            saturation_score = 50.0  # Fallback
            platform_bias = {}  # Fallback
        
        # Generate suggestions
        suggestions = await suggestion_service.generate_content_suggestions(
            keyword=request.keyword,
            niche=niche,
            lifecycle_stage=lifecycle_stage,
            profit_score=profit_score,
            social_score=social_score,
            saturation_score=saturation_score,
            platform_bias=platform_bias
        )
        
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
        "You are a friendly marketing assistant helping small business owners in Pakistan understand "
        "social media trends. Explain things in simple, plain English — no jargon. "
        "Your response MUST be valid JSON with exactly these keys: "
        "\"explanation\", \"why_now\", \"content_prompt\"."
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

    user_prompt = (
        f"Trend: \"{request.keyword}\"\n"
        f"Business niche: {request.niche}\n"
        f"Location: {request.location}\n"
        f"Metrics: {metrics_text}\n\n"
        "Write three things:\n"
        "1. \"explanation\": 2-3 sentences in plain English explaining what this trend is and why it matters for this business.\n"
        "2. \"why_now\": One short sentence explaining why the business owner should act on this today.\n"
        "3. \"content_prompt\": A ready-to-use campaign idea they can paste directly into a content generator (1-2 sentences, specific and actionable).\n\n"
        "Respond ONLY with a JSON object containing these three keys."
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
            content_prompt=result.get("content_prompt", "")
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
    """Get Google Trends cache status"""
    from application.services.google_trends_service import _TRENDS_CACHE
    from datetime import datetime
    
    cache_entries = []
    total_entries = len(_TRENDS_CACHE)
    
    for cache_key, entry in _TRENDS_CACHE.items():
        age_minutes = (datetime.now() - entry["timestamp"]).total_seconds() / 60
        cache_entries.append({
            "key": cache_key[:8] + "...",
            "age_minutes": round(age_minutes, 1),
            "ttl_minutes": entry["ttl"],
            "is_valid": age_minutes < entry["ttl"]
        })
    
    return {
        "total_entries": total_entries,
        "entries": cache_entries[:10]  # Show first 10
    }


@router.post(
    "/cache/clear",
    summary="Clear Google Trends cache",
    status_code=status.HTTP_200_OK
)
async def clear_cache(
    current_user_email: str = Depends(get_current_user_email)
):
    """Clear all cached Google Trends data (admin/dev only)"""
    from application.services.google_trends_service import _TRENDS_CACHE
    
    count = len(_TRENDS_CACHE)
    _TRENDS_CACHE.clear()
    
    logger.info("Cache cleared by %s: %d entries removed", current_user_email, count)
    
    return {
        "success": True,
        "message": f"Cleared {count} cache entries",
        "cleared_count": count
    }


@router.get(
    "/debug/database-status",
    summary="Debug endpoint - Check database trends",
    status_code=status.HTTP_200_OK
)
async def debug_database_status(
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Debug endpoint to verify what's actually in the database.
    Returns raw database record counts and sample data.
    """
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
