"""
Settings Router - handles notification and security settings endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
import logging

from presentation.schemas.settings_schemas import (
    NotificationSettingsRequest,
    NotificationSettingsResponse,
    NotificationSettingsGetResponse,
    SecuritySettingsRequest,
    SecuritySettingsResponse,
    SecuritySettingsGetResponse,
    ErrorResponse,
    SpecialtiesUpdateRequest,
    SpecialtiesUpdateResponse
)
from presentation.routers.auth_router import get_current_user_email
from infrastructure.repositories.notification_settings_repository import NotificationSettingsRepository
from infrastructure.repositories.security_settings_repository import SecuritySettingsRepository
from infrastructure.database.models.business_model import BusinessModel


router = APIRouter(prefix="/api/settings", tags=["Settings"])
logger = logging.getLogger(__name__)


# ============================================
# NOTIFICATION SETTINGS ENDPOINTS
# ============================================

@router.get(
    "/notifications",
    response_model=NotificationSettingsGetResponse,
    responses={}
)
async def get_notification_settings(
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Get notification settings for the current user.
    
    Returns all notification preferences including:
    - Email alerts
    - SMS alerts
    - Push notifications
    - Marketing alerts
    """
    try:
        repo = NotificationSettingsRepository()
        settings = await repo.get_by_user_id(current_user_email)
        
        if not settings:
            # Auto-create defaults on first run (avoid a 404 UX)
            settings = await repo.create_or_update(
                user_id=current_user_email,
                email_alerts=True,
                sms_alerts=False,
                push_notifications=True,
                marketing_alerts=False,
                campaign_alerts=True,
                performance_alerts=True,
                trend_alerts=True,
                billing_alerts=True,
            )
        
        return NotificationSettingsGetResponse(
            success=True,
            email_alerts=settings.email_alerts,
            sms_alerts=settings.sms_alerts,
            push_notifications=settings.push_notifications,
            marketing_alerts=settings.marketing_alerts,
            campaign_alerts=getattr(settings, "campaign_alerts", True),
            performance_alerts=getattr(settings, "performance_alerts", True),
            trend_alerts=getattr(settings, "trend_alerts", True),
            billing_alerts=getattr(settings, "billing_alerts", True),
            updated_at=settings.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error fetching notification settings")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch notification settings"
        ) from e


@router.post(
    "/notifications",
    response_model=NotificationSettingsResponse,
    responses={400: {"model": ErrorResponse}}
)
async def save_notification_settings(
    request: NotificationSettingsRequest,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Save or update notification settings for the current user.
    
    All fields are required:
    - email_alerts: Enable/disable email notifications
    - sms_alerts: Enable/disable SMS notifications
    - push_notifications: Enable/disable push notifications
    - marketing_alerts: Enable/disable marketing/promotional notifications
    """
    try:
        repo = NotificationSettingsRepository()
        settings = await repo.create_or_update(
            user_id=current_user_email,
            email_alerts=request.email_alerts,
            sms_alerts=request.sms_alerts,
            push_notifications=request.push_notifications,
            marketing_alerts=request.marketing_alerts,
            campaign_alerts=request.campaign_alerts,
            performance_alerts=request.performance_alerts,
            trend_alerts=request.trend_alerts,
            billing_alerts=request.billing_alerts
        )
        
        return NotificationSettingsResponse(
            success=True,
            message="Notification settings saved successfully",
            data={
                "email_alerts": settings.email_alerts,
                "sms_alerts": settings.sms_alerts,
                "push_notifications": settings.push_notifications,
                "marketing_alerts": settings.marketing_alerts,
                "campaign_alerts": settings.campaign_alerts,
                "performance_alerts": settings.performance_alerts,
                "trend_alerts": settings.trend_alerts,
                "billing_alerts": settings.billing_alerts
            },
            updated_at=settings.updated_at.isoformat()
        )
        
    except Exception as e:
        logger.exception("Error saving notification settings")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save notification settings"
        ) from e


# ============================================
# SECURITY SETTINGS ENDPOINTS
# ============================================

@router.get(
    "/security",
    response_model=SecuritySettingsGetResponse,
    responses={}
)
async def get_security_settings(
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Get security settings for the current user.
    
    Returns all security preferences including:
    - Two-factor authentication status
    - Login alerts
    - Session timeout
    - Trusted devices only mode
    - Password change requirement
    """
    try:
        repo = SecuritySettingsRepository()
        settings = await repo.get_by_user_id(current_user_email)
        
        if not settings:
            # Auto-create defaults on first run (avoid a 404 UX)
            settings = await repo.create_or_update(
                user_id=current_user_email,
                two_factor_enabled=False,
                login_alerts=True,
                session_timeout_minutes=60,
                trusted_devices_only=False,
                password_change_required=False,
            )
        
        return SecuritySettingsGetResponse(
            success=True,
            two_factor_enabled=settings.two_factor_enabled,
            login_alerts=settings.login_alerts,
            session_timeout_minutes=settings.session_timeout_minutes,
            trusted_devices_only=settings.trusted_devices_only,
            password_change_required=settings.password_change_required,
            updated_at=settings.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error fetching security settings")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch security settings"
        ) from e


@router.post(
    "/security",
    response_model=SecuritySettingsResponse,
    responses={400: {"model": ErrorResponse}}
)
async def save_security_settings(
    request: SecuritySettingsRequest,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Save or update security settings for the current user.
    
    All fields are required:
    - two_factor_enabled: Enable/disable two-factor authentication
    - login_alerts: Enable/disable new login alerts
    - session_timeout_minutes: Session timeout in minutes (5-1440)
    - trusted_devices_only: Allow login only from trusted devices
    - password_change_required: Require periodic password changes
    """
    try:
        repo = SecuritySettingsRepository()
        settings = await repo.create_or_update(
            user_id=current_user_email,
            two_factor_enabled=request.two_factor_enabled,
            login_alerts=request.login_alerts,
            session_timeout_minutes=request.session_timeout_minutes,
            trusted_devices_only=request.trusted_devices_only,
            password_change_required=request.password_change_required
        )
        
        return SecuritySettingsResponse(
            success=True,
            message="Security settings saved successfully",
            data={
                "two_factor_enabled": settings.two_factor_enabled,
                "login_alerts": settings.login_alerts,
                "session_timeout_minutes": settings.session_timeout_minutes,
                "trusted_devices_only": settings.trusted_devices_only,
                "password_change_required": settings.password_change_required
            },
            updated_at=settings.updated_at.isoformat()
        )
        
    except Exception as e:
        logger.exception("Error saving security settings")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save security settings"
        ) from e


# ============================================
# BUSINESS SPECIALTIES ENDPOINTS
# ============================================

@router.patch(
    "/business/specialties",
    response_model=SpecialtiesUpdateResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}}
)
async def update_business_specialties(
    request: SpecialtiesUpdateRequest,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Update business specialties for enhanced trend detection.
    
    Specialties are optional keywords that help the trend detection system
    find more relevant opportunities (e.g., "boba", "matcha", "vegan").
    
    Validation rules:
    - Maximum 10 specialties
    - Each specialty max 50 characters
    - Automatically converted to lowercase
    - Duplicates automatically removed
    
    Examples:
    - Restaurant: ["bubble tea", "matcha", "vegan", "sushi"]
    - Fashion: ["streetwear", "vintage", "sustainable"]
    - Fitness: ["yoga", "crossfit", "pilates"]
    """
    try:
        # Find or create business by user email
        business = await BusinessModel.find_one({"user_id": current_user_email})
        
        if not business:
            # Create a minimal business profile if it doesn't exist yet
            # This can happen during onboarding before other steps are completed
            business = BusinessModel(
                user_id=current_user_email,
                business_name="",  # Will be filled in later during onboarding
                business_type="General",
                specialties=[]
            )
            await business.save()
        
        # Validate and clean specialties
        specialties = request.specialties or []
        
        # Validation: Maximum count
        if len(specialties) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 10 specialties allowed"
            )
        
        # Validation: Length per specialty
        for specialty in specialties:
            if len(specialty) > 50:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Specialty '{specialty}' exceeds 50 character limit"
                )
        
        # Clean: Lowercase, deduplicate, trim
        cleaned_specialties = list(dict.fromkeys([
            s.strip().lower() for s in specialties if s.strip()
        ]))
        
        # Update only the specialties field
        business.specialties = cleaned_specialties
        await business.save()
        
        return SpecialtiesUpdateResponse(
            success=True,
            message="Business specialties updated successfully",
            specialties=cleaned_specialties
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error updating business specialties")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update business specialties"
        ) from e


@router.get(
    "/business/specialties",
    response_model=SpecialtiesUpdateResponse,
    responses={404: {"model": ErrorResponse}}
)
async def get_business_specialties(
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Get current business specialties for the authenticated user.
    
    Returns empty list if no specialties configured (backward compatible).
    """
    try:
        business = await BusinessModel.find_one({"user_id": current_user_email})
        
        if not business:
            # Return empty list if no business profile exists yet
            # This can happen during onboarding or for new users
            return SpecialtiesUpdateResponse(
                success=True,
                message="No specialties configured yet",
                specialties=[]
            )
        
        return SpecialtiesUpdateResponse(
            success=True,
            message="Business specialties retrieved successfully",
            specialties=business.specialties or []
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching business specialties: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch business specialties"
        ) from e
