"""
Content Generation Use Case
===========================
Business logic layer for generating social media content.
Orchestrates between the service layer and repositories.
"""

from typing import Dict, Any, Optional, List
from fastapi import HTTPException, status
from infrastructure.repositories.business_repository import BusinessRepository
from application.services.content_generation_service import get_content_generation_service
from application.services.credit_service import get_credit_service
import logging

logger = logging.getLogger(__name__)


class ContentGenerationUseCase:
    """
    Use case for generating AI-powered social media content.
    
    Responsibilities:
    - Fetch brand context from database
    - Validate user inputs
    - Orchestrate content generation
    - Format response for API layer
    """
    
    def __init__(self):
        """Initialize use case with required dependencies."""
        self.business_repo = BusinessRepository()
        self.content_service = get_content_generation_service()
        self.credit_service = get_credit_service()
    
    async def get_brand_context(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieve brand context from database for the given user.
        
        Args:
            user_id: The user's email/ID
            
        Returns:
            Dictionary with brand context fields
        """
        business = await self.business_repo.get_by_user_id(user_id)
        
        if not business:
            return {
                "business_name": None,
                "tagline": None,
                "tone_of_voice": None,
                "tone_profile": None,
                "restaurant_theme": None,
                "business_type": None,
                "primary_color": None,
                "secondary_color": None,
                "brand_colors": [],
                "palette_source": None,
                "brand_logo_url": None,
                "specialties": [],
                "city": None,
                "country": None
            }
        
        return {
            "business_name": business.business_name,
            "tagline": business.tagline,
            "tone_of_voice": business.tone_of_voice,
            "tone_profile": business.tone_profile.model_dump() if getattr(business, "tone_profile", None) else None,
            "restaurant_theme": business.restaurant_theme,
            "business_type": business.business_type,
            "primary_color": business.primary_color,
            "secondary_color": business.secondary_color,
            "brand_colors": getattr(business, "brand_colors", []) or [],
            "palette_source": getattr(business, "palette_source", None),
            "brand_logo_url": business.brand_logo_url,
            "specialties": business.specialties,
            "city": business.city,
            "country": business.country
        }
    
    async def generate_social_content(
        self,
        user_id: str,
        campaign_idea: str,
        target_audience: Optional[str] = None,
        campaign_tone: Optional[str] = None,
        platform_type: str = "post",
        campaign_id: Optional[str] = None,
        content_type: str = "all",
        aspect_ratio: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate ALL content types for a campaign in one call.
        
        Generates:
        - Social media captions + hashtags (3 variants)
        - Standalone hashtag sets (3 sets)
        - WhatsApp/Email messages (3 variants)
        - Image prompts (3 prompts - coming soon)
        
        Supports multiple platforms: post, story, reel
        
        Args:
            user_id: The user's email/ID
            campaign_idea: The campaign vision/idea
            target_audience: Optional target audience description
            campaign_tone: Optional tone override (uses brand tone if not provided)
            platform_type: Content platform (post, story, reel) - defaults to "post"
            campaign_id: Optional campaign identifier for grouping
            
        Returns:
            Dictionary with all generated content and metadata
        """
        # Validate inputs
        if not campaign_idea or len(campaign_idea.strip()) < 10:
            return {
                "success": False,
                "error": "Campaign idea must be at least 10 characters",
                "detail": "Please provide a more detailed campaign description"
            }
        
        # Fetch brand context from database
        print(f"🔍 Fetching brand context for user_id: {user_id}")
        brand_context = await self.get_brand_context(user_id)

        # Debug log to see what's actually in the brand context
        print(f"🔍 BRAND CONTEXT DEBUG: {brand_context}")

        # Brand field gate: reject early (before credits) if required fields are missing.
        # "Brand-lock": for strict brand relevance across text+images+videos,
        # require full brand identity fields (logo + palette) in addition to name/tagline/tone.
        required_fields = ["business_name", "tagline", "tone_of_voice", "restaurant_theme", "brand_logo_url"]
        missing: List[str] = []
        for f in required_fields:
            v = brand_context.get(f)
            if v is None or not str(v).strip():
                missing.append(f)
        if not (brand_context.get("brand_colors") and len(brand_context.get("brand_colors") or []) >= 2):
            missing.append("brand_colors")
        if missing:
            # Build user-friendly field names
            field_labels = {
                "business_name": "Business Name (complete Location Setup)",
                "tagline": "Tagline",
                "tone_of_voice": "Tone of Voice",
                "restaurant_theme": "Restaurant Theme",
                "brand_logo_url": "Brand Logo",
                "brand_colors": "Brand Colors (at least 2)"
            }
            missing_labels = [field_labels.get(f, f) for f in missing]
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": "brand_profile_incomplete",
                    "missing_fields": missing,
                    "message": (
                        f"Missing required fields: {', '.join(missing_labels)}. "
                        "Complete Brand Settings and Location Setup before generating content."
                    ),
                },
            )
        
        # Check credits based on what is requested.
        # - images: charge image_generation
        # - everything else (captions/hashtags/whatsapp/emails/all): charge caption_generation
        ct = (content_type or "all").lower().strip()
        action_type = "image_generation" if ct == "images" else "caption_generation"
        await self.credit_service.check_and_deduct(user_id, action_type)

        # Generate all content using AI service
        result = await self.content_service.generate_content(
            campaign_idea=campaign_idea.strip(),
            brand_context=brand_context,
            user_id=user_id,
            target_audience=target_audience.strip() if target_audience else None,
            campaign_tone=campaign_tone.strip() if campaign_tone else None,
            platform_type=platform_type,
            campaign_id=campaign_id,
            content_type=content_type,
            aspect_ratio=aspect_ratio,
        )
        
        # Add brand context to response
        if result.get("success"):
            result["brand_context"] = brand_context
        
        return result


# Factory function for dependency injection
def get_content_generation_use_case() -> ContentGenerationUseCase:
    """Get a content generation use case instance."""
    return ContentGenerationUseCase()
