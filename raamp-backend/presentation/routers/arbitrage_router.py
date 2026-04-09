
# Presentation Layer - Arbitrage Router
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import logging

from presentation.schemas.arbitrage_schemas import (
    UserProfileSchema, 
    TrendSignalInputSchema, 
    ArbitrageRecommendationResponse
)
from application.services.arbitrage_intelligence_service import ArbitrageIntelligenceService
from presentation.routers.auth_router import get_current_user_email

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/arbitrage", tags=["Arbitrage Intelligence"])

def get_arbitrage_service() -> ArbitrageIntelligenceService:
    return ArbitrageIntelligenceService()

@router.post(
    "/recommendations",
    response_model=ArbitrageRecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get AI-powered campaign recommendations"
)
async def get_recommendations(
    user_profile: UserProfileSchema,
    trend_signals: List[TrendSignalInputSchema],
    current_user_email: str = Depends(get_current_user_email),
    service: ArbitrageIntelligenceService = Depends(get_arbitrage_service)
):
    """
    Generate top 3 marketing campaign recommendations based on provided trend signals.
    """
    try:
        recommendations = await service.generate_recommendations(
            trend_signals,
            user_profile,
            user_email=current_user_email,
        )
        return recommendations
    except Exception as e:
        logger.error(f"Error in arbitrage recommendations API: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}"
        )
