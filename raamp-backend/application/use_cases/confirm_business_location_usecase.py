from typing import Dict, Any, Optional
from application.services.maps_local import show_on_map


async def confirm_business_location_usecase(place_id: str, name: Optional[str] = None) -> Dict[str, Any]:
    if not place_id or not place_id.strip():
        raise ValueError("place_id is required")
    preview = await show_on_map(place_id=place_id, query=name)
    return preview
