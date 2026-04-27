from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx
from application.services.spotify_service import SpotifyService

logger = logging.getLogger(__name__)


@dataclass
class ViralAudioTrack:
    platform: str
    track_name: str
    artist: str
    url: Optional[str] = None
    source: str = "apple_music_rss"
    confidence: float = 0.5
    image: Optional[str] = None


class ViralAudioProvider:
    """
    Provider that returns *verified* track + artist strings from a real feed.

    We intentionally do not claim these are "currently viral on TikTok/Instagram" unless we
    integrate those proprietary sources; instead, we use verified charting tracks as candidates
    and map them to platform vibe heuristics.
    """

    def __init__(self, client: Optional[httpx.AsyncClient] = None) -> None:
        self._client = client

    @staticmethod
    def _storefront(location: str) -> str:
        loc = (location or "").strip().lower()
        # Apple storefront codes are typically 2-letter country codes.
        if len(loc) == 2:
            return loc
        # common fallbacks
        if "pak" in loc:
            return "pk"
        if "usa" in loc or "united states" in loc:
            return "us"
        if "uk" in loc or "united kingdom" in loc:
            return "gb"
        return "us"

    @staticmethod
    def _genre_score(platform: str, genres: List[str]) -> float:
        g = " ".join([str(x or "").lower() for x in (genres or [])])
        p = (platform or "").lower()
        if p == "tiktok":
            # energetic / fast-paced
            hits = ["dance", "hip-hop", "rap", "pop", "electronic", "afrobeats"]
        else:
            # aesthetic / smooth
            hits = ["r&b", "soul", "alternative", "indie", "ambient", "lo-fi", "electronic", "singer-songwriter"]
        return sum(1.0 for h in hits if h in g)

    async def get_tracks(
        self,
        *,
        platform: str,
        location: str,
        niche: str,
        trend_keyword: str,
        limit: int = 2,
    ) -> List[Dict[str, Any]]:
        logger.info(f"🎵 ViralAudioProvider.get_tracks called: platform={platform}, location={location}, niche={niche}, limit={limit}")
        
        # Evergreen fallback (defined early to ensure it's always available)
        evergreen = [
            {"name": "Cruel Summer", "artist": "Taylor Swift", "image": "https://i.scdn.co/image/ab67616d0000b273e787cffec20aa2a0a65f3655"},
            {"name": "Paint The Town Red", "artist": "Doja Cat", "image": "https://i.scdn.co/image/ab67616d0000b273760ef164e622b7a66b553655"},
            {"name": "greedy", "artist": "Tate McRae", "image": "https://i.scdn.co/image/ab67616d0000b27322fd492157077a5e985f958a"},
            {"name": "Water", "artist": "Tyla", "image": "https://i.scdn.co/image/ab67616d0000b27339893645398686f99a53f090"},
        ]
        
        try:
            # Common headers to avoid being blocked by RSS feeds
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json",
            }

            # --- STRATEGY 1: Spotify (Preferred if keys available) ---
            spotify = SpotifyService()
            logger.info(f"🎵 Spotify credentials check: client_id={'SET' if spotify.client_id else 'MISSING'}, client_secret={'SET' if spotify.client_secret else 'MISSING'}")
            if spotify.client_id and spotify.client_secret:
                try:
                    # Use simplified location code for Spotify markets
                    market = self._storefront(location).upper()
                    # 1. Try to get viral tracks for the market
                    s_tracks = await spotify.get_viral_tracks(market=market, limit=limit)
                    
                    # 2. If niche/keyword provided, search for specific alignment
                    if niche or trend_keyword:
                        search_q = f"{trend_keyword or niche}"
                        aligned = await spotify.search_tracks(query=search_q, market=market, limit=limit)
                        s_tracks = (s_tracks or []) + (aligned or [])
                    
                    if s_tracks:
                        logger.info(f"✅ Spotify returned {len(s_tracks)} tracks")
                        p = (platform or "").strip().lower()
                        results = []
                        seen = set()
                        
                        # Sort by popularity (descending)
                        s_tracks.sort(key=lambda x: x.get("popularity", 0), reverse=True)
                        
                        for st in s_tracks:
                            key = f"{st['name']}|{st['artist']}".lower()
                            if key in seen: continue
                            seen.add(key)
                            
                            results.append(
                                ViralAudioTrack(
                                    platform=p or "instagram",
                                    track_name=st["name"],
                                    artist=st["artist"],
                                    url=st["url"],
                                    source="spotify_web_api",
                                    confidence=min(0.98, 0.6 + (float(st.get("popularity", 50)) / 200)),
                                    image=st.get("image")
                                ).__dict__
                            )
                        
                        if results:
                            logger.info(f"✅ Returning {len(results)} Spotify tracks")
                            return results[:limit]
                    else:
                        logger.warning("⚠️ Spotify returned no tracks, falling back to Apple Music RSS")
                except Exception as e:
                    logger.warning(f"❌ Spotify lookup failed: {e}, falling back to Apple Music RSS")

            # --- STRATEGY 2: Apple Music RSS (Reliable Global Analytics) ---
            storefront = self._storefront(location)
            logger.info(f"🍎 Trying Apple Music RSS for storefront: {storefront}")
            url = f"https://rss.applemarketingtools.com/api/v2/{storefront}/music/most-played/50/songs.json"

            async with httpx.AsyncClient(timeout=5.0, headers=headers) as client:
                try:
                    r = await client.get(url)
                    if r.status_code != 200:
                        raise httpx.HTTPStatusError(f"Status {r.status_code}", request=r.request, response=r)
                    data = r.json()
                except Exception:
                    # Storefront fallback (e.g. PK -> US)
                    if storefront == "pk":
                        fallback = "us"
                        fb_url = f"https://rss.applemarketingtools.com/api/v2/{fallback}/music/most-played/50/songs.json"
                        try:
                            rr = await client.get(fb_url)
                            rr.raise_for_status()
                            data = rr.json()
                            storefront = fallback
                        except Exception:
                            data = {}
                    else:
                        data = {}

                results = []
                feed = (data or {}).get("feed") or {}
                items = feed.get("results") or []
                
                # If still empty, try one last time with US if we haven't already
                if not items and storefront != "us":
                    try:
                        fb_url = f"https://rss.applemarketingtools.com/api/v2/us/music/most-played/20/songs.json"
                        rr = await client.get(fb_url)
                        if rr.status_code == 200:
                            data = rr.json()
                            items = (data.get("feed") or {}).get("results") or []
                    except Exception:
                        pass

                p = (platform or "").strip().lower()
                scored = []
                for it in items:
                    try:
                        name = str(it.get("name") or "").strip()
                        artist = str(it.get("artistName") or "").strip()
                        if not name or not artist: continue
                        
                        genres = [str(gg["name"]) for gg in (it.get("genres") or []) if isinstance(gg, dict) and gg.get("name")]
                        it_url = it.get("url")
                        
                        score = self._genre_score(p, genres)
                        text = f"{name} {artist} {' '.join(genres)}".lower()
                        for w in [(niche or ""), (trend_keyword or "")]:
                            ww = str(w).strip().lower()
                            if ww and ww in text:
                                score += 1.0

                        scored.append((score, name, artist, it_url))
                    except Exception:
                        continue

                scored.sort(key=lambda t: t[0], reverse=True)
                for s, name, artist, it_url in scored[:limit]:
                    results.append(
                        ViralAudioTrack(
                            platform=p or "instagram",
                            track_name=name,
                            artist=artist,
                            url=str(it_url) if it_url else None,
                            confidence=min(0.95, 0.5 + (float(s) * 0.1)),
                            source="apple_music_rss"
                        ).__dict__
                    )

                if results:
                    logger.info(f"✅ Returning {len(results)} Apple Music tracks")
                    return results

        except Exception as e:
            logger.error(f"❌ Error in get_tracks: {e}", exc_info=True)

        # --- STRATEGY 3: Evergreen Fallback (Never return empty) ---
        # If all API calls fail, provide curated 'evergreen' trending tracks to keep UI premium
        logger.warning("⚠️ All strategies failed, using evergreen fallback")
        fallback_results = []
        for track in evergreen[:limit]:
            fallback_results.append(
                ViralAudioTrack(
                    platform=platform or "instagram",
                    track_name=track["name"],
                    artist=track["artist"],
                    image=track["image"],
                    source="evergreen_fallback",
                    confidence=0.85
                ).__dict__
            )
        logger.info(f"✅ Returning {len(fallback_results)} evergreen fallback tracks")
        return fallback_results


