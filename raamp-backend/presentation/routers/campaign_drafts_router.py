from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query

from presentation.routers.auth_router import get_current_user_email
from application.constants import PaginationDefaults
from presentation.schemas.campaign_draft_schemas import (
    CreatePackRequest,
    CreatePackResponse,
    DraftItem,
    DraftListResponse,
)
from application.services.create_pack_service import CreatePackService
from infrastructure.database.models.campaign_draft_model import CampaignDraftModel


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/campaign-drafts", tags=["Campaign Drafts"])


@router.post("/create-pack", response_model=CreatePackResponse, status_code=status.HTTP_201_CREATED)
async def create_pack(
    body: CreatePackRequest,
    current_user_email: str = Depends(get_current_user_email),
):
    try:
        service = CreatePackService()
        drafts = await service.create_pack(
            user_id=current_user_email,
            trend_keyword=body.trend_keyword,
            niche=body.niche,
            location=body.location,
            suggested_hashtags=body.suggested_hashtags,
            suggested_caption=body.suggested_caption,
            platform=body.platform,
        )
        items = [
            DraftItem(
                id=str(d.id),
                kind=d.kind,
                title=d.title,
                trend_keyword=d.trend_keyword,
                niche=d.niche,
                location=d.location,
                content=d.content or {},
                created_at=d.created_at.isoformat(),
                updated_at=d.updated_at.isoformat(),
            )
            for d in drafts
        ]
        return CreatePackResponse(drafts=items)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Create pack failed: %s", e)
        raise HTTPException(status_code=500, detail="Create pack failed") from e


@router.get("", response_model=DraftListResponse)
async def list_drafts(
    kind: str | None = Query(None, description="Optional filter: carousel/reel/story"),
    limit: int = Query(PaginationDefaults.DEFAULT_LIMIT_LARGE, ge=1, le=PaginationDefaults.MAX_LIMIT_MEDIUM),
    skip: int = Query(PaginationDefaults.DEFAULT_SKIP, ge=0),
    current_user_email: str = Depends(get_current_user_email),
):
    q = {"user_id": current_user_email}
    if kind:
        q["kind"] = kind
    total = await CampaignDraftModel.find(q).count()
    rows = await CampaignDraftModel.find(q).sort("-created_at").skip(skip).limit(limit).to_list()
    items = [
        DraftItem(
            id=str(d.id),
            kind=d.kind,
            title=d.title,
            trend_keyword=d.trend_keyword,
            niche=d.niche,
            location=d.location,
            content=d.content or {},
            created_at=d.created_at.isoformat(),
            updated_at=d.updated_at.isoformat(),
        )
        for d in rows
    ]
    return DraftListResponse(drafts=items, total=total)


@router.delete("/{draft_id}", status_code=status.HTTP_200_OK)
async def delete_draft(
    draft_id: str,
    current_user_email: str = Depends(get_current_user_email),
):
    draft = await CampaignDraftModel.get(draft_id)
    if not draft or draft.user_id != current_user_email:
        raise HTTPException(status_code=404, detail="Draft not found")
    await draft.delete()
    return {"success": True}

