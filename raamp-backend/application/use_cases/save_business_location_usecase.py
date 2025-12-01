from typing import Dict
from infrastructure.repositories.google_business_repository import GoogleBusinessRepository
from infrastructure.repositories.user_repository_impl import UserRepository


async def save_business_location_usecase(user_email: str, place_id: str, name: str, address: str, latitude: float = None, longitude: float = None) -> Dict:
    if not place_id or not place_id.strip():
        raise ValueError("place_id is required")
    if not user_email:
        raise ValueError("user_email is required")

    g_repo = GoogleBusinessRepository()
    user_repo = UserRepository()

    # Persist the google business location with coordinates
    doc = await g_repo.create_or_update(user_email, business_name=name, address=address, place_id=place_id, latitude=latitude, longitude=longitude)
    # update user flags
    await user_repo.update_connection_flags(user_email, google_maps=True)

    return {
        'message': 'Google Maps business connected',
        'place_id': doc.place_id,
        'name': doc.business_name,
        'address': doc.address,
    }
