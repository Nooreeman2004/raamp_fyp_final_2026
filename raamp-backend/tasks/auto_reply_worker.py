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
from infrastructure.utils.obs import emit_event
from application.services.notification_service import NotificationService
from infrastructure.database.models.notification_model import NotificationType
from application.utils.auto_reply_utils import normalize_reply_text, sha256_hex
from application.services.instagram_graph_api_service import InstagramGraphAPIClient, InstagramAPIError
from application.services.facebook_graph_api_service import FacebookGraphAPIClient, FacebookAPIError


logger = logging.getLogger(__name__)


SAFE_AUTO_INTENTS = {"pricing", "hours", "location", "availability", "greeting"}


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
    - Instagram: match by ig_business_id or linked_fb_page_id
    - Facebook: match by fb_pages list containing page_id
    """
    if event.platform == "instagram":
        if event.ig_business_id:
            ig = await InstagramConnectionModel.find_one(InstagramConnectionModel.ig_business_id == event.ig_business_id)
            if ig:
                return str(ig.user_id)
        if event.page_id:
            ig = await InstagramConnectionModel.find_one(InstagramConnectionModel.linked_fb_page_id == event.page_id)
            if ig:
                return str(ig.user_id)
        # Fallback: for media that was created/published via RAAMP, map media_id -> post -> user.
        if event.media_id:
            post = await InstagramPostModel.find_one(
                (InstagramPostModel.instagram_post_id == str(event.media_id))
                | (InstagramPostModel.instagram_media_id == str(event.media_id))
            )
            if post:
                return str(post.user_id)
        return None

    # Facebook
    if event.page_id:
        fb = await FacebookConnectionModel.find_one({"fb_pages.id": str(event.page_id)})
        if fb:
            return str(fb.user_id)
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

            # Intent classification (highest latency) with timeout + fallback.
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

