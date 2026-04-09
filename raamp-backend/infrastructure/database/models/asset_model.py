"""
Asset Model for MongoDB - stores all AI-generated and user-uploaded media assets
"""
from beanie import Document
from pydantic import Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum


class AssetType(str, Enum):
    """Types of assets in the system"""
    GENERATED_IMAGE = "generated_image"
    GENERATED_VIDEO = "generated_video"
    GENERATED_REEL = "generated_reel"
    UPLOADED_IMAGE = "uploaded_image"
    UPLOADED_VIDEO = "uploaded_video"


class GenerationSource(str, Enum):
    """Source of asset generation"""
    AI = "AI"
    USER_UPLOAD = "user_upload"


class AssetModel(Document):
    """Asset document stored in MongoDB"""
    
    # Core Identification
    asset_id: str = Field(..., description="Unique asset identifier (UUID)")
    user_id: str = Field(..., description="Reference to the user who owns this asset")
    
    # Storage Details
    file_path: str = Field(..., description="Local file system path")
    storage_url: str = Field(..., description="Public URL for accessing the asset")
    cloudinary_url: Optional[str] = Field(None, description="Cloudinary CDN URL if uploaded")
    firebase_url: Optional[str] = Field(None, description="Firebase Storage URL if uploaded")
    
    # File Metadata
    file_name: str = Field(..., description="Original or generated filename")
    file_size_bytes: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME type (e.g., image/png)")
    width: Optional[int] = Field(None, description="Image width in pixels")
    height: Optional[int] = Field(None, description="Image height in pixels")
    
    # Asset Classification
    asset_type: AssetType = Field(..., description="Type of asset")
    generation_source: GenerationSource = Field(..., description="How the asset was created")
    
    # AI Generation Metadata (for generated images)
    generation_prompt: Optional[str] = Field(None, description="Prompt used to generate the image")
    campaign_idea: Optional[str] = Field(None, description="Original campaign idea from user")
    variation_number: Optional[int] = Field(None, description="Variation number (1, 2, or 3)")
    model_used: Optional[str] = Field(None, description="AI model used (e.g., gemini-2.0-flash-exp)")
    
    # Usage Tracking
    times_used: int = Field(default=0, description="Number of times asset was used in posts")
    last_used_at: Optional[datetime] = Field(None, description="Last time asset was used")
    instagram_post_id: Optional[str] = Field(None, description="Internal ID of the last Instagram post using this asset")
    
    # Tags and Organization
    tags: list[str] = Field(default_factory=list, description="User-defined tags for organization")
    is_favorite: bool = Field(default=False, description="Whether user marked as favorite")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(protected_namespaces=())
    
    class Settings:
        name = "assets"
        indexes = [
            "asset_id",
            "user_id",
            "asset_type",
            "generation_source",
            "created_at",
            [("user_id", 1), ("created_at", -1)],  # Compound index for user timeline
            [("user_id", 1), ("asset_type", 1)],  # Filter by user and type
        ]
