"""Admin endpoint to check and fix user verification status"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from infrastructure.repositories.user_repository_impl import UserRepository
from infrastructure.repositories.pending_verification_repository import PendingVerificationRepository
from infrastructure.database.models.user_model import UserModel
from application.services.instagram_graph_api_service import InstagramGraphAPIClient
from datetime import datetime

router = APIRouter(prefix="/admin", tags=["admin"])


class UserStatusResponse(BaseModel):
    email: str
    in_users_collection: bool
    is_verified: bool | None
    in_pending_collection: bool
    needs_fix: bool
    diagnosis: str


class FixResponse(BaseModel):
    email: str
    fixed: bool
    message: str


@router.get("/check-user-status/{email}", response_model=UserStatusResponse)
async def check_user_status(email: EmailStr):
    """
    Check if a user is properly verified or stuck in pending state
    """
    user_repo = UserRepository()
    pending_repo = PendingVerificationRepository()
    
    user = await user_repo.find_by_email(email.lower())
    pending = await pending_repo.find_by_email(email.lower())
    
    in_users = user is not None
    is_verified = user.is_verified if user else None
    in_pending = pending is not None
    
    needs_fix = False
    diagnosis = ""
    
    if user and user.is_verified and not pending:
        diagnosis = "✅ User is properly verified - can sign in normally"
    elif user and not user.is_verified:
        needs_fix = True
        diagnosis = "⚠️ User exists but NOT verified - needs is_verified=True"
    elif pending and not user:
        diagnosis = "⚠️ Still in pending verification - complete email verification"
    elif user and pending:
        needs_fix = True
        diagnosis = "❌ Data inconsistency - user in both collections"
    else:
        diagnosis = "❌ No record found - need to sign up first"
    
    return UserStatusResponse(
        email=email,
        in_users_collection=in_users,
        is_verified=is_verified,
        in_pending_collection=in_pending,
        needs_fix=needs_fix,
        diagnosis=diagnosis
    )


@router.post("/fix-user-verification/{email}", response_model=FixResponse)
async def fix_user_verification(email: EmailStr):
    """
    Fix user verification status:
    1. Set is_verified=True in users collection
    2. Delete from pending_verifications collection
    """
    user_repo = UserRepository()
    pending_repo = PendingVerificationRepository()
    
    user = await user_repo.find_by_email(email.lower())
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    fixed = False
    messages = []
    
    # Fix 1: Set is_verified=True
    if not user.is_verified:
        user_model = await UserModel.find_one(UserModel.email == email.lower())
        if user_model:
            user_model.is_verified = True
            user_model.updated_at = datetime.utcnow()
            await user_model.save()
            messages.append("Set is_verified=True")
            fixed = True
    
    # Fix 2: Delete pending verification
    pending = await pending_repo.find_by_email(email.lower())
    if pending:
        await pending_repo.delete_by_email(email.lower())
        messages.append("Deleted pending verification")
        fixed = True
    
    if not fixed:
        message = "User was already properly verified"
    else:
        message = f"Fixed: {', '.join(messages)}"
    
    return FixResponse(
        email=email,
        fixed=fixed,
        message=message
    )


@router.post("/instagram/force-refresh/{email}")
async def force_refresh_instagram_token(email: EmailStr):
    """
    Forcefully refresh Instagram token for a specific user, 
    bypassing the 24h throttling.
    """
    user_repo = UserRepository()
    user = await user_repo.find_by_email(email.lower())
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    ig_client = InstagramGraphAPIClient()
    success = await ig_client.refresh_user_token(str(user.id))
    
    if success:
        return {"status": "success", "message": f"Token refreshed for {email}"}
    else:
        return {"status": "failed", "message": f"Token refresh failed for {email}. Check logs."}
