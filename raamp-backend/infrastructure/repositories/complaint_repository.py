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

    async def find_by_user_id_paginated(self, user_id: str, limit: int = 50, offset: int = 0) -> List[ComplaintModel]:
        lim = max(1, min(int(limit or 50), 200))
        off = max(0, int(offset or 0))
        return await (
            ComplaintModel.find(ComplaintModel.userId == user_id)
            .sort(-ComplaintModel.createdAt)
            .skip(off)
            .limit(lim)
            .to_list()
        )

    async def find_by_id(self, complaint_id: str) -> Optional[ComplaintModel]:
        try:
            return await ComplaintModel.get(ObjectId(complaint_id))
        except Exception:
            return None

    async def admin_list_paginated(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
        q: Optional[str] = None,
    ) -> List[ComplaintModel]:
        lim = max(1, min(int(limit or 50), 200))
        off = max(0, int(offset or 0))

        query = ComplaintModel.find()

        if status:
            st = str(status).strip().lower()
            query = query.find(ComplaintModel.status == st)

        if q:
            # NOTE: This is a simple search across subject/description/userId/status.
            # For large-scale production usage, add text indexes or dedicated search.
            qs = str(q).strip()
            if qs:
                query = query.find(
                    {
                        "$or": [
                            {"subject": {"$regex": qs, "$options": "i"}},
                            {"description": {"$regex": qs, "$options": "i"}},
                            {"userId": {"$regex": qs, "$options": "i"}},
                            {"status": {"$regex": qs, "$options": "i"}},
                        ]
                    }
                )

        return await (
            query.sort(-ComplaintModel.createdAt)
            .skip(off)
            .limit(lim)
            .to_list()
        )
