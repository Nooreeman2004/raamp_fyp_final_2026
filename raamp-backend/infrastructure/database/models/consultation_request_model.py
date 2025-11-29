"""
Consultation Request Model for MongoDB
"""
from beanie import Document
from pydantic import Field, EmailStr
from datetime import datetime
from typing import Optional


class ConsultationRequestModel(Document):
    """Consultation booking request stored in MongoDB"""
    
    # Required fields
    first_name: str = Field(..., min_length=1, description="User's first name")
    last_name: str = Field(..., min_length=1, description="User's last name")
    business_email: EmailStr = Field(..., description="User's business email (unique)")
    company_name: str = Field(..., min_length=1, description="User's company name")
    
    # Metadata
    submitted_at: datetime = Field(default_factory=datetime.utcnow, description="Submission timestamp")
    status: str = Field(default="New", description="Request status")
    
    class Settings:
        name = "consultation_requests"
        indexes = [
            "business_email",  # Unique index for preventing duplicate submissions
            "submitted_at",
        ]
