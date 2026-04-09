from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


DraftKind = Literal["carousel", "reel", "story"]


class CreatePackRequest(BaseModel):
    trend_keyword: str = Field(..., min_length=1)
    niche: str = Field(..., min_length=1)
    location: str = Field("PK")
    # optional enrichments (lets frontend pass AI analysis outputs to improve generation)
    suggested_hashtags: List[str] = Field(default_factory=list)
    suggested_caption: Optional[str] = None
    platform: Optional[str] = Field(None, description="instagram/facebook/etc.")


class DraftItem(BaseModel):
    id: str
    kind: DraftKind
    title: str
    trend_keyword: Optional[str] = None
    niche: Optional[str] = None
    location: Optional[str] = None
    content: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


class CreatePackResponse(BaseModel):
    drafts: List[DraftItem]


class DraftListResponse(BaseModel):
    drafts: List[DraftItem]
    total: int

