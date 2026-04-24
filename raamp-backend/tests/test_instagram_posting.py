"""
Test script for Instagram auto-posting functionality.
This script will:
1. Upload a local image to storage
2. Post it to Instagram using the auto-posting agent

Usage:
    python tests/test_instagram_posting.py
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from config import Config
from application.services.firebase_storage_service import FirebaseStorageService
from infrastructure.database.database import connect_db, close_db


# Configuration
LOCAL_IMAGE_PATH = r"C:\Users\malik\Downloads\use.jpeg"
API_BASE_URL = "http://localhost:8000"

# Test user credentials (you'll need to replace with actual credentials)
TEST_USER_EMAIL = "your-test-email@example.com"  # Replace with your test user email
TEST_USER_PASSWORD = "your-password"  # Replace with your test user password


async def upload_image_to_storage(image_path: str) -> str:
    """
    Upload local image to Firebase Storage and return public URL.
    
    Args:
        image_path: Local path to image file
        
    Returns:
        Public URL of uploaded image
    """
    print(f"\n📤 Uploading image from: {image_path}")
    
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at: {image_path}")
    
    # Read image file
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    # Get file extension
    file_ext = Path(image_path).suffix
    
    # Upload to storage
    storage_service = FirebaseStorageService()
    
    # Generate unique filename
    import uuid
    filename = f"instagram_posts/{uuid.uuid4()}{file_ext}"
    
    try:
        # Upload file
        public_url = await asyncio.to_thread(
            storage_service.upload_file,
            image_data,
            filename,
            content_type=f"image/{file_ext[1:]}"
        )
        
        print(f"✅ Image uploaded successfully!")
        print(f"   Public URL: {public_url}")
        return public_url
        
    except Exception as e:
        print(f"⚠️  Firebase upload failed, using local storage")
        print(f"   Error: {e}")
        
        # Save to local storage as fallback
        local_path = Config.UPLOADED_FILES_DIR / filename
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(local_path, 'wb') as f:
            f.write(image_data)
        
        # For Instagram API, we need a publicly accessible URL
        # If using local storage, you'll need to expose this via ngrok or similar
        print("\n⚠️  WARNING: Instagram requires publicly accessible URLs!")
        print("   You'll need to use ngrok or deploy to get a public URL.")
        print(f"   Local file saved at: {local_path.absolute()}")
        
        # Return a placeholder - you'll need to replace this with actual public URL
        return f"http://localhost:8000/api/static/{filename}"


async def login_and_get_token(email: str, password: str) -> str:
    """
    Login to get JWT token for API authentication.
    
    Returns:
        JWT access token
    """
    print(f"\n🔐 Logging in as: {email}")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/signin",
            json={
                "email": email,
                "password": password
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Login failed: {response.status_code} - {response.text}")
        
        data = response.json()
        token = data.get("access_token")
        
        if not token:
            raise Exception("No access token in response")
        
        print("✅ Login successful!")
        return token


async def check_instagram_connection(token: str) -> bool:
    """
    Check if Instagram is connected for the user.
    
    Returns:
        True if connected, False otherwise
    """
    print("\n🔍 Checking Instagram connection status...")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/api/instagram/posting/connection-status",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            connected = data.get("connected", False)
            can_post = data.get("can_post", False)
            
            print(f"   Connected: {connected}")
            print(f"   Can Post: {can_post}")
            
            if connected and can_post:
                print(f"   IG Business ID: {data.get('ig_business_id')}")
                print(f"   Page Name: {data.get('page_name')}")
                print("✅ Instagram is connected and ready!")
                return True
            elif connected:
                print("⚠️  Instagram connected but token may be expired")
                return False
            else:
                print("❌ Instagram is not connected")
                return False
        else:
            print(f"❌ Error checking connection: {response.status_code}")
            return False


async def post_to_instagram(token: str, media_url: str, caption: str, mode: str = "post_now"):
    """
    Post image to Instagram.
    
    Args:
        token: JWT access token
        media_url: Public URL of the image
        caption: Post caption
        mode: Posting mode (post_now, schedule_post, post_story)
    """
    print(f"\n📱 Posting to Instagram (mode: {mode})...")
    print(f"   Media URL: {media_url}")
    print(f"   Caption: {caption}")
    
    payload = {
        "mode": mode,
        "media_url": media_url,
        "caption": caption
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{API_BASE_URL}/api/instagram/posting/post",
            headers={"Authorization": f"Bearer {token}"},
            json=payload
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ POST SUCCESSFUL!")
            print(f"   Status: {data.get('status')}")
            print(f"   Post ID: {data.get('post_id')}")
            
            if data.get('instagram_post_id'):
                print(f"   Instagram Post ID: {data.get('instagram_post_id')}")
                print(f"\n🎉 Your post is now live on Instagram!")
            
            if data.get('error'):
                print(f"   Error: {data.get('error')}")
            
            return data
        else:
            print(f"❌ POST FAILED!")
            print(f"   Response: {response.text}")
            return None


async def get_post_history(token: str):
    """Get recent post history."""
    print("\n📜 Fetching post history...")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/api/instagram/posting/history",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            posts = data.get('posts', [])
            total = data.get('total', 0)
            
            print(f"   Total posts: {total}")
            
            if posts:
                print("\n   Recent posts:")
                for post in posts[:3]:  # Show last 3
                    print(f"   - {post.get('status')}: {post.get('caption', 'No caption')[:50]}...")
        else:
            print(f"   Error: {response.status_code}")


async def main():
    """Main test flow."""
    print("=" * 70)
    print("🚀 INSTAGRAM AUTO-POSTING TEST SCRIPT")
    print("=" * 70)
    
    try:
        # Connect to database
        print("\n🔌 Connecting to database...")
        await connect_db()
        print("✅ Database connected")
        
        # Step 1: Login
        token = await login_and_get_token(TEST_USER_EMAIL, TEST_USER_PASSWORD)
        
        # Step 2: Check Instagram connection
        is_connected = await check_instagram_connection(token)
        
        if not is_connected:
            print("\n❌ Cannot proceed: Instagram is not connected")
            print("   Please connect your Instagram account first via the app")
            return
        
        # Step 3: Upload image
        try:
            media_url = await upload_image_to_storage(LOCAL_IMAGE_PATH)
        except FileNotFoundError as e:
            print(f"\n❌ Error: {e}")
            print("   Please update LOCAL_IMAGE_PATH in the script")
            return
        
        # Step 4: Post to Instagram
        caption = """Iftar drive DONATION

A small act of kindness can make someone's Iftar special. Be a part of something meaningful this Ramadan.

🌙 #Ramadan #Iftar #Charity #KaarEFalah"""
        
        result = await post_to_instagram(token, media_url, caption, mode="post_now")
        
        # Step 5: Check post history
        if result:
            await asyncio.sleep(2)  # Wait a bit
            await get_post_history(token)
        
        print("\n" + "=" * 70)
        print("✅ TEST COMPLETE")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Close database connection
        await close_db()
        print("\n🔌 Database connection closed")


if __name__ == "__main__":
    print("\n⚠️  BEFORE RUNNING THIS SCRIPT:")
    print("1. Update TEST_USER_EMAIL and TEST_USER_PASSWORD")
    print("2. Make sure your Instagram account is connected")
    print("3. Ensure the backend server is running on localhost:8000")
    print("4. For Instagram posting, the image URL must be publicly accessible")
    print("\nPress Ctrl+C to cancel, or Enter to continue...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\n\n👋 Test cancelled by user")
        sys.exit(0)
    
    asyncio.run(main())
