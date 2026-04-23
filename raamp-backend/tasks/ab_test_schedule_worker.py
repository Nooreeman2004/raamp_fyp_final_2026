"""
A/B test schedule worker

Emits in-app notifications when tests go live and when monitoring windows end.
"""

import logging
from datetime import datetime, timedelta

from application.services.notification_service import NotificationService
from infrastructure.database.database import get_database
from infrastructure.database.models.notification_model import NotificationType

logger = logging.getLogger(__name__)


async def process_ab_test_schedule_transitions() -> None:
    """Check schedule transitions and notify users once per milestone."""
    db = get_database()
    schedules = db["ab_test_schedules"]
    notifier = NotificationService()
    now = datetime.utcnow()

    cursor = schedules.find(
        {
            "$or": [
                {"notified_live_at": {"$exists": False}},
                {"notified_completed_at": {"$exists": False}},
            ]
        },
        {
            "schedule_id": 1,
            "user_id": 1,
            "platform": 1,
            "status": 1,
            "variant_a_post_time": 1,
            "variant_b_post_time": 1,
            "post_time": 1,
            "test_duration_hours": 1,
            "notified_live_at": 1,
            "notified_completed_at": 1,
        },
    ).limit(300)

    docs = await cursor.to_list(length=300)
    for schedule in docs:
        schedule_id = schedule.get("schedule_id")
        user_id = schedule.get("user_id")
        if not schedule_id or not user_id:
            continue

        post_a = schedule.get("variant_a_post_time") or schedule.get("post_time")
        post_b = schedule.get("variant_b_post_time") or schedule.get("post_time")
        if not post_a or not post_b:
            continue

        duration_hours = int(schedule.get("test_duration_hours", 48) or 48)
        monitoring_start = min(post_a, post_b)
        monitoring_end = max(post_a, post_b) + timedelta(hours=duration_hours)

        if now < monitoring_start:
            computed_status = "scheduled"
        elif now < monitoring_end:
            computed_status = "active"
        else:
            computed_status = "completed"

        updates = {}
        if schedule.get("status") != computed_status:
            updates["status"] = computed_status

        if computed_status == "active" and not schedule.get("notified_live_at"):
            await notifier.create_and_send(
                user_id=user_id,
                type=NotificationType.CAMPAIGN,
                title="A/B Test Is Live",
                message="Your A/B test variants are now live. Open Monitor Test to track progress or promote a top variant.",
                related_entity_id=schedule_id,
                metadata={
                    "sub_type": "ab_test_live",
                    "post_id": schedule_id,
                    "platform": schedule.get("platform"),
                },
            )
            updates["notified_live_at"] = now

        if computed_status == "completed" and not schedule.get("notified_completed_at"):
            await notifier.create_and_send(
                user_id=user_id,
                type=NotificationType.CAMPAIGN,
                title="A/B Monitoring Completed",
                message="Monitoring has ended. Enter final metrics to pick a winner, or promote a variant now.",
                related_entity_id=schedule_id,
                metadata={
                    "sub_type": "ab_test_completed",
                    "post_id": schedule_id,
                    "platform": schedule.get("platform"),
                },
            )
            updates["notified_completed_at"] = now

        if updates:
            await schedules.update_one({"schedule_id": schedule_id}, {"$set": updates})

    if docs:
        logger.debug("AB test schedule worker checked %s schedules", len(docs))
