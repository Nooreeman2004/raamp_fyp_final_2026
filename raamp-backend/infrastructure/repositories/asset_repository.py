"""
Asset Repository - handles database operations for media assets
"""
from infrastructure.database.models.asset_model import AssetModel, AssetType, GenerationSource
from typing import Optional, List, Dict, Any
from datetime import datetime
from beanie.operators import In
import logging

logger = logging.getLogger(__name__)


class AssetRepository:
    """Repository for asset data operations"""
    
    async def create(self, asset_data: Dict[str, Any]) -> AssetModel:
        """Create a new asset record"""
        asset = AssetModel(**asset_data)
        await asset.insert()
        return asset
    
    async def get_by_asset_id(self, asset_id: str) -> Optional[AssetModel]:
        """Get asset by asset_id"""
        return await AssetModel.find_one(AssetModel.asset_id == asset_id)

    async def get_by_asset_ids(self, asset_ids: List[str]) -> List[AssetModel]:
        """
        Batch-fetch multiple assets by their asset_ids in a single query.

        Eliminates N+1 query patterns when processing multiple assets.
        Returns assets in the order found (not guaranteed to match input order).
        Use {a.asset_id: a for a in assets} to build a lookup dict if order matters.
        """
        if not asset_ids:
            return []
        return await AssetModel.find(In(AssetModel.asset_id, asset_ids)).to_list()


    async def get_by_user_id(
        self,
        user_id: str,
        limit: int = 100,
        skip: int = 0,
        asset_type: Optional[AssetType] = None,
        asset_types: Optional[List[AssetType]] = None,
        generation_source: Optional[GenerationSource] = None
    ) -> List[AssetModel]:
        """
        Get all assets for a user with optional filtering
        
        Args:
            user_id: User identifier
            limit: Maximum number of results
            skip: Number of results to skip (pagination)
            asset_type: Filter by a single asset type
            asset_types: Filter by multiple asset types (OR)
            generation_source: Filter by generation source
        """
        query = AssetModel.find(AssetModel.user_id == user_id)
        
        if asset_types:
            query = query.find(In(AssetModel.asset_type, asset_types))
        elif asset_type:
            query = query.find(AssetModel.asset_type == asset_type)
        
        if generation_source:
            query = query.find(AssetModel.generation_source == generation_source)
        
        # Sort by created_at descending (newest first)
        query = query.sort(-AssetModel.created_at)
        
        assets = await query.skip(skip).limit(limit).to_list()
        return assets
    
    async def get_generated_images(self, user_id: str, limit: int = 50) -> List[AssetModel]:
        """Get all AI-generated images for a user"""
        return await self.get_by_user_id(
            user_id=user_id,
            limit=limit,
            asset_type=AssetType.GENERATED_IMAGE,
            generation_source=GenerationSource.AI
        )
    
    async def increment_usage(self, asset_id: str) -> bool:
        """Increment the usage counter for an asset"""
        asset = await self.get_by_asset_id(asset_id)
        if not asset:
            return False
        
        asset.times_used += 1
        asset.last_used_at = datetime.utcnow()
        asset.updated_at = datetime.utcnow()
        await asset.save()
        return True
    
    async def update_tags(self, asset_id: str, tags: List[str]) -> bool:
        """Update tags for an asset"""
        asset = await self.get_by_asset_id(asset_id)
        if not asset:
            return False
        
        asset.tags = tags
        asset.updated_at = datetime.utcnow()
        await asset.save()
        return True
    
    async def toggle_favorite(self, asset_id: str) -> bool:
        """Toggle favorite status for an asset"""
        asset = await self.get_by_asset_id(asset_id)
        if not asset:
            return False
        
        asset.is_favorite = not asset.is_favorite
        asset.updated_at = datetime.utcnow()
        await asset.save()
        return True
    
    async def delete(self, asset_id: str) -> bool:
        """Delete an asset record"""
        asset = await self.get_by_asset_id(asset_id)
        if not asset:
            return False
        
        await asset.delete()
        return True
    
    async def count_user_assets(
        self,
        user_id: str,
        asset_type: Optional[AssetType] = None,
        asset_types: Optional[List[AssetType]] = None
    ) -> int:
        """Count total assets for a user"""
        query = AssetModel.find(AssetModel.user_id == user_id)
        
        if asset_types:
            query = query.find(In(AssetModel.asset_type, asset_types))
        elif asset_type:
            query = query.find(AssetModel.asset_type == asset_type)
        
        return await query.count()
