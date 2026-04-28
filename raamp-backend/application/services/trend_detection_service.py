# Application Layer - Trend Detection Service
import logging
import time
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os

from application.services.google_trends_service import GoogleTrendsService
from application.services.notification_service import NotificationService
from application.services.instagram_graph_api_service import InstagramGraphAPIClient
from application.services.trend_simplification_service import TrendSimplificationService
from infrastructure.database.models.user_model import UserModel
from infrastructure.database.models.business_model import BusinessModel
from infrastructure.database.models.notification_model import NotificationType
from infrastructure.database.models.trend_detection_model import TrendDetectionModel
from infrastructure.database.models.trend_watchlist_model import TrendWatchlistModel
from infrastructure.utils.trend_math import TrendDetectionEngine
from domain.entities.trend_detection import TrendDetectionConfig, TrendSpike
from presentation.routers.activity_router import log_activity
from config import config as app_config
from infrastructure.utils.obs import emit_event
from application.services.trend_actionable_recommendation_service import TrendActionableRecommendationService

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
        self.actionable_rec_service = TrendActionableRecommendationService()
        # Detection parameters are environment-configurable; defaults preserve prior behavior.
        self.config = TrendDetectionConfig(
            rolling_window=int(getattr(app_config, "TREND_ROLLING_WINDOW_DAYS", 14) or 14),
            threshold=float(getattr(app_config, "TREND_Z_THRESHOLD", 2.0) or 2.0),
            alpha=float(getattr(app_config, "TREND_EWMA_ALPHA", 0.3) or 0.3),
            min_data_points=int(getattr(app_config, "TREND_MIN_DATA_POINTS", 5) or 5),
        )

    def _generate_relevant_hashtags(self, keyword: str, niche: str) -> list[str]:
        """
        Generate relevant hashtags based on the trend keyword.
        Prioritizes trend-specific hashtags over business niche hashtags.
        Only adds niche hashtags if they're contextually relevant to the trend.
        """
        hashtags = []
        keyword_lower = keyword.lower()
        
        # Add the main keyword hashtag
        keyword_clean = keyword.replace(' ', '').replace('-', '')
        if keyword_clean:
            hashtags.append(f"#{keyword_clean}")
        
        # Add individual words from multi-word keywords
        keyword_words = [w.strip() for w in keyword.split() if len(w.strip()) > 3]
        for word in keyword_words[:2]:  # Limit to first 2 words
            word_clean = word.replace('-', '')
            if word_clean:
                hashtags.append(f"#{word_clean}")
        
        # Detect trend category from keyword content (not user's business niche)
        trend_category_map = {
            "sports": ["cricket", "football", "soccer", "basketball", "tennis", "match", "game", "vs", "league", "tournament"],
            "fashion": ["fashion", "style", "outfit", "ootd", "clothing", "apparel", "wear", "dress"],
            "food": ["food", "recipe", "cooking", "meal", "dish", "cuisine", "delicious"],
            "tech": ["tech", "technology", "ai", "software", "app", "digital", "innovation"],
            "fitness": ["fitness", "workout", "gym", "exercise", "health", "training"],
            "beauty": ["beauty", "makeup", "skincare", "cosmetic", "hair"],
            "travel": ["travel", "trip", "vacation", "destination", "tourism"],
        }
        
        detected_category = None
        for category, patterns in trend_category_map.items():
            if any(pattern in keyword_lower for pattern in patterns):
                detected_category = category
                break
        
        # Add category-specific hashtags ONLY if they match the trend content
        category_hashtags = {
            "sports": ["#sports", "#game", "#competition"],
            "fashion": ["#fashion", "#style", "#ootd"],
            "food": ["#foodie", "#foodlover", "#instafood"],
            "tech": ["#tech", "#technology", "#innovation"],
            "fitness": ["#fitness", "#workout", "#health"],
            "beauty": ["#beauty", "#makeup", "#skincare"],
            "travel": ["#travel", "#wanderlust", "#explore"],
        }
        
        if detected_category and detected_category in category_hashtags:
            hashtags.extend(category_hashtags[detected_category][:2])
        
        # Add trending/viral hashtags
        hashtags.extend(["#trending", "#viral"])
        
        # Remove duplicates while preserving order (case-insensitive)
        seen = set()
        unique_hashtags = []
        for tag in hashtags:
            tag_lower = tag.lower()
            if tag_lower not in seen:
                seen.add(tag_lower)
                unique_hashtags.append(tag)
        
        # Return top 8 hashtags
        return unique_hashtags[:8]
    
    def _detect_trend_category(self, keyword: str) -> str:
        """
        Detect the actual category/niche of a trend based on its keyword content.
        Returns the detected category or "general" if no specific category is detected.
        """
        keyword_lower = keyword.lower()
        
        # Category detection patterns
        category_patterns = {
            "sports": ["cricket", "football", "soccer", "basketball", "tennis", "match", "game", "vs", "league", "tournament", "fifa", "uefa", "premier", "champions"],
            "politics": ["election", "government", "minister", "president", "parliament", "political", "vote", "campaign", "party"],
            "entertainment": ["movie", "film", "actor", "actress", "celebrity", "music", "concert", "show", "series", "netflix"],
            "fashion": ["fashion", "style", "outfit", "ootd", "clothing", "apparel", "wear", "dress", "designer"],
            "food": ["food", "recipe", "cooking", "meal", "dish", "cuisine", "restaurant", "cafe", "bakery"],
            "tech": ["tech", "technology", "ai", "software", "app", "digital", "innovation", "startup"],
            "fitness": ["fitness", "workout", "gym", "exercise", "health", "training", "yoga"],
            "beauty": ["beauty", "makeup", "skincare", "cosmetic", "hair", "salon"],
            "travel": ["travel", "trip", "vacation", "destination", "tourism", "hotel"],
        }
        
        for category, patterns in category_patterns.items():
            if any(pattern in keyword_lower for pattern in patterns):
                return category
        
        return "general"

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
        
        # Use dict-based query to avoid class-attribute operator issues under Pydantic v2 / Beanie.
        # Prefer DB-side filtering when collections are initialized.
        # In unit tests (no Beanie init), fall back to find_all() which is commonly patched.
        try:
            users = await UserModel.find({"last_login": {"$gte": active_threshold}}).to_list()
        except Exception:
            try:
                users = await UserModel.find_all().to_list()
                users = [u for u in users if getattr(u, "last_login", datetime.utcnow()) >= active_threshold]
            except Exception:
                users = []
        logger.info("Found %d active users for detection cycle.", len(users))
        
        for user in users:
            try:
                await self.run_detection_for_user(user)
                # Randomized delay to avoid Google Trends rate limiting (429)
                import random
                await asyncio.sleep(random.uniform(10.0, 30.0)) # Increased delay
            except ValueError as e:
                # Business specialties are mandatory. If missing, notify once and skip user.
                msg = str(e or "")
                if "Business specialties are required" in msg:
                    try:
                        from infrastructure.database.models.notification_model import NotificationModel

                        existing = await NotificationModel.find_one(
                            NotificationModel.user_id == user.email,
                            NotificationModel.metadata["sub_type"] == "specialties_required",
                        )
                        if not existing:
                            await self.notification_service.create_and_send(
                                user_id=user.email,
                                type=NotificationType.ALERT,
                                title="Action required: add Business Specialties",
                                message="To start background trend scans, add at least 1 Business Specialty in Settings → Business Specialties.",
                                metadata={
                                    "sub_type": "specialties_required",
                                    "action": "open_settings_business_specialties",
                                    "source": "background_scan",
                                },
                            )
                    except Exception:
                        # Never crash the global cycle due to notification issues.
                        pass
                    continue
                logger.error("Validation error in trend detection for user %s: %s", user.email, msg)
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

        # Business specialties are mandatory (compulsory onboarding requirement).
        raw_specialties = getattr(business, "specialties", None) if business else None
        specialties = raw_specialties if isinstance(raw_specialties, list) else []
        specialties = [s for s in specialties if isinstance(s, str) and s.strip()]
        if len(specialties) == 0:
            raise ValueError(
                f"Business specialties are required for user {user.email}. "
                "Please add at least 1 specialty in Settings → Business Specialties."
            )
        
        # Priority 1: Onboarding location (user-level lock)
        if user.onboarding_location:
            location = user.onboarding_location
        # Priority 2: Business country (fallback)
        elif business and business.country:
            location = business.country
        
        # Validation: Location is mandatory
        if not location:
            raise ValueError(
                "Your business location is not set. Please complete your business profile before scanning trends."
            )
        
        # PART 3: Expand keywords with business specialties (backward compatible)
        from application.utils.trend_helpers import expand_with_synonyms
        
        expanded_keywords = []
        if business and isinstance(getattr(business, "specialties", None), list) and business.specialties:
            # User has configured specialties - expand with synonyms
            expanded_keywords = expand_with_synonyms(business.specialties)
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

        # Seed Google Trends keywords with top business specialties (2-3) + base niche/category mapping.
        # Persisted at creation time so `process_trend_signal()` can prefer these on reload.
        seed_keywords: List[str] = []
        try:
            specialties = []
            if business and getattr(business, "specialties", None):
                specialties = [s for s in business.specialties if isinstance(s, str) and s.strip()]
            specialties = specialties[:3]

            base = self.trends_service._get_keywords_for_niche(niche, category)
            merged: List[str] = []
            seen = set()
            for k in (specialties + base):
                kk = (k or "").strip()
                if not kk:
                    continue
                # Guard: never treat UI filter values like "all" as a real keyword.
                if kk.lower() == "all":
                    continue
                lk = kk.lower()
                if lk in seen:
                    continue
                seen.add(lk)
                merged.append(kk)
            seed_keywords = merged[:10]
        except Exception as e:
            logger.info("Specialty keyword seeding skipped (non-fatal): %s", str(e))

        # Phase 1 (IG Hashtag Discovery): if Instagram is connected, enrich the keyword list
        # with real hashtag names from the Instagram Graph API. Silent skip if not connected
        # or if the API fails for any keyword.
        try:
            from application.services.onboarding_service import OnboardingService

            onboarding_service = OnboardingService()
            ig_conn = await onboarding_service.get_instagram_connection(user.email)
            if ig_conn:
                ig_hashtags = await self.ig_client.fetch_trending_hashtags(user.email, seed_keywords)
                if ig_hashtags:
                    merged_all: List[str] = []
                    seen = set()
                    for k in (seed_keywords + ig_hashtags):
                        kk = (k or "").strip()
                        if not kk:
                            continue
                        lk = kk.lower()
                        if lk in seen:
                            continue
                        seen.add(lk)
                        merged_all.append(kk)
                    seed_keywords = merged_all[:10]
        except Exception:
            # Silent by requirement: do not fail or log errors during background scans
            pass
        
        # 3. Create Trend Signal
        trend_signal = await self.trends_service.create_trend_signal(
            user_email=user.email,
            niche=niche,
            category=category,
            location=location,
            keywords=seed_keywords,
        )

        return trend_signal

    async def execute_detection_pipeline(self, trend_signal_id: str, timeframe: str = "30d"):
        """
        Execute the trend detection pipeline for an existing trend signal.

        Current mode: **Fast Current Trends** (no time-series).
        - discovery (SerpAPI Trending Now when available)
        - Instagram hashtag engagement sampling (when connected)
        - persist ranked keywords into TrendSignal
        - persist top opportunities into TrendDetectionModel
        - notify user (discovery low priority, opportunity high priority w/ campaign prefill)
        """
        from application.services.social_trend_service import SocialTrendService
        from application.services.saturation_service import SaturationService
        from application.services.lifecycle_classification_service import LifecycleClassificationService
        from application.services.trend_prediction_service import TrendPredictionService
        from application.services.profit_proxy_service import ProfitProxyService
        from tasks.trend_retry_worker import enqueue_trend_retry
        from infrastructure.database.models.trend_retry_job_model import (
            TrendRetryJobModel,
            TrendRetryJobStatus,
        )
        
        started_at = datetime.utcnow()
        # Get trend signal first to update status
        trend_signal = await self.trends_service.get_trend_by_id(trend_signal_id)
        if not trend_signal:
            logger.error("Trend signal %s not found", trend_signal_id)
            return

        # Observability: log detection parameters for this scan.
        logger.info(
            "Trend detection params: trend_id=%s threshold=%.3f rolling_window=%d alpha=%.3f min_points=%d timeframe=%s",
            trend_signal_id,
            float(getattr(self.config, "threshold", 2.0)),
            int(getattr(self.config, "rolling_window", 14)),
            float(getattr(self.config, "alpha", 0.3)),
            int(getattr(self.config, "min_data_points", 5)),
            timeframe,
        )
        
        try:
            # Step 1: Signal Aggregation
            await self.trends_service.repository.update_status(
                trend_signal_id, "processing", progress_step="Checking what's popular..."
            )

            # -------------------------------
            # FAST CURRENT TRENDS PIPELINE
            # -------------------------------
            # No Google Trends time-series calls. We rank "what's hot now" using:
            # - SerpAPI Trending Now discovery (best-effort)
            # - Instagram hashtag engagement sampling (best-effort)
            # and persist results back to the TrendSignal + TrendDetections.

            from application.services.trends_providers.trending_now_fetcher import TrendingNowFetcher
            from application.services.onboarding_service import OnboardingService
            from infrastructure.database.models.notification_model import NotificationType, NotificationModel

            # Reload signal (ensure we have latest keywords/custom keywords persisted)
            trend_signal = await self.trends_service.get_trend_by_id(trend_signal_id)
            if not trend_signal:
                return

            base_keywords = [k for k in (getattr(trend_signal, "keywords", None) or []) if isinstance(k, str) and k.strip()]

            # Discovery (SerpAPI Trending Now) — non-fatal
            discovered_terms: list[str] = []
            try:
                geo_code = self.trends_service.convert_location_to_code(trend_signal.location)
                discovered_terms = await TrendingNowFetcher().fetch_terms(
                    geo=geo_code,
                    category=getattr(trend_signal, "category", None) or "all",
                    limit=10,
                    use_cache=True,
                )
            except Exception:
                discovered_terms = []

            # Instagram hashtag expansion + engagement scoring (best-effort)
            ig_connected = False
            try:
                ig_connected = bool(await OnboardingService().get_instagram_connection(trend_signal.user_email))
            except Exception:
                ig_connected = False

            ig_hashtags: list[str] = []
            if ig_connected:
                try:
                    # Expand with real hashtag names (strings without '#')
                    ig_hashtags = await self.ig_client.fetch_trending_hashtags(trend_signal.user_email, base_keywords[:8])
                except Exception:
                    ig_hashtags = []

            # Merge candidates
            merged: list[str] = []
            seen = set()
            for k in (discovered_terms + ig_hashtags + base_keywords):
                kk = (k or "").strip()
                if not kk:
                    continue
                # Guard: avoid generic placeholders rendering as trends
                if kk.lower() == "all":
                    continue
                lk = kk.lower()
                if lk in seen:
                    continue
                seen.add(lk)
                merged.append(kk)

            # Keep the fast scan fast: cap candidates aggressively so the UI poll loop
            # sees `completed` quickly even when Instagram calls are slow.
            candidates = merged[:10]

            scored: list[dict] = []
            for idx, kw in enumerate(candidates):
                engagement = None
                if ig_connected:
                    try:
                        # Only sample engagement for the first few candidates to avoid long runtimes.
                        # Hard-timeout each call to keep scans bounded.
                        if idx < 5:
                            engagement = await asyncio.wait_for(
                                self.ig_client.compute_keyword_engagement_score(trend_signal.user_email, kw),
                                timeout=8.0,
                            )
                    except Exception:
                        engagement = None

                score = None
                media_count = None
                if isinstance(engagement, dict):
                    score = float(engagement.get("engagement_score", 0.0) or 0.0)
                    media_count = int(engagement.get("media_count", 0) or 0)

                # Fallback scoring: if IG not connected or sampling failed, use discovery position.
                if score is None:
                    try:
                        if kw in discovered_terms:
                            score = max(5.0, 30.0 - float(discovered_terms.index(kw) * 2))
                        else:
                            score = 5.0
                    except Exception:
                        score = 5.0

                scored.append(
                    {
                        "keyword": kw,
                        "score": float(score or 0.0),  # 0..100-ish proxy
                        "media_count": media_count,
                        "is_real_social": bool(ig_connected and isinstance(engagement, dict)),
                    }
                )

            scored.sort(key=lambda d: float(d.get("score", 0.0)), reverse=True)
            top = scored[:10]
            top_keywords = [d["keyword"] for d in top if d.get("keyword")]

            # Persist ranked keywords back to TrendSignal (so Trend page shows current trends immediately)
            try:
                await self.trends_service.repository.update_status(
                    trend_signal_id, "processing", progress_step="Saving trends..."
                )
                # Reuse enriched-data persistence to keep consistency; search_interest remains empty in fast mode.
                await self.trends_service.repository.update_enriched_data(
                    trend_id=trend_signal_id,
                    arbitrage_score=None,
                    saturation_score=None,
                    social_score=float(top[0]["score"]) if top else None,
                    hashtags=[f"#{k.replace(' ', '')}" for k in top_keywords[:10]],
                    platform_bias={"instagram": 1.0 if ig_connected else 0.0, "google": 0.0, "facebook": 0.0},
                    is_real_social=bool(ig_connected),
                    is_real_saturation=False,
                    lifecycle_stage="Current",
                    predicted_growth_pct=None,
                    breakout_probability=None,
                    profit_score=float(top[0]["score"]) if top else None,
                    forecast_series=[],
                    timeframe="fast_current",
                )
            except Exception:
                pass

            # Also persist keywords list itself (source of truth for UI list)
            try:
                from bson import ObjectId
                from infrastructure.database.models.trend_signal_model import TrendSignalModel

                m = await TrendSignalModel.get(ObjectId(str(trend_signal_id)))
                if m:
                    m.keywords = top_keywords[:20]
                    m.fetch_status = "completed"
                    m.fetched_at = datetime.utcnow()
                    m.updated_at = datetime.utcnow()
                    await m.save()
            except Exception:
                pass

            # Always finalize status via repository (source of truth for status polling).
            try:
                await self.trends_service.repository.update_status(trend_signal_id, "completed")
            except Exception:
                pass

            # Fetch business profile for trend filtering (non-fatal)
            business = None
            try:
                business = await BusinessModel.find_one({"user_id": trend_signal.user_email})
            except Exception:
                pass

            # Persist detections for top items (so live feed can show them).
            # Do not gate this on repository.update_status success.
            try:
                for i, item in enumerate(top[:8]):
                        kw = item.get("keyword")
                        if not kw:
                            continue
                        if str(kw).strip().lower() == "all":
                            continue
                        
                        # Filter out irrelevant trends (sports, politics, etc.) for specific business types
                        business_type = getattr(business, "business_type", None) or trend_signal.niche or "business"
                        if not TrendSimplificationService.is_relevant_for_business(kw, business_type, trend_signal.niche):
                            logger.info(f"🚫 Filtered irrelevant trend '{kw}' for {business_type} business")
                            continue
                        
                        s = float(item.get("score", 0.0) or 0.0)
                        impact = "LOW"
                        if s >= 70:
                            impact = "HIGH"
                        elif s >= 40:
                            impact = "MEDIUM"

                        # Detect the actual trend category from keyword content
                        detected_category = self._detect_trend_category(kw)
                        
                        det = TrendDetectionModel(
                            user_id=trend_signal.user_email,
                            keyword=kw,
                            niche=detected_category,  # Use detected category, not user's business niche
                            location=trend_signal.location,
                            trend_signal_id=str(trend_signal_id),
                            # Compatibility fields (no time-series): use score as a 0..100 proxy.
                            z_score=round(s / 20.0, 3),  # 0..5-ish
                            current_value=round(s, 2),
                            expected_value=50.0,
                            impact_level=impact,
                            detected_at=datetime.utcnow(),
                            timeframe="fast_current",
                            is_recent=True,
                            is_real_social=bool(item.get("is_real_social", False)),
                            is_real_saturation=False,
                            is_real_events=False,
                            status="notified" if i == 0 else "new",
                            expires_at=datetime.utcnow() + timedelta(hours=72),
                            niche_match_score=None,
                            # Populate rising_queries with other keywords from the same scan for UI title enhancement
                            rising_queries=[k for k in top_keywords if k != kw][:5],
                            recommendations={
                                "rising_queries": [k for k in top_keywords if k != kw][:5]
                            }
                        )
                        await det.insert()
                        # Best-effort actionable payload per trend (non-fatal; does not change required contracts)
                        try:
                            business_type = getattr(business, "business_type", None) or trend_signal.niche or "business"
                            tone = getattr(business, "tone_of_voice", None) or getattr(business, "brand_tone", None) or "Professional"

                            # Derive primary platform (prefer real bias if present)
                            platform = "instagram"
                            try:
                                bias = getattr(trend_signal, "platform_bias", None) or {}
                                if isinstance(bias, dict) and bias:
                                    best = max(bias.items(), key=lambda kv: float(kv[1] or 0.0))
                                    if best and str(best[0]).strip().lower() in {"tiktok", "instagram", "facebook"}:
                                        platform = str(best[0]).strip().lower()
                            except Exception:
                                platform = "instagram"

                            payload = await self.actionable_rec_service.generate(
                                location=str(trend_signal.location or "GLOBAL"),
                                trend_keywords=[str(kw)]
                                + [
                                    str(x.get("keyword"))
                                    for x in top[:10]
                                    if x.get("keyword") and str(x.get("keyword")).strip().lower() != str(kw).strip().lower()
                                ],
                                business_type=str(business_type),
                                platform=platform,
                                brand_tone=TrendActionableRecommendationService._derive_brand_tone(str(tone)),
                                age_group="18-34",
                                niche=str(trend_signal.niche or "general"),
                                budget="Medium",
                            )

                            existing = (await TrendDetectionModel.find_one({"_id": det.id})).recommendations or {}
                            existing.update(payload)
                            await TrendDetectionModel.find_one({"_id": det.id}).update({"$set": {"recommendations": existing}})
                        except Exception:
                            pass
            except Exception as e:
                # Do not fail the scan, but log so we can debug missing cards.
                logger.warning("Failed persisting detections (non-fatal): %s", str(e), exc_info=True)

            # Notifications:
            # - low-priority discovery notifications for top keywords (deduped 24h)
            # - high-priority opportunity notification for best keyword with campaign prefill
            try:
                now = datetime.utcnow()
                cutoff = now - timedelta(hours=24)
                for item in top[:5]:
                    kw = (item.get("keyword") or "").strip()
                    if not kw:
                        continue
                    kw_norm = kw.lower()
                    existing = await NotificationModel.find_one(
                        NotificationModel.user_id == trend_signal.user_email,
                        NotificationModel.type == NotificationType.TREND_DISCOVERED,
                        NotificationModel.metadata["keyword_norm"] == kw_norm,
                        NotificationModel.created_at >= cutoff,
                    )
                    if existing:
                        continue
                    await self.notification_service.create_and_send(
                        user_id=trend_signal.user_email,
                        type=NotificationType.TREND_DISCOVERED,
                        title="New trend discovered",
                        message=f"Trending now: '{kw}' in {trend_signal.location}.",
                        related_entity_id=str(trend_signal_id),
                        metadata={
                            "sub_type": "trend_discovered",
                            "keyword": kw,
                            "keyword_norm": kw_norm,
                            "niche": trend_signal.niche,
                            "location": trend_signal.location,
                            "trend_id": str(trend_signal_id),
                            "action": "open_trends",
                        },
                        priority=1,
                    )

                # High-priority: best trend gets actionable campaign launch
                if top:
                    best = (top[0].get("keyword") or "").strip()
                    if best:
                        # Dedupe: do not spam identical "Current Trend Opportunity" notifications if the
                        # scheduler runs frequently or multiple scans overlap.
                        # Default window: 60 minutes (override via config.TREND_SPIKE_DEDUPE_MINUTES).
                        try:
                            dedupe_minutes = int(getattr(app_config, "TREND_SPIKE_DEDUPE_MINUTES", 60) or 60)
                        except Exception:
                            dedupe_minutes = 60
                        dedupe_cutoff = now - timedelta(minutes=max(1, dedupe_minutes))
                        best_norm = best.lower()

                        existing_spike = await NotificationModel.find_one(
                            NotificationModel.user_id == trend_signal.user_email,
                            NotificationModel.type == NotificationType.TREND_SPIKE,
                            NotificationModel.metadata["sub_type"] == "trend",
                            NotificationModel.metadata["keyword_norm"] == best_norm,
                            NotificationModel.created_at >= dedupe_cutoff,
                        )

                        if not existing_spike:
                            await self.notification_service.create_and_send(
                                user_id=trend_signal.user_email,
                                type=NotificationType.TREND_SPIKE,
                                title="Current Trend Opportunity",
                                message=f"Current trend: '{best}' is hot right now in {trend_signal.location}. Launch a campaign?",
                                related_entity_id=str(trend_signal_id),
                                metadata={
                                    "sub_type": "trend",
                                    "trend_id": str(trend_signal_id),
                                    "keyword": best,
                                    "keyword_norm": best_norm,
                                    "niche": trend_signal.niche,
                                    "location": trend_signal.location,
                                    "z_score": round(float(top[0]["score"]) / 20.0, 1),
                                    "action": "launch_campaign",
                                    "campaign_prefill": {
                                        "keyword": best,
                                        "niche": trend_signal.niche,
                                        "location": trend_signal.location,
                                        "suggested_platforms": ["instagram"] if ig_connected else [],
                                        "hashtags": self._generate_relevant_hashtags(best, trend_signal.niche),
                                        "lifecycle_stage": "Current",
                                    },
                                },
                                priority=10,
                            )
            except Exception:
                pass

            duration_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)
            emit_event(
                "trends.pipeline.completed",
                trend_id=str(trend_signal_id),
                user_id=str(trend_signal.user_email),
                status="completed",
                provider="fast_current",
                fallback_from=None,
                timeline_points=0,
                spikes_detected=0,
                duration_ms=duration_ms,
            )

            # Non-blocking: trigger AI analysis generation (best-effort; never delays pipeline).
            try:
                from application.services.trend_ai_analysis_service import TrendAIAnalysisService

                asyncio.create_task(
                    TrendAIAnalysisService().generate_analysis(
                        trend_id=str(trend_signal_id),
                        user_id=str(trend_signal.user_email),
                    )
                )
            except Exception:
                pass
            return
            
            social_service = SocialTrendService()
            saturation_service = SaturationService()
            lifecycle_service = LifecycleClassificationService()
            prediction_service = TrendPredictionService()
            profit_service = ProfitProxyService()
            
            # Fetch the data
            success = await self.trends_service.process_trend_signal(trend_signal_id, timeframe)
            
            # Refresh trend signal after processing
            trend_signal = await self.trends_service.get_trend_by_id(trend_signal_id)
            if not trend_signal:
                logger.error("Trend signal %s disappeared during processing", trend_signal_id)
                return

            if not success:
                # Determine error type to decide retry strategy
                err = (trend_signal.error_message or "").lower()
                if "rate_limited" in err or "429" in err or "too many requests" in err:
                    emit_event(
                        "trends.provider.rate_limited",
                        trend_id=str(trend_signal_id),
                        user_id=str(trend_signal.user_email),
                        provider=getattr(trend_signal, "provider", None),
                        fallback_from=getattr(trend_signal, "fallback_from", None),
                        error=str(trend_signal.error_message or ""),
                    )
                    logger.warning("Google Trends rate limited for %s. Queueing retry.", trend_signal.user_email)
                    await self.trends_service.repository.update_status(
                        trend_signal_id,
                        "failed",
                        "rate_limited",
                        progress_step="Rate limited — retry queued."
                    )
                    try:
                        # Deduplicate retry jobs: avoid multiple pending/running jobs for same trend_id.
                        existing = await TrendRetryJobModel.find_one(
                            TrendRetryJobModel.trend_id == str(trend_signal_id),
                            TrendRetryJobModel.status.in_(
                                [TrendRetryJobStatus.PENDING, TrendRetryJobStatus.RUNNING]
                            ),
                        )
                        if existing:
                            logger.info(
                                "Retry job already exists for trend_id=%s (status=%s). Skipping enqueue.",
                                trend_signal_id,
                                existing.status,
                            )
                        else:
                            await enqueue_trend_retry(
                                trend_id=str(trend_signal_id),
                                user_email=trend_signal.user_email,
                                reason="rate_limited",
                                max_attempts=3,
                            )
                            emit_event(
                                "trends.retry.enqueued",
                                trend_id=str(trend_signal_id),
                                user_id=str(trend_signal.user_email),
                                reason="rate_limited",
                                max_attempts=3,
                            )
                    except Exception as qerr:
                        logger.error("Failed to enqueue retry for %s: %s", trend_signal_id, qerr)
                else:
                    logger.warning("Failed to fetch Google Trends data for %s", trend_signal.user_email)
                    await self.trends_service.repository.update_status(
                        trend_signal_id, 
                        "failed", 
                        "Failed to fetch Google Trends data"
                    )
                # Pipeline failed early
                duration_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)
                emit_event(
                    "trends.pipeline.completed",
                    trend_id=str(trend_signal_id),
                    user_id=str(trend_signal.user_email),
                    status="failed",
                    provider=getattr(trend_signal, "provider", None),
                    fallback_from=getattr(trend_signal, "fallback_from", None),
                    timeline_points=0,
                    spikes_detected=0,
                    duration_ms=duration_ms,
                    error=str(trend_signal.error_message or ""),
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

            # Observability: point density matters for spike detection.
            # Serp providers may return weekly granularity for some windows, which can
            # fall below min_data_points and lead to 0 spikes even when the trend changes.
            try:
                series_lens = {k: (len(v) if isinstance(v, list) else 0) for k, v in (data_streams or {}).items()}
                logger.info(
                    "Trend series lengths for %s: points=%s (min_data_points=%d, rolling_window=%d, threshold=%.2f)",
                    trend_signal_id,
                    series_lens,
                    int(getattr(self.config, "min_data_points", 5)),
                    int(getattr(self.config, "rolling_window", 14)),
                    float(getattr(self.config, "threshold", 2.0)),
                )
            except Exception:
                pass
            
            all_spikes = []
            top_keyword = None
            max_z = -1.0
            max_interest = 0
            keyword_scores = {}  # Track all keywords with their z-scores and interest

            # Step 2: Heat Score Calculation & Trend Detection
            await self.trends_service.repository.update_status(
                trend_signal_id, "processing", progress_step="Finding trends..."
            )
            # Window filter: detection runs on full series (may include extended history for SerpAPI),
            # but we only persist spikes within the originally requested window.
            window_start = None
            try:
                tf = (timeframe or "").strip().lower()
                if tf.endswith("d"):
                    days = int(tf.replace("d", "") or "0")
                    window_start = datetime.utcnow() - timedelta(days=max(days, 0))
                elif tf == "24h":
                    window_start = datetime.utcnow() - timedelta(days=1)
                elif tf == "7d":
                    window_start = datetime.utcnow() - timedelta(days=7)
                elif tf == "30d":
                    window_start = datetime.utcnow() - timedelta(days=30)
                elif tf == "90d":
                    window_start = datetime.utcnow() - timedelta(days=90)
            except Exception:
                window_start = None

            for keyword, values in data_streams.items():
                if not isinstance(values, list) or len(values) < getattr(self.config, "min_data_points", 5):
                    logger.warning(
                        "Insufficient points for spike detection: trend_id=%s keyword=%s points=%s min=%s",
                        trend_signal_id,
                        keyword,
                        (len(values) if isinstance(values, list) else "n/a"),
                        getattr(self.config, "min_data_points", 5),
                    )
                # Temporary diagnostics (gated): print max rolling z-score per keyword.
                # Enable with RAAMP_DEBUG_ZSCORES=1
                if os.getenv("RAAMP_DEBUG_ZSCORES", "").strip() in ("1", "true", "True", "yes", "YES"):
                    try:
                        import pandas as pd

                        s = pd.Series([float(v) for v in values])
                        rolling_mean = s.rolling(window=self.config.rolling_window, min_periods=1).mean()
                        rolling_std = s.rolling(window=self.config.rolling_window, min_periods=1).std()
                        eps = 1e-9
                        z_scores = (s - rolling_mean) / (rolling_std + eps)
                        zmax = float(z_scores.max()) if len(z_scores) else 0.0
                        logger.info(
                            "Z-SCORE DIAGNOSTIC: keyword=%r max_z=%.3f threshold=%.2f points=%d",
                            keyword,
                            zmax,
                            float(getattr(self.config, "threshold", 2.0)),
                            len(values),
                        )
                    except Exception as _e:
                        logger.info(
                            "Z-SCORE DIAGNOSTIC: keyword=%r max_z=UNKNOWN threshold=%.2f points=%s",
                            keyword,
                            float(getattr(self.config, "threshold", 2.0)),
                            (len(values) if isinstance(values, list) else "n/a"),
                        )
                spikes = TrendDetectionEngine.detect_spikes(
                    dates=dates,
                    values=values,
                    keyword=keyword,
                    niche=trend_data.niche,
                    location=trend_data.location,
                    config=self.config
                )
                if window_start is not None:
                    before = len(spikes)
                    spikes = [s for s in spikes if getattr(s, "timestamp", None) and s.timestamp >= window_start]
                    after = len(spikes)
                    if before != after:
                        logger.info(
                            "Filtered to %d spikes within requested window (keyword=%s, before=%d, window_start=%s)",
                            after,
                            keyword,
                            before,
                            window_start.isoformat() + "Z" if window_start else None,
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

            # Option C notifications: emit low-priority "trend discovered" notifications for newly surfaced
            # high-signal keywords, distinct from spike/opportunity alerts.
            # Dedupe: one notification per (user, keyword) within 24h.
            try:
                from infrastructure.database.models.notification_model import NotificationModel, NotificationType

                # Build a set of keywords that already produced recent spikes (we'll avoid double-notifying discovery).
                spiked_recent = set()
                for s in all_spikes:
                    if bool(getattr(s, "is_recent", False)):
                        spiked_recent.add((s.keyword or "").strip().lower())

                ranked = sorted(
                    keyword_scores.items(),
                    key=lambda kv: (
                        float(kv[1].get("z_score", 0.0)),
                        float(kv[1].get("interest", 0.0)),
                    ),
                    reverse=True,
                )
                discovered_candidates = [k for k, _ in ranked[:5] if isinstance(k, str) and k.strip()]

                now = datetime.utcnow()
                cutoff = now - timedelta(hours=24)

                for kw in discovered_candidates:
                    kw_norm = kw.strip().lower()
                    if not kw_norm:
                        continue
                    if kw_norm in spiked_recent:
                        continue

                    existing = await NotificationModel.find_one(
                        NotificationModel.user_id == trend_signal.user_email,
                        NotificationModel.type == NotificationType.TREND_DISCOVERED,
                        NotificationModel.metadata["keyword_norm"] == kw_norm,
                        NotificationModel.created_at >= cutoff,
                    )
                    if existing:
                        continue

                    await self.notification_service.create_and_send(
                        user_id=trend_signal.user_email,
                        type=NotificationType.TREND_DISCOVERED,
                        title="New trend discovered",
                        message=f"New trend found for you: '{kw}' in {trend_signal.location}.",
                        related_entity_id=str(trend_signal_id),
                        metadata={
                            "sub_type": "trend_discovered",
                            "keyword": kw,
                            "keyword_norm": kw_norm,
                            "niche": trend_signal.niche,
                            "location": trend_signal.location,
                            "trend_id": str(trend_signal_id),
                            "action": "open_trends",
                        },
                        priority=1,
                    )
            except Exception as e:
                logger.info("Discovery notification step skipped (non-fatal): %s", str(e))
            
            # Step 3: Persona Mapping & Social Enrichment
            await self.trends_service.repository.update_status(
                trend_signal_id, "processing", progress_step="Checking social media..."
            )

            # Load business once for specialty-based boosts (best-effort).
            business = None
            try:
                business = await BusinessModel.find_one({"user_id": trend_signal.user_email})
            except Exception:
                business = None

            # Step 3b: Event Signals (Google News RSS) — bounded, cached, non-fatal
            is_real_events = False
            _event_fields_written = False
            try:
                from application.services.event_signal_service import EventSignalService

                await self.trends_service.repository.update_status(
                    trend_signal_id, "processing", progress_step="Checking news..."
                )

                ranked = sorted(
                    keyword_scores.items(),
                    key=lambda kv: (
                        float(kv[1].get("z_score", 0.0)),
                        float(kv[1].get("interest", 0.0)),
                    ),
                    reverse=True,
                )
                top_keywords = [k for k, _ in ranked[:3] if k]

                if top_keywords:
                    event_service = EventSignalService()
                    event_signal = await event_service.get_event_signal(
                        keywords=top_keywords,
                        location=trend_signal.location,
                        niche=trend_signal.niche,
                        specialties=list(getattr(business, "specialties", []) or [])[:3] if business else None,
                        max_keywords=3,
                    )
                    await self.trends_service.repository.update_event_fields(
                        trend_signal_id,
                        event_score=event_signal.get("event_score", 0.0),
                        event_items=event_signal.get("event_items", []),
                        is_real_events=bool(event_signal.get("is_real_events", False)),
                    )
                    is_real_events = bool(event_signal.get("is_real_events", False))
                    _event_fields_written = True
            except Exception as e:
                logger.warning("Event signal step failed (non-fatal): %s", str(e))
            finally:
                # Ensure provenance flag is always present on TrendSignal, even if the event step errors or returns no keywords.
                if not _event_fields_written:
                    try:
                        await self.trends_service.repository.update_event_fields(
                            trend_signal_id,
                            event_score=None,
                            event_items=None,
                            is_real_events=False,
                        )
                    except Exception:
                        # Non-fatal: do not block the scan on observability/provenance persistence
                        pass

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
                    logger.warning(
                        "Instagram engagement fetch failed for '%s': %s. Falling back to semantic analysis.",
                        top_keyword,
                        str(e),
                    )
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
                # Step 4: Campaign Suggestion & ROI Prediction
                await self.trends_service.repository.update_status(
                    trend_signal_id, "processing", progress_step="Almost done..."
                )
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
            
            await self.trends_service.repository.update_status(
                trend_signal_id, 
                "completed"
            )
            
            # Log Activity (Non-blocking)
            asyncio.create_task(log_activity(
                business_id=trend_signal.user_email,
                event_type="scan_completed",
                title="Market Scan Completed",
                subtitle=f"Intelligence refreshed for {trend_signal.niche}"
            ))
            
            logger.info("PIPELINE SUCCESS: Signal %s completed for user %s", trend_signal_id, trend_signal.user_email)

            # Observability: pipeline completion event.
            duration_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)
            provider_used = getattr(trend_signal, "provider", None)
            fallback_from = getattr(trend_signal, "fallback_from", None)
            timeline_points = len(dates) if isinstance(dates, list) else 0
            emit_event(
                "trends.pipeline.completed",
                trend_id=str(trend_signal_id),
                user_id=str(trend_signal.user_email),
                status="completed",
                provider=provider_used,
                fallback_from=fallback_from,
                timeline_points=timeline_points,
                spikes_detected=len(all_spikes),
                duration_ms=duration_ms,
            )

            # Non-blocking: trigger AI analysis generation (best-effort; never delays pipeline).
            try:
                from application.services.trend_ai_analysis_service import TrendAIAnalysisService

                asyncio.create_task(
                    TrendAIAnalysisService().generate_analysis(
                        trend_id=str(trend_signal_id),
                        user_id=str(trend_signal.user_email),
                    )
                )
            except Exception:
                pass
            
            # 6. Notify User
            if all_spikes:
                await self._notify_spikes(
                    trend_data.user_email,
                    all_spikes,
                    timeframe,
                    trend_id=str(trend_signal_id),
                    platform_bias=getattr(trend_signal, "platform_bias", None),
                    hashtags=getattr(trend_signal, "hashtags", None),
                    lifecycle_stage=getattr(trend_signal, "lifecycle_stage", None),
                    is_real_social=bool(getattr(trend_signal, "is_real_social", False)),
                    is_real_saturation=bool(getattr(trend_signal, "is_real_saturation", False)),
                    is_real_events=bool(is_real_events),
                )
                
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
            # Observability: pipeline failure event (unhandled exception)
            duration_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)
            emit_event(
                "trends.pipeline.completed",
                trend_id=str(trend_signal_id),
                user_id=str(getattr(trend_signal, "user_email", "")),
                status="failed",
                provider=getattr(trend_signal, "provider", None),
                fallback_from=getattr(trend_signal, "fallback_from", None),
                timeline_points=0,
                spikes_detected=0,
                duration_ms=duration_ms,
                error=str(e),
            )

    async def run_detection_for_user(self, user: UserModel, override_niche: str = None):
        """Run full detection cycle for a specific user (legacy wrapper)"""
        trend_signal = await self.initialize_detection_signal(user, override_niche)
        await self.execute_detection_pipeline(trend_signal.id)

    async def _notify_spikes(
        self,
        user_email: str,
        spikes: List[TrendSpike],
        timeframe: str = "30d",
        *,
        trend_id: Optional[str] = None,
        platform_bias: Optional[dict] = None,
        hashtags: Optional[List[str]] = None,
        lifecycle_stage: Optional[str] = None,
        is_real_social: bool = False,
        is_real_saturation: bool = False,
        is_real_events: bool = False,
    ):
        """Create notifications and store persistent records for detected spikes"""
        # Best-effort: load business specialties for niche match scoring.
        business_specialties: List[str] = []
        try:
            business = await BusinessModel.find_one({"user_id": user_email})
            business_specialties = list(getattr(business, "specialties", []) or []) if business else []
            business_specialties = [s for s in business_specialties if isinstance(s, str) and s.strip()]
        except Exception:
            business_specialties = []

        def _niche_match_score(keyword: str, niche: str, specialties: List[str]) -> float:
            """
            Heuristic 0..1 confidence that the keyword matches the user's niche/specialties.
            Production intent: avoid promoting irrelevant spikes.
            """
            try:
                import re

                def toks(s: str) -> set[str]:
                    s = (s or "").lower()
                    parts = re.split(r"[^a-z0-9]+", s)
                    return {p for p in parts if p and len(p) >= 3}

                kw = toks(keyword)
                if not kw:
                    return 0.0
                niche_t = toks(niche)
                spec_t = set()
                for sp in specialties or []:
                    spec_t |= toks(sp)
                universe = niche_t | spec_t
                if not universe:
                    return 0.5  # unknown; don't hard-fail relevance
                inter = kw & universe
                # Weighted: specialty overlap matters a bit more than niche label match
                spec_inter = kw & spec_t
                niche_inter = kw & niche_t
                score = 0.0
                score += 0.6 * (len(spec_inter) / max(1, len(spec_t))) if spec_t else 0.0
                score += 0.4 * (len(niche_inter) / max(1, len(niche_t))) if niche_t else 0.0
                # Bound
                return max(0.0, min(1.0, float(score)))
            except Exception:
                return 0.5

        for spike in spikes:
            # Filter out irrelevant trends before creating detection records
            business_type = spike.niche or "business"
            if not TrendSimplificationService.is_relevant_for_business(spike.keyword, business_type, spike.niche):
                logger.info(f"🚫 Filtered irrelevant spike '{spike.keyword}' for {business_type} business")
                continue
            
            # Determine impact level
            impact = "LOW"
            if spike.z_score > 4.0:
                impact = "HIGH"
            elif spike.z_score > 2.5:
                impact = "MEDIUM"
                
            # 1. Store persistent detection record
            try:
                from infrastructure.database.models.trend_detection_model import TrendDetectionStatus
            except Exception:
                TrendDetectionStatus = None  # type: ignore

            exp_at = None
            try:
                exp_at = (spike.timestamp or datetime.utcnow()) + timedelta(hours=72)
            except Exception:
                exp_at = datetime.utcnow() + timedelta(hours=72)

            # Detect the actual trend category from keyword content
            detected_category = self._detect_trend_category(spike.keyword)
            
            detection = TrendDetectionModel(
                user_id=user_email,
                keyword=spike.keyword,
                niche=detected_category,  # Use detected category, not spike.niche (which is user's business niche)
                location=spike.location,
                trend_signal_id=str(trend_id) if trend_id else None,
                z_score=spike.z_score,
                current_value=spike.current_value,
                expected_value=spike.expected_value,
                impact_level=impact,
                detected_at=spike.timestamp,
                timeframe=timeframe,
                is_recent=bool(getattr(spike, "is_recent", False)),
                is_real_social=bool(is_real_social),
                is_real_saturation=bool(is_real_saturation),
                is_real_events=bool(is_real_events),
                status=(TrendDetectionStatus.NOTIFIED if (TrendDetectionStatus and bool(getattr(spike, "is_recent", False))) else (TrendDetectionStatus.NEW if TrendDetectionStatus else "new")),
                expires_at=exp_at,
                niche_match_score=_niche_match_score(spike.keyword, spike.niche, business_specialties),
            )
            await detection.insert()
            
            # 2. Trigger notification (only for recent spikes)
            if not bool(getattr(spike, "is_recent", False)):
                continue
            title = "🚀 Emerging Trend Detected!"
            message = f"Trend alert: '{spike.keyword}' is spiking in {spike.location} for the {spike.niche} niche!"

            # Convert platform_bias dict -> ordered list of platform names (highest score first)
            suggested_platforms: List[str] = []
            try:
                if isinstance(platform_bias, dict):
                    ranked = sorted(
                        platform_bias.items(),
                        key=lambda kv: float(kv[1] or 0.0),
                        reverse=True,
                    )
                    suggested_platforms = [k for k, _ in ranked if k]
            except Exception:
                suggested_platforms = []

            top_hashtags: List[str] = []
            try:
                if isinstance(hashtags, list):
                    top_hashtags = [h for h in hashtags if isinstance(h, str) and h.strip()][:10]
            except Exception:
                top_hashtags = []

            z_rounded = round(float(spike.z_score or 0.0), 1)

            metadata = {
                # keep legacy discriminator for existing preference gating + UI behaviors
                "sub_type": "trend",
                # Phase 2 required payload
                "trend_id": str(trend_id) if trend_id else None,
                "keyword": spike.keyword,
                "keyword_norm": (spike.keyword or "").strip().lower(),
                "niche": spike.niche,
                "location": spike.location,
                "z_score": z_rounded,
                "action": "launch_campaign",
                "campaign_prefill": {
                    "keyword": spike.keyword,
                    "niche": spike.niche,
                    "location": spike.location,
                    "suggested_platforms": suggested_platforms,
                    "hashtags": top_hashtags,
                    "lifecycle_stage": lifecycle_stage,
                },
                # extra context (safe)
                "impact_level": impact,
                "detected_at": spike.timestamp.isoformat(),
                "platform_bias": platform_bias or {},
                "hashtags": top_hashtags,
                "lifecycle_stage": lifecycle_stage,
            }

            # Dedupe: prevent repeated "spike" notifications for the same keyword in a short window.
            try:
                dedupe_minutes = int(getattr(app_config, "TREND_SPIKE_DEDUPE_MINUTES", 60) or 60)
            except Exception:
                dedupe_minutes = 60
            dedupe_cutoff = datetime.utcnow() - timedelta(minutes=max(1, dedupe_minutes))
            kw_norm = (spike.keyword or "").strip().lower()
            existing_spike = None
            try:
                from infrastructure.database.models.notification_model import NotificationModel

                existing_spike = await NotificationModel.find_one(
                    NotificationModel.user_id == user_email,
                    NotificationModel.type == NotificationType.TREND_SPIKE,
                    NotificationModel.metadata["sub_type"] == "trend",
                    NotificationModel.metadata["keyword_norm"] == kw_norm,
                    NotificationModel.created_at >= dedupe_cutoff,
                )
            except Exception:
                existing_spike = None

            if not existing_spike:
                await self.notification_service.create_and_send(
                    user_id=user_email,
                    type=NotificationType.TREND_SPIKE,
                    title=title,
                    message=message,
                    related_entity_id=str(trend_id) if trend_id else None,
                    metadata=metadata
                )
            
            # Log Activity (Non-blocking)
            asyncio.create_task(log_activity(
                business_id=user_email,
                event_type="trend_detected",
                title="Niche Trend Detected",
                subtitle=f"Opportunity spike for '{spike.keyword}'"
            ))
            
            logger.info("Notification sent and spike stored for %s: %s", user_email, spike.keyword)

    async def _check_watchlist_alerts(
        self,
        user_email: str,
        keyword: str,
        velocity: float,
        saturation: float,
        profit_score: float | None = None,
    ):
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
                prev_saturation = float(getattr(watchlist_item, "last_saturation", 0.0) or 0.0)
                watchlist_item.last_velocity = velocity
                watchlist_item.last_saturation = saturation
                watchlist_item.last_arbitrage_score = round((velocity * 100) / max(1, saturation), 2)
                if profit_score is not None:
                    watchlist_item.last_profit_score = float(profit_score or 0.0)
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

                # Profit score threshold alert (0-100)
                ps = None
                try:
                    if profit_score is not None:
                        ps = float(profit_score)
                except Exception:
                    ps = None
                if ps is not None and getattr(watchlist_item, "alert_on_profit_score", True):
                    thr = float(getattr(watchlist_item, "profit_score_threshold", 75.0) or 75.0)
                    if ps >= thr:
                        await self.notification_service.create_and_send(
                            user_id=user_email,
                            type=NotificationType.ALERT,
                            title="💰 Watchlist Alert: Opportunity Threshold",
                            message=f"Tracked trend '{keyword}' opportunity score is {ps:.0f}/100 (≥ {thr:.0f}).",
                            metadata={
                                "sub_type": "watchlist_profit_score",
                                "keyword": keyword,
                                "profit_score": ps,
                                "threshold": thr,
                            },
                        )

                # Saturation drop alert (less competition)
                if getattr(watchlist_item, "alert_on_saturation_drop", False):
                    drop_thr = float(getattr(watchlist_item, "saturation_drop_threshold", 10.0) or 10.0)
                    if (prev_saturation - float(saturation or 0.0)) >= drop_thr:
                        await self.notification_service.create_and_send(
                            user_id=user_email,
                            type=NotificationType.ALERT,
                            title="📉 Watchlist Alert: Competition Dropped",
                            message=f"Tracked trend '{keyword}' competition dropped ({prev_saturation:.0f} → {float(saturation or 0.0):.0f}).",
                            metadata={
                                "sub_type": "watchlist_saturation_drop",
                                "keyword": keyword,
                                "previous_saturation": prev_saturation,
                                "saturation": saturation,
                                "drop_threshold": drop_thr,
                            },
                        )
        except Exception as e:
            logger.error("Error checking watchlist alerts: %s", e)
