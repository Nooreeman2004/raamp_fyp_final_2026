# Presentation Layer - Auth Router
from fastapi import APIRouter, Depends, status, HTTPException, Response, Request
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta

from presentation.schemas.auth_schemas import (
    SignupRequest,
    SignupResponse,
    ErrorResponse,
    GoogleSignupRequest,
    GoogleAuthPlaceholder,
    SignInRequest,
    SignInResponse,
    UserResponse,
    VerifyEmailRequest,
    VerifyEmailResponse,
    ResendVerificationRequest,
    ResendVerificationResponse,
    UpdateProfileRequest,
    UpdateProfileResponse,
    ChangePasswordRequest,
    ChangePasswordResponse,
    ChangePasswordSendOtpRequest,
    ChangePasswordSendOtpResponse,
    ProfileEditSendRequest,
    ProfileEditSendResponse,
    ProfileEditVerifyRequest,
    ProfileEditVerifyResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)
from application.use_cases.signup_use_case import SignupUseCase
from application.use_cases.signin_use_case import SignInUseCase
from application.use_cases.verify_email_use_case import VerifyEmailUseCase
from application.use_cases.resend_verification_use_case import ResendVerificationUseCase
from application.services.password_service import PasswordHasher, PasswordVerifier
from application.services.jwt_service import JWTService
from application.services.mailtrap_service import MailtrapService
from application.utils.otp_utils import OTPGenerator
from config import OTP_EXPIRY_HOURS, OTP_RESEND_COOLDOWN_SECONDS, OTP_MAX_RESENDS_PER_HOUR, OTP_MAX_RESENDS_PER_DAY
from application.services.firebase_service import firebase_service
from infrastructure.repositories.user_repository_impl import UserRepository
from infrastructure.repositories.pending_verification_repository import PendingVerificationRepository
from infrastructure.repositories.profile_edit_verification_repository import ProfileEditVerificationRepository
from infrastructure.repositories.password_reset_repository import PasswordResetRepository
from domain.entities.user import User
import secrets
from fastapi import Body
from datetime import timedelta


router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_signup_use_case() -> SignupUseCase:
    """Dependency injection for SignupUseCase"""
    pending_repo = PendingVerificationRepository()
    user_repository = UserRepository()
    password_hasher = PasswordHasher()
    mailtrap_service = MailtrapService()
    return SignupUseCase(pending_repo, user_repository, password_hasher, mailtrap_service)


def get_signin_use_case() -> SignInUseCase:
    """Dependency injection for SignInUseCase"""
    user_repository = UserRepository()
    password_verifier = PasswordVerifier()
    jwt_service = JWTService()
    return SignInUseCase(user_repository, password_verifier, jwt_service)


def get_verify_email_use_case() -> VerifyEmailUseCase:
    """Dependency injection for VerifyEmailUseCase"""
    pending_repo = PendingVerificationRepository()
    user_repository = UserRepository()
    mailtrap_service = MailtrapService()
    return VerifyEmailUseCase(pending_repo, user_repository, mailtrap_service)


def get_resend_verification_use_case() -> ResendVerificationUseCase:
    """Dependency injection for ResendVerificationUseCase"""
    pending_repo = PendingVerificationRepository()
    mailtrap_service = MailtrapService()
    return ResendVerificationUseCase(pending_repo, mailtrap_service)



@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error or duplicate user"},
        200: {"model": SignupResponse, "description": "Verification email sent"}
    }
)
async def signup(
    request: SignupRequest,
    use_case: SignupUseCase = Depends(get_signup_use_case)
):
    """
    Initiate signup: Generate OTP and send verification email.
    User account is NOT created until email is verified.
    
    Flow:
    1. Validate username, email, password, terms
    2. Generate 6-digit OTP (valid 24 hours)
    3. Store pending verification (NOT creating user yet)
    4. Send verification email via Mailtrap
    5. Return success message
    
    Requirements:
    - Username: 3-50 characters, alphanumeric with underscores
    - Email: Valid email format
    - Password: Min 8 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special character
    - Must agree to Terms & Conditions and Privacy Policy
    """
    success, errors = await use_case.execute(
        username=request.username,
        email=request.email,
        password=request.password,
        agreed_to_terms=request.agreed_to_terms
    )
    
    if errors:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "errors": errors,
                "message": "Signup failed due to validation errors"
            }
        )
    
    return SignupResponse(
        id="",  # No ID yet - user not created
        username=request.username,
        email=request.email,
        created_at=None,  # No creation timestamp yet
        message="Verification code sent! Please check your email to complete registration."
    )


@router.post(
    "/signup/google",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid token or duplicate user"},
        201: {"model": SignupResponse, "description": "User created successfully"}
    }
)
async def signup_with_google(request: GoogleSignupRequest):
    """
    Sign up with Google OAuth.
    Verifies Firebase ID token and creates user account.
    """
    # Verify Firebase ID token
    verified_user = await firebase_service.verify_id_token(request.id_token)
    
    if not verified_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Google token"
        )
    
    # Check if email matches
    if verified_user["email"].lower() != request.email.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email mismatch"
        )
    
    # Create repository
    user_repository = UserRepository()
    password_hasher = PasswordHasher()
    
    # Check if user already exists
    existing_user = await user_repository.find_by_email(request.email)
    if existing_user:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "errors": {"email": "Email is already registered"},
                "message": "User already exists"
            }
        )
    
    # Generate username from display name or email
    base_username = (request.display_name.lower()
                     .replace(" ", "")
                     .replace(".", "")[:15])
    
    # Make username unique if needed
    username = base_username
    counter = 1
    while await user_repository.exists_by_username(username):
        username = f"{base_username}{counter}"
        counter += 1
    
    # Ensure username meets validation (7-20 chars, lowercase + numbers)
    if len(username) < 7:
        username = username + str(secrets.randbelow(1000000)).zfill(6)
    username = username[:20]  # Truncate if too long
    
    # Create user (Google users don't need password, so use a secure random one)
    random_password = secrets.token_urlsafe(32)
    password_hash = password_hasher.hash_password(random_password)
    
    user = User(
        id=None,
        username=username,
        email=request.email.lower(),
        password_hash=password_hash,
        agreed_to_terms=True,  # Implicit via Google OAuth
        is_verified=True,  # Google accounts are pre-verified
        profile_picture=request.photo_url,  # Use Google profile picture if provided
        profile_completed=False,  # ensure newly created Google users must finish onboarding/profile
    )
    
    # Save to database (lastLogin automatically set to utcnow)
    created_user = await user_repository.create(user)
    # Ensure onboarding is not skipped for Google signups: mark profile incomplete
    try:
        await user_repository.update_profile_completed(created_user.email, completed=False)
    except Exception:
        # non-fatal: log and continue
        import logging
        logging.exception("Failed to explicitly set profile_completed for Google signup")
    
    return SignupResponse(
        id=created_user.id,
        username=created_user.username,
        email=created_user.email,
        created_at=created_user.created_at,
        message="Account created successfully with Google"
    )


@router.post(
    "/signin",
    response_model=SignInResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid credentials or unverified email"},
        200: {"model": SignInResponse, "description": "Sign in successful"}
    }
)
async def signin(
    request: SignInRequest,
    response: Response,
    use_case: SignInUseCase = Depends(get_signin_use_case)
):
    """
    Sign in to RAAMP account.
    
    Flow:
    1. Validate email and password format
    2. Fetch user from MongoDB
    3. Verify password with bcrypt
    4. Check if email is verified
    5. Generate JWT token (HS256)
    6. Set HTTP-only cookie with JWT
    7. Return user data
    
    Requirements:
    - Valid email format
    - Correct password
    - Email must be verified
    """
    user, token, errors = await use_case.execute(
        email=request.email,
        password=request.password
    )
    
    if errors:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "errors": errors,
                "message": "Sign in failed"
            }
        )
    
    # Update last login timestamp
    user_repository = UserRepository()
    await user_repository.update_last_login(email=user.email)
    
    # Refresh user data to get updated last_login
    user = await user_repository.find_by_email(user.email)
    
    # Set JWT in HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7 days
    )
    
    # Return user data with all profile fields including auto-generated ones
    user_response = UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        is_verified=user.is_verified,
        profile_completed=user.profile_completed,
        first_name=user.first_name,
        last_name=user.last_name,
        phone_number=user.phone_number,
        company=user.company,
        role=user.role,
        bio=user.bio,
        business_domain=user.business_domain,
        profile_picture=user.profile_picture,
        is_admin=user.is_admin,
        subscription=user.subscription,
        last_login=user.last_login,
        created_at=user.created_at
    )
    
    return SignInResponse(
        user=user_response,
        message="Sign in successful"
    )


@router.post(
    "/signin/google",
    response_model=SignInResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid token"},
        401: {"model": ErrorResponse, "description": "User not found or unverified"},
        200: {"model": SignInResponse, "description": "Sign in successful"}
    }
)
async def signin_with_google(request: GoogleSignupRequest, response: Response):
    """
    Sign in with Google OAuth.
    Verifies Firebase ID token and authenticates existing user.
    Updates lastLogin timestamp on successful authentication.
    
    Flow:
    1. Verify Firebase ID token
    2. Check if user exists and is verified
    3. Update lastLogin timestamp
    4. Generate JWT token
    5. Set HTTP-only cookie
    6. Return user data
    """
    # Verify Firebase ID token
    verified_user = await firebase_service.verify_id_token(request.id_token)
    
    if not verified_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Google token"
        )
    
    # Check if email matches
    if verified_user["email"].lower() != request.email.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email mismatch"
        )
    
    # Create repository
    user_repository = UserRepository()
    
    # Find user by email
    user = await user_repository.find_by_email(request.email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found. Please sign up first."
        )
    
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified"
        )
    
    # Update last login timestamp
    await user_repository.update_last_login(email=user.email)
    
    # Refresh user data to get updated last_login
    user = await user_repository.find_by_email(user.email)
    
    # Generate JWT token
    jwt_service = JWTService()
    token = jwt_service.create_access_token(user_id=str(user.id), email=user.email)
    
    # Set JWT in HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7 days
    )
    
    # Return user data with all profile fields
    user_response = UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        is_verified=user.is_verified,
        profile_completed=user.profile_completed,
        first_name=user.first_name,
        last_name=user.last_name,
        phone_number=user.phone_number,
        company=user.company,
        role=user.role,
        bio=user.bio,
        business_domain=user.business_domain,
        profile_picture=user.profile_picture,
        is_admin=user.is_admin,
        subscription=user.subscription,
        last_login=user.last_login,
        created_at=user.created_at
    )
    
    return SignInResponse(
        user=user_response,
        message="Signed in successfully with Google"
    )


@router.post(
    "/verify-email",
    response_model=VerifyEmailResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid or expired code"},
        201: {"model": VerifyEmailResponse, "description": "User account created successfully"}
    }
)
async def verify_email(
    request: VerifyEmailRequest,
    use_case: VerifyEmailUseCase = Depends(get_verify_email_use_case)
):
    """
    Verify email with 6-digit OTP and CREATE user account.
    
    NEW FLOW (User created here, not at signup):
    1. Validate email and 6-digit code format
    2. Find pending verification in database
    3. Verify OTP code matches and hasn't expired (24-hour validity)
    4. CREATE user account in database (with is_verified=True)
    5. Delete pending verification entry
    6. Send welcome email via Mailtrap
    7. Return success message
    
    Requirements:
    - Valid email format
    - Exactly 6-digit numeric code
    - Code must not be expired (< 24 hours old)
    - Pending verification must exist
    """
    success, errors = await use_case.execute(
        email=request.email,
        code=request.code
    )
    
    if errors:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "errors": errors,
                "message": "Email verification failed"
            }
        )
    
    return VerifyEmailResponse(
        message="Email verified successfully! You can now sign in to your account."
    )


@router.post(
    "/resend-verification",
    response_model=ResendVerificationResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Cooldown active or no pending verification"},
        200: {"model": ResendVerificationResponse, "description": "Verification code resent"}
    }
)
async def resend_verification(
    request: ResendVerificationRequest,
    use_case: ResendVerificationUseCase = Depends(get_resend_verification_use_case)
):
    """
    Resend verification code email.
    
    NEW FLOW (Works with pending verifications):
    1. Validate email format
    2. Find pending verification in database
    3. Enforce 60-second cooldown (can_resend_otp check)
    4. Generate new 6-digit OTP with 24-hour expiry
    5. Update pending verification with new code and sent_at timestamp
    6. Send verification email via Mailtrap
    7. Return success message
    
    Requirements:
    - Valid email format
    - User must not be already verified
    - Must wait 60 seconds between resend requests
    """
    success, errors, remaining = await use_case.execute(email=request.email)
    
    if errors:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "errors": errors,
                "message": "Failed to resend verification code"
            }
        )
    
    return ResendVerificationResponse(
        message="Verification code sent! Check your email."
    )


async def get_current_user_email(request: Request) -> str:
    """
    JWT Authentication Dependency
    Extracts and validates JWT token from cookies.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        User's email from token payload
        
    Raises:
        HTTPException: 401 if token is missing or invalid
    """
    token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please log in."
        )
    
    jwt_service = JWTService()
    payload = jwt_service.verify_token(token)
    
    if not payload or "email" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please log in again."
        )
    
    return payload["email"]


@router.get(
    "/profile",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    responses={401: {"model": ErrorResponse, "description": "Not authenticated"}, 404: {"model": ErrorResponse, "description": "User not found"}}
)
async def get_profile(current_user_email: str = Depends(get_current_user_email)):
    """Return authenticated user's profile"""
    user_repository = UserRepository()
    user = await user_repository.find_by_email(current_user_email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user_response = UserResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        is_verified=user.is_verified,
        profile_completed=user.profile_completed,
        first_name=user.first_name,
        last_name=user.last_name,
        phone_number=user.phone_number,
        company=user.company,
        role=user.role,
        bio=user.bio,
        business_domain=user.business_domain,
        profile_picture=user.profile_picture,
        is_admin=user.is_admin,
        subscription=user.subscription,
        last_login=user.last_login,
        created_at=user.created_at
    )

    return user_response


@router.get(
    "/verification-status",
    status_code=status.HTTP_200_OK,
    responses={200: {"description": "Returns whether the email is verified"}}
)
async def verification_status(email: str):
    """
    Check whether a given email is already verified.

    Query Params:
    - email: email address to check

    Returns JSON: {"is_verified": bool, "message": str}
    """
    if not email:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success": False, "errors": {"email": "Email is required"}, "message": "Email query parameter is required"})

    user_repository = UserRepository()
    user = await user_repository.find_by_email(email.lower())

    if not user:
        # For privacy we do not expose additional user info — return not verified
        return JSONResponse(status_code=status.HTTP_200_OK, content={"is_verified": False, "message": "User not found"})

    return JSONResponse(status_code=status.HTTP_200_OK, content={"is_verified": bool(user.is_verified), "message": "OK"})


@router.post(
    "/profile/send-edit-otp",
    response_model=ProfileEditSendResponse,
    status_code=status.HTTP_200_OK,
    responses={400: {"model": ErrorResponse, "description": "Failed to send code"}}
)
async def send_profile_edit_otp(request: ProfileEditSendRequest):
    """Send OTP code for verifying profile edits"""
    email = request.email.lower()
    repo = ProfileEditVerificationRepository()
    email_service = MailtrapService()

    # Check existing entry
    existing = await repo.find_by_email(email)
    if existing:
        # Check cooldown
        can_resend, remaining = OTPGenerator.can_resend_otp(existing.code_sent_at, OTP_RESEND_COOLDOWN_SECONDS)
        if not can_resend:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success": False, "errors": {"cooldown": f"Please wait {remaining} seconds"}, "message": "Cooldown active"})

        if existing.resend_count >= OTP_MAX_RESENDS_PER_HOUR:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success": False, "errors": {"rate_limit": "Hourly resend limit exceeded"}, "message": "Rate limit"})

    otp_code, expires_at = OTPGenerator.generate_otp_with_expiry(expiry_hours=OTP_EXPIRY_HOURS)
    sent_at = __import__('datetime').datetime.utcnow()

    await repo.create_or_update(email=email, code=otp_code, expires_at=expires_at, sent_at=sent_at)

    # Send verification email (uses Mailtrap)
    await email_service.send_verification_email(to_email=email, name=email.split('@')[0], otp_code=otp_code)

    # Log OTP to console for debugging
    print(f"Profile edit OTP for {email}: {otp_code} (expires {expires_at})")

    return ProfileEditSendResponse(message="Verification code sent for profile edit")


@router.post(
    "/profile/verify-edit-otp",
    response_model=ProfileEditVerifyResponse,
    status_code=status.HTTP_200_OK,
    responses={400: {"model": ErrorResponse, "description": "Invalid or expired code"}}
)
async def verify_profile_edit_otp(request: ProfileEditVerifyRequest):
    email = request.email.lower()
    repo = ProfileEditVerificationRepository()

    entry = await repo.find_by_email(email)
    if not entry:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success": False, "errors": {"email": "No pending verification found"}, "message": "No pending verification"})

    is_valid, err_msg = OTPGenerator.is_otp_valid(request.code, entry.verification_code, entry.code_expires_at)
    if not is_valid:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success": False, "errors": {"code": err_msg}, "message": "Invalid or expired code"})

    # On success, delete the entry so it cannot be reused
    await repo.delete_by_email(email)

    return ProfileEditVerifyResponse(message="Profile edit verified")


@router.put(
    "/profile",
    response_model=UpdateProfileResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "User not found"},
        200: {"model": UpdateProfileResponse, "description": "Profile updated successfully"}
    }
)
async def update_profile(
    request: UpdateProfileRequest,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Create user profile with required personal information.
    This endpoint is used for first-time profile creation after signup.
    Requires authentication via JWT token in cookies.
    
    Flow:
    1. Extract user email from JWT token
    2. Validate all required profile fields
    3. Store profile information in database
    4. Set profile_completed=True
    5. Return updated user data
    
    All fields are required:
    - first_name: 1-50 characters
    - last_name: 1-50 characters
    - phone_number: 1-20 characters
    - company: 1-100 characters
    - role: 1-100 characters
    - bio: 1-500 characters
    
    After successful profile creation, user can proceed to ecosystem connection.
    """
    user_repository = UserRepository()
    
    updated_user = await user_repository.update_profile(
        email=current_user_email,
        first_name=request.first_name,
        last_name=request.last_name,
        phone_number=request.phone_number,
        company=request.company,
        role=request.role,
        bio=request.bio,
        business_domain=request.business_domain
    )
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user_response = UserResponse(
        id=str(updated_user.id),
        username=updated_user.username,
        email=updated_user.email,
        is_verified=updated_user.is_verified,
        profile_completed=updated_user.profile_completed,
        first_name=updated_user.first_name,
        last_name=updated_user.last_name,
        phone_number=updated_user.phone_number,
        company=updated_user.company,
        role=updated_user.role,
        bio=updated_user.bio,
        business_domain=updated_user.business_domain,
        profile_picture=updated_user.profile_picture,
        is_admin=updated_user.is_admin,
        subscription=updated_user.subscription,
        last_login=updated_user.last_login,
        created_at=updated_user.created_at
    )
    
    return UpdateProfileResponse(
        user=user_response,
        message="Profile created successfully. Proceed to ecosystem connection."
    )



@router.post(
    "/change-password/send-otp",
    response_model=ChangePasswordSendOtpResponse,
    status_code=status.HTTP_200_OK,
    responses={400: {"model": ErrorResponse, "description": "Failed to send OTP"}}
)
async def send_change_password_otp(
    request: ChangePasswordSendOtpRequest = Body(...),
    current_user_email: str = Depends(get_current_user_email)
):
    """Send OTP code for password change verification"""
    # Verify the email matches the authenticated user
    if request.email.lower() != current_user_email.lower():
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"success": False, "errors": {"email": "Email does not match authenticated user"}, "message": "Unauthorized"}
        )
    
    email = request.email.lower()
    repo = ProfileEditVerificationRepository()
    email_service = MailtrapService()

    # Check existing entry
    existing = await repo.find_by_email(email)
    if existing:
        # Check cooldown
        can_resend, remaining = OTPGenerator.can_resend_otp(existing.code_sent_at, OTP_RESEND_COOLDOWN_SECONDS)
        if not can_resend:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success": False, "errors": {"cooldown": f"Please wait {remaining} seconds"}, "message": "Cooldown active"})

        if existing.resend_count >= OTP_MAX_RESENDS_PER_HOUR:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success": False, "errors": {"rate_limit": "Hourly resend limit exceeded"}, "message": "Rate limit"})

    otp_code, expires_at = OTPGenerator.generate_otp_with_expiry(expiry_hours=OTP_EXPIRY_HOURS)
    sent_at = __import__('datetime').datetime.utcnow()

    await repo.create_or_update(email=email, code=otp_code, expires_at=expires_at, sent_at=sent_at)

    # Send verification email (uses Mailtrap)
    await email_service.send_verification_email(to_email=email, name=email.split('@')[0], otp_code=otp_code)

    # Log OTP to console for debugging
    print(f"Password change OTP for {email}: {otp_code} (expires {expires_at})")

    return ChangePasswordSendOtpResponse(message="OTP sent to your email for password change verification")


@router.post(
    "/change-password",
    response_model=ChangePasswordResponse,
    status_code=status.HTTP_200_OK,
    responses={401: {"model": ErrorResponse, "description": "Not authenticated"}, 400: {"model": ErrorResponse, "description": "Invalid request or OTP"}}
)
async def change_password(
    request: ChangePasswordRequest = Body(...),
    current_user_email: str = Depends(get_current_user_email)
):
    """Change user's password after verifying OTP"""
    if request.new_password != request.confirm_password:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "errors": {"confirm_password": "Passwords do not match"}, "message": "New passwords do not match"}
        )

    # Verify OTP first
    email = current_user_email.lower()
    repo = ProfileEditVerificationRepository()
    entry = await repo.find_by_email(email)
    
    if not entry:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "errors": {"otp_code": "No pending OTP verification found. Please request an OTP first."}, "message": "OTP verification required"}
        )

    is_valid, err_msg = OTPGenerator.is_otp_valid(request.otp_code, entry.verification_code, entry.code_expires_at)
    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "errors": {"otp_code": err_msg}, "message": "Invalid or expired OTP"}
        )

    # OTP verified, proceed with password change
    user_repository = UserRepository()
    user = await user_repository.find_by_email(current_user_email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    password_hasher = PasswordHasher()
    new_hash = password_hasher.hash_password(request.new_password)
    updated = await user_repository.update_password(email=current_user_email, new_password_hash=new_hash)
    if not updated:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "errors": {"server": "Failed to update password"}, "message": "Could not update password"}
        )

    # Delete OTP entry after successful password change
    await repo.delete_by_email(email)

    return ChangePasswordResponse(success=True, message="Password changed successfully")


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    status_code=status.HTTP_200_OK,
    responses={400: {"model": ErrorResponse, "description": "Invalid request"}, 404: {"model": ErrorResponse, "description": "User not found"}}
)
async def forgot_password(request: ForgotPasswordRequest = Body(...)):
    """Handle forgot password request - send OTP or reset link"""
    email = request.email.lower()
    user_repository = UserRepository()
    user = await user_repository.find_by_email(email)
    
    if not user:
        # Don't reveal if user exists for security
        return ForgotPasswordResponse(message="If an account exists with this email, password reset instructions have been sent")
    
    reset_repo = PasswordResetRepository()
    email_service = MailtrapService()
    
    if request.method == "otp":
        # Generate OTP
        otp_code, expires_at = OTPGenerator.generate_otp_with_expiry(expiry_hours=1)  # 1 hour expiry for password reset
        
        # Create reset entry
        await reset_repo.create(
            email=email,
            otp_code=otp_code,
            expires_at=expires_at
        )
        
        # Send OTP email
        await email_service.send_verification_email(
            to_email=email,
            name=user.username or email.split('@')[0],
            otp_code=otp_code
        )
        
        print(f"Password reset OTP for {email}: {otp_code} (expires {expires_at})")
        
        return ForgotPasswordResponse(message="Password reset OTP sent to your email")
    
    else:  # method == "link"
        # Generate secure reset token
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
        
        # Create reset entry
        await reset_repo.create(
            email=email,
            reset_token=reset_token,
            expires_at=expires_at
        )
        
        # Send reset link email
        await email_service.send_password_reset_email(
            to_email=email,
            name=user.username or email.split('@')[0],
            reset_token=reset_token
        )
        
        return ForgotPasswordResponse(message="Password reset link sent to your email")


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    status_code=status.HTTP_200_OK,
    responses={400: {"model": ErrorResponse, "description": "Invalid request or token/OTP"}, 404: {"model": ErrorResponse, "description": "User not found"}}
)
async def reset_password(request: ResetPasswordRequest = Body(...)):
    """Reset password using OTP or reset token"""
    if request.new_password != request.confirm_password:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "errors": {"confirm_password": "Passwords do not match"}, "message": "Passwords do not match"}
        )
    
    reset_repo = PasswordResetRepository()
    user_repository = UserRepository()
    
    # Find reset entry
    reset_entry = None
    email = None
    
    if request.otp_code:
        if not request.email:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "errors": {"email": "Email is required when using OTP"}, "message": "Email required"}
            )
        email = request.email.lower()
        reset_entry = await reset_repo.find_by_otp(email, request.otp_code)
        if not reset_entry:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "errors": {"otp_code": "Invalid or expired OTP"}, "message": "Invalid or expired OTP"}
            )
    elif request.reset_token:
        reset_entry = await reset_repo.find_by_token(request.reset_token)
        if not reset_entry:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "errors": {"reset_token": "Invalid or expired reset token"}, "message": "Invalid or expired reset token"}
            )
        # Extract email from reset entry
        email = reset_entry.email.lower()
        # If email was provided, verify it matches
        if request.email and request.email.lower() != email:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "errors": {"email": "Email does not match reset token"}, "message": "Email mismatch"}
            )
    else:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "errors": {"general": "Either OTP code or reset token is required"}, "message": "Invalid request"}
        )
    
    # Verify user exists
    user = await user_repository.find_by_email(email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Update password
    password_hasher = PasswordHasher()
    new_hash = password_hasher.hash_password(request.new_password)
    updated = await user_repository.update_password(email=email, new_password_hash=new_hash)
    if not updated:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "errors": {"server": "Failed to update password"}, "message": "Could not update password"}
        )
    
    # Mark reset entry as used
    await reset_repo.mark_as_used(str(reset_entry.id))
    
    # Send success email
    email_service = MailtrapService()
    await email_service.send_reset_success_email(
        to_email=email,
        name=user.username or email.split('@')[0]
    )
    
    return ResetPasswordResponse(message="Password reset successfully")



