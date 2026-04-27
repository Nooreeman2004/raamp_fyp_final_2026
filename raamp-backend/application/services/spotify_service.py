import logging
import base64
import httpx
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from config import config

logger = logging.getLogger(__name__)

class SpotifyService:
    """
    Service for interacting with Spotify Web API to fetch trending musical signals.
    Uses Client Credentials Flow (no user login required).
    """

    MARKET_NAMES = {
        "PK": "Pakistan",
        "US": "USA",
        "GB": "UK",
        "AE": "UAE",
        "IN": "India",
        "CA": "Canada",
        "AU": "Australia",
        "SA": "Saudi Arabia",
        "DE": "Germany",
        "FR": "France",
        "BR": "Brazil",
        "JP": "Japan"
    }

    def __init__(self):
        self.client_id = config.SPOTIFY_CLIENT_ID
        self.client_secret = config.SPOTIFY_CLIENT_SECRET
        self.token_url = "https://accounts.spotify.com/api/token"
        self.api_base_url = "https://api.spotify.com/v1"
        self._access_token: Optional[str] = None
        self._token_expiry: float = 0  # Unix timestamp
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create a shared HTTP client with connection pooling"""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=10.0,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
        return self._http_client

    async def close(self):
        """Close the HTTP client (call this on shutdown)"""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    async def _get_access_token(self) -> Optional[str]:
        """
        Fetch or reuse cached access token.
        Tokens are valid for 3600 seconds, we reuse with 60s buffer.
        """
        # Reuse token if still valid (with 60s buffer)
        if self._access_token and time.time() < self._token_expiry - 60:
            logger.debug("♻️ Reusing cached Spotify token")
            return self._access_token
        
        if not self.client_id or not self.client_secret:
            logger.warning("Spotify credentials missing in config.")
            return None

        logger.info("🔑 Fetching new Spotify access token")
        auth_str = f"{self.client_id}:{self.client_secret}"
        auth_b64 = base64.b64encode(auth_str.encode()).decode()

        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "client_credentials"}

        client = await self._get_http_client()
        try:
            response = await client.post(self.token_url, headers=headers, data=data)
            response.raise_for_status()
            token_data = response.json()
            self._access_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 3600)
            self._token_expiry = time.time() + expires_in
            logger.info(f"✅ Got Spotify token (expires in {expires_in}s)")
            return self._access_token
        except Exception as e:
            logger.error(f"Failed to get Spotify access token: {e}")
            return None

    async def get_viral_tracks(self, market: str = "US", limit: int = 5) -> List[Dict[str, Any]]:
        """
        Fetch trending tracks from Spotify charts.
        Uses multiple strategies: Top 50 playlists, Browse API, and search fallback.
        """
        logger.info(f"🎵 SpotifyService.get_viral_tracks: market={market}, limit={limit}")
        token = await self._get_access_token()
        if not token:
            logger.error("❌ Failed to get Spotify access token")
            return []

        headers = {"Authorization": f"Bearer {token}"}
        client = await self._get_http_client()
        
        try:
            # STRATEGY 1: Try Browse API for featured playlists (most reliable)
            logger.info(f"🔍 Strategy 1: Trying Browse API for {market}")
            try:
                browse_params = {
                    "country": market.upper(),
                    "limit": 1
                }
                browse_res = await client.get(
                    f"{self.api_base_url}/browse/featured-playlists",
                    headers=headers,
                    params=browse_params
                )
                if browse_res.status_code == 200:
                    playlists = browse_res.json().get("playlists", {}).get("items", [])
                    if playlists and playlists[0]:
                        playlist_id = playlists[0].get("id")
                        playlist_name = playlists[0].get("name", "Unknown")
                        logger.info(f"✅ Found featured playlist: {playlist_name}")
                        
                        # Get tracks from this playlist
                        tracks_res = await client.get(
                            f"{self.api_base_url}/playlists/{playlist_id}/tracks",
                            headers=headers,
                            params={"limit": limit}
                        )
                        if tracks_res.status_code == 200:
                            items = tracks_res.json().get("items", [])
                            if items:
                                return self._parse_playlist_tracks(items)
            except Exception as e:
                logger.info(f"⚠️ Browse API failed: {e}")
            
            # STRATEGY 2: Search for Top 50 playlists
            logger.info(f"🔍 Strategy 2: Searching for Top 50 playlists")
            market_display = self.MARKET_NAMES.get(market.upper(), market.upper())
            search_queries = [
                f"Top 50 - {market_display}",
                f"Top Songs - {market_display}",
                f"Top 50 {market.upper()}",
                "Top 50 - Global",
                "Today's Top Hits",
            ]

            for query in search_queries:
                try:
                    search_params = {"q": query, "type": "playlist", "limit": 1}
                    search_res = await client.get(
                        f"{self.api_base_url}/search",
                        headers=headers,
                        params=search_params
                    )
                    if search_res.status_code == 200:
                        playlists = search_res.json().get("playlists", {}).get("items", [])
                        if playlists and playlists[0]:
                            playlist_id = playlists[0].get("id")
                            playlist_name = playlists[0].get("name", "Unknown")
                            logger.info(f"✅ Found playlist: {playlist_name}")
                            
                            # Try to get tracks (may fail with 403 for private playlists)
                            tracks_res = await client.get(
                                f"{self.api_base_url}/playlists/{playlist_id}/tracks",
                                headers=headers,
                                params={"limit": limit}
                            )
                            if tracks_res.status_code == 200:
                                items = tracks_res.json().get("items", [])
                                if items:
                                    return self._parse_playlist_tracks(items)
                except Exception as e:
                    logger.debug(f"Playlist query '{query}' failed: {e}")
                    continue
            
            # STRATEGY 3: Market-aware search for popular tracks
            logger.info(f"🔍 Strategy 3: Market-aware search for {market}")
            current_year = datetime.now().year
            market_display = self.MARKET_NAMES.get(market.upper(), market.upper())
            
            # Try multiple search queries with market context
            search_terms = [
                f"top hits {market_display} {current_year}",
                f"popular songs {market_display}",
                f"trending {market_display}",
                f"top hits {current_year}",  # Fallback without market
            ]
            
            for search_term in search_terms:
                try:
                    tracks = await self.search_tracks(query=search_term, market=market, limit=limit)
                    if tracks:
                        logger.info(f"✅ Found {len(tracks)} tracks via search: '{search_term}'")
                        return tracks
                except Exception as e:
                    logger.debug(f"Search term '{search_term}' failed: {e}")
                    continue
            
            logger.warning(f"❌ All strategies failed for market {market}")
            return []

        except Exception as e:
            logger.error(f"Error fetching Spotify trending tracks: {e}", exc_info=True)
            return []
    
    def _parse_playlist_tracks(self, items: List[Dict]) -> List[Dict[str, Any]]:
        """Parse playlist track items into standardized format"""
        results = []
        for item in items:
            if not item:
                continue
            track = item.get("track")
            if not track:
                continue
            
            # Safety check for album and images
            album = track.get("album")
            images = album.get("images") if album else []
            image_url = images[0].get("url") if images and len(images) > 0 else None
            
            results.append({
                "name": track.get("name", "Unknown"),
                "artist": ", ".join([a.get("name", "Unknown") for a in track.get("artists", [])]),
                "url": track.get("external_urls", {}).get("spotify"),
                "preview_url": track.get("preview_url"),
                "popularity": track.get("popularity", 0),
                "image": image_url
            })
        return results

    async def search_tracks(self, query: str, market: str = "US", limit: int = 5) -> List[Dict[str, Any]]:
        """Search for tracks matching a keyword or niche."""
        token = await self._get_access_token()
        if not token:
            return []

        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "q": query,
            "type": "track",
            "market": market,
            "limit": limit
        }

        client = await self._get_http_client()
        try:
            res = await client.get(f"{self.api_base_url}/search", headers=headers, params=params)
            res.raise_for_status()
            tracks = res.json().get("tracks", {}).get("items", [])
            
            results = []
            for track in tracks:
                if not track: continue
                album = track.get("album")
                images = album.get("images") if album else []
                image_url = images[0].get("url") if images and len(images) > 0 else None
                
                results.append({
                    "name": track.get("name", "Unknown"),
                    "artist": ", ".join([a.get("name", "Unknown") for a in track.get("artists", [])]),
                    "url": track.get("external_urls", {}).get("spotify"),
                    "preview_url": track.get("preview_url"),
                    "popularity": track.get("popularity", 0),
                    "image": image_url
                })
            return results
        except Exception as e:
            logger.error(f"Error searching Spotify tracks: {e}", exc_info=True)
            return []
