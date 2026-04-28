"""
Reel & Video Generation Router
================================
FastAPI router for AI-powered Reel and Video generation using Veo 3.1.
Generates short-form videos (4-8 seconds) for social media.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from pathlib import Path
import uuid

from config import Config


def _to_api_url(abs_path: str) -> str:
    """Convert an absolute generated-asset file path to its /api/... serve URL."""
    p = Path(abs_path)
    mapping = [
        (Config.GENERATED_REELS_DIR,  "/api/reels"),
        (Config.GENERATED_VIDEOS_DIR, "/api/videos"),
        (Config.GENERATED_IMAGES_DIR, "/api/generated"),
    ]
    for base, prefix in mapping:
        try:
            rel = p.relative_to(base)
            return f"{prefix}/{rel.as_posix()}"
        except ValueError:
            continue
    # Fallback: return as-is (already a URL or relative path)
    return abs_path


def _paths_to_urls(paths: list) -> list:
    return [_to_api_url(str(p)) for p in paths]

from application.services.reel_generation_service import get_reel_generation_service
from application.services.video_generation_service import get_video_generation_service
from infrastructure.repositories.business_repository import BusinessRepository
from presentation.routers.auth_router import get_current_user_email

# Shared dependency for fetching onboarding brand context
_business_repo = BusinessRepository()

async def get_user_brand_context(user_email: str) -> dict:
    """Fetch brand context from onboarding data for the given user."""
    try:
        business = await _business_repo.get_by_user_id(user_email)
        if not business:
            return {}
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
            "specialties": business.specialties or []
        }
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Could not fetch brand context for %s: %s", user_email, e)
        return {}

router = APIRouter(prefix="/api/media", tags=["Media Generation"])


def _require_brand_lock(ctx: dict):
    required = ["business_name", "tagline", "tone_of_voice", "restaurant_theme", "brand_logo_url"]
    missing = []
    for f in required:
        v = ctx.get(f)
        if v is None or not str(v).strip():
            missing.append(f)
    if not (ctx.get("brand_colors") and len(ctx.get("brand_colors") or []) >= 2):
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
                "message": f"Missing required fields: {', '.join(missing_labels)}. Complete Brand Settings and Location Setup before generating media.",
            },
        )


def _safe_merge_request_brand_context(db_ctx: dict, req_ctx: Optional[dict]) -> dict:
    """
    Never allow overriding core brand identity from the request body.
    This prevents off-brand / prompt injection through client-supplied brand_context.
    """
    if not req_ctx:
        return db_ctx
    protected = {
        "business_name",
        "tagline",
        "tone_of_voice",
        "tone_profile",
        "restaurant_theme",
        "primary_color",
        "secondary_color",
        "brand_colors",
        "palette_source",
        "brand_logo_url",
        "specialties",
    }
    for k, v in req_ctx.items():
        if k in protected:
            continue
        db_ctx[k] = v
    return db_ctx


def _brand_lock_suffix(ctx: dict) -> str:
    palette = ctx.get("brand_colors") or []
    palette_str = ", ".join([str(c).strip() for c in palette if str(c).strip()][:6])
    return (
        "\n\nBRAND LOCK (HARD RULES — treat violations as invalid):\n"
        f'- Business name must be visible/mentioned: "{ctx.get("business_name")}".\n'
        f'- Tagline must appear verbatim on-screen (end card or overlay): "{ctx.get("tagline")}".\n'
        f'- Use brand tone: "{ctx.get("tone_of_voice")}".\n'
        f"- Use brand color palette (HEX) for overlays/end card: {palette_str}.\n"
        f'- Show brand logo/end-card using provided logo reference: "{ctx.get("brand_logo_url")}".\n'
        "- Do NOT introduce other brand names, logos, or unrelated palettes.\n"
    )


# ==================== Request/Response Schemas ====================

class ReelPromptRequest(BaseModel):
    """Request to generate a Reel prompt/script"""
    idea: str = Field(..., description="Reel idea or campaign description", min_length=10)
    brand_context: Optional[dict] = Field(None, description="Optional brand information")


class ReelPromptResponse(BaseModel):
    """Response containing generated Reel prompt"""
    success: bool
    reel_prompt: str
    timestamp: str


class ReelGenerationRequest(BaseModel):
    """Request to generate Reel video"""
    reel_prompt: str = Field(..., description="Detailed Reel production prompt")
    campaign_id: Optional[str] = Field(None, description="Optional campaign ID")
    count: int = Field(1, ge=1, le=3, description="Number of variations (1-3)")
    duration_seconds: int = Field(8, ge=4, le=8, description="Duration in seconds (4-8 max)")


class VideoPromptRequest(BaseModel):
    """Request to generate a Video prompt"""
    idea: str = Field(..., description="Video idea or campaign description", min_length=10)
    aspect_ratio: Literal["16:9", "1:1"] = Field("16:9", description="Video aspect ratio")
    brand_context: Optional[dict] = Field(None, description="Optional brand information")


class VideoPromptResponse(BaseModel):
    """Response containing generated Video prompt"""
    success: bool
    video_prompt: str
    aspect_ratio: str
    timestamp: str


class VideoGenerationRequest(BaseModel):
    """Request to generate Video"""
    video_prompt: str = Field(..., description="Detailed video production prompt")
    campaign_id: Optional[str] = Field(None, description="Optional campaign ID")
    aspect_ratio: Literal["16:9", "1:1"] = Field("16:9", description="Video aspect ratio")
    count: int = Field(1, ge=1, le=3, description="Number of variations (1-3)")
    duration_seconds: int = Field(8, ge=4, le=8, description="Duration in seconds (4-8 max)")


class QuickReelRequest(BaseModel):
    """Request for one-step quick reel generation"""
    idea: str = Field(..., description="Reel concept", min_length=10)
    duration_seconds: int = Field(8, ge=4, le=8, description="Duration in seconds (4-8 max)")


class MediaGenerationResponse(BaseModel):
    """Response for Reel/Video generation"""
    success: bool
    message: str
    media_paths: list[str]
    asset_ids: list[str] = Field(default_factory=list, description="Asset IDs for usage tracking")
    campaign_id: str
    duration_seconds: int
    count: int
    timestamp: str


class ErrorResponse(BaseModel):
    """Error response"""
    success: bool = False
    error: str
    detail: Optional[str] = None


# ==================== Reel Endpoints ====================

@router.post(
    "/reels/generate-prompt",
    response_model=ReelPromptResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        401: {"description": "Not authenticated"},
        500: {"model": ErrorResponse, "description": "Generation failed"}
    }
)
async def generate_reel_prompt(
    request: ReelPromptRequest,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Generate an Instagram Reel script/prompt using Gemini AI.
    
    **Input:**
    - `idea`: Your Reel concept (min 10 characters)
    - `brand_context`: Optional brand information for consistency
    
    **Output:**
    - Detailed Reel production prompt optimized for 4-8 second vertical video
    - Includes hook, scene description, camera movements, timing, CTA
    
    **Example:**
    ```json
    {
      "idea": "Quick workout transformation showing before/after",
      "brand_context": {
        "business_name": "FitLife Gym",
        "tone_of_voice": "Energetic and motivating"
      }
    }
    ```
    """
    try:
        service = get_reel_generation_service()
        
        # Fetch user's onboarding brand context
        brand_context = await get_user_brand_context(current_user_email)
        brand_context = _safe_merge_request_brand_context(brand_context, request.brand_context)
        _require_brand_lock(brand_context)
        
        reel_prompt = service.generate_reel_prompt(
            user_input=request.idea,
            brand_context=brand_context if brand_context else None
        )
        
        return ReelPromptResponse(
            success=True,
            reel_prompt=reel_prompt,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "Failed to generate Reel prompt",
                "detail": str(e)
            }
        ) from e


@router.post(
    "/reels/generate",
    response_model=MediaGenerationResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        401: {"description": "Not authenticated"},
        500: {"model": ErrorResponse, "description": "Generation failed"}
    }
)
async def generate_reels(
    request: ReelGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Generate Instagram Reel videos using Veo 3.1.
    
    **Specifications:**
    - ⏱️ Duration: 4-8 seconds (Veo 3.1 Fast limit)
    - 📱 Aspect Ratio: 9:16 (vertical)
    - 🎬 Format: MP4
    - ⏳ Processing Time: 2-5 minutes per video
    
    **Input:**
    - `reel_prompt`: Detailed production prompt (from /generate-prompt)
    - `count`: Number of variations (1-3)
    - `duration_seconds`: Video length (4-8 seconds)
    
    **Output:**
    - List of file paths for generated Reels
    - Videos saved to `generated_reels/CAMPAIGN_ID/`
    
    **Note:** This endpoint may take several minutes to complete.
    """
    try:
        service = get_reel_generation_service()
        brand_context = await get_user_brand_context(current_user_email)
        _require_brand_lock(brand_context)
        
        # Generate campaign ID if not provided
        campaign_id = request.campaign_id or f"reel_{uuid.uuid4().hex[:12]}"

        # Enforce brand lock on any user-provided prompt by appending constraints.
        reel_prompt = (request.reel_prompt or "").strip() + _brand_lock_suffix(brand_context)
        
        # Generate Reels synchronously (frontend will wait)
        # For production, consider using background tasks or webhooks
        results = service.generate_reels_sync(
            reel_prompt=reel_prompt,
            output_folder=f"generated_reels/{campaign_id}",
            count=request.count,
            duration_seconds=request.duration_seconds
        )
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "error": "No Reels were generated",
                    "detail": "Check API quota and logs for errors"
                }
            )
        
        # Save reels to Asset Library (MongoDB)
        try:
            asset_ids = await service.save_reels_as_assets(
                reel_paths=results,
                user_id=current_user_email,
                reel_prompt=reel_prompt,
                campaign_idea=request.campaign_id or campaign_id,
                duration_seconds=request.duration_seconds
            )
        except Exception as e:
            # Log error but don't fail the request - reels are already generated
            print(f"Warning: Failed to save reels to Asset Library: {e}")
        
        return MediaGenerationResponse(
            success=True,
            message=f"Successfully generated {len(results)} Reel(s)",
            media_paths=_paths_to_urls(results),
            campaign_id=campaign_id,
            duration_seconds=request.duration_seconds,
            count=len(results),
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "Failed to generate Reels",
                "detail": str(e)
            }
        ) from e


# ==================== Video Endpoints ====================

@router.post(
    "/videos/generate-prompt",
    response_model=VideoPromptResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        401: {"description": "Not authenticated"},
        500: {"model": ErrorResponse, "description": "Generation failed"}
    }
)
async def generate_video_prompt(
    request: VideoPromptRequest,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Generate a video production prompt using Gemini AI.
    
    **Input:**
    - `idea`: Your video concept (min 10 characters)
    - `aspect_ratio`: "16:9" (horizontal) or "1:1" (square)
    - `brand_context`: Optional brand information
    
    **Output:**
    - Detailed video production prompt for Veo 3.1
    - Optimized for the selected aspect ratio
    
    **Use Cases:**
    - **16:9**: YouTube, Facebook, LinkedIn videos
    - **1:1**: Instagram feed, Facebook posts
    """
    try:
        service = get_video_generation_service()
        
        # Fetch user's onboarding brand context
        brand_context = await get_user_brand_context(current_user_email)
        brand_context = _safe_merge_request_brand_context(brand_context, request.brand_context)
        _require_brand_lock(brand_context)
        
        video_prompt = service.generate_video_prompt(
            user_input=request.idea,
            brand_context=brand_context if brand_context else None,
            aspect_ratio=request.aspect_ratio
        )
        
        return VideoPromptResponse(
            success=True,
            video_prompt=video_prompt,
            aspect_ratio=request.aspect_ratio,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "Failed to generate video prompt",
                "detail": str(e)
            }
        ) from e


@router.post(
    "/videos/generate",
    response_model=MediaGenerationResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        401: {"description": "Not authenticated"},
        500: {"model": ErrorResponse, "description": "Generation failed"}
    }
)
async def generate_videos(
    request: VideoGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Generate videos using Veo 3.1.
    
    **Specifications:**
    - ⏱️ Duration: 4-8 seconds (Veo 3.1 Fast limit)
    - 📐 Aspect Ratios: 16:9 (horizontal) or 1:1 (square)
    - 🎬 Format: MP4
    - ⏳ Processing Time: 2-5 minutes per video
    
    **Input:**
    - `video_prompt`: Detailed production prompt (from /generate-prompt)
    - `aspect_ratio`: "16:9" or "1:1"
    - `count`: Number of variations (1-3)
    - `duration_seconds`: Video length (4-8 seconds)
    
    **Output:**
    - List of file paths for generated videos
    - Videos saved to `generated_videos/CAMPAIGN_ID/`
    
    **Note:** This endpoint may take several minutes to complete.
    """
    try:
        service = get_video_generation_service()
        brand_context = await get_user_brand_context(current_user_email)
        _require_brand_lock(brand_context)
        
        # Generate campaign ID if not provided
        campaign_id = request.campaign_id or f"video_{uuid.uuid4().hex[:12]}"

        # Enforce brand lock on any user-provided prompt by appending constraints.
        video_prompt = (request.video_prompt or "").strip() + _brand_lock_suffix(brand_context)
        
        # Generate videos synchronously
        results = service.generate_videos_sync(
            video_prompt=video_prompt,
            output_folder=str(service.output_folder / campaign_id),
            count=request.count,
            aspect_ratio=request.aspect_ratio,
            duration_seconds=request.duration_seconds
        )
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "error": "No videos were generated",
                    "detail": "Check API quota and logs for errors"
                }
            )
        
        # Save videos to Asset Library (MongoDB)
        asset_ids = []
        try:
            asset_ids = await service.save_videos_as_assets(
                video_paths=results,
                user_id=current_user_email,
                video_prompt=video_prompt,
                campaign_idea=request.campaign_id or campaign_id,
                aspect_ratio=request.aspect_ratio,
                duration_seconds=request.duration_seconds
            )
        except Exception as e:
            # Log error but don't fail the request - videos are already generated
            print(f"Warning: Failed to save videos to Asset Library: {e}")
        
        return MediaGenerationResponse(
            success=True,
            message=f"Successfully generated {len(results)} video(s)",
            media_paths=_paths_to_urls(results),
            asset_ids=asset_ids,
            campaign_id=campaign_id,
            duration_seconds=request.duration_seconds,
            count=len(results),
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "Failed to generate videos",
                "detail": str(e)
            }
        ) from e


# ==================== Quick Generation Endpoint ====================

@router.post(
    "/generate-quick-reel",
    response_model=MediaGenerationResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def generate_quick_reel(
    request: QuickReelRequest,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    **Quick Reel Generation** - One-step Reel creation.
    
    Combines prompt generation + video generation in a single request.
    Perfect for simple use cases where you just want a quick Reel.
    
    **Input:**
    - `idea`: Your Reel concept
    - `duration_seconds`: 4-8 seconds (default 8)
    
    **Output:**
    - Generated Reel video path
    
    **Note:** Takes 2-5 minutes to complete.
    """
    try:
        service = get_reel_generation_service()
        
        # Fetch user's onboarding brand context for richer prompts
        brand_context = await get_user_brand_context(current_user_email)
        _require_brand_lock(brand_context)
        
        # Step 1: Generate prompt enriched with brand context
        reel_prompt = service.generate_reel_prompt(
            user_input=request.idea,
            brand_context=brand_context if brand_context else None
        )
        
        # Step 2: Generate Reel
        campaign_id = f"quick_{uuid.uuid4().hex[:8]}"
        results = service.generate_reels_sync(
            reel_prompt=reel_prompt,
            output_folder=str(service.output_folder / campaign_id),
            count=1,
            duration_seconds=request.duration_seconds
        )
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"success": False, "error": "Failed to generate Reel"}
            )
        
        # Save to Asset Library (MongoDB + Cloudinary)
        try:
            await service.save_reels_as_assets(
                reel_paths=results,
                user_id=current_user_email,
                reel_prompt=reel_prompt,
                campaign_idea=request.idea,
                duration_seconds=request.duration_seconds
            )
        except Exception as e:
            print(f"Warning: Failed to save quick reel to Asset Library: {e}")
        
        return MediaGenerationResponse(
            success=True,
            message="Quick Reel generated successfully",
            media_paths=_paths_to_urls(results),
            campaign_id=campaign_id,
            duration_seconds=request.duration_seconds,
            count=1,
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "Failed to generate quick Reel",
                "detail": str(e)
            }
        ) from e
