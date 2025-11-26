# Presentation Layer - Pydantic Schemas (v2)
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional, Dict


class SignupRequest(BaseModel):
    """Request schema for user signup"""
    username: str = Field(..., min_length=7, max_length=20, description="Username for the account")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password with required complexity")
    agreed_to_terms: bool = Field(..., description="Must agree to Terms & Conditions and Privacy Policy")
    
    @field_validator('username')
    @classmethod
    def username_lowercase_alphanumeric(cls, v: str) -> str:
        """Ensure username is lowercase letters and numbers only (7-20 chars)"""
        if not v.islower() or not v.isalnum():
            raise ValueError('Username must contain only lowercase letters and numbers')
        return v
    
    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v: str) -> str:
        """Normalize email to lowercase"""
        return v.lower()


class SignupResponse(BaseModel):
    """Response schema for successful signup (before verification)"""
    id: str = ""  # Empty until user is created after verification
    username: str
    email: str
    created_at: Optional[datetime] = None  # None until user is created
    message: str = "Verification code sent! Please check your email to complete registration."
    
    model_config = {
        "from_attributes": True
    }


class ErrorDetail(BaseModel):
    """Schema for individual field errors"""
    field: str
    message: str | list[str]


class ErrorResponse(BaseModel):
    """Response schema for errors"""
    success: bool = False
    errors: dict[str, str | list[str]]
    message: str = "Validation failed"


class GoogleSignupRequest(BaseModel):
    """Request schema for Google OAuth signup"""
    id_token: str = Field(..., description="Firebase ID token from client")
    email: EmailStr = Field(..., description="Email from Google account")
    display_name: str = Field(..., description="Display name from Google")
    photo_url: Optional[str] = Field(None, description="Profile photo URL")


class GoogleAuthPlaceholder(BaseModel):
    """Placeholder for Google OAuth - not yet implemented"""
    provider: str = "google"
    message: str = "Google OAuth integration coming soon"


class SignInRequest(BaseModel):
    """Request schema for user sign-in"""
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=1, description="User password")
    
    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v: str) -> str:
        """Normalize email to lowercase"""
        return v.lower()


class UserResponse(BaseModel):
    """Response schema for authenticated user"""
    id: str
    username: str
    email: str
    is_verified: bool
    profile_completed: bool
    first_name: str = ""
    last_name: str = ""
    phone_number: str = ""
    company: str = ""
    role: str = ""
    bio: str = ""
    business_domain: Optional[str] = None  # ObjectId reference
    profile_picture: Optional[str] = None
    is_admin: bool = False
    subscription: Optional[Dict] = None
    last_login: Optional[datetime] = None
    created_at: datetime
    
    model_config = {
        "from_attributes": True
    }


class SignInResponse(BaseModel):
    """Response schema for successful sign-in"""
    user: UserResponse
    message: str = "Sign in successful"


class VerifyEmailRequest(BaseModel):
    """Request schema for email verification with OTP"""
    email: EmailStr = Field(..., description="User's email address")
    code: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")
    
    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v: str) -> str:
        """Normalize email to lowercase"""
        return v.lower()
    
    @field_validator('code')
    @classmethod
    def code_numeric(cls, v: str) -> str:
        """Ensure code is numeric"""
        if not v.isdigit():
            raise ValueError('Verification code must contain only digits')
        return v


class VerifyEmailResponse(BaseModel):
    """Response schema for successful email verification"""
    success: bool = True
    message: str = "Email verified successfully"


class ResendVerificationRequest(BaseModel):
    """Request schema for resending verification code"""
    email: EmailStr = Field(..., description="User's email address")
    
    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v: str) -> str:
        """Normalize email to lowercase"""
        return v.lower()


class ResendVerificationResponse(BaseModel):
    """Response schema for resend verification"""
    success: bool = True
    message: str = "Verification code sent successfully"


class UpdateProfileRequest(BaseModel):
    """Request schema for updating user profile - all fields required for profile creation"""
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    phone_number: str = Field(..., min_length=1, max_length=20)
    company: str = Field(..., min_length=1, max_length=100)
    role: str = Field(..., min_length=1, max_length=100)
    bio: str = Field(..., min_length=1, max_length=500)
    business_domain: str = Field(..., description="ObjectId of the business domain category")


class UpdateProfileResponse(BaseModel):
    """Response schema for profile update"""
    user: UserResponse
    message: str = "Profile updated successfully"


class ChangePasswordRequest(BaseModel):
    """Request schema for changing password - now requires OTP verification"""
    otp_code: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code for verification")
    new_password: str = Field(..., min_length=8, description="New password with required complexity")
    confirm_password: str = Field(..., min_length=8)

    @field_validator('new_password')
    @classmethod
    def new_password_complex(cls, v: str) -> str:
        # Basic complexity rules can be enforced here or in service layer
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters long')
        return v


class ChangePasswordSendOtpRequest(BaseModel):
    """Request schema for sending OTP for password change"""
    email: EmailStr


class ChangePasswordSendOtpResponse(BaseModel):
    success: bool = True
    message: str = "OTP sent to your email for password change verification"


class ChangePasswordResponse(BaseModel):
    success: bool = True
    message: str = "Password changed successfully"


class ProfileEditSendRequest(BaseModel):
    email: EmailStr


class ProfileEditSendResponse(BaseModel):
    success: bool = True
    message: str = "Verification code sent for profile edit"


class ProfileEditVerifyRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)


class ProfileEditVerifyResponse(BaseModel):
    success: bool = True
    message: str = "Profile edit verified"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    method: str = Field(default="otp", description="Reset method: 'otp' or 'link'")


class ForgotPasswordResponse(BaseModel):
    success: bool = True
    message: str = "Password reset instructions sent to your email"


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp_code: Optional[str] = Field(None, min_length=6, max_length=6, description="OTP code if method is 'otp'")
    reset_token: Optional[str] = Field(None, description="Reset token if method is 'link'")
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)


class ResetPasswordResponse(BaseModel):
    success: bool = True
    message: str = "Password reset successfully"

