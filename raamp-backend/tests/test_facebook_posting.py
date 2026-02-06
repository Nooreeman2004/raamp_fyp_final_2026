"""
Test Facebook Posting Implementation
Tests the complete Facebook posting workflow
"""
import asyncio
import httpx
from datetime import datetime, timedelta

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = "test@example.com"  # Replace with your test user email
TEST_USER_PASSWORD = "testpassword"   # Replace with your test user password
TEST_PAGE_ID = "123456789"            # Replace with your Facebook Page ID


async def login_and_get_cookies():
    """Login and return session cookies"""
    async with httpx.AsyncClient() as client:
        # Login
        response = await client.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
        )
        
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code}")
            print(response.json())
            return None
        
        print("✅ Login successful")
        return response.cookies


async def test_facebook_connection(cookies):
    """Test if Facebook is connected"""
    async with httpx.AsyncClient(cookies=cookies) as client:
        response = await client.get(f"{BASE_URL}/api/instagram/connections")
        
        if response.status_code != 200:
            print(f"❌ Failed to check connections: {response.status_code}")
            return False
        
        data = response.json()
        print(f"\n📱 Connection Status:")
        print(f"   Facebook Connected: {data.get('facebook_connected', False)}")
        print(f"   Instagram Connected: {data.get('instagram_connected', False)}")
        
        return data.get('facebook_connected', False)


async def test_post_photo_now(cookies):
    """Test posting a photo immediately"""
    print("\n🧪 Test 1: Post Photo Now")
    print("=" * 50)
    
    async with httpx.AsyncClient(cookies=cookies) as client:
        response = await client.post(
            f"{BASE_URL}/api/facebook/posting/post",
            json={
                "mode": "POST_NOW",
                "page_id": TEST_PAGE_ID,
                "media_type": "PHOTO",
                "media_url": "https://picsum.photos/800/600",
                "message": "Test photo from RAAMP platform! 📸"
            }
        )
        
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {data}")
        
        if response.status_code == 200:
            print("✅ Photo posted successfully!")
            return data.get('facebook_post_id')
        else:
            print("❌ Photo posting failed")
            return None


async def test_post_video_now(cookies):
    """Test posting a video immediately"""
    print("\n🧪 Test 2: Post Video Now")
    print("=" * 50)
    
    async with httpx.AsyncClient(cookies=cookies, timeout=120.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/facebook/posting/post",
            json={
                "mode": "POST_NOW",
                "page_id": TEST_PAGE_ID,
                "media_type": "VIDEO",
                "media_url": "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/Big_Buck_Bunny_360_10s_1MB.mp4",
                "title": "Test Video",
                "message": "Test video from RAAMP platform! 🎥"
            }
        )
        
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {data}")
        
        if response.status_code == 200:
            print("✅ Video posted successfully!")
            return data.get('facebook_post_id')
        else:
            print("❌ Video posting failed")
            return None


async def test_post_text_now(cookies):
    """Test posting text only"""
    print("\n🧪 Test 3: Post Text Now")
    print("=" * 50)
    
    async with httpx.AsyncClient(cookies=cookies) as client:
        response = await client.post(
            f"{BASE_URL}/api/facebook/posting/post",
            json={
                "mode": "POST_NOW",
                "page_id": TEST_PAGE_ID,
                "media_type": "TEXT",
                "message": "Hello from RAAMP! This is a text-only post. 👋"
            }
        )
        
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {data}")
        
        if response.status_code == 200:
            print("✅ Text posted successfully!")
            return data.get('facebook_post_id')
        else:
            print("❌ Text posting failed")
            return None


async def test_schedule_post(cookies):
    """Test scheduling a post"""
    print("\n🧪 Test 4: Schedule Post")
    print("=" * 50)
    
    # Schedule for 5 minutes from now
    scheduled_time = datetime.now() + timedelta(minutes=5)
    
    async with httpx.AsyncClient(cookies=cookies) as client:
        response = await client.post(
            f"{BASE_URL}/api/facebook/posting/post",
            json={
                "mode": "SCHEDULE_POST",
                "page_id": TEST_PAGE_ID,
                "media_type": "PHOTO",
                "media_url": "https://picsum.photos/800/600?random=2",
                "message": "This post was scheduled using RAAMP! ⏰",
                "scheduled_time": scheduled_time.isoformat()
            }
        )
        
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {data}")
        
        if response.status_code == 200:
            print(f"✅ Post scheduled for {scheduled_time}")
            return data.get('post_id')
        else:
            print("❌ Post scheduling failed")
            return None


async def test_get_scheduled_posts(cookies):
    """Test getting scheduled posts"""
    print("\n🧪 Test 5: Get Scheduled Posts")
    print("=" * 50)
    
    async with httpx.AsyncClient(cookies=cookies) as client:
        response = await client.get(f"{BASE_URL}/api/facebook/posting/scheduled")
        
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Total Scheduled Posts: {data.get('total', 0)}")
        
        if response.status_code == 200:
            for post in data.get('scheduled_posts', []):
                print(f"\n   📅 Post ID: {post.get('post_id')}")
                print(f"      Page: {post.get('page_name')} ({post.get('page_id')})")
                print(f"      Type: {post.get('media_type')}")
                print(f"      Scheduled: {post.get('scheduled_time')}")
                print(f"      Status: {post.get('status')}")
            print("✅ Retrieved scheduled posts")
        else:
            print("❌ Failed to get scheduled posts")


async def test_cancel_scheduled_post(cookies, post_id):
    """Test canceling a scheduled post"""
    if not post_id:
        print("\n⚠️  Skipping Test 6: No post_id to cancel")
        return
    
    print("\n🧪 Test 6: Cancel Scheduled Post")
    print("=" * 50)
    
    async with httpx.AsyncClient(cookies=cookies) as client:
        response = await client.post(
            f"{BASE_URL}/api/facebook/posting/scheduled/cancel",
            json={"post_id": post_id}
        )
        
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {data}")
        
        if response.status_code == 200 and data.get('success'):
            print("✅ Post cancelled successfully")
        else:
            print("❌ Post cancellation failed")


async def test_get_posting_history(cookies):
    """Test getting posting history"""
    print("\n🧪 Test 7: Get Posting History")
    print("=" * 50)
    
    async with httpx.AsyncClient(cookies=cookies) as client:
        response = await client.get(f"{BASE_URL}/api/facebook/posting/history")
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            posts = response.json()
            print(f"Total Posts: {len(posts)}")
            
            for post in posts[:5]:  # Show first 5
                print(f"\n   📄 Post ID: {post.get('post_id')}")
                print(f"      Page: {post.get('page_name')} ({post.get('page_id')})")
                print(f"      Type: {post.get('media_type')}")
                print(f"      Status: {post.get('status')}")
                if post.get('facebook_post_id'):
                    print(f"      Facebook ID: {post.get('facebook_post_id')}")
                if post.get('error'):
                    print(f"      Error: {post.get('error')}")
            
            print("✅ Retrieved posting history")
        else:
            print("❌ Failed to get posting history")


async def main():
    """Run all tests"""
    print("=" * 70)
    print("🚀 Facebook Posting API Tests")
    print("=" * 70)
    
    # Login
    cookies = await login_and_get_cookies()
    if not cookies:
        print("❌ Cannot proceed without authentication")
        return
    
    # Check Facebook connection
    is_connected = await test_facebook_connection(cookies)
    if not is_connected:
        print("\n⚠️  WARNING: Facebook not connected!")
        print("   Please connect your Facebook account before testing posting.")
        print("   Visit: http://localhost:3000/profile/connections")
        return
    
    # Run tests
    print("\n" + "=" * 70)
    print("Running Facebook Posting Tests")
    print("=" * 70)
    
    # Test immediate posting
    await test_post_photo_now(cookies)
    await asyncio.sleep(2)
    
    await test_post_text_now(cookies)
    await asyncio.sleep(2)
    
    # Test video posting (takes longer)
    await test_post_video_now(cookies)
    await asyncio.sleep(2)
    
    # Test scheduling
    scheduled_post_id = await test_schedule_post(cookies)
    await asyncio.sleep(1)
    
    # Get scheduled posts
    await test_get_scheduled_posts(cookies)
    await asyncio.sleep(1)
    
    # Cancel scheduled post
    await test_cancel_scheduled_post(cookies, scheduled_post_id)
    await asyncio.sleep(1)
    
    # Get history
    await test_get_posting_history(cookies)
    
    print("\n" + "=" * 70)
    print("✅ All tests completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
