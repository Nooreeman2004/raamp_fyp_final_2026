"""
Content Generation Schemas
==========================
Pydantic schemas for the AI-powered social media content generation API.
Generates ALL content types in a single request.
"""

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class ContentVariant(BaseModel):
    """A single content variant with caption and hashtags."""
    id: int = Field(..., description="Variant ID (1, 2, or 3)")
    tone: str = Field(..., description="Tone of this variant (e.g., 'Vibrant & Direct')")
    caption: str = Field(..., description="Generated caption (max 200 tokens)")
    hashtags: List[str] = Field(..., description="3-5 relevant hashtags")
    predicted_performance: Optional[str] = Field(None, description="AI prediction: 'Best', 'Good', or 'Experimental'")


class MessageVariant(BaseModel):
    """A WhatsApp/Email message variant."""
    id: int = Field(..., description="Variant ID (1, 2, or 3)")
    tone: str = Field(..., description="Tone: 'Professional', 'Friendly', or 'Urgent'")
    message: str = Field(..., description="The complete message text")
    predicted_performance: Optional[str] = Field(None, description="AI prediction: 'Best', 'Good', or 'Experimental'")


class ContentGenerationRequest(BaseModel):
    """Request body for content generation endpoint.
    
    Generates ALL content types in a single request:
    - Captions for social media (posts, stories, reels)
    - Hashtags for reach
    - WhatsApp/Email campaign messages
    - AI-generated images
    """
    campaign_idea: str = Field(
        ..., 
        min_length=10, 
        max_length=1000,
        description="Campaign idea/vision describing what the user wants to promote"
    )
    target_audience: Optional[str] = Field(
        None,
        max_length=500,
        description="Target audience description (e.g., 'health-conscious millennials in urban areas')"
    )
    campaign_tone: Optional[str] = Field(
        None,
        max_length=100,
        description="Optional tone override for this campaign. If empty, uses brand's default tone."
    )
    platform_type: str = Field(
        default="post",
        description=(
            "Preferred platform prompt mode for text generation. "
            "Allowed: 'post', 'story', 'reel'. "
            "If omitted/invalid, the backend derives it from aspect_ratio (9:16 → story, else post)."
        )
    )
    aspect_ratio: Optional[str] = Field(
        default="1:1",
        description="Content aspect ratio: '1:1' (square), '9:16' (vertical), '4:5' (portrait)"
    )
    content_type: Optional[str] = Field(
        default="all",
        description=(
            "Content type to generate: "
            "'captions' (social media captions + hashtags), "
            "'hashtags' (hashtag sets only), "
            "'whatsapp' (WhatsApp broadcast messages), "
            "'emails' (email campaign messages), "
            "'images' (image generation only), "
            "'all' (generate all text types — default)"
        )
    )
    campaign_id: Optional[str] = Field(
        None,
        description="Optional campaign identifier for grouping related content"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "campaign_idea": "Create a summer promotion campaign for our new smoothie line emphasizing organic ingredients and sustainability.",
                "target_audience": "Health-conscious millennials in urban areas",
                "campaign_tone": "Playful and energetic",
                "platform_type": "post"
            }
        }


class BrandContext(BaseModel):
    """Brand context retrieved from database."""
    business_name: Optional[str] = None
    tagline: Optional[str] = None
    tone_of_voice: Optional[str] = None
    restaurant_theme: Optional[str] = None
    business_type: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None


class HashtagSet(BaseModel):
    """A set of hashtags for reach."""
    id: int = Field(..., description="Set ID (1, 2, or 3)")
    hashtag_id: str = Field(..., description="Unique ID for this hashtag set")
    hashtags: List[str] = Field(..., description="The set of hashtags")


class ContentGenerationResponse(BaseModel):
    """Response from content generation endpoint.
    
    Contains ALL content types generated in a single request.
    """
    success: bool = Field(..., description="Whether generation was successful")
    platform_type: str = Field(default="post", description="Platform type used for generation: post, story, or reel")
    brand_context: BrandContext = Field(..., description="Brand context used for generation")
    
    # Social Media Content (Captions + Hashtags)
    caption_variants: List[ContentVariant] = Field(..., description="Three caption+hashtag variants")
    best_caption_id: int = Field(..., description="ID of best performing caption variant")
    
    # Standalone Hashtags
    hashtag_sets: List[HashtagSet] = Field(..., description="Three different hashtag sets for maximum reach")
    best_hashtag_set_id: int = Field(..., description="ID of best performing hashtag set (1=Broad, 2=Niche, 3=Mixed)")
    
    # WhatsApp Messages
    whatsapp_variants: List[MessageVariant] = Field(..., description="Three WhatsApp broadcast variants")
    
    # Email Campaigns
    email_variants: List[MessageVariant] = Field(..., description="Three email campaign variants")
    
    # [Deprecated] WhatsApp/Email Messages (Combined)
    message_variants: List[MessageVariant] = Field(..., description="Combined message variants (legacy)")
    best_message_id: int = Field(..., description="ID of best performing message variant")
    
    # AI-Generated Images
    image_prompts: List[str] = Field(default=[], description="AI-generated image prompts for reference")
    image_paths: List[str] = Field(default=[], description="Generated image file URLs")
    asset_ids: List[str] = Field(default=[], description="Asset IDs for generated images (stored in database)")
    image_generation_prompt: Optional[str] = Field(None, description="The detailed prompt used for image generation")
    
    # Metadata
    reasoning: Optional[str] = Field(None, description="AI reasoning for content strategy")
    validation_warnings: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Non-blocking validation warnings when brand-lock checks fail after retries"
    )
    generated_at: str = Field(..., description="ISO timestamp of generation")

    # Image generation transparency (optional)
    logo_used: Optional[bool] = Field(
        default=None,
        description="Whether the stored brand logo was successfully fetched and used as a visual reference for image prompts"
    )
    logo_warning: Optional[str] = Field(
        default=None,
        description="If logo_used is false, a human-readable reason/warning for the UI"
    )


class ContentGenerationError(BaseModel):
    """Error response for content generation."""
    success: bool = False
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")


class PlatformInfo(BaseModel):
    """Static platform configuration used by the UI."""
    id: str = Field(..., description="Platform identifier (e.g. instagram, facebook)")
    name: str = Field(..., description="Human-friendly platform name")
    description: str = Field(..., description="Short description of what this platform is used for")
    guidelines: str = Field(..., description="Short content guidelines for this platform")
    supported_generation_types: List[str] = Field(
        default_factory=list,
        description="Supported generation modes (e.g. post, story, reel)"
    )
    supported_aspect_ratios: List[str] = Field(
        default_factory=list,
        description="Supported aspect ratios (e.g. 1:1, 4:5, 9:16)"
    )


class PlatformsResponse(BaseModel):
    """Response payload for GET /api/content/platforms."""
    platforms: List[PlatformInfo] = Field(default_factory=list)


# ============================================================================
# SIMPLIFIED TRENDS - QUICK POST GENERATION
# ============================================================================

class GenerateFromTrendRequest(BaseModel):
    """Request to generate content from a trending topic (simplified for restaurant owners)"""
    topic: str = Field(..., description="The trending topic to create content about")
    location: str = Field(default="GLOBAL", description="Geographic location context")
    niche: str = Field(default="restaurant", description="Business niche/industry")
    business_type: str = Field(default="restaurant", description="Type of business (restaurant, cafe, bakery, etc.)")
    count: int = Field(default=3, ge=1, le=5, description="Number of caption variants to generate")


class TrendCaptionVariant(BaseModel):
    """A single caption variant with hashtags for trending topics"""
    caption: str = Field(..., description="The post caption text (under 80 words, sensory language, CTA)")
    hashtags: List[str] = Field(default_factory=list, description="3-5 suggested hashtags (without # symbol)")


class GenerateFromTrendResponse(BaseModel):
    """Response containing caption variants for a trending topic"""
    variants: List[TrendCaptionVariant] = Field(..., description="List of caption variants")
    topic: str = Field(..., description="The topic these captions are about")
    generated_at: str = Field(..., description="Timestamp when generated")
