"""
Campaign Launch Router
=====================
Approval-gated campaign launch workflow for Trend Arbitrage.
"""

from __future__ import annotations

import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query

from presentation.routers.auth_router import get_current_user_email
from presentation.schemas.campaign_launch_schemas import (
    CampaignLaunchCreateRequest,
    CampaignLaunchCreateResponse,
    CampaignLaunchApproveResponse,
    CampaignLaunchRejectRequest,
    CampaignLaunchListResponse,
    CampaignLaunchItem,
)
from application.services.campaign_launch_service import CampaignLaunchService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/campaign-launch", tags=["Campaign Launch"])
service = CampaignLaunchService()


@router.post("/request", response_model=CampaignLaunchCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_launch_request(
    request: CampaignLaunchCreateRequest,
    current_user_email: str = Depends(get_current_user_email),
):
    try:
        req = await service.create_request(
            user_email=current_user_email,
            platform=request.platform,
            mode=request.mode,
            media_url=request.media_url,
            caption=request.caption,
            scheduled_time=request.scheduled_time,
            facebook_page_id=request.facebook_page_id,
            trend_keyword=request.trend_keyword,
            trend_signal_id=request.trend_signal_id,
            source=(request.source or "trend"),
            campaign_plan_id=request.campaign_plan_id,
            planned_post_id=request.planned_post_id,
        )
        return CampaignLaunchCreateResponse(
            request_id=str(req.id),
            status=req.status,
            message="Launch request created. Approval required to execute.",
        )
    except Exception as e:
        logger.exception("Failed to create launch request: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create launch request") from e


@router.post("/{request_id}/approve", response_model=CampaignLaunchApproveResponse)
async def approve_launch_request(
    request_id: str,
    current_user_email: str = Depends(get_current_user_email),
):
    req = await service.approve_and_execute(user_email=current_user_email, request_id=request_id)
    return CampaignLaunchApproveResponse(
        success=req.status == "completed",
        request_id=str(req.id),
        status=req.status,
        result=req.result or {},
    )


@router.post("/{request_id}/reject", response_model=CampaignLaunchApproveResponse)
async def reject_launch_request(
    request_id: str,
    body: CampaignLaunchRejectRequest,
    current_user_email: str = Depends(get_current_user_email),
):
    req = await service.reject_request(user_email=current_user_email, request_id=request_id, reason=body.reason)
    return CampaignLaunchApproveResponse(
        success=True,
        request_id=str(req.id),
        status=req.status,
        result=req.result or {},
    )


@router.get("", response_model=CampaignLaunchListResponse)
async def list_launch_requests(
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user_email: str = Depends(get_current_user_email),
):
    data = await service.list_requests(user_email=current_user_email, limit=limit, skip=skip)
    rows = data["rows"]
    items = [
        CampaignLaunchItem(
            id=str(r.id),
            status=r.status,
            platform=r.platform,
            mode=r.mode,
            media_url=r.media_url,
            caption=r.caption,
            scheduled_time=r.scheduled_time,
            source=getattr(r, "source", None),
            campaign_plan_id=getattr(r, "campaign_plan_id", None),
            planned_post_id=getattr(r, "planned_post_id", None),
            trend_keyword=r.trend_keyword,
            trend_signal_id=r.trend_signal_id,
            created_at=r.created_at.isoformat(),
            updated_at=r.updated_at.isoformat(),
            result=r.result or {},
        )
        for r in rows
    ]
    return CampaignLaunchListResponse(requests=items, total=data["total"])

