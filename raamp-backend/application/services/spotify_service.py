import logging
import base64
import httpx
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

    async def _get_access_token(self) -> Optional[str]:
        """Fetch a new access token using client credentials."""
        if not self.client_id or not self.client_secret:
            logger.warning("Spotify credentials missing in config.")
            return None

        auth_str = f"{self.client_id}:{self.client_secret}"
        auth_b64 = base64.b64encode(auth_str.encode()).decode()

        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "client_credentials"}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.token_url, headers=headers, data=data)
                response.raise_for_status()
                token_data = response.json()
                self._access_token = token_data.get("access_token")
                return self._access_token
            except Exception as e:
                logger.error(f"Failed to get Spotify access token: {e}")
                return None

    async def get_viral_tracks(self, market: str = "US", limit: int = 5) -> List[Dict[str, Any]]:
        """
        Fetch viral tracks from Spotify. 
        Since there is no direct 'viral' endpoint, we search for 'Viral 50' playlists 
        or use the browse categories.
        """
        token = await self._get_access_token()
        if not token:
            return []

        headers = {"Authorization": f"Bearer {token}"}
        
        # Strategy: Search for the 'Viral 50' playlist for the specific market
        market_display = self.MARKET_NAMES.get(market.upper(), market.upper())
        query = f"Viral 50 - {market_display}"
        search_params = {
            "q": query,
            "type": "playlist",
            "limit": 1
        }

        async with httpx.AsyncClient() as client:
            try:
                # 1. Find the Viral 50 playlist ID
                search_res = await client.get(f"{self.api_base_url}/search", headers=headers, params=search_params)
                search_res.raise_for_status()
                playlists = search_res.json().get("playlists", {}).get("items", [])
                
                if not playlists:
                    # Try just with market code
                    search_params["q"] = f"Viral 50 - {market.upper()}"
                    search_res = await client.get(f"{self.api_base_url}/search", headers=headers, params=search_params)
                    playlists = search_res.json().get("playlists", {}).get("items", [])
                
                if not playlists:
                    # Fallback: search for global viral 50
                    search_params["q"] = "Viral 50 - Global"
                    search_res = await client.get(f"{self.api_base_url}/search", headers=headers, params=search_params)
                    playlists = search_res.json().get("playlists", {}).get("items", [])

                if not playlists or not playlists[0]:
                    return []

                playlist_id = playlists[0].get("id")
                if not playlist_id:
                    return []
                
                # 2. Get tracks from the playlist
                tracks_res = await client.get(f"{self.api_base_url}/playlists/{playlist_id}/tracks", headers=headers, params={"limit": limit})
                tracks_res.raise_for_status()
                items = tracks_res.json().get("items", [])
                
                results = []
                for item in items:
                    if not item: continue
                    track = item.get("track")
                    if not track: continue
                    
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

            except Exception as e:
                logger.error(f"Error fetching Spotify viral tracks: {e}", exc_info=True)
                return []

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

        async with httpx.AsyncClient() as client:
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
