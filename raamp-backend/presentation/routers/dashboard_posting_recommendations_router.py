import logging
from fastapi import APIRouter, Depends

from presentation.routers.auth_router import get_current_user_email
from application.services.posting_recommendation_service import PostingRecommendationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])
service = PostingRecommendationService()


@router.get("/posting-recommendations")
async def get_posting_recommendations(current_user_email: str = Depends(get_current_user_email)):
    """
    Suggest best days/times to post content.

    Response shape:
    {
      "timezone": "Asia/Karachi",
      "next_best_time": "2026-04-22T19:00:00",
      "days": ["Tuesday", "Thursday", "Saturday"],
      "slots": [{"start":"12:00","end":"14:00"}, ...],
      "confidence": "high"|"low"
    }
    """
    result = await service.get_recommendations(current_user_email)
    return {
        "timezone": result.timezone,
        "next_best_time": result.next_best_time,
        "days": result.days,
        "slots": result.slots,
        "confidence": result.confidence,
    }

