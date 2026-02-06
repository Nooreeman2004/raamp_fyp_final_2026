"""
Google Business Repository - Now uses BusinessModel as Single Source of Truth
=============================================================================

This repository provides backward-compatible methods for Google Business Location
operations while using BusinessModel as the underlying storage.
"""
from typing import Optional
from datetime import datetime
from infrastructure.database.models.business_model import BusinessModel


class GoogleBusinessRepository:
    """
    Repository for Google Business Location data.
    
    Now uses BusinessModel as the single source of truth for location data.
    Methods maintain backward compatibility with existing code.
    """
    
    async def find_by_user_id(self, user_id: str) -> Optional[BusinessModel]:
        """Find business by user ID (backward compatible)."""
        return await BusinessModel.find_one(BusinessModel.user_id == user_id)

    async def create_or_update(
        self, 
        user_id: str, 
        business_name: str = None, 
        address: str = None, 
        latitude: float = None, 
        longitude: float = None, 
        place_id: str = None
    ) -> BusinessModel:
        """
        Create or update Google Business location data in BusinessModel.
        
        This method maintains backward compatibility while storing data
        in the consolidated BusinessModel.
        """
        doc = await self.find_by_user_id(user_id)
        
        if not doc:
            # Create new business document
            doc = BusinessModel(
                user_id=user_id,
                business_name=business_name,
                business_address=address,
                latitude=latitude,
                longitude=longitude,
                google_place_id=place_id
            )
            await doc.insert()
            return doc
        
        # Update existing document
        if business_name is not None:
            doc.business_name = business_name
        if address is not None:
            doc.business_address = address
        if latitude is not None:
            doc.latitude = latitude
        if longitude is not None:
            doc.longitude = longitude
        if place_id is not None:
            doc.google_place_id = place_id
        
        doc.updated_at = datetime.utcnow()
        await doc.save()
        return doc
    
    async def get_location_data(self, user_id: str) -> Optional[dict]:
        """
        Get location data in a standardized format.
        
        Returns dict with keys matching the old GoogleBusinessLocationModel
        for backward compatibility.
        """
        doc = await self.find_by_user_id(user_id)
        if not doc:
            return None
        
        return {
            "user_id": doc.user_id,
            "business_name": doc.business_name,
            "address": doc.business_address,
            "latitude": doc.latitude,
            "longitude": doc.longitude,
            "place_id": doc.google_place_id,
        }
