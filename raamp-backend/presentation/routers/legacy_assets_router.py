from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from pathlib import Path
import logging
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
        base_dir = Path("uploaded_files")
        possible_paths = [
            base_dir / sanitized_email / "content" / filename,
            base_dir / sanitized_email / "logos" / filename,
            base_dir / sanitized_email / "profiles" / filename,
            base_dir / filename, # Flat structure fallback
        ]
        
        for path in possible_paths:
            if path.exists() and path.is_file():
                logger.info(f"✅ Legacy asset found: {email}/{filename} -> {path}")
                return FileResponse(path)
        
        logger.warning(f"❌ Legacy asset not found: {email}/{filename} (Tried sanitized: {sanitized_email})")
        raise HTTPException(status_code=404, detail="Asset not found")
        
    except Exception as e:
        logger.error(f"Error resolving legacy asset: {e}")
        raise HTTPException(status_code=404, detail="Asset not found")
