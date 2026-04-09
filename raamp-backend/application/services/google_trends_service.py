# Application Layer - Google Trends Service
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pytrends.request import TrendReq
import asyncio
from functools import partial
import hashlib
import json

from domain.entities.trend_signal import TrendSignal
from domain.repositories.trend_signal_repository import ITrendSignalRepository
from infrastructure.repositories.trend_signal_repository import TrendSignalRepository
from application.services.trends_providers.selector import TrendsProviderSelector
from infrastructure.database.models.trend_cache_model import TrendCacheModel


logger = logging.getLogger(__name__)


class GoogleTrendsService:
    """Service for fetching and processing Google Trends data"""
    
    # Country name to ISO 3166-1 alpha-2 code mapping
    LOCATION_CODES = {
        "pakistan": "PK",
        "india": "IN",
        "united states": "US",
        "united kingdom": "GB",
        "canada": "CA",
        "australia": "AU",
        "germany": "DE",
        "france": "FR",
        "italy": "IT",
        "spain": "ES",
        "brazil": "BR",
        "mexico": "MX",
        "japan": "JP",
        "south korea": "KR",
        "china": "CN",
        "singapore": "SG",
        "malaysia": "MY",
        "indonesia": "ID",
        "thailand": "TH",
        "philippines": "PH",
        "vietnam": "VN",
        "saudi arabia": "SA",
        "united arab emirates": "AE",
        "turkey": "TR",
        "egypt": "EG",
        "south africa": "ZA",
        "nigeria": "NG",
        "kenya": "KE",
        "global": "",
    }
    
    # Niche-to-keywords mapping (keep as general topics, not "X trends" phrases).
    NICHE_KEYWORDS = {
        # Fashion needs broader seeds to reliably yield related/rising queries.
        # Keep these as high-level topics people actually search (not "X trends" phrases).
        "fashion": [
            "outfit ideas",
            "streetwear",
            "modest fashion",
            "summer outfits",
            "winter outfits",
            "mens fashion",
            "womens fashion",
            "capsule wardrobe",
            "sneakers",
            "fashion accessories",
            "fashion brands",
            "online shopping",
        ],
        "food": ["recipes", "restaurant near me"],
        "tech": ["technology", "AI"],
        "crypto": ["cryptocurrency", "bitcoin"],
        "fitness": ["fitness", "workout"],
        "beauty": ["beauty", "makeup"],
        "travel": ["travel", "vacation"],
        "gaming": ["gaming", "video games"],
        "real_estate": ["real estate", "property"],
        "automotive": ["cars", "vehicles"],
    }
    
    def __init__(self, repository: Optional[ITrendSignalRepository] = None):
        self.repository = repository or TrendSignalRepository()
        self.pytrends = None
        self.cache_ttl_minutes = 60  # Cache for 1 hour
        self.last_request_time = datetime.min
        self.min_request_interval = 2.0  # Minimum 2 seconds between requests
        self._provider_selector = TrendsProviderSelector()
    
    def _get_pytrends(self) -> TrendReq:
        """Get or create PyTrends instance with resilient settings and urllib3 v2 fix"""
        if self.pytrends is None:
            import requests
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            
            # Configure custom session with robust retry logic
            session = requests.Session()
            
            # Urllib3 v2.0+ uses 'allowed_methods', older versions used 'method_whitelist'
            # We explicitly configure it here to avoid PyTrends internal default which might be outdated
            retry_strategy = Retry(
                total=5,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "OPTIONS"] # Modern replacement for method_whitelist
            )
            
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("https://", adapter)
            session.mount("http://", adapter)
            
            # Initialize TrendReq with our custom session
            # timeout=(connect_timeout, read_timeout)
            # Do NOT pass retries/backoff_factor - let it use our custom session with fixed Retry config
            self.pytrends = TrendReq(
                hl='en-US', 
                tz=360, 
                timeout=(10, 25), 
                requests_args={'verify': True}
            )
            
            # Monkey-patch the session into the instance to ensure our retry strategy is used
            self.pytrends.requests = session
            
        return self.pytrends
    
    def _get_keywords_for_niche(self, niche: str, category: str) -> List[str]:
        """Get relevant keywords based on niche and category"""
        base_keywords = self.NICHE_KEYWORDS.get(niche.lower(), [niche])
        
        # Treat "all" as a UI filter value, not a keyword.
        category_norm = (category or "").strip()
        if category_norm.lower() == "all":
            category_norm = ""

        # Add category-specific keyword
        if category_norm and category_norm.lower() not in [kw.lower() for kw in base_keywords]:
            # For industry discovery we want a slightly larger seed list.
            keywords = [category_norm] + base_keywords[:5]  # cap to 6 total
        else:
            # Return up to 6 seeds (industry_trends endpoint will cap again).
            keywords = base_keywords[:6]
        
        return keywords
    
    def convert_location_to_code(self, location: str) -> str:
        """
        Convert country name to ISO 3166-1 alpha-2 code for Google Trends API.
        
        Args:
            location: Country name (e.g., "Pakistan", "United States")
            
        Returns:
            ISO alpha-2 code (e.g., "PK", "US") or empty string for global
        """
        # If already a 2-letter code, return as-is
        if len(location) == 2 and location.isupper():
            return location
        
        # Convert to lowercase for lookup
        location_lower = location.lower().strip()
        
        # Check if it's in the mapping
        code = self.LOCATION_CODES.get(location_lower)
        if code is not None:
            return code
        
        # If not found, assume it might already be a code or return as-is
        logger.warning("Unknown location '%s', using as-is. Add to LOCATION_CODES if this is a country name.", location)
        return location
    
    def convert_timeframe_to_google_format(self, timeframe: str) -> str:
        """
        Convert user-friendly timeframe to Google Trends format.
        
        Args:
            timeframe: User timeframe (24h, 7d, 30d, 90d)
            
        Returns:
            Google Trends timeframe string
        """
        timeframe_map = {
            "24h": "now 1-d",
            "7d": "now 7-d",
            "30d": "today 1-m",
            "90d": "today 3-m"
        }
        
        return timeframe_map.get(timeframe, "today 3-m")  # Default to 90d
    
    def _get_cache_key(self, keywords: List[str], location: str, timeframe: str) -> str:
        """Generate cache key from request parameters"""
        key_data = {
            "keywords": sorted(keywords),  # Sort to ensure consistent hashing
            "location": location,
            "timeframe": timeframe
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()

    async def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Get cached trends data from MongoDB if present and unexpired."""
        now = datetime.utcnow()
        doc = await TrendCacheModel.find_one(
            TrendCacheModel.namespace == "google_trends",
            TrendCacheModel.key == cache_key,
            TrendCacheModel.expires_at > now,
        )
        if not doc:
            return None
        try:
            return doc.value if isinstance(doc.value, dict) else None
        except Exception:
            return None

    async def _save_to_cache(self, cache_key: str, data: Dict, ttl_minutes: Optional[int] = None) -> None:
        """Upsert cached trends data into MongoDB with TTL expiry."""
        ttl = int(ttl_minutes or self.cache_ttl_minutes)
        ttl = max(1, min(ttl, 24 * 60))
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=ttl)
        try:
            await TrendCacheModel.find_one(
                TrendCacheModel.namespace == "google_trends",
                TrendCacheModel.key == cache_key,
            ).upsert(
                {"$set": {
                    "value": data,
                    "meta": {"ttl_minutes": ttl},
                    "expires_at": expires_at,
                    "created_at": now,
                }},
                on_insert=TrendCacheModel(
                    namespace="google_trends",
                    key=cache_key,
                    value=data,
                    meta={"ttl_minutes": ttl},
                    expires_at=expires_at,
                    created_at=now,
                ),
            )
        except Exception as e:
            # Cache failures must never break the pipeline.
            logger.warning("Trends DB cache write failed (non-fatal): %s", str(e))
    
    async def _rate_limit_delay(self):
        """Enforce minimum delay between requests"""
        time_since_last = (datetime.now() - self.last_request_time).total_seconds()
        if time_since_last < self.min_request_interval:
            delay = self.min_request_interval - time_since_last
            logger.info("Rate limiting: waiting %.2fs before next request", delay)
            await asyncio.sleep(delay)
        self.last_request_time = datetime.now()
    
    async def fetch_trends_data(
        self,
        keywords: List[str],
        location: str,
        timeframe: str = 'today 3-m',
        use_cache: bool = True
    ) -> Dict:
        """
        Fetch Google Trends data for given keywords and location with caching and rate limit handling
        """
        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key(keywords, location, timeframe)
            cached_data = await self._get_from_cache(cache_key)
            if cached_data:
                return cached_data

        # Delegate provider choice + fallback to selector (SerpAPI primary, pytrends fallback).
        res = await self._provider_selector.fetch_trends_data(
            keywords=keywords,
            location=location,
            timeframe=timeframe,
        )

        result = {
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

        # Service-level safety validation (defense-in-depth). Selector should already validate,
        # but we keep this to avoid persisting/caching malformed payloads.
        if result.get("success"):
            ok, err = self._validate_provider_payload(result)
            if not ok:
                result["success"] = False
                result["retryable"] = True
                result["error"] = err or "invalid_provider_payload"

        if res.success and use_cache:
            await self._save_to_cache(cache_key, result)

        return result

    def _validate_provider_payload(self, result: Dict) -> tuple[bool, Optional[str]]:
        """
        Validate provider payload shape + usefulness:
        - dates non-empty
        - every series length equals dates length
        - no series is entirely zero/None
        """
        si = result.get("search_interest") or {}
        dates = si.get("dates") if isinstance(si, dict) else None
        data = si.get("data") if isinstance(si, dict) else None
        if not isinstance(dates, list) or len(dates) == 0:
            return False, "invalid_payload_empty_dates"
        if not isinstance(data, dict) or len(data) == 0:
            return False, "invalid_payload_empty_data"

        n = len(dates)
        for k, values in data.items():
            if not isinstance(values, list) or len(values) != n:
                return False, f"invalid_payload_length_mismatch:{k}"
            cleaned = [v for v in values if v is not None]
            if not cleaned:
                return False, f"invalid_payload_all_null:{k}"
            # treat "all zeros" as non-useful
            try:
                if all(float(v) == 0.0 for v in cleaned):
                    return False, f"invalid_payload_all_zero:{k}"
            except Exception:
                # if parsing fails, consider it invalid
                return False, f"invalid_payload_non_numeric:{k}"
        return True, None
    
    async def create_trend_signal(
        self,
        user_email: str,
        niche: str,
        category: str,
        location: str,
        keywords: Optional[List[str]] = None,
        radius: Optional[str] = None,
        timeframe: str = "30d"
    ) -> TrendSignal:
        """
        Create a new trend signal record
        
        Args:
            user_email: Email of the user requesting trends
            niche: Business niche
            category: Sub-category within the niche
            location: Geographic location
            radius: Optional radius for geo-specific searches
            timeframe: Analysis timeframe (24h, 7d, 30d, 90d)
        
        Returns:
            Created TrendSignal entity
        """
        trend_signal = TrendSignal(
            id=None,
            user_email=user_email,
            niche=niche,
            category=category,
            location=location,
            radius=radius,
            keywords=list(keywords or []),
            fetch_status="pending"
        )
        
        return await self.repository.create(trend_signal)
    
    async def process_trend_signal(self, trend_id: str, timeframe: str = "30d") -> bool:
        """
        Process a trend signal by fetching Google Trends data
        
        Args:
            trend_id: ID of the trend signal to process
            timeframe: Analysis timeframe (24h, 7d, 30d, 90d)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the trend signal
            trend_signal = await self.repository.get_by_id(trend_id)
            if not trend_signal:
                logger.error("Trend signal %s not found", trend_id)
                return False
            
            # Update status to processing
            await self.repository.update_status(trend_id, "processing")
            
            # Get keywords for the niche, but prefer seeded keywords (e.g., specialties) if present.
            keywords = list(getattr(trend_signal, "keywords", None) or [])
            # If discovery ran, it should have prepended trending-now terms. Keep that priority
            # and ensure we keep only a small "top of funnel" set for time-series.
            # This reduces SerpAPI empty timelines when niche/specialty terms are off-signal.
            if len(keywords) > 8:
                keywords = keywords[:8]
            if not keywords:
                keywords = self._get_keywords_for_niche(trend_signal.niche, trend_signal.category)
            
            # Convert location to ISO code & timeframe to Google format
            location_code = self.convert_location_to_code(trend_signal.location)
            google_timeframe = self.convert_timeframe_to_google_format(timeframe)
            
            logger.info("Fetching trends: location='%s' -> code='%s', timeframe='%s' -> '%s'",
                       trend_signal.location, location_code, timeframe, google_timeframe)
            
            # Fetch trends data
            trends_data = await self.fetch_trends_data(
                keywords=keywords,
                location=location_code,
                timeframe=google_timeframe
            )
            
            if not trends_data["success"]:
                # Update status to failed
                await self.repository.update_status(
                    trend_id,
                    "failed",
                    trends_data["error"]
                )
                return False
            
            # Update trend signal with fetched data
            success = await self.repository.update_trend_data(
                trend_id=trend_id,
                keywords=trends_data["keywords"],
                search_interest=trends_data["search_interest"],
                geo_data=trends_data["geo_data"],
                related_queries=trends_data["related_queries"],
                rising_queries=trends_data["rising_queries"],
                provider=trends_data.get("provider"),
                fallback_from=trends_data.get("fallback_from"),
                geo_relaxed=trends_data.get("geo_relaxed"),
            )
            
            return success
            
        except Exception as exc:
            logger.error("Error processing trend signal %s: %s", trend_id, str(exc))
            await self.repository.update_status(trend_id, "failed", str(exc))
            return False
    
    async def get_latest_trends(self, user_email: str, limit: int = 10) -> List[TrendSignal]:
        """Get latest trend signals for a user"""
        return await self.repository.get_latest_by_user(user_email, limit)
    
    async def get_trend_by_id(self, trend_id: str) -> Optional[TrendSignal]:
        """Get a specific trend signal by ID"""
        return await self.repository.get_by_id(trend_id)
