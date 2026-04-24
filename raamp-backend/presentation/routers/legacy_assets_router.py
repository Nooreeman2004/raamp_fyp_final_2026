from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import logging
from config import Config
from application.utils.file_manager import FileManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/static/assets", tags=["Legacy Assets"])

@router.get("/{email}/{filename}")
async def get_legacy_asset(email: str, filename: str):
    """
    Handle old-style asset URLs and map them to the new sanitized structure.
    Old: /api/static/assets/user@email.com/file.jpg
    New: /api/static/user_email_com/content/file.jpg
    """
    try:
        # 1. Sanitize the email to find the new folder name
        sanitized_email = FileManager.sanitize_email_for_folder(email)
        
        # 2. Try 'content' subfolder (most common for these assets)
        base_dir = Config.UPLOADED_FILES_DIR
        possible_paths = [
            base_dir / sanitized_email / "content" / filename,
            base_dir / sanitized_email / "logos" / filename,
            base_dir / sanitized_email / "profiles" / filename,
            base_dir / filename, # Flat structure fallback
        ]
        
        for path in possible_paths:
            if path.exists() and path.is_file():
                return FileResponse(path)
        
        # Don't log - middleware will log the 404. Missing legacy assets are expected.
        raise HTTPException(status_code=404, detail="Asset not found")
        
    except HTTPException:
        raise  # Re-raise without additional logging
    except Exception as e:
        logger.error(f"Unexpected error resolving legacy asset {email}/{filename}: {e}")
        raise HTTPException(status_code=404, detail="Asset not found")
