"""
Trend Retry Worker (APScheduler driven)
======================================
Processes persistent retry jobs for trend signals.

Design:
- APScheduler calls `process_due_trend_retries()` periodically.
- Jobs are stored in MongoDB to survive restarts.
- Concurrency is limited by claiming jobs (status=running) before execution.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

from infrastructure.database.models.trend_retry_job_model import (
    TrendRetryJobModel,
    TrendRetryJobStatus,
)
from application.services.trend_detection_service import TrendDetectionService
from infrastructure.database.models.trend_signal_model import TrendSignalModel
from infrastructure.utils.obs import emit_event

logger = logging.getLogger(__name__)


def _next_backoff(attempt: int) -> timedelta:
    """
    Exponential-ish backoff: 2m, 5m, 15m (capped).
    attempt is 1-based for scheduling purposes.
    """
    if attempt <= 1:
        return timedelta(minutes=2)
    if attempt == 2:
        return timedelta(minutes=5)
    return timedelta(minutes=15)


async def enqueue_trend_retry(
    *,
    trend_id: str,
    user_email: str,
    reason: str,
    max_attempts: int = 3,
    delay: Optional[timedelta] = None,
) -> TrendRetryJobModel:
    now = datetime.utcnow()
    run_at = now + (delay or timedelta(minutes=2))
    job = TrendRetryJobModel(
        trend_id=trend_id,
        user_email=user_email,
        attempt=0,
        max_attempts=max_attempts,
        run_at=run_at,
        status=TrendRetryJobStatus.PENDING,
        last_error=reason[:500] if reason else None,
        last_run_at=None,
        updated_at=now,
    )
    await job.insert()
    logger.info(
        "Queued trend retry job: trend_id=%s user=%s run_at=%s max_attempts=%d reason=%s",
        trend_id,
        user_email,
        run_at.isoformat(),
        max_attempts,
        reason,
    )
    return job


async def process_due_trend_retries(limit: int = 5) -> dict:
    """
    Process up to `limit` due retry jobs.
    Returns a summary dict for logging/inspection.
    """
    now = datetime.utcnow()
    processed = 0
    succeeded = 0
    failed = 0
    rescheduled = 0

    # Fetch due pending jobs
    due_jobs = (
        await TrendRetryJobModel.find(
            TrendRetryJobModel.status == TrendRetryJobStatus.PENDING,
            TrendRetryJobModel.run_at <= now,
        )
        .sort(TrendRetryJobModel.run_at)
        .limit(limit)
        .to_list()
    )

    if not due_jobs:
        emit_event(
            "trends.retry_worker.run",
            processed=0,
            succeeded=0,
            failed=0,
            rescheduled=0,
            limit=limit,
        )
        return {"processed": 0, "succeeded": 0, "failed": 0, "rescheduled": 0}

    detection_service = TrendDetectionService()

    for job in due_jobs:
        processed += 1
        try:
            # Safety net dedup: if another job for the same trend_id is already running, skip this one.
            other_running = await TrendRetryJobModel.find_one(
                TrendRetryJobModel.trend_id == job.trend_id,
                TrendRetryJobModel.status == TrendRetryJobStatus.RUNNING,
                TrendRetryJobModel.id != job.id,
            )
            if other_running:
                logger.info(
                    "Skipping retry job %s for trend_id=%s because another job is already running (%s).",
                    str(job.id),
                    job.trend_id,
                    str(other_running.id),
                )
                # Leave it pending, but push it slightly into the future to avoid tight loops.
                job.run_at = datetime.utcnow() + timedelta(minutes=1)
                job.updated_at = datetime.utcnow()
                await job.save()
                continue

            # Claim job (best-effort). If another worker claimed it, skip.
            job.status = TrendRetryJobStatus.RUNNING
            job.last_run_at = now
            job.updated_at = now
            await job.save()

            logger.info(
                "Running trend retry: id=%s trend_id=%s attempt=%d/%d",
                str(job.id),
                job.trend_id,
                job.attempt + 1,
                job.max_attempts,
            )

            await detection_service.execute_detection_pipeline(job.trend_id)

            job.status = TrendRetryJobStatus.SUCCEEDED
            job.updated_at = datetime.utcnow()
            await job.save()
            succeeded += 1
            emit_event(
                "trends.retry.succeeded",
                trend_id=str(job.trend_id),
                user_id=str(job.user_email),
                retry_job_id=str(job.id),
                attempt=int(job.attempt + 1),
                max_attempts=int(job.max_attempts),
            )

        except Exception as exc:
            err = str(exc)
            job.last_error = err[:500]
            job.updated_at = datetime.utcnow()
            emit_event(
                "trends.retry.failed",
                trend_id=str(job.trend_id),
                user_id=str(job.user_email),
                retry_job_id=str(job.id),
                attempt=int(job.attempt + 1),
                max_attempts=int(job.max_attempts),
                error=str(job.last_error or ""),
            )

            # Determine if we should retry again
            next_attempt = job.attempt + 1
            if next_attempt >= job.max_attempts:
                job.status = TrendRetryJobStatus.FAILED
                await job.save()
                failed += 1

                # Mark the TrendSignal as failed if it still exists
                try:
                    signal = await TrendSignalModel.get(job.trend_id)
                    if signal:
                        signal.fetch_status = "failed"
                        signal.error_message = f"Retry exhausted: {job.last_error}"
                        signal.progress_step = "Retry exhausted."
                        signal.updated_at = datetime.utcnow()
                        await signal.save()
                except Exception:
                    logger.exception("Failed updating TrendSignal after retry exhaustion: %s", job.trend_id)

                logger.error(
                    "Trend retry exhausted: trend_id=%s attempts=%d error=%s",
                    job.trend_id,
                    job.max_attempts,
                    job.last_error,
                )
                emit_event(
                    "trends.retry.exhausted",
                    trend_id=str(job.trend_id),
                    attempts=int(job.max_attempts),
                    final_error=str(job.last_error or ""),
                )
            else:
                # Reschedule
                job.attempt = next_attempt
                job.status = TrendRetryJobStatus.PENDING
                job.run_at = datetime.utcnow() + _next_backoff(next_attempt)
                await job.save()
                rescheduled += 1

                logger.warning(
                    "Trend retry rescheduled: trend_id=%s next_attempt=%d run_at=%s error=%s",
                    job.trend_id,
                    job.attempt + 1,
                    job.run_at.isoformat(),
                    job.last_error,
                )

    summary = {
        "processed": processed,
        "succeeded": succeeded,
        "failed": failed,
        "rescheduled": rescheduled,
    }
    emit_event("trends.retry_worker.run", **summary, limit=limit)
    return summary


