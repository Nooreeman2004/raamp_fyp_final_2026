"""
Complaint Repository - MongoDB (Beanie)
"""
from infrastructure.database.models.complaint_model import ComplaintModel
from typing import List, Optional
from datetime import datetime
from bson import ObjectId


class ComplaintRepository:
    async def create(self, user_id: str, subject: str, description: str, priority: str = "medium") -> ComplaintModel:
        now = datetime.utcnow()
        complaint = ComplaintModel(
            userId=user_id,
            subject=subject,
            description=description,
            priority=priority,
            status="pending",
            adminResponse="",
            adminId="",
            resolvedAt=None,
            createdAt=now,
            updatedAt=now,
        )

        await complaint.insert()
        return complaint

    async def find_by_user_id(self, user_id: str) -> List[ComplaintModel]:
        return await ComplaintModel.find(ComplaintModel.userId == user_id).sort(-ComplaintModel.createdAt).to_list()

    async def find_by_id(self, complaint_id: str) -> Optional[ComplaintModel]:
        try:
            return await ComplaintModel.get(ObjectId(complaint_id))
        except Exception:
            return None
