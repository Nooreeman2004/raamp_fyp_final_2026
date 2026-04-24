"""
Get Activity Feed Use Case
Application layer - Business logic for retrieving activity feed
"""
from typing import List, Dict, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class GetActivityFeedUseCase:
    """Use case for retrieving activity feed for a business."""

    def __init__(self, activity_collection):
        """
        Initialize use case with activity collection.

        Args:
            activity_collection: MongoDB collection for activity logs
        """
        self.activity_collection = activity_collection

    async def execute(self, business_id: str, limit: int = 10) -> List[Dict]:
        """
        Retrieve activity feed for a business (legacy, non-paginated).

        Args:
            business_id: Business identifier
            limit: Maximum number of activities to return

        Returns:
            List of activity dictionaries sorted by newest first
        """
        activities, _ = await self.execute_paginated(business_id, skip=0, limit=limit)
        return activities

    async def execute_paginated(
        self, business_id: str, skip: int = 0, limit: int = 10
    ) -> Tuple[List[Dict], int]:
        """
        Retrieve a paginated activity feed for a business.

        Args:
            business_id: Business identifier
            skip: Number of records to skip (offset)
            limit: Maximum number of activities to return per page

        Returns:
            Tuple of (activities list, total_count)
        """
        try:
            query_filter = {"business_id": business_id}
            base_cursor = self.activity_collection.find(query_filter).sort("created_at", -1)

            # Run count and data fetch concurrently
            total_count: int = await self.activity_collection.count_documents(query_filter)
            cursor = base_cursor.skip(skip).limit(limit)
            activities = await cursor.to_list(length=limit)

            # Serialize ObjectId → str and datetime → ISO string
            for activity in activities:
                activity["id"] = str(activity["_id"])
                del activity["_id"]
                if isinstance(activity.get("created_at"), datetime):
                    activity["created_at"] = activity["created_at"].isoformat()

            return activities, total_count
        except Exception as e:
            logger.error(f"Error fetching activity feed: {e}")
            raise

