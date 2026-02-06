"""
Cloudinary Service - handles media uploads to Cloudinary
"""
import cloudinary
import cloudinary.uploader
import logging
import urllib.parse
import httpx
from typing import Optional, Dict, Any
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

    def _url_encode_filename(self, filename: str) -> str:
        """URL-encode filename to handle special characters like @ in emails"""
        # Replace @ with %40 and other special characters
        return urllib.parse.quote(filename, safe='')

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

    def upload_file_from_bytes(
        self, 
        file_content: bytes, 
        folder: str = "raamp_assets",
        filename: Optional[str] = None,
        validate_aspect_ratio: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Upload file content to Cloudinary
        
        Args:
            file_content: Binary content of the file
            folder: Cloudinary folder name
            filename: Optional filename (will be URL-encoded)
            validate_aspect_ratio: Whether to validate aspect ratio for Instagram
            
        Returns:
            Dict containing:
                - secure_url: Public HTTPS URL
                - width: Asset width (if image/video)
                - height: Asset height (if image/video)
                - resource_type: "image", "video", or "raw"
                - format: file format (jpg, png, etc.)
                - aspect_ratio_validation: Validation results (if enabled)
            Returns None if upload fails
        """
        if not self.is_available:
            logger.error("Cloudinary upload failed: Service not configured.")
            return None
            
        try:
            # Prepare upload options
            upload_options = {
                "folder": folder,
                "resource_type": "auto"  # Automatically detects if it's image or video
            }
            
            # Add URL-encoded filename if provided
            if filename:
                encoded_filename = self._url_encode_filename(filename)
                upload_options["public_id"] = f"{folder}/{encoded_filename}"
                logger.info(f"Uploading with encoded filename: {encoded_filename}")
            
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                file_content,
                **upload_options
            )
            
            secure_url = upload_result.get("secure_url")
            width = upload_result.get("width")
            height = upload_result.get("height")
            
            if not secure_url:
                logger.error("Cloudinary upload succeeded but no secure_url returned")
                return None
            
            logger.info(f"✓ File uploaded to Cloudinary: {secure_url} ({width}x{height})")
            
            # Prepare response
            response = {
                "secure_url": secure_url,
                "width": width,
                "height": height,
                "resource_type": upload_result.get("resource_type"),
                "format": upload_result.get("format"),
                "public_id": upload_result.get("public_id")
            }
            
            # Validate aspect ratio if requested and dimensions available
            if validate_aspect_ratio and width and height:
                validation = self._validate_aspect_ratio(width, height)
                response["aspect_ratio_validation"] = validation
                
                if not validation["valid"]:
                    logger.warning(
                        f"⚠️  Aspect ratio {validation['aspect_ratio_decimal']} not optimal for Instagram. "
                        f"Recommended: {validation['recommended_ratio']}"
                    )
            
            return response
            
        except cloudinary.exceptions.Error as e:
            logger.error(f"⚠️  Cloudinary API error: {e}")
            return None
        except Exception as e:
            logger.error(f"⚠️  Cloudinary upload failed: {e}")
            return None
