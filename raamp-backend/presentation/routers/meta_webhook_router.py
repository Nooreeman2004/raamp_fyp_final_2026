"""
Meta Webhook Router (Facebook + Instagram)
=========================================
Implements:
- GET verification handshake
- POST ingestion with signature verification (X-Hub-Signature-256)

This router persists CommentEventModel records and relies on the background worker
step to process RECEIVED events asynchronously.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import PlainTextResponse

from infrastructure.database.models.auto_reply_models import (
    CommentEventModel,
    CommentEventStatus,
)
from infrastructure.utils.obs import emit_event
from tasks import auto_reply_worker


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/meta/webhooks", tags=["Meta Webhooks"])

def _env_flag(name: str) -> bool:
    return str(os.getenv(name) or "").strip().lower() in ("1", "true", "yes", "y", "on")


def _get_required_env(name: str) -> str:
    v = (os.getenv(name) or "").strip()
    if not v:
        raise RuntimeError(f"Missing required env var: {name}")
    return v


def _verify_meta_signature(*, app_secret: str, raw_body: bytes, signature_header: Optional[str]) -> bool:
    """
    Verify `X-Hub-Signature-256: sha256=<hex>` using HMAC-SHA256 over raw request body.
    """
    if not signature_header:
        return False
    sig = signature_header.strip()
    if not sig.lower().startswith("sha256="):
        return False
    provided = sig.split("=", 1)[1].strip()
    computed = hmac.new(app_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(provided, computed)


def _hash_payload(raw_body: bytes) -> str:
    return hashlib.sha256(raw_body).hexdigest()


def _safe_trunc(s: Optional[str], limit: int = 500) -> Optional[str]:
    if s is None:
        return None
    s = str(s)
    return s[:limit]


@router.get("/health")
async def webhook_health():
    """
    Lightweight health endpoint for webhook + worker pipeline.
    """
    pending = await CommentEventModel.find(CommentEventModel.status == CommentEventStatus.RECEIVED).count()
    last_run = getattr(auto_reply_worker, "LAST_RUN_AT", None)
    backend_url = (os.getenv("BACKEND_URL") or "").strip()
    return {
        "worker_last_run_at": (last_run.isoformat() + "Z") if last_run else None,
        "pending_events": int(pending or 0),
        "backend_url": backend_url or None,
    }


def _extract_comment_event(payload: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Best-effort extraction of comment events from Meta webhook payloads.
    Returns (event_dict, platform_guess).

    event_dict shape (all optional):
    - platform: facebook|instagram
    - page_id / ig_business_id
    - post_id / media_id
    - comment_id
    - from_id
    - text
    - created_time (datetime)
    """
    platform_guess: str = "facebook"

    # Meta webhooks commonly provide: { object, entry: [ { id, changes: [ { field, value } ] } ] }
    obj = (payload.get("object") or "").lower()
    if "instagram" in obj:
        platform_guess = "instagram"
    elif "page" in obj or "user" in obj:
        platform_guess = "facebook"

    entry = payload.get("entry")
    if not isinstance(entry, list) or not entry:
        return None, platform_guess

    first_entry = entry[0] if isinstance(entry[0], dict) else {}
    entry_id = first_entry.get("id")

    changes = first_entry.get("changes")
    if not isinstance(changes, list) or not changes:
        # Some payloads use messaging / different shapes; store raw only.
        return None, platform_guess

    # Meta can include multiple changes; pick the first one that looks like a comment.
    selected_change: Dict[str, Any] = {}
    value: Dict[str, Any] = {}
    field = ""
    for ch in changes:
        if not isinstance(ch, dict):
            continue
        v = ch.get("value")
        if not isinstance(v, dict):
            continue

        candidate_comment_id = (
            v.get("comment_id")
            or v.get("id")
            or ((v.get("comment", {}) or {}).get("id") if isinstance(v.get("comment"), dict) else None)
        )
        candidate_text = (
            v.get("text")
            or v.get("message")
            or ((v.get("comment", {}) or {}).get("text") if isinstance(v.get("comment"), dict) else None)
        )
        if candidate_comment_id or candidate_text:
            selected_change = ch
            value = v
            field = (ch.get("field") or "").lower()
            break

    if not selected_change:
        return None, platform_guess

    # Platform refinement from field if possible
    if "instagram" in field:
        platform_guess = "instagram"

    comment_id = (
        value.get("comment_id")
        or value.get("id")
        or ((value.get("comment", {}) or {}).get("id") if isinstance(value.get("comment"), dict) else None)
    )
    text = (
        value.get("text")
        or value.get("message")
        or ((value.get("comment", {}) or {}).get("text") if isinstance(value.get("comment"), dict) else None)
    )
    from_id = None
    if isinstance(value.get("from"), dict):
        from_id = value.get("from", {}).get("id")
    from_id = from_id or value.get("from_id")

    # Parent identifiers (used for platform inference too)
    if isinstance(value.get("post"), dict):
        post_id = value.get("post_id") or (value.get("post", {}) or {}).get("id")
    else:
        post_id = value.get("post_id")

    if isinstance(value.get("media"), dict):
        media_id = value.get("media_id") or (value.get("media", {}) or {}).get("id")
    else:
        media_id = value.get("media_id")
    if media_id is not None:
        # Instagram comment webhooks frequently include media_id/media.
        platform_guess = "instagram"

    # Some Instagram comment webhooks are delivered under object=page with entry.id being the FB Page ID.
    # Preserve entry_id as page_id to allow resolving the user via InstagramConnectionModel.linked_fb_page_id.
    # If the payload carries an explicit ig_business_id, prefer it; otherwise fallback to entry_id.
    if isinstance(value.get("instagram_business_account"), dict):
        explicit_ig_business_id = (
            value.get("ig_business_id")
            or value.get("instagram_business_id")
            or (value.get("instagram_business_account", {}) or {}).get("id")
        )
    else:
        explicit_ig_business_id = value.get("ig_business_id") or value.get("instagram_business_id")

    # Timestamp
    created_time = None
    ct = value.get("created_time") or value.get("timestamp") or value.get("time")
    try:
        if isinstance(ct, (int, float)):
            created_time = datetime.utcfromtimestamp(int(ct))
        elif isinstance(ct, str) and ct.isdigit():
            created_time = datetime.utcfromtimestamp(int(ct))
    except Exception:
        created_time = None

    event: Dict[str, Any] = {
        "platform": platform_guess,
        "comment_id": str(comment_id) if comment_id is not None else None,
        "from_id": str(from_id) if from_id is not None else None,
        "text": str(text) if text is not None else None,
        "created_time": created_time,
    }

    # Use entry_id as the "account" id; map to page_id or ig_business_id as a guess.
    if platform_guess == "instagram":
        # Keep the entry id as page_id as well (often the linked FB Page id).
        event["page_id"] = str(entry_id) if entry_id is not None else None
        event["ig_business_id"] = (
            str(explicit_ig_business_id) if explicit_ig_business_id is not None else (str(entry_id) if entry_id is not None else None)
        )
        if media_id is not None:
            event["media_id"] = str(media_id)
    else:
        event["page_id"] = str(entry_id) if entry_id is not None else None
        if post_id is not None:
            event["post_id"] = str(post_id)

    # Require minimal fields for a real comment event
    if not event.get("comment_id") or not event.get("text"):
        return None, platform_guess

    return event, platform_guess


@router.get("/comments")
async def verify_webhook(request: Request):
    """
    Meta webhook verification handshake.
    Expects query params:
    - hub.mode=subscribe
    - hub.verify_token=<token>
    - hub.challenge=<challenge>
    """
    verify_token = _get_required_env("META_WEBHOOK_VERIFY_TOKEN")
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == verify_token and challenge:
        return PlainTextResponse(content=str(challenge), status_code=status.HTTP_200_OK)

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Webhook verification failed")


@router.post("/comments")
async def ingest_comments(request: Request):
    """
    Ingest Meta webhook events for FB/IG comments.
    Validates request signature and persists CommentEventModel for async processing.
    """
    app_secret = _get_required_env("FACEBOOK_APP_SECRET")
    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256") or request.headers.get("x-hub-signature-256")

    # In production, ALWAYS require a valid signature.
    # For local/dev webhook testing, Meta's "test" deliveries may omit the signature header.
    # Allow opt-in bypass via env to unblock end-to-end testing.
    allow_unsigned = _env_flag("META_WEBHOOK_ALLOW_UNSIGNED") and _env_flag("DEBUG")
    if not signature and allow_unsigned:
        logger.warning("META_WEBHOOK_ALLOW_UNSIGNED enabled; accepting unsigned webhook POST (dev only).")
    elif not _verify_meta_signature(app_secret=app_secret, raw_body=raw_body, signature_header=signature):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid signature")

    try:
        payload = json.loads(raw_body.decode("utf-8") or "{}")
    except Exception:
        payload = {}

    extracted, platform_guess = _extract_comment_event(payload if isinstance(payload, dict) else {})

    # Dedupe key: prefer platform+comment_id; otherwise hash payload.
    if extracted and extracted.get("comment_id"):
        dedupe_key = f"{platform_guess}:{extracted.get('comment_id')}"
    else:
        dedupe_key = f"{platform_guess}:payload:{_hash_payload(raw_body)}"

    # Always persist event for audit/debugging; worker will decide whether it can process.
    try:
        # Best-effort: avoid duplicates on retries (dedupe_key index exists).
        existing = await CommentEventModel.find_one(CommentEventModel.dedupe_key == dedupe_key)
        if existing:
            emit_event(
                "auto_replies.webhook.duplicate",
                user_id=getattr(existing, "user_id", None),
                platform=getattr(existing, "platform", platform_guess),
                dedupe_key=dedupe_key,
            )
            return {"ok": True}

        platform = extracted.get("platform") if extracted else platform_guess
        text = extracted.get("text") if extracted else ""
        comment_id = extracted.get("comment_id") if extracted else f"unknown:{_hash_payload(raw_body)[:16]}"

        doc = CommentEventModel(
            user_id=None,
            platform=str(platform),
            page_id=extracted.get("page_id") if extracted else None,
            ig_business_id=extracted.get("ig_business_id") if extracted else None,
            post_id=extracted.get("post_id") if extracted else None,
            media_id=extracted.get("media_id") if extracted else None,
            comment_id=str(comment_id),
            from_id=extracted.get("from_id") if extracted else None,
            text=str(text or ""),
            created_time=extracted.get("created_time") if extracted else None,
            raw_payload=payload if isinstance(payload, dict) else {},
            dedupe_key=dedupe_key,
            status=CommentEventStatus.RECEIVED,
            error=None,
            updated_at=datetime.utcnow(),
        )
        await doc.insert()
        emit_event(
            "auto_replies.webhook.received",
            user_id=None,
            platform=str(platform),
            comment_id=str(doc.comment_id),
            dedupe_key=dedupe_key,
        )
        return {"ok": True}
    except Exception as e:
        logger.exception("Failed to persist webhook event")
        emit_event(
            "auto_replies.webhook.persist_failed",
            user_id=None,
            platform=str(platform_guess),
            dedupe_key=dedupe_key,
            error=_safe_trunc(str(e)),
        )
        # Return 200 to avoid Meta retry storms; worker/audit will surface failures via monitoring.
        return {"ok": True}

