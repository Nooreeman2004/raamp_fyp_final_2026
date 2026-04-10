"""
application/services/caption_roi_join_service.py — Backfill caption_logs.engagement_rate
======================================================================================
Links:
  caption_logs (CaptionLogModel)  ←→  instagram_posts / scheduled_instagram_posts / instagram_stories

Goal:
  Populate CaptionLogModel.engagement_rate so the ML trainer can learn from real outcomes.

Key constraint:
  There is no hard foreign key from an Instagram post back to a caption_log entry.
  We therefore use a best-effort heuristic join:
    - same user_id
    - same asset type (post/story/reel)
    - caption text match (substring match against IG caption) when available
    - otherwise, time proximity (closest caption_log.created_at to post.created_at/published time)

Important normalization:
  Instagram ROI service stores engagement_rate as a PERCENT (e.g., 3.4).
  ML expects a RATE fraction (e.g., 0.034). We write back percent/100.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional, Iterable

from infrastructure.database.models.caption_log_model import CaptionLogModel, AssetTypeEnum
from infrastructure.database.models.instagram_post_model import (
    InstagramPostModel,
    ScheduledInstagramPostModel,
    InstagramStoryModel,
)

logger = logging.getLogger(__name__)


def _utc(dt: Optional[datetime]) -> Optional[datetime]:
    if not dt:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _norm_text(s: str) -> str:
    # lower, collapse whitespace, strip most punctuation noise
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def _caption_in_post(caption_text: str, post_caption: str) -> bool:
    """
    True if caption_text appears inside post_caption after normalization.
    This handles cases where the IG caption includes hashtags appended.
    """
    a = _norm_text(caption_text)
    b = _norm_text(post_caption)
    if not a or not b:
        return False
    return a in b


@dataclass(frozen=True)
class _IGItem:
    kind: str  # "post" | "scheduled_post" | "story"
    id: str
    user_id: str
    caption: str
    created_at: Optional[datetime]
    published_at: Optional[datetime]
    roi_engagement_percent: float


async def _iter_recent_ig_items(
    *,
    lookback_days: int,
    limit_per_collection: int,
) -> list[_IGItem]:
    """
    Pull recent IG items with ROI success and a non-zero engagement rate.
    """
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=max(1, lookback_days))

    posts = await InstagramPostModel.find(
        InstagramPostModel.roi_metrics.fetch_status == "success",
        InstagramPostModel.roi_metrics.engagement_rate > 0,
        InstagramPostModel.created_at >= since,
    ).sort(-InstagramPostModel.created_at).limit(limit_per_collection).to_list()

    scheduled = await ScheduledInstagramPostModel.find(
        ScheduledInstagramPostModel.roi_metrics.fetch_status == "success",
        ScheduledInstagramPostModel.roi_metrics.engagement_rate > 0,
        ScheduledInstagramPostModel.created_at >= since,
    ).sort(-ScheduledInstagramPostModel.created_at).limit(limit_per_collection).to_list()

    stories = await InstagramStoryModel.find(
        InstagramStoryModel.roi_metrics.fetch_status == "success",
        InstagramStoryModel.roi_metrics.engagement_rate > 0,
        InstagramStoryModel.created_at >= since,
    ).sort(-InstagramStoryModel.created_at).limit(limit_per_collection).to_list()

    items: list[_IGItem] = []

    for p in posts:
        items.append(
            _IGItem(
                kind="post",
                id=str(p.id),
                user_id=p.user_id,
                caption=p.caption or "",
                created_at=_utc(p.created_at),
                published_at=_utc(p.published_at),
                roi_engagement_percent=float(p.roi_metrics.engagement_rate or 0.0),
            )
        )

    for p in scheduled:
        # Scheduled posts do not have published_at; executed_at is the best proxy.
        items.append(
            _IGItem(
                kind="scheduled_post",
                id=str(p.id),
                user_id=p.user_id,
                caption=p.caption or "",
                created_at=_utc(p.created_at),
                published_at=_utc(getattr(p, "executed_at", None) or getattr(p, "scheduled_time", None)),
                roi_engagement_percent=float(p.roi_metrics.engagement_rate or 0.0),
            )
        )

    for s in stories:
        items.append(
            _IGItem(
                kind="story",
                id=str(s.id),
                user_id=s.user_id,
                caption="",  # stories often have no caption field in model
                created_at=_utc(s.created_at),
                published_at=_utc(s.published_at),
                roi_engagement_percent=float(s.roi_metrics.engagement_rate or 0.0),
            )
        )

    return items


async def _pick_caption_log_for_item(
    *,
    item: _IGItem,
    asset_type: AssetTypeEnum,
    time_window: timedelta,
    max_candidates: int,
) -> Optional[CaptionLogModel]:
    """
    Best-effort join:
      1) caption substring match (if we have the IG caption text)
      2) time proximity: closest created_at within time_window around pivot time
    """
    # Pivot time: prefer item.created_at (posting request time), else published_at.
    pivot = item.created_at or item.published_at
    if not pivot:
        return None

    start = pivot - time_window
    end = pivot + time_window

    # Query candidates scoped by user + type + unlabeled.
    candidates = await CaptionLogModel.find(
        CaptionLogModel.user_id == item.user_id,
        CaptionLogModel.asset_type == asset_type,
        CaptionLogModel.engagement_rate == None,  # noqa: E711
        CaptionLogModel.caption_text != None,     # noqa: E711
        CaptionLogModel.created_at >= start.replace(tzinfo=None),
        CaptionLogModel.created_at <= end.replace(tzinfo=None),
    ).sort(-CaptionLogModel.created_at).limit(max_candidates).to_list()

    if not candidates:
        return None

    # 1) caption substring match (handles appended hashtags in IG caption)
    if item.caption:
        for c in candidates:
            if _caption_in_post(c.caption_text or "", item.caption):
                return c

    # 2) time proximity fallback: choose nearest created_at
    pivot_naive = pivot.replace(tzinfo=None)
    best = min(
        candidates,
        key=lambda c: abs((c.created_at - pivot_naive).total_seconds()) if c.created_at else 10**12,
    )
    return best


async def backfill_caption_log_engagement_rates(
    *,
    lookback_days: int = 30,
    limit_per_collection: int = 200,
    time_window_hours: int = 48,
    max_candidates: int = 50,
) -> dict:
    """
    Backfill CaptionLogModel.engagement_rate using recent Instagram ROI metrics.

    Returns a small summary dict suitable for job logging.
    """
    time_window = timedelta(hours=max(1, time_window_hours))
    items = await _iter_recent_ig_items(
        lookback_days=lookback_days,
        limit_per_collection=limit_per_collection,
    )

    updated = 0
    skipped = 0
    errors = 0

    for item in items:
        try:
            if item.kind in ("post", "scheduled_post"):
                asset_type = AssetTypeEnum.POST
            elif item.kind == "story":
                asset_type = AssetTypeEnum.STORY
            else:
                skipped += 1
                continue

            # Convert percent (e.g., 3.4) → fraction (0.034)
            er_fraction = float(item.roi_engagement_percent) / 100.0
            if er_fraction <= 0:
                skipped += 1
                continue

            cap = await _pick_caption_log_for_item(
                item=item,
                asset_type=asset_type,
                time_window=time_window,
                max_candidates=max_candidates,
            )

            if not cap:
                skipped += 1
                continue

            # Write back engagement_rate (do not overwrite existing labels)
            cap.engagement_rate = round(er_fraction, 6)
            cap.updated_at = datetime.utcnow()
            await cap.save()
            updated += 1

        except Exception as exc:
            errors += 1
            logger.warning(
                "Caption ROI join failed for item kind=%s id=%s user=%s: %s",
                item.kind,
                item.id,
                item.user_id,
                exc,
            )

    summary = {
        "lookback_days": lookback_days,
        "limit_per_collection": limit_per_collection,
        "time_window_hours": time_window_hours,
        "items_considered": len(items),
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
    }
    logger.info("✅ Caption ROI join summary: %s", summary)
    return summary

