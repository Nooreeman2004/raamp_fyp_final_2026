"""
Upload local image and get public URL
This script uploads your local image to storage and returns a public URL
that can be used for Instagram posting.

Run: python tests/upload_image_helper.py
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from application.services.firebase_storage_service import FirebaseStorageService
import uuid

# ============================================================================
# CONFIGURATION
# ============================================================================
IMAGE_PATH = r"C:\Users\malik\Downloads\use.jpeg"

# ============================================================================

def upload_image():
    """Upload image and return public URL."""
    print("=" * 70)
    print("📤 IMAGE UPLOAD HELPER")
    print("=" * 70)
    
    # Check if file exists
    if not os.path.exists(IMAGE_PATH):
        print(f"\n❌ Error: File not found at {IMAGE_PATH}")
        return None
    
    print(f"\n✅ File found: {IMAGE_PATH}")
    print(f"   Size: {os.path.getsize(IMAGE_PATH) / 1024:.2f} KB")
    
    # Read file
    with open(IMAGE_PATH, 'rb') as f:
        file_data = f.read()
    
    # Get extension
    file_ext = Path(IMAGE_PATH).suffix
    
    # Generate unique filename
    filename = f"instagram_posts/{uuid.uuid4()}{file_ext}"
    
    print(f"\n📤 Uploading to storage...")
    print(f"   Filename: {filename}")
    
    try:
        # Initialize storage service
        storage = FirebaseStorageService()
        
        # Upload file
        public_url = storage.upload_file(
            file_data,
            filename,
            content_type=f"image/{file_ext[1:]}"
        )
        
        print(f"\n✅ Upload successful!")
        print(f"\n📎 PUBLIC URL:")
        print(f"   {public_url}")
        print("\n   Copy this URL and use it for Instagram posting!")
        
        return public_url
        
    except Exception as e:
        print(f"\n❌ Upload failed: {e}")
        print("\n⚠️  Fallback: Saving to local storage...")
        
        # Save to local storage
        local_dir = Path("uploaded_files/instagram_posts")
        local_dir.mkdir(parents=True, exist_ok=True)
        
        local_file = local_dir / f"{uuid.uuid4()}{file_ext}"
        with open(local_file, 'wb') as f:
            f.write(file_data)
        
        print(f"✅ Saved locally: {local_file.absolute()}")
        print("\n⚠️  To use this with Instagram:")
        print("   1. Install ngrok: https://ngrok.com/download")
        print("   2. Run: ngrok http 8000")
        print("   3. Use the ngrok URL + /uploaded_files/instagram_posts/[filename]")
        
        return None


if __name__ == "__main__":
    print("\nThis helper uploads your image and provides a public URL")
    print("Press Enter to continue or Ctrl+C to cancel...")
    
    try:
        input()
        upload_image()
    except KeyboardInterrupt:
        print("\n\n👋 Cancelled")
