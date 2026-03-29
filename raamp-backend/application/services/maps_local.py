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
        return []

    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {"query": query, "key": api_key}
    if type:
        params["type"] = type
    
    async with httpx.AsyncClient() as client:
        try:
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
        except Exception as e:
            print(f"Maps query error: {e}")
            return []


async def autocomplete_places(query: str, limit: int = 5, type: str = None) -> List[Dict[str, Any]]:
    """Query Google Places Autocomplete API for suggestions matching `query`.
    
    Standard autocomplete returns predictions which are better for 'as you type' searches.
    """
    api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', None)
    if not api_key:
        return []

    url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
    # types: 'establishment' is often what people want for businesses
    params = {"input": query, "key": api_key, "types": type}
    
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(url, params=params, timeout=5.0)
            r.raise_for_status()
            data = r.json()
            predictions = data.get('predictions', [])[:limit]
            
            # Autocomplete doesn't return lat/lng, so we return a list of predictions
            # The frontend will then have to call details/confirm to get coordinates.
            out = []
            for p in predictions:
                out.append({
                    'name': p.get('structured_formatting', {}).get('main_text') or p.get('description'),
                    'address': p.get('description'),
                    'place_id': p.get('place_id'),
                    # Coordinates are NOT available in autocomplete results
                    'latitude': None, 
                    'longitude': None,
                })
            return out
        except Exception as e:
            print(f"Maps autocomplete error: {e}")
            return []


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
        try:
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
        except Exception as e:
            print(f"Maps details error: {e}")
            return {
                'place_id': place_id,
                'name': query or '',
                'latitude': None,
                'longitude': None,
            }
