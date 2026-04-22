"""
Campaign Launch Service
======================
Orchestrates approval-gated launches by reusing existing posting routers/use-cases.

Key rule: do NOT rewrite posting logic. This service only coordinates:
- create request (pending)
- approve (execute existing posting flow)
- reject
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import HTTPException, status

from infrastructure.database.models.campaign_launch_request_model import (
    CampaignLaunchRequestModel,
    CampaignLaunchStatus,
)

logger = logging.getLogger(__name__)


class CampaignLaunchService:
    async def _update_related_trend_detections(
        self,
        *,
        user_email: str,
        trend_signal_id: Optional[str],
        trend_keyword: Optional[str],
        status_value: str,
    ) -> None:
        """
        Best-effort linkage from campaign approval flow → trend detection lifecycle.
        Keeps Trend Arbitrage dashboards clean and auditable.
        """
        try:
            from datetime import datetime
            from infrastructure.database.models.trend_detection_model import TrendDetectionModel

            now = datetime.utcnow()
            query: dict = {
                "user_id": user_email,
                "expires_at": {"$gt": now},
            }
            if trend_signal_id:
                query["trend_signal_id"] = str(trend_signal_id)
            elif trend_keyword:
                query["keyword"] = {"$regex": f"^{trend_keyword}$", "$options": "i"}
            else:
                return

            await TrendDetectionModel.find(query).update({"$set": {"status": status_value}})
        except Exception:
            # Non-fatal: campaign flow must not fail due to optional analytics state updates.
            return

    async def _set_trend_attribution_on_posts(
        self,
        *,
        user_email: str,
        platform_results: list[dict],
        trend_signal_id: Optional[str],
    ) -> None:
        """
        Best-effort attribution threading.
        We do NOT change posting logic; we update already-created post documents to attach trend_signal_id.
        """
        if not trend_signal_id:
            return

        try:
            from bson import ObjectId
        except Exception:
            ObjectId = None  # type: ignore

        async def _maybe_oid(s: Optional[str]):
            if not s:
                return None
            if ObjectId is None:
                return None
            try:
                return ObjectId(str(s))
            except Exception:
                return None

        from infrastructure.database.models.instagram_post_model import (
            InstagramPostModel,
            ScheduledInstagramPostModel,
            InstagramStoryModel,
        )
        from infrastructure.database.models.facebook_post_model import (
            FacebookPostModel,
            ScheduledFacebookPostModel,
        )

        updated = 0
        for r in platform_results or []:
            post_id = r.get("post_id") or r.get("id")
            if not post_id:
                continue

            oid = await _maybe_oid(str(post_id))
            key = oid or str(post_id)

            # Instagram: post_id might belong to post, scheduled post, or story collections.
            if r.get("platform") == "instagram":
                for model in (InstagramPostModel, ScheduledInstagramPostModel, InstagramStoryModel):
                    try:
                        doc = await model.get(key)
                        if doc and getattr(doc, "user_id", None) == user_email:
                            doc.trend_signal_id = trend_signal_id
                            doc.updated_at = datetime.utcnow()
                            await doc.save()
                            updated += 1
                            break
                    except Exception:
                        continue

            # Facebook: post_id might belong to immediate or scheduled collection.
            if r.get("platform") == "facebook":
                for model in (FacebookPostModel, ScheduledFacebookPostModel):
                    try:
                        doc = await model.get(key)
                        if doc and getattr(doc, "user_id", None) == user_email:
                            doc.trend_signal_id = trend_signal_id
                            doc.updated_at = datetime.utcnow()
                            await doc.save()
                            updated += 1
                            break
                    except Exception:
                        continue

        if updated:
            logger.info(
                "Attribution attached to %d post docs: user=%s trend_signal_id=%s",
                updated,
                user_email,
                trend_signal_id,
            )

    async def create_request(
        self,
        *,
        user_email: str,
        platform: str,
        mode: str,
        media_url: str,
        caption: Optional[str],
        scheduled_time: Optional[str],
        facebook_page_id: Optional[str],
        trend_keyword: Optional[str],
        trend_signal_id: Optional[str],
        source: str = "trend",
        campaign_plan_id: Optional[str] = None,
        planned_post_id: Optional[str] = None,
    ) -> CampaignLaunchRequestModel:
        now = datetime.utcnow()
        req = CampaignLaunchRequestModel(
            user_email=user_email,
            platform=platform,
            mode=mode,
            media_url=media_url,
            caption=caption,
            scheduled_time=scheduled_time,
            facebook_page_id=facebook_page_id,
            source=(source or "trend").strip().lower(),
            campaign_plan_id=campaign_plan_id,
            planned_post_id=planned_post_id,
            trend_keyword=trend_keyword,
            trend_signal_id=trend_signal_id,
            status=CampaignLaunchStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        await req.insert()
        return req

    async def reject_request(self, *, user_email: str, request_id: str, reason: Optional[str]) -> CampaignLaunchRequestModel:
        req = await CampaignLaunchRequestModel.get(request_id)
        if not req or req.user_email != user_email:
            raise HTTPException(status_code=404, detail="Launch request not found")
        if req.status != CampaignLaunchStatus.PENDING:
            raise HTTPException(status_code=400, detail=f"Cannot reject request in status={req.status}")
        req.status = CampaignLaunchStatus.REJECTED
        req.status_reason = reason
        req.rejected_at = datetime.utcnow()
        req.updated_at = datetime.utcnow()
        await req.save()
        await self._update_related_trend_detections(
            user_email=user_email,
            trend_signal_id=req.trend_signal_id,
            trend_keyword=req.trend_keyword,
            status_value="rejected",
        )
        return req

    async def approve_and_execute(self, *, user_email: str, request_id: str) -> CampaignLaunchRequestModel:
        req = await CampaignLaunchRequestModel.get(request_id)
        if not req or req.user_email != user_email:
            raise HTTPException(status_code=404, detail="Launch request not found")
        # Idempotency: if user clicks approve twice (or UI retries), do not fail.
        if req.status != CampaignLaunchStatus.PENDING:
            if req.status in (CampaignLaunchStatus.EXECUTING, CampaignLaunchStatus.COMPLETED, CampaignLaunchStatus.FAILED, CampaignLaunchStatus.APPROVED):
                return req
            raise HTTPException(status_code=400, detail=f"Cannot approve request in status={req.status}")

        req.status = CampaignLaunchStatus.APPROVED
        req.approved_at = datetime.utcnow()
        req.updated_at = datetime.utcnow()
        await req.save()
        await self._update_related_trend_detections(
            user_email=user_email,
            trend_signal_id=req.trend_signal_id,
            trend_keyword=req.trend_keyword,
            status_value="approved",
        )

        # Execute
        req.status = CampaignLaunchStatus.EXECUTING
        req.executed_at = datetime.utcnow()
        req.updated_at = datetime.utcnow()
        await req.save()

        try:
            result = await self._execute_posting(req, user_email)
            req.result = result or {}
            req.status = CampaignLaunchStatus.COMPLETED if (result or {}).get("success") else CampaignLaunchStatus.FAILED
            req.completed_at = datetime.utcnow()
            req.updated_at = datetime.utcnow()
            await req.save()
            if req.status == CampaignLaunchStatus.COMPLETED:
                await self._update_related_trend_detections(
                    user_email=user_email,
                    trend_signal_id=req.trend_signal_id,
                    trend_keyword=req.trend_keyword,
                    status_value="campaign_launched",
                )
            return req
        except HTTPException as e:
            req.status = CampaignLaunchStatus.FAILED
            req.status_reason = str(e.detail)
            req.result = {"success": False, "error": str(e.detail)}
            req.completed_at = datetime.utcnow()
            req.updated_at = datetime.utcnow()
            await req.save()
            raise
        except Exception as e:
            logger.exception("Launch execution failed: %s", e)
            req.status = CampaignLaunchStatus.FAILED
            req.status_reason = str(e)[:200]
            req.result = {"success": False, "error": "Internal execution error"}
            req.completed_at = datetime.utcnow()
            req.updated_at = datetime.utcnow()
            await req.save()
            raise HTTPException(status_code=500, detail="Launch execution failed") from e

    async def _execute_posting(self, req: CampaignLaunchRequestModel, user_email: str) -> Dict[str, Any]:
        """
        Reuse existing posting orchestration (same behavior as existing API endpoints),
        but without doing an HTTP round-trip.
        """
        from presentation.schemas.unified_posting_schemas import UnifiedPostRequest, PlatformEnum, PostModeEnum
        from application.services.unified_posting_service import UnifiedPostingService

        platform_enum = PlatformEnum(req.platform)
        mode_enum = PostModeEnum(req.mode)

        request = UnifiedPostRequest(
            platform=platform_enum,
            mode=mode_enum,
            media_url=req.media_url,
            caption=req.caption,
            scheduled_time=req.scheduled_time,
            facebook_page_id=req.facebook_page_id,
        )

        # Call the unified posting orchestration from the application layer.
        response = await UnifiedPostingService().unified_post(request, user_email)

        payload: Dict[str, Any] = response.model_dump() if hasattr(response, "model_dump") else dict(response)

        # Attach attribution info in result (DB attribution happens in the posting models separately)
        payload["trend_signal_id"] = req.trend_signal_id
        payload["trend_keyword"] = req.trend_keyword

        # Thread attribution into the created post docs (best-effort, non-fatal).
        try:
            await self._set_trend_attribution_on_posts(
                user_email=user_email,
                platform_results=list(payload.get("results") or []),
                trend_signal_id=req.trend_signal_id,
            )
        except Exception as e:
            logger.warning("Failed attaching trend attribution to posts (non-fatal): %s", str(e))

        return payload

    async def list_requests(self, *, user_email: str, limit: int = 50, skip: int = 0) -> Dict[str, Any]:
        rows = (
            await CampaignLaunchRequestModel.find(CampaignLaunchRequestModel.user_email == user_email)
            .sort(-CampaignLaunchRequestModel.created_at)
            .skip(skip)
            .limit(limit)
            .to_list()
        )
        total = await CampaignLaunchRequestModel.find(CampaignLaunchRequestModel.user_email == user_email).count()
        return {"rows": rows, "total": total}

