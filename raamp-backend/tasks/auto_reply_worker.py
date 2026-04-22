"""
Auto Reply Worker (APScheduler driven)
=====================================
Processes CommentEventModel records received from Meta webhooks.

Design:
- APScheduler calls `process_due_auto_replies()` periodically.
- We process CommentEventModel where status=received.
- Policy decisions are persisted; reply publishing is implemented in a later step.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple
from uuid import uuid4

import httpx

from infrastructure.clients.llm_client import LLMClient
from infrastructure.database.models.auto_reply_models import (
    AutoReplyDecisionModel,
    AutoReplyDraftModel,
    AutoReplyDraftStatus,
    AutoReplySentModel,
    CommentEventModel,
    CommentEventStatus,
    PolicyAction,
)
from infrastructure.database.models.auto_reply_settings_model import (
    AutoReplyMode,
    AutoReplySettingsModel,
)
from infrastructure.database.models.facebook_connection_model import FacebookConnectionModel
from infrastructure.database.models.instagram_connection_model import InstagramConnectionModel
from infrastructure.database.models.instagram_post_model import InstagramPostModel
from infrastructure.database.models.social_escalation_ticket_model import (
    SocialEscalationTicketModel,
    SocialEscalationPriority,
    SocialEscalationStatus,
)
from infrastructure.database.models.user_model import UserModel
from infrastructure.database.models.business_model import BusinessModel
from infrastructure.utils.obs import emit_event
from application.services.notification_service import NotificationService
from infrastructure.database.models.notification_model import NotificationType
from application.utils.auto_reply_utils import normalize_reply_text, sha256_hex
from application.services.instagram_graph_api_service import InstagramGraphAPIClient, InstagramAPIError
from application.services.facebook_graph_api_service import FacebookGraphAPIClient, FacebookAPIError
from application.services.encryption_service import EncryptionService


logger = logging.getLogger(__name__)

LAST_RUN_AT: Optional[datetime] = None


SAFE_AUTO_INTENTS = {"pricing", "hours", "location", "availability", "greeting"}

_BASIC_GREET_RE = re.compile(r"^\\s*(hi|hey|hello|hy|hii+|heyy+)\\s*[!.]*\\s*$", re.IGNORECASE)


def _is_basic_greeting(text: str) -> bool:
    t = (text or "").strip()
    if not t:
        return False
    # Keep it very conservative (avoid "hi, I need a refund" etc.)
    if len(t) > 20:
        return False
    return bool(_BASIC_GREET_RE.match(t))


ESCALATION_INTENTS = {"complaint", "refund", "chargeback", "scam", "angry"}


def _is_escalation_intent(intent_label: Optional[str]) -> bool:
    return str(intent_label or "").strip().lower() in ESCALATION_INTENTS


def _map_escalation_priority(intent_label: str) -> Tuple[str, int]:
    """
    Returns (priority, sla_seconds).
    """
    i = str(intent_label or "").strip().lower()
    if i in {"refund", "chargeback", "scam"}:
        return SocialEscalationPriority.CRITICAL, 30 * 60
    if i in {"complaint", "angry"}:
        return SocialEscalationPriority.HIGH, 2 * 60 * 60
    return SocialEscalationPriority.MEDIUM, 24 * 60 * 60


async def _resolve_business_id(owner_user_email: str) -> Optional[str]:
    """
    Resolve BusinessModel.id from owner email.
    Returns stringified business id or None.
    """
    email = str(owner_user_email or "").strip().lower()
    if not email:
        return None
    user = await UserModel.find_one(UserModel.email == email)
    if not user:
        return None
    biz = await BusinessModel.find_one(BusinessModel.user_id == str(user.id))
    return str(biz.id) if biz else None


def _social_account_id_from_event(ev: CommentEventModel) -> Optional[str]:
    if not ev:
        return None
    if str(getattr(ev, "platform", "") or "").lower() == "instagram":
        return str(getattr(ev, "ig_business_id", "") or "").strip() or None
    return str(getattr(ev, "page_id", "") or "").strip() or None


def _truthy(v: Optional[str]) -> bool:
    return str(v or "").strip().lower() in ("1", "true", "yes", "y", "on")


def _llm_timeout_seconds() -> float:
    # Default 8s: intent classification is hot-path and must have a hard timeout.
    raw = (os.getenv("AUTO_REPLY_LLM_TIMEOUT_SECONDS") or "").strip()
    try:
        v = float(raw)
        if v > 0:
            return v
    except Exception:
        pass
    return 8.0


def _draft_ttl_hours() -> int:
    raw = (os.getenv("AUTO_REPLY_DRAFT_TTL_HOURS") or "").strip()
    try:
        v = int(raw)
        if v > 0:
            return v
    except Exception:
        pass
    return 24


def _risk_check(text: str) -> Tuple[bool, str]:
    """
    Conservative keyword/PII heuristic.
    Returns (is_risky, reason).
    """
    t = (text or "").lower()
    if not t.strip():
        return True, "empty_comment"

    # PII patterns
    if re.search(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", t):
        return True, "pii_email"
    if re.search(r"\b(\+?\d[\d\s().-]{7,}\d)\b", t):
        return True, "pii_phone"
    if "address" in t or "my address" in t or "home address" in t:
        return True, "pii_address"

    # Sensitive domains
    sensitive_terms = [
        "diagnosis",
        "prescription",
        "medicine",
        "symptom",
        "lawyer",
        "legal",
        "court",
        "sue",
        "bank",
        "loan",
        "credit card",
        "investment",
        "tax",
        "insurance claim",
    ]
    if any(term in t for term in sensitive_terms):
        return True, "sensitive_domain"

    return False, "ok"


async def _resolve_user_id(event: CommentEventModel) -> Optional[str]:
    """
    Map a webhook event to a RAAMP user.
    - Instagram: match by ig_business_id -> media_id -> linked_fb_page_id
    - Facebook: match by fb_pages list containing page_id
    """
    if event.platform == "instagram":
        # 1) ig_business_id -> user
        if event.ig_business_id:
            ig = await InstagramConnectionModel.find_one(InstagramConnectionModel.ig_business_id == event.ig_business_id)
            if ig:
                emit_event(
                    "auto_replies.user_resolution.matched",
                    platform="instagram",
                    method="ig_business_id",
                    user_id=str(ig.user_id),
                    ig_business_id=str(event.ig_business_id),
                    comment_id=str(event.comment_id),
                )
                return str(ig.user_id)
            emit_event(
                "auto_replies.user_resolution.no_match",
                platform="instagram",
                method="ig_business_id",
                ig_business_id=str(event.ig_business_id),
                comment_id=str(event.comment_id),
            )

        # 2) media_id -> InstagramPostModel -> user_id
        if event.media_id:
            post = await InstagramPostModel.find_one(
                (InstagramPostModel.instagram_post_id == str(event.media_id))
                | (InstagramPostModel.instagram_media_id == str(event.media_id))
            )
            if post:
                emit_event(
                    "auto_replies.user_resolution.matched",
                    platform="instagram",
                    method="media_id",
                    user_id=str(post.user_id),
                    media_id=str(event.media_id),
                    comment_id=str(event.comment_id),
                )
                return str(post.user_id)
            emit_event(
                "auto_replies.user_resolution.no_match",
                platform="instagram",
                method="media_id",
                media_id=str(event.media_id),
                comment_id=str(event.comment_id),
            )

            # 2b) media_id -> probe Graph API across connected accounts (last-resort)
            # Try each InstagramConnectionModel's page_access_token; the first token that can read the media
            # is treated as the owning account for user resolution.
            enc_service = EncryptionService()
            connections = (
                await InstagramConnectionModel.find(
                    InstagramConnectionModel.token_valid == True,  # noqa: E712
                    InstagramConnectionModel.page_access_token != None,  # noqa: E711
                )
                .limit(200)
                .to_list()
            )

            for conn in connections:
                token = enc_service.decrypt(conn.page_access_token)
                if not token:
                    continue

                try:
                    url = f"https://graph.facebook.com/v22.0/{str(event.media_id)}"
                    params = {"fields": "ig_id", "access_token": token}
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        r = await client.get(url, params=params)
                    data = r.json() if r.content else {}
                except Exception as e:
                    emit_event(
                        "auto_replies.user_resolution.graph_probe_error",
                        platform="instagram",
                        method="graph_media_probe",
                        user_id=str(conn.user_id),
                        media_id=str(event.media_id),
                        comment_id=str(event.comment_id),
                        error=str(e)[:300],
                    )
                    continue

                if isinstance(data, dict) and data.get("error"):
                    err = data.get("error") or {}
                    emit_event(
                        "auto_replies.user_resolution.graph_probe_denied",
                        platform="instagram",
                        method="graph_media_probe",
                        user_id=str(conn.user_id),
                        media_id=str(event.media_id),
                        comment_id=str(event.comment_id),
                        error_code=err.get("code"),
                        error_message=str(err.get("message") or "")[:300],
                    )
                    continue

                # Success (no error) => treat this connection/user as the owner
                emit_event(
                    "auto_replies.user_resolution.matched",
                    platform="instagram",
                    method="graph_media_probe",
                    user_id=str(conn.user_id),
                    media_id=str(event.media_id),
                    comment_id=str(event.comment_id),
                )

                # Cache into instagram_posts so future lookups are instant.
                try:
                    existing = await InstagramPostModel.find_one(
                        (InstagramPostModel.instagram_post_id == str(event.media_id))
                        | (InstagramPostModel.instagram_media_id == str(event.media_id))
                    )
                    if not existing:
                        await InstagramPostModel(
                            user_id=str(conn.user_id),
                            ig_business_id=str(conn.ig_business_id or ""),
                            media_url="graph_media_probe_cache",
                            caption=None,
                            media_type="IMAGE",
                            status="published",
                            instagram_media_id=str(event.media_id),
                            instagram_post_id=str(event.media_id),
                            error_message=None,
                            retry_count=0,
                            published_at=None,
                        ).insert()
                        emit_event(
                            "auto_replies.user_resolution.cached",
                            platform="instagram",
                            method="instagram_posts",
                            user_id=str(conn.user_id),
                            media_id=str(event.media_id),
                        )
                except Exception as e:
                    emit_event(
                        "auto_replies.user_resolution.cache_failed",
                        platform="instagram",
                        method="instagram_posts",
                        user_id=str(conn.user_id),
                        media_id=str(event.media_id),
                        error=str(e)[:300],
                    )

                return str(conn.user_id)

        # 3) linked_fb_page_id -> user
        if event.page_id:
            ig = await InstagramConnectionModel.find_one(InstagramConnectionModel.linked_fb_page_id == event.page_id)
            if ig:
                emit_event(
                    "auto_replies.user_resolution.matched",
                    platform="instagram",
                    method="linked_fb_page_id",
                    user_id=str(ig.user_id),
                    linked_fb_page_id=str(event.page_id),
                    comment_id=str(event.comment_id),
                )
                return str(ig.user_id)
            emit_event(
                "auto_replies.user_resolution.no_match",
                platform="instagram",
                method="linked_fb_page_id",
                linked_fb_page_id=str(event.page_id),
                comment_id=str(event.comment_id),
            )
        return None

    # Facebook
    if event.page_id:
        fb = await FacebookConnectionModel.find_one({"fb_pages.id": str(event.page_id)})
        if fb:
            emit_event(
                "auto_replies.user_resolution.matched",
                platform="facebook",
                method="page_id",
                user_id=str(fb.user_id),
                page_id=str(event.page_id),
                comment_id=str(event.comment_id),
            )
            return str(fb.user_id)
        emit_event(
            "auto_replies.user_resolution.no_match",
            platform="facebook",
            method="page_id",
            page_id=str(event.page_id),
            comment_id=str(event.comment_id),
        )
    return None


async def _get_settings(user_id: str) -> AutoReplySettingsModel:
    settings = await AutoReplySettingsModel.find_one(AutoReplySettingsModel.user_id == user_id)
    if settings:
        return settings
    # Default off, review-only.
    settings = AutoReplySettingsModel(user_id=user_id)
    await settings.insert()
    return settings


def _platform_enabled(settings: AutoReplySettingsModel, platform: str) -> bool:
    if platform == "instagram":
        return bool(settings.instagram_auto_replies_enabled)
    return bool(settings.facebook_auto_replies_enabled)


def _platform_mode(settings: AutoReplySettingsModel, platform: str) -> str:
    if platform == "instagram":
        return str(getattr(settings, "instagram_mode", AutoReplyMode.REVIEW_ONLY))
    return str(getattr(settings, "facebook_mode", AutoReplyMode.REVIEW_ONLY))


async def _classify_intent_llm(*, llm: LLMClient, comment_text: str) -> Dict[str, Any]:
    """
    LLM intent classifier with strict timeout. On timeout/failure, caller must route to needs_review.
    """
    if not getattr(llm, "client", None):
        raise RuntimeError("llm_unavailable")

    system_prompt = (
        "You are a fast intent classifier for social media comments.\n"
        "Return ONLY valid JSON.\n"
        "Do not include markdown.\n"
    )
    user_prompt = f"""
Classify the user's intent for this comment.

Comment:
{comment_text}

Return JSON with keys:
- intent_label: one of [pricing, hours, location, availability, complaint, spam, greeting, purchase_intent, irrelevant, other]
- confidence: number 0..1
- reason: short string
""".strip()

    timeout_s = _llm_timeout_seconds()

    # LLMClient.generate_structured_json is async but uses a sync OpenAI client internally.
    # Run it off the event loop and enforce a hard timeout.
    coro = llm.generate_structured_json(system_prompt, user_prompt)
    payload = await asyncio.wait_for(coro, timeout=timeout_s)
    if not isinstance(payload, dict):
        raise RuntimeError("llm_invalid_json")
    return payload


async def _generate_reply_llm(*, llm: LLMClient, comment_text: str, intent_label: str) -> str:
    if not getattr(llm, "client", None):
        raise RuntimeError("llm_unavailable")

    system_prompt = (
        "You write short, helpful, brand-safe replies to social media comments.\n"
        "Be concise, polite, and avoid promises.\n"
        "Return ONLY valid JSON.\n"
    )
    user_prompt = f"""
Write a single reply to this comment.

Intent: {intent_label}
Comment: {comment_text}

Return JSON with keys:
- reply: string
""".strip()

    timeout_s = _llm_timeout_seconds()
    payload = await asyncio.wait_for(llm.generate_structured_json(system_prompt, user_prompt), timeout=timeout_s)
    reply = str((payload or {}).get("reply") or "").strip()
    if not reply:
        raise RuntimeError("llm_empty_reply")
    return reply


async def process_due_auto_replies(limit: int = 10) -> Dict[str, int]:
    """
    Process up to `limit` received comment events.
    """
    global LAST_RUN_AT
    LAST_RUN_AT = datetime.utcnow()

    now = datetime.utcnow()
    processed = 0
    skipped = 0
    needs_review = 0
    auto_reply_selected = 0
    failed = 0
    llm_timeouts = 0
    token_expiry_failures = 0

    events = (
        await CommentEventModel.find(CommentEventModel.status == CommentEventStatus.RECEIVED)
        .sort(CommentEventModel.created_at)
        .limit(limit)
        .to_list()
    )

    if not events:
        emit_event(
            "auto_replies.worker.run",
            processed=0,
            skipped=0,
            needs_review=0,
            auto_reply_selected=0,
            failed=0,
            llm_timeouts=0,
            limit=limit,
        )
        return {
            "processed": 0,
            "skipped": 0,
            "needs_review": 0,
            "auto_reply_selected": 0,
            "failed": 0,
            "llm_timeouts": 0,
            "token_expiry_failures": 0,
        }

    llm = LLMClient()
    notification_service = NotificationService()

    for ev in events:
        processed += 1
        try:
            user_id = await _resolve_user_id(ev)
            if not user_id:
                ev.status = CommentEventStatus.FAILED
                ev.error = "user_not_resolved"
                ev.updated_at = datetime.utcnow()
                await ev.save()
                failed += 1
                emit_event(
                    "auto_replies.event.failed",
                    user_id=None,
                    platform=ev.platform,
                    comment_id=str(ev.comment_id),
                    error="user_not_resolved",
                )
                continue

            # Attach ownership to the event (best-effort).
            if not ev.user_id:
                ev.user_id = user_id
                ev.updated_at = datetime.utcnow()
                await ev.save()

            settings = await _get_settings(user_id)

            # Skip "self-comments" (our own Page/IG account replies) to avoid loops,
            # duplicated drafts, and showing our reply text as the "user comment".
            try:
                from_id = str(getattr(ev, "from_id", "") or "").strip()
                page_id = str(getattr(ev, "page_id", "") or "").strip()
                ig_business_id = str(getattr(ev, "ig_business_id", "") or "").strip()

                is_self = False
                if ev.platform == "facebook" and from_id and page_id and from_id == page_id:
                    is_self = True
                if ev.platform == "instagram" and from_id and ig_business_id and from_id == ig_business_id:
                    is_self = True

                # Strong fallback: if this comment_id is a reply_id we already posted,
                # then the webhook event is about our own reply, and must never trigger another reply.
                if not is_self:
                    already_ours = await AutoReplySentModel.find_one(
                        AutoReplySentModel.platform == ev.platform,
                        AutoReplySentModel.reply_id == str(ev.comment_id),
                    )
                    if already_ours:
                        is_self = True

                if is_self:
                    await AutoReplyDecisionModel(
                        comment_event_id=str(ev.id),
                        user_id=user_id,
                        platform=ev.platform,
                        comment_id=str(ev.comment_id),
                        intent_label=None,
                        confidence=None,
                        risk_level="low",
                        policy_action=PolicyAction.SKIP,
                        reason="self_comment",
                        context_snapshot={},
                    ).insert()
                    ev.status = CommentEventStatus.SKIPPED
                    ev.updated_at = datetime.utcnow()
                    await ev.save()
                    skipped += 1
                    emit_event(
                        "auto_replies.event.skipped",
                        user_id=user_id,
                        platform=ev.platform,
                        comment_id=str(ev.comment_id),
                        reason="self_comment",
                    )
                    continue
            except Exception:
                # Never break pipeline on self-check issues
                pass

            if not _platform_enabled(settings, ev.platform):
                # Persist decision for auditability.
                await AutoReplyDecisionModel(
                    comment_event_id=str(ev.id),
                    user_id=user_id,
                    platform=ev.platform,
                    comment_id=str(ev.comment_id),
                    intent_label=None,
                    confidence=None,
                    risk_level="low",
                    policy_action=PolicyAction.SKIP,
                    reason="platform_disabled",
                    context_snapshot={},
                ).insert()
                ev.status = CommentEventStatus.SKIPPED
                ev.updated_at = datetime.utcnow()
                await ev.save()
                skipped += 1
                emit_event(
                    "auto_replies.event.skipped",
                    user_id=user_id,
                    platform=ev.platform,
                    comment_id=str(ev.comment_id),
                    reason="platform_disabled",
                )
                continue

            # Risk check must run BEFORE any reply-generation calls.
            risky, risk_reason = _risk_check(ev.text)
            if risky:
                decision = await AutoReplyDecisionModel(
                    comment_event_id=str(ev.id),
                    user_id=user_id,
                    platform=ev.platform,
                    comment_id=str(ev.comment_id),
                    intent_label=None,
                    confidence=None,
                    risk_level="high",
                    policy_action=PolicyAction.NEEDS_REVIEW,
                    reason=f"risk:{risk_reason}",
                    context_snapshot={},
                ).insert()

                draft = AutoReplyDraftModel(
                    comment_event_id=str(ev.id),
                    decision_id=str(decision.id),
                    user_id=user_id,
                    platform=ev.platform,
                    comment_id=str(ev.comment_id),
                    suggested_reply="(No auto-suggestion generated due to sensitivity.)",
                    alternatives=[],
                    requires_user_action=True,
                    expires_at=now + timedelta(hours=_draft_ttl_hours()),
                    status=AutoReplyDraftStatus.ACTIVE,
                    resolved_at=None,
                    approval_nonce=str(uuid4()),
                    updated_at=datetime.utcnow(),
                )
                await draft.insert()
                await notification_service.create_and_send(
                    user_id=user_id,
                    type=NotificationType.SOCIAL_POST,
                    title="Reply needs review",
                    message="A comment may contain sensitive info. Review is required before replying.",
                    related_entity_id=str(draft.id),
                    metadata={
                        "sub_type": "auto_reply_needs_review",
                        "platform": ev.platform,
                        "comment_id": str(ev.comment_id),
                        "action": PolicyAction.NEEDS_REVIEW,
                        "reason": f"risk:{risk_reason}",
                        "draft_id": str(draft.id),
                    },
                    priority=5,
                )

                ev.status = CommentEventStatus.PROCESSED
                ev.updated_at = datetime.utcnow()
                await ev.save()
                needs_review += 1
                emit_event(
                    "auto_replies.event.needs_review",
                    user_id=user_id,
                    platform=ev.platform,
                    comment_id=str(ev.comment_id),
                    reason=f"risk:{risk_reason}",
                    draft_id=str(draft.id),
                )
                continue

            # Fast-path: basic greetings shouldn't wait for user approval.
            # Only auto-send when the platform mode is HYBRID_AUTO (still respects settings).
            mode = _platform_mode(settings, ev.platform)
            if mode == AutoReplyMode.HYBRID_AUTO and _is_basic_greeting(ev.text):
                intent_label = "greeting"
                confidence_f = 1.0
                reason = "heuristic_greeting"
            else:
                intent_label = None
                confidence_f = None
                reason = ""

            # Intent classification (highest latency) with timeout + fallback.
            if intent_label is None:
                try:
                    cls = await _classify_intent_llm(llm=llm, comment_text=ev.text)
                    intent_label = str(cls.get("intent_label") or "other").strip().lower()
                    confidence = cls.get("confidence")
                    try:
                        confidence_f = float(confidence)
                    except Exception:
                        confidence_f = 0.0
                    reason = str(cls.get("reason") or "").strip()[:200]
                except asyncio.TimeoutError:
                    llm_timeouts += 1
                    intent_label = None
                    confidence_f = None
                    reason = "llm_timeout"
                except Exception as e:
                    intent_label = None
                    confidence_f = None
                    reason = f"llm_failed:{str(e)[:120]}"

            # Never auto-skip/auto-reply on failed classification: always needs_review.
            if not intent_label:
                decision = await AutoReplyDecisionModel(
                    comment_event_id=str(ev.id),
                    user_id=user_id,
                    platform=ev.platform,
                    comment_id=str(ev.comment_id),
                    intent_label=None,
                    confidence=None,
                    risk_level="low",
                    policy_action=PolicyAction.NEEDS_REVIEW,
                    reason=reason,
                    context_snapshot={},
                ).insert()
                draft = AutoReplyDraftModel(
                    comment_event_id=str(ev.id),
                    decision_id=str(decision.id),
                    user_id=user_id,
                    platform=ev.platform,
                    comment_id=str(ev.comment_id),
                    suggested_reply="(No auto-suggestion generated due to classification failure.)",
                    alternatives=[],
                    requires_user_action=True,
                    expires_at=now + timedelta(hours=_draft_ttl_hours()),
                    status=AutoReplyDraftStatus.ACTIVE,
                    resolved_at=None,
                    approval_nonce=str(uuid4()),
                    updated_at=datetime.utcnow(),
                )
                await draft.insert()
                await notification_service.create_and_send(
                    user_id=user_id,
                    type=NotificationType.SOCIAL_POST,
                    title="Reply needs review",
                    message="We couldn't confidently classify a new comment. Review is required before replying.",
                    related_entity_id=str(draft.id),
                    metadata={
                        "sub_type": "auto_reply_needs_review",
                        "platform": ev.platform,
                        "comment_id": str(ev.comment_id),
                        "action": PolicyAction.NEEDS_REVIEW,
                        "reason": reason,
                        "draft_id": str(draft.id),
                    },
                    priority=5,
                )

                ev.status = CommentEventStatus.PROCESSED
                ev.updated_at = datetime.utcnow()
                await ev.save()
                needs_review += 1
                emit_event(
                    "auto_replies.event.needs_review",
                    user_id=user_id,
                    platform=ev.platform,
                    comment_id=str(ev.comment_id),
                    reason=reason,
                    draft_id=str(draft.id),
                )
                continue

            mode = _platform_mode(settings, ev.platform)

            # Escalation routing: complaint/refund/chargeback/scam/angry -> needs_review + ticket + admin alert.
            # This is independent of auto-send mode (even review_only should still escalate).
            if _is_escalation_intent(intent_label):
                try:
                    business_id = await _resolve_business_id(user_id)
                    social_account_id = _social_account_id_from_event(ev)
                    if business_id and social_account_id:
                        priority, sla_seconds = _map_escalation_priority(str(intent_label))
                        external_ref = f"meta_comment:{str(ev.platform)}:{str(ev.comment_id)}"

                        # Ensure decision exists (needs review)
                        decision = await AutoReplyDecisionModel(
                            comment_event_id=str(ev.id),
                            user_id=user_id,
                            platform=ev.platform,
                            comment_id=str(ev.comment_id),
                            intent_label=str(intent_label),
                            confidence=float(confidence_f) if confidence_f is not None else None,
                            risk_level="low",
                            policy_action=PolicyAction.NEEDS_REVIEW,
                            reason="escalation_intent",
                            context_snapshot={},
                        ).insert()

                        # Generate a draft suggestion (still editable)
                        suggested = await _generate_reply_llm(llm=llm, comment_text=ev.text, intent_label=str(intent_label))
                        draft = AutoReplyDraftModel(
                            comment_event_id=str(ev.id),
                            decision_id=str(decision.id),
                            user_id=user_id,
                            platform=ev.platform,
                            comment_id=str(ev.comment_id),
                            suggested_reply=suggested,
                            alternatives=[],
                            requires_user_action=True,
                            expires_at=now + timedelta(hours=_draft_ttl_hours()),
                            status=AutoReplyDraftStatus.ACTIVE,
                            resolved_at=None,
                            approval_nonce=str(uuid4()),
                            updated_at=datetime.utcnow(),
                        )
                        await draft.insert()

                        # Upsert ticket by external_ref (dedupe)
                        ticket = await SocialEscalationTicketModel.find_one(SocialEscalationTicketModel.external_ref == external_ref)
                        created = False
                        if not ticket:
                            created = True
                            ticket = SocialEscalationTicketModel(
                                business_id=str(business_id),
                                social_account_id=str(social_account_id),
                                owner_user_id=str(user_id),
                                external_ref=external_ref,
                                comment_event_id=str(ev.id),
                                draft_id=str(draft.id),
                                platform=str(ev.platform),
                                comment_id=str(ev.comment_id),
                                intent=str(intent_label),
                                confidence=float(confidence_f) if confidence_f is not None else None,
                                priority=str(priority),
                                status=SocialEscalationStatus.OPEN,
                                sla_seconds=int(sla_seconds),
                                sla_due_at=(datetime.utcnow() + timedelta(seconds=int(sla_seconds))),
                                context={
                                    "comment_text": (ev.text or "")[:800],
                                    "from_id": getattr(ev, "from_id", None),
                                },
                            )
                            await ticket.insert()
                        else:
                            # Keep ticket current, but do not overwrite lifecycle timestamps.
                            ticket.comment_event_id = str(ev.id)
                            ticket.draft_id = str(draft.id)
                            ticket.intent = str(intent_label)
                            ticket.confidence = float(confidence_f) if confidence_f is not None else None
                            ticket.priority = str(priority)
                            ticket.updated_at = datetime.utcnow()
                            await ticket.save()

                        # Admin notification (deduped via NotificationService metadata.dedupe_key)
                        try:
                            await notification_service.create_and_send(
                                user_id=user_id,
                                type=NotificationType.ALERT,
                                title=f"Escalation: {str(intent_label).replace('_', ' ').title()}",
                                message="A customer comment needs urgent review.",
                                related_entity_id=str(ticket.id),
                                metadata={
                                    "sub_type": "social_escalation",
                                    "ticket_id": str(ticket.id),
                                    "draft_id": str(draft.id),
                                    "platform": str(ev.platform),
                                    "comment_id": str(ev.comment_id),
                                    "intent": str(intent_label),
                                    "priority": str(priority),
                                    "sla_due_at": ticket.sla_due_at.isoformat() if getattr(ticket, "sla_due_at", None) else None,
                                },
                                priority=9 if str(priority) == SocialEscalationPriority.CRITICAL else 7,
                            )
                            ticket.admin_notification_sent_at = datetime.utcnow()
                            ticket.updated_at = datetime.utcnow()
                            await ticket.save()
                        except Exception:
                            pass

                        # Mark event processed so it won't re-run classification.
                        ev.status = CommentEventStatus.PROCESSED
                        ev.updated_at = datetime.utcnow()
                        await ev.save()
                        needs_review += 1
                        emit_event(
                            "auto_replies.escalation.ticket_created" if created else "auto_replies.escalation.ticket_deduped",
                            user_id=user_id,
                            platform=str(ev.platform),
                            comment_id=str(ev.comment_id),
                            ticket_id=str(ticket.id),
                            priority=str(priority),
                        )
                        continue
                except Exception:
                    # If escalation routing fails, fall back to normal flow (draft/needs_review).
                    pass

            should_auto = (
                mode == AutoReplyMode.HYBRID_AUTO
                and intent_label in SAFE_AUTO_INTENTS
                and (confidence_f is not None and confidence_f >= 0.80)
            )

            policy_action = PolicyAction.AUTO_REPLY if should_auto else PolicyAction.NEEDS_REVIEW

            decision = await AutoReplyDecisionModel(
                comment_event_id=str(ev.id),
                user_id=user_id,
                platform=ev.platform,
                comment_id=str(ev.comment_id),
                intent_label=intent_label,
                confidence=float(confidence_f) if confidence_f is not None else None,
                risk_level="low",
                policy_action=policy_action,
                reason=reason or "ok",
                context_snapshot={},
            ).insert()

            # Reply generation (only after risk check).
            # If generation fails, degrade to needs_review and do not auto-send.
            suggested: str
            try:
                suggested = await _generate_reply_llm(llm=llm, comment_text=ev.text, intent_label=intent_label)
            except asyncio.TimeoutError:
                llm_timeouts += 1
                suggested = "(No auto-suggestion generated due to LLM timeout.)"
                policy_action = PolicyAction.NEEDS_REVIEW
                decision.policy_action = PolicyAction.NEEDS_REVIEW
                decision.reason = "reply_llm_timeout"
                await decision.save()
            except Exception as e:
                suggested = "(No auto-suggestion generated due to LLM failure.)"
                policy_action = PolicyAction.NEEDS_REVIEW
                decision.policy_action = PolicyAction.NEEDS_REVIEW
                decision.reason = f"reply_llm_failed:{str(e)[:120]}"
                await decision.save()

            # Until Graph reply publishing is implemented (next step), store as a draft.
            # For auto-reply-selected cases we set requires_user_action=False so UI can distinguish.
            draft = AutoReplyDraftModel(
                comment_event_id=str(ev.id),
                decision_id=str(decision.id),
                user_id=user_id,
                platform=ev.platform,
                comment_id=str(ev.comment_id),
                suggested_reply=suggested,
                alternatives=[],
                requires_user_action=(policy_action != PolicyAction.AUTO_REPLY),
                expires_at=now + timedelta(hours=_draft_ttl_hours()),
                status=AutoReplyDraftStatus.ACTIVE,
                resolved_at=None,
                approval_nonce=str(uuid4()),
                updated_at=datetime.utcnow(),
            )
            await draft.insert()

            ev.status = CommentEventStatus.PROCESSED
            ev.updated_at = datetime.utcnow()
            await ev.save()

            if policy_action == PolicyAction.AUTO_REPLY:
                auto_reply_selected += 1
                await notification_service.create_and_send(
                    user_id=user_id,
                    type=NotificationType.SOCIAL_POST,
                    title="Auto-reply ready",
                    message="A high-confidence reply was prepared and is ready to send.",
                    related_entity_id=str(draft.id),
                    metadata={
                        "sub_type": "auto_reply_auto_selected",
                        "platform": ev.platform,
                        "comment_id": str(ev.comment_id),
                        "action": PolicyAction.AUTO_REPLY,
                        "intent": intent_label,
                        "confidence": float(confidence_f),
                        "draft_id": str(draft.id),
                    },
                    priority=2,
                )

                # If platform is in HYBRID_AUTO mode, post immediately.
                # On any auth/token failure, degrade to needs_review and notify reconnect-required.
                try:
                    normalized_hash = sha256_hex(normalize_reply_text(suggested))
                    idempotency_key = f"{ev.platform}:{ev.comment_id}:{normalized_hash}"

                    already_sent = await AutoReplySentModel.find_one(AutoReplySentModel.idempotency_key == idempotency_key)
                    if already_sent:
                        # Treat as idempotent success.
                        draft.status = AutoReplyDraftStatus.SENT
                        draft.resolved_at = datetime.utcnow()
                        draft.updated_at = datetime.utcnow()
                        await draft.save()

                        ev.status = CommentEventStatus.REPLIED
                        ev.updated_at = datetime.utcnow()
                        await ev.save()
                        emit_event(
                            "auto_replies.event.auto_reply_idempotent",
                            user_id=user_id,
                            platform=ev.platform,
                            comment_id=str(ev.comment_id),
                            sent_id=str(already_sent.id),
                        )
                    else:
                        # Guardrail: cap number of replies per comment (prevent spam loops)
                        sent_count = await AutoReplySentModel.find(
                            AutoReplySentModel.platform == ev.platform,
                            AutoReplySentModel.comment_id == str(ev.comment_id),
                        ).count()
                        if int(sent_count) >= 2:
                            raise RuntimeError("reply_limit_reached")

                        reply_id = None
                        if ev.platform == "instagram":
                            ig = InstagramGraphAPIClient()
                            reply_id = await ig.reply_to_comment(user_id, str(ev.comment_id), suggested)
                        else:
                            # Facebook: require page_id on the event; use stored FB user token to derive page token.
                            if not ev.page_id:
                                raise RuntimeError("missing_page_id")
                            fb_conn = await FacebookConnectionModel.find_one(FacebookConnectionModel.user_id == user_id)
                            if not fb_conn:
                                raise RuntimeError("facebook_not_connected")
                            async with FacebookGraphAPIClient() as fb:
                                page_token = await fb.get_page_access_token(fb_conn.access_token, str(ev.page_id))
                                reply_id = await fb.reply_to_comment(
                                    comment_id=str(ev.comment_id),
                                    page_access_token=page_token,
                                    message=suggested,
                                )
                                # Best-effort: like the original comment after replying
                                try:
                                    liked = await fb.like_comment(comment_id=str(ev.comment_id), page_access_token=page_token)
                                    emit_event(
                                        "auto_replies.comment_liked",
                                        user_id=user_id,
                                        platform="facebook",
                                        comment_id=str(ev.comment_id),
                                        success=bool(liked),
                                    )
                                except Exception:
                                    pass

                        sent = AutoReplySentModel(
                            comment_event_id=str(ev.id),
                            draft_id=str(draft.id),
                            decision_id=str(decision.id),
                            user_id=user_id,
                            platform=ev.platform,
                            comment_id=str(ev.comment_id),
                            reply_id=str(reply_id) if reply_id else None,
                            reply_text=suggested,
                            normalized_reply_hash=normalized_hash,
                            graph_response={"id": str(reply_id)} if reply_id else {},
                            idempotency_key=idempotency_key,
                        )
                        await sent.insert()

                        draft.status = AutoReplyDraftStatus.SENT
                        draft.resolved_at = datetime.utcnow()
                        draft.updated_at = datetime.utcnow()
                        await draft.save()

                        ev.status = CommentEventStatus.REPLIED
                        ev.updated_at = datetime.utcnow()
                        await ev.save()

                        await notification_service.create_and_send(
                            user_id=user_id,
                            type=NotificationType.SOCIAL_POST,
                            title="Auto-reply sent",
                            message="A reply was posted automatically.",
                            related_entity_id=str(sent.id),
                            metadata={
                                "sub_type": "auto_reply_sent",
                                "platform": ev.platform,
                                "comment_id": str(ev.comment_id),
                                "draft_id": str(draft.id),
                                "sent_id": str(sent.id),
                            },
                            priority=2,
                        )
                        emit_event(
                            "auto_replies.event.auto_reply_sent",
                            user_id=user_id,
                            platform=ev.platform,
                            comment_id=str(ev.comment_id),
                            sent_id=str(sent.id),
                        )

                except InstagramAPIError as e:
                    token_expiry_failures += 1
                    decision.policy_action = PolicyAction.NEEDS_REVIEW
                    decision.reason = f"token_error:{str(getattr(e, 'code', '') or '')}"
                    await decision.save()
                    draft.requires_user_action = True
                    draft.updated_at = datetime.utcnow()
                    await draft.save()
                    await notification_service.create_and_send(
                        user_id=user_id,
                        type=NotificationType.ALERT,
                        title="Cannot auto-reply — reconnect Instagram",
                        message="Your Instagram connection appears expired/invalid. Reconnect to resume auto-replies.",
                        metadata={"sub_type": "connection_required", "platform": "instagram"},
                        priority=8,
                    )
                    emit_event(
                        "auto_replies.token_expiry_failure",
                        user_id=user_id,
                        platform="instagram",
                        comment_id=str(ev.comment_id),
                        error=str(getattr(e, "message", "") or str(e))[:200],
                    )
                except FacebookAPIError as e:
                    token_expiry_failures += 1
                    decision.policy_action = PolicyAction.NEEDS_REVIEW
                    decision.reason = "facebook_api_error"
                    await decision.save()
                    draft.requires_user_action = True
                    draft.updated_at = datetime.utcnow()
                    await draft.save()
                    await notification_service.create_and_send(
                        user_id=user_id,
                        type=NotificationType.ALERT,
                        title="Cannot auto-reply — reconnect Facebook",
                        message="Your Facebook connection appears expired/invalid. Reconnect to resume auto-replies.",
                        metadata={"sub_type": "connection_required", "platform": "facebook"},
                        priority=8,
                    )
                    emit_event(
                        "auto_replies.token_expiry_failure",
                        user_id=user_id,
                        platform="facebook",
                        comment_id=str(ev.comment_id),
                        error=str(e)[:200],
                    )
                except Exception as e:
                    # Degrade to needs_review on any send failure.
                    decision.policy_action = PolicyAction.NEEDS_REVIEW
                    decision.reason = f"auto_send_failed:{str(e)[:120]}"
                    await decision.save()
                    draft.requires_user_action = True
                    draft.updated_at = datetime.utcnow()
                    await draft.save()
                    emit_event(
                        "auto_replies.event.auto_send_failed",
                        user_id=user_id,
                        platform=ev.platform,
                        comment_id=str(ev.comment_id),
                        error=str(e)[:200],
                    )

                emit_event(
                    "auto_replies.event.auto_reply_selected",
                    user_id=user_id,
                    platform=ev.platform,
                    comment_id=str(ev.comment_id),
                    intent=intent_label,
                    confidence=float(confidence_f),
                    draft_id=str(draft.id),
                )
            else:
                needs_review += 1
                await notification_service.create_and_send(
                    user_id=user_id,
                    type=NotificationType.SOCIAL_POST,
                    title="Reply suggestion ready",
                    message="A reply suggestion is ready for your approval.",
                    related_entity_id=str(draft.id),
                    metadata={
                        "sub_type": "auto_reply_needs_review",
                        "platform": ev.platform,
                        "comment_id": str(ev.comment_id),
                        "action": PolicyAction.NEEDS_REVIEW,
                        "intent": intent_label,
                        "confidence": float(confidence_f),
                        "draft_id": str(draft.id),
                    },
                    priority=3,
                )
                emit_event(
                    "auto_replies.event.needs_review",
                    user_id=user_id,
                    platform=ev.platform,
                    comment_id=str(ev.comment_id),
                    intent=intent_label,
                    confidence=float(confidence_f),
                    draft_id=str(draft.id),
                )

        except Exception as e:
            failed += 1
            try:
                ev.status = CommentEventStatus.FAILED
                ev.error = str(e)[:500]
                ev.updated_at = datetime.utcnow()
                await ev.save()
            except Exception:
                pass
            emit_event(
                "auto_replies.event.failed",
                user_id=getattr(ev, "user_id", None),
                platform=getattr(ev, "platform", None),
                comment_id=str(getattr(ev, "comment_id", "")),
                error=str(e)[:200],
            )

    summary = {
        "processed": processed,
        "skipped": skipped,
        "needs_review": needs_review,
        "auto_reply_selected": auto_reply_selected,
        "failed": failed,
        "llm_timeouts": llm_timeouts,
        "token_expiry_failures": token_expiry_failures,
    }
    emit_event("auto_replies.worker.run", **summary, limit=limit)
    return summary

