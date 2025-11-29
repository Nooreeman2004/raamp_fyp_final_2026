"""
Brand Alignment Router - handles brand identity settings
"""
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, status
from application.services.firebase_storage_service import FirebaseStorageService
from infrastructure.repositories.business_repository import BusinessRepository
from presentation.schemas.brand_alignment_schema import BrandAlignmentRequest, BrandAlignmentResponse
from presentation.routers.auth_router import get_current_user_email


router = APIRouter(prefix="/api/brand-alignment", tags=["Brand Alignment"])


@router.post("/upload-logo")
async def upload_brand_logo(
    logo: UploadFile = File(..., description="Brand logo (SVG, PNG, JPG, max 2MB)"),
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Upload brand logo to Firebase Storage
    
    Returns the public URL of the uploaded logo
    """
    try:
        # Read file content
        file_content = await logo.read()
        
        # Create service instance
        firebase_storage = FirebaseStorageService()
        
        # Upload to Firebase
        logo_url = await firebase_storage.upload_logo(
            file_content=file_content,
            file_name=logo.filename,
            user_id=current_user_email
        )
        
        return {
            "success": True,
            "logo_url": logo_url
        }
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        print(f"Error uploading logo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload logo"
        ) from e


@router.post("/save", response_model=BrandAlignmentResponse)
async def save_brand_alignment(
    brand_logo_url: str = Form(..., description="Firebase URL of uploaded logo"),
    primary_color: str = Form(..., description="Primary color hex code"),
    secondary_color: str = Form(..., description="Secondary color hex code"),
    tagline: str = Form(..., description="Restaurant tagline"),
    tone_of_voice: str = Form(..., description="Tone of voice"),
    restaurant_theme: str = Form(None, description="Restaurant theme"),
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Save brand alignment settings (all fields required)
    
    Logo must be uploaded first using /upload-logo endpoint
    """
    try:
        # Validate using Pydantic
        request = BrandAlignmentRequest(
            primary_color=primary_color,
            secondary_color=secondary_color,
            tagline=tagline,
            tone_of_voice=tone_of_voice,
            restaurant_theme=restaurant_theme
        )
        
        # Create repository instance
        business_repo = BusinessRepository()
        
        # Save to database
        business = await business_repo.update_brand_alignment(
            user_id=current_user_email,
            brand_logo_url=brand_logo_url,
            primary_color=request.primary_color,
            secondary_color=request.secondary_color,
            tagline=request.tagline,
            tone_of_voice=request.tone_of_voice,
            restaurant_theme=request.restaurant_theme
        )
        
        return BrandAlignmentResponse(
            brand_logo_url=business.brand_logo_url,
            primary_color=business.primary_color,
            secondary_color=business.secondary_color,
            tagline=business.tagline,
            tone_of_voice=business.tone_of_voice,
            restaurant_theme=business.restaurant_theme,
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
    current_user_email: str = Depends(get_current_user_email)
):
    """Get current brand alignment settings"""
    business_repo = BusinessRepository()
    business = await business_repo.get_by_user_id(current_user_email)
    
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
        updated_at=business.updated_at.isoformat()
    )
