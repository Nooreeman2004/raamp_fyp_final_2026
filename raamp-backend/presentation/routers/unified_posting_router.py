"""
Unified Posting Router.
Provides a single endpoint for multi-platform posting.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import logging
from datetime import datetime

from presentation.routers.auth_router import get_current_user_email
from presentation.schemas.unified_posting_schemas import (
    UnifiedPostRequest,
    UnifiedPostResponse,
    PlatformResult,
    PlatformEnum,
    PostModeEnum
)
from application.services.unified_posting_service import UnifiedPostingService
from application.services.unified_posting_service import UnifiedPostingService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/social", tags=["Unified Posting"])

@router.post("/post", response_model=UnifiedPostResponse)
async def unified_post(
    request: UnifiedPostRequest,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Unified endpoint to post to Instagram, Facebook, or both.
    """
    service = UnifiedPostingService()
    return await service.unified_post(request, current_user_email)
