from pydantic import BaseModel, Field, constr
from typing import Optional, List, Literal


class ComplaintSubmitRequest(BaseModel):
    subject: constr(strip_whitespace=True, min_length=1, max_length=100) = Field(..., description="Short subject of the complaint")
    description: constr(strip_whitespace=True, min_length=1) = Field(..., description="Detailed description of the complaint")
    priority: Literal["low", "medium", "high", "critical"] = Field(default="medium", description="Priority level")


class ComplaintUpdateRequest(BaseModel):
    subject: constr(strip_whitespace=True, min_length=1, max_length=100) = Field(..., description="Updated subject")
    description: constr(strip_whitespace=True, min_length=1) = Field(..., description="Updated description")
    priority: Literal["low", "medium", "high", "critical"] = Field(default="medium", description="Priority level")


class ComplaintCommentRequest(BaseModel):
    text: constr(strip_whitespace=True, min_length=1, max_length=1000) = Field(..., description="Comment text")


class ComplaintRatingRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")


class ComplaintSubmitResponse(BaseModel):
    id: str


class StatusUpdateSchema(BaseModel):
    status: str
    timestamp: str
    comment: Optional[str]
    adminId: Optional[str]


class CommentSchema(BaseModel):
    text: str
    author: str
    timestamp: str
    isAdmin: bool


class ComplaintResponseItem(BaseModel):
    id: str
    userId: str
    subject: str
    description: str
    status: str
    priority: Optional[str] = "medium"
    adminResponse: str
    adminId: str
    resolvedAt: Optional[str]
    createdAt: str
    updatedAt: str
    statusUpdates: List[StatusUpdateSchema]
    comments: Optional[List[CommentSchema]] = []
    rating: Optional[int] = None
    attachments: Optional[List[str]] = []
