"""
Caption Log Repository - handles database operations for caption logs
"""
from infrastructure.database.models.caption_log_model import CaptionLogModel, AssetTypeEnum
from typing import Optional, List, Dict, Any
from datetime import datetime


class CaptionLogRepository:
    """Repository for caption log data operations"""
    
    async def create(self, caption_data: Dict[str, Any]) -> CaptionLogModel:
        """Create a new caption log record"""
        caption = CaptionLogModel(**caption_data)
        await caption.insert()
        return caption
    
    async def create_many(self, captions_data: List[Dict[str, Any]]) -> List[CaptionLogModel]:
        """Create multiple caption log records in bulk"""
        captions = [CaptionLogModel(**data) for data in captions_data]
        await CaptionLogModel.insert_many(captions)
        return captions
    
    async def get_by_caption_id(self, caption_id: str) -> Optional[CaptionLogModel]:
        """Get caption log by caption_id"""
        return await CaptionLogModel.find_one(CaptionLogModel.caption_id == caption_id)
    
    async def get_by_user_id(
        self,
        user_id: str,
        limit: int = 100,
        skip: int = 0,
        asset_type: Optional[AssetTypeEnum] = None,
        campaign_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[CaptionLogModel]:
        """
        Get all caption logs for a user with optional filtering
        
        Args:
            user_id: User identifier
            limit: Maximum number of results
            skip: Number of results to skip (pagination)
            asset_type: Filter by asset type (post, story, reel, etc.)
            campaign_id: Filter by campaign ID
            start_date: Filter by start date
            end_date: Filter by end date
        """
        query = CaptionLogModel.find(CaptionLogModel.user_id == user_id)
        
        if asset_type:
            query = query.find(CaptionLogModel.asset_type == asset_type)
        
        if campaign_id:
            query = query.find(CaptionLogModel.campaign_id == campaign_id)
        
        if start_date:
            query = query.find(CaptionLogModel.created_at >= start_date)
        
        if end_date:
            query = query.find(CaptionLogModel.created_at <= end_date)
        
        # Sort by created_at descending (newest first)
        query = query.sort(-CaptionLogModel.created_at)
        
        captions = await query.skip(skip).limit(limit).to_list()
        return captions
    
    async def count_user_captions(
        self,
        user_id: str,
        asset_type: Optional[AssetTypeEnum] = None,
        campaign_id: Optional[str] = None
    ) -> int:
        """Count total captions for a user with optional filters"""
        query = CaptionLogModel.find(CaptionLogModel.user_id == user_id)
        
        if asset_type:
            query = query.find(CaptionLogModel.asset_type == asset_type)
        
        if campaign_id:
            query = query.find(CaptionLogModel.campaign_id == campaign_id)
        
        return await query.count()
    
    async def increment_usage(self, caption_id: str) -> bool:
        """Increment the usage counter for a caption"""
        caption = await self.get_by_caption_id(caption_id)
        if not caption:
            return False
        
        caption.times_used += 1
        caption.last_used_at = datetime.utcnow()
        caption.updated_at = datetime.utcnow()
        await caption.save()
        return True
    
    async def update_tags(self, caption_id: str, tags: List[str]) -> bool:
        """Update tags for a caption"""
        caption = await self.get_by_caption_id(caption_id)
        if not caption:
            return False
        
        caption.tags = tags
        caption.updated_at = datetime.utcnow()
        await caption.save()
        return True
    
    async def toggle_favorite(self, caption_id: str) -> bool:
        """Toggle favorite status for a caption"""
        caption = await self.get_by_caption_id(caption_id)
        if not caption:
            return False
        
        caption.is_favorite = not caption.is_favorite
        caption.updated_at = datetime.utcnow()
        await caption.save()
        return True
    
    async def update_performance(
        self,
        caption_id: str,
        actual_performance: Optional[str] = None,
        engagement_rate: Optional[float] = None
    ) -> bool:
        """Update performance tracking for a caption"""
        caption = await self.get_by_caption_id(caption_id)
        if not caption:
            return False
        
        if actual_performance:
            caption.actual_performance = actual_performance
        if engagement_rate is not None:
            caption.engagement_rate = engagement_rate
        
        caption.updated_at = datetime.utcnow()
        await caption.save()
        return True
    
    async def delete(self, caption_id: str) -> bool:
        """Delete a caption log record"""
        caption = await self.get_by_caption_id(caption_id)
        if not caption:
            return False
        
        await caption.delete()
        return True
