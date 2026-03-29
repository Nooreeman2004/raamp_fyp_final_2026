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
    HashtagSet,
    BrandContext,
    ContentGenerationError
)
from application.use_cases.content_generation_use_case import (
    ContentGenerationUseCase,
    get_content_generation_use_case
)
from presentation.routers.auth_router import get_current_user_email
import uuid
import traceback
import logging

logger = logging.getLogger(__name__)


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
    
    This endpoint generates ALL content types at once for:
    - **Regular Posts**: Instagram/Facebook feed posts
    - **Instagram Stories**: 9:16 vertical format with interactive elements  
    - **Instagram Reels**: Short-form video captions with trending hooks
    
    **1. Social Media Captions + Hashtags (3 variants)**
    - Platform-optimized variants with different tones
    
    **2. Standalone Hashtag Sets (3 sets)**
    - Broad Reach hashtags
    - Niche Specific hashtags
    - Mixed Strategy hashtags
    
    **3. WhatsApp/Email Messages (3 variants)**
    - Professional tone
    - Friendly tone
    - Urgent tone
    
    **4. Image Prompts (3 prompts)**
    - Product shot description
    - Lifestyle shot description
    - Promo graphic description
    
    All content is generated based on brand voice guidelines from the database.
    Captions are automatically logged for creative history.
    """
    try:
        # Generate campaign_id if not provided
        campaign_id = request.campaign_id if hasattr(request, 'campaign_id') and request.campaign_id else str(uuid.uuid4())
        
        # Generate ALL content using the use case
        result = await use_case.generate_social_content(
            user_id=current_user_email,
            campaign_idea=request.campaign_idea,
            target_audience=request.target_audience,
            campaign_tone=request.campaign_tone,
            platform_type="story" if getattr(request, 'aspect_ratio', '1:1') == "9:16" else "post",
            campaign_id=campaign_id,
            content_type=getattr(request, 'content_type', 'all') or 'all'
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
        
        # Build WhatsApp variants
        whatsapp_variants = [
            MessageVariant(
                id=m["id"],
                tone=m["tone"],
                message=m["message"],
                predicted_performance=m.get("predicted_performance")
            )
            for m in result.get("whatsapp_variants", [])
        ]
        
        # Build Email variants
        email_variants = [
            MessageVariant(
                id=m["id"],
                tone=m["tone"],
                message=m["message"],
                predicted_performance=m.get("predicted_performance")
            )
            for m in result.get("email_variants", [])
        ]
        
        # Build Hashtag sets
        hashtag_sets = [
            HashtagSet(
                id=h["id"],
                hashtag_id=h.get("hashtag_id") or str(uuid.uuid4()),
                hashtags=h["hashtags"]
            )
            for h in result.get("hashtag_sets", [])
        ]
        
        # Build message variants (Legacy fallback)
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
            platform_type=result.get("platform_type", "post"),
            brand_context=brand_context,
            caption_variants=caption_variants,
            best_caption_id=result.get("best_caption_id", 1),
            hashtag_sets=hashtag_sets,
            best_hashtag_set_id=result.get("best_hashtag_set_id", 1),
            whatsapp_variants=whatsapp_variants,
            email_variants=email_variants,
            message_variants=message_variants,
            best_message_id=result.get("best_message_id", 1),
            image_prompts=result.get("image_prompts", []),
            image_paths=result.get("image_paths", []),
            asset_ids=result.get("asset_ids", []),
            image_generation_prompt=result.get("image_generation_prompt"),
            reasoning=result.get("reasoning"),
            generated_at=result["generated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        logger.error("❌ Content generation exception: %s: %s", type(e).__name__, e)
        logger.error("   Traceback:\n%s", tb)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "Content generation failed",
                "detail": f"{type(e).__name__}: {str(e)}"
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
