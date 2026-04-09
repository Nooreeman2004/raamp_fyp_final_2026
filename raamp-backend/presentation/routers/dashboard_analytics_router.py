import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query, HTTPException, status
from typing import List, Optional

from presentation.routers.auth_router import get_current_user_email
from application.services.performance_analytics_service import PerformanceAnalyticsService, dashboard_manager
from presentation.schemas.dashboard_analytics_schemas import (
    DashboardSummaryResponse, 
    ConversionLogRequest,
    KPIMetric,
    ConversionEvent,
    CampaignHealth,
    StrategicInsight,
    HeatmapRegion,
    ScheduledPostItem,
    CreativeVelocityPoint,
    PostingCadenceDay
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/dashboard-analytics", tags=["Home Dashboard Analytics"])
service = PerformanceAnalyticsService()

@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    business_id: Optional[str] = None,
    current_user_email: str = Depends(get_current_user_email)
):
    try:
        data = await service.get_dashboard_summary(user_id=current_user_email, business_id=business_id)
        
        return DashboardSummaryResponse(
            kpis=[KPIMetric(**k.model_dump() if hasattr(k, "model_dump") else k) for k in data["kpis"]],
            recent_pings=[
                ConversionEvent(
                    id=str(c.id), campaign_id=c.campaign_id, business_id=c.business_id,
                    revenue=c.revenue, latitude=c.latitude, longitude=c.longitude,
                    platform=c.platform, timestamp=c.timestamp
                ) for c in data["recent_pings"]
            ],
            campaign_health=[CampaignHealth(**ch) for ch in data["campaign_health"]],
            strategic_insights=[StrategicInsight(**si.model_dump() if hasattr(si, "model_dump") else si) for si in data["strategic_insights"]],
            top_regions=[HeatmapRegion(**tr.model_dump() if hasattr(tr, "model_dump") else tr) for tr in data["top_regions"]],
            deployment_timeline=[ScheduledPostItem(**dt.model_dump() if hasattr(dt, "model_dump") else dt) for dt in data["deployment_timeline"]],
            creative_velocity=[CreativeVelocityPoint(**cv.model_dump() if hasattr(cv, "model_dump") else cv) for cv in data["creative_velocity"]],
            posting_cadence=[PostingCadenceDay(**pc.model_dump() if hasattr(pc, "model_dump") else pc) for pc in data["posting_cadence"]],
            last_updated=datetime.now(timezone.utc)
        )
    except Exception as e:
        import traceback
        logger.error(f"Failed to fetch dashboard summary: {e}")
        logger.error(traceback.format_exc())
        
        # Safe fallback response if data is missing or crashes
        return DashboardSummaryResponse(
            kpis=[],
            recent_pings=[],
            campaign_health=[],
            strategic_insights=[
                StrategicInsight(
                    id="ins_fallback",
                    type="caution",
                    title="Analytics Degraded",
                    message="Dashboard is running in offline mode due to an internal calculation issue.",
                    impact="Metrics may appear empty. Engineering has been notified.",
                    color="red"
                )
            ],
            top_regions=[],
            deployment_timeline=[],
            creative_velocity=[],
            posting_cadence=[],
            last_updated=datetime.now(timezone.utc)
        )

@router.post("/conversion", status_code=status.HTTP_201_CREATED)
async def simulate_conversion(
    request: ConversionLogRequest,
    current_user_email: str = Depends(get_current_user_email)
):
    try:
        event = await service.track_conversion(request.model_dump())
        return {"success": True, "event_id": str(event.id)}
    except Exception as e:
        logger.error(f"Failed to track conversion: {e}")
        raise HTTPException(status_code=500, detail="Failed to log conversion event")

@router.websocket("/ws")
async def dashboard_websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(None)
):
    await websocket.accept()
    user_email = "anonymous"
    try:
         from application.services.jwt_service import JWTService
         jwt_service = JWTService()
         if token:
             payload = jwt_service.verify_token(token)
             if payload: user_email = payload.get("email")
    except Exception as e:
        logger.error(f"Dashboard WS Auth Exception: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    if user_email == "anonymous":
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await dashboard_manager.connect(websocket, user_email)
    try:
        while True: await websocket.receive_text()
    except WebSocketDisconnect: dashboard_manager.disconnect(websocket, user_email)
    except Exception as e:
        logger.error(f"Dashboard WS Error: {e}")
        dashboard_manager.disconnect(websocket, user_email)
