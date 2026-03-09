"""
Billing Router - handles billing profile and wallet/add-funds endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status

from presentation.schemas.settings_schemas import (
    BillingProfileRequest,
    BillingProfileResponse,
    BillingProfileGetResponse,
    WalletBalanceResponse,
    ErrorResponse
)
from presentation.routers.auth_router import get_current_user_email
from infrastructure.repositories.billing_profile_repository import BillingProfileRepository
from infrastructure.repositories.wallet_repository import WalletRepository


router = APIRouter(prefix="/api/billing", tags=["Billing"])


# ============================================
# BILLING PROFILE ENDPOINTS
# ============================================

@router.get(
    "",
    response_model=BillingProfileGetResponse,
    responses={404: {"model": ErrorResponse}}
)
async def get_billing_profile(
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Get billing profile for the current user.
    
    Returns all billing information including:
    - Personal/Company info
    - Address details
    - Tax information
    - Payment method (masked)
    """
    try:
        repo = BillingProfileRepository()
        profile = await repo.get_by_user_id(current_user_email)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Billing profile not found. Please set up your billing information first."
            )
        
        return BillingProfileGetResponse(
            success=True,
            full_name=profile.full_name,
            company_name=profile.company_name,
            email=profile.email,
            phone=profile.phone,
            address_line1=profile.address_line1,
            address_line2=profile.address_line2,
            city=profile.city,
            state=profile.state,
            postal_code=profile.postal_code,
            country=profile.country,
            tax_id=profile.tax_id,
            payment_method_type=profile.payment_method_type,
            card_last_four=profile.card_last_four,
            card_expiry_month=profile.card_expiry_month,
            card_expiry_year=profile.card_expiry_year,
            updated_at=profile.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching billing profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch billing profile"
        ) from e


@router.post(
    "",
    response_model=BillingProfileResponse,
    responses={400: {"model": ErrorResponse}}
)
async def save_billing_profile(
    request: BillingProfileRequest,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Save or update billing profile for the current user.
    
    All fields are required:
    - Personal info: full_name, company_name, email, phone
    - Address: address_line1, address_line2, city, state, postal_code, country
    - Tax: tax_id
    - Payment: payment_method_type, card_last_four, card_expiry_month, card_expiry_year
    """
    try:
        repo = BillingProfileRepository()
        profile = await repo.create_or_update(
            user_id=current_user_email,
            full_name=request.full_name,
            company_name=request.company_name,
            email=request.email,
            phone=request.phone,
            address_line1=request.address_line1,
            address_line2=request.address_line2,
            city=request.city,
            state=request.state,
            postal_code=request.postal_code,
            country=request.country,
            tax_id=request.tax_id,
            payment_method_type=request.payment_method_type,
            card_last_four=request.card_last_four,
            card_expiry_month=request.card_expiry_month,
            card_expiry_year=request.card_expiry_year
        )
        
        # Return masked data for security
        return BillingProfileResponse(
            success=True,
            message="Billing profile saved successfully",
            data={
                "full_name": profile.full_name,
                "company_name": profile.company_name,
                "email": profile.email,
                "phone": f"***-***-{profile.phone[-4:]}" if len(profile.phone) >= 4 else "****",
                "address": f"{profile.city}, {profile.state}, {profile.country}",
                "payment_method": f"{profile.payment_method_type} ending in {profile.card_last_four}",
                "card_expiry": f"{profile.card_expiry_month:02d}/{profile.card_expiry_year}"
            },
            updated_at=profile.updated_at.isoformat()
        )
        
    except Exception as e:
        print(f"Error saving billing profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save billing profile"
        ) from e


# ============================================
# WALLET / ADD FUNDS ENDPOINTS
# ============================================

@router.get(
    "/wallet",
    response_model=WalletBalanceResponse
)
async def get_wallet_balance(
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Get current wallet balance for the user.
    
    Returns:
    - Current balance
    - Currency
    - Last transaction timestamp
    """
    try:
        repo = WalletRepository()
        wallet = await repo.get_or_create(current_user_email)
        
        return WalletBalanceResponse(
            success=True,
            balance=round(wallet.balance, 2),
            currency=wallet.currency,
            last_transaction_at=wallet.last_transaction_at.isoformat() if wallet.last_transaction_at else None
        )
        
    except Exception as e:
        print(f"Error fetching wallet balance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch wallet balance"
        ) from e
