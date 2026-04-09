import { apiClient } from "./api";

export interface KPIMetric {
  label: string;
  value: number;
  prefix?: string;
  suffix?: string;
  change: string;
  trend: 'up' | 'down' | 'neutral';
  icon_type: 'revenue' | 'trends' | 'assets' | 'social' | 'campaigns';
}

export interface ConversionPing {
  latitude: number;
  longitude: number;
  revenue: number;
  platform: string;
  timestamp: string;
}

export interface CampaignHealth {
  campaign_id: string;
  name: string;
  roi: number;
  status: 'green' | 'yellow' | 'red';
  spend: number;
  revenue: number;
}

export interface StrategicInsight {
  id: string;
  type: 'action' | 'caution' | 'suggestion';
  title: string;
  message: string;
  impact: string;
  color: 'yellow' | 'red' | 'emerald';
}

export interface HeatmapRegion {
  id: string;
  name: string;
  score: number;
  urgency: string;
  trend: string;
}

export interface ScheduledPostItem {
  id: string;
  platform: string;
  media_url: string;
  caption?: string;
  time: string;
  status: string;
}

export interface CreativeVelocityPoint {
  type: string;
  value: number;
}

export interface PostingCadenceDay {
  day: string;
  posts: number;
}

export interface DashboardSummary {
  kpis: KPIMetric[];
  recent_pings: ConversionPing[];
  campaign_health: CampaignHealth[];
  strategic_insights: StrategicInsight[];
  
  // NEW
  top_regions: HeatmapRegion[];
  deployment_timeline: ScheduledPostItem[];
  posting_cadence: PostingCadenceDay[];
  
  last_updated: string;
}

class DashboardService {
  async getSummary(businessId?: string): Promise<DashboardSummary> {
    const url = businessId ? `/v1/dashboard-analytics/summary?business_id=${businessId}` : "/v1/dashboard-analytics/summary";
    return apiClient.get<DashboardSummary>(url);
  }

  getRealtimeSocket(token: string): WebSocket {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//localhost:8000/api/v1/dashboard-analytics/ws?token=${token}`;
    return new WebSocket(wsUrl);
  }
}

export const dashboardService = new DashboardService();
