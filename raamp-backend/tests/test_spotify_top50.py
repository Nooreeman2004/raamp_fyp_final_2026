"""
Test Spotify Top 50 for Asia/Pakistan
Run with: python raamp-backend/tests/test_spotify_top50.py
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from application.services.spotify_service import SpotifyService
from application.services.viral_audio_provider import ViralAudioProvider


async def test_spotify_markets():
    """Test Spotify for different Asian markets"""
    print("\n" + "="*60)
    print("SPOTIFY TOP 50 TEST - ASIAN MARKETS")
    print("="*60)
    
    spotify = SpotifyService()
    
    # Check if credentials are configured
    if not spotify.client_id or not spotify.client_secret:
        print("\n❌ Spotify credentials not configured")
        print("   Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env")
        return
    
    print(f"\n✅ Spotify credentials configured")
    
    # Test different Asian markets
    markets = [
        ("PK", "Pakistan"),
        ("IN", "India"),
        ("ID", "Indonesia"),
        ("PH", "Philippines"),
        ("TH", "Thailand"),
        ("US", "United States (control)"),
    ]
    
    for market_code, market_name in markets:
        print(f"\n{'='*60}")
        print(f"Testing: {market_name} ({market_code})")
        print(f"{'='*60}")
        
        try:
            tracks = await spotify.get_viral_tracks(market=market_code, limit=3)
            
            if tracks:
                print(f"✅ Got {len(tracks)} tracks:")
                for i, track in enumerate(tracks, 1):
                    print(f"   {i}. {track['name']} - {track['artist']}")
                    print(f"      Popularity: {track.get('popularity', 'N/A')}")
                    if track.get('url'):
                        print(f"      URL: {track['url']}")
            else:
                print(f"❌ No tracks returned for {market_name}")
                
        except Exception as e:
            print(f"❌ Error: {e}")


async def test_viral_audio_provider():
    """Test the full ViralAudioProvider with fallback logic"""
    print("\n" + "="*60)
    print("VIRAL AUDIO PROVIDER TEST")
    print("="*60)
    
    provider = ViralAudioProvider()
    
    test_cases = [
        ("instagram", "PK", "fashion"),
        ("instagram", "IN", "food"),
        ("instagram", "GLOBAL", "general"),
    ]
    
    for platform, location, niche in test_cases:
        print(f"\n{'='*60}")
        print(f"Testing: platform={platform}, location={location}, niche={niche}")
        print(f"{'='*60}")
        
        try:
            tracks = await provider.get_tracks(
                platform=platform,
                location=location,
                niche=niche,
                trend_keyword=niche,
                limit=2
            )
            
            if tracks:
                print(f"✅ Got {len(tracks)} tracks:")
                for i, track in enumerate(tracks, 1):
                    print(f"   {i}. {track['track_name']} - {track['artist']}")
                    print(f"      Source: {track.get('source', 'unknown')}")
                    print(f"      Confidence: {track.get('confidence', 0):.2f}")
            else:
                print(f"❌ No tracks returned")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


async def main():
    print("\n" + "🎵"*30)
    print("SPOTIFY & VIRAL AUDIO TEST SUITE")
    print("🎵"*30)
    
    # Test 1: Direct Spotify API
    await test_spotify_markets()
    
    # Test 2: Full provider with fallback
    await test_viral_audio_provider()
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    print("""
If you see tracks for Asian markets (PK, IN, etc.):
✅ The fix is working!

If you see "No tracks returned":
- Check Spotify credentials in .env
- Check internet connection
- Spotify API might be rate limited
""")


if __name__ == "__main__":
    asyncio.run(main())
