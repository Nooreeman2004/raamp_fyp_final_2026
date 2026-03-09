# Application Layer - Google Trends Service
import logging
from typing import List, Dict, Optional
from datetime import datetime
from pytrends.request import TrendReq
import asyncio
from functools import partial
import hashlib
import json

from domain.entities.trend_signal import TrendSignal
from domain.repositories.trend_signal_repository import ITrendSignalRepository
from infrastructure.repositories.trend_signal_repository import TrendSignalRepository


logger = logging.getLogger(__name__)

# Global cache for Google Trends data
# Key: hash of (keywords, location, timeframe)
# Value: {"data": <trends_data>, "timestamp": <datetime>, "ttl": <minutes>}
_TRENDS_CACHE = {}


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
    
    # Niche-to-keywords mapping (reduced to 2 keywords to minimize rate limiting)
    NICHE_KEYWORDS = {
        "fashion": ["fashion trends", "clothing styles"],
        "food": ["food trends", "recipes"],
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
        
        # Add category-specific keyword
        if category and category.lower() not in [kw.lower() for kw in base_keywords]:
            keywords = [category] + base_keywords[:2]  # Limit to 3 keywords total (1 category + 2 niche)
        else:
            keywords = base_keywords[:3]  # Max 3 keywords
        
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
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Get data from cache if valid"""
        if cache_key in _TRENDS_CACHE:
            cache_entry = _TRENDS_CACHE[cache_key]
            age_minutes = (datetime.now() - cache_entry["timestamp"]).total_seconds() / 60
            
            if age_minutes < cache_entry["ttl"]:
                logger.info("Cache HIT for %s... (age: %.1fm, ttl: %dm)",
                          cache_key[:8], age_minutes, cache_entry['ttl'])
                return cache_entry["data"]
            else:
                logger.info("Cache EXPIRED for %s... (age: %.1fm)",
                          cache_key[:8], age_minutes)
                del _TRENDS_CACHE[cache_key]
        
        return None
    
    def _save_to_cache(self, cache_key: str, data: Dict, ttl_minutes: Optional[int] = None):
        """Save data to cache"""
        ttl = ttl_minutes or self.cache_ttl_minutes
        _TRENDS_CACHE[cache_key] = {
            "data": data,
            "timestamp": datetime.now(),
            "ttl": ttl
        }
        logger.info("Cached trends data %s... (ttl: %dm)", cache_key[:8], ttl)
    
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
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
        
        # Enforce rate limiting between requests
        await self._rate_limit_delay()
        
        max_retries = 3
        base_retry_delay = 5  # Start with 5s instead of 30s
        
        for attempt in range(max_retries):
            try:
                # Run blocking PyTrends calls in thread pool to avoid blocking the event loop
                loop = asyncio.get_event_loop()
                pytrends = self._get_pytrends()
                
                # Build payload with error handling for empty niches
                if not keywords:
                    return {"success": False, "error": "No keywords provided for analysis"}

                await loop.run_in_executor(
                    None,
                    partial(
                        pytrends.build_payload,
                        keywords,
                        cat=0,
                        timeframe=timeframe,
                        geo=location if location.upper() != "GLOBAL" else "",
                        gprop=''
                    )
                )
                
                # Fetch interest over time - ensure we handle empty dataframes gracefully
                interest_over_time_df = await loop.run_in_executor(
                    None,
                    pytrends.interest_over_time
                )
                
                # Fetch interest by region
                interest_by_region_df = await loop.run_in_executor(
                    None,
                    partial(
                        pytrends.interest_by_region,
                        resolution='COUNTRY',
                        inc_low_vol=True,
                        inc_geo_code=False
                    )
                )
                
                # Fetch related queries
                related_queries_dict = await loop.run_in_executor(
                    None,
                    pytrends.related_queries
                )
                
                # Convert DataFrames to dictionaries with safety checks
                search_interest = {}
                if interest_over_time_df is not None and not interest_over_time_df.empty:
                    # Remove 'isPartial' column if exists
                    if 'isPartial' in interest_over_time_df.columns:
                        interest_over_time_df = interest_over_time_df.drop('isPartial', axis=1)
                    
                    search_interest = {
                        "dates": interest_over_time_df.index.strftime('%Y-%m-%d').tolist(),
                        "data": interest_over_time_df.to_dict(orient='list')
                    }
                
                geo_data = {}
                if interest_by_region_df is not None and not interest_by_region_df.empty:
                    geo_data = interest_by_region_df.to_dict(orient='index')
                
                # Process related queries with dictionary defensive logic
                related_queries = {}
                rising_queries = {}
                
                if related_queries_dict:
                    for keyword, queries in related_queries_dict.items():
                        if queries.get('top') is not None and not queries['top'].empty:
                            related_queries[keyword] = queries['top'].to_dict(orient='records')
                        
                        if queries.get('rising') is not None and not queries['rising'].empty:
                            rising_queries[keyword] = queries['rising'].to_dict(orient='records')
                
                result = {
                    "keywords": keywords,
                    "search_interest": search_interest,
                    "geo_data": geo_data,
                    "related_queries": related_queries,
                    "rising_queries": rising_queries,
                    "success": True,
                    "error": None
                }
                
                # Cache the successful result
                if use_cache:
                    self._save_to_cache(cache_key, result)
                
                return result
                
            except Exception as e:
                error_msg = str(e)
                if ("429" in error_msg or "Too Many Requests" in error_msg) and attempt < max_retries - 1:
                    import random
                    # Progressive backoff: 5s, 15s, 45s (much faster than before)
                    wait_time = (base_retry_delay * (3 ** attempt)) + random.uniform(1, 3)
                    logger.warning("Google Trends rate limited (429). Backoff: %.1fs... (Attempt %d/%d)",
                                 wait_time, attempt+1, max_retries)
                    await asyncio.sleep(wait_time)
                    # Force reset pytrends instance to break any sticky sessions
                    self.pytrends = None
                elif "429" in error_msg or "Too Many Requests" in error_msg:
                    # On final retry failure for 429, return cached mock data if available
                    logger.error("Max retries exceeded due to rate limiting. Returning fallback data.")
                    return {
                        "keywords": keywords,
                        "search_interest": {},
                        "geo_data": {},
                        "related_queries": {},
                        "rising_queries": {},
                        "success": False,
                        "error": "Rate limit exceeded. Please try again in a few minutes."
                    }
                else:
                    logger.error("Critical error in Google Trends pipeline: %s", error_msg)
                    return {
                        "keywords": keywords,
                        "search_interest": {},
                        "geo_data": {},
                        "related_queries": {},
                        "rising_queries": {},
                        "success": False,
                        "error": error_msg
                    }
        
        return {
            "keywords": keywords,
            "success": False,
            "error": "Max retries exceeded for Google Trends"
        }
    
    async def create_trend_signal(
        self,
        user_email: str,
        niche: str,
        category: str,
        location: str,
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
            
            # Get keywords for the niche
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
                rising_queries=trends_data["rising_queries"]
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
