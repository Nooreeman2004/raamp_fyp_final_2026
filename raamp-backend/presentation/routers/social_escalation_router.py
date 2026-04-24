from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from infrastructure.database.models.social_escalation_ticket_model import (
    SocialEscalationStatus,
    SocialEscalationTicketModel,
)
from presentation.routers.auth_router import get_current_user_email
from application.constants import PaginationDefaults
from presentation.schemas.social_escalation_schemas import (
    SocialEscalationAckResponse,
    SocialEscalationResolveResponse,
    SocialEscalationTicketResponse,
    SocialEscalationTicketListResponse,
)


router = APIRouter(prefix="/api/social-escalations", tags=["Social Escalations"])


def _to_response(t: SocialEscalationTicketModel) -> SocialEscalationTicketResponse:
    return SocialEscalationTicketResponse(
        id=str(t.id),
        business_id=str(t.business_id),
        social_account_id=str(t.social_account_id),
        owner_user_id=getattr(t, "owner_user_id", None),
        external_ref=str(t.external_ref),
        comment_event_id=str(t.comment_event_id),
        draft_id=getattr(t, "draft_id", None),
        platform=str(t.platform),
        comment_id=str(t.comment_id),
        intent=getattr(t, "intent", None),
        confidence=getattr(t, "confidence", None),
        priority=str(t.priority),
        status=str(t.status),
        created_at=t.created_at.isoformat(),
        updated_at=t.updated_at.isoformat(),
        first_viewed_at=t.first_viewed_at.isoformat() if getattr(t, "first_viewed_at", None) else None,
        acknowledged_at=t.acknowledged_at.isoformat() if getattr(t, "acknowledged_at", None) else None,
        resolved_at=t.resolved_at.isoformat() if getattr(t, "resolved_at", None) else None,
        sla_seconds=int(getattr(t, "sla_seconds", 0) or 0),
        sla_due_at=t.sla_due_at.isoformat() if getattr(t, "sla_due_at", None) else None,
        admin_notification_sent_at=(
            t.admin_notification_sent_at.isoformat() if getattr(t, "admin_notification_sent_at", None) else None
        ),
        context=dict(getattr(t, "context", {}) or {}),
    )


async def _require_owner(ticket: SocialEscalationTicketModel, current_user_email: str) -> None:
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    # For now, ownership is by owner_user_id (business admin). Later we can expand to multi-admin via business roles.
    if str(getattr(ticket, "owner_user_id", "") or "").lower() != str(current_user_email or "").lower():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.get("", response_model=SocialEscalationTicketListResponse)
async def list_tickets(
    status_filter: str = Query("open", description="open|acknowledged|resolved|all"),
    limit: int = Query(PaginationDefaults.DEFAULT_LIMIT_LARGE, ge=1, le=PaginationDefaults.MAX_LIMIT_MEDIUM),
    skip: int = Query(PaginationDefaults.DEFAULT_SKIP, ge=0),
    current_user_email: str = Depends(get_current_user_email),
):
    q: dict = {"owner_user_id": str(current_user_email or "").lower()}
    sf = str(status_filter or "").strip().lower()
    if sf and sf != "all":
        q["status"] = sf

    total = await SocialEscalationTicketModel.find(q).count()
    rows = await SocialEscalationTicketModel.find(q).sort("-created_at").skip(skip).limit(limit).to_list()
    return SocialEscalationTicketListResponse(tickets=[_to_response(r) for r in rows], total=int(total))


@router.get("/{ticket_id}", response_model=SocialEscalationTicketResponse)
async def get_ticket(
    ticket_id: str,
    current_user_email: str = Depends(get_current_user_email),
):
    t = await SocialEscalationTicketModel.get(ticket_id)
    await _require_owner(t, current_user_email)
    if not t.first_viewed_at:
        t.first_viewed_at = datetime.utcnow()
        t.updated_at = datetime.utcnow()
        await t.save()
    return _to_response(t)


@router.post("/{ticket_id}/ack", response_model=SocialEscalationAckResponse)
async def acknowledge_ticket(
    ticket_id: str,
    current_user_email: str = Depends(get_current_user_email),
):
    t = await SocialEscalationTicketModel.get(ticket_id)
    await _require_owner(t, current_user_email)
    if t.status != SocialEscalationStatus.RESOLVED:
        if not t.acknowledged_at:
            t.acknowledged_at = datetime.utcnow()
        t.status = SocialEscalationStatus.ACKNOWLEDGED
        t.updated_at = datetime.utcnow()
        await t.save()
    return SocialEscalationAckResponse(ok=True, status=str(t.status))


@router.post("/{ticket_id}/resolve", response_model=SocialEscalationResolveResponse)
async def resolve_ticket(
    ticket_id: str,
    current_user_email: str = Depends(get_current_user_email),
):
    t = await SocialEscalationTicketModel.get(ticket_id)
    await _require_owner(t, current_user_email)
    if t.status != SocialEscalationStatus.RESOLVED:
        t.status = SocialEscalationStatus.RESOLVED
        t.resolved_at = datetime.utcnow()
        t.updated_at = datetime.utcnow()
        await t.save()
    return SocialEscalationResolveResponse(ok=True, status=str(t.status))

