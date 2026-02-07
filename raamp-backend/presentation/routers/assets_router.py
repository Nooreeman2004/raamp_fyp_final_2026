"""
Creative Assets API Router
Provides access to generated media and captions from AI Creative Studio
Handles file uploads to Firebase Storage and local storage
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
import logging
import uuid
from datetime import datetime
from pathlib import Path

from presentation.routers.auth_router import get_current_user_email
from application.services.cloudinary_service import CloudinaryService
from application.utils.file_manager import FileManager
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/assets", tags=["creative-assets"])

# Initialize storage services
cloudinary_service = CloudinaryService()

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
    id: str
    text: str
    platform: str  # "instagram", "facebook", etc.
    created_at: str
    campaign_name: Optional[str] = None
    tone: Optional[str] = None

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
                    
                    # Adaptive Ratio Mapping (Instagram supported: 4:5, 1:1, 1.91:1)
                    # Use integer ratios for Cloudinary: 4:5, 1:1, 191:100
                    target_ar = None
                    cloudinary_ar = None  # Cloudinary-compatible format
                    if ratio <= 0.9:
                        target_ar = "4:5"
                        cloudinary_ar = "4:5"
                        target_val = 0.8
                    elif 0.9 < ratio <= 1.4:
                        target_ar = "1:1"
                        cloudinary_ar = "1:1"
                        target_val = 1.0
                    else:
                        target_ar = "1.91:1"
                        cloudinary_ar = "191:100"  # Cloudinary needs integer ratio
                        target_val = 1.91
                    
                    # Detect if transformation is needed (if original is outside bounds or far from target)
                    # Instagram allows [0.8, 1.91]. If it's in range, we COULD skip, 
                    # but mapping to exactly 4:5, 1:1, or 1.91:1 is more predictable.
                    # We transform if it's > 5% away from the target mapping.
                    if abs(ratio - target_val) > 0.05 or ratio < 0.79 or ratio > 1.92:
                        parts = cloudinary_original_url.split("/upload/")
                        logger.info(f"🔍 URL Transformation Analysis:")
                        logger.info(f"  Splitting URL: {cloudinary_original_url}")
                        logger.info(f"  Number of parts after split: {len(parts)}")
                        
                        if len(parts) == 2:
                            logger.info(f"  Part 0 (base): {parts[0]}")
                            logger.info(f"  Part 1 (path): {parts[1]}")
                            logger.info(f"  Part 1 length: {len(parts[1])}")
                            
                            if len(parts[1]) > 10:  # Ensure we have a valid path
                                # Use auto:best instead of q_100 for better smart compression
                                # Use cloudinary_ar (integer format) for Cloudinary API compatibility
                                transformation = f"c_limit,g_center,ar_{cloudinary_ar},q_auto:best,f_auto"
                                cloudinary_url = f"{parts[0]}/upload/{transformation}/{parts[1]}"
                                logger.info(f"✨ Created transformed URL with ar_{cloudinary_ar}")
                                logger.info(f"  Final URL: {cloudinary_url}")
                                is_auto_cropped = True
                            else:
                                logger.error(f"❌ Part 1 too short ({len(parts[1])} chars), using original")
                                cloudinary_url = cloudinary_original_url
                        else:
                            logger.error(f"❌ URL split failed - expected 2 parts, got {len(parts)}")
                            if len(parts) > 0:
                                for i, part in enumerate(parts):
                                    logger.error(f"  Part {i}: {part[:100]}...")
                            cloudinary_url = cloudinary_original_url
                            
                            # Estimate transformed dims based on standard 1080w
                            t_w = 1080
                            t_h = int(1080 / target_val)
                            transformed_dims = {"w": t_w, "h": t_h, "ratio": target_val, "target": target_ar}
                            logger.info(f"✨ Auto-cropped image to {target_ar} ratio ({original_dims['ratio']} -> {target_val})")
                
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
            detail=f"File upload failed: {str(e)}"
        )

@router.get("/media", response_model=MediaAssetsResponse)
async def get_media_assets(
    current_user_email: str = Depends(get_current_user_email),
    limit: int = Query(50, ge=1, le=100),
    asset_type: Optional[str] = Query(None, regex="^(image|video)$")
):
    """
    Get media assets from Creative Studio.
    Returns generated images/videos that can be used for posting.
    
    TODO: This is a placeholder. Implement actual storage/retrieval from:
    - uploaded_files/content_generated/ directory
    - Or a proper asset management system
    """
    try:
        # TODO: Implement actual asset retrieval
        # For now, return empty list as placeholder
        logger.info(f"Fetching media assets for user: {current_user_email}, type: {asset_type}")
        
        # Placeholder response - implement actual storage integration
        return MediaAssetsResponse(
            assets=[],
            total=0
        )
    
    except Exception as e:
        logger.exception(f"Error fetching media assets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve media assets"
        )

@router.get("/captions", response_model=CaptionAssetsResponse)
async def get_caption_assets(
    current_user_email: str = Depends(get_current_user_email),
    limit: int = Query(50, ge=1, le=100),
    platform: Optional[str] = Query(None)
):
    """
    Get saved captions from AI Creative Studio.
    Returns AI-generated captions that can be reused for posts.
    
    TODO: This integrates with content_generation service
    - Retrieve from database/cache
    - Filter by platform and user
    """
    try:
        logger.info(f"Fetching caption assets for user: {current_user_email}, platform: {platform}")
        
        # TODO: Implement actual caption retrieval from content generation service
        # Placeholder response
        return CaptionAssetsResponse(
            captions=[],
            total=0
        )
    
    except Exception as e:
        logger.exception(f"Error fetching caption assets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve captions"
        )
