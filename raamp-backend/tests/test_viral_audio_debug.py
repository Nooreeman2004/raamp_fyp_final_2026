"""
Test script to debug viral audio API
Run with: python -m pytest raamp-backend/tests/test_viral_audio_debug.py -v -s
Or directly: python raamp-backend/tests/test_viral_audio_debug.py
"""
import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from application.services.viral_audio_provider import ViralAudioProvider
from application.services.spotify_service import SpotifyService
from config import config


async def test_spotify_credentials():
    """Test if Spotify credentials are loaded"""
    print("\n" + "="*60)
    print("TEST 1: Spotify Credentials Check")
    print("="*60)
    
    spotify = SpotifyService()
    print(f"Client ID: {'✅ SET' if spotify.client_id else '❌ MISSING'}")
    print(f"Client Secret: {'✅ SET' if spotify.client_secret else '❌ MISSING'}")
    
    if spotify.client_id:
        print(f"Client ID (first 10 chars): {spotify.client_id[:10]}...")
    if spotify.client_secret:
        print(f"Client Secret (first 10 chars): {spotify.client_secret[:10]}...")
    
    return bool(spotify.client_id and spotify.client_secret)


async def test_spotify_token():
    """Test if we can get a Spotify access token"""
    print("\n" + "="*60)
    print("TEST 2: Spotify Access Token")
    print("="*60)
    
    spotify = SpotifyService()
    token = await spotify._get_access_token()
    
    if token:
        print(f"✅ Successfully got access token")
        print(f"Token (first 20 chars): {token[:20]}...")
        return True
    else:
        print(f"❌ Failed to get access token")
        return False


async def test_spotify_viral_tracks():
    """Test if we can fetch viral tracks from Spotify"""
    print("\n" + "="*60)
    print("TEST 3: Spotify Viral Tracks")
    print("="*60)
    
    spotify = SpotifyService()
    
    # Test different markets
    markets = ["PK", "US", "GB"]
    
    for market in markets:
        print(f"\n📍 Testing market: {market}")
        tracks = await spotify.get_viral_tracks(market=market, limit=3)
        
        if tracks:
            print(f"✅ Got {len(tracks)} tracks for {market}")
            for i, track in enumerate(tracks, 1):
                print(f"  {i}. {track.get('name')} - {track.get('artist')}")
                print(f"     Popularity: {track.get('popularity')}")
                print(f"     URL: {track.get('url')}")
        else:
            print(f"❌ No tracks returned for {market}")
    
    return len(tracks) > 0 if tracks else False


async def test_spotify_search():
    """Test if we can search for tracks"""
    print("\n" + "="*60)
    print("TEST 4: Spotify Track Search")
    print("="*60)
    
    spotify = SpotifyService()
    
    queries = ["trending", "viral", "popular"]
    
    for query in queries:
        print(f"\n🔍 Searching for: {query}")
        tracks = await spotify.search_tracks(query=query, market="US", limit=3)
        
        if tracks:
            print(f"✅ Got {len(tracks)} tracks")
            for i, track in enumerate(tracks, 1):
                print(f"  {i}. {track.get('name')} - {track.get('artist')}")
        else:
            print(f"❌ No tracks found")
    
    return len(tracks) > 0 if tracks else False


async def test_viral_audio_provider():
    """Test the complete ViralAudioProvider flow"""
    print("\n" + "="*60)
    print("TEST 5: ViralAudioProvider (Complete Flow)")
    print("="*60)
    
    provider = ViralAudioProvider()
    
    test_cases = [
        {"platform": "instagram", "location": "PK", "niche": "fashion", "trend_keyword": "fashion"},
        {"platform": "instagram", "location": "US", "niche": "food", "trend_keyword": "food"},
        {"platform": "tiktok", "location": "GB", "niche": "music", "trend_keyword": "music"},
    ]
    
    all_success = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test Case {i}:")
        print(f"   Platform: {test_case['platform']}")
        print(f"   Location: {test_case['location']}")
        print(f"   Niche: {test_case['niche']}")
        
        tracks = await provider.get_tracks(
            platform=test_case['platform'],
            location=test_case['location'],
            niche=test_case['niche'],
            trend_keyword=test_case['trend_keyword'],
            limit=2
        )
        
        if tracks:
            print(f"   ✅ Got {len(tracks)} tracks")
            for j, track in enumerate(tracks, 1):
                print(f"      {j}. {track.get('track_name')} - {track.get('artist')}")
                print(f"         Source: {track.get('source')}")
                print(f"         Confidence: {track.get('confidence')}")
                if track.get('image'):
                    print(f"         Image: {track.get('image')[:50]}...")
        else:
            print(f"   ❌ No tracks returned")
            all_success = False
    
    return all_success


async def test_apple_music_rss():
    """Test Apple Music RSS feed directly"""
    print("\n" + "="*60)
    print("TEST 6: Apple Music RSS Feed")
    print("="*60)
    
    import httpx
    
    storefronts = ["pk", "us", "gb"]
    
    for storefront in storefronts:
        print(f"\n🍎 Testing storefront: {storefront.upper()}")
        url = f"https://rss.applemarketingtools.com/api/v2/{storefront}/music/most-played/10/songs.json"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    items = (data.get("feed") or {}).get("results") or []
                    print(f"   ✅ Got {len(items)} tracks")
                    
                    for i, item in enumerate(items[:3], 1):
                        name = item.get("name", "Unknown")
                        artist = item.get("artistName", "Unknown")
                        print(f"      {i}. {name} - {artist}")
                else:
                    print(f"   ❌ HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return True


async def test_endpoint_simulation():
    """Simulate what the actual API endpoint does"""
    print("\n" + "="*60)
    print("TEST 7: Endpoint Simulation (What /api/trends/viral-audio does)")
    print("="*60)
    
    # This simulates the exact flow in trend_signal_router.py
    platform = "instagram"
    geo = "PK"
    niche = "general"
    
    print(f"Simulating: GET /api/trends/viral-audio?platform={platform}&geo={geo}&niche={niche}")
    
    provider = ViralAudioProvider()
    tracks = await provider.get_tracks(
        platform=platform,
        location=geo,
        niche=niche,
        trend_keyword=niche,
        limit=2,
    )
    
    # Format response like the endpoint does
    response = {
        "source": "spotify_or_apple", 
        "label": "Trending Audio (charting)", 
        "recommended_tracks": tracks,
        "tracks": tracks
    }
    
    print(f"\n📦 Response:")
    print(f"   Source: {response['source']}")
    print(f"   Label: {response['label']}")
    print(f"   Track count: {len(response['recommended_tracks'])}")
    
    if response['recommended_tracks']:
        print(f"\n   Tracks:")
        for i, track in enumerate(response['recommended_tracks'], 1):
            print(f"      {i}. {track.get('track_name')} - {track.get('artist')}")
            print(f"         Source: {track.get('source')}")
        return True
    else:
        print(f"   ❌ No tracks in response!")
        return False


async def main():
    """Run all tests"""
    print("\n" + "🎵"*30)
    print("VIRAL AUDIO API DEBUG TEST SUITE")
    print("🎵"*30)
    
    results = {}
    
    # Run tests
    results['credentials'] = await test_spotify_credentials()
    
    if results['credentials']:
        results['token'] = await test_spotify_token()
        
        if results['token']:
            results['viral_tracks'] = await test_spotify_viral_tracks()
            results['search'] = await test_spotify_search()
    else:
        print("\n⚠️ Skipping Spotify tests - credentials not configured")
        results['token'] = False
        results['viral_tracks'] = False
        results['search'] = False
    
    results['provider'] = await test_viral_audio_provider()
    results['apple_rss'] = await test_apple_music_rss()
    results['endpoint'] = await test_endpoint_simulation()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if results['endpoint']:
        print("\n🎉 SUCCESS: The viral audio API should be working!")
        print("If the frontend still shows empty, check:")
        print("  1. Browser Network tab - is the request being made?")
        print("  2. Backend logs - are there any errors?")
        print("  3. Cache - try clearing browser cache or wait 6 hours")
    else:
        print("\n⚠️ WARNING: The endpoint simulation failed")
        print("This means the API will return empty results")
        
        if not results['credentials']:
            print("\n💡 FIX: Add Spotify credentials to .env:")
            print("   SPOTIFY_CLIENT_ID=your_client_id")
            print("   SPOTIFY_CLIENT_SECRET=your_client_secret")
            print("   Get them from: https://developer.spotify.com/dashboard")
        elif not results['token']:
            print("\n💡 FIX: Spotify credentials are invalid or expired")
            print("   Check your credentials at: https://developer.spotify.com/dashboard")
        elif not results['apple_rss']:
            print("\n💡 FIX: Network issue - cannot reach external APIs")
            print("   Check firewall/proxy settings")


if __name__ == "__main__":
    asyncio.run(main())
