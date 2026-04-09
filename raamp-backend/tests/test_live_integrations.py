import asyncio
import sys
import os
import json
from typing import Any, Dict

# Setup path to include the raamp-backend root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set dummy environment variables if needed, though they should be in .env
# Load .env manually for the script if not already loaded by config
from dotenv import load_dotenv
load_dotenv()

from application.services.spotify_service import SpotifyService
from application.services.viral_audio_provider import ViralAudioProvider
from presentation.routers.trend_signal_router import competitor_radar

async def test_spotify_service():
    print("\n--- Testing SpotifyService ---")
    spotify = SpotifyService()
    
    # Test Viral Tracks
    print("Fetching Viral 50 tracks for PK...")
    tracks = await spotify.get_viral_tracks(market="PK", limit=3)
    print(f"Found {len(tracks)} tracks.")
    if tracks:
        print(f"Sample: {tracks[0]['name']} by {tracks[0]['artist']} (Popularity: {tracks[0].get('popularity')})")
    
    # Test Search Tracks
    print("\nSearching for 'marketing' tracks...")
    results = await spotify.search_tracks(query="marketing", market="US", limit=2)
    print(f"Found {len(results)} search results.")
    if results:
        print(f"Sample: {results[0]['name']} by {results[0]['artist']}")
    
    return len(tracks) > 0 or len(results) > 0

async def test_viral_audio_provider():
    print("\n--- Testing ViralAudioProvider (Spotify fallback) ---")
    provider = ViralAudioProvider()
    
    print("Getting tracks for platform=instagram, location=Pakistan, niche=fashion...")
    tracks = await provider.get_tracks(
        platform="instagram",
        location="Pakistan",
        niche="fashion",
        trend_keyword="summer",
        limit=3
    )
    
    print(f"Provider returned {len(tracks)} tracks.")
    for t in tracks:
        print(f"- {t['track_name']} by {t['artist']} [Source: {t.get('source')}]")
        if t.get('image'):
            print(f"  Image: {t['image'][:50]}...")
            
    return len(tracks) > 0

async def test_competitor_radar_live():
    print("\n--- Testing Competitor Radar (SerpAPI) ---")
    
    # We mock out the cache to force a real API call
    from unittest.mock import AsyncMock, patch
    
    with patch("presentation.routers.trend_signal_router._cached_get", AsyncMock(return_value=None)):
        with patch("presentation.routers.trend_signal_router._cached_set", AsyncMock(return_value=True)):
            print("Calling competitor_radar for geo=PK, niche=Real Estate, keyword=Bahria Town...")
            result = await competitor_radar(
                geo="PK",
                niche="Real Estate",
                keyword="Bahria Town",
                current_user_email="test@raamp.ai"
            )
            
            print(f"Source: {result.get('source')}")
            influencers = result.get("influencers", [])
            print(f"Found {len(influencers)} influencers.")
            
            for inf in influencers:
                print(f"- @{inf['handle']} | {inf['url']}")
                if 'snippet' in inf:
                    print(f"  Snippet: {inf['snippet'][:80]}...")
            
            return len(influencers) > 0

async def main():
    print("🚀 STARTING LIVE INTEGRATION TESTS")
    
    spotify_ok = await test_spotify_service()
    provider_ok = await test_viral_audio_provider()
    radar_ok = await test_competitor_radar_live()
    
    print("\n--- TEST SUMMARY ---")
    print(f"Spotify Service:      {'✅ PASSED' if spotify_ok else '❌ FAILED'}")
    print(f"Viral Audio Provider: {'✅ PASSED' if provider_ok else '❌ FAILED'}")
    print(f"Competitor Radar:     {'✅ PASSED' if radar_ok else '❌ FAILED'}")

if __name__ == "__main__":
    asyncio.run(main())
