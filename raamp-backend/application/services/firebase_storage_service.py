"""
Firebase Storage Service - handles file uploads to Firebase Storage
"""
import uuid
import os
import base64
import logging
from pathlib import Path
from application.utils.file_manager import FileManager

logger = logging.getLogger(__name__)

# Default profile picture URL
DEFAULT_PROFILE_PICTURE = "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_960_720.png"


class FirebaseStorageService:
    """Service for uploading files to Firebase Storage with local fallback"""
    
    def __init__(self):
        self._local_storage_path = Path("uploaded_files")
        # Create local storage directory
        self._local_storage_path.mkdir(exist_ok=True)
        self._bucket = None
        self._initialized = False

    def _ensure_initialized(self):
        """Lazy initialization of Firebase Storage"""
        if self._initialized:
            return
            
        try:
            from firebase_admin import storage, _apps
            if not _apps:
                # Still not initialized by main.py, don't fail here but keep it as not initialized
                return
            
            self._bucket = storage.bucket()
            self._initialized = True
            print(f"✅ Firebase Storage connected successfully")
        except Exception as e:
            print(f"⚠️  Firebase Storage initialization failed: {e}")
            self._initialized = True # Mark as initialized to stop retrying even on failure

    @property
    def bucket(self):
        """Get Firebase bucket with lazy loading"""
        self._ensure_initialized()
        return self._bucket
    
    def _save_locally(self, file_content: bytes, file_path: str) -> str:
        """Save file to local storage and return a localhost URL"""
        full_path = self._local_storage_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save file
        with open(full_path, 'wb') as f:
            f.write(file_content)
        
        print(f"✓ Saved file locally: {full_path}")
        
        # Return local file URL (works with backend static file serving)
        # Static files are mounted at /api/static in main.py
        from config import settings
        return f"{settings.BACKEND_URL}/api/static/{file_path}"
    
    async def upload_logo(self, file_content: bytes, file_name: str, user_id: str, user_email: str = None) -> str:
        """
        Upload brand logo to Firebase Storage (with local fallback/copy)
        
        Args:
            file_content: Binary file content
            file_name: Original filename
            user_id: User ID
            user_email: User email for organized folder structure (optional)
        
        Returns:
            Public URL or Data URL of uploaded file
        """
        # Generate unique filename
        file_extension = file_name.split('.')[-1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        
        # Validate file type
        allowed_extensions = ['svg', 'png', 'jpg', 'jpeg', 'webp']
        if file_extension not in allowed_extensions:
            raise ValueError(f"Invalid file type. Allowed: {', '.join(allowed_extensions)}")
        
        # Validate file size (max 5MB)
        max_size = 5 * 1024 * 1024 
        if len(file_content) > max_size:
            raise ValueError("File size exceeds 5MB limit")
        
        # Use organized folder structure if email provided
        if user_email:
            try:
                user_logos_dir = FileManager.get_user_upload_path(
                    email=user_email,
                    subfolder='logos',
                    create=True
                )
                sanitized_email = FileManager.sanitize_email_for_folder(user_email)
                local_filename = f"{sanitized_email}/logos/{unique_filename}"
                firebase_path = f"brand_logos/{sanitized_email}/{unique_filename}"
                local_path = user_logos_dir / unique_filename
            except Exception as e:
                logger.warning(f"Failed to use organized structure: {e}, falling back to legacy")
                local_filename = f"brand_logos/{user_id}/{unique_filename}"
                firebase_path = local_filename
                local_path = None
        else:
            # Legacy path for backward compatibility
            local_filename = f"brand_logos/{user_id}/{unique_filename}"
            firebase_path = local_filename
            local_path = None
        
        # 1. Save Locally (as backup/dev fallback)
        if local_path:
            with open(local_path, 'wb') as f:
                f.write(file_content)
            local_result = self._build_local_url(str(local_path).replace('uploaded_files/', ''))
        else:
            local_result = self._save_locally(file_content, local_filename)
        
        # 2. Upload to Firebase Storage if available
        if self.bucket:
            try:
                blob = self.bucket.blob(firebase_path)
                content_types = {
                    'svg': 'image/svg+xml',
                    'png': 'image/png',
                    'jpg': 'image/jpeg',
                    'jpeg': 'image/jpeg',
                    'webp': 'image/webp'
                }
                content_type = content_types.get(file_extension, 'application/octet-stream')
                blob.content_type = content_type
                blob.upload_from_string(file_content, content_type=content_type)
                blob.make_public()
                logger.info(f"✓ Logo uploaded to Firebase: {blob.public_url}")
                return blob.public_url
            except Exception as e:
                logger.warning(f"⚠️  Firebase upload failed, using local: {e}")
        
        return local_result
    
    async def upload_profile_picture(self, file_content: bytes, file_name: str, user_id: str) -> str:
        """
        Upload user profile picture to Firebase Storage
        
        Args:
            file_content: Binary content of the file
            file_name: Original filename
            user_id: User ID for organizing files
            
        Returns:
            Public URL of uploaded file
        """
        # Generate unique filename
        file_extension = file_name.split('.')[-1].lower()
        unique_filename = f"profile_pictures/{user_id}/{uuid.uuid4()}.{file_extension}"
        
        # Validate file type
        allowed_extensions = ['png', 'jpg', 'jpeg', 'webp']
        if file_extension not in allowed_extensions:
            raise ValueError(f"Invalid file type. Allowed: {', '.join(allowed_extensions)}")
        
        # Validate file size (max 5MB for profile pictures)
        max_size = 5 * 1024 * 1024  # 5MB
        if len(file_content) > max_size:
            raise ValueError("File size exceeds 5MB limit")
        
        # Upload to Firebase Storage if available
        bucket = self.bucket
        if bucket:
            try:
                blob = bucket.blob(unique_filename)
                
                # Set content type
                content_types = {
                    'png': 'image/png',
                    'jpg': 'image/jpeg',
                    'jpeg': 'image/jpeg',
                    'webp': 'image/webp'
                }
                content_type = content_types.get(file_extension, 'application/octet-stream')
                blob.content_type = content_type
                
                # Upload with explicit content_type
                blob.upload_from_string(file_content, content_type=content_type)
                
                # Make public
                blob.make_public()
                
                return blob.public_url
            except Exception as e:
                print(f"⚠️  Firebase profile picture upload failed: {e}")
        
        # Fallback to local storage (or default)
        return self._save_locally(file_content, unique_filename) or DEFAULT_PROFILE_PICTURE
    
    async def delete_profile_picture(self, picture_url: str):
        """Delete profile picture from Firebase Storage"""
        # Don't delete if it's the default picture or an external URL
        if not picture_url or DEFAULT_PROFILE_PICTURE in picture_url:
            return
        if "storage.googleapis.com" not in picture_url:
            return  # External URL, don't try to delete
            
        bucket = self.bucket
        if not bucket:
            return
            
        try:
            # Extract blob name from URL
            bucket_name = bucket.name
            blob_name = picture_url.split(f"{bucket_name}/")[-1].split("?")[0]
            blob = bucket.blob(blob_name)
            blob.delete()
        except (ValueError, KeyError, IndexError, Exception) as e:
            print(f"Error deleting profile picture: {e}")
            # Don't raise error, just log it
    
    async def delete_logo(self, logo_url: str):
        """Delete logo from Firebase Storage"""
        bucket = self.bucket
        if not bucket:
            return

        try:
            # Extract blob name from URL
            bucket_name = bucket.name
            blob_name = logo_url.split(f"{bucket_name}/")[-1].split("?")[0]
            blob = bucket.blob(blob_name)
            blob.delete()
        except (ValueError, KeyError, IndexError, Exception) as e:
            print(f"Error deleting logo: {e}")
            # Don't raise error, just log it

    async def upload_complaint_attachment(self, file_content: bytes, file_name: str, user_id: str, complaint_id: str) -> str:
        """
        Upload complaint attachment to Firebase Storage
        
        Args:
            file_content: Binary content of the file
            file_name: Original filename
            user_id: User ID for organizing files
            complaint_id: Complaint ID for organizing files
            
        Returns:
            Public URL of uploaded file
        """
        # Generate unique filename
        file_extension = file_name.split('.')[-1].lower()
        unique_filename = f"complaint_attachments/{user_id}/{complaint_id}/{uuid.uuid4()}.{file_extension}"
        
        # Validate file type
        allowed_extensions = ['png', 'jpg', 'jpeg', 'webp', 'gif', 'pdf', 'doc', 'docx', 'txt']
        if file_extension not in allowed_extensions:
            raise ValueError(f"Invalid file type. Allowed: {', '.join(allowed_extensions)}")
        
        # Validate file size (max 10MB for attachments)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(file_content) > max_size:
            raise ValueError("File size exceeds 10MB limit")
        
        # 1. Save locally first (optional, but good for tracking)
        # For now, we'll just try Firebase
        bucket = self.bucket
        if not bucket:
             # If no Firebase, save locally and return a local path or data URL
             return self._save_locally(file_content, unique_filename)

        try:
            # Upload to Firebase Storage
            blob = bucket.blob(unique_filename)
            
            # Set content type
            content_types = {
                'png': 'image/png',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'webp': 'image/webp',
                'gif': 'image/gif',
                'pdf': 'application/pdf',
                'doc': 'application/msword',
                'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'txt': 'text/plain'
            }
            content_type = content_types.get(file_extension, 'application/octet-stream')
            blob.content_type = content_type
            
            # Upload with explicit content_type
            blob.upload_from_string(file_content, content_type=content_type)
            
            # Make public
            blob.make_public()
            
            return blob.public_url
        except Exception as e:
            print(f"⚠️  Firebase attachment upload failed: {e}")
            return self._save_locally(file_content, unique_filename)

    def upload_file_from_bytes(self, file_content: bytes, file_path: str, content_type: str = "application/octet-stream") -> str:
        """
        Upload file from bytes to Firebase Storage
        
        Args:
            file_content: Binary content of the file
            file_path: Path in Firebase bucket (e.g., "assets/user@email.com/file.jpg")
            content_type: MIME type of the file
            
        Returns:
            Public URL of uploaded file
        """
        bucket = self.bucket
        if not bucket:
            # Fallback to local storage if Firebase not available
            return self._save_locally(file_content, file_path)
        
        try:
            blob = bucket.blob(file_path)
            blob.content_type = content_type
            blob.upload_from_string(file_content, content_type=content_type)
            blob.make_public()
            
            print(f"✓ File uploaded to Firebase: {blob.public_url}")
            return blob.public_url
        except Exception as e:
            print(f"⚠️  Firebase upload failed, using local: {e}")
            return self._save_locally(file_content, file_path)
