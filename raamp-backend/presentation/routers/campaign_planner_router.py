from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from presentation.routers.auth_router import get_current_user_email
from presentation.schemas.campaign_planner_schemas import (
    CampaignPlannerCreateRequest,
    CampaignPlannerCreateResponse,
    CampaignPlanListResponse,
    CampaignPlanListItem,
    CampaignPlanDetailResponse,
    CalendarQueryResponse,
    PlannedPostItem,
    PlannedPostPatchRequest,
)
from application.services.campaign_planner_service import CampaignPlannerService
from infrastructure.database.models.campaign_plan_model import CampaignPlanModel
from infrastructure.database.models.campaign_planned_post_model import CampaignPlannedPostModel
from infrastructure.database.models.campaign_draft_model import CampaignDraftModel
from application.services.campaign_launch_service import CampaignLaunchService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/campaign-planner", tags=["Campaign Planner"])
planner_service = CampaignPlannerService()
launch_service = CampaignLaunchService()


def _post_item(p: CampaignPlannedPostModel) -> PlannedPostItem:
    return PlannedPostItem(
        id=str(p.id),
        campaign_plan_id=p.campaign_plan_id,
        scheduled_time=p.scheduled_time.replace(tzinfo=timezone.utc).isoformat(),
        timezone=p.timezone,
        title=p.title,
        post_type=p.post_type,
        status=p.status,
        prompts=p.prompts or {},
        cta=p.cta,
        hashtags=p.hashtags or [],
        why_it_fits_brand=p.why_it_fits_brand,
        draft_id=p.draft_id,
        launch_request_id=p.launch_request_id,
        last_error=p.last_error,
        last_error_at=p.last_error_at.isoformat() if p.last_error_at else None,
    )


@router.post("/plans", response_model=CampaignPlannerCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    body: CampaignPlannerCreateRequest,
    current_user_email: str = Depends(get_current_user_email),
):
    brief = body.model_dump()
    plan = await planner_service.create_plan(user_email=current_user_email, brief=brief)
    return CampaignPlannerCreateResponse(plan_id=str(plan.id), generation_status=plan.generation_status)


@router.get("/plans", response_model=CampaignPlanListResponse)
async def list_plans(
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user_email: str = Depends(get_current_user_email),
):
    q = CampaignPlanModel.user_email == current_user_email
    rows = await CampaignPlanModel.find(q).sort(-CampaignPlanModel.created_at).skip(skip).limit(limit).to_list()
    total = await CampaignPlanModel.find(q).count()
    items: list[CampaignPlanListItem] = []
    for r in rows:
        name = (r.generated or {}).get("campaign_name") or "Campaign Plan"
        items.append(
            CampaignPlanListItem(
                id=str(r.id),
                name=name,
                objective=(r.generated or {}).get("objective"),
                start_date=r.start_date.isoformat(),
                end_date=r.end_date.isoformat(),
                timezone=r.timezone,
                generation_status=r.generation_status,
                created_at=r.created_at.isoformat(),
            )
        )
    return CampaignPlanListResponse(plans=items, total=total)


@router.get("/plans/{plan_id}", response_model=CampaignPlanDetailResponse)
async def get_plan(
    plan_id: str,
    current_user_email: str = Depends(get_current_user_email),
):
    plan = await CampaignPlanModel.get(plan_id)
    if not plan or plan.user_email != current_user_email:
        raise HTTPException(status_code=404, detail="Plan not found")
    posts = (
        await CampaignPlannedPostModel.find(
            CampaignPlannedPostModel.user_email == current_user_email,
            CampaignPlannedPostModel.campaign_plan_id == str(plan.id),
        )
        .sort(CampaignPlannedPostModel.scheduled_time)
        .to_list()
    )
    return CampaignPlanDetailResponse(
        id=str(plan.id),
        input_brief=plan.input_brief or {},
        generated=plan.generated or {},
        start_date=plan.start_date.isoformat(),
        end_date=plan.end_date.isoformat(),
        timezone=plan.timezone,
        posting_frequency=plan.posting_frequency,
        generation_status=plan.generation_status,
        generation_error=plan.generation_error,
        status=plan.status,
        created_at=plan.created_at.isoformat(),
        updated_at=plan.updated_at.isoformat(),
        posts=[_post_item(p) for p in posts],
    )


@router.delete("/plans/{plan_id}")
async def delete_plan(
    plan_id: str,
    current_user_email: str = Depends(get_current_user_email),
):
    plan = await CampaignPlanModel.get(plan_id)
    if not plan or plan.user_email != current_user_email:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    await CampaignPlannedPostModel.find(
        CampaignPlannedPostModel.campaign_plan_id == plan_id,
        CampaignPlannedPostModel.user_email == current_user_email
    ).delete()
    
    await plan.delete()

    # Verify removal so client doesn't get false success.
    verify = await CampaignPlanModel.get(plan_id)
    if verify and verify.user_email == current_user_email:
        raise HTTPException(status_code=500, detail="Plan could not be deleted")

    return {"success": True, "deleted_plan_id": plan_id}



@router.get("/plans/{plan_id}/calendar", response_model=CalendarQueryResponse)
async def calendar_for_plan(
    plan_id: str,
    start: datetime = Query(...),
    end: datetime = Query(...),
    tz: str = Query("UTC"),
    platform: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user_email: str = Depends(get_current_user_email),
):
    # Note: platform is not yet stored on planned posts; reserved for future.
    plan = await CampaignPlanModel.get(plan_id)
    if not plan or plan.user_email != current_user_email:
        raise HTTPException(status_code=404, detail="Plan not found")
    q = [
        CampaignPlannedPostModel.user_email == current_user_email,
        CampaignPlannedPostModel.campaign_plan_id == plan_id,
        CampaignPlannedPostModel.scheduled_time >= start.astimezone(timezone.utc),
        CampaignPlannedPostModel.scheduled_time <= end.astimezone(timezone.utc),
    ]
    if status_filter:
        q.append(CampaignPlannedPostModel.status == status_filter)
    rows = await CampaignPlannedPostModel.find(*q).sort(CampaignPlannedPostModel.scheduled_time).to_list()
    return CalendarQueryResponse(items=[_post_item(p) for p in rows])


@router.get("/calendar", response_model=CalendarQueryResponse)
async def calendar_global(
    start: datetime = Query(...),
    end: datetime = Query(...),
    campaign_ids: Optional[str] = Query(None, description="Comma-separated plan ids"),
    tz: str = Query("UTC"),
    platform: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user_email: str = Depends(get_current_user_email),
):
    ids: Optional[List[str]] = None
    if campaign_ids:
        ids = [s.strip() for s in campaign_ids.split(",") if s.strip()]
    q = [
        CampaignPlannedPostModel.user_email == current_user_email,
        CampaignPlannedPostModel.scheduled_time >= start.astimezone(timezone.utc),
        CampaignPlannedPostModel.scheduled_time <= end.astimezone(timezone.utc),
    ]
    if ids:
        q.append(CampaignPlannedPostModel.campaign_plan_id.in_(ids))  # type: ignore[attr-defined]
    if status_filter:
        q.append(CampaignPlannedPostModel.status == status_filter)
    rows = await CampaignPlannedPostModel.find(*q).sort(CampaignPlannedPostModel.scheduled_time).to_list()
    return CalendarQueryResponse(items=[_post_item(p) for p in rows])


@router.patch("/planned-posts/{post_id}", response_model=PlannedPostItem)
async def patch_planned_post(
    post_id: str,
    body: PlannedPostPatchRequest,
    current_user_email: str = Depends(get_current_user_email),
):
    post = await CampaignPlannedPostModel.get(post_id)
    if not post or post.user_email != current_user_email:
        raise HTTPException(status_code=404, detail="Planned post not found")

    if body.scheduled_time:
        post.scheduled_time = body.scheduled_time.astimezone(timezone.utc)
    if body.title:
        post.title = body.title
    if body.status:
        post.status = body.status
    post.updated_at = datetime.utcnow()
    await post.save()
    return _post_item(post)


@router.post("/planned-posts/{post_id}/convert-to-draft")
async def convert_to_draft(
    post_id: str,
    current_user_email: str = Depends(get_current_user_email),
):
    post = await CampaignPlannedPostModel.get(post_id)
    if not post or post.user_email != current_user_email:
        raise HTTPException(status_code=404, detail="Planned post not found")

    # Minimal draft shape to reuse CreativeStudio flows.
    now = datetime.utcnow()
    draft = CampaignDraftModel(
        user_id=current_user_email,
        kind="carousel" if post.post_type == "carousel" else ("reel" if post.post_type == "reel" else "story" if post.post_type == "story" else "carousel"),
        trend_keyword=None,
        niche=None,
        location=None,
        title=f"Planner draft • {post.title}",
        content={
            "caption_prompt": (post.prompts or {}).get("caption_prompt"),
            "creative_prompt": (post.prompts or {}).get("creative_prompt"),
            "cta": post.cta,
            "hashtags": post.hashtags,
            "planned_post_id": str(post.id),
            "campaign_plan_id": post.campaign_plan_id,
        },
        created_at=now,
        updated_at=now,
    )
    await draft.insert()

    post.draft_id = str(draft.id)
    post.status = "draft_created" if post.status == "planned" else post.status
    post.updated_at = now
    await post.save()

    return {"success": True, "draft_id": str(draft.id)}


@router.post("/planned-posts/{post_id}/request-approval")
async def request_approval(
    post_id: str,
    mode: str = Query("schedule_post", description="post_now|schedule_post|post_story"),
    platform: str = Query("instagram", description="instagram|facebook|both"),
    media_url: str = Query(..., description="Public HTTPS media URL"),
    current_user_email: str = Depends(get_current_user_email),
):
    post = await CampaignPlannedPostModel.get(post_id)
    if not post or post.user_email != current_user_email:
        raise HTTPException(status_code=404, detail="Planned post not found")

    req = await launch_service.create_request(
        user_email=current_user_email,
        platform=platform,
        mode=mode,
        media_url=media_url,
        caption=(post.prompts or {}).get("caption_prompt") or post.title,
        scheduled_time=post.scheduled_time.isoformat() if mode == "schedule_post" else None,
        facebook_page_id=None,
        trend_keyword=None,
        trend_signal_id=None,
        source="planner",
        campaign_plan_id=post.campaign_plan_id,
        planned_post_id=str(post.id),
    )

    post.launch_request_id = str(req.id)
    if post.status in ("planned", "draft_created"):
        post.status = "approval_requested"
    post.updated_at = datetime.utcnow()
    await post.save()

    return {"success": True, "request_id": str(req.id), "status": req.status}

