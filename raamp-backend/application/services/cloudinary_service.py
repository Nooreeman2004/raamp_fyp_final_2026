"""
Cloudinary Service - handles media uploads to Cloudinary
"""
import cloudinary
import cloudinary.uploader
import logging
import urllib.parse
import httpx
from typing import Optional, Dict, Any, Union, BinaryIO
from config import settings

logger = logging.getLogger(__name__)

class CloudinaryService:
    """Service for uploading media to Cloudinary"""
    
    def __init__(self):
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True
        )
        self._available = bool(settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_SECRET)
        if self._available:
            logger.info("✅ Cloudinary Service initialized successfully")
        else:
            logger.warning("⚠️  Cloudinary Service credentials missing. Cloudinary uploads will fail.")

    @property
    def is_available(self) -> bool:
        """Check if Cloudinary service is configured and available"""
        return self._available

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for Cloudinary - keep alphanumeric, dots, underscores, hyphens"""
        import re
        # Replace any non-safe characters with underscores
        # Keep alphanumeric, dots, underscores, hyphens
        sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        return sanitized

    def _validate_aspect_ratio(self, width: int, height: int, target_ratio: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate image aspect ratio for Instagram compatibility
        
        Args:
            width: Image width in pixels
            height: Image height in pixels
            target_ratio: Target aspect ratio ('4:5' for feed, '1.91:1' for landscape, '1:1' for square)
            
        Returns:
            Dict with validation result and recommended transformation
        """
        if not width or not height:
            return {"valid": False, "error": "Missing dimensions"}
        
        aspect_ratio = width / height
        
        # Instagram supported ratios
        INSTAGRAM_RATIOS = {
            "1:1": (1.0, 0.05),      # Square (0.95-1.05)
            "4:5": (0.8, 0.05),      # Portrait (0.75-0.85)
            "1.91:1": (1.91, 0.1)    # Landscape (1.81-2.01)
        }
        
        # Find closest supported ratio
        closest_ratio = None
        min_diff = float('inf')
        
        for ratio_name, (target, tolerance) in INSTAGRAM_RATIOS.items():
            diff = abs(aspect_ratio - target)
            if diff < min_diff:
                min_diff = diff
                closest_ratio = ratio_name
        
        # Check if within tolerance
        target, tolerance = INSTAGRAM_RATIOS[closest_ratio]
        is_valid = abs(aspect_ratio - target) <= tolerance
        
        return {
            "valid": is_valid,
            "current_ratio": f"{width}:{height}",
            "aspect_ratio_decimal": round(aspect_ratio, 2),
            "recommended_ratio": closest_ratio,
            "needs_transformation": not is_valid
        }

    async def _verify_url_accessible(self, url: str) -> bool:
        """Verify that the Cloudinary URL is publicly accessible"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.head(url, follow_redirects=True)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"URL accessibility check failed for {url}: {e}")
            return False

    def upload_file(
        self,
        file: Union[str, BinaryIO, bytes],
        folder: str = "raamp_assets",
        filename: Optional[str] = None,
        validate_aspect_ratio: bool = True,
        optimize_for_stories: bool = False,
        authenticated: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Upload a file (path, file object, or bytes) to Cloudinary.
        
        Args:
            file: File path, file-like object, or raw bytes
            folder: Cloudinary folder name
            filename: Optional original filename
            validate_aspect_ratio: Whether to validate for Instagram
            optimize_for_stories: Whether to optimize for 9:16
            authenticated: Whether to use authenticated delivery
            
        Returns:
            Dict with upload details or None if failed
        """
        if not self.is_available:
            logger.error("Cloudinary upload failed: Service not configured.")
            return None
            
        try:
            # Prepare upload options
            upload_options = {
                "folder": folder,
                "resource_type": "auto",
                "quality": "auto:best",
                "flags": "preserve_transparency.lossy",
            }

            if authenticated:
                upload_options["type"] = "authenticated"
            
            if optimize_for_stories:
                upload_options["transformation"] = [
                    {
                        "width": 1080, 
                        "height": 1920, 
                        "crop": "limit",
                        "gravity": "center",
                        "quality": "auto:best",
                        "fetch_format": "auto",
                        "flags": "progressive"
                    }
                ]
            
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                file,
                **upload_options
            )
            
            secure_url = upload_result.get("secure_url")
            width = upload_result.get("width")
            height = upload_result.get("height")
            
            if not secure_url:
                logger.error("Cloudinary upload succeeded but no secure_url returned")
                return None
            
            response = {
                "secure_url": secure_url,
                "width": width,
                "height": height,
                "resource_type": upload_result.get("resource_type"),
                "format": upload_result.get("format"),
                "public_id": upload_result.get("public_id")
            }
            
            if validate_aspect_ratio and width and height:
                response["aspect_ratio_validation"] = self._validate_aspect_ratio(width, height)
            
            return response
            
        except Exception as e:
            logger.error(f"⚠️  Cloudinary upload failed: {e}")
            return None

    def upload_file_from_bytes(
        self, 
        file_content: bytes, 
        folder: str = "raamp_assets",
        filename: Optional[str] = None,
        validate_aspect_ratio: bool = True,
        optimize_for_stories: bool = False,
        authenticated: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Backward compatibility wrapper for upload_file
        """
        return self.upload_file(
            file=file_content,
            folder=folder,
            filename=filename,
            validate_aspect_ratio=validate_aspect_ratio,
            optimize_for_stories=optimize_for_stories,
            authenticated=authenticated
        )

    def build_authenticated_signed_url(self, public_id: str, resource_type: str = "image") -> Optional[str]:
        """
        Build a signed URL for an authenticated asset.

        Note: This produces a signed Cloudinary URL for authenticated delivery. If you need time-limited URLs,
        use Cloudinary auth tokens (not implemented here).
        """
        if not self.is_available:
            return None
        try:
            from cloudinary.utils import cloudinary_url

            url, _ = cloudinary_url(
                public_id,
                secure=True,
                sign_url=True,
                type="authenticated",
                resource_type=resource_type or "image",
            )
            return url
        except Exception as e:
            logger.error("Failed to build signed Cloudinary URL: %s", str(e))
            return None
