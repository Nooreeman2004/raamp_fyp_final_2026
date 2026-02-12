"""
URL Validator Utility
Validates that media URLs are publicly accessible before posting to Instagram/Facebook
"""
import httpx
import logging
from typing import Tuple
import asyncio

logger = logging.getLogger(__name__)

class URLValidator:
    """Validates URLs are publicly accessible"""
    
    @staticmethod
    async def verify_url_accessible(
        url: str,
        max_retries: int = 3,
        initial_delay: float = 2.0
    ) -> Tuple[bool, str]:
        """
        Verify that a URL is publicly accessible via HTTP HEAD request.
        Retries with exponential backoff to handle propagation delays.
        
        Args:
            url: The URL to verify
            max_retries: Number of retry attempts
            initial_delay: Initial delay in seconds (doubles each retry)
            
        Returns:
            Tuple of (is_accessible: bool, error_message: str)
        """
        # Quick validation
        if not url:
            return False, "URL is empty"
        
        if not url.startswith(("http://", "https://")):
            return False, f"URL must start with http:// or https://, got: {url}"
        
        if "localhost" in url or "127.0.0.1" in url:
            return False, f"Localhost URLs are not publicly accessible: {url}"
        
        # Instagram requires HTTPS
        if not url.startswith("https://"):
            logger.warning(f"⚠️  URL is HTTP not HTTPS, Instagram may reject: {url}")
        
        # Try to access the URL with retries
        delay = initial_delay
        last_error = ""
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"🔍 Verifying URL accessibility (attempt {attempt}/{max_retries}): {url[:100]}...")
                
                async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                    # Use HEAD request (faster, doesn't download content)
                    response = await client.head(url)
                    
                    if response.status_code == 200:
                        logger.info(f"✅ URL is accessible (HTTP {response.status_code})")
                        return True, ""
                    
                    elif response.status_code == 405:  # Method not allowed
                        # Some servers don't support HEAD, try GET
                        logger.info("HEAD not supported, trying GET...")
                        response = await client.get(url, timeout=10.0)
                        if response.status_code == 200:
                            logger.info(f"✅ URL is accessible via GET (HTTP {response.status_code})")
                            return True, ""
                    
                    last_error = f"HTTP {response.status_code}"
                    logger.warning(f"❌ URL returned HTTP {response.status_code}")
                    
            except httpx.TimeoutException as e:
                last_error = f"Timeout after 10s: {str(e)}"
                logger.warning(f"⏱️  Timeout accessing URL (attempt {attempt}): {e}")
                
            except httpx.ConnectError as e:
                last_error = f"Connection failed: {str(e)}"
                logger.error(f"🔌 Connection error (attempt {attempt}): {e}")
                
            except Exception as e:
                last_error = f"Error: {str(e)}"
                logger.error(f"❌ Error verifying URL (attempt {attempt}): {e}")
            
            # Wait before retry (exponential backoff)
            if attempt < max_retries:
                logger.info(f"⏳ Waiting {delay}s before retry (URL propagation delay)...")
                await asyncio.sleep(delay)
                delay *= 2  # Exponential backoff
        
        # All retries failed
        error_msg = (
            f"URL is not accessible after {max_retries} attempts. "
            f"Last error: {last_error}. "
            f"Instagram requires publicly accessible HTTPS URLs. "
            f"URL: {url[:100]}"
        )
        logger.error(f"❌❌ {error_msg}")
        return False, error_msg
    
    @staticmethod
    async def verify_cloudinary_url(url: str) -> Tuple[bool, str]:
        """
        Verify a Cloudinary URL specifically.
        Uses stricter validation for Cloudinary.
        
        Args:
            url: Cloudinary URL
            
        Returns:
            Tuple of (is_accessible: bool, error_message: str)
        """
        if "res.cloudinary.com" not in url:
            return False, f"Not a Cloudinary URL: {url}"
        
        if not url.startswith("https://"):
            return False, f"Cloudinary URL must use HTTPS: {url}"
        
        # Cloudinary URLs should be immediately accessible
        # Use shorter retry window
        return await URLValidator.verify_url_accessible(url, max_retries=2, initial_delay=1.0)
