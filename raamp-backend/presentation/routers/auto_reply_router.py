from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from application.services.facebook_graph_api_service import FacebookGraphAPIClient, FacebookAPIError
from application.services.instagram_graph_api_service import InstagramGraphAPIClient, InstagramAPIError
from application.services.notification_service import NotificationService
from application.utils.auto_reply_utils import normalize_reply_text, sha256_hex
from infrastructure.database.models.auto_reply_models import (
    AutoReplyDraftModel,
    AutoReplyDraftStatus,
    AutoReplySentModel,
    CommentEventModel,
    CommentEventStatus,
)
from infrastructure.database.models.facebook_connection_model import FacebookConnectionModel
from infrastructure.database.models.notification_model import NotificationType
from presentation.routers.auth_router import get_current_user_email
from infrastructure.database.models.auto_reply_settings_model import AutoReplyMode, AutoReplySettingsModel
from infrastructure.database.models.social_escalation_ticket_model import SocialEscalationTicketModel
from presentation.schemas.auto_reply_schemas import (
    AutoReplyApproveRequest,
    AutoReplyApproveResponse,
    AutoReplyDraftItem,
    AutoReplyDraftListResponse,
    AutoReplySettingsPatchRequest,
    AutoReplySettingsResponse,
    AutoReplySkipRequest,
    AutoReplySkipResponse,
)


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auto-replies", tags=["Auto Replies"])


MAX_REPLIES_PER_COMMENT = 2


@router.get("/dashboard-stats")
async def auto_reply_dashboard_stats(
    current_user_email: str = Depends(get_current_user_email),
):
    """
    Lightweight dashboard stats for comments + escalations.
    """
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=24)

    email = str(current_user_email or "").strip().lower()

    # Comments in last 24h
    total_comments = await CommentEventModel.find(
        CommentEventModel.user_id == email,
        CommentEventModel.created_at >= cutoff,
    ).count()
    fb_comments = await CommentEventModel.find(
        CommentEventModel.user_id == email,
        CommentEventModel.created_at >= cutoff,
        CommentEventModel.platform == "facebook",
    ).count()
    ig_comments = await CommentEventModel.find(
        CommentEventModel.user_id == email,
        CommentEventModel.created_at >= cutoff,
        CommentEventModel.platform == "instagram",
    ).count()

    # Comments all-time
    total_comments_all = await CommentEventModel.find(
        CommentEventModel.user_id == email,
    ).count()
    fb_comments_all = await CommentEventModel.find(
        CommentEventModel.user_id == email,
        CommentEventModel.platform == "facebook",
    ).count()
    ig_comments_all = await CommentEventModel.find(
        CommentEventModel.user_id == email,
        CommentEventModel.platform == "instagram",
    ).count()

    # Escalations (open) + soonest SLA
    open_count = await SocialEscalationTicketModel.find(
        {"owner_user_id": email, "status": "open"}
    ).count()
    soonest_due_at = None
    try:
        soonest = await SocialEscalationTicketModel.find(
            {"owner_user_id": email, "status": "open"}
        ).sort("sla_due_at").limit(1).to_list()
        if soonest:
            soonest_due_at = getattr(soonest[0], "sla_due_at", None)
    except Exception:
        soonest_due_at = None

    return {
        "window_hours": 24,
        "comments": {
            "total": int(total_comments or 0),
            "facebook": int(fb_comments or 0),
            "instagram": int(ig_comments or 0),
        },
        "comments_all_time": {
            "total": int(total_comments_all or 0),
            "facebook": int(fb_comments_all or 0),
            "instagram": int(ig_comments_all or 0),
        },
        "escalations": {
            "open": int(open_count or 0),
            "soonest_sla_due_at": soonest_due_at.isoformat() if soonest_due_at else None,
        },
        "generated_at": now.isoformat(),
    }


async def _get_or_create_settings(user_id: str) -> AutoReplySettingsModel:
    s = await AutoReplySettingsModel.find_one(AutoReplySettingsModel.user_id == user_id)
    if s:
        return s
    s = AutoReplySettingsModel(user_id=user_id)
    await s.insert()
    return s


@router.get("/settings", response_model=AutoReplySettingsResponse)
async def get_auto_reply_settings(
    current_user_email: str = Depends(get_current_user_email),
):
    s = await _get_or_create_settings(current_user_email)
    return AutoReplySettingsResponse(
        instagram_auto_replies_enabled=bool(getattr(s, "instagram_auto_replies_enabled", False)),
        instagram_mode=str(getattr(s, "instagram_mode", AutoReplyMode.REVIEW_ONLY)),
        facebook_auto_replies_enabled=bool(getattr(s, "facebook_auto_replies_enabled", False)),
        facebook_mode=str(getattr(s, "facebook_mode", AutoReplyMode.REVIEW_ONLY)),
        thread_context_depth=int(getattr(s, "thread_context_depth", 0) or 0),
        updated_at=getattr(s, "updated_at", datetime.utcnow()).isoformat(),
    )


@router.patch("/settings", response_model=AutoReplySettingsResponse)
async def patch_auto_reply_settings(
    body: AutoReplySettingsPatchRequest,
    current_user_email: str = Depends(get_current_user_email),
):
    s = await _get_or_create_settings(current_user_email)

    if body.instagram_auto_replies_enabled is not None:
        s.instagram_auto_replies_enabled = bool(body.instagram_auto_replies_enabled)
    if body.facebook_auto_replies_enabled is not None:
        s.facebook_auto_replies_enabled = bool(body.facebook_auto_replies_enabled)

    if body.instagram_mode is not None:
        mode = str(body.instagram_mode)
        if mode not in (AutoReplyMode.REVIEW_ONLY, AutoReplyMode.HYBRID_AUTO):
            raise HTTPException(status_code=400, detail="Invalid instagram_mode")
        s.instagram_mode = mode
    if body.facebook_mode is not None:
        mode = str(body.facebook_mode)
        if mode not in (AutoReplyMode.REVIEW_ONLY, AutoReplyMode.HYBRID_AUTO):
            raise HTTPException(status_code=400, detail="Invalid facebook_mode")
        s.facebook_mode = mode

    if body.thread_context_depth is not None:
        s.thread_context_depth = int(body.thread_context_depth)

    s.updated_at = datetime.utcnow()
    await s.save()

    return AutoReplySettingsResponse(
        instagram_auto_replies_enabled=bool(s.instagram_auto_replies_enabled),
        instagram_mode=str(s.instagram_mode),
        facebook_auto_replies_enabled=bool(s.facebook_auto_replies_enabled),
        facebook_mode=str(s.facebook_mode),
        thread_context_depth=int(s.thread_context_depth),
        updated_at=s.updated_at.isoformat(),
    )


@router.get("/drafts", response_model=AutoReplyDraftListResponse)
async def list_auto_reply_drafts(
    status_filter: Optional[str] = Query("active", description="active/expired/sent/skipped"),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user_email: str = Depends(get_current_user_email),
):
    q = {"user_id": current_user_email}
    if status_filter:
        q["status"] = str(status_filter)

    total = await AutoReplyDraftModel.find(q).count()
    rows = await AutoReplyDraftModel.find(q).sort("-created_at").skip(skip).limit(limit).to_list()

    # Avoid N+1 queries: fetch all escalation tickets for this page of drafts in one query.
    external_refs: list[str] = []
    for d in rows:
        try:
            external_refs.append(f"meta_comment:{d.platform}:{d.comment_id}")
        except Exception:
            continue
    ticket_by_ref: dict[str, str] = {}
    if external_refs:
        try:
            tickets = await SocialEscalationTicketModel.find(
                {"external_ref": {"$in": list({r for r in external_refs if r})}}
            ).to_list()
            for t in tickets:
                ref = str(getattr(t, "external_ref", "") or "")
                if ref:
                    ticket_by_ref[ref] = str(t.id)
        except Exception:
            ticket_by_ref = {}

    items: list[AutoReplyDraftItem] = []
    for d in rows:
        comment_text = None
        escalation_ticket_id = ticket_by_ref.get(f"meta_comment:{d.platform}:{d.comment_id}")
        try:
            ev = await CommentEventModel.get(d.comment_event_id)
            if ev and ev.user_id == current_user_email:
                comment_text = getattr(ev, "text", None)
        except Exception:
            comment_text = None

        items.append(
            AutoReplyDraftItem(
                id=str(d.id),
                platform=d.platform,
                comment_id=d.comment_id,
                suggested_reply=d.suggested_reply,
                alternatives=list(d.alternatives or []),
                requires_user_action=bool(d.requires_user_action),
                status=d.status,
                expires_at=d.expires_at.isoformat(),
                created_at=d.created_at.isoformat(),
                updated_at=d.updated_at.isoformat(),
                approval_nonce=d.approval_nonce,
                comment_text=comment_text,
                escalation_ticket_id=escalation_ticket_id,
            )
        )

    return AutoReplyDraftListResponse(drafts=items, total=int(total))


@router.post("/drafts/{draft_id}/skip", response_model=AutoReplySkipResponse)
async def skip_auto_reply_draft(
    draft_id: str,
    body: AutoReplySkipRequest,
    current_user_email: str = Depends(get_current_user_email),
):
    draft = await AutoReplyDraftModel.get(draft_id)
    if not draft or draft.user_id != current_user_email:
        raise HTTPException(status_code=404, detail="Draft not found")

    if draft.status in (AutoReplyDraftStatus.SENT, AutoReplyDraftStatus.EXPIRED):
        return AutoReplySkipResponse(success=False, status=draft.status)

    draft.status = AutoReplyDraftStatus.SKIPPED
    draft.resolved_at = datetime.utcnow()
    draft.updated_at = datetime.utcnow()
    await draft.save()

    try:
        svc = NotificationService()
        await svc.create_and_send(
            user_id=current_user_email,
            type=NotificationType.SOCIAL_POST,
            title="Reply draft skipped",
            message="You skipped a reply draft.",
            related_entity_id=str(draft.id),
            metadata={
                "sub_type": "auto_reply_draft_skipped",
                "platform": draft.platform,
                "comment_id": draft.comment_id,
                "reason": (body.reason or "")[:200],
                "draft_id": str(draft.id),
            },
            priority=1,
        )
    except Exception:
        pass

    return AutoReplySkipResponse(success=True, status=draft.status)


@router.post("/drafts/{draft_id}/approve", response_model=AutoReplyApproveResponse)
async def approve_and_send_auto_reply(
    draft_id: str,
    body: AutoReplyApproveRequest,
    current_user_email: str = Depends(get_current_user_email),
):
    draft = await AutoReplyDraftModel.get(draft_id)
    if not draft or draft.user_id != current_user_email:
        raise HTTPException(status_code=404, detail="Draft not found")

    # Expiry enforcement
    if draft.expires_at < datetime.utcnow():
        if draft.status == AutoReplyDraftStatus.ACTIVE:
            draft.status = AutoReplyDraftStatus.EXPIRED
            draft.resolved_at = datetime.utcnow()
            draft.updated_at = datetime.utcnow()
            await draft.save()
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Draft expired")

    # Approval idempotency token must match
    if str(body.approval_nonce) != str(draft.approval_nonce):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invalid approval token")

    # Idempotent response if already sent
    if draft.status == AutoReplyDraftStatus.SENT:
        sent = await AutoReplySentModel.find_one(AutoReplySentModel.draft_id == str(draft.id))
        return AutoReplyApproveResponse(
            success=True,
            status="sent",
            reply_id=getattr(sent, "reply_id", None) if sent else None,
            sent_id=str(sent.id) if sent else None,
            message="Already sent",
        )

    if draft.status in (AutoReplyDraftStatus.EXPIRED, AutoReplyDraftStatus.SKIPPED):
        raise HTTPException(status_code=400, detail=f"Draft not sendable (status={draft.status})")

    # Guardrail: cap number of replies per comment
    already = await AutoReplySentModel.find(
        AutoReplySentModel.platform == draft.platform,
        AutoReplySentModel.comment_id == draft.comment_id,
    ).count()
    if int(already) >= MAX_REPLIES_PER_COMMENT:
        raise HTTPException(status_code=400, detail="Reply limit reached for this comment")

    message = (body.message if body.message is not None else draft.suggested_reply) or ""
    message = str(message).strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    normalized_hash = sha256_hex(normalize_reply_text(message))
    idempotency_key = f"{draft.platform}:{draft.comment_id}:{normalized_hash}"

    # Send via Graph API
    reply_id: Optional[str] = None
    graph_response: dict = {}

    try:
        if draft.platform == "instagram":
            ig = InstagramGraphAPIClient()
            reply_id = await ig.reply_to_comment(current_user_email, draft.comment_id, message)
            graph_response = {"id": reply_id}
        else:
            # Facebook: derive page access token from stored user access token and page_id
            ev = await CommentEventModel.get(draft.comment_event_id)
            page_id = getattr(ev, "page_id", None) if ev else None
            if not page_id:
                raise HTTPException(status_code=400, detail="Missing page_id for Facebook reply")
            fb_conn = await FacebookConnectionModel.find_one(FacebookConnectionModel.user_id == current_user_email)
            if not fb_conn:
                raise HTTPException(status_code=400, detail="Facebook not connected")
            async with FacebookGraphAPIClient() as fb:
                page_token = await fb.get_page_access_token(fb_conn.access_token, str(page_id))
                reply_id = await fb.reply_to_comment(comment_id=draft.comment_id, page_access_token=page_token, message=message)
                # Best-effort: like the original comment after replying
                try:
                    await fb.like_comment(comment_id=draft.comment_id, page_access_token=page_token)
                except Exception:
                    pass
            graph_response = {"id": reply_id}

    except InstagramAPIError as e:
        # token-expiry / permission failures should surface as reconnect-required notifications
        err = str(getattr(e, "message", "") or str(e))
        code = getattr(e, "code", None)
        token_related = str(code) == "190" or "oauth" in err.lower() or "expired" in err.lower()
        if token_related:
            try:
                svc = NotificationService()
                await svc.create_and_send(
                    user_id=current_user_email,
                    type=NotificationType.ALERT,
                    title="Cannot reply — reconnect Instagram",
                    message="Your Instagram connection appears expired or invalid. Reconnect to resume replying.",
                    metadata={"sub_type": "connection_required", "platform": "instagram"},
                    priority=8,
                )
            except Exception:
                pass
        raise HTTPException(status_code=502, detail=f"Instagram API error: {err}")

    except (FacebookAPIError, Exception) as e:
        err = str(e)
        if "oauth" in err.lower() or "expired" in err.lower() or "190" in err:
            try:
                svc = NotificationService()
                await svc.create_and_send(
                    user_id=current_user_email,
                    type=NotificationType.ALERT,
                    title="Cannot reply — reconnect Facebook",
                    message="Your Facebook connection appears expired or invalid. Reconnect to resume replying.",
                    metadata={"sub_type": "connection_required", "platform": "facebook"},
                    priority=8,
                )
            except Exception:
                pass
        raise HTTPException(status_code=502, detail=f"Facebook API error: {err}")

    # Persist sent record + update draft/event
    sent = AutoReplySentModel(
        comment_event_id=str(draft.comment_event_id),
        draft_id=str(draft.id),
        decision_id=str(draft.decision_id) if getattr(draft, "decision_id", None) else None,
        user_id=current_user_email,
        platform=draft.platform,
        comment_id=draft.comment_id,
        reply_id=reply_id,
        reply_text=message,
        normalized_reply_hash=normalized_hash,
        graph_response=graph_response,
        idempotency_key=idempotency_key,
    )
    await sent.insert()

    draft.status = AutoReplyDraftStatus.SENT
    draft.resolved_at = datetime.utcnow()
    draft.updated_at = datetime.utcnow()
    await draft.save()

    # If this draft is tied to an escalation ticket, auto-resolve the ticket after a successful reply.
    try:
        external_ref = f"meta_comment:{draft.platform}:{draft.comment_id}"
        t = await SocialEscalationTicketModel.find_one(SocialEscalationTicketModel.external_ref == external_ref)
        if t and str(getattr(t, "owner_user_id", "") or "").lower() == str(current_user_email or "").lower():
            if str(getattr(t, "status", "") or "").lower() != "resolved":
                t.status = "resolved"
                t.resolved_at = datetime.utcnow()
                t.updated_at = datetime.utcnow()
                await t.save()
    except Exception:
        pass

    try:
        ev = await CommentEventModel.get(draft.comment_event_id)
        if ev and ev.user_id == current_user_email:
            ev.status = CommentEventStatus.REPLIED
            ev.updated_at = datetime.utcnow()
            await ev.save()
    except Exception:
        pass

    try:
        svc = NotificationService()
        await svc.create_and_send(
            user_id=current_user_email,
            type=NotificationType.SOCIAL_POST,
            title="Reply sent",
            message="Your reply was posted successfully.",
            related_entity_id=str(sent.id),
            metadata={
                "sub_type": "auto_reply_sent",
                "platform": draft.platform,
                "comment_id": draft.comment_id,
                "draft_id": str(draft.id),
                "sent_id": str(sent.id),
            },
            priority=2,
        )
    except Exception:
        pass

    return AutoReplyApproveResponse(
        success=True,
        status="sent",
        reply_id=reply_id,
        sent_id=str(sent.id),
        message="Sent",
    )

