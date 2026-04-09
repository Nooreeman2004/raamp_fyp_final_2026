"""
Optional migration/backfill script for trends collections.

This script is SAFE to run multiple times (idempotent).

What it does:
- Backfill missing provider/fallback fields on `trend_signals`
- Backfill missing provenance flags on `trend_signals` and `trend_detections`

Run:
  python scripts/migrate_trends_fields.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient

# Ensure imports work when running as a script:
# `python scripts/migrate_trends_fields.py` from repo root.
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from infrastructure.database.database import MONGODB_URL, DATABASE_NAME


async def main() -> None:
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]

    now = datetime.utcnow()

    def missing_or_null(field: str) -> dict:
        # Mongo treats {field: None} as matching both null and missing.
        return {"$or": [{field: {"$exists": False}}, {field: None}]}

    # trend_signals backfill
    signals = db["trend_signals"]
    sig_updates = 0
    res = await signals.update_many(
        missing_or_null("is_real_social"),
        {"$set": {"is_real_social": False, "updated_at": now}},
    )
    sig_updates += int(res.modified_count or 0)
    res = await signals.update_many(
        missing_or_null("is_real_saturation"),
        {"$set": {"is_real_saturation": False, "updated_at": now}},
    )
    sig_updates += int(res.modified_count or 0)
    res = await signals.update_many(
        missing_or_null("is_real_events"),
        {"$set": {"is_real_events": False, "updated_at": now}},
    )
    sig_updates += int(res.modified_count or 0)

    # Provider fields may be absent on older docs; keep them nullable.
    res = await signals.update_many(
        missing_or_null("provider"),
        {"$set": {"provider": None, "updated_at": now}},
    )
    sig_updates += int(res.modified_count or 0)
    res = await signals.update_many(
        missing_or_null("fallback_from"),
        {"$set": {"fallback_from": None, "updated_at": now}},
    )
    sig_updates += int(res.modified_count or 0)
    res = await signals.update_many(
        missing_or_null("geo_relaxed"),
        {"$set": {"geo_relaxed": False, "updated_at": now}},
    )
    sig_updates += int(res.modified_count or 0)

    # trend_detections backfill
    detections = db["trend_detections"]
    det_updates = 0
    res = await detections.update_many(
        missing_or_null("is_real_social"),
        {"$set": {"is_real_social": False}},
    )
    det_updates += int(res.modified_count or 0)
    res = await detections.update_many(
        missing_or_null("is_real_saturation"),
        {"$set": {"is_real_saturation": False}},
    )
    det_updates += int(res.modified_count or 0)
    res = await detections.update_many(
        missing_or_null("is_real_events"),
        {"$set": {"is_real_events": False}},
    )
    det_updates += int(res.modified_count or 0)

    print("[migrate_trends_fields] done")
    print(f"  trend_signals modified fields (sum): {sig_updates}")
    print(f"  trend_detections modified fields (sum): {det_updates}")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())

