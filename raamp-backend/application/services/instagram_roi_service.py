"""
Instagram ROI Service.
Handles fetching and processing performance metrics for Instagram content.
"""
import httpx
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

from beanie.operators import NE, Or

from infrastructure.database.models.instagram_post_model import (
    ROIMetrics, 
    InstagramPostModel, 
    ScheduledInstagramPostModel, 
    InstagramStoryModel
)
from infrastructure.database.models.instagram_connection_model import InstagramConnectionModel
from application.services.encryption_service import EncryptionService
from presentation.routers.activity_router import log_activity

logger = logging.getLogger(__name__)

class InstagramROIFetchError(Exception):
    """Exception raised for errors during ROI metric fetching."""
    def __init__(self, message: str, code: Optional[int] = None):
        self.message = message
        self.code = code
        super().__init__(self.message)

async def fetch_post_insights(instagram_post_id: str, access_token: str) -> Dict[str, Any]:
    """
    Calls the Meta Graph API insights endpoint and normalizes the response.
    """
    base_url = "https://graph.facebook.com/v22.0"
    
    # Insights metrics to fetch
    metrics = "reach,impressions,total_interactions,likes,comments,shares,saved"
    insights_url = f"{base_url}/{instagram_post_id}/insights"
    insights_params = {
        "metric": metrics,
        "access_token": access_token
    }
    
    # Fields to fetch directly (for baseline counts)
    fields_url = f"{base_url}/{instagram_post_id}"
    fields_params = {
        "fields": "like_count,comments_count",
        "access_token": access_token
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Fetch insights and fields in parallel
            insights_task = client.get(insights_url, params=insights_params)
            fields_task = client.get(fields_url, params=fields_params)
            
            insights_res, fields_res = await asyncio.gather(insights_task, fields_task)
            
            # Check for API errors
            if insights_res.status_code != 200:
                error_data = insights_res.json().get("error", {})
                error_code = error_data.get("code")
                error_msg = error_data.get("message", "Unknown insights error")
                
                # Code 100 is overloaded (can mean "not enough data" OR "invalid param/metric").
                # Only treat it as pending when the message clearly indicates insufficient data.
                if error_code == 100:
                    msg_lower = (error_msg or "").lower()
                    if "not enough" in msg_lower or "insufficient" in msg_lower or "temporarily unavailable" in msg_lower:
                        logger.info(f"Insufficient data for post {instagram_post_id}: {error_msg}")
                        return {"status": "pending"}
                    raise InstagramROIFetchError(error_msg, error_code)
                
                raise InstagramROIFetchError(error_msg, error_code)
                
            if fields_res.status_code != 200:
                error_data = fields_res.json().get("error", {})
                raise InstagramROIFetchError(error_data.get("message", "Unknown fields error"))
            
            insights_data = insights_res.json().get("data", [])
            fields_data = fields_res.json()
            
            # Map insights array to a flat dict
            metrics_map = {m["name"]: m["values"][0]["value"] for m in insights_data if m.get("values")}
            
            # Normalize fields
            reach = metrics_map.get("reach", 0)
            impressions = metrics_map.get("impressions", 0)
            engagement = metrics_map.get("total_interactions", 0)
            likes = metrics_map.get("likes", fields_data.get("like_count", 0))
            comments = metrics_map.get("comments", fields_data.get("comments_count", 0))
            shares = metrics_map.get("shares", 0)
            saved = metrics_map.get("saved", 0)
            
            # Compute engagement rate
            # engagement_rate = (likes + comments + shares) / reach * 100
            engagement_rate = 0.0
            if reach > 0:
                engagement_rate = ((likes + comments + shares) / reach) * 100
            
            return {
                "status": "success",
                "metrics": {
                    "reach": reach,
                    "impressions": impressions,
                    "engagement": engagement,
                    "likes": likes,
                    "comments": comments,
                    "shares": shares,
                    "saved": saved,
                    "engagement_rate": round(float(engagement_rate), 2)
                }
            }
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching Instagram ROI: {e}")
        raise InstagramROIFetchError(f"HTTP communication failure: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in fetch_post_insights: {e}")
        raise InstagramROIFetchError(f"ROI fetch failed: {str(e)}")

async def refresh_post_roi(post_id: str, db=None) -> Optional[ROIMetrics]:
    """
    Fetches the post, retrieves access token, calls Meta API, and updates MongoDB.
    """
    encryption_service = EncryptionService()
    
    try:
        # 1. Find the post in any of the 3 collections
        post = await InstagramPostModel.get(post_id)
        if not post:
            post = await ScheduledInstagramPostModel.get(post_id)
        if not post:
            post = await InstagramStoryModel.get(post_id)
            
        if not post:
            logger.warning(f"Post {post_id} not found for ROI refresh.")
            return None
            
        # 2. Check if we have an external ID to fetch for
        instagram_post_id = getattr(post, "instagram_post_id", None) or getattr(post, "instagram_story_id", None)
        if not instagram_post_id:
            logger.info(f"Post {post_id} has no external Instagram ID yet. Setting status to pending.")
            post.roi_metrics.fetch_status = "pending"
            await post.save()
            return post.roi_metrics
            
        # 3. Get connection and token
        # Prefer the connection that belongs to the same user and has a usable page token.
        # (There may be multiple connection docs pointing at the same ig_business_id.)
        connection = await InstagramConnectionModel.find_one(
            InstagramConnectionModel.user_id == getattr(post, "user_id", None),
            InstagramConnectionModel.ig_business_id == getattr(post, "ig_business_id", None),
            InstagramConnectionModel.token_valid == True,  # noqa: E712
            InstagramConnectionModel.page_access_token != None,  # noqa: E711
        )
        if not connection:
            # Fallback: any valid connection with a page token for this ig_business_id
            connection = await InstagramConnectionModel.find_one(
                InstagramConnectionModel.ig_business_id == getattr(post, "ig_business_id", None),
                InstagramConnectionModel.token_valid == True,  # noqa: E712
                InstagramConnectionModel.page_access_token != None,  # noqa: E711
            )
        if not connection:
            # Final fallback: user-scoped connection (legacy records may not store ig_business_id)
            connection = await InstagramConnectionModel.find_one(
                InstagramConnectionModel.user_id == getattr(post, "user_id", None),
                InstagramConnectionModel.token_valid == True,  # noqa: E712
                InstagramConnectionModel.page_access_token != None,  # noqa: E711
            )

        if not connection or not connection.page_access_token:
            logger.error(
                "No valid Instagram connection found for ROI refresh. ig_business_id=%s user_id=%s",
                getattr(post, "ig_business_id", None),
                getattr(post, "user_id", None),
            )
            post.roi_metrics.fetch_status = "failed"
            await post.save()
            return post.roi_metrics
            
        # For some Graph API reads (esp. insights), IG User token can be required depending on app setup.
        # Prefer user_access_token when present; fallback to page_access_token.
        encrypted_token = connection.user_access_token or connection.page_access_token
        access_token = encryption_service.decrypt(encrypted_token)
        
        # 4. Fetch insights
        result = await fetch_post_insights(instagram_post_id, access_token)
        
        if result["status"] == "pending":
            post.roi_metrics.fetch_status = "pending"
            post.roi_metrics.last_fetched_at = datetime.now(timezone.utc)
            await post.save()
            return post.roi_metrics
            
        # 5. Update metrics
        metrics_data = result["metrics"]
        post.roi_metrics.reach = metrics_data["reach"]
        post.roi_metrics.impressions = metrics_data["impressions"]
        post.roi_metrics.engagement = metrics_data["engagement"]
        post.roi_metrics.likes = metrics_data["likes"]
        post.roi_metrics.comments = metrics_data["comments"]
        post.roi_metrics.shares = metrics_data["shares"]
        post.roi_metrics.saved = metrics_data["saved"]
        post.roi_metrics.engagement_rate = metrics_data["engagement_rate"]
        post.roi_metrics.fetch_status = "success"
        post.roi_metrics.last_fetched_at = datetime.now(timezone.utc)
        
        await post.save()
        logger.info(f"Successfully refreshed ROI for post {post_id} (IG ID: {instagram_post_id})")
        
        # Log Activity (Non-blocking)
        asyncio.create_task(log_activity(
            business_id=post.ig_business_id,
            event_type="insight_updated",
            title="Performance Metrics Updated",
            subtitle=f"Reach: {post.roi_metrics.reach} | Engagement: {post.roi_metrics.engagement_rate}%"
        ))
        
        return post.roi_metrics
        
    except InstagramROIFetchError as e:
        logger.warning(f"Failed to fetch ROI for post {post_id}: {e.message}")
        # Mark as failed if it's a real error (not just pending)
        try:
            post = await InstagramPostModel.get(post_id) or \
                   await ScheduledInstagramPostModel.get(post_id) or \
                   await InstagramStoryModel.get(post_id)
            if post:
                post.roi_metrics.fetch_status = "failed"
                post.roi_metrics.last_fetched_at = datetime.now(timezone.utc)
                await post.save()
        except Exception as db_err:
            logger.error(f"Failed to update failed status in DB: {db_err}")
        return None
        
    except Exception as e:
        logger.exception(f"Unexpected error in refresh_post_roi for {post_id}: {e}")
        return None

async def scheduled_roi_refresh() -> None:
    """
    Background job to refresh ROI for pending feed posts/stories.
    Eligible items: fetch_status pending, has instagram_post_id (or story id),
    and either no published_at or published long enough ago to retry Meta insights
    (>=1h, or null published_at which previously excluded rows from the old query).
    Runs every 6 hours (triggered from main.py).
    """
    try:
        now = datetime.now(timezone.utc)
        eligible_before = now - timedelta(hours=1)

        # Pending + must have external IG media id for insights API
        # Include published_at is None (older code paths never picked these up)
        pending_posts = await InstagramPostModel.find(
            InstagramPostModel.roi_metrics.fetch_status == "pending",
            NE(InstagramPostModel.instagram_post_id, None),
            Or(
                InstagramPostModel.published_at == None,  # noqa: E711
                InstagramPostModel.published_at < eligible_before,
            ),
        ).limit(50).to_list()

        pending_stories = await InstagramStoryModel.find(
            InstagramStoryModel.roi_metrics.fetch_status == "pending",
            NE(InstagramStoryModel.instagram_story_id, None),
            Or(
                InstagramStoryModel.published_at == None,  # noqa: E711
                InstagramStoryModel.published_at < eligible_before,
            ),
        ).limit(max(0, 50 - len(pending_posts))).to_list()
        
        all_pending = pending_posts + pending_stories
        
        if not all_pending:
            logger.info("No pending ROI refreshes needed at this time.")
            return
            
        logger.info(f"Starting scheduled ROI refresh for {len(all_pending)} items.")
        
        success_count = 0
        fail_count = 0
        
        for item in all_pending:
            metrics = await refresh_post_roi(str(item.id))
            if metrics and metrics.fetch_status == "success":
                success_count += 1
            else:
                fail_count += 1
                
        logger.info(f"Scheduled ROI refresh complete. Success: {success_count}, Failed: {fail_count}")
        
    except Exception as e:
        logger.error(f"Error in scheduled_roi_refresh job: {e}")
