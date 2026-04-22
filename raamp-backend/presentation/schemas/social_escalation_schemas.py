from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel


class SocialEscalationTicketResponse(BaseModel):
    id: str
    business_id: str
    social_account_id: str
    owner_user_id: Optional[str] = None

    external_ref: str
    comment_event_id: str
    draft_id: Optional[str] = None
    platform: str
    comment_id: str

    intent: Optional[str] = None
    confidence: Optional[float] = None
    priority: str
    status: str

    created_at: str
    updated_at: str
    first_viewed_at: Optional[str] = None
    acknowledged_at: Optional[str] = None
    resolved_at: Optional[str] = None

    sla_seconds: int
    sla_due_at: Optional[str] = None
    admin_notification_sent_at: Optional[str] = None

    context: Dict[str, Any] = {}


class SocialEscalationTicketListResponse(BaseModel):
    tickets: list[SocialEscalationTicketResponse]
    total: int


class SocialEscalationAckResponse(BaseModel):
    ok: bool
    status: str


class SocialEscalationResolveResponse(BaseModel):
    ok: bool
    status: str

