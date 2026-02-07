"""
Background worker for processing scheduled Instagram posts.
This module can be triggered by cron, Celery, or other schedulers.

Usage:
    # As a standalone script
    python -m application.services.instagram_scheduler_service
    
    # Or import and call from your scheduler
    from application.services.instagram_scheduler_service import process_scheduled_posts
    await process_scheduled_posts()
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import List

from application.use_cases.instagram_posting_use_cases import (
    GetPendingScheduledPostsUseCase,
    ExecuteScheduledPostUseCase,
    PostNowUseCase
)
from application.services.instagram_graph_api_service import InstagramGraphAPIClient
from application.services.notification_service import NotificationService
from infrastructure.repositories.instagram_post_repository_impl import (
    InstagramPostRepository,
    ScheduledPostRepository
)
from domain.entities.instagram_post_entity import ScheduledPost

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class InstagramSchedulerService:
    """
    Service for processing scheduled Instagram posts.
    Runs periodically to execute posts at their scheduled time.
    Emits notifications for lifecycle events.
    """
    
    def __init__(self):
        self.api_client = InstagramGraphAPIClient()
        self.post_repo = InstagramPostRepository()
        self.scheduled_repo = ScheduledPostRepository()
        self.notification_service = NotificationService()
        
        # Initialize use cases
        self.get_pending_use_case = GetPendingScheduledPostsUseCase(self.scheduled_repo)
        post_now_use_case = PostNowUseCase(self.post_repo, self.api_client)
        self.execute_scheduled_use_case = ExecuteScheduledPostUseCase(
            self.scheduled_repo,
            post_now_use_case
        )
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delays = [60, 300, 900]  # 1min, 5min, 15min
    
    async def process_scheduled_posts(self) -> dict:
        """
        Main entry point for processing scheduled posts.
        Finds and executes all posts scheduled for current time.
        
        Returns:
            Summary dict with counts of processed, succeeded, and failed posts
        """
        logger.info("Starting scheduled post processor")
        
        try:
            # Get all posts scheduled for now or earlier
            current_time = datetime.now(timezone.utc)
            pending_posts = await self.get_pending_use_case.execute(current_time)
            
            if not pending_posts:
                logger.info("No scheduled posts found for execution")
                return {
                    "processed": 0,
                    "succeeded": 0,
                    "failed": 0,
                    "timestamp": current_time.isoformat()
                }
            
            logger.info(f"Found {len(pending_posts)} scheduled posts to execute")
            
            # Process each post
            results = await self._process_posts(pending_posts)
            
            summary = {
                "processed": len(results),
                "succeeded": sum(1 for r in results if r["status"] == "published"),
                "failed": sum(1 for r in results if r["status"] == "failed"),
                "timestamp": current_time.isoformat()
            }
            
            logger.info(f"Scheduled post processing complete: {summary}")
            return summary
            
        except Exception as e:
            logger.exception(f"Error in scheduled post processor: {e}")
            return {
                "processed": 0,
                "succeeded": 0,
                "failed": 0,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def _process_posts(self, posts: List[ScheduledPost]) -> List[dict]:
        """
        Process multiple scheduled posts concurrently with rate limiting.
        Emits notifications for each lifecycle event.
        
        Args:
            posts: List of ScheduledPost entities to execute
            
        Returns:
            List of execution results
        """
        results = []
        
        # Process posts with concurrency control to respect rate limits
        # Instagram allows ~25 posts/hour per account
        # We'll process sequentially to be safe, but this could be optimized
        for post in posts:
            try:
                # Get post_id with fallback for legacy posts without ID
                post_id = str(post.id) if (hasattr(post, 'id') and post.id) else str(post.created_at.timestamp())
                user_id = post.user_id
                scheduled_time = post.scheduled_time
                
                logger.info(f"📤 Executing scheduled post: {post_id} for user {user_id}")
                
                # Execute the post
                result = await self._execute_with_retry(post, post_id, user_id, scheduled_time)
                results.append(result)
                
                # Add small delay between posts to avoid rate limits
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.exception(f"💥 Error processing scheduled post {post_id}: {e}")
                
                # Send failure notification
                try:
                    await self.notification_service.create_scheduled_post_failure(
                        user_id=user_id,
                        platform="instagram",
                        post_type="post",
                        scheduled_time=scheduled_time,
                        post_id=post_id,
                        error_reason=str(e),
                        error_code="job_crash"
                    )
                except Exception as notif_error:
                    logger.error(f"Failed to send error notification: {notif_error}")
                
                results.append({
                    "post_id": post_id,
                    "status": "failed",
                    "instagram_post_id": None,
                    "error": str(e)
                })
        
        return results
    
    async def _execute_with_retry(
        self,
        post: ScheduledPost,
        post_id: str,
        user_id: str,
        scheduled_time: datetime
    ) -> dict:
        """Execute post with automatic retry on failure"""
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries:
            try:
                # First attempt or retry
                if retry_count > 0:
                    delay = self.retry_delays[min(retry_count - 1, len(self.retry_delays) - 1)]
                    next_attempt = datetime.now(timezone.utc) + timedelta(seconds=delay)
                    
                    logger.info(f"🔄 Retry attempt {retry_count} for post {post_id}")
                    
                    # Send retry notification
                    await self.notification_service.create_retry_started(
                        user_id=user_id,
                        platform="instagram",
                        post_id=post_id,
                        retry_attempt=retry_count,
                        next_retry_time=next_attempt
                    )
                    
                    await asyncio.sleep(delay)
                
                # Execute the post
                result = await self.execute_scheduled_use_case.execute(post_id)
                actual_publish_time = datetime.now(timezone.utc)
                
                if result.get("status") == "published":
                    # Success!
                    logger.info(f"✅ Post {post_id} published successfully")
                    
                    # Send success notification
                    notification_func = (
                        self.notification_service.create_retry_success
                        if retry_count > 0
                        else self.notification_service.create_scheduled_post_success
                    )
                    
                    await notification_func(
                        user_id=user_id,
                        platform="instagram",
                        post_type=getattr(post, 'post_type', 'post'),
                        scheduled_time=scheduled_time,
                        actual_publish_time=actual_publish_time,
                        post_id=post_id,
                        instagram_post_id=result.get("instagram_post_id"),
                        **{"retry_attempt": retry_count} if retry_count > 0 else {}
                    )
                    
                    return result
                else:
                    # Non-published status
                    last_error = result.get("error", "Unknown error")
                    logger.warning(f"⚠️ Post {post_id} returned status: {result.get('status')}")
                    
            except Exception as e:
                last_error = str(e)
                logger.error(f"❌ Attempt {retry_count + 1} failed for post {post_id}: {e}")
            
            retry_count += 1
        
        # All retries exhausted
        logger.error(f"💀 Post {post_id} failed permanently after {self.max_retries} retries")
        
        # Categorize error
        error_code = self._categorize_error(last_error)
        
        # Send permanent failure notification
        await self.notification_service.create_retry_failed_permanently(
            user_id=user_id,
            platform="instagram",
            post_id=post_id,
            max_retries=self.max_retries,
            final_error=last_error
        )
        
        return {
            "post_id": post_id,
            "status": "failed",
            "instagram_post_id": None,
            "error": last_error,
            "error_code": error_code
        }
    
    def _categorize_error(self, error_message: str) -> str:
        """Categorize error for better user messaging"""
        error_lower = error_message.lower()
        
        if "token" in error_lower and ("expired" in error_lower or "invalid" in error_lower):
            return "token_expired"
        elif "permission" in error_lower or "authorized" in error_lower:
            return "permission_missing"
        elif "media" in error_lower and "upload" in error_lower:
            return "media_upload_failed"
        elif "rate" in error_lower and "limit" in error_lower:
            return "rate_limit"
        elif "timeout" in error_lower or "network" in error_lower:
            return "network_timeout"
        elif "format" in error_lower or "invalid" in error_lower:
            return "invalid_media"
        else:
            return "meta_api_error"
    
    async def send_10min_reminders(self):
        """Send reminder notifications for posts scheduled in 10 minutes"""
        try:
            target_time = datetime.now(timezone.utc) + timedelta(minutes=10)
            time_window = timedelta(minutes=1)  # 10±1 minute window
            
            # Get posts scheduled around 10 minutes from now
            upcoming_posts = await self.scheduled_repo.find_by_time_range(
                start_time=target_time - time_window,
                end_time=target_time + time_window
            )
            
            for post in upcoming_posts:
                try:
                    await self.notification_service.create_reminder_10min_before(
                        user_id=post.user_id,
                        platform="instagram",
                        post_type=getattr(post, 'post_type', 'post'),
                        scheduled_time=post.scheduled_time,
                        post_id=str(post.id),
                        caption_preview=getattr(post, 'caption', None)
                    )
                except Exception as e:
                    logger.error(f"Failed to send reminder for post {post.id}: {e}")
            
            logger.info(f"📢 Sent {len(upcoming_posts)} reminder notifications")
            
        except Exception as e:
            logger.exception(f"Error sending reminders: {e}")


# Global instance for easy importing
_scheduler_service = None


def get_scheduler_service() -> InstagramSchedulerService:
    """Get or create singleton instance of scheduler service"""
    global _scheduler_service
    if _scheduler_service is None:
        _scheduler_service = InstagramSchedulerService()
    return _scheduler_service


async def process_scheduled_posts() -> dict:
    """
    Convenience function for external schedulers.
    Process all scheduled posts due for execution.
    Includes job health monitoring to prevent duplicates and track execution.
    
    Usage in cron/scheduler:
        from application.services.instagram_scheduler_service import process_scheduled_posts
        result = await process_scheduled_posts()
    """
    from application.services.job_health_monitor_service import job_health_monitor
    
    # Start job execution tracking
    execution_id = await job_health_monitor.start_job_execution("process_scheduled_posts")
    
    if execution_id is None:
        # Duplicate execution detected, skip this run
        logger.warning("Skipping duplicate execution of process_scheduled_posts")
        return {"status": "skipped", "reason": "duplicate_execution"}
    
    try:
        # Execute the job
        service = get_scheduler_service()
        result = await service.process_scheduled_posts()
        
        # Mark as completed
        await job_health_monitor.complete_job_execution(
            execution_id=execution_id,
            status="COMPLETED",
            result=result
        )
        
        return result
    
    except Exception as e:
        # Mark as failed
        await job_health_monitor.complete_job_execution(
            execution_id=execution_id,
            status="FAILED",
            error=str(e)
        )
        logger.error(f"Error in process_scheduled_posts: {e}")
        return {"status": "error", "error": str(e)}


async def main():
    """
    Main entry point when running as standalone script.
    Useful for testing or running via cron.
    """
    logger.info("Instagram Scheduler Service - Standalone Mode")
    result = await process_scheduled_posts()
    logger.info(f"Execution complete: {result}")
    return result


if __name__ == "__main__":
    # Run as standalone script
    asyncio.run(main())
