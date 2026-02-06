"""
Billing Router - handles billing profile and wallet/add-funds endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
import uuid
import asyncio
import random

from presentation.schemas.settings_schemas import (
    BillingProfileRequest,
    BillingProfileResponse,
    BillingProfileGetResponse,
    AddFundsRequest,
    AddFundsResponse,
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


@router.post(
    "/add-funds",
    response_model=AddFundsResponse,
    responses={400: {"model": ErrorResponse}}
)
async def add_funds(
    request: AddFundsRequest,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Add funds to user's wallet (SIMULATED - no real payment processing).
    
    This is a mock endpoint that:
    1. Validates the amount
    2. Simulates payment processing with a delay
    3. Updates the wallet balance
    4. Returns transaction details with breadcrumbs
    
    Parameters:
    - amount: Amount to add (must be positive, max 10000)
    """
    try:
        # Generate mock transaction ID
        transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        
        # Get current balance
        repo = WalletRepository()
        wallet = await repo.get_or_create(current_user_email)
        previous_balance = wallet.balance
        
        # Simulate payment processing with breadcrumbs
        breadcrumbs = []
        start_time = datetime.utcnow()
        
        # Step 1: Validate request
        breadcrumbs.append({
            "step": 1,
            "action": "validate_request",
            "status": "success",
            "message": f"Request validated: Adding ${request.amount:.2f}"
        })
        
        # Step 2: Simulate payment gateway connection (mock delay)
        await asyncio.sleep(random.uniform(0.3, 0.8))
        breadcrumbs.append({
            "step": 2,
            "action": "connect_payment_gateway",
            "status": "success",
            "message": "Connected to payment gateway (simulated)"
        })
        
        # Step 3: Simulate payment authorization
        await asyncio.sleep(random.uniform(0.2, 0.5))
        breadcrumbs.append({
            "step": 3,
            "action": "authorize_payment",
            "status": "success",
            "message": f"Payment authorized for ${request.amount:.2f}"
        })
        
        # Step 4: Process payment (mock)
        await asyncio.sleep(random.uniform(0.1, 0.3))
        breadcrumbs.append({
            "step": 4,
            "action": "process_payment",
            "status": "success",
            "message": "Payment processed successfully (simulated)"
        })
        
        # Step 5: Update wallet balance
        updated_wallet = await repo.add_funds(
            user_id=current_user_email,
            amount=request.amount,
            transaction_id=transaction_id
        )
        breadcrumbs.append({
            "step": 5,
            "action": "update_wallet",
            "status": "success",
            "message": f"Wallet updated: ${previous_balance:.2f} → ${updated_wallet.balance:.2f}"
        })
        
        # Calculate processing time
        end_time = datetime.utcnow()
        processing_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Step 6: Complete transaction
        breadcrumbs.append({
            "step": 6,
            "action": "complete_transaction",
            "status": "success",
            "message": f"Transaction {transaction_id} completed"
        })
        
        return AddFundsResponse(
            success=True,
            message="Funds added successfully",
            transaction_id=transaction_id,
            amount_added=request.amount,
            previous_balance=round(previous_balance, 2),
            new_balance=round(updated_wallet.balance, 2),
            processing_time_ms=processing_time_ms,
            breadcrumbs=breadcrumbs,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        print(f"Error adding funds: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add funds to wallet"
        ) from e
