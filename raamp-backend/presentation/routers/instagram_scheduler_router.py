"""
Internal endpoint for triggering scheduled post processing.
This can be called by cron jobs or other schedulers.
"""
from fastapi import APIRouter, HTTPException, Header
import logging
from application.services.instagram_scheduler_service import process_scheduled_posts
from config import settings as cfg

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/internal/instagram", tags=["internal-scheduler"])


@router.post("/process-scheduled-posts")
async def trigger_scheduled_posts_processor(
    x_cron_secret: str = Header(None)
):
    """
    Internal endpoint to trigger scheduled post processing.
    Should be called by cron/scheduler every 5-10 minutes.
    
    **Security**: Requires X-Cron-Secret header matching CRON_SECRET env var.
    
    Returns:
        Summary of processed posts
    """
    # Basic security - verify cron secret
    expected_secret = getattr(cfg, 'CRON_SECRET', None)
    if expected_secret and x_cron_secret != expected_secret:
        logger.warning("Unauthorized scheduler access attempt")
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    logger.info("Scheduler triggered via internal endpoint")
    
    try:
        result = await process_scheduled_posts()
        return result
    except Exception as e:
        logger.exception(f"Scheduler execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scheduler-health")
async def scheduler_health():
    """
    Health check endpoint for scheduler monitoring.
    Can be used by monitoring systems to verify scheduler is responsive.
    """
    return {
        "status": "healthy",
        "service": "instagram-scheduler",
        "version": "1.0.0"
    }
