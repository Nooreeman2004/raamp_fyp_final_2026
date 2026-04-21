from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AutoReplyDraftItem(BaseModel):
    id: str
    platform: str
    comment_id: str
    suggested_reply: str
    alternatives: List[str] = Field(default_factory=list)
    requires_user_action: bool
    status: str
    expires_at: str
    created_at: str
    updated_at: str

    # For idempotent approve & send
    approval_nonce: str

    # Minimal context for UI (safe + optional)
    comment_text: Optional[str] = None


class AutoReplyDraftListResponse(BaseModel):
    drafts: List[AutoReplyDraftItem]
    total: int


class AutoReplyApproveRequest(BaseModel):
    approval_nonce: str = Field(..., min_length=8)
    message: Optional[str] = Field(None, description="Optional edited message to send instead of suggested reply.")


class AutoReplyApproveResponse(BaseModel):
    success: bool
    status: str
    reply_id: Optional[str] = None
    sent_id: Optional[str] = None
    message: Optional[str] = None


class AutoReplySkipRequest(BaseModel):
    reason: Optional[str] = None


class AutoReplySkipResponse(BaseModel):
    success: bool
    status: str


class AutoReplySettingsResponse(BaseModel):
    instagram_auto_replies_enabled: bool
    instagram_mode: str
    facebook_auto_replies_enabled: bool
    facebook_mode: str
    thread_context_depth: int
    updated_at: str


class AutoReplySettingsPatchRequest(BaseModel):
    instagram_auto_replies_enabled: Optional[bool] = None
    instagram_mode: Optional[str] = None
    facebook_auto_replies_enabled: Optional[bool] = None
    facebook_mode: Optional[str] = None
    thread_context_depth: Optional[int] = Field(default=None, ge=0, le=3)

