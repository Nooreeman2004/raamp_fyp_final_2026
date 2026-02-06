"""
Content Generation Router
=========================
FastAPI router for AI-powered social media content generation.
Generates ALL content types in a single request:
- Captions + Hashtags
- Standalone Hashtags
- WhatsApp/Email Messages
- Image Prompts (coming soon)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional

from presentation.schemas.content_generation_schema import (
    ContentGenerationRequest,
    ContentGenerationResponse,
    ContentVariant,
    MessageVariant,
    BrandContext,
    ContentGenerationError
)
from application.use_cases.content_generation_use_case import (
    ContentGenerationUseCase,
    get_content_generation_use_case
)
from presentation.routers.auth_router import get_current_user_email


router = APIRouter(prefix="/api/content", tags=["Content Generation"])


@router.post(
    "/generate",
    response_model=ContentGenerationResponse,
    responses={
        400: {"model": ContentGenerationError, "description": "Invalid request"},
        401: {"description": "Not authenticated"},
        500: {"model": ContentGenerationError, "description": "Generation failed"}
    }
)
async def generate_content(
    request: ContentGenerationRequest,
    current_user_email: str = Depends(get_current_user_email),
    use_case: ContentGenerationUseCase = Depends(get_content_generation_use_case)
):
    """
    Generate a COMPLETE marketing package in one click.
    
    This endpoint generates ALL content types at once:
    
    **1. Social Media Captions + Hashtags (3 variants)**
    - Vibrant & Direct
    - Informative & Engaging  
    - Curious & Playful
    
    **2. Standalone Hashtag Sets (3 sets)**
    - Broad Reach hashtags
    - Niche Specific hashtags
    - Mixed Strategy hashtags
    
    **3. WhatsApp/Email Messages (3 variants)**
    - Professional tone
    - Friendly tone
    - Urgent tone
    
    **4. Image Prompts (3 prompts) - Coming Soon**
    - Product shot description
    - Lifestyle shot description
    - Promo graphic description
    
    All content is generated based on brand voice guidelines from the database.
    """
    try:
        # Generate ALL content using the use case
        result = await use_case.generate_social_content(
            user_id=current_user_email,
            campaign_idea=request.campaign_idea,
            target_audience=request.target_audience,
            campaign_tone=request.campaign_tone
        )
        
        # Handle errors from the use case
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": result.get("error", "Generation failed"),
                    "detail": result.get("detail")
                }
            )
        
        # Build caption variants
        caption_variants = [
            ContentVariant(
                id=v["id"],
                tone=v["tone"],
                caption=v["caption"],
                hashtags=v["hashtags"],
                predicted_performance=v.get("predicted_performance")
            )
            for v in result["caption_variants"]
        ]
        
        # Build message variants
        message_variants = [
            MessageVariant(
                id=m["id"],
                tone=m["tone"],
                message=m["message"],
                predicted_performance=m.get("predicted_performance")
            )
            for m in result["message_variants"]
        ]
        
        # Build brand context
        brand_ctx = result.get("brand_context", {})
        brand_context = BrandContext(
            business_name=brand_ctx.get("business_name"),
            tagline=brand_ctx.get("tagline"),
            tone_of_voice=brand_ctx.get("tone_of_voice"),
            restaurant_theme=brand_ctx.get("restaurant_theme"),
            business_type=brand_ctx.get("business_type"),
            primary_color=brand_ctx.get("primary_color"),
            secondary_color=brand_ctx.get("secondary_color")
        )
        
        return ContentGenerationResponse(
            success=True,
            brand_context=brand_context,
            caption_variants=caption_variants,
            best_caption_id=result["best_caption_id"],
            hashtag_sets=result["hashtag_sets"],
            best_hashtag_set_id=result.get("best_hashtag_set_id", 1),
            message_variants=message_variants,
            best_message_id=result["best_message_id"],
            image_prompts=result.get("image_prompts", []),
            reasoning=result.get("reasoning"),
            generated_at=result["generated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Content generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "Content generation failed",
                "detail": str(e)
            }
        ) from e


@router.get("/brand-context", response_model=BrandContext)
async def get_brand_context(
    current_user_email: str = Depends(get_current_user_email),
    use_case: ContentGenerationUseCase = Depends(get_content_generation_use_case)
):
    """
    Get the current user's brand context.
    
    Returns the brand voice guidelines that will be used for content generation.
    This includes business name, tagline, tone of voice, theme, etc.
    
    Users should complete brand alignment setup to get better AI-generated content.
    """
    try:
        brand_context = await use_case.get_brand_context(current_user_email)
        
        return BrandContext(
            business_name=brand_context.get("business_name"),
            tagline=brand_context.get("tagline"),
            tone_of_voice=brand_context.get("tone_of_voice"),
            restaurant_theme=brand_context.get("restaurant_theme"),
            business_type=brand_context.get("business_type"),
            primary_color=brand_context.get("primary_color"),
            secondary_color=brand_context.get("secondary_color")
        )
        
    except Exception as e:
        print(f"Error fetching brand context: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch brand context"
        ) from e
