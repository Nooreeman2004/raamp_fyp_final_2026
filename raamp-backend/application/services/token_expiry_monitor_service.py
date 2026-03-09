"""
Token Expiry Monitoring Service
Monitors Instagram and Facebook token expiration and sends alerts
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from infrastructure.repositories.instagram_repository import InstagramRepository
from infrastructure.repositories.facebook_repository import FacebookRepository
from infrastructure.repositories.notification_repository import NotificationRepository
from infrastructure.database.models.notification_model import NotificationType
from application.services.instagram_graph_api_service import InstagramGraphAPIClient
from infrastructure.repositories.social_media_repository import SocialMediaRepository

logger = logging.getLogger(__name__)


class TokenExpiryMonitorService:
    """Service to monitor OAuth token expiration and send alerts"""
    
    def __init__(self):
        self.instagram_repo = InstagramRepository()
        self.facebook_repo = FacebookRepository()
        self.social_media_repo = SocialMediaRepository()
        self.notification_repo = NotificationRepository()
        self.ig_client = InstagramGraphAPIClient()
    
    async def check_expiring_tokens(self, days_before: int = 7) -> Dict[str, int]:
        """
        Check for tokens expiring within specified days and send notifications.
        
        Args:
            days_before: Number of days before expiry to send alert (default: 7)
            
        Returns:
            Dictionary with counts of alerts sent per platform
        """
        logger.info("Checking for tokens expiring within %d days...", days_before)
        
        alerts_sent = {
            "instagram": 0,
            "facebook": 0,
            "total": 0
        }
        
        # Check Instagram tokens
        instagram_alerts = await self._check_instagram_tokens(days_before)
        alerts_sent["instagram"] = instagram_alerts
        
        # Check Facebook tokens
        facebook_alerts = await self._check_facebook_tokens(days_before)
        alerts_sent["facebook"] = facebook_alerts
        
        alerts_sent["total"] = instagram_alerts + facebook_alerts
        
        logger.info("Token expiry check complete: %s", alerts_sent)
        return alerts_sent
    
    async def _check_instagram_tokens(self, days_before: int) -> int:
        """Check Instagram tokens and send alerts for expiring ones"""
        alerts_sent = 0
        
        try:
            # Get all Instagram connections
            # Note: Instagram tokens expire after 60 days, but we check for custom threshold
            all_connections = await self.instagram_repo.get_all_connections()
            
            threshold_date = datetime.now() + timedelta(days=days_before)
            
            for connection in all_connections:
                if not connection.access_token:
                    continue
                
                # Instagram short-lived tokens expire in 1 hour, long-lived in 60 days
                # We'll check if connection was created more than (60 - days_before) days ago
                token_age_days = (datetime.now() - connection.created_at).days
                estimated_expiry_days = 60 - token_age_days
                
                if 0 < estimated_expiry_days <= days_before:
                    # Token is expiring soon
                    user = await self.social_media_repo.get_user_by_id(connection.user_id)
                    if user:
                        await self._send_expiry_notification(
                            user_id=str(user.id),
                            platform="Instagram",
                            days_remaining=estimated_expiry_days
                        )
                        alerts_sent += 1
                        logger.info("Sent Instagram token expiry alert to user %s", user.email)
        
        except Exception as e:
            logger.error("Error checking Instagram tokens: %s", e)
        
        return alerts_sent
    
    async def _check_facebook_tokens(self, days_before: int) -> int:
        """Check Facebook tokens and send alerts for expiring ones"""
        alerts_sent = 0
        
        try:
            # Get all Facebook connections
            all_connections = await self.facebook_repo.get_all_connections()
            
            for connection in all_connections:
                if not connection.access_token:
                    continue
                
                # Facebook user tokens expire in 60 days, page tokens don't expire
                # Check if user token is expiring
                token_age_days = (datetime.now() - connection.created_at).days
                estimated_expiry_days = 60 - token_age_days
                
                if 0 < estimated_expiry_days <= days_before:
                    # Token is expiring soon
                    user = await self.social_media_repo.get_user_by_id(connection.user_id)
                    if user:
                        await self._send_expiry_notification(
                            user_id=str(user.id),
                            platform="Facebook",
                            days_remaining=estimated_expiry_days
                        )
                        alerts_sent += 1
                        logger.info("Sent Facebook token expiry alert to user %s", user.email)
        
        except Exception as e:
            logger.error("Error checking Facebook tokens: %s", e)
        
        return alerts_sent
    
    async def _send_expiry_notification(self, user_id: str, platform: str, days_remaining: int):
        """Send token expiry notification to user"""
        try:
            title = f"{platform} Token Expiring Soon"
            
            if days_remaining == 1:
                message = f"Your {platform} connection will expire in 1 day. Please reconnect to continue posting."
            else:
                message = f"Your {platform} connection will expire in {days_remaining} days. Please reconnect to avoid interruption."
            
            await self.notification_repo.create_notification(
                user_id=user_id,
                notification_type=NotificationType.ALERT,
                title=title,
                message=message,
                metadata={
                    "platform": platform.lower(),
                    "days_remaining": days_remaining,
                    "alert_type": "token_expiry",
                    "action_url": "/profile/connections"
                }
            )
        
        except Exception as e:
            logger.error("Error sending expiry notification: %s", e)

    async def auto_refresh_tokens(self) -> Dict[str, Any]:
        """
        Scan all Instagram connections and refresh tokens nearing expiry.
        Includes 24h throttling and admin alerts for mass failures.
        """
        logger.info("Starting automatic Instagram token refresh...")
        connections = await self.instagram_repo.get_all_connections()
        
        total = len(connections)
        refreshed = 0
        failed = 0
        skipped_throttle = 0
        not_needed = 0
        
        refresh_threshold_days = 15
        throttle_hours = 24
        
        for conn in connections:
            try:
                # 1. Check if refresh is needed
                if not conn.expires_at:
                    # If we don't have expiry, check reached reachability
                    # but for now, let's assume we only refresh if we have expiry or reachability fails
                    # If no expiry, we might need a manual reconnect once to get it
                    not_needed += 1
                    continue
                
                days_until_expiry = (conn.expires_at - datetime.utcnow()).days
                
                if days_until_expiry > refresh_threshold_days:
                    not_needed += 1
                    continue
                
                # 2. Check throttling
                if conn.last_refreshed_at:
                    hours_since_refresh = (datetime.utcnow() - conn.last_refreshed_at).total_seconds() / 3600
                    if hours_since_refresh < throttle_hours:
                        logger.info("Throttling refresh for %s - last refresh was %.1fh ago", conn.user_id, hours_since_refresh)
                        skipped_throttle += 1
                        continue
                
                # 3. Perform refresh
                success = await self.ig_client.refresh_user_token(conn.user_id)
                if success:
                    refreshed += 1
                else:
                    failed += 1
                    
            except Exception as e:
                logger.error("Unexpected error in refresh loop for %s: %s", conn.user_id, e)
                failed += 1
        
        # 4. Admin Alert for Mass Failures
        if failed >= 5 or (total > 0 and (failed / total) >= 0.2):
            logger.warning("Mass refresh failure detected: %d/%d failed. Sending admin alert.", failed, total)
            await self._send_admin_alert(failed, total)
            
        result = {
            "total": total,
            "refreshed": refreshed,
            "failed": failed,
            "skipped_throttle": skipped_throttle,
            "not_needed": not_needed
        }
        logger.info("Automatic refresh complete: %s", result)
        return result

    async def _send_admin_alert(self, failed_count: int, total_count: int):
        """Send alert to administrators about mass refresh failures"""
        try:
            admins = await self.social_media_repo.get_admin_users()
            for admin in admins:
                await self.notification_repo.create_notification(
                    user_id=str(admin.id),
                    notification_type=NotificationType.ALERT,
                    title="CRITICAL: Instagram Refresh Failures",
                    message=f"System detected {failed_count} failures out of {total_count} Instagram token refreshes. Possible Meta API issue or app restriction.",
                    metadata={"failed": failed_count, "total": total_count, "alert_type": "mass_refresh_failure"}
                )
        except Exception as e:
            logger.error("Error sending admin alert: %s", e)


# Singleton instance
token_monitor_service = TokenExpiryMonitorService()


async def check_token_expiry() -> Dict[str, int]:
    """
    Scheduled function to check for expiring tokens.
    Run this daily via cron job.
    """
    try:
        # 1. Check for expiring tokens (notifications)
        result = await token_monitor_service.check_expiring_tokens(days_before=7)
        
        # 2. Automatically refresh tokens nearing expiry
        refresh_result = await token_monitor_service.auto_refresh_tokens()
        
        logger.info("Token maintenance completed. Alerts: %s, Refreshes: %s", result, refresh_result)
        return {**result, "refresh_summary": refresh_result}
    except Exception as e:
        logger.error("Token maintenance failed: %s", e)
        return {"instagram": 0, "facebook": 0, "total": 0, "error": str(e)}
