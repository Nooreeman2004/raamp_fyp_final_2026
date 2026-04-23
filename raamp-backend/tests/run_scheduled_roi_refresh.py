"""
Run the scheduled ROI refresh manually to fetch metrics for all pending posts
"""

import asyncio
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND_ROOT = os.path.dirname(_HERE)
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)


async def main() -> int:
    from infrastructure.database.database import connect_to_mongo, init_db, close_mongo_connection
    from application.services.instagram_roi_service import scheduled_roi_refresh

    await connect_to_mongo()
    await init_db()
    try:
        print("=== Running scheduled ROI refresh ===\n")
        await scheduled_roi_refresh()
        print("\n✓ Scheduled ROI refresh completed")
        return 0
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
