"""
Content Generation Use Case
===========================
Business logic layer for generating social media content.
Orchestrates between the service layer and repositories.
"""

from typing import Dict, Any, Optional
from infrastructure.repositories.business_repository import BusinessRepository
from application.services.content_generation_service import get_content_generation_service
from application.services.credit_service import get_credit_service


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
                "restaurant_theme": None,
                "business_type": None,
                "primary_color": None,
                "secondary_color": None,
                "brand_logo_url": None,
                "specialties": []
            }
        
        return {
            "business_name": business.business_name,
            "tagline": business.tagline,
            "tone_of_voice": business.tone_of_voice,
            "restaurant_theme": business.restaurant_theme,
            "business_type": business.business_type,
            "primary_color": business.primary_color,
            "secondary_color": business.secondary_color,
            "brand_logo_url": business.brand_logo_url,
            "specialties": business.specialties
        }
    
    async def generate_social_content(
        self,
        user_id: str,
        campaign_idea: str,
        target_audience: Optional[str] = None,
        campaign_tone: Optional[str] = None,
        platform_type: str = "post",
        campaign_id: Optional[str] = None,
        content_type: str = "all"
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
        brand_context = await self.get_brand_context(user_id)
        
        # Check Credits and Enforce Tier Limits (1 credit for captions/ads)
        await self.credit_service.check_and_deduct(user_id, "caption_generation")

        # Generate all content using AI service
        result = await self.content_service.generate_content(
            campaign_idea=campaign_idea.strip(),
            brand_context=brand_context,
            user_id=user_id,
            target_audience=target_audience.strip() if target_audience else None,
            campaign_tone=campaign_tone.strip() if campaign_tone else None,
            platform_type=platform_type,
            campaign_id=campaign_id,
            content_type=content_type
        )
        
        # Add brand context to response
        if result.get("success"):
            result["brand_context"] = brand_context
        
        return result


# Factory function for dependency injection
def get_content_generation_use_case() -> ContentGenerationUseCase:
    """Get a content generation use case instance."""
    return ContentGenerationUseCase()
