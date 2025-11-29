"""
Test script to diagnose Instagram/Facebook connection issues
Run: python test_instagram_connect.py
"""
import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID", "")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET", "")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

async def test_instagram_connect():
    print("=" * 60)
    print("INSTAGRAM CONNECTION DIAGNOSTIC TEST")
    print("=" * 60)
    
    # Step 1: Check Facebook App Configuration
    print("\n[1] Checking Facebook App Configuration...")
    if not FACEBOOK_APP_ID:
        print("❌ ERROR: FACEBOOK_APP_ID not found in .env")
        return
    if not FACEBOOK_APP_SECRET:
        print("❌ ERROR: FACEBOOK_APP_SECRET not found in .env")
        return
    
    print(f"✅ Facebook App ID: {FACEBOOK_APP_ID}")
    print(f"✅ Backend URL: {BACKEND_URL}")
    
    # Step 2: Check OAuth Scopes
    print("\n[2] Required Instagram/Facebook Scopes...")
    required_scopes = [
        'instagram_basic',
        'instagram_manage_insights',
        'business_management',
        'pages_show_list',
        'pages_read_engagement',
        'pages_manage_metadata'
    ]
    
    env_scopes = os.getenv("FACEBOOK_OAUTH_SCOPES", "").split(',')
    env_scopes = [s.strip() for s in env_scopes if s.strip()]
    
    print(f"   Scopes in .env: {', '.join(env_scopes)}")
    print("\n   Checking required scopes:")
    for scope in required_scopes:
        if scope in env_scopes:
            print(f"   ✅ {scope}")
        else:
            print(f"   ❌ {scope} - MISSING!")
    
    # Step 3: Test Facebook Graph API connectivity
    print("\n[3] Testing Facebook Graph API connectivity...")
    test_url = "https://graph.facebook.com/v22.0/me"
    
    print("   Note: This will fail without a valid access token (expected)")
    print("   Just checking if Facebook API is reachable...")
    
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(test_url, params={'access_token': 'test'}, timeout=5.0)
            data = r.json()
            if 'error' in data:
                error = data['error']
                if error.get('code') == 190:  # Invalid token
                    print("   ✅ Facebook Graph API is reachable")
                    print(f"   (Got expected error: {error.get('message')})")
                else:
                    print(f"   ⚠️  Unexpected error: {error.get('message')}")
    except Exception as e:
        print(f"   ❌ Cannot reach Facebook API: {str(e)}")
    
    # Step 4: Check Facebook App Settings
    print("\n[4] Facebook App Settings Checklist...")
    print("   Go to: https://developers.facebook.com/apps/")
    print(f"   Select your app (ID: {FACEBOOK_APP_ID})")
    print("\n   Required Settings:")
    print("   ✓ App is in 'Development' mode (for testing)")
    print("   ✓ Add test users if needed (Settings → Basic → Add Platform)")
    print("   ✓ Valid OAuth Redirect URIs configured:")
    print(f"     - {BACKEND_URL}/api/profile/onboarding/facebook/callback")
    print(f"     - {BACKEND_URL}/api/instagram/callback")
    
    # Step 5: Instagram Business Account Requirements
    print("\n[5] Instagram Business Account Requirements...")
    print("   ✓ Facebook Page must exist")
    print("   ✓ Instagram account must be a 'Business' or 'Creator' account")
    print("   ✓ Instagram must be linked to the Facebook Page:")
    print("     → Page Settings → Instagram → Connect Account")
    print("   ✓ The Facebook user must be admin of both Page and Instagram")
    
    # Step 6: Common Issues
    print("\n[6] Common Instagram Connection Issues...")
    print("\n   Issue: 'No Instagram Business account found'")
    print("   → Instagram is not linked to any Facebook Page")
    print("   → Instagram account is not Business/Creator type")
    print("   → User doesn't have admin access to the Instagram")
    
    print("\n   Issue: 'Missing Facebook permissions'")
    print("   → Facebook account wasn't authorized with Instagram scopes")
    print("   → Need to disconnect and reconnect Facebook with new scopes")
    print("   → In Facebook settings, revoke app access and try again")
    
    print("\n   Issue: 'This page has no Instagram account linked'")
    print("   → Selected Facebook Page doesn't have Instagram connected")
    print("   → Go to Page → Settings → Instagram → Link account")
    
    # Step 7: Test User Flow
    print("\n[7] Test the Full Flow...")
    print("   Step 1: Go to your app → http://localhost:8080/profile/onboarding")
    print("   Step 2: If Facebook already connected, disconnect it first")
    print("   Step 3: Click 'Connect' on Facebook")
    print("   Step 4: Authorize with ALL permissions (check the list)")
    print("   Step 5: After Facebook connects, click 'Connect' on Instagram")
    print("   Step 6: Select the Facebook Page that has Instagram linked")
    print("   Step 7: Should connect successfully!")
    
    # Step 8: Debug Endpoints
    print("\n[8] Backend Debug Endpoints...")
    print(f"   GET {BACKEND_URL}/api/profile/onboarding/status")
    print(f"   GET {BACKEND_URL}/api/profile/onboarding/instagram/pages")
    print(f"   GET {BACKEND_URL}/api/profile/connections/facebook/granted-scopes")
    print("   (All require authentication)")
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("1. Verify your Instagram is a Business/Creator account")
    print("2. Link Instagram to your Facebook Page in Page Settings")
    print("3. Disconnect Facebook in the app if already connected")
    print("4. Reconnect Facebook to get new scopes")
    print("5. Try connecting Instagram again")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_instagram_connect())
