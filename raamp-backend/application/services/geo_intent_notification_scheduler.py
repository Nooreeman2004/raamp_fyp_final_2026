"""
Geo-Intent Notification Scheduler

Implements the only daily Geo-Intent notification:
  - Best time to post — daily

This module is designed to be invoked by APScheduler (see main.py).
It uses the existing NotificationService + job health monitor.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from application.services.job_health_monitor_service import job_health_monitor
from application.services.notification_service import NotificationService
from application.services.geo_intent_service import GeoIntentService
from infrastructure.database.models.notification_model import NotificationType
from infrastructure.database.models.notification_model import NotificationModel
from infrastructure.database.models.user_model import UserModel
from infrastructure.repositories.business_repository import BusinessRepository

logger = logging.getLogger(__name__)


def _resolve_geo_business_id_from_business(business, user_id_fallback: str) -> str:
    """
    Mirror the geo-id resolution rules used in frontend/router:
    prefer Google place id, else stable onboarding coordinate key, else user-scoped key.
    """
    if business:
        pid = (getattr(business, "google_place_id", None) or "").strip()
        if pid:
            return pid
        lat = getattr(business, "latitude", None)
        lng = getattr(business, "longitude", None)
        if lat is not None and lng is not None:
            return f"onboarding_{float(lat):.6f}_{float(lng):.6f}"
    return f"user_{user_id_fallback}"


def _format_best_hour(best_hours: List[Dict]) -> Optional[str]:
    """
    best_hours is a list like: [{"hour": 17, "avg_score": 78.2}, ...]
    We only need the top hour window.
    """
    if not best_hours:
        return None
    top = best_hours[0]
    h = int(top.get("hour"))
    end = (h + 1) % 24
    # Use simple 12h formatting like "5–6pm"
    def fmt(hr: int) -> str:
        suffix = "am" if hr < 12 else "pm"
        hr12 = hr % 12
        if hr12 == 0:
            hr12 = 12
        return f"{hr12}{suffix}"
    return f"{fmt(h)}–{fmt(end)}"


async def send_daily_best_posting_time_notifications() -> Dict:
    """
    Daily, quiet, genuinely useful.
    Sends at most 1 notification per day per user per business.
    """
    execution_id = await job_health_monitor.start_job_execution("geo_intent_daily_best_time")
    if execution_id is None:
        logger.warning("Skipping duplicate execution of geo_intent_daily_best_time")
        return {"status": "skipped", "reason": "duplicate_execution"}

    notif_service = NotificationService()
    geo_service = GeoIntentService()
    biz_repo = BusinessRepository()

    now = datetime.utcnow()
    day_key = now.strftime("%Y-%m-%d")

    sent = 0
    skipped = 0
    errors = 0

    try:
        users = await UserModel.find_all().to_list()
        for user in users:
            try:
                user_email = getattr(user, "email", None)
                if not user_email:
                    skipped += 1
                    continue

                business = await biz_repo.get_by_user_id(str(user.id))
                business_id = _resolve_geo_business_id_from_business(business, str(user.id))

                # Fetch best posting time (based on history). If no history, skip quietly.
                logs = await geo_service.get_campaign_history(business_id=business_id, limit=500)
                if not logs:
                    skipped += 1
                    continue

                # Reuse router logic: compute hourly averages and pick top
                hour_scores: Dict[int, List[int]] = {h: [] for h in range(24)}
                found_dates = set()
                for log in logs:
                    ts = log.get("timestamp")
                    if isinstance(ts, datetime):
                        found_dates.add(ts.date())
                        hour_scores[ts.hour].append(int(log.get("final_score") or 0))

                avg_hours = []
                for h, scores in hour_scores.items():
                    if scores:
                        avg_hours.append({"hour": h, "avg_score": round(sum(scores) / len(scores), 1)})
                avg_hours.sort(key=lambda x: x["avg_score"], reverse=True)

                best_window = _format_best_hour(avg_hours[:2])
                if not best_window:
                    skipped += 1
                    continue

                dedupe_key = f"geo_intent_best_time_daily:{business_id}:{day_key}"
                already = await NotificationModel.find(
                    NotificationModel.user_id == user_email,
                    NotificationModel.related_entity_id == dedupe_key,
                ).count()
                if already:
                    skipped += 1
                    continue

                # Message: keep it quiet + useful. Area naming may be improved later.
                title = "Best time to post — today"
                message = f"Peak intent window starting in your area. Today's best hour: {best_window}."

                await notif_service.create_and_send(
                    user_id=user_email,
                    type=NotificationType.REMINDER,
                    title=title,
                    message=message,
                    related_entity_id=dedupe_key,
                    metadata={
                        "sub_type": "geo_intent_best_time_daily",
                        "business_id": business_id,
                        "date": day_key,
                        "best_window": best_window,
                        "based_on_days": len(found_dates),
                    },
                    priority=1,
                )
                sent += 1
            except Exception as exc:
                errors += 1
                logger.warning("Geo daily best-time notif failed for user=%s: %s", getattr(user, "email", None), exc)

        result = {"status": "ok", "sent": sent, "skipped": skipped, "errors": errors, "date": day_key}
        await job_health_monitor.complete_job_execution(execution_id=execution_id, status="COMPLETED", result=result)
        return result
    except Exception as exc:
        await job_health_monitor.complete_job_execution(execution_id=execution_id, status="FAILED", error=str(exc))
        logger.exception("Geo daily best-time job failed: %s", exc)
        return {"status": "error", "error": str(exc)}

