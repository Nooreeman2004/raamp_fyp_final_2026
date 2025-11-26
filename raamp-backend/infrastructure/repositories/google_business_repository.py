from typing import Optional
from infrastructure.database.models.google_business_location_model import GoogleBusinessLocationModel


class GoogleBusinessRepository:
    async def find_by_user_id(self, user_id: str) -> Optional[GoogleBusinessLocationModel]:
        return await GoogleBusinessLocationModel.find_one(GoogleBusinessLocationModel.user_id == user_id)

    async def create_or_update(self, user_id: str, business_name: str = None, address: str = None, latitude: float = None, longitude: float = None, place_id: str = None) -> GoogleBusinessLocationModel:
        doc = await self.find_by_user_id(user_id)
        if not doc:
            doc = GoogleBusinessLocationModel(user_id=user_id, business_name=business_name, address=address, latitude=latitude, longitude=longitude, place_id=place_id)
            await doc.insert()
            return doc
        if business_name is not None:
            doc.business_name = business_name
        if address is not None:
            doc.address = address
        if latitude is not None:
            doc.latitude = latitude
        if longitude is not None:
            doc.longitude = longitude
        if place_id is not None:
            doc.place_id = place_id
        doc.updated_at = __import__('datetime').datetime.utcnow()
        await doc.save()
        return doc
