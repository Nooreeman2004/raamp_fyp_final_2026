"""
Check when posts were published vs when insights became available
"""

import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta

_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND_ROOT = os.path.dirname(_HERE)
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)


async def main() -> int:
    from infrastructure.database.database import connect_to_mongo, init_db, close_mongo_connection
    from infrastructure.database.models.instagram_post_model import InstagramPostModel
    from beanie.operators import NE

    await connect_to_mongo()
    await init_db()
    try:
        # Get published posts
        posts = await InstagramPostModel.find(
            NE(InstagramPostModel.instagram_post_id, None),
            InstagramPostModel.status == "published"
        ).limit(10).to_list()
        
        now = datetime.now(timezone.utc)
        
        print("=== Published Posts (with instagram_post_id) ===\n")
        for p in posts:
            if p.published_at:
                # Handle both offset-aware and offset-naive datetimes
                pub_at = p.published_at
                if pub_at.tzinfo is None:
                    pub_at = pub_at.replace(tzinfo=timezone.utc)
                
                age = now - pub_at
                age_hours = age.total_seconds() / 3600
                print(f"Post {p.id}")
                print(f"  Published: {p.published_at}")
                print(f"  Age: {age_hours:.1f} hours ({age.days} days)")
                print(f"  ROI fetch_status: {p.roi_metrics.fetch_status}")
                print(f"  ROI reach: {p.roi_metrics.reach}")
                print()

        return 0
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
