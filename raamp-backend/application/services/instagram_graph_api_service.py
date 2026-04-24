"""
Instagram Graph API Client Service.
This is an adapter that abstracts Meta Graph API interactions.
Follows Interface Segregation and Dependency Inversion principles.
"""
import httpx
import asyncio
import logging
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime, timedelta
from application.services.encryption_service import EncryptionService
from infrastructure.repositories.social_media_repository import SocialMediaRepository
from infrastructure.repositories.instagram_repository import InstagramRepository
from infrastructure.repositories.notification_repository import NotificationRepository
from infrastructure.database.models.notification_model import NotificationType

logger = logging.getLogger(__name__)


class InstagramAPIError(Exception):
    """Custom exception for Instagram API errors"""
    def __init__(self, message: str, code: Optional[str] = None, retry_after: Optional[int] = None):
        self.message = message
        self.code = code
        self.retry_after = retry_after
        super().__init__(self.message)


class InstagramGraphAPIClient:
    """
    Client for Instagram Graph API operations.
    Handles authentication, rate limiting, and API communication.
    
    This is a port/adapter in Clean Architecture terms - it abstracts
    external API details from business logic.
    """
    
    GRAPH_API_VERSION = "v22.0"
    BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds
    TOKEN_REFRESH_THRESHOLD_DAYS = 5
    
    def __init__(self):
        self.encryption_service = EncryptionService()
        self.social_media_repo = SocialMediaRepository()  # Legacy, kept for compatibility
        self.instagram_repo = InstagramRepository()
        self.notification_repo = NotificationRepository()
        self.rate_limit_remaining = 100  # Track rate limits
        self.rate_limit_reset_time = None

    async def get_access_token(self, user_id: str) -> Tuple[str, str]:
        """
        Retrieve and decrypt Instagram access token for user.
        Returns: (page_access_token, ig_business_id)
        Raises: InstagramAPIError if credentials not found
        """
        # Use InstagramRepository for Instagram data
        ig_account = await self.instagram_repo.find_by_user_id(user_id)
        if not ig_account:
            logger.error(f"DEBUG: Instagram account NOT found for user_id: {user_id}")
            raise InstagramAPIError("Instagram account not connected. Please connect first.")
            
        if not ig_account.page_access_token or not ig_account.ig_business_id:
            logger.error(f"DEBUG: Instagram account found but missing data for {user_id}. page_access_token: {bool(ig_account.page_access_token)}, ig_business_id: {ig_account.ig_business_id}")
            raise InstagramAPIError("Instagram account not connected. Please connect first.")
        
        # Decrypt token
        decrypted_token = self.encryption_service.decrypt(ig_account.page_access_token)
        
        # Instagram tokens are long-lived (60 days) but don't have explicit expiry tracking
        # Token refresh should be handled separately
        
        return decrypted_token, ig_account.ig_business_id

    async def create_media_container(
        self,
        user_id: str,
        media_url: str,
        caption: Optional[str] = None,
        is_story: bool = False,
        media_type: str = "IMAGE"
    ) -> str:
        """
        Create media container on Instagram.
        Step 1 of 2-step publishing process.
        """
        # Validate media URL before sending to Meta
        await self.validate_media_url(media_url)
        
        access_token, ig_business_id = await self.get_access_token(user_id)
        
        url = f"{self.BASE_URL}/{ig_business_id}/media"
        
        # Detect video based on type or extension
        is_video = media_type == "VIDEO" or any(ext in media_url.lower() for ext in [".mp4", ".mov", ".avi"])
        
        payload = {
            "access_token": access_token,
        }
        
        if is_video:
            payload["video_url"] = media_url
            payload["media_type"] = "VIDEO"
        else:
            payload["image_url"] = media_url

        if is_story:
            payload["media_type"] = "STORIES"
        elif caption:
            payload["caption"] = caption
        
        # Execute with retry logic
        return await self._execute_with_retry(
            method="POST",
            url=url,
            data=payload,
            operation="create_media_container"
        )

    async def publish_media(self, user_id: str, creation_id: str) -> str:
        """
        Publish media container to Instagram feed/story.
        Step 2 of 2-step publishing process.
        
        Args:
            user_id: Internal user ID
            creation_id: Media container ID from create_media_container
            
        Returns:
            Instagram post/story ID
            
        Raises:
            InstagramAPIError: If publication fails
        """
        access_token, ig_business_id = await self.get_access_token(user_id)
        
        url = f"{self.BASE_URL}/{ig_business_id}/media_publish"
        
        payload = {
            "access_token": access_token,
            "creation_id": creation_id
        }
        
        return await self._execute_with_retry(
            method="POST",
            url=url,
            data=payload,
            operation="publish_media"
        )

    async def reply_to_comment(self, user_id: str, comment_id: str, message: str) -> str:
        """
        Reply to an Instagram comment via Graph API using the stored Page access token.

        Endpoint: POST /{comment-id}/replies
        Returns: reply_id
        """
        access_token, _ = await self.get_access_token(user_id)
        url = f"{self.BASE_URL}/{comment_id}/replies"
        payload = {
            "access_token": access_token,
            "message": message,
        }
        return await self._execute_with_retry(
            method="POST",
            url=url,
            data=payload,
            operation="reply_to_comment",
        )

    async def delete_comment(self, user_id: str, comment_id: str) -> bool:
        """
        Delete an Instagram comment.

        Endpoint: DELETE /{comment-id}
        Returns: True on success.
        """
        access_token, _ = await self.get_access_token(user_id)
        url = f"{self.BASE_URL}/{comment_id}"
        params = {
            "access_token": access_token,
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(url, params=params)
                response.raise_for_status()
                data = response.json()
                return data.get("success") is True
        except Exception as e:
            logger.error(f"Failed to delete Instagram comment {comment_id}: {e}")
            raise InstagramAPIError(f"Failed to delete comment: {str(e)}")

    async def check_media_status(self, user_id: str, creation_id: str) -> Dict[str, Any]:
        """
        Check status of media container (for video processing).
        Videos need to be processed before publishing.
        
        Returns:
            Status info including status_code (IN_PROGRESS, FINISHED, ERROR)
        """
        access_token, _ = await self.get_access_token(user_id)
        
        url = f"{self.BASE_URL}/{creation_id}"
        params = {
            "access_token": access_token,
            "fields": "status_code,status"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def wait_for_media_processing(
        self,
        user_id: str,
        creation_id: str,
        max_wait_seconds: int = 120
    ) -> bool:
        """
        Poll media status until processing completes.
        Used for video uploads which require processing time.
        
        Returns:
            True if processing succeeded, False otherwise
        """
        start_time = datetime.now(timezone.utc)
        poll_interval = 5  # seconds
        
        while (datetime.now(timezone.utc) - start_time).total_seconds() < max_wait_seconds:
            try:
                status = await self.check_media_status(user_id, creation_id)
                status_code = status.get("status_code")
                
                if status_code == "FINISHED":
                    return True
                elif status_code == "ERROR":
                    logger.error(f"Media processing failed: {status}")
                    return False
                
                # Still processing, wait and retry
                await asyncio.sleep(poll_interval)
                
            except Exception as e:
                logger.error(f"Error checking media status: {e}")
                return False
        
        logger.warning(f"Media processing timeout for creation_id: {creation_id}")
        return False

    async def _execute_with_retry(
        self,
        method: str,
        url: str,
        data: Optional[Dict] = None,
        operation: str = "api_call"
    ) -> str:
        """
        Execute API call with exponential backoff retry logic.
        Handles rate limiting and transient failures.
        
        Returns:
            The 'id' field from API response
        """
        last_error = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    if method == "POST":
                        response = await client.post(url, data=data)
                    else:
                        response = await client.get(url, params=data)
                    
                    # Update rate limit tracking
                    self._update_rate_limits(response.headers)
                    
                    # Check for rate limiting
                    if response.status_code == 429:
                        retry_after = int(response.headers.get("Retry-After", 60))
                        logger.warning(f"Rate limited. Retry after {retry_after}s")
                        await asyncio.sleep(retry_after)
                        continue
                    
                    response.raise_for_status()
                    result = response.json()
                    
                    # Instagram API returns {id: "..."} on success
                    if "id" in result:
                        logger.info(f"{operation} successful: {result['id']}")
                        return result["id"]
                    else:
                        raise InstagramAPIError(f"Unexpected response format: {result}")
            
            except httpx.HTTPStatusError as e:
                last_error = e
                error_data = e.response.json() if e.response.content else {}
                error_message = error_data.get("error", {}).get("message", str(e))
                error_code = error_data.get("error", {}).get("code")
                
                logger.error(f"{operation} failed (attempt {attempt + 1}/{self.MAX_RETRIES}): {error_message}")
                
                # Don't retry on client errors (4xx except 429)
                if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                    raise InstagramAPIError(error_message, error_code)
                
                # Exponential backoff for retryable errors
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = self.RETRY_DELAY * (2 ** attempt)
                    logger.info(f"Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
            
            except Exception as e:
                last_error = e
                logger.error(f"{operation} failed (attempt {attempt + 1}/{self.MAX_RETRIES}): {e}")
                
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = self.RETRY_DELAY * (2 ** attempt)
                    await asyncio.sleep(wait_time)
        
        # All retries exhausted
        error_msg = f"{operation} failed after {self.MAX_RETRIES} attempts: {last_error}"
        raise InstagramAPIError(error_msg)

    def _update_rate_limits(self, headers: Dict[str, str]):
        """
        Update rate limit tracking from response headers.
        Instagram Graph API includes rate limit info in headers.
        """
        # Meta uses various header names for rate limits
        usage = headers.get("x-app-usage") or headers.get("x-business-use-case-usage")
        if usage:
            # Parse rate limit info (format varies)
            # This is a simplified version - actual implementation may need JSON parsing
            logger.debug(f"Rate limit usage: {usage}")

    async def refresh_user_token(self, user_id: str) -> bool:
        """
        Refresh long-lived User access token.
        Exchange the existing long-lived token for a NEW long-lived token.
        Meta allows refreshing long-lived tokens if they are not yet expired.
        
        Returns:
            True if refresh succeeded
        """
        try:
            account = await self.instagram_repo.find_by_user_id(user_id)
            if not account or not account.user_access_token:
                logger.warning(f"No Instagram account or user token found for {user_id}")
                return False
            
            # Decrypt current long-lived token
            current_token = self.encryption_service.decrypt(account.user_access_token)
            
            # Meta endpoint for refreshing long-lived tokens is the same as exchange
            # Exchange long-lived -> NEw long-lived
            refresh_url = "https://graph.facebook.com/v22.0/oauth/access_token"
            params = {
                "grant_type": "fb_exchange_token",
                "client_id": __import__('config').settings.FACEBOOK_APP_ID,
                "client_secret": __import__('config').settings.FACEBOOK_APP_SECRET,
                "fb_exchange_token": current_token
            }
            
            async with httpx.AsyncClient() as client:
                r = await client.get(refresh_url, params=params, timeout=15.0)
                
                if r.status_code != 200:
                    error_data = r.json()
                    error_msg = error_data.get("error", {}).get("message", "Unknown error")
                    error_code = error_data.get("error", {}).get("code")
                    
                    logger.error(f"Token refresh failed for {user_id}: {error_msg} (Code: {error_code})")
                    
                    # If it's an OAuthException (190), mark as invalid and notify user
                    if r.status_code == 400 or error_code == 190:
                        account.token_valid = False
                        await account.save()
                        
                        await self.notification_repo.create_notification(
                            user_id=user_id,
                            notification_type=NotificationType.ALERT,
                            title="Instagram Session Expired",
                            message="Your Meta session has expired. Please reconnect in Integrations to enable posting.",
                            metadata={"platform": "instagram", "error_code": error_code}
                        )
                    return False
                
                data = r.json()
                new_token = data.get("access_token")
                expires_in = data.get("expires_in")
                
                if not new_token:
                    logger.error(f"No new token returned for {user_id}")
                    return False
                
                # Encrypt and store
                encrypted_token = self.encryption_service.encrypt(new_token)
                expires_at = None
                if expires_in:
                    expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
                
                # Update DB
                await self.instagram_repo.create_or_update(
                    user_id,
                    user_access_token=encrypted_token,
                    expires_at=expires_at
                )
                
                # Update last_refreshed_at directly as create_or_update doesn't handle it yet specifically like this
                account = await self.instagram_repo.find_by_user_id(user_id)
                account.last_refreshed_at = datetime.now(timezone.utc)
                account.token_valid = True
                await account.save()
                
                logger.info(f"Successfully refreshed Instagram token for {user_id}. New expiry: {expires_at}")
                return True
                
        except Exception as e:
            logger.error(f"Unexpected error refreshing token for {user_id}: {e}")
            return False

    def _mask_token(self, token: str) -> str:
        """Safely mask a token for logging (first 4 and last 4 chars)."""
        if not token:
            return "None"
        if len(token) <= 8:
            return "***"
        return f"{token[:4]}...{token[-4:]}"

    async def refresh_long_lived_token(self, user_id: str) -> bool:
        """Deprecated: Use refresh_user_token instead."""
        return await self.refresh_user_token(user_id)
    async def validate_token_reachability(self, user_id: str) -> bool:
        """
        Validate if the stored Instagram token is reachable and valid.
        Calls a lightweight Meta API endpoint to verify.
        """
        try:
            access_token, ig_business_id = await self.get_access_token(user_id)
            
            # Call /me endpoint with the token
            url = f"{self.BASE_URL}/me"
            params = {
                "access_token": access_token,
                "fields": "id,name"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    logger.info(f"Token reachability confirmed for user {user_id}")
                    return True
                else:
                    error_data = response.json() if response.content else {}
                    logger.warning(f"Token reachability check failed for user {user_id}: {error_data}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error during token reachability check for user {user_id}: {e}")
            return False

    # --- SOCIAL INTELLIGENCE METHODS ---

    async def search_hashtag_id(self, user_id: str, hashtag_name: str) -> Optional[str]:
        """
        Get the ID for a specific hashtag. Required for subsequent hashtag-related calls.
        """
        try:
            access_token, ig_business_id = await self.get_access_token(user_id)
            url = f"{self.BASE_URL}/ig_hashtag_search"
            params = {
                "user_id": ig_business_id,
                "q": hashtag_name.replace("#", ""),
                "access_token": access_token
            }
            
            async with httpx.AsyncClient() as client:
                r = await client.get(url, params=params)
                if r.status_code == 200:
                    data = r.json().get("data", [])
                    if data:
                        return data[0].get("id")
                return None
        except Exception as e:
            logger.warning(f"Failed to find hashtag ID for {hashtag_name}: {e}")
            return None

    async def get_hashtag_info(self, user_id: str, hashtag_id: str) -> Dict[str, Any]:
        """
        Get metadata for a hashtag, including total media count.
        """
        try:
            access_token, _ = await self.get_access_token(user_id)
            url = f"{self.BASE_URL}/{hashtag_id}"
            params = {
                "fields": "id,name,media_count",
                "access_token": access_token
            }
            
            async with httpx.AsyncClient() as client:
                r = await client.get(url, params=params)
                if r.status_code == 200:
                    return r.json()
                return {}
        except Exception as e:
            logger.warning(f"Failed to fetch hashtag info for {hashtag_id}: {e}")
            return {}

    async def get_hashtag_recent_media_info(self, user_id: str, hashtag_id: str, limit: int = 10) -> List[Dict]:
        """
        Fetch recent media for a hashtag to analyze engagement velocity.
        """
        try:
            access_token, ig_business_id = await self.get_access_token(user_id)
            url = f"{self.BASE_URL}/{hashtag_id}/recent_media"
            params = {
                "user_id": ig_business_id,
                # Include username/permalink for downstream "influencer radar" proxy.
                "fields": "id,media_type,comments_count,like_count,timestamp,permalink,username",
                "access_token": access_token,
                "limit": limit
            }
            
            async with httpx.AsyncClient() as client:
                r = await client.get(url, params=params)
                if r.status_code == 200:
                    return r.json().get("data", [])
                return []
        except Exception as e:
            logger.warning(f"Failed to fetch recent media for hashtag {hashtag_id}: {e}")
            return []

    async def fetch_trending_hashtags(self, user_id: str, seed_keywords: List[str]) -> List[str]:
        """
        Discover real Instagram hashtags from seed keywords.

        For each seed keyword (capped to 5), we:
        - call ig_hashtag_search (q=keyword, user_id=ig_business_id) to get a hashtag id
        - call /{hashtag_id}?fields=name,media_count to confirm it exists
        - collect the returned `name`

        Errors are handled silently: any failing keyword is skipped.
        """
        if not isinstance(seed_keywords, list) or len(seed_keywords) == 0:
            return []

        keywords = [k for k in seed_keywords if isinstance(k, str) and k.strip()][:5]
        if not keywords:
            return []

        results: List[str] = []

        try:
            access_token, ig_business_id = await self.get_access_token(user_id)
        except Exception:
            # Silent failure: treat as "no IG available" for this scan
            return []

        async with httpx.AsyncClient(timeout=15.0) as client:
            for raw_kw in keywords:
                kw = (raw_kw or "").strip().replace("#", "")
                if not kw:
                    continue
                try:
                    # 1) Search hashtag id
                    search_url = f"{self.BASE_URL}/ig_hashtag_search"
                    search_params = {
                        "user_id": ig_business_id,
                        "q": kw,
                        "access_token": access_token,
                    }
                    r = await client.get(search_url, params=search_params)
                    if r.status_code != 200:
                        continue
                    data = (r.json() or {}).get("data", []) or []
                    if not data or not isinstance(data, list):
                        continue
                    hashtag_id = (data[0] or {}).get("id")
                    if not hashtag_id:
                        continue

                    # 2) Confirm hashtag exists (name/media_count)
                    detail_url = f"{self.BASE_URL}/{hashtag_id}"
                    detail_params = {
                        "fields": "name,media_count",
                        "access_token": access_token,
                    }
                    r2 = await client.get(detail_url, params=detail_params)
                    if r2.status_code != 200:
                        continue
                    detail = r2.json() or {}
                    name = (detail.get("name") or "").strip()
                    if not name:
                        continue

                    results.append(name)
                except Exception:
                    # Silent skip per requirements
                    continue

        # Deduplicate (case-insensitive) while preserving order
        seen = set()
        deduped: List[str] = []
        for n in results:
            ln = n.lower()
            if ln in seen:
                continue
            seen.add(ln)
            deduped.append(n)

        return deduped
    
    async def compute_keyword_engagement_score(self, user_id: str, keyword: str) -> Optional[Dict[str, Any]]:
        """
        Compute aggregate Instagram engagement score for a keyword/hashtag.
        
        Returns:
            {
                "keyword": str,
                "media_count": int,  # Total posts with this hashtag
                "avg_likes": float,  # Average likes on recent posts
                "avg_comments": float,  # Average comments on recent posts
                "engagement_score": float,  # 0-100 normalized engagement score
                "total_engagement": int  # Sum of likes + comments on recent sample
            }
            or None if API fails
        """
        try:
            # Search for hashtag ID
            clean_keyword = keyword.replace("#", "").replace(" ", "")
            hashtag_id = await self.search_hashtag_id(user_id, clean_keyword)
            
            if not hashtag_id:
                logger.warning("Hashtag ID not found for keyword: %s", keyword)
                return None
            
            # Get hashtag metadata (total media count)
            info = await self.get_hashtag_info(user_id, hashtag_id)
            media_count = info.get("media_count", 0)
            
            # Get recent media for engagement analysis
            recent_media = await self.get_hashtag_recent_media_info(user_id, hashtag_id, limit=20)
            
            if not recent_media:
                logger.warning("No recent media found for hashtag: %s", keyword)
                return None
            
            # Compute engagement metrics
            total_likes = sum(post.get("like_count", 0) for post in recent_media)
            total_comments = sum(post.get("comments_count", 0) for post in recent_media)
            total_engagement = total_likes + total_comments
            
            avg_likes = total_likes / len(recent_media)
            avg_comments = total_comments / len(recent_media)
            
            # Normalized engagement score (0-100)
            # Higher engagement per post = higher score
            # Use logarithmic scale to handle wide variance in engagement numbers
            # Typical viral post: 10k+ engagements, typical niche post: 100-1k
            import math
            engagement_per_post = total_engagement / len(recent_media)
            if engagement_per_post > 0:
                # Log scale: 100 engagement -> ~40, 1000 -> ~60, 10000 -> ~80, 100000 -> ~100
                engagement_score = min(100.0, max(0.0, 20 * math.log10(engagement_per_post + 1)))
            else:
                engagement_score = 0.0
            
            logger.info(
                "Instagram engagement for '%s': %d posts, %.1f avg likes, %.1f avg comments, score: %.2f",
                keyword, media_count, avg_likes, avg_comments, engagement_score
            )
            
            return {
                "keyword": keyword,
                "media_count": media_count,
                "avg_likes": avg_likes,
                "avg_comments": avg_comments,
                "engagement_score": engagement_score,
                "total_engagement": total_engagement
            }
            
        except InstagramAPIError as e:
            logger.warning("Instagram API error for keyword '%s': %s", keyword, e.message)
            return None
        except Exception as e:
            logger.error("Unexpected error computing engagement for '%s': %s", keyword, str(e))
            return None
    async def validate_media_url(self, media_url: str):
        """
        Perform a pre-flight check on the media URL to ensure it's Meta-compatible.
        Checks for:
        1. Public accessibility (200 OK)
        2. Correct Content-Type (image or video)
        3. No tunnel interstitial pages
        """
        # 1. Block Localhost and Local Tunnels
        blocked_keywords = ["localhost", "127.0.0.1", "loca.lt", "ngrok", "api/static"]
        if any(kw in media_url for kw in blocked_keywords):
            raise InstagramAPIError(
                "Instagram requires media to be available at a PUBLICLY accessible CDN URL (HTTPS). "
                f"The provided URL '{media_url}' is not suitable for Meta's servers. "
                "Please use Cloudinary or Firebase Storage for your assets."
            )

        # 2. Require HTTPS
        if not media_url.startswith("https://"):
             raise InstagramAPIError(
                "Instagram requires media URLs to use secure HTTPS. "
                f"The provided URL '{media_url}' is insecure."
            )
        
        # 3. Ratio Validation (Informational for now, since we have auto-crop)
        # In a real scenario, if transformation fails, we would block here.
        if "ar_" not in media_url and "cloudinary.com" not in media_url:
            logger.info("Ratio validation: External URL, assuming user knows best or transformation skipped.")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Meta scrapers don't send special bypass headers, so we check what they see
                # We use a User-Agent similar to Meta to see if we get a landing page
                headers = {"User-Agent": "facebookexternalhit/1.1"}
                response = await client.head(media_url, headers=headers, follow_redirects=True)
                
                # If HEAD fails or is not supported, try GET with a small range
                if response.status_code != 200:
                    response = await client.get(media_url, headers=headers, follow_redirects=True)
                
                if response.status_code != 200:
                    # Retry once after a delay for Cloudinary/CDN propagation
                    logger.warning(f"Media URL not immediately accessible (Status {response.status_code}). Retrying in 3s...")
                    await asyncio.sleep(3)
                    response = await client.get(media_url, headers=headers, follow_redirects=True)
                
                if response.status_code != 200:
                    raise InstagramAPIError(
                        f"Media URL is not accessible (Status {response.status_code}). "
                        "Instagram requires your image to be publicly reachable. "
                        "This usually resolves itself in a few seconds as the link propagates."
                    )
                
                content_type = response.headers.get("Content-Type", "").lower()
                logger.info(f"Media validation: {media_url} returned Content-Type: {content_type}")
                
                # Check for HTML (tunnel landing pages usually return text/html)
                if "text/html" in content_type:
                    raise InstagramAPIError(
                        "The media URL returned an HTML page instead of an image or video! "
                        "This is likely due to a tunnel (like localtunnel) showing a landing page. "
                        "Please use Cloudinary or Firebase Storage for reliable results."
                    )
                
                # Check for valid media types
                valid_types = ["image/", "video/"]
                if not any(t in content_type for t in valid_types):
                     raise InstagramAPIError(
                        f"Invalid media type: {content_type}. Instagram only accepts direct links to images or videos."
                    )
                     
        except httpx.RequestError as e:
            raise InstagramAPIError(f"Could not reach media URL for verification: {str(e)}")
        except Exception as e:
            if isinstance(e, InstagramAPIError):
                raise e
            logger.exception("Unexpected error during media validation")
            # We don't block here if it's an unknown error, but we've warned

    async def get_comments(self, user_id: str, media_id: str) -> List[Dict[str, Any]]:
        """
        Fetch all comments for a specific Instagram media ID.
        Returns:
            List of dicts with: id, text, timestamp, from {id, username}
        """
        access_token, _ = await self.get_access_token(user_id)
        url = f"{self.BASE_URL}/{media_id}/comments"
        params = {
            "fields": "id,text,timestamp,from",
            "access_token": access_token
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                return data.get("data", [])
        except Exception as e:
            logger.error(f"Failed to fetch comments for media {media_id}: {e}")
            return []

async def fetch_comments(post_id: str) -> List[Dict[str, Any]]:
    """
    Legacy wrapper for backward compatibility with older service calls.
    Note: Requires a global/system user resolution if user_id is not passed.
    """
    # This is a stub for the legacy call in comment_analysis_service.py
    # In a real scenario, we'd need to resolve the user owning this post.
    client = InstagramGraphAPIClient()
    # Attempt to resolve user_id from the post_id if possible, or use a default.
    # For now, we return empty to avoid crashes while we fix the calling logic.
    return []
