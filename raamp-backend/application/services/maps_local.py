from typing import List, Dict, Any
import httpx
from config import settings


async def query_places(query: str, limit: int = 5, type: str = None) -> List[Dict[str, Any]]:
    """Query Google Places Text Search API for places matching `query`.

    Returns a list of place dicts with keys: name, address, place_id.
    If `GOOGLE_MAPS_API_KEY` is not set, returns an empty list.
    """
    api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', None)
    if not api_key:
        # Return empty list in dev if no API key
        return []

    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {"query": query, "key": api_key}
    if type:
        # Google Places textsearch supports an optional type filter
        params["type"] = type
    async with httpx.AsyncClient() as client:
        r = await client.get(url, params=params, timeout=8.0)
        r.raise_for_status()
        data = r.json()
        results = data.get('results', [])[:limit]
        out = []
        for p in results:
            loc = p.get('geometry', {}).get('location', {})
            out.append({
                'name': p.get('name'),
                'address': p.get('formatted_address') or p.get('vicinity'),
                'place_id': p.get('place_id'),
                'latitude': loc.get('lat'),
                'longitude': loc.get('lng'),
            })
        return out


async def show_on_map(place_id: str, query: str = None) -> Dict[str, Any]:
    """Return basic place details (geometry) and an embeddable maps URL for preview.

    If API key is missing, returns a minimal structure that frontend can use.
    """
    api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', None)
    if not api_key:
        return {
            'place_id': place_id,
            'preview_url': f'https://www.google.com/maps/search/?api=1&query=place_id:{place_id}',
            'name': query or '',
            'latitude': None,
            'longitude': None,
        }

    details_url = 'https://maps.googleapis.com/maps/api/place/details/json'
    params = {'place_id': place_id, 'key': api_key, 'fields': 'name,formatted_address,geometry'}
    async with httpx.AsyncClient() as client:
        r = await client.get(details_url, params=params, timeout=8.0)
        r.raise_for_status()
        data = r.json()
        result = data.get('result', {})
        loc = result.get('geometry', {}).get('location', {})
        lat = loc.get('lat')
        lng = loc.get('lng')
        return {
            'place_id': place_id,
            'preview_url': f'https://www.google.com/maps/search/?api=1&query=place_id:{place_id}',
            'name': result.get('name') or query,
            'address': result.get('formatted_address'),
            'latitude': lat,
            'longitude': lng,
        }
