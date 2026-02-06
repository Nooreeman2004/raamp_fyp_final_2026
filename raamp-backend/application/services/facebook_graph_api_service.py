"""
Facebook Graph API Service
Handles communication with Facebook Graph API for posting content
"""
import httpx
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class FacebookAPIError(Exception):
    """Custom exception for Facebook API errors"""
    pass


class FacebookGraphAPIClient:
    """
    Facebook Graph API client for posting content to Facebook Pages.
    Handles photo posts, video posts, and text posts.
    """
    
    GRAPH_API_VERSION = "v22.0"
    BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def post_photo(
        self,
        page_id: str,
        page_access_token: str,
        photo_url: str,
        message: Optional[str] = None
    ) -> str:
        """
        Post a photo to a Facebook Page.
        
        Args:
            page_id: Facebook Page ID
            page_access_token: Page access token
            photo_url: Publicly accessible photo URL
            message: Optional caption/message
            
        Returns:
            post_id: Facebook post ID
            
        Raises:
            FacebookAPIError: If posting fails
        """
        url = f"{self.BASE_URL}/{page_id}/photos"
        
        payload = {
            "url": photo_url,
            "access_token": page_access_token
        }
        
        if message:
            payload["message"] = message
        
        logger.info(f"Posting photo to Facebook Page: {page_id}")
        logger.info(f"Photo URL: {photo_url}")
        logger.info(f"Payload: {payload}")
        
        try:
            response = await self.client.post(url, data=payload)
            response.raise_for_status()
            data = response.json()
            
            if "id" in data:
                post_id = data["id"]
                logger.info(f"Photo posted successfully: {post_id}")
                return post_id
            else:
                raise FacebookAPIError(f"Unexpected response: {data}")
                
        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response.content else {}
            error_msg = error_data.get("error", {}).get("message", str(e))
            error_code = error_data.get("error", {}).get("code")
            error_type = error_data.get("error", {}).get("type")
            error_subcode = error_data.get("error", {}).get("error_subcode")
            logger.error(f"Facebook API error - Code: {error_code}, Subcode: {error_subcode}, Type: {error_type}, Message: {error_msg}")
            logger.error(f"Full error response: {error_data}")
            
            # Provide user-friendly error messages
            if error_code == 324 or error_subcode == 2069019:
                raise FacebookAPIError(
                    "Facebook could not access the image. Please ensure the URL is a direct link to an image file "
                    f"(e.g., .jpg, .png) and is publicly accessible. URL provided: {photo_url}"
                )
            
            raise FacebookAPIError(f"Failed to post photo: {error_msg}")
        except Exception as e:
            logger.error(f"Failed to post photo: {e}")
            raise FacebookAPIError(f"Failed to post photo: {str(e)}")
    
    async def post_video(
        self,
        page_id: str,
        page_access_token: str,
        video_url: str,
        title: Optional[str] = None,
        description: Optional[str] = None
    ) -> str:
        """
        Post a video to a Facebook Page.
        Uses resumable upload for better reliability.
        
        Args:
            page_id: Facebook Page ID
            page_access_token: Page access token
            video_url: Publicly accessible video URL
            title: Optional video title
            description: Optional video description
            
        Returns:
            post_id: Facebook post ID
            
        Raises:
            FacebookAPIError: If posting fails
        """
        url = f"{self.BASE_URL}/{page_id}/videos"
        
        payload = {
            "file_url": video_url,
            "access_token": page_access_token
        }
        
        if title:
            payload["title"] = title
        if description:
            payload["description"] = description
        
        logger.info(f"Posting video to Facebook Page: {page_id}")
        
        try:
            response = await self.client.post(url, data=payload)
            response.raise_for_status()
            data = response.json()
            
            if "id" in data:
                post_id = data["id"]
                logger.info(f"Video posted successfully: {post_id}")
                return post_id
            else:
                raise FacebookAPIError(f"Unexpected response: {data}")
                
        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response.content else {}
            error_msg = error_data.get("error", {}).get("message", str(e))
            logger.error(f"Facebook API error: {error_msg}")
            raise FacebookAPIError(f"Failed to post video: {error_msg}")
        except Exception as e:
            logger.error(f"Failed to post video: {e}")
            raise FacebookAPIError(f"Failed to post video: {str(e)}")
    
    async def post_text(
        self,
        page_id: str,
        page_access_token: str,
        message: str
    ) -> str:
        """
        Post a text status to a Facebook Page.
        
        Args:
            page_id: Facebook Page ID
            page_access_token: Page access token
            message: Text message to post
            
        Returns:
            post_id: Facebook post ID
            
        Raises:
            FacebookAPIError: If posting fails
        """
        url = f"{self.BASE_URL}/{page_id}/feed"
        
        payload = {
            "message": message,
            "access_token": page_access_token
        }
        
        logger.info(f"Posting text to Facebook Page: {page_id}")
        
        try:
            response = await self.client.post(url, data=payload)
            response.raise_for_status()
            data = response.json()
            
            if "id" in data:
                post_id = data["id"]
                logger.info(f"Text posted successfully: {post_id}")
                return post_id
            else:
                raise FacebookAPIError(f"Unexpected response: {data}")
                
        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response.content else {}
            error_msg = error_data.get("error", {}).get("message", str(e))
            logger.error(f"Facebook API error: {error_msg}")
            raise FacebookAPIError(f"Failed to post text: {error_msg}")
        except Exception as e:
            logger.error(f"Failed to post text: {e}")
            raise FacebookAPIError(f"Failed to post text: {str(e)}")
    
    async def get_page_access_token(
        self,
        user_access_token: str,
        page_id: str
    ) -> str:
        """
        Get page access token from user access token.
        
        Args:
            user_access_token: User's access token
            page_id: Facebook Page ID
            
        Returns:
            page_access_token: Page-specific access token
            
        Raises:
            FacebookAPIError: If token retrieval fails
        """
        url = f"{self.BASE_URL}/{page_id}"
        
        params = {
            "fields": "access_token",
            "access_token": user_access_token
        }
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "access_token" in data:
                return data["access_token"]
            else:
                raise FacebookAPIError("Page access token not found in response")
                
        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response.content else {}
            error_msg = error_data.get("error", {}).get("message", str(e))
            raise FacebookAPIError(f"Failed to get page access token: {error_msg}")
        except Exception as e:
            raise FacebookAPIError(f"Failed to get page access token: {str(e)}")
    
    async def get_page_info(
        self,
        page_id: str,
        access_token: str
    ) -> Dict[str, Any]:
        """
        Get Facebook Page information.
        
        Args:
            page_id: Facebook Page ID
            access_token: Access token
            
        Returns:
            Page information dict
        """
        url = f"{self.BASE_URL}/{page_id}"
        
        params = {
            "fields": "id,name,category,picture",
            "access_token": access_token
        }
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get page info: {e}")
            raise FacebookAPIError(f"Failed to get page info: {str(e)}")
