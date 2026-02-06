"""
Geo Intent Simulation Repository
Handles CRUD operations for geo_intent_simulations collection
"""
from typing import Optional, List
from datetime import datetime
from infrastructure.database.models.geo_intent_simulation_model import GeoIntentSimulationModel


class GeoIntentSimulationRepository:
    """Repository for geo-intent simulation operations"""
    
    async def create(
        self,
        request_id: str,
        user_id: str,
        hot_regions: List[dict],
        total_regions: int,
        simulation_params: dict = None,
        analysis_metadata: dict = None
    ) -> GeoIntentSimulationModel:
        """Create a new geo-intent simulation record"""
        simulation = GeoIntentSimulationModel(
            request_id=request_id,
            user_id=user_id,
            hot_regions=hot_regions,
            total_regions=total_regions,
            simulation_params=simulation_params or {},
            analysis_metadata=analysis_metadata or {}
        )
        await simulation.insert()
        return simulation
    
    async def get_by_request_id(self, request_id: str) -> Optional[GeoIntentSimulationModel]:
        """Get simulation by request ID"""
        return await GeoIntentSimulationModel.find_one(
            GeoIntentSimulationModel.request_id == request_id
        )
    
    async def get_recent_by_user(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[GeoIntentSimulationModel]:
        """Get recent simulations for a user"""
        return await GeoIntentSimulationModel.find(
            GeoIntentSimulationModel.user_id == user_id
        ).sort(-GeoIntentSimulationModel.created_at).limit(limit).to_list()
    
    async def delete_old_simulations(self, older_than: datetime) -> int:
        """Delete simulations older than specified date (cleanup)"""
        result = await GeoIntentSimulationModel.find(
            GeoIntentSimulationModel.created_at < older_than
        ).delete()
        return result.deleted_count if result else 0
