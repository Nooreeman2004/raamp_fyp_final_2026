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
        # --- STRATEGY 1: Spotify (Preferred if keys available) ---
        spotify = SpotifyService()
        if spotify.client_id and spotify.client_secret:
            try:
                # Use simplified location code for Spotify markets
                market = self._storefront(location).upper()
                # 1. Try to get viral tracks for the market
                s_tracks = await spotify.get_viral_tracks(market=market, limit=limit)
                
                # 2. If niche/keyword provided, search for specific alignment
                if niche or trend_keyword:
                    search_q = f"{trend_keyword or niche} {niche}"
                    aligned = await spotify.search_tracks(query=search_q, market=market, limit=limit)
                    # Merge and sort by popularity if possible
                    s_tracks = (s_tracks + aligned)
                
                if s_tracks:
                    # Dedupe and score
                    p = (platform or "").strip().lower()
                    results = []
                    seen = set()
                    
                    # Sort by popularity (descending)
                    s_tracks.sort(key=lambda x: x.get("popularity", 0), reverse=True)
                    
                    for st in s_tracks:
                        key = f"{st['name']}|{st['artist']}".lower()
                        if key in seen: continue
                        seen.add(key)
                        
                        # Apply vibe scoring
                        # In Spotify case, we assume the provider is already giving us relevant hits
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
                        return results[:limit]
            except Exception as e:
                logger.warning(f"Spotify lookup failed, falling back to Apple Music: {e}")

        # --- STRATEGY 2: Apple Music RSS (Reliable Global Analytics) ---
        storefront = self._storefront(location)
        url = f"https://rss.applemarketingtools.com/api/v2/{storefront}/music/most-played/50/songs.json"

        close_client = False
        client = self._client
        if client is None:
            client = httpx.AsyncClient(timeout=10.0)
            close_client = True

        try:
            r = await client.get(url)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            # PK storefront is frequently unavailable/empty; fall back to a global-ish chart (US)
            # so UI doesn't look broken for PK.
            if storefront == "pk":
                fallback = "us"
                fb_url = f"https://rss.applemarketingtools.com/api/v2/{fallback}/music/most-played/50/songs.json"
                logger.info(
                    "viral_audio_provider_pk_fallback storefront=%s -> %s err=%s",
                    storefront,
                    fallback,
                    str(e)[:200],
                )
                try:
                    rr = await client.get(fb_url)
                    rr.raise_for_status()
                    data = rr.json()
                    storefront = fallback
                except Exception as ee:
                    logger.warning("viral_audio_provider_failed storefront=%s err=%s", fallback, str(ee))
                    return []
            else:
                logger.warning("viral_audio_provider_failed storefront=%s err=%s", storefront, str(e))
                return []
        finally:
            if close_client:
                try:
                    await client.aclose()
                except Exception:
                    pass

        results = []
        feed = (data or {}).get("feed") or {}
        items = feed.get("results") or []
        if storefront == "pk" and not items:
            fallback = "us"
            fb_url = f"https://rss.applemarketingtools.com/api/v2/{fallback}/music/most-played/50/songs.json"
            logger.info("viral_audio_provider_pk_empty_feed_fallback storefront=%s -> %s", storefront, fallback)
            try:
                rr = await client.get(fb_url)
                rr.raise_for_status()
                data2 = rr.json()
                feed2 = (data2 or {}).get("feed") or {}
                items = feed2.get("results") or []
                storefront = fallback
            except Exception as ee:
                logger.warning("viral_audio_provider_failed storefront=%s err=%s", fallback, str(ee))
        p = (platform or "").strip().lower()

        scored = []
        for it in items:
            try:
                name = str(it.get("name") or "").strip()
                artist = str(it.get("artistName") or "").strip()
                if not name or not artist:
                    continue
                genres = []
                for gg in (it.get("genres") or []):
                    if isinstance(gg, dict) and gg.get("name"):
                        genres.append(str(gg["name"]))
                it_url = it.get("url")

                # heuristic scoring: platform vibe + light relevance to niche/keyword if present
                score = self._genre_score(p, genres)
                text = f"{name} {artist} {' '.join(genres)}".lower()
                for w in [(niche or ""), (trend_keyword or "")]:
                    ww = str(w).strip().lower()
                    if ww and ww in text:
                        score += 0.5

                scored.append((score, name, artist, it_url))
            except Exception:
                continue

        scored.sort(key=lambda t: t[0], reverse=True)
        for s, name, artist, it_url in scored[: max(1, int(limit))]:
            results.append(
                ViralAudioTrack(
                    platform=p or "instagram",
                    track_name=name,
                    artist=artist,
                    url=str(it_url) if it_url else None,
                    confidence=min(0.95, 0.5 + (float(s) * 0.1)),
                ).__dict__
            )
        return results

