import { apiClient } from './api';

export interface SignalBreakdown {
  trends_score: number;
  places_score: number;
  weather_score: number;
}

export interface SignalsStatus {
  trends: string;
  places: string;
  weather: string;
}

export interface PersonaEntry {
  type: string;
  pct: number;
  desc: string;
}

export interface RadarSignal {
  id: string;
  time: string;
  msg: string;
  type: 'info' | 'alert' | 'success';
}

export interface ZoneResult {
  label: string;
  latitude: number;
  longitude: number;
  score: number;
  urgency: string;
  reason: string;
  signals: SignalBreakdown;
}

export interface ZoneRecommendationResponse {
  zones: ZoneResult[];
  center_lat: number;
  center_lng: number;
  radius_m: number;
  timestamp: string;
}

export interface HeatScoreResponse {
  score: number;
  urgency: string;
  is_critical: boolean;
  latitude: number;
  longitude: number;
  radius_km: number;
  signals: SignalBreakdown;
  signals_status: SignalsStatus;
  reasoning?: string;
  persona_split?: PersonaEntry[];
  radar_feed?: RadarSignal[];
  timestamp: string;
}

export interface HeatmapFeature {
  type: string;
  geometry: {
    type: string;
    coordinates: [number, number];
  };
  properties: {
    score: number;
    urgency: string;
    zone: string;
    timestamp: string;
  };
}

export interface HeatmapResponse {
  type: string;
  features: HeatmapFeature[];
}

export interface CampaignLogEntry {
  business_id: string;
  keywords: string[];
  radius: number;
  final_score: number;
  urgency: string;
  is_indoor: boolean;
  signals: SignalBreakdown;
  timestamp: string;
}

export interface CampaignHistoryResponse {
  business_id: string;
  total: number;
  logs: CampaignLogEntry[];
}

export interface CampaignBrief {
  id?: string;
  campaign_id?: string;
  business_id: string;
  user_email: string;
  location: {
    type: string;
    coordinates: [number, number];
  };
  radius_km: number;
  zone_label: string;
  coordinates_display: string;
  heat_score: number;
  urgency: string;
  trends_score: number;
  weather_score: number;
  places_score: number;
  dominant_persona: string;
  dominant_persona_pct: number;
  persona_split: PersonaEntry[];
  strategy_rationale: string;
  reasoning: string;
  caption_variants?: {
    aggressive: string;
    soft: string;
    urgency: string;
  };
  caption: string;
  hashtags: string[];
  best_time_window: string;
  suggested_budget_min: number;
  suggested_budget_max: number;
  meta_objective: string;
  meta_deep_link: string;
  timestamp: string;
}

export const geoIntentService = {
  getHeatScore: async (payload: {
    business_id: string;
    keywords: string[];
    latitude: number;
    longitude: number;
    radius: number;
    is_indoor: boolean;
  }): Promise<HeatScoreResponse> => {
    return apiClient.post<HeatScoreResponse>('/v1/geo/heat-score', payload);
  },

  getHeatmap: async (businessId?: string, limit: number = 100): Promise<HeatmapResponse> => {
    const query = new URLSearchParams();
    if (businessId) query.append('business_id', businessId);
    query.append('limit', limit.toString());
    return apiClient.get<HeatmapResponse>(`/v1/geo/heatmap?${query.toString()}`);
  },

  getHistory: async (businessId: string, limit: number = 50): Promise<CampaignHistoryResponse> => {
    return apiClient.get<CampaignHistoryResponse>(`/v1/geo/history/${businessId}?limit=${limit}`);
  },

  getHeatScoreHistory: async (businessId: string, days: number = 7): Promise<Array<{date: string, max_score: number, urgency: string}>> => {
    return apiClient.get<Array<{date: string, max_score: number, urgency: string}>>(`/v1/geo/heat-score/history/${businessId}?days=${days}`);
  },

  getBestPostingTime: async (businessId: string): Promise<{
    best_hours: Array<{hour: number, avg_score: number}>,
    best_day: string,
    based_on_days: number
  }> => {
    return apiClient.get(`/v1/geo/best-posting-time/${businessId}`);
  },

  generateCampaignBrief: async (payload: any): Promise<CampaignBrief> => {
    return apiClient.post<CampaignBrief>('/v1/geo/generate-campaign-brief', payload);
  },

  getCampaignBriefHistory: async (businessId: string, limit: number = 20): Promise<CampaignBrief[]> => {
    return apiClient.get<CampaignBrief[]>(`/v1/geo/campaign-briefs/${businessId}?limit=${limit}`);
  },

  getCampaignBriefById: async (briefId: string): Promise<CampaignBrief> => {
    return apiClient.get<CampaignBrief>(`/v1/geo/campaign-brief/${briefId}`);
  },

  recommendZones: async (payload: {
    business_id: string;
    keywords: string[];
    latitude: number;
    longitude: number;
    radius: number;
    is_indoor: boolean;
  }): Promise<ZoneRecommendationResponse> => {
    return apiClient.post<ZoneRecommendationResponse>('/v1/geo/recommend-zones', payload);
  },
};
