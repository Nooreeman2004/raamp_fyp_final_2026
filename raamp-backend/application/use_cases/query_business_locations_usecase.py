from typing import List, Dict
from application.services.maps_local import query_places


async def query_business_locations_usecase(query: str, limit: int = 5) -> List[Dict]:
    if not query or not query.strip():
        raise ValueError("Query must be a non-empty string")
    places = await query_places(query=query, limit=limit)
    # return simple DTOs
    return [{'name': p.get('name'), 'address': p.get('address'), 'place_id': p.get('place_id')} for p in places]
