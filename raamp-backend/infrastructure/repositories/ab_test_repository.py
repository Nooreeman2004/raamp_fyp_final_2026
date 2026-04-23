"""
A/B Test Image Repository
==========================
Data access layer for image analysis results.
"""

import logging
from typing import Optional, List, Dict, Any

from infrastructure.database.database import get_database

logger = logging.getLogger(__name__)


class ABTestImageRepository:
    """Repository for managing A/B test image analysis data"""
    
    def __init__(self):
        """Initialize repository with database connection"""
        self.db = get_database()
        self.images_collection = self.db["ab_test_images"]
        self.batches_collection = self.db["ab_test_batches"]
    
    async def create_indexes(self):
        """Create indexes for efficient queries and data integrity"""
        # Image indexes
        await self.images_collection.create_index("image_id", unique=True)
        await self.images_collection.create_index("user_id")
        await self.images_collection.create_index("ab_test_batch_id")
        # Uniqueness for file_hash per user to prevent redundant AI analysis
        await self.images_collection.create_index([("user_id", 1), ("file_hash", 1)], unique=True)
        await self.images_collection.create_index([("user_id", 1), ("created_at", -1)])
        
        # Batch indexes
        await self.batches_collection.create_index("batch_id", unique=True)
        await self.batches_collection.create_index("user_id")
        await self.batches_collection.create_index([("user_id", 1), ("created_at", -1)])
    
    async def save_analysis(self, analysis: Dict[str, Any]) -> str:
        """
        Save image analysis result to database.
        
        Args:
            analysis: Analysis result dictionary
            
        Returns:
            image_id of the saved document
        """
        try:
            result = await self.images_collection.insert_one(analysis)
            logger.info(f"✅ Saved analysis for image: {analysis['image_id']}")
            return analysis["image_id"]
        except Exception as e:
            logger.error(f"❌ Failed to save analysis: {str(e)}")
            raise
    
    async def get_by_image_id(self, image_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve analysis by image ID.
        
        Args:
            image_id: Unique image identifier
            
        Returns:
            Analysis document or None
        """
        return await self.images_collection.find_one({"image_id": image_id})
    
    async def get_by_file_hash(self, file_hash: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached analysis by file hash (for duplicate detection).
        
        Args:
            file_hash: MD5 hash of the file
            user_id: User ID to scope the search
            
        Returns:
            Analysis document or None
        """
        return await self.images_collection.find_one({
            "file_hash": file_hash,
            "user_id": user_id
        })
    
    async def get_user_images(
        self,
        user_id: str,
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get all analyzed images for a user.
        
        Args:
            user_id: User ID
            limit: Maximum results to return
            skip: Number of results to skip (pagination)
            
        Returns:
            List of analysis documents
        """
        cursor = self.images_collection.find({"user_id": user_id}) \
            .sort("created_at", -1) \
            .skip(skip) \
            .limit(limit)
        
        return await cursor.to_list(length=limit)
    
    async def get_batch_images(self, batch_id: str) -> List[Dict[str, Any]]:
        """
        Get all images in a specific batch.
        
        Args:
            batch_id: Batch identifier
            
        Returns:
            List of analysis documents in the batch
        """
        cursor = self.images_collection.find({"ab_test_batch_id": batch_id}) \
            .sort("composite_score", -1)
        
        return await cursor.to_list(length=None)
    
    async def create_batch(self, batch: Dict[str, Any]) -> str:
        """
        Create a new A/B test batch.
        
        Args:
            batch: Batch data dictionary
            
        Returns:
            batch_id of the created batch
        """
        try:
            result = await self.batches_collection.insert_one(batch)
            logger.info(f"✅ Created batch: {batch['batch_id']}")
            return batch["batch_id"]
        except Exception as e:
            logger.error(f"❌ Failed to create batch: {str(e)}")
            raise
    
    async def get_batch(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve batch by ID.
        
        Args:
            batch_id: Batch identifier
            
        Returns:
            Batch document or None
        """
        return await self.batches_collection.find_one({"batch_id": batch_id})
    
    async def update_batch_recommendations(
        self,
        batch_id: str,
        recommended_pair: List[str],
        score_gap: float
    ) -> bool:
        """
        Update batch with A/B test recommendations.
        
        Args:
            batch_id: Batch identifier
            recommended_pair: [image_id_1, image_id_2]
            score_gap: Score difference between the two images
            
        Returns:
            True if successful
        """
        result = await self.batches_collection.update_one(
            {"batch_id": batch_id},
            {"$set": {
                "recommended_pair": recommended_pair,
                "score_gap": score_gap
            }}
        )
        return result.modified_count > 0
    
    async def get_user_batches(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get all batches for a user with image counts in a single query.
        Uses MongoDB aggregation to avoid N+1 query problem.
        """
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$sort": {"created_at": -1}},
            {"$limit": limit},
            {
                "$lookup": {
                    "from": "ab_test_images",
                    "localField": "batch_id",
                    "foreignField": "ab_test_batch_id",
                    "as": "batch_images"
                }
            },
            {
                "$project": {
                    "batch_id": 1,
                    "user_id": 1,
                    "created_at": 1,
                    "recommended_pair": 1,
                    "score_gap": 1,
                    "schedule_id": 1,
                    "image_count": {"$size": "$batch_images"}
                }
            }
        ]
        
        cursor = self.batches_collection.aggregate(pipeline)
        return await cursor.to_list(length=limit)
    
    async def delete_image(self, image_id: str) -> bool:
        """
        Delete an image analysis.
        
        Args:
            image_id: Image identifier
            
        Returns:
            True if deleted
        """
        result = await self.images_collection.delete_one({"image_id": image_id})
        return result.deleted_count > 0
    
    # Schedule methods
    
    async def save_schedule(self, schedule: Dict[str, Any]) -> str:
        """Save A/B test schedule"""
        result = await self.db["ab_test_schedules"].insert_one(schedule)
        return schedule["schedule_id"]
    
    async def get_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """Get schedule by ID"""
        return await self.db["ab_test_schedules"].find_one({"schedule_id": schedule_id})
    
    async def update_schedule_status(self, schedule_id: str, status: str) -> bool:
        """Update schedule status"""
        result = await self.db["ab_test_schedules"].update_one(
            {"schedule_id": schedule_id},
            {"$set": {"status": status}}
        )
        return result.modified_count > 0
    
    # Result methods
    
    async def save_result(self, result: Dict[str, Any]) -> str:
        """Save A/B test result"""
        await self.db["ab_test_results"].insert_one(result)
        return result["result_id"]
    
    async def get_result(self, result_id: str) -> Optional[Dict[str, Any]]:
        """Get result by ID"""
        return await self.db["ab_test_results"].find_one({"result_id": result_id})
    
    async def get_result_by_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """Get result by schedule ID"""
        return await self.db["ab_test_results"].find_one({"schedule_id": schedule_id})
    
    # Ad Brief methods
    
    async def save_ad_brief(self, brief: Dict[str, Any]) -> str:
        """Save ad brief"""
        await self.db["ab_test_ad_briefs"].insert_one(brief)
        return brief["brief_id"]
    
    async def get_ad_brief(self, brief_id: str) -> Optional[Dict[str, Any]]:
        """Get ad brief by ID"""
        return await self.db["ab_test_ad_briefs"].find_one({"brief_id": brief_id})
    
    async def get_ad_brief_by_result(self, result_id: str) -> Optional[Dict[str, Any]]:
        """Get ad brief by result ID"""
        return await self.db["ab_test_ad_briefs"].find_one({"result_id": result_id})


# Singleton instance
_repository_instance: Optional[ABTestImageRepository] = None


def get_ab_test_repository() -> ABTestImageRepository:
    """
    Get or create singleton repository instance.
    
    Returns:
        ABTestImageRepository instance
    """
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = ABTestImageRepository()
    return _repository_instance
