"""
Job Health Monitoring Service
Monitors scheduler job execution, detects issues, and prevents duplicates
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from infrastructure.database.models.job_execution_log_model import JobExecutionLogModel

logger = logging.getLogger(__name__)


class JobHealthMonitorService:
    """Service to monitor scheduled job health and prevent issues"""
    
    def __init__(self):
        self.max_execution_time = 300  # 5 minutes
        self.heartbeat_tolerance = 120  # 2 minutes
        self.duplicate_threshold = 10  # seconds
    
    async def start_job_execution(self, job_id: str) -> Optional[str]:
        """
        Start tracking a job execution.
        Returns execution_id if job can proceed, None if duplicate detected.
        
        Args:
            job_id: Unique identifier for the job type
            
        Returns:
            Execution ID if successful, None if duplicate detected
        """
        try:
            # Check for duplicate executions (within last 10 seconds)
            recent_cutoff = datetime.now() - timedelta(seconds=self.duplicate_threshold)
            recent_executions = await JobExecutionLogModel.find(
                JobExecutionLogModel.job_id == job_id,
                JobExecutionLogModel.started_at >= recent_cutoff,
                JobExecutionLogModel.status == "RUNNING"
            ).to_list()
            
            if recent_executions:
                logger.warning(
                    f"Duplicate execution detected for job '{job_id}'. "
                    f"Already running: {len(recent_executions)} instance(s)"
                )
                return None
            
            # Create new execution log
            execution_id = f"{job_id}_{int(datetime.now().timestamp() * 1000)}"
            log = JobExecutionLogModel(
                job_id=job_id,
                execution_id=execution_id,
                started_at=datetime.now(),
                status="RUNNING"
            )
            await log.insert()
            
            logger.info(f"Started job execution: {execution_id}")
            return execution_id
        
        except Exception as e:
            logger.error(f"Error starting job execution tracking: {e}")
            return None
    
    async def complete_job_execution(
        self,
        execution_id: str,
        status: str = "COMPLETED",
        result: Optional[Dict] = None,
        error: Optional[str] = None
    ):
        """
        Mark job execution as complete.
        
        Args:
            execution_id: Execution identifier from start_job_execution
            status: COMPLETED or FAILED
            result: Job result data
            error: Error message if failed
        """
        try:
            # Find and update the execution log
            log = await JobExecutionLogModel.find_one(
                JobExecutionLogModel.execution_id == execution_id
            )
            
            if not log:
                logger.warning(f"Execution log not found: {execution_id}")
                return
            
            completed_at = datetime.now()
            duration = (completed_at - log.started_at).total_seconds()
            
            log.completed_at = completed_at
            log.status = status
            log.duration_seconds = duration
            log.result = result
            log.error = error
            
            await log.save()
            
            logger.info(
                f"Completed job execution: {execution_id} "
                f"(status={status}, duration={duration:.2f}s)"
            )
            
            # Check for abnormal execution time
            if duration > self.max_execution_time:
                await self._send_admin_alert(
                    title="Slow Job Execution Detected",
                    message=f"Job '{log.job_id}' took {duration:.2f} seconds (threshold: {self.max_execution_time}s)",
                    severity="warning",
                    metadata={
                        "job_id": log.job_id,
                        "execution_id": execution_id,
                        "duration_seconds": duration
                    }
                )
        
        except Exception as e:
            logger.error(f"Error completing job execution tracking: {e}")
    
    async def check_job_health(self) -> Dict[str, any]:
        """
        Check overall job health and detect issues.
        
        Returns:
            Health report with detected issues
        """
        try:
            report = {
                "status": "healthy",
                "issues": [],
                "stats": {}
            }
            
            # Check for stale running jobs (hung jobs)
            stale_cutoff = datetime.now() - timedelta(seconds=self.max_execution_time)
            stale_jobs = await JobExecutionLogModel.find(
                JobExecutionLogModel.status == "RUNNING",
                JobExecutionLogModel.started_at < stale_cutoff
            ).to_list()
            
            if stale_jobs:
                report["status"] = "unhealthy"
                report["issues"].append({
                    "type": "stale_jobs",
                    "count": len(stale_jobs),
                    "message": f"Found {len(stale_jobs)} job(s) running for over {self.max_execution_time}s"
                })
                
                # Send admin alert
                await self._send_admin_alert(
                    title="Stale Jobs Detected",
                    message=f"{len(stale_jobs)} job(s) have been running for over {self.max_execution_time} seconds",
                    severity="critical",
                    metadata={"stale_jobs": [j.job_id for j in stale_jobs]}
                )
            
            # Check for recent failures
            recent_cutoff = datetime.now() - timedelta(hours=1)
            recent_failures = await JobExecutionLogModel.find(
                JobExecutionLogModel.status == "FAILED",
                JobExecutionLogModel.started_at >= recent_cutoff
            ).to_list()
            
            if len(recent_failures) > 5:  # More than 5 failures in last hour
                report["status"] = "degraded"
                report["issues"].append({
                    "type": "high_failure_rate",
                    "count": len(recent_failures),
                    "message": f"High failure rate: {len(recent_failures)} failures in last hour"
                })
            
            # Get execution stats
            last_24h = datetime.now() - timedelta(hours=24)
            recent_logs = await JobExecutionLogModel.find(
                JobExecutionLogModel.started_at >= last_24h
            ).to_list()
            
            if recent_logs:
                completed = [log for log in recent_logs if log.status == "COMPLETED"]
                failed = [log for log in recent_logs if log.status == "FAILED"]
                
                avg_duration = sum(
                    log.duration_seconds for log in completed if log.duration_seconds
                ) / len(completed) if completed else 0
                
                report["stats"] = {
                    "total_executions_24h": len(recent_logs),
                    "completed": len(completed),
                    "failed": len(failed),
                    "failure_rate": len(failed) / len(recent_logs) if recent_logs else 0,
                    "avg_duration_seconds": round(avg_duration, 2)
                }
            
            logger.info(f"Job health check: {report['status']}")
            return report
        
        except Exception as e:
            logger.error(f"Error checking job health: {e}")
            return {
                "status": "error",
                "issues": [{"type": "health_check_error", "message": str(e)}],
                "stats": {}
            }
    
    async def cleanup_old_logs(self, days_to_keep: int = 30):
        """Delete job execution logs older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            result = await JobExecutionLogModel.find(
                JobExecutionLogModel.started_at < cutoff_date
            ).delete()
            
            logger.info(f"Cleaned up {result.deleted_count} old job execution logs")
            return result.deleted_count
        
        except Exception as e:
            logger.error(f"Error cleaning up job logs: {e}")
            return 0
    
    async def _send_admin_alert(
        self,
        title: str,
        message: str,
        severity: str = "warning",
        metadata: Optional[Dict] = None
    ):
        """Send alert to admin users about job health issues"""
        try:
            # Get admin users
            from infrastructure.repositories.social_media_repository import SocialMediaRepository
            from infrastructure.repositories.notification_repository import NotificationRepository
            from infrastructure.database.models.notification_model import NotificationType
            
            social_repo = SocialMediaRepository()
            notification_repo = NotificationRepository()
            
            # Find admin users
            admin_users = await social_repo.get_admin_users()
            
            for admin in admin_users:
                await notification_repo.create_notification(
                    user_id=str(admin.id),
                    notification_type=NotificationType.SYSTEM,
                    title=title,
                    message=message,
                    metadata={
                        **(metadata or {}),
                        "severity": severity,
                        "alert_type": "job_health",
                        "timestamp": datetime.now().isoformat()
                    }
                )
            
            logger.info(f"Sent admin alert: {title}")
        
        except Exception as e:
            logger.error(f"Error sending admin alert: {e}")


# Singleton instance
job_health_monitor = JobHealthMonitorService()


async def check_scheduler_health() -> Dict:
    """
    Scheduled function to check job health.
    Run this every 5 minutes via cron job.
    """
    try:
        report = await job_health_monitor.check_job_health()
        logger.info(f"Scheduler health check completed: {report['status']}")
        return report
    except Exception as e:
        logger.error(f"Scheduler health check failed: {e}")
        return {"status": "error", "error": str(e)}


async def cleanup_job_logs():
    """
    Scheduled function to cleanup old job logs.
    Run this daily via cron job.
    """
    try:
        deleted = await job_health_monitor.cleanup_old_logs(days_to_keep=30)
        logger.info(f"Job log cleanup completed: {deleted} logs deleted")
        return {"deleted": deleted}
    except Exception as e:
        logger.error(f"Job log cleanup failed: {e}")
        return {"deleted": 0, "error": str(e)}
