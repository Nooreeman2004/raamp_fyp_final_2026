# Presentation Layer - Trend Signal Schemas
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class TrendFetchRequest(BaseModel):
    """Request schema for fetching Google Trends data"""
    niche: str = Field(..., description="Business niche (fashion, food, tech, crypto, etc.)", example="fashion")
    category: str = Field(..., description="Sub-category or specific area within the niche", example="streetwear")
    # Location removed - enforced from user's onboarding_location
    radius: Optional[str] = Field(None, description="Optional radius for geo-specific searches", example="50km")
    timeframe: Optional[str] = Field("30d", description="Analysis timeframe: 24h, 7d, 30d, 90d", example="30d")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "niche": "fashion",
                "category": "streetwear",
                "radius": "50km",
                "timeframe": "30d"
            }
        }
    }


class TrendSignalResponse(BaseModel):
    """Response schema for a single trend signal"""
    id: str
    user_email: str
    niche: str
    category: str
    location: str
    radius: Optional[str] = None
    keywords: List[str] = []
    search_interest: Dict = {}
    geo_data: Dict = {}
    related_queries: Dict = {}
    rising_queries: Dict = {}
    
    # Computed metrics
    arbitrage_score: Optional[float] = None
    saturation_score: Optional[float] = None
    social_score: Optional[float] = None
    hashtags: List[str] = []
    platform_bias: Dict[str, float] = {}
    
    # Enhanced metrics (NEW)
    lifecycle_stage: Optional[str] = None
    predicted_growth_pct: Optional[float] = None
    breakout_probability: Optional[float] = None
    profit_score: Optional[float] = None
    forecast_series: Optional[List[float]] = None
    timeframe: Optional[str] = "30d"
    
    fetch_status: str
    error_message: Optional[str] = None
    fetched_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True
    }


class TrendSignalListResponse(BaseModel):
    """Response schema for list of trend signals"""
    trends: List[TrendSignalResponse]
    total: int
    
    model_config = {
        "from_attributes": True
    }


class TrendFetchResponse(BaseModel):
    """Response schema for trend fetch operation"""
    trend_id: str
    status: str
    message: str
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "trend_id": "507f1f77bcf86cd799439011",
                "status": "processing",
                "message": "Trend data fetch initiated successfully"
            }
        }
    }


class TrendStatusResponse(BaseModel):
    """Response schema for trend fetch status"""
    trend_id: str
    status: str
    error_message: Optional[str] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "trend_id": "507f1f77bcf86cd799439011",
                "status": "completed",
                "error_message": None
            }
        }
    }


# NEW SCHEMAS FOR ENHANCEMENTS

class ContentSuggestionRequest(BaseModel):
    """Request schema for AI content suggestions"""
    keyword: str = Field(..., description="Trending keyword to generate content for")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "keyword": "sustainable fashion"
            }
        }
    }


class ContentSuggestionResponse(BaseModel):
    """Response schema for AI-generated content suggestions"""
    keyword: str
    video_ideas: List[str] = Field(..., description="3 short-form video concepts")
    hooks: List[str] = Field(..., description="3 attention-grabbing opening lines")
    hashtags: List[str] = Field(..., description="10 optimized hashtags")
    campaign_angle: str = Field(..., description="Paid campaign strategy")
    influencer_strategy: str = Field(..., description="Influencer partnership approach")
    
    # Metadata
    lifecycle_stage: Optional[str] = None
    profit_score: Optional[float] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "keyword": "sustainable fashion",
                "video_ideas": [
                    "Why everyone is switching to sustainable fashion",
                    "3 sustainable brands that look expensive",
                    "I bought only sustainable clothes for 30 days"
                ],
                "hooks": [
                    "Stop buying fast fashion. Here's why.",
                    "I spent $500 on sustainable fashion - worth it?",
                    "This sustainable brand changed my entire wardrobe"
                ],
                "hashtags": [
                    "#sustainablefashion", "#ecofriendly", "#slowfashion",
                    "#ethicalfashion", "#consciousstyle", "#greenliving",
                    "#fashionrev", "#secondhandfirst", "#vintage", "#thriftflip"
                ],
                "campaign_angle": "Target eco-conscious millennials with Instagram Story ads...",
                "influencer_strategy": "Partner with 5-10 micro-influencers in sustainable lifestyle..."
            }
        }
    }


class TrendExplainRequest(BaseModel):
    """Request for a plain-language explanation of why a trend matters to the user's business"""
    keyword: str = Field(..., description="The trending keyword")
    niche: str = Field(..., description="User's business niche")
    location: str = Field("PK", description="Market location")
    lifecycle_stage: Optional[str] = Field(None)
    breakout_probability: Optional[float] = Field(None)
    profit_score: Optional[float] = Field(None)
    competition: Optional[float] = Field(None, description="Saturation score 0-100")
    buzz: Optional[float] = Field(None, description="Social score 0-100")


class TrendExplainResponse(BaseModel):
    """Plain-language explanation of a trend for non-marketing users"""
    keyword: str
    explanation: str = Field(..., description="2-3 sentence plain English summary")
    why_now: str = Field(..., description="One sentence: why act on this today")
    content_prompt: str = Field(..., description="Ready-to-use campaign idea for CreativeStudio")


class ForecastResponse(BaseModel):
    """Response schema for trend forecast data"""
    keyword: str
    historical_series: List[float] = Field(..., description="Historical values")
    forecast_series: List[float] = Field(..., description="7-day forecast")
    predicted_growth_pct: float = Field(..., description="Predicted growth percentage")
    breakout_probability: float = Field(..., description="Breakout probability (0-100)")
    
    # Additional context
    lifecycle_stage: Optional[str] = None
    current_value: float
    z_score: float
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "keyword": "AI marketing",
                "historical_series": [45, 48, 52, 58, 62, 67, 73],
                "forecast_series": [76, 79, 82, 84, 86, 88, 89],
                "predicted_growth_pct": 21.9,
                "breakout_probability": 78.5,
                "lifecycle_stage": "Breakout",
                "current_value": 73.0,
                "z_score": 3.2
            }
        }
    }
