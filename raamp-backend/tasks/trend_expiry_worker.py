"""
Trend expiry worker
===================
Keeps the Trend Arbitrage dashboards clean by expiring old spike detections.

Policy:
- a spike detection is considered expired after 72 hours

Notes:
- Expiry is a UI/ops concern; we do NOT delete historical data.
- This worker only updates `TrendDetectionModel.status` to "expired".
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from infrastructure.database.models.trend_detection_model import TrendDetectionModel

logger = logging.getLogger(__name__)


async def expire_old_trend_detections(*, ttl_hours: int = 72) -> int:
    """
    Mark detections as expired when outside the TTL.
    Returns number of documents updated (best-effort).
    """
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=int(ttl_hours or 72))

    query = {
        "$or": [
            # Preferred: expires_at already computed at insert time.
            {"expires_at": {"$lte": now}},
            # Backward compatibility for older docs without expires_at.
            {"expires_at": {"$exists": False}, "detected_at": {"$lte": cutoff}},
        ],
        "status": {"$ne": "expired"},
    }

    try:
        result = await TrendDetectionModel.find(query).update({"$set": {"status": "expired"}})
        updated = int(getattr(result, "modified_count", 0) or 0)
        if updated:
            logger.info("Expired %d trend detections (ttl_hours=%d)", updated, int(ttl_hours or 72))
        return updated
    except Exception as e:
        logger.warning("Failed expiring trend detections (non-fatal): %s", str(e))
        return 0

