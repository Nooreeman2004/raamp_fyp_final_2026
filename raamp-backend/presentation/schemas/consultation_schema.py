"""
Pydantic schemas for Consultation Request
"""
from pydantic import BaseModel, EmailStr, Field, validator
import re


class ConsultationRequestSchema(BaseModel):
    """Request schema for consultation booking - ALL FIELDS REQUIRED"""
    
    first_name: str = Field(..., min_length=1, max_length=100, description="First name (required)")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name (required)")
    business_email: EmailStr = Field(..., description="Business email (required)")
    company_name: str = Field(..., min_length=1, max_length=200, description="Company name (required)")
    
    @validator('first_name', 'last_name', 'company_name')
    @classmethod
    def sanitize_string(cls, v):
        """Sanitize input to prevent XSS and injection attacks"""
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        
        # Remove any potential HTML/script tags and their content
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '', v, flags=re.DOTALL | re.IGNORECASE)
        sanitized = re.sub(r'<[^>]*>', '', sanitized)
        # Remove common XSS patterns
        sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'on\w+\s*=', '', sanitized, flags=re.IGNORECASE)
        # Remove special characters that could be used for injection
        sanitized = re.sub(r'[{}$]', '', sanitized)
        # Remove parentheses that might be used for function calls
        sanitized = re.sub(r'[()]', '', sanitized)
        
        return sanitized.strip()
    
    @validator('business_email')
    @classmethod
    def validate_email(cls, v):
        """Additional email validation"""
        if not v or not v.strip():
            raise ValueError('Email cannot be empty')
        return v.lower().strip()


class ConsultationResponseSchema(BaseModel):
    """Response schema for successful consultation request"""
    
    success: bool = True
    message: str = "Request submitted successfully."
