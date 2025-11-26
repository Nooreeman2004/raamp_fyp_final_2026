# Application Layer - Scheduled Cleanup Service
import asyncio
from datetime import datetime, timedelta
from infrastructure.repositories.pending_verification_repository import PendingVerificationRepository
from config import config
import logging

logger = logging.getLogger(__name__)


class CleanupService:
    """Service for scheduled cleanup of expired pending verifications"""
    
    def __init__(self):
        self.pending_repo = PendingVerificationRepository()
        self.is_running = False
    
    async def cleanup_expired_verifications(self) -> int:
        """
        Remove expired pending verifications from database
        Returns number of entries deleted
        """
        try:
            count = await self.pending_repo.cleanup_expired()
            if count > 0:
                logger.info(f"Cleanup: Removed {count} expired pending verifications")
            return count
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            return 0
    
    async def start_scheduled_cleanup(self):
        """
        Start background task that runs cleanup periodically
        Runs every N hours based on config
        """
        if self.is_running:
            logger.warning("Cleanup service already running")
            return
        
        self.is_running = True
        interval_seconds = config.OTP_CLEANUP_INTERVAL_HOURS * 3600
        
        logger.info(f"Starting cleanup service (runs every {config.OTP_CLEANUP_INTERVAL_HOURS} hours)")
        
        while self.is_running:
            try:
                await self.cleanup_expired_verifications()
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                logger.info("Cleanup service cancelled")
                break
            except Exception as e:
                logger.error(f"Cleanup service error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    def stop_scheduled_cleanup(self):
        """Stop the background cleanup task"""
        self.is_running = False
        logger.info("Stopping cleanup service")


# Singleton instance
cleanup_service = CleanupService()
