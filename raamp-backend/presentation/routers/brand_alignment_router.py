"""
Brand Alignment Router - handles brand identity settings
"""
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
import os
import shutil
import uuid
# from application.services.firebase_storage_service import FirebaseStorageService
from infrastructure.repositories.business_repository import BusinessRepository
from presentation.schemas.brand_alignment_schema import BrandAlignmentRequest, BrandAlignmentResponse
from presentation.routers.auth_router import get_current_user_id


router = APIRouter(prefix="/api/brand-alignment", tags=["Brand Alignment"])


@router.post("/upload-logo")
async def upload_brand_logo(
    logo: UploadFile = File(..., description="Brand logo (SVG, PNG, JPG, max 2MB)"),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Upload brand logo to Local Storage
    
    Returns the local path of the uploaded logo
    """
    try:
        # Define save directory
        SAVE_DIR = "uploaded_files/brand_logos"
        os.makedirs(SAVE_DIR, exist_ok=True)
        
        # Generate unique filename
        file_extension = os.path.splitext(logo.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(SAVE_DIR, unique_filename)
        
        # Save file locally
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(logo.file, buffer)
            
        # Return relative URL
        return {
            "success": True,
            "logo_url": f"/api/static/brand_logos/{unique_filename}"
        }
    
    except Exception as e:
        print(f"Error uploading logo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload logo: {str(e)}"
        ) from e


@router.post("/save", response_model=BrandAlignmentResponse)
async def save_brand_alignment(
    request: BrandAlignmentRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Save brand alignment settings (ALL fields required)
    
    Fields:
    - brand_logo_url: Firebase Storage URL of uploaded logo (use /upload-logo first)
    - primary_color: Hex color code (#RRGGBB)
    - secondary_color: Hex color code (#RRGGBB)
    - tagline: Restaurant tagline (1-100 chars)
    - tone_of_voice: Tone description for AI content
    - restaurant_theme: Restaurant theme/ambiance description (REQUIRED)
    """
    try:
        # Create repository instance
        business_repo = BusinessRepository()
        
        # Save to database
        business = await business_repo.update_brand_alignment(
            user_id=current_user_id,
            brand_logo_url=request.brand_logo_url,
            primary_color=request.primary_color,
            secondary_color=request.secondary_color,
            tagline=request.tagline,
            tone_of_voice=request.tone_of_voice,
            restaurant_theme=request.restaurant_theme,
            brand_colors=request.brand_colors,
            palette_source=request.palette_source
        )
        
        return BrandAlignmentResponse(
            brand_logo_url=business.brand_logo_url,
            primary_color=business.primary_color,
            secondary_color=business.secondary_color,
            tagline=business.tagline,
            tone_of_voice=business.tone_of_voice,
            restaurant_theme=business.restaurant_theme,
            brand_colors=business.brand_colors,
            palette_source=business.palette_source,
            updated_at=business.updated_at.isoformat()
        )
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        print(f"Error saving brand alignment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save brand alignment settings"
        ) from e


@router.get("/settings", response_model=BrandAlignmentResponse)
async def get_brand_alignment(
    current_user_id: str = Depends(get_current_user_id)
):
    """Get current brand alignment settings"""
    business_repo = BusinessRepository()
    business = await business_repo.get_by_user_id(current_user_id)
    
    if not business or not business.brand_logo_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand alignment settings not found"
        )
    
    return BrandAlignmentResponse(
        brand_logo_url=business.brand_logo_url,
        primary_color=business.primary_color,
        secondary_color=business.secondary_color,
        tagline=business.tagline,
        tone_of_voice=business.tone_of_voice,
        restaurant_theme=business.restaurant_theme,
        brand_colors=business.brand_colors,
        palette_source=business.palette_source,
        updated_at=business.updated_at.isoformat()
    )
