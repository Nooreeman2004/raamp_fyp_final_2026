"""
Complaint Model for MongoDB (Beanie Document)
"""
from beanie import Document
from pydantic import Field, BaseModel
from typing import Optional, List, Literal
from datetime import datetime


class StatusUpdate(BaseModel):
    status: str
    timestamp: datetime
    comment: str = ""
    adminId: str = ""


class Comment(BaseModel):
    text: str
    author: str
    timestamp: datetime
    isAdmin: bool = False


class ComplaintModel(Document):
    """Persistent complaint document stored in `complaints` collection."""

    userId: str = Field(..., description="Reference to the user's id")
    subject: str = Field(..., max_length=100)
    description: str = Field(...)
    priority: Literal["low", "medium", "high", "critical"] = Field(default="medium")

    status: str = Field(default="pending", description="pending|in-progress|resolved|rejected")
    adminResponse: str = Field(default="")
    adminId: str = Field(default="")
    resolvedAt: Optional[datetime] = None

    createdAt: datetime = Field(default_factory=lambda: datetime.utcnow())
    updatedAt: datetime = Field(default_factory=lambda: datetime.utcnow())

    statusUpdates: List[StatusUpdate] = Field(default_factory=lambda: [
        StatusUpdate(
            status="pending",
            timestamp=datetime.utcnow(),
            comment="Complaint submitted by user",
            adminId=""
        )
    ])

    comments: List[Comment] = Field(default_factory=list)
    rating: Optional[int] = None
    attachments: List[str] = Field(default_factory=list)  # URLs to uploaded files

    class Settings:
        name = "complaints"
        indexes = [
            "userId",
            "createdAt",
        ]
