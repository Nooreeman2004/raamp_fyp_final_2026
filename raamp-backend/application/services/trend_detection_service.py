# Application Layer - Trend Detection Service
import logging
import asyncio
from typing import List, Optional
from datetime import datetime

from application.services.google_trends_service import GoogleTrendsService
from application.services.notification_service import NotificationService
from application.services.instagram_graph_api_service import InstagramGraphAPIClient
from infrastructure.database.models.user_model import UserModel
from infrastructure.database.models.business_model import BusinessModel
from infrastructure.database.models.notification_model import NotificationType
from infrastructure.database.models.trend_detection_model import TrendDetectionModel
from infrastructure.database.models.trend_watchlist_model import TrendWatchlistModel
from infrastructure.utils.trend_math import TrendDetectionEngine
from domain.entities.trend_detection import TrendDetectionConfig, TrendSpike

logger = logging.getLogger(__name__)


class TrendDetectionService:
    """Service for orchestrating business-level trend detection logic"""
    
    def __init__(
        self, 
        trends_service: Optional[GoogleTrendsService] = None,
        notification_service: Optional[NotificationService] = None,
        ig_client: Optional[InstagramGraphAPIClient] = None
    ):
        self.trends_service = trends_service or GoogleTrendsService()
        self.notification_service = notification_service or NotificationService()
        self.ig_client = ig_client or InstagramGraphAPIClient()
        self.config = TrendDetectionConfig()

    async def run_detection_for_all_users(self):
        """
        Background task to run detection for all users.
        1. Fetch all users
        2. Get their niche and location
        3. Fetch/Update trend signals
        4. Run detection
        5. Notify if spikes found
        """
        logger.info("Starting global trend detection cycle...")
        # Only run for users who have logged in within the last 2 hours to save rate limits
        from datetime import timedelta
        active_threshold = datetime.utcnow() - timedelta(hours=2)
        
        users = await UserModel.find(UserModel.last_login >= active_threshold).to_list()
        logger.info("Found %d active users for detection cycle.", len(users))
        
        for user in users:
            try:
                await self.run_detection_for_user(user)
                # Randomized delay to avoid Google Trends rate limiting (429)
                import random
                await asyncio.sleep(random.uniform(10.0, 30.0)) # Increased delay
            except Exception as e:
                logger.error("Error in trend detection for user %s: %s", user.email, str(e))
                
        logger.info("Global trend detection cycle completed.")

    async def initialize_detection_signal(self, user: UserModel, override_niche: str = None, override_category: str = None):
        """
        Create a pending trend signal based on user context.
        Location is LOCKED from user.onboarding_location or BusinessModel.country.
        Returns the created TrendSignal object.
        
        PART 1: Resolves niche (handles ObjectID or plain string)
        PART 3: Expands keywords with business specialties if available
        """
        # 1. Resolve Niche (Business Domain) - Use new helper for clean ObjectID handling
        from application.utils.trend_helpers import resolve_niche_name
        
        if override_niche:
            niche = await resolve_niche_name(override_niche)
        elif user.business_domain:
            niche = await resolve_niche_name(user.business_domain)
        else:
            niche = "marketing"  # Safe fallback
        
        category = override_category or "all"  # Default to all categories for broader trend coverage
        
        # 2. Get Location (LOCKED - no override allowed)
        location = None
        business = await BusinessModel.find_one({"user_id": user.email})
        
        # Priority 1: Onboarding location (user-level lock)
        if user.onboarding_location:
            location = user.onboarding_location
        # Priority 2: Business country (fallback)
        elif business and business.country:
            location = business.country
        
        # Validation: Location is mandatory
        if not location:
            raise ValueError(
                f"Location not configured for user {user.email}. "
                "User must complete onboarding or set business location."
            )
        
        # PART 3: Expand keywords with business specialties (backward compatible)
        from application.utils.trend_helpers import expand_with_synonyms
        
        expanded_keywords = []
        if business and business.specialties:
            # User has configured specialties - expand with synonyms
            expanded_keywords = await expand_with_synonyms(business.specialties)
            logger.info(
                "🎯 SPECIALTY EXPANSION - User: %s, Original: %s, Expanded: %s", 
                user.email, business.specialties, expanded_keywords
            )
        
        # If category override is "all" but we have specialties, use first specialty
        # This allows specialty-based detection while maintaining backward compatibility
        if category == "all" and expanded_keywords:
            category = expanded_keywords[0]  # Use primary expanded keyword
            logger.info("📊 ENHANCED DETECTION - Switched from 'all' to specialty keyword: %s", category)
        
        logger.info("Resolved detection context for %s: Niche='%s', Category='%s', Location='%s'", user.email, niche, category, location)
        
        # 3. Create Trend Signal
        trend_signal = await self.trends_service.create_trend_signal(
            user_email=user.email,
            niche=niche,
            category=category,
            location=location
        )
        return trend_signal

    async def execute_detection_pipeline(self, trend_signal_id: str, timeframe: str = "30d"):
        """Execute the heavy detection logic for an existing trend signal"""
        from application.services.social_trend_service import SocialTrendService
        from application.services.saturation_service import SaturationService
        from application.services.lifecycle_classification_service import LifecycleClassificationService
        from application.services.trend_prediction_service import TrendPredictionService
        from application.services.profit_proxy_service import ProfitProxyService
        
        # Get trend signal first to update status
        trend_signal = await self.trends_service.get_trend_by_id(trend_signal_id)
        if not trend_signal:
            logger.error("Trend signal %s not found", trend_signal_id)
            return
        
        try:
            logger.info("PIPELINE START: Fetching Google Trends for signal %s (user: %s)...", trend_signal_id, trend_signal.user_email)
            
            social_service = SocialTrendService()
            saturation_service = SaturationService()
            lifecycle_service = LifecycleClassificationService()
            prediction_service = TrendPredictionService()
            profit_service = ProfitProxyService()
            
            # Fetch the data (blocking but we are in async task)
            success = await self.trends_service.process_trend_signal(trend_signal_id, timeframe)
            
            # Refresh trend signal after processing
            trend_signal = await self.trends_service.get_trend_by_id(trend_signal_id)
            if not trend_signal:
                logger.error("Trend signal %s disappeared during processing", trend_signal_id)
                return

            if not success:
                logger.warning("Failed to fetch Google Trends data for %s", trend_signal.user_email)
                await self.trends_service.repository.update_status(
                    trend_signal_id, 
                    "failed", 
                    "Failed to fetch Google Trends data"
                )
                return
                
            # 4. Detect Spikes and Enrich Data
            trend_data = trend_signal 
            if not trend_data or not trend_data.search_interest:
                # Mark as completed even if no data
                await self.trends_service.repository.update_status(
                    trend_signal_id, 
                    "completed"
                )
                return
                
            dates = trend_data.search_interest.get("dates", [])
            data_streams = trend_data.search_interest.get("data", {})
            
            all_spikes = []
            top_keyword = None
            max_z = -1.0
            max_interest = 0
            keyword_scores = {}  # Track all keywords with their z-scores and interest
            
            for keyword, values in data_streams.items():
                spikes = TrendDetectionEngine.detect_spikes(
                    dates=dates,
                    values=values,
                    keyword=keyword,
                    niche=trend_data.niche,
                    location=trend_data.location,
                    config=self.config
                )
                all_spikes.extend(spikes)
                
                # Track the current interest value and z-score for each keyword
                current_interest = values[-1] if values else 0
                current_z = spikes[-1].z_score if spikes else 0.0
                keyword_scores[keyword] = {"z_score": current_z, "interest": current_interest}
                
                if spikes:
                    if current_z > max_z:
                        max_z = current_z
                        top_keyword = keyword
                        max_interest = current_interest
                        
                # Track the highest interest keyword even if no spikes
                if current_interest > max_interest:
                    max_interest = current_interest
                    if not top_keyword:  # Only set if we haven't found a spike
                        top_keyword = keyword
                        max_z = current_z

            logger.info("DETECTION COMPLETE: Found %d spikes. Strongest signal: '%s' (%.1fσ, interest: %d)", len(all_spikes), top_keyword, max_z, max_interest)
            
            # 5. Enrich with Social & Saturation Logic (Layer 1 Complete)
            # ALWAYS enrich if we have data, even without spikes
            if top_keyword and max_interest > 0:
                # --- PLATFORM BIAS ---
                platform_scores = social_service.analyze_platform_bias(top_keyword)
                trend_signal.platform_bias = platform_scores
                
                # --- HASHTAGS (Real Discovery) ---
                # Try to fetch real hashtag variations from Instagram if user is connected
                real_hashtags = []
                
                # Check mandatory connection status
                from application.services.onboarding_service import OnboardingService
                onboarding_service = OnboardingService()
                ig_conn = await onboarding_service.get_instagram_connection(trend_signal.user_email)
                
                if not ig_conn:
                    logger.error("MANDATORY CONNECTION MISSING: Instagram not configured for %s", trend_signal.user_email)
                    await self.notification_service.create_and_send(
                        user_id=trend_signal.user_email,
                        type=NotificationType.ALERT,
                        title="⚠️ Arbitrage Data Restricted",
                        message="Your Instagram Business account is disconnected. Connect it in Settings to unlock real-world social velocity scores.",
                        metadata={"sub_type": "connection_required", "platform": "instagram"}
                    )
                
                try:
                    # Use new aggregated engagement API for real Instagram metrics
                    ig_engagement = await self.ig_client.compute_keyword_engagement_score(
                        trend_signal.user_email, 
                        top_keyword
                    )
                    
                    if ig_engagement:
                        # Use real Instagram engagement score (0-100)
                        media_count = ig_engagement.get("media_count", 0)
                        engagement_score = ig_engagement.get("engagement_score", 0)
                        avg_likes = ig_engagement.get("avg_likes", 0)
                        avg_comments = ig_engagement.get("avg_comments", 0)
                        
                        logger.info(
                            "✅ REAL Instagram data for '%s': %d posts, %.1f avg likes, %.1f avg comments, score: %.2f",
                            top_keyword, media_count, avg_likes, avg_comments, engagement_score
                        )
                        
                        # Override platform score for Instagram with real data
                        # engagement_score is already 0-100, normalize to 0-1 for platform_scores
                        platform_scores["instagram"] = engagement_score / 100.0
                        
                        real_hashtags.append(f"#{top_keyword.replace(' ', '')}")
                        trend_signal.is_real_social = True
                    else:
                        logger.warning("Instagram API returned no data for '%s', falling back to semantic analysis", top_keyword)
                        
                except Exception as e:
                    logger.error("Instagram API error for '%s': %s. Falling back to semantic analysis.", top_keyword, str(e))
                    # Continue with semantic fallback (platform_scores already computed)

                # Fallback hashtags
                # related_queries structure: {keyword: [{query: "...", value: ...}, ...]}
                related_query_list = trend_signal.related_queries.get(top_keyword, [])
                if related_query_list and isinstance(related_query_list, list):
                    # Extract query strings from the list of dicts
                    query_strings = [q.get("query", top_keyword) for q in related_query_list if isinstance(q, dict)]
                    derived_hashtags = social_service.generate_hashtags(query_strings or [top_keyword])
                else:
                    # Fallback to just the top keyword
                    derived_hashtags = social_service.generate_hashtags([top_keyword])
                trend_signal.hashtags = list(set(real_hashtags + derived_hashtags))
                
                # --- SOCIAL SCORE ---
                # Use real platform scores enriched by Meta API
                trend_signal.social_score = social_service.compute_social_trend_score(max_z * 10, platform_scores)
                
                # --- SATURATION SCORE (Stability Upgrade) ---
                current_interest = data_streams[top_keyword][-1] if data_streams.get(top_keyword) else 50
                logger.info("ENRICHMENT: Starting Saturation analysis for '%s' (Interest: %s)...", top_keyword, current_interest)
                saturation_data = await saturation_service.batch_saturation_analysis([{"keyword": top_keyword, "interest": current_interest}])
                if saturation_data:
                    trend_signal.saturation_score = saturation_data[0].get("saturation_score", 50)
                    trend_signal.is_real_saturation = saturation_data[0].get("is_real_data", False)
                    logger.info("ENRICHMENT: Saturation score for '%s': %s", top_keyword, trend_signal.saturation_score)
                
                # --- ARBITRAGE SCORE ---
                sat = max(1, trend_signal.saturation_score or 50)
                trend_signal.arbitrage_score = round((max_z * 100) / sat, 2)
                logger.info("PIPELINE COMPLETE: Arbitrage score for '%s': %s", top_keyword, trend_signal.arbitrage_score)
                
                # --- LIFECYCLE & PREDICTION ENHANCEMENT (NEW) ---
                # Calculate slopes and acceleration for lifecycle classification
                top_keyword_values = data_streams.get(top_keyword, [])
                if top_keyword_values and len(top_keyword_values) > 7:
                    # Calculate slopes
                    slopes = lifecycle_service.calculate_slopes(top_keyword_values, dates)
                    short_term_slope = slopes["short_term_slope"]
                    long_term_slope = slopes["long_term_slope"]
                    acceleration = slopes["acceleration"]
                    avg_volume = sum(top_keyword_values) / len(top_keyword_values)
                    current_value = top_keyword_values[-1]
                    
                    # Classify lifecycle stage
                    lifecycle_stage = lifecycle_service.classify_lifecycle(
                        z_score=max_z,
                        short_term_slope=short_term_slope,
                        long_term_slope=long_term_slope,
                        acceleration=acceleration,
                        saturation_score=trend_signal.saturation_score or 50,
                        avg_volume=avg_volume,
                        current_value=current_value
                    )
                    
                    # Generate 7-day forecast and breakout probability
                    prediction_result = prediction_service.predict_trend(
                        values=top_keyword_values,
                        forecast_days=7
                    )
                    
                    # Calculate profit score
                    profit_score = profit_service.calculate_profit_score(
                        arbitrage_score=trend_signal.arbitrage_score or 0,
                        social_score=trend_signal.social_score or 0,
                        saturation_score=trend_signal.saturation_score or 50,
                        breakout_probability=prediction_result["breakout_probability"],
                        lifecycle_stage=lifecycle_stage
                    )
                    
                    logger.info("ENRICHMENT COMPLETE: Lifecycle=%s, Profit=%.1f, Breakout Prob=%.1f%%", lifecycle_stage, profit_score, prediction_result['breakout_probability'])
                else:
                    # Fallback values for insufficient data
                    lifecycle_stage = "Emerging"
                    prediction_result = {
                        "forecast_series": [],
                        "predicted_growth_pct": 0.0,
                        "breakout_probability": 0.0
                    }
                    profit_score = 50.0
                    logger.warning("Insufficient data for lifecycle/prediction analysis on '%s'", top_keyword)
                
                # Store enhanced metrics in TrendSignal
                trend_signal.lifecycle_stage = lifecycle_stage
                trend_signal.predicted_growth_pct = prediction_result["predicted_growth_pct"]
                trend_signal.breakout_probability = prediction_result["breakout_probability"]
                trend_signal.profit_score = profit_score
                trend_signal.forecast_series = prediction_result["forecast_series"]
                trend_signal.timeframe = timeframe
                
                # Persist all enriched data to database
                await self.trends_service.repository.update_enriched_data(
                    trend_id=trend_signal_id,
                    arbitrage_score=trend_signal.arbitrage_score,
                    saturation_score=trend_signal.saturation_score,
                    social_score=trend_signal.social_score,
                    hashtags=trend_signal.hashtags,
                    platform_bias=trend_signal.platform_bias,
                    is_real_social=trend_signal.is_real_social,
                    is_real_saturation=trend_signal.is_real_saturation,
                    lifecycle_stage=lifecycle_stage,
                    predicted_growth_pct=prediction_result["predicted_growth_pct"],
                    breakout_probability=prediction_result["breakout_probability"],
                    profit_score=profit_score,
                    forecast_series=prediction_result["forecast_series"],
                    timeframe=timeframe
                )
                
                # --- WATCHLIST CHECKS ---
                await self._check_watchlist_alerts(trend_signal.user_email, top_keyword, max_z, trend_signal.saturation_score)
            
            # Update status to completed
            await self.trends_service.repository.update_status(
                trend_signal_id, 
                "completed"
            )
            
            logger.info("PIPELINE SUCCESS: Signal %s completed for user %s", trend_signal_id, trend_signal.user_email)
            
            # 6. Notify User
            if all_spikes:
                await self._notify_spikes(trend_data.user_email, all_spikes, timeframe)
                
        except Exception as e:
            logger.error("PIPELINE ERROR: Failed to process signal %s for user %s: %s", 
                        trend_signal_id, trend_signal.user_email, str(e), exc_info=True)
            
            # Update status to failed with internal error details
            try:
                await self.trends_service.repository.update_status(
                    trend_signal_id, 
                    "failed", 
                    str(e)[:200]  # Store first 200 chars of error for internal logging
                )
            except Exception as save_err:
                logger.error("Failed to update failed status for signal %s: %s", trend_signal_id, str(save_err))
            
            # Notify user with user-friendly message (hide internal errors)
            try:
                await self.notification_service.create_and_send(
                    user_id=trend_signal.user_email,
                    type=NotificationType.ALERT,
                    title="⚠️ Trend Analysis Unavailable",
                    message="Trend analysis is temporarily unavailable. Please try again in a few moments.",
                    metadata={"sub_type": "pipeline_error", "trend_signal_id": trend_signal_id}
                )
            except Exception as notif_err:
                logger.error("Failed to send failure notification: %s", str(notif_err))

    async def run_detection_for_user(self, user: UserModel, override_niche: str = None):
        """Run full detection cycle for a specific user (legacy wrapper)"""
        trend_signal = await self.initialize_detection_signal(user, override_niche)
        await self.execute_detection_pipeline(trend_signal.id)

    async def _notify_spikes(self, user_email: str, spikes: List[TrendSpike], timeframe: str = "30d"):
        """Create notifications and store persistent records for detected spikes"""
        for spike in spikes:
            # Determine impact level
            impact = "LOW"
            if spike.z_score > 4.0:
                impact = "HIGH"
            elif spike.z_score > 2.5:
                impact = "MEDIUM"
                
            # 1. Store persistent detection record
            detection = TrendDetectionModel(
                user_id=user_email,
                keyword=spike.keyword,
                niche=spike.niche,
                location=spike.location,
                z_score=spike.z_score,
                current_value=spike.current_value,
                expected_value=spike.expected_value,
                impact_level=impact,
                detected_at=spike.timestamp,
                timeframe=timeframe
            )
            await detection.insert()
            
            # 2. Trigger notification
            title = "🚀 Emerging Trend Detected!"
            message = f"Trend alert: '{spike.keyword}' is spiking in {spike.location} for the {spike.niche} niche!"
            
            metadata = {
                "sub_type": "trend",
                "keyword": spike.keyword,
                "z_score": spike.z_score,
                "niche": spike.niche,
                "location": spike.location,
                "impact_level": impact,
                "detected_at": spike.timestamp.isoformat()
            }
            
            await self.notification_service.create_and_send(
                user_id=user_email,
                type=NotificationType.ALERT,
                title=title,
                message=message,
                metadata=metadata
            )
            logger.info("Notification sent and spike stored for %s: %s", user_email, spike.keyword)

    async def _check_watchlist_alerts(self, user_email: str, keyword: str, velocity: float, saturation: float):
        """Check if a tracked keyword has triggered any watchlist alerts"""
        try:
            watchlist_item = await TrendWatchlistModel.find_one({
                "user_email": user_email,
                "keyword": {"$regex": f"^{keyword}$", "$options": "i"},
                "is_active": True
            })
            
            if watchlist_item:
                logger.info("Watchlist hit for %s: %s. Checking thresholds...", user_email, keyword)
                
                # Update snapshots
                watchlist_item.last_velocity = velocity
                watchlist_item.last_saturation = saturation
                watchlist_item.last_arbitrage_score = round((velocity * 100) / max(1, saturation), 2)
                watchlist_item.updated_at = datetime.utcnow()
                await watchlist_item.save()
                
                # Trigger specific watchlist alert if threshold met
                if watchlist_item.alert_on_spike and velocity >= watchlist_item.velocity_threshold:
                    await self.notification_service.create_and_send(
                        user_id=user_email,
                        type=NotificationType.ALERT,
                        title="🎯 Watchlist Alert: Spike Detected!",
                        message=f"Tracked trend '{keyword}' has hit a velocity of {velocity}σ. Time to execute!",
                        metadata={
                            "sub_type": "watchlist_alert",
                            "keyword": keyword,
                            "velocity": velocity,
                            "saturation": saturation
                        }
                    )
                    logger.info("Watchlist ALERT fired for %s: %s", user_email, keyword)
        except Exception as e:
            logger.error("Error checking watchlist alerts: %s", e)
