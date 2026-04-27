"""
Creative Assets API Router
Provides access to generated media and captions from AI Creative Studio
Handles file uploads to Firebase Storage and local storage
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
import logging
import uuid
from datetime import datetime
from pathlib import Path

from presentation.routers.auth_router import get_current_user_email
from application.constants import PaginationDefaults
from application.services.cloudinary_service import CloudinaryService
from application.utils.file_manager import FileManager
from application.utils.path_resolver import resolve_asset_path
from infrastructure.repositories.asset_repository import AssetRepository
from infrastructure.repositories.caption_log_repository import CaptionLogRepository
from infrastructure.database.models.asset_model import AssetType, GenerationSource, AssetModel
from infrastructure.database.models.caption_log_model import AssetTypeEnum
from config import settings, Config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/assets", tags=["creative-assets"])

# Initialize services
cloudinary_service = CloudinaryService()
asset_repository = AssetRepository()
caption_log_repository = CaptionLogRepository()

class MediaAsset(BaseModel):
    id: str
    url: str
    type: str  # "image" or "video"
    title: str
    created_at: str
    width: Optional[int] = None
    height: Optional[int] = None
    size_bytes: Optional[int] = None

class CaptionAsset(BaseModel):
    """Saved caption asset from AI generation"""
    caption_id: str
    caption_text: str
    hashtags: List[str]
    tone: str
    asset_type: str  # "post", "story", "reel", etc.
    platform: str  # deprecated, use asset_type
    created_at: str
    campaign_id: Optional[str] = None
    campaign_idea: Optional[str] = None
    times_used: int
    is_favorite: bool
    predicted_performance: Optional[str] = None

class MediaAssetsResponse(BaseModel):
    assets: List[MediaAsset]
    total: int

class CaptionAssetsResponse(BaseModel):
    captions: List[CaptionAsset]
    total: int

class UploadResponse(BaseModel):
    asset_id: str
    cloudinary_url: Optional[str] = None
    public_url: str # The prioritized public URL for sharing
    local_path: str
    filename: str
    content_type: str
    size_bytes: int
    # Auto-cropping metadata
    is_auto_cropped: bool = False
    original_dims: Optional[dict] = None
    transformed_dims: Optional[dict] = None
    cloudinary_original_url: Optional[str] = None

@router.post("/upload", response_model=UploadResponse)
async def upload_media(
    file: UploadFile = File(...),
    upload_type: str = Query("content", regex="^(content|logo|profile)$"),
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Upload media file to user-specific organized storage.
    
    Saves to:
    - Local: uploaded_files/{sanitized_email}/{upload_type}/{timestamp}_{filename}
    - Cloudinary: users/{sanitized_email}/{upload_type}/{filename}
    
    Args:
        file: The file to upload
        upload_type: Type of upload - 'content' (posts), 'logo' (brand), or 'profile'
        
    Returns public URL and metadata for the uploaded file.
    """
    logger.info(f"📤 Upload request from user: {current_user_email}, file: {file.filename}, type: {upload_type}, content_type: {file.content_type}")
    
    try:
        # Map upload_type to subfolder
        subfolder_map = {
            'content': 'content',
            'logo': 'logos',
            'profile': 'profiles'
        }
        subfolder = subfolder_map[upload_type]
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Validate file type for specific subfolder
        FileManager.validate_file_type(file.content_type, subfolder)
        
        # Validate file size for specific subfolder
        FileManager.validate_file_size(file_size, subfolder)
        
        # Reset file pointer
        await file.seek(0)
        
        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_ext = Path(file.filename).suffix if file.filename else ".jpg"
        unique_id = str(uuid.uuid4())[:8]
        new_filename = f"{timestamp}_{unique_id}{file_ext}"
        
        # Get user-specific upload path
        local_dir = FileManager.get_user_upload_path(
            email=current_user_email,
            subfolder=subfolder,
            create=True
        )
        local_path = local_dir / new_filename
        
        with open(local_path, "wb") as f:
            f.write(file_content)
        
        # 1. Upload to Cloudinary (Primary for public access if configured)
        cloudinary_url = None
        cloudinary_original_url = None
        is_auto_cropped = False
        original_dims = None
        transformed_dims = None
        
        if cloudinary_service.is_available:
            logger.info("Attempting Cloudinary upload...")
            # Use organized user-specific Cloudinary folder
            cloudinary_folder = FileManager.get_cloudinary_folder(current_user_email, subfolder)
            
            # Determine if this is for stories (needs special handling)
            is_story_upload = (upload_type == 'content')  # Assume content uploads might be for stories
            
            cloudinary_data = cloudinary_service.upload_file_from_bytes(
                file_content=file_content,
                folder=cloudinary_folder,
                filename=new_filename,
                validate_aspect_ratio=is_story_upload,  # Validate for content posts
                optimize_for_stories=False  # Don't force resize, let Instagram handle it
            )
            
            if cloudinary_data:
                cloudinary_original_url = cloudinary_data["secure_url"]
                cloudinary_url = cloudinary_original_url  # Initial default
                
                logger.info(f"📸 Cloudinary upload result:")
                logger.info(f"  Original URL: {cloudinary_original_url}")
                logger.info(f"  Public ID: {cloudinary_data.get('public_id')}")
                
                width = cloudinary_data.get("width")
                height = cloudinary_data.get("height")
                resource_type = cloudinary_data.get("resource_type")
                
                if width and height and resource_type == "image":
                    ratio = width / height
                    original_dims = {"w": width, "h": height, "ratio": round(ratio, 2)}
                    
                    # CRITICAL: Validate the original Cloudinary URL structure BEFORE transformation
                    logger.info(f"🔍 Validating original Cloudinary URL structure:")
                    logger.info(f"  URL: {cloudinary_original_url}")
                    
                    # Check if URL has proper structure
                    if "/upload/" not in cloudinary_original_url:
                        logger.error(f"❌ Cloudinary URL missing '/upload/' segment - cannot transform")
                        cloudinary_url = cloudinary_original_url
                    else:
                        # Split and validate
                        url_parts = cloudinary_original_url.split("/upload/")
                        if len(url_parts) == 2:
                            resource_path = url_parts[1]
                            path_segments = resource_path.split('/')
                            
                            logger.info(f"  Resource path: {resource_path}")
                            logger.info(f"  Path segments: {path_segments}")
                            logger.info(f"  Number of segments: {len(path_segments)}")
                            
                            # Valid Cloudinary paths should have at least:
                            # - v{version}/{folder}/{file}.{ext} (3 segments)
                            # - {folder}/{file}.{ext} (2 segments)
                            # Invalid: just v{version} (1 segment)
                            if len(path_segments) < 2:
                                logger.error(f"❌ INVALID Cloudinary URL structure detected!")
                                logger.error(f"  Resource path only has {len(path_segments)} segment(s): {resource_path}")
                                logger.error(f"  Expected at minimum: folder/file.ext or v123/folder/file.ext")
                                logger.error(f"  This URL will NOT be transformed to avoid Instagram API errors")
                                cloudinary_url = cloudinary_original_url
                            else:
                                # URL structure is valid
                                # IMPORTANT: Skip aspect ratio transformation to avoid Cloudinary HTTP 400 errors
                                # Instagram can handle various aspect ratios (0.8 to 1.91) natively
                                # Cloudinary transformations with ar_ parameter are causing issues
                                
                                logger.info(f"✅ Cloudinary URL structure is valid")
                                logger.info(f"  Image dimensions: {width}x{height} (ratio: {ratio:.2f})")
                                logger.info(f"  Instagram supports ratios from 0.8 (4:5) to 1.91 (1.91:1)")
                                
                                # Check if image is within Instagram's acceptable range
                                if 0.8 <= ratio <= 1.91:
                                    logger.info(f"✅ Image ratio {ratio:.2f} is within Instagram's acceptable range")
                                    logger.info(f"  Using original Cloudinary URL without transformation")
                                    cloudinary_url = cloudinary_original_url
                                else:
                                    logger.warning(f"⚠️ Image ratio {ratio:.2f} is outside Instagram's range (0.8-1.91)")
                                    logger.warning(f"  Instagram may crop this image automatically")
                                    logger.warning(f"  Using original URL - Instagram will handle cropping")
                                    cloudinary_url = cloudinary_original_url
                        else:
                            logger.error(f"❌ URL split failed - expected 2 parts, got {len(url_parts)}")
                            cloudinary_url = cloudinary_original_url
                
                logger.info(f"✓ Cloudinary upload complete. Auto-cropped: {is_auto_cropped}")
            else:
                logger.warning("Cloudinary upload failed, check credentials or logs.")
        else:
            logger.info("Cloudinary service not available (missing credentials).")
        
            
        # 3. Determine prioritized public URL
        # Preference: Cloudinary (reliable public HTTPS) → Local Tunnel/Localhost
        if cloudinary_url:
            public_url = cloudinary_url
            logger.info(f"Using Cloudinary URL as primary: {public_url}")
        else:
            # Fallback to local file URL (using BACKEND_URL which could be a tunnel)
            # Use new user-specific folder structure
            sanitized_email = FileManager.sanitize_email_for_folder(current_user_email)
            public_url = f"{settings.BACKEND_URL}/api/static/{sanitized_email}/{subfolder}/{new_filename}"
            logger.info(f"Using local/tunnel fallback URL: {public_url}")
            
            # Critical warnings for Instagram posting
            if "localhost" in public_url or "127.0.0.1" in public_url:
                logger.error("❌ CRITICAL: Using LOCALHOST URL. Instagram CANNOT access this! Use Cloudinary or ngrok/localtunnel.")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Media URL is not publicly accessible. Instagram requires public URLs. Please configure Cloudinary or use a tunnel service (ngrok/localtunnel)."
                )
            elif "loca.lt" in public_url:
                logger.warning("⚠️  WARNING: Using localtunnel URL. If Instagram fails, the interstitial page may be blocking access.")
        
        # Generate asset ID
        asset_id = str(uuid.uuid4())
        
        return UploadResponse(
            asset_id=asset_id,
            cloudinary_url=cloudinary_url,
            public_url=public_url,
            local_path=str(local_path),
            filename=new_filename,
            content_type=file.content_type,
            size_bytes=file_size,
            is_auto_cropped=is_auto_cropped,
            original_dims=original_dims,
            transformed_dims=transformed_dims,
            cloudinary_original_url=cloudinary_original_url
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File upload failed"
        )

def _public_asset_url(asset: AssetModel) -> str:
    """Prefer CDN URLs; resolve relative API paths against BACKEND_URL."""
    raw = asset.cloudinary_url or asset.firebase_url or asset.storage_url or ""
    if not raw:
        return ""
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    if raw.startswith("/"):
        base = settings.BACKEND_URL.rstrip("/")
        return f"{base}{raw}"
    return raw


@router.get("/media", response_model=MediaAssetsResponse)
async def get_media_assets(
    current_user_email: str = Depends(get_current_user_email),
    limit: int = Query(PaginationDefaults.DEFAULT_LIMIT_LARGE, ge=1, le=PaginationDefaults.MAX_LIMIT_MEDIUM),
    asset_type: Optional[str] = Query(None, regex="^(image|video)$")
):
    """
    List media assets for the current user from the assets collection (AI-generated and uploads).
    URLs prefer Cloudinary/Firebase; local `storage_url` paths are prefixed with BACKEND_URL.
    """
    try:
        logger.info("Fetching media assets for user: %s, type: %s", current_user_email, asset_type)

        if asset_type == "image":
            type_filter = [AssetType.GENERATED_IMAGE, AssetType.UPLOADED_IMAGE]
        elif asset_type == "video":
            type_filter = [AssetType.GENERATED_VIDEO, AssetType.GENERATED_REEL, AssetType.UPLOADED_VIDEO]
        else:
            type_filter = [
                AssetType.GENERATED_IMAGE,
                AssetType.UPLOADED_IMAGE,
                AssetType.GENERATED_VIDEO,
                AssetType.GENERATED_REEL,
                AssetType.UPLOADED_VIDEO,
            ]

        rows = await asset_repository.get_by_user_id(
            user_id=current_user_email,
            limit=limit,
            asset_types=type_filter,
        )

        assets: List[MediaAsset] = []
        for a in rows:
            url = _public_asset_url(a)
            if not url:
                continue
            kind = "video" if a.asset_type in (
                AssetType.GENERATED_VIDEO,
                AssetType.GENERATED_REEL,
                AssetType.UPLOADED_VIDEO,
            ) else "image"
            gp = (a.generation_prompt or "")[:80] if a.generation_prompt else ""
            title = a.file_name or gp or "Media"
            assets.append(
                MediaAsset(
                    id=a.asset_id,
                    url=url,
                    type=kind,
                    title=title,
                    created_at=a.created_at.isoformat() if a.created_at else datetime.utcnow().isoformat(),
                    width=a.width,
                    height=a.height,
                    size_bytes=a.file_size_bytes,
                )
            )

        return MediaAssetsResponse(assets=assets, total=len(assets))

    except Exception as e:
        logger.exception("Error fetching media assets: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve media assets"
        )

@router.get("/captions", response_model=CaptionAssetsResponse)
async def get_caption_assets(
    current_user_email: str = Depends(get_current_user_email),
    limit: int = Query(PaginationDefaults.DEFAULT_LIMIT_LARGE, ge=1, le=PaginationDefaults.MAX_LIMIT_MEDIUM),
    asset_type: Optional[str] = Query(None, description="Filter by asset type: post, story, reel"),
    campaign_id: Optional[str] = Query(None, description="Filter by campaign ID")
):
    """
    Get saved captions from AI Creative Studio.
    Returns AI-generated captions that can be reused for posts.
    
    Supports filtering by:
    - asset_type: post, story, reel
    - campaign_id: specific campaign identifier
    """
    try:
        logger.info(f"Fetching caption assets for user: {current_user_email}, asset_type: {asset_type}, limit: {limit}")
        
        # Convert asset_type string to enum if provided
        asset_type_filter = None
        if asset_type:
            try:
                asset_type_filter = AssetTypeEnum(asset_type.lower())
            except ValueError:
                logger.warning(f"Invalid asset_type: {asset_type}, ignoring filter")
        
        # Retrieve captions from database
        captions = await caption_log_repository.get_by_user_id(
            user_id=current_user_email,
            limit=limit,
            asset_type=asset_type_filter,
            campaign_id=campaign_id
        )
        
        # Convert to response format
        caption_responses = []
        for caption in captions:
            caption_responses.append(CaptionAsset(
                caption_id=caption.caption_id,
                caption_text=caption.caption_text,
                hashtags=caption.hashtags,
                tone=caption.tone,
                asset_type=caption.asset_type.value,
                platform=caption.asset_type.value,  # For backward compatibility
                created_at=caption.created_at.isoformat(),
                campaign_id=caption.campaign_id,
                campaign_idea=caption.campaign_idea,
                times_used=caption.times_used,
                is_favorite=caption.is_favorite,
                predicted_performance=caption.predicted_performance
            ))
        
        logger.info(f"✅ Retrieved {len(caption_responses)} captions for user")
        
        return CaptionAssetsResponse(
            captions=caption_responses,
            total=len(caption_responses)
        )
    
    except Exception as e:
        logger.exception(f"Error fetching caption assets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve captions"
        )

@router.post("/captions/{caption_id}/use")
async def mark_caption_used(
    caption_id: str,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Mark a caption as used (increment usage counter).
    Called when user selects and uses a caption for posting.
    """
    try:
        # Verify caption belongs to user
        caption = await caption_log_repository.get_by_caption_id(caption_id)
        if not caption:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Caption not found"
            )
        
        if caption.user_id != current_user_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this caption"
            )
        
        # Increment usage
        success = await caption_log_repository.increment_usage(caption_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update caption usage"
            )
        
        return {"success": True, "message": "Caption usage recorded"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error marking caption as used: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update caption"
        )

@router.post("/captions/{caption_id}/favorite")
async def toggle_caption_favorite(
    caption_id: str,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Toggle favorite status for a caption.
    """
    try:
        # Verify caption belongs to user
        caption = await caption_log_repository.get_by_caption_id(caption_id)
        if not caption:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Caption not found"
            )
        
        if caption.user_id != current_user_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this caption"
            )
        
        # Toggle favorite
        success = await caption_log_repository.toggle_favorite(caption_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update caption favorite status"
            )
        
        # Get updated status
        updated_caption = await caption_log_repository.get_by_caption_id(caption_id)
        
        return {
            "success": True,
            "is_favorite": updated_caption.is_favorite,
            "message": "Favorite status updated"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error toggling caption favorite: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update caption"
        )

# ============================================================================
# ASSET LIBRARY ENDPOINTS
# ============================================================================

class AssetResponse(BaseModel):
    """Response model for a single asset"""
    model_config = ConfigDict(protected_namespaces=())
    
    asset_id: str
    storage_url: str
    cloudinary_url: Optional[str] = None
    firebase_url: Optional[str] = None
    file_name: str
    file_size_bytes: int
    content_type: str
    width: Optional[int] = None
    height: Optional[int] = None
    asset_type: str
    generation_source: str
    generation_prompt: Optional[str] = None
    campaign_idea: Optional[str] = None
    variation_number: Optional[int] = None
    model_used: Optional[str] = None
    times_used: int
    last_used_at: Optional[str] = None
    tags: List[str]
    is_favorite: bool
    created_at: str
    updated_at: str


class AssetsLibraryResponse(BaseModel):
    """Response model for asset library"""
    assets: List[AssetResponse]
    total: int
    page: int
    per_page: int


@router.get("/library", response_model=AssetsLibraryResponse)
async def get_asset_library(
    current_user_email: str = Depends(get_current_user_email),
    page: int = Query(PaginationDefaults.DEFAULT_PAGE, ge=1),
    per_page: int = Query(PaginationDefaults.DEFAULT_PER_PAGE, ge=1, le=PaginationDefaults.MAX_PER_PAGE),
    asset_type: Optional[str] = Query(None),
    source: Optional[str] = Query(None)
):
    """
    Get all assets for the current user with pagination and filtering.
    
    Args:
        page: Page number (starts at 1)
        per_page: Items per page
        asset_type: Filter by asset type (generated_image, uploaded_image, etc.)
        source: Filter by generation source (AI, user_upload)
    """
    try:
        skip = (page - 1) * per_page
        
        # Parse filters — support 'video' as a combined type for generated_video + generated_reel
        VIDEO_TYPES = [AssetType.GENERATED_VIDEO, AssetType.GENERATED_REEL]
        asset_type_filter = None
        asset_types_filter = None
        if asset_type == "video":
            asset_types_filter = VIDEO_TYPES
        elif asset_type:
            asset_type_filter = AssetType(asset_type)
        source_filter = GenerationSource(source) if source else None
        
        # Fetch assets
        assets = await asset_repository.get_by_user_id(
            user_id=current_user_email,
            limit=per_page,
            skip=skip,
            asset_type=asset_type_filter,
            asset_types=asset_types_filter,
            generation_source=source_filter
        )
        
        # Get total count
        total = await asset_repository.count_user_assets(
            user_id=current_user_email,
            asset_type=asset_type_filter,
            asset_types=asset_types_filter
        )
        
        # Convert to response format
        asset_responses = []
        for asset in assets:
            asset_responses.append(AssetResponse(
                asset_id=asset.asset_id,
                storage_url=asset.storage_url,
                cloudinary_url=asset.cloudinary_url,
                firebase_url=asset.firebase_url,
                file_name=asset.file_name,
                file_size_bytes=asset.file_size_bytes,
                content_type=asset.content_type,
                width=asset.width,
                height=asset.height,
                asset_type=asset.asset_type.value,
                generation_source=asset.generation_source.value,
                generation_prompt=asset.generation_prompt,
                campaign_idea=asset.campaign_idea,
                variation_number=asset.variation_number,
                model_used=asset.model_used,
                times_used=asset.times_used,
                last_used_at=asset.last_used_at.isoformat() if asset.last_used_at else None,
                tags=asset.tags,
                is_favorite=asset.is_favorite,
                created_at=asset.created_at.isoformat(),
                updated_at=asset.updated_at.isoformat()
            ))
        
        return AssetsLibraryResponse(
            assets=asset_responses,
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception:
        logger.exception("Error fetching asset library")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve asset library",
        )


class RescanResponse(BaseModel):
    """Response from filesystem rescan"""
    success: bool
    imported: int
    skipped: int
    errors: int
    message: str


@router.post("/rescan", response_model=RescanResponse)
async def rescan_generated_files(
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Scan the generated_reels/ and generated_videos/ directories on disk and
    create missing asset records in MongoDB for any .mp4 files found.
    Useful for recovering assets after a failed save.
    """
    imported = 0
    skipped = 0
    errors = 0

    scan_dirs = [
        (Config.GENERATED_REELS_DIR, AssetType.GENERATED_REEL, "/api/reels/"),
        (Config.GENERATED_VIDEOS_DIR, AssetType.GENERATED_VIDEO, "/api/videos/"),
    ]

    for folder_path, asset_type, url_prefix in scan_dirs:
        folder = Path(folder_path)
        if not folder.exists():
            continue

        for mp4_file in folder.rglob("*.mp4"):
            try:
                # Derive the storage URL from the relative path inside the folder
                rel = mp4_file.relative_to(folder)
                storage_url = f"{url_prefix}{str(rel).replace(chr(92), '/')}"

                # Check if a record already exists for this URL
                existing = await AssetModel.find_one(AssetModel.storage_url == storage_url)
                if existing:
                    skipped += 1
                    continue

                asset_data = {
                    "asset_id": str(uuid.uuid4()),
                    "user_id": current_user_email,
                    "file_path": str(mp4_file),
                    "storage_url": storage_url,
                    "cloudinary_url": None,
                    "firebase_url": None,
                    "file_name": mp4_file.name,
                    "file_size_bytes": mp4_file.stat().st_size,
                    "content_type": "video/mp4",
                    "asset_type": asset_type,
                    "generation_source": GenerationSource.AI,
                    "generation_prompt": None,
                    "campaign_idea": mp4_file.parent.name,
                    "variation_number": None,
                    "model_used": None,
                    "times_used": 0,
                    "tags": [],
                    "is_favorite": False,
                }
                doc = AssetModel(**asset_data)
                await doc.insert()
                imported += 1
                logger.info("Rescan imported %s as %s", storage_url, asset_type.value)

            except Exception as exc:
                logger.error("Rescan failed for %s: %s", mp4_file, exc)
                errors += 1

    return RescanResponse(
        success=True,
        imported=imported,
        skipped=skipped,
        errors=errors,
        message=f"Rescan complete: {imported} imported, {skipped} already in library, {errors} errors."
    )


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset_details(
    asset_id: str,
    current_user_email: str = Depends(get_current_user_email)
):
    """Get details of a specific asset"""
    try:
        asset = await asset_repository.get_by_asset_id(asset_id)
        
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found"
            )
        
        # Verify ownership
        if asset.user_id != current_user_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return AssetResponse(
            asset_id=asset.asset_id,
            storage_url=asset.storage_url,
            cloudinary_url=asset.cloudinary_url,
            firebase_url=asset.firebase_url,
            file_name=asset.file_name,
            file_size_bytes=asset.file_size_bytes,
            content_type=asset.content_type,
            width=asset.width,
            height=asset.height,
            asset_type=asset.asset_type.value,
            generation_source=asset.generation_source.value,
            generation_prompt=asset.generation_prompt,
            campaign_idea=asset.campaign_idea,
            variation_number=asset.variation_number,
            model_used=asset.model_used,
            times_used=asset.times_used,
            last_used_at=asset.last_used_at.isoformat() if asset.last_used_at else None,
            tags=asset.tags,
            is_favorite=asset.is_favorite,
            created_at=asset.created_at.isoformat(),
            updated_at=asset.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error fetching asset details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve asset"
        )


@router.get("/{asset_id}/download")
async def download_asset(
    asset_id: str,
    current_user_email: str = Depends(get_current_user_email)
):
    """Download an asset file"""
    try:
        asset = await asset_repository.get_by_asset_id(asset_id)
        
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found"
            )
        
        # Verify ownership
        if asset.user_id != current_user_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Check if file exists - handle legacy paths
        file_path = resolve_asset_path(asset.file_path)
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found on server"
            )
        
        # Return file for download
        return FileResponse(
            path=str(file_path),
            filename=asset.file_name,
            media_type=asset.content_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error downloading asset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download asset"
        )


@router.post("/{asset_id}/favorite")
async def toggle_asset_favorite(
    asset_id: str,
    current_user_email: str = Depends(get_current_user_email)
):
    """Toggle favorite status on an asset"""
    try:
        asset = await asset_repository.get_by_asset_id(asset_id)
        if not asset:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
        if asset.user_id != current_user_email:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        asset.is_favorite = not asset.is_favorite
        asset.updated_at = datetime.utcnow()
        await asset.save()

        return {"success": True, "is_favorite": asset.is_favorite}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error toggling asset favorite: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle favorite"
        )


@router.post("/{asset_id}/use")
async def mark_asset_used(
    asset_id: str,
    current_user_email: str = Depends(get_current_user_email)
):
    """Mark an asset as used (increments usage counter)"""
    try:
        asset = await asset_repository.get_by_asset_id(asset_id)
        
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found"
            )
        
        # Verify ownership
        if asset.user_id != current_user_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Increment usage
        await asset_repository.increment_usage(asset_id)
        
        return {"success": True, "message": "Asset usage recorded"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error marking asset used: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update asset"
        )


@router.delete("/{asset_id}")
async def delete_asset(
    asset_id: str,
    current_user_email: str = Depends(get_current_user_email)
):
    """Delete an asset"""
    try:
        asset = await asset_repository.get_by_asset_id(asset_id)
        
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found"
            )
        
        # Verify ownership
        if asset.user_id != current_user_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Delete file from filesystem - handle legacy paths
        file_path = resolve_asset_path(asset.file_path)
        
        if file_path.exists():
            file_path.unlink()
        
        # Delete from database
        await asset_repository.delete(asset_id)
        
        return {"success": True, "message": "Asset deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error deleting asset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete asset"
        )