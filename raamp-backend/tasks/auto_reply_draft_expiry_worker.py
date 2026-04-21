"""
Auto Reply Draft Expiry Worker (APScheduler driven)
==================================================
Expires AutoReplyDraftModel rows that passed expires_at and notifies users via digest.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, List

from infrastructure.database.models.auto_reply_models import AutoReplyDraftModel, AutoReplyDraftStatus
from infrastructure.utils.obs import emit_event
from application.services.notification_service import NotificationService
from infrastructure.database.models.notification_model import NotificationType


logger = logging.getLogger(__name__)


async def expire_auto_reply_drafts(*, limit: int = 200) -> Dict[str, int]:
    """
    Expire drafts where status=active and expires_at < now.
    Sends a required per-user digest notification summarizing expirations.
    """
    now = datetime.utcnow()

    due = (
        await AutoReplyDraftModel.find(
            AutoReplyDraftModel.status == AutoReplyDraftStatus.ACTIVE,
            AutoReplyDraftModel.expires_at < now,
        )
        .sort(AutoReplyDraftModel.expires_at)
        .limit(limit)
        .to_list()
    )

    if not due:
        emit_event("auto_replies.draft_expiry.run", expired=0, limit=limit)
        return {"expired": 0}

    by_user: Dict[str, List[AutoReplyDraftModel]] = {}
    for d in due:
        by_user.setdefault(str(d.user_id), []).append(d)

    expired_count = 0
    for user_id, drafts in by_user.items():
        for d in drafts:
            try:
                d.status = AutoReplyDraftStatus.EXPIRED
                d.resolved_at = now
                d.updated_at = now
                await d.save()
                expired_count += 1
            except Exception:
                logger.exception("Failed expiring draft %s", str(getattr(d, "id", "")))

        # Required digest notification (batch per user)
        try:
            n = len(drafts)
            svc = NotificationService()
            await svc.create_and_send(
                user_id=user_id,
                type=NotificationType.SOCIAL_POST,
                title="Reply drafts expired",
                message=f"You have {n} expired reply draft(s). Those comments may have gone unanswered.",
                metadata={
                    "sub_type": "auto_reply_drafts_expired",
                    "count": n,
                    "draft_ids": [str(d.id) for d in drafts],
                },
                priority=4,
            )
        except Exception:
            logger.exception("Failed sending expired draft digest for user=%s", user_id)

    emit_event("auto_replies.draft_expiry.run", expired=expired_count, limit=limit)
    return {"expired": int(expired_count)}

