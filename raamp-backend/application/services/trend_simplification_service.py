"""
Service to transform complex trend data into simplified, actionable insights
for restaurant owners without marketing expertise.
"""
import logging
from typing import List, Dict, Any
from datetime import datetime
from infrastructure.database.models.business_model import BusinessTypeEnum

logger = logging.getLogger(__name__)


class TrendSimplificationService:
    """Transforms complex trend analytics into simple, actionable insights"""
    
    @staticmethod
    def is_food_business(business_type: str) -> bool:
        """Check if business type is food-related"""
        if not business_type:
            return False
        
        business_type_lower = business_type.lower()
        
        # Check enum values
        food_types = [
            BusinessTypeEnum.RESTAURANT.value,
            BusinessTypeEnum.CAFE.value,
            BusinessTypeEnum.BAKERY.value,
        ]
        
        return business_type_lower in food_types or any(
            keyword in business_type_lower 
            for keyword in ["food", "restaurant", "cafe", "bakery", "dining"]
        )
    
    @staticmethod
    def is_relevant_for_business(keyword: str, business_type: str, niche: str = "") -> bool:
        """
        Check if a trend keyword is relevant for the business type.
        Filters out obviously irrelevant trends (sports, politics, etc.)
        """
        if not keyword:
            return False
        
        keyword_lower = keyword.lower().strip()
        
        # Common irrelevant patterns for food businesses
        if TrendSimplificationService.is_food_business(business_type):
            # Sports-related keywords
            sports_patterns = [
                "vs ", " vs", "match", "game", "score", "league", "tournament",
                "fifa", "uefa", "premier league", "champions league",
                "barcelona", "real madrid", "manchester", "liverpool",
                "cricket", "football", "soccer", "basketball", "tennis"
            ]
            
            # Politics/news keywords
            politics_patterns = [
                "election", "government", "minister", "president", "parliament",
                "political", "vote", "campaign", "party"
            ]
            
            # Check if keyword matches irrelevant patterns
            for pattern in sports_patterns + politics_patterns:
                if pattern in keyword_lower:
                    return False
        
        # If niche is provided, check for basic relevance
        if niche:
            niche_lower = niche.lower()
            # Very basic check - keyword or niche should have some overlap
            # This is a simple heuristic, can be improved with ML
            if niche_lower in keyword_lower or keyword_lower in niche_lower:
                return True
        
        # Default: allow the trend (conservative filtering)
        return True
    
    @staticmethod
    def classify_opportunity_level(score: float) -> str:
        """
        Convert profit/signal score to simple opportunity level
        
        Args:
            score: Numeric score (0-100 typically)
            
        Returns:
            "high" | "medium" | "low"
        """
        if score >= 70:
            return "high"
        elif score >= 40:
            return "medium"
        else:
            return "low"
    
    @staticmethod
    def format_location(location: str) -> str:
        """
        Format location for display - handle country codes and missing data
        
        Args:
            location: Raw location string (could be city, country code, or GLOBAL)
            
        Returns:
            Human-readable location text
        """
        if not location or location == "GLOBAL":
            return "your area"
        
        # Map common country codes to readable names
        country_map = {
            "PK": "Pakistan",
            "US": "the US",
            "UK": "the UK",
            "IN": "India",
            "AE": "UAE",
            "SA": "Saudi Arabia",
            "CA": "Canada",
            "AU": "Australia",
        }
        
        # If it's a 2-letter code, try to map it
        if len(location) == 2 and location.upper() in country_map:
            return country_map[location.upper()]
        
        # Otherwise return as-is (could be city name)
        return location
    
    @staticmethod
    def generate_why_relevant(
        keyword: str,
        location: str,
        business_type: str = "restaurant",
        score: float = 0
    ) -> str:
        """
        Generate simple explanation in restaurant terms
        
        Args:
            keyword: The trending topic
            location: Geographic location
            business_type: Type of business (restaurant, cafe, etc.)
            score: Opportunity score
            
        Returns:
            Simple, actionable explanation
        """
        location_display = TrendSimplificationService.format_location(location)
        
        is_food = TrendSimplificationService.is_food_business(business_type)
        
        # Handle null, zero, or very low scores with meaningful copy
        if score is None or score <= 0:
            if is_food:
                return f"{keyword} is emerging in {location_display}. Early opportunity to create content before competition increases."
            else:
                return f"{keyword} is gaining early traction in {location_display}. Consider being an early mover."
        
        if is_food:
            if score >= 70:
                return f"People in {location_display} are actively searching for {keyword}. High demand right now - great time to post."
            elif score >= 40:
                return f"{keyword} is getting attention in {location_display}. Good opportunity to reach interested customers."
            else:
                return f"{keyword} is building momentum in {location_display}. Post now to get ahead of the trend."
        else:
            # Generic business
            if score >= 70:
                return f"High customer interest in {keyword} in {location_display}. Strong opportunity to engage."
            elif score >= 40:
                return f"Growing interest in {keyword} in {location_display}. Good time to create content."
            else:
                return f"{keyword} is gaining traction in {location_display}. Early opportunity to stand out."
    
    @staticmethod
    def generate_suggested_action(
        keyword: str,
        opportunity_level: str,
        business_type: str = "restaurant",
        score: float = 0
    ) -> str:
        """
        Generate one clear action in simple language
        
        Args:
            keyword: The trending topic
            opportunity_level: high | medium | low
            business_type: Type of business
            score: Opportunity score for context
            
        Returns:
            Clear, actionable suggestion
        """
        is_food = TrendSimplificationService.is_food_business(business_type)
        
        # Handle null or very low scores with specific guidance
        if score is None or score <= 0:
            if is_food:
                return f"Create a post about {keyword} to test customer interest. Be an early mover."
            else:
                return f"Experiment with {keyword} content to gauge audience response."
        
        if is_food:
            if opportunity_level == "high":
                return f"Post about {keyword} in the next 2 hours. Include photos and a call-to-action."
            elif opportunity_level == "medium":
                return f"Create a post about {keyword} today. Share what makes your offering special."
            else:
                return f"Plan content about {keyword} this week. Get ahead before demand peaks."
        else:
            if opportunity_level == "high":
                return f"Create content about {keyword} immediately. Engage while interest is high."
            elif opportunity_level == "medium":
                return f"Post about {keyword} soon. Share your unique perspective."
            else:
                return f"Plan content around {keyword}. Position yourself as an early expert."
    
    @classmethod
    def simplify_trend(
        cls,
        trend: Dict[str, Any],
        business_type: str = "restaurant"
    ) -> Dict[str, Any]:
        """
        Transform a complex trend object into simplified format
        
        Args:
            trend: Raw trend data from database
            business_type: Type of business for context
            
        Returns:
            Simplified trend dict
        """
        # Extract score (try multiple fields for compatibility)
        score = float(
            trend.get("profit_score") or 
            trend.get("score") or 
            trend.get("social_score") or 
            0
        )
        
        keyword = str(trend.get("keyword", "Unknown"))
        location = str(trend.get("location", ""))
        
        opportunity_level = cls.classify_opportunity_level(score)
        
        return {
            "id": str(trend.get("id", "")),
            "topic": keyword,
            "opportunity_level": opportunity_level,
            "why_relevant": cls.generate_why_relevant(
                keyword, location, business_type, score
            ),
            "suggested_action": cls.generate_suggested_action(
                keyword, opportunity_level, business_type, score
            ),
            "ready_to_use": True,
            "location": cls.format_location(location),
            "niche": trend.get("niche"),
            "detected_at": trend.get("detected_at") or trend.get("created_at"),
        }
    
    @classmethod
    def simplify_trends_list(
        cls,
        trends: List[Dict[str, Any]],
        business_type: str = "restaurant",
        location: str = "GLOBAL"
    ) -> Dict[str, Any]:
        """
        Transform a list of trends into simplified format
        
        Args:
            trends: List of raw trend data
            business_type: Type of business
            location: Geographic location
            
        Returns:
            Simplified trends list response
        """
        # Filter out irrelevant trends first
        relevant_trends = [
            trend for trend in trends
            if cls.is_relevant_for_business(
                trend.get("keyword", ""),
                business_type,
                trend.get("niche", "")
            )
        ]
        
        simplified = [
            cls.simplify_trend(trend, business_type)
            for trend in relevant_trends
        ]
        
        return {
            "trends": simplified,
            "total": len(simplified),
            "location": location,
            "last_updated": datetime.utcnow(),
        }
