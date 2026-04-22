"""
Migration: enforce unique external_ref for social escalation tickets.

Why:
- We want exactly one escalation ticket per Meta comment.
- `external_ref` is our dedupe key: "meta_comment:{platform}:{comment_id}".

Safety:
- Default mode is DRY RUN (no writes).
- With --apply, the script will:
  - detect duplicates
  - (optionally) delete duplicate rows (keeping the oldest) if --dedupe is provided
  - drop the existing external_ref index
  - recreate it as UNIQUE

Run:
  python scripts/migrate_social_escalations_external_ref_unique.py
  python scripts/migrate_social_escalations_external_ref_unique.py --apply --dedupe
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from infrastructure.database.database import MONGODB_URL, DATABASE_NAME  # noqa: E402


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Actually perform writes (drop/create index).")
    parser.add_argument(
        "--dedupe",
        action="store_true",
        help="If duplicates exist, delete duplicates (keep oldest) before creating unique index.",
    )
    args = parser.parse_args()

    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    col = db["social_escalation_tickets"]

    print(f"[INFO] DB={DATABASE_NAME} collection=social_escalation_tickets")

    # 1) Find duplicates by external_ref
    pipeline = [
        {"$group": {"_id": "$external_ref", "count": {"$sum": 1}, "ids": {"$push": "$_id"}}},
        {"$match": {"count": {"$gt": 1}}},
        {"$sort": {"count": -1}},
    ]
    dupes = await col.aggregate(pipeline).to_list(length=None)
    if not dupes:
        print("[OK] No duplicate external_ref values found.")
    else:
        total_dupe_groups = len(dupes)
        total_extra = sum(int(d.get("count", 0)) - 1 for d in dupes)
        print(f"[WARN] Found {total_dupe_groups} duplicate external_ref groups, {total_extra} extra docs.")
        for d in dupes[:10]:
            print(f"  - external_ref={d.get('_id')} count={d.get('count')}")
        if total_dupe_groups > 10:
            print("  ... (truncated)")

        if args.apply and args.dedupe:
            print("[INFO] Dedupe enabled: deleting duplicates (keeping oldest by created_at).")
            deleted = 0
            now = datetime.utcnow()
            for g in dupes:
                ref = g.get("_id")
                if not ref:
                    continue
                docs = await col.find({"external_ref": ref}).sort([("created_at", 1), ("_id", 1)]).to_list(length=None)
                if len(docs) <= 1:
                    continue
                keep = docs[0]
                drop_ids = [d["_id"] for d in docs[1:] if "_id" in d]
                if drop_ids:
                    res = await col.delete_many({"_id": {"$in": drop_ids}})
                    deleted += int(res.deleted_count or 0)
                # Touch kept doc updated_at so we know it was migrated (optional)
                try:
                    await col.update_one({"_id": keep["_id"]}, {"$set": {"updated_at": now}})
                except Exception:
                    pass
            print(f"[OK] Deleted {deleted} duplicate docs.")
        elif args.apply and not args.dedupe:
            print("[ERROR] Duplicates exist. Re-run with --apply --dedupe (or dedupe manually) before making index unique.")
            return
        else:
            print("[INFO] DRY RUN: not modifying duplicates.")
            return

    # 2) Drop + recreate index as UNIQUE
    if not args.apply:
        print("[INFO] DRY RUN: would drop index 'external_ref_1' and create UNIQUE index.")
        return

    # Best-effort: drop by known default name; if missing, ignore.
    try:
        await col.drop_index("external_ref_1")
        print("[OK] Dropped index external_ref_1")
    except Exception as e:
        print(f"[WARN] Could not drop index external_ref_1 (may not exist): {str(e)[:200]}")

    try:
        await col.create_index([("external_ref", 1)], unique=True, name="external_ref_1")
        print("[OK] Created UNIQUE index external_ref_1 on external_ref")
    except Exception as e:
        print(f"[ERROR] Failed to create UNIQUE index: {str(e)[:400]}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

