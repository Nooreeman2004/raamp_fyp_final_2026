"""
File Manager Utility
Handles user-specific file organization with proper sanitization and structure
"""
import re
from pathlib import Path
import logging
from config import Config
from application.constants import FileLimits

logger = logging.getLogger(__name__)

class FileManager:
    """Manages user-specific file uploads with organized folder structure"""
    
    BASE_UPLOAD_DIR = Config.UPLOADED_FILES_DIR
    
    @staticmethod
    def sanitize_email_for_folder(email: str) -> str:
        """
        Sanitize email address for use as folder name.
        Replaces special characters and ensures safe directory naming.
        
        Args:
            email: User email address
            
        Returns:
            Sanitized folder name (e.g., "john_doe_gmail_com")
        """
        if not email or not isinstance(email, str):
            raise ValueError("Email must be a non-empty string")
        
        # Convert to lowercase
        sanitized = email.lower().strip()
        
        # Replace @ and . with underscores
        sanitized = sanitized.replace("@", "_").replace(".", "_")
        
        # Remove any characters that aren't alphanumeric, underscore, or hyphen
        sanitized = re.sub(r'[^a-z0-9_-]', '', sanitized)
        
        # Prevent directory traversal
        sanitized = sanitized.replace("..", "")
        
        # Ensure not empty after sanitization
        if not sanitized:
            raise ValueError("Email sanitization resulted in empty string")
        
        # Limit length to 100 characters
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
        
        return sanitized
    
    @staticmethod
    def get_user_upload_path(
        email: str,
        subfolder: str,
        create: bool = True
    ) -> Path:
        """
        Get the upload path for a user's specific content type.
        
        Args:
            email: User email address
            subfolder: Content type subfolder ('logos', 'content', 'profiles', etc.)
            create: Whether to create the directory if it doesn't exist
            
        Returns:
            Path object for the user's upload directory
        """
        # Sanitize email
        sanitized_email = FileManager.sanitize_email_for_folder(email)
        
        # Validate subfolder (only allow specific types)
        allowed_subfolders = ['logos', 'content', 'profiles', 'temp']
        if subfolder not in allowed_subfolders:
            raise ValueError(f"Invalid subfolder. Allowed: {', '.join(allowed_subfolders)}")
        
        # Build path: uploaded_files/{user_email}/{subfolder}/
        user_path = FileManager.BASE_UPLOAD_DIR / sanitized_email / subfolder
        
        # Create directory if requested
        if create:
            user_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 Created/verified upload path: {user_path}")
        
        return user_path
    
    @staticmethod
    def validate_file_type(
        content_type: str,
        subfolder: str
    ) -> bool:
        """
        Validate that file type is appropriate for the subfolder.
        
        Args:
            content_type: MIME type of the file
            subfolder: Target subfolder ('logos', 'content', etc.)
            
        Returns:
            True if valid, raises ValueError otherwise
        """
        allowed_types = {
            'logos': [
                'image/svg+xml',
                'image/png', 
                'image/jpeg',
                'image/jpg',
                'image/webp'
            ],
            'content': [
                'image/jpeg',
                'image/jpg',
                'image/png',
                'image/gif',
                'image/webp',
                'video/mp4',
                'video/quicktime',
                'video/x-msvideo'
            ],
            'profiles': [
                'image/jpeg',
                'image/jpg', 
                'image/png',
                'image/webp'
            ],
            'temp': [
                'image/jpeg',
                'image/jpg',
                'image/png',
                'image/gif',
                'image/webp',
                'video/mp4',
                'video/quicktime'
            ]
        }
        
        if subfolder not in allowed_types:
            raise ValueError(f"Unknown subfolder: {subfolder}")
        
        if content_type not in allowed_types[subfolder]:
            raise ValueError(
                f"File type '{content_type}' not allowed in '{subfolder}'. "
                f"Allowed types: {', '.join(allowed_types[subfolder])}"
            )
        
        return True
    
    @staticmethod
    def validate_file_size(
        file_size: int,
        subfolder: str
    ) -> bool:
        """
        Validate file size based on subfolder type.
        
        Args:
            file_size: Size in bytes
            subfolder: Target subfolder
            
        Returns:
            True if valid, raises ValueError otherwise
        """
        max_sizes = {
            'logos': FileLimits.MAX_LOGO_SIZE_BYTES,
            'content': FileLimits.MAX_CONTENT_SIZE_BYTES,
            'profiles': FileLimits.MAX_PROFILE_SIZE_BYTES,
            'temp': FileLimits.MAX_TEMP_FILE_SIZE_BYTES
        }
        
        max_size = max_sizes.get(subfolder, FileLimits.MAX_ATTACHMENT_SIZE_BYTES)
        
        if file_size > max_size:
            raise ValueError(
                f"File size {file_size / FileLimits.MB:.2f}MB exceeds "
                f"maximum {max_size / FileLimits.MB:.0f}MB for '{subfolder}'"
            )
        
        return True
    
    @staticmethod
    def get_cloudinary_folder(email: str, subfolder: str) -> str:
        """
        Get the Cloudinary folder path for organized cloud storage.
        
        Args:
            email: User email
            subfolder: Content type
            
        Returns:
            Cloudinary folder path (e.g., "users/john_doe_gmail_com/logos")
        """
        sanitized_email = FileManager.sanitize_email_for_folder(email)
        return f"users/{sanitized_email}/{subfolder}"
