from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional


logger = logging.getLogger("raamp.obs")

def _truthy(v: Optional[str]) -> bool:
    return str(v or "").strip().lower() in ("1", "true", "yes", "y", "on")


def emit_event(
    event: str,
    *,
    trend_id: Optional[str] = None,
    user_id: Optional[str] = None,
    **fields: Any,
) -> None:
    """
    Emit a structured JSON log event (monitoring destination = logs).

    Standard fields included for traceability:
    - event
    - timestamp (UTC ISO)
    - trend_id
    - user_id
    """
    payload: Dict[str, Any] = {
        "event": event,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    if trend_id is not None:
        payload["trend_id"] = trend_id
    if user_id is not None:
        payload["user_id"] = user_id
    payload.update(fields)
    try:
        logger.info(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    except Exception:
        # Fall back to plain logging if serialization fails
        logger.info("event=%s trend_id=%s user_id=%s fields=%s", event, trend_id, user_id, fields)

    # Optional metrics sink: Sentry (if configured).
    # This keeps the default "logs-only" behavior, but enables production-grade visibility
    # without forcing a full metrics stack.
    try:
        import os

        if not _truthy(os.getenv("RAAMP_OBS_SENTRY_ENABLED")):
            return
        dsn = (os.getenv("SENTRY_DSN") or "").strip()
        if not dsn:
            return

        import sentry_sdk  # type: ignore

        # Init once, lazily.
        if not getattr(emit_event, "_sentry_inited", False):
            sentry_sdk.init(
                dsn=dsn,
                environment=(os.getenv("ENV") or os.getenv("RAAMP_ENV") or "development"),
                traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE") or "0.0"),
            )
            setattr(emit_event, "_sentry_inited", True)

        with sentry_sdk.push_scope() as scope:
            scope.set_extra("raamp_event", payload)
            scope.set_tag("event", str(event))
            if trend_id:
                scope.set_tag("trend_id", str(trend_id))
            sentry_sdk.capture_message(f"raamp_event:{event}", level="info")
    except Exception:
        # Never break the app due to observability plumbing.
        return

