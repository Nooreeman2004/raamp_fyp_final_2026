"""
Check ML training labels in MongoDB.

Runs the same query logic you'd do in mongosh:
  db.caption_logs.findOne({ engagement_rate: { $ne: null } })
  db.caption_logs.countDocuments({ engagement_rate: { $ne: null } })

But using the app's existing Beanie models + Mongo connection.
"""

import asyncio
import os
import sys
from datetime import datetime

# Allow running from repo root by adding backend root to sys.path
_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND_ROOT = os.path.dirname(_HERE)  # .../raamp-backend
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)


async def main() -> int:
    from infrastructure.database.database import connect_to_mongo, init_db, close_mongo_connection
    from infrastructure.database.models.caption_log_model import CaptionLogModel

    await connect_to_mongo()
    await init_db()

    try:
        labeled_docs = await CaptionLogModel.find(
            CaptionLogModel.engagement_rate != None  # noqa: E711
        ).to_list()
        labeled_count = len(labeled_docs)
        labeled_core = len(
            [
                d
                for d in labeled_docs
                if getattr(d, "asset_type", None)
                and str(d.asset_type.value) in ("post", "story", "reel")
            ]
        )

        one = await CaptionLogModel.find_one(
            CaptionLogModel.engagement_rate != None  # noqa: E711
        )

        print("\n=== caption_logs label check ===")
        print(f"labeled_count: {labeled_count}")
        print(f"labeled_post_story_reel: {labeled_core}")
        print(f"checked_at:    {datetime.utcnow().isoformat()}Z")

        if not one:
            print("\nfindOne: null (no labeled caption_logs found)")
            return 0

        # Print a compact view of the document so we can validate fields are present.
        doc = one.model_dump() if hasattr(one, "model_dump") else dict(one)
        preview = {
            "caption_id": doc.get("caption_id"),
            "user_id": doc.get("user_id"),
            "asset_type": doc.get("asset_type"),
            "tone": doc.get("tone"),
            "hashtags_count": len(doc.get("hashtags") or []),
            "caption_text_preview": (doc.get("caption_text") or "")[:180],
            "engagement_rate": doc.get("engagement_rate"),
            "created_at": doc.get("created_at"),
            "updated_at": doc.get("updated_at"),
        }
        print("\nfindOne preview:")
        for k, v in preview.items():
            # Windows consoles can choke on emoji/unicode; print safely.
            s = f"- {k}: {v}"
            try:
                print(s)
            except UnicodeEncodeError:
                # Force ASCII-safe output for legacy Windows consoles
                print(s.encode("ascii", errors="backslashreplace").decode("ascii"))

        return 0
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

