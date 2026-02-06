"""
Simple Instagram Posting Test Script
Quick test to post the Iftar image to Instagram

Run from raamp-backend directory:
    python tests/test_instagram_post_simple.py
"""
import requests
import os
from pathlib import Path

# ============================================================================
# CONFIGURATION - UPDATE THESE VALUES
# ============================================================================

# Your login credentials
USER_EMAIL = "your-email@example.com"  # UPDATE THIS
USER_PASSWORD = "your-password"        # UPDATE THIS

# Image to post
IMAGE_PATH = r"C:\Users\malik\Downloads\use.jpeg"

# Caption for the post
CAPTION = """Iftar drive DONATION

A small act of kindness can make someone's Iftar special. Be a part of something meaningful this Ramadan.

DONATE HERE
Title: NOOR E EMAN
Jazzcash: 03355180227

Visit Our Page @kaarefalah

🌙 #Ramadan #Iftar #Charity #Donation #KaarEFalah #RamadanKareem"""

# Backend URL
API_URL = "http://localhost:8000"

# ============================================================================
# SCRIPT LOGIC
# ============================================================================

def main():
    print("=" * 70)
    print("🚀 INSTAGRAM POSTING TEST")
    print("=" * 70)
    
    # Check if image exists
    if not os.path.exists(IMAGE_PATH):
        print(f"\n❌ Error: Image not found at {IMAGE_PATH}")
        print("   Please update IMAGE_PATH in the script")
        return
    
    print(f"\n✅ Image found: {IMAGE_PATH}")
    print(f"   Size: {os.path.getsize(IMAGE_PATH) / 1024:.2f} KB")
    
    # Step 1: Login
    print("\n" + "-" * 70)
    print("Step 1: Logging in...")
    print("-" * 70)
    
    try:
        response = requests.post(
            f"{API_URL}/api/signin",
            json={
                "email": USER_EMAIL,
                "password": USER_PASSWORD
            }
        )
        
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return
        
        token = response.json().get("access_token")
        if not token:
            print("❌ No access token received")
            return
        
        print("✅ Login successful!")
        print(f"   Token: {token[:20]}...")
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    # Step 2: Check Instagram connection
    print("\n" + "-" * 70)
    print("Step 2: Checking Instagram connection...")
    print("-" * 70)
    
    try:
        response = requests.get(
            f"{API_URL}/api/instagram/posting/connection-status",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Connected: {data.get('connected')}")
            print(f"   Can Post: {data.get('can_post')}")
            
            if data.get('connected') and data.get('can_post'):
                print(f"   IG Business ID: {data.get('ig_business_id')}")
                print(f"   Page Name: {data.get('page_name')}")
                print("✅ Instagram is ready!")
            else:
                print("\n❌ Instagram not connected or token expired")
                print("   Please connect Instagram via the app first")
                return
        else:
            print(f"❌ Connection check failed: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Connection check error: {e}")
        return
    
    # Step 3: Upload image to storage
    print("\n" + "-" * 70)
    print("Step 3: Uploading image...")
    print("-" * 70)
    
    # For this test, we need to upload the image to make it publicly accessible
    # Instagram API requires a publicly accessible URL
    
    print("\n⚠️  IMPORTANT: Instagram requires publicly accessible image URLs")
    print("   Options:")
    print("   1. Upload to Firebase Storage (if configured)")
    print("   2. Use ngrok to expose local server")
    print("   3. Upload to any CDN/cloud storage")
    print("\n   For this test, please provide a public URL for your image.")
    print("   Or press Enter to use a test image URL (demonstration only)")
    
    public_url = input("\n   Enter public image URL (or press Enter for demo): ").strip()
    
    if not public_url:
        print("\n   Using demo image URL for testing...")
        # Use a sample image URL for demonstration
        public_url = "https://picsum.photos/1080/1080"
        print(f"   Demo URL: {public_url}")
    
    # Step 4: Post to Instagram
    print("\n" + "-" * 70)
    print("Step 4: Posting to Instagram...")
    print("-" * 70)
    print(f"\n   Media URL: {public_url}")
    print(f"   Caption: {CAPTION[:60]}...")
    print("\n   This may take 30-60 seconds...")
    
    try:
        response = requests.post(
            f"{API_URL}/api/instagram/posting/post",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "mode": "post_now",
                "media_url": public_url,
                "caption": CAPTION
            },
            timeout=120  # 2 minutes timeout
        )
        
        print(f"\n   Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n" + "=" * 70)
            print("✅ POST SUCCESSFUL!")
            print("=" * 70)
            print(f"\n   Status: {data.get('status')}")
            print(f"   Post ID: {data.get('post_id')}")
            
            if data.get('instagram_post_id'):
                print(f"   Instagram Post ID: {data.get('instagram_post_id')}")
                print(f"\n   🎉 Your post is now live on Instagram!")
                print(f"   View it in your Instagram app or Business Suite")
            
            if data.get('error'):
                print(f"\n   ⚠️  Error: {data.get('error')}")
        else:
            print("\n" + "=" * 70)
            print("❌ POST FAILED")
            print("=" * 70)
            print(f"\n   Response: {response.text}")
            
    except requests.Timeout:
        print("\n❌ Request timeout - Instagram API may be slow")
        print("   Check post history to see if it succeeded")
    except Exception as e:
        print(f"\n❌ Posting error: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 5: Check post history
    print("\n" + "-" * 70)
    print("Step 5: Checking post history...")
    print("-" * 70)
    
    try:
        response = requests.get(
            f"{API_URL}/api/instagram/posting/history",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            posts = data.get('posts', [])
            
            print(f"\n   Total posts: {len(posts)}")
            
            if posts:
                print("\n   Recent posts:")
                for i, post in enumerate(posts[:3], 1):
                    status = post.get('status')
                    caption = post.get('caption', 'No caption')[:40]
                    ig_id = post.get('instagram_post_id', 'N/A')
                    print(f"\n   {i}. Status: {status}")
                    print(f"      Caption: {caption}...")
                    print(f"      IG Post ID: {ig_id}")
    except Exception as e:
        print(f"   Error fetching history: {e}")
    
    print("\n" + "=" * 70)
    print("✅ TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    print("\n⚠️  BEFORE RUNNING:")
    print("1. Update USER_EMAIL and USER_PASSWORD in the script")
    print("2. Make sure Instagram is connected to your account")
    print("3. Ensure backend server is running (python main.py)")
    print("4. For real posting, you need a publicly accessible image URL")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    
    try:
        input()
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Test cancelled")
