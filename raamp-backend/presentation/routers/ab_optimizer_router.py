"""
A/B Test Optimizer API Router
==============================
REST API endpoints for restaurant marketing image A/B testing.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import os
import shutil
from pathlib import Path
import uuid
from datetime import datetime, timedelta

from presentation.routers.auth_router import get_current_user_email
from application.utils.rate_limiter import limiter
from fastapi import Request
from application.use_cases.ab_test_optimizer_use_case import get_ab_optimizer_use_case
from application.services.cloudinary_service import CloudinaryService
from infrastructure.services.scheduling_lookup_service import (
    get_schedule_recommendation,
    get_next_optimal_posting_time
)
from infrastructure.services.winner_calculation_service import get_winner_service
from infrastructure.services.ad_brief_generation_service import get_ad_brief_service
from infrastructure.repositories.ab_test_repository import get_ab_test_repository
from application.services.notification_service import NotificationService
from infrastructure.database.models.notification_model import NotificationType
from domain.entities.ab_test_image import EngagementMetrics
from infrastructure.repositories.asset_repository import AssetRepository
from domain.utils.scoring_logic import get_scoring_config, generate_test_advice, is_irrelevant
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ab-optimizer", tags=["ab-optimizer"])

# Services initialized on-demand (lazy loading)
_cloudinary_service = None
_winner_service = None
_ad_brief_service = None


def get_services():
    """Lazy initialization of services"""
    global _cloudinary_service, _winner_service, _ad_brief_service
    
    if _cloudinary_service is None:
        _cloudinary_service = CloudinaryService()
    if _winner_service is None:
        _winner_service = get_winner_service()
    if _ad_brief_service is None:
        _ad_brief_service = get_ad_brief_service()
    
    return {
        'cloudinary': _cloudinary_service,
        'winner': _winner_service,
        'ad_brief': _ad_brief_service,
    }


class ImageScoreResponse(BaseModel):
    """Response for a single image analysis"""
    image_id: str
    filename: str
    content_type: str
    scores: Dict[str, float]
    why_good: str
    why_bad: str
    recommendation: str
    image_url: Optional[str] = None


class AnalyzeFromLibraryRequest(BaseModel):
    """Request body for analyzing images from asset library."""
    image_ids: List[str] = Field(..., min_length=2, max_length=5, description="Asset IDs from user's library")


class BatchAnalysisResponse(BaseModel):
    """Response for batch analysis with A/B test recommendations"""
    batch_id: str
    images: List[ImageScoreResponse]
    total_images: int
    
    # A/B Test Recommendation
    recommended_pair: Optional[List[str]] = Field(None, description="Top 2 image IDs to A/B test")
    score_gap: Optional[float] = Field(None, description="Score difference between top 2")
    test_advice: Optional[str] = Field(None, description="Recommendation text")
    
    # Warnings
    irrelevant_images: List[Dict[str, Any]] = Field(default_factory=list, description="Images with low restaurant relevance")


class BatchSummary(BaseModel):
    """Summary of a previously analyzed batch"""
    batch_id: str
    image_count: int
    created_at: str
    recommended_pair: Optional[List[str]] = None
    score_gap: Optional[float] = None
    schedule_id: Optional[str] = None


class CostEstimateResponse(BaseModel):
    """Cost estimate for analyzing images"""
    num_images: int
    estimated_cost_usd: float


def _build_batch_response(batch: Any) -> BatchAnalysisResponse:
    """Helper to convert ABTestBatch entity to BatchAnalysisResponse DTO"""
    images_response = []
    irrelevant_images = []
    
    for img in batch.images:
        img_response = ImageScoreResponse(
            image_id=img.image_id,
            filename=img.filename,
            content_type=img.content_type.value,
            scores={
                "restaurant_relevance": img.scores.restaurant_relevance,
                "viral_potential": img.scores.viral_potential,
                "aesthetic_quality": img.scores.aesthetic_quality,
                "composite_score": img.scores.composite_score
            },
            why_good=img.why_good,
            why_bad=img.why_bad,
            recommendation=img.recommendation,
            image_url=img.image_url
        )
        images_response.append(img_response)
        
        # Flag irrelevant images using centralized logic
        if is_irrelevant(img.scores.restaurant_relevance):
            irrelevant_images.append({
                "filename": img.filename,
                "relevance_score": img.scores.restaurant_relevance,
                "reason": img.why_bad
            })
    
    # Generate test advice using centralized logic
    test_advice = None
    if batch.recommended_pair and batch.score_gap is not None:
        test_advice = generate_test_advice(batch.score_gap)
    
    return BatchAnalysisResponse(
        batch_id=batch.batch_id,
        images=images_response,
        total_images=len(images_response),
        recommended_pair=list(batch.recommended_pair) if batch.recommended_pair else None,
        score_gap=batch.score_gap,
        test_advice=test_advice,
        irrelevant_images=irrelevant_images
    )
    estimated_cost_usd: float
    cost_per_image_usd: float
    model: str


@router.get("/config")
async def get_ab_optimizer_config():
    """Get centralized scoring thresholds and labels for the frontend"""
    return get_scoring_config()


@router.post("/upload-and-analyze", response_model=BatchAnalysisResponse)
@limiter.limit("5/minute")
async def upload_and_analyze_batch(
    request: Request,
    files: List[UploadFile] = File(..., description="2-5 images to analyze"),
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Upload 2-5 images and analyze them for A/B testing potential.
    
    **Process:**
    1. Validates image count (2-5 required)
    2. Saves images to user's directory
    3. Uploads to Cloudinary for permanent storage
    4. Analyzes with GPT-4o Vision API
    5. Ranks by composite score
    6. Recommends top 2 for A/B testing
    
    **Returns:**
    - Ranked list of images with scores
    - A/B test recommendations
    - Warnings for irrelevant content
    """
    logger.info(f"📤 A/B Optimizer: {current_user_email} uploaded {len(files)} images")
    
    # Validate file count
    if len(files) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A/B testing requires at least 2 images"
        )
    
    if len(files) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 5 images allowed per batch"
        )
    
    # Validate file sizes (10MB limit)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    for file in files:
        # Check size if available (FastAPI UploadFile.size)
        if file.size and file.size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File {file.filename} is too large. Max size is 10MB."
            )
    
    # Get services (lazy initialization)
    services = get_services()
    cloudinary_service = services['cloudinary']
    ab_optimizer = get_ab_optimizer_use_case()
    
    # Validate file types
    allowed_types = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
    for file in files:
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type: {file.filename}. Allowed: JPEG, PNG, WebP"
            )
    
    # Save files temporarily
    temp_dir = Path("uploaded_files") / "ab_optimizer_temp" / str(uuid.uuid4())
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    images_data = []
    
    try:
        for file in files:
            # Save to temp location
            temp_path = temp_dir / file.filename
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Upload to Cloudinary
            try:
                sanitized_email = current_user_email.replace("@", "_at_").replace(".", "_")
                cloudinary_folder = f"users/{sanitized_email}/ab_optimizer"
                
                # Upload to Cloudinary using file path to save memory
                cloudinary_result = cloudinary_service.upload_file(
                    file=str(temp_path),
                    folder=cloudinary_folder,
                    filename=file.filename,
                    validate_aspect_ratio=False
                )
                
                image_url = cloudinary_result.get("secure_url") if cloudinary_result else None
                logger.info(f"✅ Uploaded to Cloudinary: {file.filename}")
                
            except Exception as e:
                logger.warning(f"⚠️  Cloudinary upload failed for {file.filename}: {str(e)}")
                image_url = None
            
            images_data.append({
                "path": str(temp_path),
                "filename": file.filename,
                "url": image_url
            })
        
        # Analyze batch
        batch = await ab_optimizer.analyze_batch(images_data, current_user_email)
        
        # Build response using helper
        response = _build_batch_response(batch)
        
        logger.info(f"✅ Batch analysis complete: {batch.batch_id}")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Batch analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )
    
    finally:
        # Cleanup temp files
        try:
            shutil.rmtree(temp_dir)
            logger.info("🧹 Cleaned up temp files")
        except Exception as e:
            logger.warning(f"⚠️  Failed to cleanup temp files: {str(e)}")


@router.post("/analyze-from-library", response_model=BatchAnalysisResponse)
@limiter.limit("5/minute")
async def analyze_from_library(
    request: Request,
    body: AnalyzeFromLibraryRequest = Body(...),
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Analyze images from the user's existing assets library.
    
    **Use Case:** User has already uploaded images to RAAMP's Creative Assets
    and wants to compare them for A/B testing.
    
    Args:
        body: Request containing list of 2-5 asset IDs from the user's library
    """
    image_ids = body.image_ids
    logger.info(f"📚 A/B Optimizer: {current_user_email} analyzing {len(image_ids)} images from library")
    
    # Validate count
    if len(image_ids) < 2:
        raise HTTPException(status_code=400, detail="Select at least 2 images")
    if len(image_ids) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 images allowed")
        
    asset_repo = AssetRepository()
    ab_optimizer = get_ab_optimizer_use_case()
    
    images_data = []
    
    for asset_id in image_ids:
        asset = await asset_repo.get_by_asset_id(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
        
        if asset.user_id != current_user_email:
            raise HTTPException(status_code=403, detail=f"Access denied to asset {asset_id}")
            
        # Determine public URL (logic same as assets_router)
        url = asset.cloudinary_url or asset.firebase_url or asset.storage_url or ""
        if not (url.startswith("http://") or url.startswith("https://")):
            if url.startswith("/"):
                base = settings.BACKEND_URL.rstrip("/")
                url = f"{base}{url}"
        
        images_data.append({
            "path": asset.file_path,
            "filename": asset.file_name,
            "url": url
        })
        
    try:
        batch = await ab_optimizer.analyze_batch(images_data, current_user_email)
        
        # Build response using helper
        return _build_batch_response(batch)
        
    except Exception as e:
        logger.error(f"❌ Batch analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batch/{batch_id}", response_model=BatchAnalysisResponse)
async def get_batch_results(
    batch_id: str,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Retrieve results of a previously analyzed batch.
    
    Useful for:
    - Reviewing past A/B test recommendations
    - Accessing analysis without re-running expensive API calls
    """
    ab_optimizer = get_ab_optimizer_use_case()
    batch = await ab_optimizer.get_batch(batch_id, current_user_email)
    
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found or access denied"
        )
    
    # Build response using helper
    return _build_batch_response(batch)


@router.get("/batches", response_model=List[BatchSummary])
async def get_user_batches(
    limit: int = 20,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Get all A/B test batches for the current user.
    
    Returns a summary list without full image details.
    Use GET /batch/{batch_id} to get full details.
    """
    ab_optimizer = get_ab_optimizer_use_case()
    batches = await ab_optimizer.get_user_batches(current_user_email, limit)
    
    summaries = []
    for batch in batches:
        summaries.append(BatchSummary(
            batch_id=batch["batch_id"],
            image_count=batch.get("image_count", 0),
            created_at=batch["created_at"].isoformat(),
            recommended_pair=batch.get("recommended_pair"),
            score_gap=batch.get("score_gap"),
            schedule_id=batch.get("schedule_id")
        ))
    
    return summaries


@router.get("/cost-estimate", response_model=CostEstimateResponse)
async def estimate_analysis_cost(
    num_images: int,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Estimate OpenAI API cost for analyzing a given number of images.
    
    **Pricing (as of 2024):**
    - GPT-4o Vision (high detail): ~$0.00765 per image
    
    Use this before analyzing large batches to set user expectations.
    """
    if num_images < 1 or num_images > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="num_images must be between 1 and 100"
        )
    
    ab_optimizer = get_ab_optimizer_use_case()
    estimate = ab_optimizer.estimate_cost(num_images)
    
    return CostEstimateResponse(**estimate)


# =====================================================
# STAGE 2: Schedule Recommendation Endpoint
# =====================================================

class ScheduleRecommendationRequest(BaseModel):
    """Request for schedule recommendation"""
    batch_id: str
    platform: str = Field(..., description="instagram, facebook, or tiktok")
    niche: str = Field(default="restaurant", description="restaurant, food, fitness, retail, general")


class ScheduleRecommendationResponse(BaseModel):
    """Response with optimal posting schedule"""
    days: str
    time_range: str
    confidence: str
    source: str
    next_optimal: Dict[str, str]  # {"day": "Tuesday", "time": "11 AM - 1 PM"}


@router.post("/schedule-recommendation", response_model=ScheduleRecommendationResponse)
async def get_schedule_recommendation_endpoint(
    req: ScheduleRecommendationRequest,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    **Stage 2: Get optimal posting schedule based on platform and niche.**
    
    Uses pre-loaded lookup tables from published platform studies.
    Returns one optimal time applied to all variants.
    """
    ab_optimizer = get_ab_optimizer_use_case()
    
    # Verify batch ownership
    batch = await ab_optimizer.get_batch(req.batch_id, current_user_email)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    # Get schedule recommendation
    schedule = get_schedule_recommendation(req.platform, req.niche)
    next_day, next_time = get_next_optimal_posting_time(req.platform, req.niche)
    
    return ScheduleRecommendationResponse(
        days=", ".join(schedule.days),
        time_range=schedule.time_range,
        confidence=schedule.confidence,
        source=schedule.source,
        next_optimal={"day": next_day, "time": next_time}
    )


# =====================================================
# STAGE 3: Confirm & Schedule Test Endpoint
# =====================================================

class ConfirmScheduleRequest(BaseModel):
    """Request to confirm and schedule A/B test"""
    batch_id: str
    variant_a_image_id: str
    variant_b_image_id: str
    platform: str
    variant_a_post_time: datetime
    variant_b_post_time: datetime
    post_time: Optional[datetime] = None  # backward compat
    caption: Optional[str] = None  # Keep for backward compatibility
    caption_a: Optional[str] = None
    caption_b: Optional[str] = None
    test_duration_hours: int = 48
    campaign_id: Optional[str] = None


class ConfirmScheduleResponse(BaseModel):
    """Response after scheduling test"""
    schedule_id: str
    status: str
    post_time: datetime
    message: str


@router.post("/confirm-schedule", response_model=ConfirmScheduleResponse)
async def confirm_schedule(
    req: ConfirmScheduleRequest,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    **Stage 3: User confirms schedule and posts go into queue.**
    
    Creates scheduled test entry. Integration with Instagram/Facebook posting
    will publish posts automatically at the specified time.
    """
    repository = get_ab_test_repository()
    
    # Verify batch ownership via the raw batch doc (avoids image-query issues)
    batch_doc = await repository.get_batch(req.batch_id)
    if not batch_doc or batch_doc.get("user_id") != current_user_email:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    # Verify images are in batch using the stored image_ids list
    batch_image_ids = batch_doc.get("image_ids", [])
    if req.variant_a_image_id not in batch_image_ids or req.variant_b_image_id not in batch_image_ids:
        raise HTTPException(status_code=400, detail="Selected images not in batch")
    
    # Create schedule entry
    schedule_id = str(uuid.uuid4())
    schedule_data = {
        "schedule_id": schedule_id,
        "batch_id": req.batch_id,
        "user_id": current_user_email,
        "campaign_id": req.campaign_id,
        "variant_a_image_id": req.variant_a_image_id,
        "variant_b_image_id": req.variant_b_image_id,
        "platform": req.platform,
        "post_time": req.variant_a_post_time,  # Keep for backward compatibility
        "variant_a_post_time": req.variant_a_post_time,
        "variant_b_post_time": req.variant_b_post_time,
        "caption": req.caption or req.caption_a,  # Backward compatibility
        "caption_a": req.caption_a,
        "caption_b": req.caption_b,
        "status": "scheduled",
        "test_duration_hours": req.test_duration_hours,
        "created_at": datetime.utcnow()
    }
    
    await repository.save_schedule(schedule_data)
    
    # Update batch with schedule reference
    await repository.db["ab_test_batches"].update_one(
        {"batch_id": req.batch_id},
        {"$set": {"schedule_id": schedule_id}}
    )
    
    logger.info(f"✅ Scheduled A/B test {schedule_id} for {req.variant_a_post_time}")
    
    return ConfirmScheduleResponse(
        schedule_id=schedule_id,
        status="scheduled",
        post_time=req.variant_a_post_time,
        message=f"A/B test scheduled. Variant A at {req.variant_a_post_time.strftime('%Y-%m-%d %H:%M')}, Variant B at {req.variant_b_post_time.strftime('%Y-%m-%d %H:%M')}."
    )


@router.get("/schedule/{schedule_id}")
async def get_schedule_status(
    schedule_id: str,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    **Stage 4: Get schedule status (scheduled → live → completed).**
    
    Check if posts have been published and test is running.
    """
    repository = get_ab_test_repository()
    schedule = await repository.get_schedule(schedule_id)

    if not schedule or schedule["user_id"] != current_user_email:
        raise HTTPException(status_code=404, detail="Schedule not found")

    # Compute lifecycle status from both variant windows.
    now = datetime.utcnow()
    post_a = schedule.get("variant_a_post_time") or schedule.get("post_time")
    post_b = schedule.get("variant_b_post_time") or schedule.get("post_time")
    duration_hours = int(schedule.get("test_duration_hours", 48) or 48)

    if not post_a or not post_b:
        raise HTTPException(status_code=400, detail="Schedule has invalid post times")

    monitoring_start = min(post_a, post_b)
    monitoring_end = max(post_a, post_b) + timedelta(hours=duration_hours)

    if now < monitoring_start:
        computed_status = "scheduled"
    elif now < monitoring_end:
        computed_status = "active"
    else:
        computed_status = "completed"

    # Persist state transition.
    if schedule.get("status") != computed_status:
        await repository.update_schedule_status(schedule_id, computed_status)
        schedule["status"] = computed_status

    # In-app notifications (one-time) for lifecycle transitions.
    notifier = NotificationService()
    if computed_status == "active" and not schedule.get("notified_live_at"):
        await notifier.create_and_send(
            user_id=current_user_email,
            type=NotificationType.CAMPAIGN,
            title="A/B Test Is Live",
            message="Your A/B test variants are now live. Open Monitor Test to track progress or promote a top variant.",
            related_entity_id=schedule_id,
            metadata={
                "sub_type": "ab_test_live",
                "post_id": schedule_id,
                "platform": schedule.get("platform"),
            },
        )
        await repository.db["ab_test_schedules"].update_one(
            {"schedule_id": schedule_id},
            {"$set": {"notified_live_at": now}}
        )

    if computed_status == "completed" and not schedule.get("notified_completed_at"):
        await notifier.create_and_send(
            user_id=current_user_email,
            type=NotificationType.CAMPAIGN,
            title="A/B Monitoring Completed",
            message="Monitoring has ended. Enter final metrics to pick a winner, or promote a variant now.",
            related_entity_id=schedule_id,
            metadata={
                "sub_type": "ab_test_completed",
                "post_id": schedule_id,
                "platform": schedule.get("platform"),
            },
        )
        await repository.db["ab_test_schedules"].update_one(
            {"schedule_id": schedule_id},
            {"$set": {"notified_completed_at": now}}
        )

    # Enrich monitor payload with pre-ranking and ad-ready info.
    variant_a_doc = await repository.get_by_image_id(schedule["variant_a_image_id"])
    variant_b_doc = await repository.get_by_image_id(schedule["variant_b_image_id"])

    score_a = float(variant_a_doc.get("composite_score", 0.0)) if variant_a_doc else 0.0
    score_b = float(variant_b_doc.get("composite_score", 0.0)) if variant_b_doc else 0.0
    recommended_variant = "variant_a" if score_a >= score_b else "variant_b"
    score_gap = abs(score_a - score_b)
    confidence = "strong" if score_gap >= 1.0 else ("moderate" if score_gap >= 0.4 else "close")

    result = await repository.get_result_by_schedule(schedule_id)

    response = {
        "schedule_id": schedule_id,
        "batch_id": schedule.get("batch_id"),
        "variant_a_image_id": schedule.get("variant_a_image_id"),
        "variant_b_image_id": schedule.get("variant_b_image_id"),
        "platform": schedule.get("platform"),
        "post_time": post_a,
        "variant_a_post_time": post_a,
        "variant_b_post_time": post_b,
        "test_duration_hours": duration_hours,
        "status": computed_status,
        "created_at": schedule.get("created_at"),
        "monitoring_start_time": monitoring_start,
        "monitoring_end_time": monitoring_end,
        "caption_a": schedule.get("caption_a"),
        "caption_b": schedule.get("caption_b"),
        "pre_ranking": {
            "recommended_variant": recommended_variant,
            "score_gap": score_gap,
            "confidence": confidence,
            "variant_a_composite": score_a,
            "variant_b_composite": score_b,
        },
        "variant_a_analysis": {
            "filename": variant_a_doc.get("filename") if variant_a_doc else None,
            "image_url": variant_a_doc.get("image_url") if variant_a_doc else None,
            "composite_score": score_a,
            "restaurant_relevance": float(variant_a_doc.get("restaurant_relevance", 0.0)) if variant_a_doc else 0.0,
            "viral_potential": float(variant_a_doc.get("viral_potential", 0.0)) if variant_a_doc else 0.0,
            "aesthetic_quality": float(variant_a_doc.get("aesthetic_quality", 0.0)) if variant_a_doc else 0.0,
        },
        "variant_b_analysis": {
            "filename": variant_b_doc.get("filename") if variant_b_doc else None,
            "image_url": variant_b_doc.get("image_url") if variant_b_doc else None,
            "composite_score": score_b,
            "restaurant_relevance": float(variant_b_doc.get("restaurant_relevance", 0.0)) if variant_b_doc else 0.0,
            "viral_potential": float(variant_b_doc.get("viral_potential", 0.0)) if variant_b_doc else 0.0,
            "aesthetic_quality": float(variant_b_doc.get("aesthetic_quality", 0.0)) if variant_b_doc else 0.0,
        },
        "stats_template": {
            "fields": ["likes", "comments", "shares", "saves", "reach", "ctr"],
            "formula": "score=(likes*1)+(comments*3)+(shares*5)+(saves*4)+(reach*0.1)+(ctr*10)",
            "notes": "You can promote a variant now using AI pre-ranking, or wait for full monitoring and submit final metrics.",
        },
        "meta_ads_link": "https://business.facebook.com/adsmanager/manage/campaigns",
        "variant_a_ads_link": f"https://business.facebook.com/adsmanager/manage/campaigns?variant={schedule.get('variant_a_image_id')}&source=ab_optimizer",
        "variant_b_ads_link": f"https://business.facebook.com/adsmanager/manage/campaigns?variant={schedule.get('variant_b_image_id')}&source=ab_optimizer",
        "result": None,
    }

    if result:
        result.pop("_id", None)
        response["result"] = result

    # Strip MongoDB ObjectId and serialize datetimes recursively.
    def _serialize(value: Any):
        if isinstance(value, dict):
            return {k: _serialize(v) for k, v in value.items() if k != "_id"}
        if isinstance(value, list):
            return [_serialize(v) for v in value]
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return value

    return _serialize(response)


# =====================================================
# STAGE 5: Winner Calculation Endpoint
# =====================================================

class CalculateWinnerRequest(BaseModel):
    """Request to calculate test winner"""
    schedule_id: str
    variant_a_metrics: Dict[str, Any]  # likes, comments, shares, saves, reach, ctr
    variant_b_metrics: Dict[str, Any]


class WinnerResponse(BaseModel):
    """Response with winner declaration"""
    result_id: str
    winner: str  # "variant_a" or "variant_b"
    winner_image_id: str
    winner_score: float
    loser_score: float
    delta_percentage: float
    confidence_level: str  # "clear_winner", "moderate", "too_close"
    analysis: str


@router.post("/calculate-winner", response_model=WinnerResponse)
async def calculate_winner(
    req: CalculateWinnerRequest,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    **Stage 5: Determine A/B test winner based on engagement metrics.**
    
    Calculates composite scores using weighted formula:
    (likes×1) + (comments×3) + (shares×5) + (saves×4) + (reach×0.1) + (CTR×10)
    
    Confidence levels:
    - < 10% delta: "too_close" - Results inconclusive
    - 10-30%: "moderate" - Clear preference
    - > 30%: "clear_winner" - Statistically significant
    """
    services = get_services()
    winner_service = services['winner']
    repository = get_ab_test_repository()
    
    # Verify schedule ownership
    schedule = await repository.get_schedule(req.schedule_id)
    if not schedule or schedule["user_id"] != current_user_email:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    # Convert to EngagementMetrics objects
    metrics_a = EngagementMetrics(**req.variant_a_metrics)
    metrics_b = EngagementMetrics(**req.variant_b_metrics)
    
    # Calculate winner
    result = winner_service.determine_winner(metrics_a, metrics_b)
    
    # Get winner image ID
    winner_image_id = (
        schedule["variant_a_image_id"]
        if result["winner"] == "variant_a"
        else schedule["variant_b_image_id"]
    )
    
    # Save result
    result_id = str(uuid.uuid4())
    result_data = {
        "result_id": result_id,
        "schedule_id": req.schedule_id,
        "user_id": current_user_email,
        "variant_a_image_id": schedule["variant_a_image_id"],
        "variant_a_metrics": metrics_a.dict(),
        "variant_b_image_id": schedule["variant_b_image_id"],
        "variant_b_metrics": metrics_b.dict(),
        "winner_image_id": winner_image_id,
        "delta_percentage": result["delta_percentage"],
        "confidence_level": result["confidence_level"],
        "completed_at": datetime.utcnow()
    }
    
    await repository.save_result(result_data)
    
    # Update batch with result reference
    await repository.db["ab_test_batches"].update_one(
        {"batch_id": schedule["batch_id"]},
        {"$set": {"result_id": result_id}}
    )
    
    logger.info(f"✅ Winner calculated for schedule {req.schedule_id}: {result['winner']}")
    
    return WinnerResponse(
        result_id=result_id,
        winner=result["winner"],
        winner_image_id=winner_image_id,
        winner_score=result["winner_score"],
        loser_score=result["loser_score"],
        delta_percentage=result["delta_percentage"],
        confidence_level=result["confidence_level"],
        analysis=result["analysis"]
    )


# =====================================================
# STAGE 6: Ad Brief Generation Endpoint
# =====================================================

class GenerateAdBriefRequest(BaseModel):
    """Request to generate ad brief"""
    result_id: str
    platform: str = "instagram"
    custom_budget_daily: Optional[float] = None
    custom_duration_days: Optional[int] = None


class AdBriefResponse(BaseModel):
    """Response with complete ad campaign brief"""
    brief_id: str
    winning_image_id: str
    
    # Targeting
    target_geo: str
    audience_segment: str
    
    # Budget
    suggested_budget_daily: float
    suggested_duration_days: int
    total_spend: float
    
    # Projections
    estimated_reach: str
    estimated_clicks: str
    estimated_ctr: float
    estimated_cost_per_click: str
    
    # Creative
    creative_hook: str
    cta_recommendation: str
    what_not_to_change: str
    
    platform: str
    meta_ads_link: str


@router.post("/generate-ad-brief", response_model=AdBriefResponse)
async def generate_ad_brief(
    req: GenerateAdBriefRequest,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    **Stage 6: Generate paid ad campaign brief from winning variant.**
    
    Integrates with geo-intent module for location targeting.
    Provides budget recommendations, audience segments, and creative guidance.
    
    Returns a ready-to-use brief with link to Meta Ads Manager.
    """
    services = get_services()
    ad_brief_service = services['ad_brief']
    repository = get_ab_test_repository()
    
    # Verify result ownership
    result = await repository.get_result(req.result_id)
    if not result or result["user_id"] != current_user_email:
        raise HTTPException(status_code=404, detail="Result not found")
    
    # Get winning metrics
    winner_variant = "variant_a" if result["winner_image_id"] == result["variant_a_image_id"] else "variant_b"
    winning_metrics_dict = result[f"{winner_variant}_metrics"]
    winning_metrics = EngagementMetrics(**winning_metrics_dict)
    
    # Generate ad brief
    brief = await ad_brief_service.generate_ad_brief(
        user_id=current_user_email,
        winning_image_id=result["winner_image_id"],
        winning_metrics=winning_metrics,
        platform=req.platform,
        budget_daily=req.custom_budget_daily,
        duration_days=req.custom_duration_days
    )
    
    # Save brief
    brief_dict = brief.dict()
    brief_dict["result_id"] = req.result_id
    brief_dict["user_id"] = current_user_email
    await repository.save_ad_brief(brief_dict)
    
    # Update batch with brief reference
    schedule = await repository.get_schedule(result["schedule_id"])
    await repository.db["ab_test_batches"].update_one(
        {"batch_id": schedule["batch_id"]},
        {"$set": {"ad_brief_id": brief.brief_id}}
    )
    
    # Generate Meta Ads link
    meta_ads_link = "https://business.facebook.com/adsmanager/manage/campaigns"
    
    logger.info(f"✅ Generated ad brief {brief.brief_id} for result {req.result_id}")
    
    return AdBriefResponse(
        brief_id=brief.brief_id,
        winning_image_id=brief.winning_image_id,
        target_geo=brief.target_geo,
        audience_segment=brief.audience_segment,
        suggested_budget_daily=brief.suggested_budget_daily,
        suggested_duration_days=brief.suggested_duration_days,
        total_spend=brief.total_spend,
        estimated_reach=brief.estimated_reach,
        estimated_clicks=brief.estimated_clicks,
        estimated_ctr=brief.estimated_ctr,
        estimated_cost_per_click=brief.estimated_cost_per_click,
        creative_hook=brief.creative_hook,
        cta_recommendation=brief.cta_recommendation,
        what_not_to_change=brief.what_not_to_change,
        platform=brief.platform,
        meta_ads_link=meta_ads_link
    )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for A/B Optimizer service.
    
    Verifies:
    - OpenAI API key is configured
    - Service is ready to analyze images
    """
    try:
        # Check if OpenAI key is set
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "unavailable",
                    "error": "OPENAI_API_KEY not configured"
                }
            )
        
        return {
            "status": "healthy",
            "service": "A/B Test Optimizer",
            "model": "gpt-4o",
            "features": [
                "batch_upload",
                "image_analysis",
                "ab_test_recommendations",
                "cost_estimation"
            ]
        }
    
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "error": str(e)
            }
        )
