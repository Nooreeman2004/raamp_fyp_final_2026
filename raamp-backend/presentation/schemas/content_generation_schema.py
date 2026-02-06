"""
Content Generation Schemas
==========================
Pydantic schemas for the AI-powered social media content generation API.
Generates ALL content types in a single request.
"""

from typing import List, Optional
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
    - Captions for social media
    - Hashtags for reach
    - WhatsApp/Email campaign messages
    - Image placeholder (coming soon)
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
    
    class Config:
        json_schema_extra = {
            "example": {
                "campaign_idea": "Create a summer promotion campaign for our new smoothie line emphasizing organic ingredients and sustainability.",
                "target_audience": "Health-conscious millennials in urban areas",
                "campaign_tone": "Playful and energetic"
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


class ContentGenerationResponse(BaseModel):
    """Response from content generation endpoint.
    
    Contains ALL content types generated in a single request.
    """
    success: bool = Field(..., description="Whether generation was successful")
    brand_context: BrandContext = Field(..., description="Brand context used for generation")
    
    # Social Media Content (Captions + Hashtags)
    caption_variants: List[ContentVariant] = Field(..., description="Three caption+hashtag variants")
    best_caption_id: int = Field(..., description="ID of best performing caption variant")
    
    # Standalone Hashtags
    hashtag_sets: List[List[str]] = Field(..., description="Three different hashtag sets for maximum reach")
    best_hashtag_set_id: int = Field(..., description="ID of best performing hashtag set (1=Broad, 2=Niche, 3=Mixed)")
    
    # WhatsApp/Email Messages
    message_variants: List[MessageVariant] = Field(..., description="Three message variants for direct outreach")
    best_message_id: int = Field(..., description="ID of best performing message variant")
    
    # Images (placeholder for now)
    image_prompts: List[str] = Field(default=[], description="AI-generated image prompts (coming soon)")
    
    # Metadata
    reasoning: Optional[str] = Field(None, description="AI reasoning for content strategy")
    generated_at: str = Field(..., description="ISO timestamp of generation")


class ContentGenerationError(BaseModel):
    """Error response for content generation."""
    success: bool = False
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
