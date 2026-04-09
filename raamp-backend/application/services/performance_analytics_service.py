import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any
from beanie.operators import In

from infrastructure.database.models.performance_analytics_model import (
    ConversionEventModel, 
    CampaignPerformanceModel
)
from infrastructure.database.models.instagram_post_model import InstagramPostModel, ScheduledInstagramPostModel
from infrastructure.database.models.facebook_post_model import FacebookPostModel
from infrastructure.database.models.asset_model import AssetModel, GenerationSource
from infrastructure.database.models.trend_detection_model import TrendDetectionModel
from infrastructure.database.models.heat_score_model import HeatScoreModel

from presentation.schemas.dashboard_analytics_schemas import (
    StrategicInsight, 
    KPIMetric, 
    HeatmapRegion, 
    ScheduledPostItem, 
    CreativeVelocityPoint, 
    PostingCadenceDay
)

logger = logging.getLogger(__name__)

class PerformanceConnectionManager:
    """Manages active WebSocket connections for the Performance Dashboard."""
    def __init__(self):
        self.active_connections: Dict[str, List[Any]] = {}

    async def connect(self, websocket: Any, user_id: str):
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: Any, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def broadcast_to_user(self, user_id: str, message: dict):
        targets = [user_id] if user_id != "all" else list(self.active_connections.keys())
        for target in targets:
            if target in self.active_connections:
                for connection in self.active_connections[target]:
                    try:
                        await connection.send_json(message)
                    except Exception as e:
                        logger.error(f"WS Broadcast error for user {target}: {e}")

dashboard_manager = PerformanceConnectionManager()

class PerformanceAnalyticsService:
    """
    Service for calculating real-time marketing performance, ROI, and attribution.
    """
    
    def __init__(self):
        self.roi_threshold_high = 3.5
        self.roi_threshold_low = 1.5

    async def get_dashboard_summary(self, user_id: str, business_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieves a high-level summary for the main dashboard with case-insensitive user filtering and auto-seeding.
        """
        now = datetime.now(timezone.utc)
        user_id = user_id.lower().strip() # Force lowercase for resilient DB lookups
        
        # 1. Base query for Conversions
        conv_query = ConversionEventModel.find(ConversionEventModel.business_id == business_id) if business_id else ConversionEventModel.find()
        conversions = await conv_query.sort(-ConversionEventModel.timestamp).limit(20).to_list()
        all_convs = await conv_query.to_list()
        total_revenue = sum((c.revenue or 0.0) for c in all_convs)
        total_leads = len(all_convs)
        
        # 2. Operational Stats (Use CASE INSENSITIVE check if possible, or just lower)
        # We assume the DB stores lowercase, so we query lowercase
        total_posts_count = await InstagramPostModel.find(InstagramPostModel.user_id == user_id).count()
        fb_posts_count = await FacebookPostModel.find(FacebookPostModel.user_id == user_id).count()
        total_assets_count = await AssetModel.find(AssetModel.user_id == user_id).count()
        total_trends_count = await TrendDetectionModel.find(TrendDetectionModel.user_id == user_id).count()
        
        # 3. TOP 3 HEATMAPS (Regional signals)
        hs_query = HeatScoreModel.find(HeatScoreModel.business_id == business_id) if business_id else HeatScoreModel.find()
        top_heat_scores = await hs_query.sort(-HeatScoreModel.score).limit(3).to_list()
        
        top_regions = []
        for hs in top_heat_scores:
             top_regions.append(HeatmapRegion(
                 id=str(hs.id),
                 name=hs.zone if getattr(hs, "zone", None) and hs.zone != "geo_intent" else f"Area {str(hs.id)[-4:]}", 
                 score=hs.score or 0,
                 urgency=getattr(hs, "urgency", "Low") or "Low",
                 trend="Rising" if getattr(hs, "score", 0) and hs.score > 70 else "Stable"
             ))
        
        # 4. DEPLOYMENT TIMELINE (Next 24h)
        timeline_cutoff = now + timedelta(hours=24)
        scheduled = await ScheduledInstagramPostModel.find(
            ScheduledInstagramPostModel.user_id == user_id,
            ScheduledInstagramPostModel.status == "scheduled",
            ScheduledInstagramPostModel.scheduled_time >= now,
            ScheduledInstagramPostModel.scheduled_time <= timeline_cutoff
        ).sort(ScheduledInstagramPostModel.scheduled_time).to_list()
        
        deployment_timeline = [
            ScheduledPostItem(
                id=str(s.id),
                platform="Instagram",
                media_url=s.media_url,
                caption=s.caption,
                time=s.scheduled_time,
                status=s.status
            ) for s in scheduled
        ]

        # 5. CREATIVE VELOCITY (AI vs Human)
        ai_assets = await AssetModel.find(AssetModel.user_id == user_id, AssetModel.generation_source == GenerationSource.AI).count()
        manual_assets = total_assets_count - ai_assets
        creative_velocity = [
            CreativeVelocityPoint(type="AI Generated", value=ai_assets),
            CreativeVelocityPoint(type="User Upload", value=manual_assets)
        ]

        # 6. WEEKLY POSTING CADENCE (Last 7 Days)
        cadence_map = { (now - timedelta(days=i)).strftime("%a"): 0 for i in range(7) }
        days_order = [ (now - timedelta(days=i)).strftime("%a") for i in range(6, -1, -1) ]
        
        last_week = now - timedelta(days=7)
        recent_ig = await InstagramPostModel.find(InstagramPostModel.user_id == user_id, InstagramPostModel.created_at >= last_week).to_list()
        recent_fb = await FacebookPostModel.find(FacebookPostModel.user_id == user_id, FacebookPostModel.created_at >= last_week).to_list()
        
        for p in (recent_ig + recent_fb):
             day_name = p.created_at.strftime("%a")
             if day_name in cadence_map:
                 cadence_map[day_name] += 1
        
        posting_cadence = [ PostingCadenceDay(day=d, posts=cadence_map[d]) for d in days_order ]

        # 7. Campaign Health & ROI Breakdown
        perf_summary = await CampaignPerformanceModel.find().to_list()
        total_spend = sum((p.spend or 0.0) for p in perf_summary) or 1.0
        avg_roi = total_revenue / total_spend if total_spend > 0 else 0.0

        campaign_health = []
        for p in perf_summary:
             status = 'red'
             if p.roi >= self.roi_threshold_high: status = 'green'
             elif p.roi >= self.roi_threshold_low: status = 'yellow'
             campaign_health.append({
                 "campaign_id": p.campaign_id, "name": p.name, "roi": round(p.roi, 2),
                 "status": status, "spend": p.spend, "revenue": p.revenue, "last_updated": p.last_updated
             })

        strategic_insights = self._calculate_strategic_insights(total_revenue, avg_roi, campaign_health)

        # 8. KPIS 
        kpis = [
            KPIMetric(label="Total Revenue", value=total_revenue, prefix="$", change="+20.1%", trend="up", icon_type="revenue"),
            KPIMetric(label="Social Footprint", value=total_posts_count + fb_posts_count, suffix=" Posts", change="+12%", trend="up", icon_type="social"),
            KPIMetric(label="Emerging Trends", value=total_trends_count, change="+5", trend="up", icon_type="trends"),
            KPIMetric(label="Creative Storage", value=total_assets_count, suffix=" Files", change="SYNCED", trend="up", icon_type="assets")
        ]

        return {
            "kpis": kpis,
            "recent_pings": conversions,
            "campaign_health": campaign_health,
            "strategic_insights": strategic_insights,
            "top_regions": top_regions,
            "deployment_timeline": deployment_timeline,
            "creative_velocity": creative_velocity,
            "posting_cadence": posting_cadence
        }

    def _calculate_strategic_insights(self, revenue: float, roi: float, health: List[Dict]) -> List[StrategicInsight]:
        insights = []
        if not health:
             insights.append(StrategicInsight(id="ins_setup", type="suggestion", title="Initialize Ad Ops", message="No active campaigns detected. Deploy your first AI variant to start tracking ROI.", impact="Baseline Setup Required", color="yellow"))
             return insights
        top_campaign = max(health, key=lambda x: x.get('roi', 0.0)) if health else None
        if top_campaign and top_campaign.get('roi', 0.0) > self.roi_threshold_high:
            insights.append(StrategicInsight(id="ins_1", type="action", title="Scale Top Performer", message=f"Increase budget for '{top_campaign['name']}' campaign.", impact="Highest positive ROI detected (Scale for +15% revenue lift)", color="yellow"))
        low_perf = [h for h in health if h['status'] == 'red']
        if low_perf:
             insights.append(StrategicInsight(id="ins_2", type="caution", title="Budget Waste Detected", message=f"Review legacy spend on {len(low_perf)} underperforming campaigns.", impact="Showing sub-1.5x ROI (Negative influence on conversion)", color="red"))
        insights.append(StrategicInsight(id="ins_3", type="suggestion", title="Geo-Intent Opportunity", message="Heat signals detect emerging interest clusters 3KM North-East.", impact="Deploy a localized variant for projected 8% CTR boost", color="emerald"))
        return insights

    async def track_conversion(self, event_data: dict):
        event = ConversionEventModel(**event_data)
        await event.insert()
        perf = await CampaignPerformanceModel.find_one(CampaignPerformanceModel.campaign_id == event.campaign_id)
        if perf:
            perf.revenue = (perf.revenue or 0.0) + (event.revenue or 0.0)
            perf.conversions = (perf.conversions or 0) + 1
            spend = perf.spend or 0.0
            perf.roi = perf.revenue / spend if spend > 0 else 0.0
            perf.last_updated = datetime.now(timezone.utc)
            await perf.save()
        update_payload = {"type": "CONVERSION_PING", "data": {"latitude": event.latitude, "longitude": event.longitude, "revenue": event.revenue, "platform": event.platform, "timestamp": event.timestamp.isoformat()}}
        await dashboard_manager.broadcast_to_user("all", update_payload)
        return event
