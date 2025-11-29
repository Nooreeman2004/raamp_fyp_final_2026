"""
Firebase Storage Service - handles file uploads to Firebase Storage
"""
from firebase_admin import storage
import uuid


class FirebaseStorageService:
    """Service for uploading files to Firebase Storage"""
    
    def __init__(self):
        self._bucket = None
    
    @property
    def bucket(self):
        """Lazy-load bucket to avoid initialization issues"""
        if self._bucket is None:
            self._bucket = storage.bucket()
        return self._bucket
    
    async def upload_logo(self, file_content: bytes, file_name: str, user_id: str) -> str:
        """
        Upload brand logo to Firebase Storage
        
        Args:
            file_content: Binary content of the file
            file_name: Original filename
            user_id: User ID for organizing files
            
        Returns:
            Public URL of uploaded file
        """
        # Generate unique filename
        file_extension = file_name.split('.')[-1].lower()
        unique_filename = f"brand_logos/{user_id}/{uuid.uuid4()}.{file_extension}"
        
        # Validate file type
        allowed_extensions = ['svg', 'png', 'jpg', 'jpeg']
        if file_extension not in allowed_extensions:
            raise ValueError(f"Invalid file type. Allowed: {', '.join(allowed_extensions)}")
        
        # Validate file size (max 2MB)
        max_size = 2 * 1024 * 1024  # 2MB
        if len(file_content) > max_size:
            raise ValueError("File size exceeds 2MB limit")
        
        # Upload to Firebase Storage
        blob = self.bucket.blob(unique_filename)
        
        # Set content type
        content_types = {
            'svg': 'image/svg+xml',
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg'
        }
        blob.content_type = content_types.get(file_extension, 'application/octet-stream')
        
        # Upload
        blob.upload_from_string(file_content)
        
        # Make public
        blob.make_public()
        
        return blob.public_url
    
    async def delete_logo(self, logo_url: str):
        """Delete logo from Firebase Storage"""
        try:
            # Extract blob name from URL
            blob_name = logo_url.split(f"{self.bucket.name}/")[-1].split("?")[0]
            blob = self.bucket.blob(blob_name)
            blob.delete()
        except (ValueError, KeyError, IndexError) as e:
            print(f"Error deleting logo: {e}")
            # Don't raise error, just log it
