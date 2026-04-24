"""
Background Task Utilities
==========================
Safe wrappers for fire-and-forget async tasks with error tracking.

PROBLEM: asyncio.create_task() silently drops exceptions, causing:
- Lost activity logs
- Failed email notifications
- Silent data corruption

SOLUTION: Wrap all background tasks with error logging and optional retry logic.
"""

import asyncio
import logging
from typing import Callable, Any, Coroutine
from functools import wraps

logger = logging.getLogger(__name__)


async def _safe_task_wrapper(
    task_coro: Coroutine,
    task_name: str,
    max_retries: int = 0,
    critical: bool = False
):
    """
    Execute a task with error handling and retry logic.
    
    Args:
        task_coro: The coroutine to execute
        task_name: Human-readable task name for logging
        max_retries: Number of retry attempts (0 = no retries)
        critical: If True, log as ERROR; if False, log as WARNING
    """
    attempt = 0
    last_error = None
    
    while attempt <= max_retries:
        try:
            await task_coro
            if attempt > 0:
                logger.info(f"✅ Background task '{task_name}' succeeded on attempt {attempt + 1}")
            return
        except Exception as e:
            last_error = e
            attempt += 1
            
            if attempt <= max_retries:
                logger.warning(
                    f"⚠️  Background task '{task_name}' failed (attempt {attempt}/{max_retries + 1}): {e}. Retrying..."
                )
                await asyncio.sleep(min(2 ** attempt, 10))  # Exponential backoff, max 10s
            else:
                log_fn = logger.error if critical else logger.warning
                log_fn(
                    f"{'❌' if critical else '⚠️ '} Background task '{task_name}' failed after {max_retries + 1} attempts: {e}",
                    exc_info=True
                )
    
    # If critical and all retries failed, consider adding to error tracking service (Sentry, etc.)
    if critical and last_error:
        # TODO: Send to error tracking service
        pass


def create_background_task(
    coro: Coroutine,
    task_name: str,
    max_retries: int = 0,
    critical: bool = False
) -> asyncio.Task:
    """
    Create a background task with automatic error handling.
    
    Use this instead of asyncio.create_task() for fire-and-forget operations.
    
    Args:
        coro: The coroutine to run in the background
        task_name: Human-readable name for logging (e.g., "log_activity", "send_email")
        max_retries: Number of retry attempts on failure (default: 0)
        critical: Whether failure should be logged as ERROR (default: False = WARNING)
    
    Returns:
        asyncio.Task: The background task (can be safely ignored)
    
    Examples:
        # Non-critical operation (log as warning if fails)
        create_background_task(
            log_activity(business_id="123", event_type="post_published"),
            task_name="log_post_activity"
        )
        
        # Critical operation with retries
        create_background_task(
            send_notification_email(user_email="user@example.com"),
            task_name="send_verification_email",
            max_retries=3,
            critical=True
        )
    """
    wrapped_coro = _safe_task_wrapper(coro, task_name, max_retries, critical)
    return asyncio.create_task(wrapped_coro)


def background_task(task_name: str = None, max_retries: int = 0, critical: bool = False):
    """
    Decorator to convert a function into a safe background task.
    
    Usage:
        @background_task(task_name="send_welcome_email", max_retries=3, critical=True)
        async def send_welcome_email(user_email: str):
            # Email sending logic
            pass
        
        # Call normally - error handling is automatic
        await send_welcome_email("user@example.com")
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            name = task_name or f"{func.__module__}.{func.__name__}"
            coro = func(*args, **kwargs)
            await _safe_task_wrapper(coro, name, max_retries, critical)
        return wrapper
    return decorator
