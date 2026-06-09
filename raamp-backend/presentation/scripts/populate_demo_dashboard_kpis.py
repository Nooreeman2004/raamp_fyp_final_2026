"""
Populate dashboard KPI data for a user (default: demo account).

Does the following (best-effort, skips on error with a message):
  1. Geo-intent: one heat-score run + persist campaign_logs / heat_scores (needs API keys for Places/Trends/Weather).
  2. Trend watchlist: ensures at least one active watchlist row (drives "Active Trends" count on the home KPI strip).
  3. Instagram ROI: calls refresh_post_roi for each feed post with an instagram_post_id (needs valid Meta tokens).

Usage (from raamp-backend):
  python scripts/populate_demo_dashboard_kpis.py
  python scripts/populate_demo_dashboard_kpis.py user@example.com
  python scripts/populate_demo_dashboard_kpis.py --with-trend-pipeline

For a full trend *detection* pipeline (heavier), use instead:
  python tests/diagnostics/run_manual_trend_scan.py abdullah@gmail.com
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND_ROOT = os.path.dirname(_HERE)
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)


class ImmediateBackgroundTasks:
    """Starlette-compatible: run tasks immediately (for scripts, no HTTP response)."""

    def __init__(self) -> None:
        self._tasks: list[tuple] = []

    def add_task(self, func, *args, **kwargs) -> None:
        self._tasks.append((func, args, kwargs))

    async def flush(self) -> None:
        for fn, args, kwargs in self._tasks:
            await fn(*args, **kwargs)


async def _run_geo_scan(email: str, logger: logging.Logger) -> bool:
    from infrastructure.database.database import connect_to_mongo, init_db, close_mongo_connection
    from infrastructure.repositories.business_repository import BusinessRepository
    from infrastructure.database.models.user_model import UserModel
    from application.services.geo_intent_service import GeoIntentService

    await connect_to_mongo()
    await init_db()
    try:
        user = await UserModel.find_one(UserModel.email == email)
        if not user:
            logger.error("User not found: %s", email)
            return False

        biz = await BusinessRepository().get_by_user_id(str(user.id))
        if not biz:
            logger.error("No business for user %s", email)
            return False

        lat = biz.latitude
        lng = biz.longitude
        if lat is None or lng is None:
            logger.error(
                "Business missing latitude/longitude — set hyperlocal location first (see tests/check_demo_user_geo.py)."
            )
            return False

        bid = str(biz.id)
        radius = int(biz.targeting_radius_m or 5000)
        kw = list(biz.tracking_keywords or [])
        if not kw:
            if biz.business_type:
                kw = [biz.business_type, "food"]
            else:
                kw = ["restaurant", "food"]
        kw = kw[:5]
        is_indoor = bool(biz.is_indoor) if biz.is_indoor is not None else True

        svc = GeoIntentService()
        bg = ImmediateBackgroundTasks()
        await svc.compute(
            business_id=bid,
            keywords=kw,
            latitude=float(lat),
            longitude=float(lng),
            radius=radius,
            is_indoor=is_indoor,
            background_tasks=bg,
            user_id=email,
            skip_credits=True,
        )
        await bg.flush()
        logger.info("Geo-intent scan persisted for business_id=%s keywords=%s", bid, kw)
        return True
    finally:
        await close_mongo_connection()


async def _ensure_watchlist(email: str, logger: logging.Logger) -> bool:
    from infrastructure.database.database import connect_to_mongo, init_db, close_mongo_connection
    from infrastructure.database.models.trend_watchlist_model import TrendWatchlistModel
    from infrastructure.repositories.business_repository import BusinessRepository
    from infrastructure.database.models.user_model import UserModel

    await connect_to_mongo()
    await init_db()
    try:
        n = await TrendWatchlistModel.find(
            TrendWatchlistModel.user_email == email,
            TrendWatchlistModel.is_active == True,  # noqa: E712
        ).count()
        if n > 0:
            logger.info("Watchlist already has %d active item(s).", n)
            return True

        user = await UserModel.find_one(UserModel.email == email)
        biz = await BusinessRepository().get_by_user_id(str(user.id)) if user else None
        keyword = (biz.specialties[0] if biz and biz.specialties else None) or (
            biz.business_type if biz and biz.business_type else "coffee"
        )
        loc = (biz.country if biz and biz.country else None) or "US"
        niche = (biz.business_type if biz and biz.business_type else "food")

        item = TrendWatchlistModel(
            user_email=email,
            keyword=str(keyword)[:80],
            niche=str(niche)[:80],
            location=str(loc)[:80],
            last_arbitrage_score=50.0,
            last_profit_score=60.0,
        )
        await item.insert()
        logger.info("Added watchlist keyword=%r for %s", keyword, email)
        return True
    finally:
        await close_mongo_connection()


async def _refresh_instagram_roi(email: str, logger: logging.Logger) -> None:
    from infrastructure.database.database import connect_to_mongo, init_db, close_mongo_connection
    from infrastructure.database.models.instagram_post_model import InstagramPostModel
    from application.services.instagram_roi_service import refresh_post_roi

    await connect_to_mongo()
    await init_db()
    try:
        posts = await InstagramPostModel.find(
            InstagramPostModel.user_id == email,
            InstagramPostModel.instagram_post_id != None,  # noqa: E711
        ).sort(-InstagramPostModel.created_at).limit(25).to_list()

        if not posts:
            logger.warning("No Instagram posts with instagram_post_id for %s", email)
            return

        ok = pend = fail = 0
        for p in posts:
            m = await refresh_post_roi(str(p.id))
            st = getattr(m, "fetch_status", None) if m else None
            if st == "success":
                ok += 1
            elif st == "pending":
                pend += 1
            else:
                fail += 1
        logger.info("ROI refresh: success=%s pending=%s failed/missing=%s (posts tried=%s)", ok, pend, fail, len(posts))
    finally:
        await close_mongo_connection()


async def _run_trend_pipeline(email: str, logger: logging.Logger) -> bool:
    from infrastructure.database.database import connect_to_mongo, init_db, close_mongo_connection
    from infrastructure.database.models.user_model import UserModel
    from infrastructure.database.models.trend_signal_model import TrendSignalModel
    from application.services.trend_detection_service import TrendDetectionService

    await connect_to_mongo()
    await init_db()
    try:
        user = await UserModel.find_one(UserModel.email == email)
        if not user:
            logger.error("User not found: %s", email)
            return False
        svc = TrendDetectionService()
        sig = await svc.initialize_detection_signal(user, None, "all")
        await svc.execute_detection_pipeline(str(sig.id), "90d")
        persisted = await TrendSignalModel.get(sig.id)
        logger.info(
            "Trend pipeline finished: fetch_status=%s",
            getattr(persisted, "fetch_status", None),
        )
        return True
    finally:
        await close_mongo_connection()


async def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logger = logging.getLogger("populate_demo_dashboard_kpis")

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("email", nargs="?", default="abdullah@gmail.com", help="User email")
    p.add_argument("--skip-geo", action="store_true", help="Skip geo-intent scan")
    p.add_argument("--skip-watchlist", action="store_true", help="Skip watchlist seed")
    p.add_argument("--skip-roi", action="store_true", help="Skip Instagram ROI refresh")
    p.add_argument(
        "--with-trend-pipeline",
        action="store_true",
        help="Run full trend detection pipeline (slow; watchlist alone updates Active Trends count)",
    )
    args = p.parse_args()
    email = (args.email or "").strip()
    if not email:
        logger.error("Email required")
        return 2

    if not args.skip_geo:
        await _run_geo_scan(email, logger)
    if not args.skip_watchlist:
        await _ensure_watchlist(email, logger)
    if args.with_trend_pipeline:
        await _run_trend_pipeline(email, logger)
    if not args.skip_roi:
        await _refresh_instagram_roi(email, logger)

    print(
        "\nDone. Refresh the dashboard. "
        "If ROI stays pending, Meta may not have insights yet — retry later or check tokens."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
