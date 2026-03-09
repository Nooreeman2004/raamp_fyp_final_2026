import { apiClient } from './api';

export type LifecycleStage = "Emerging" | "Breakout" | "Mainstream" | "Saturated" | "Declining";
export type Timeframe = "24h" | "7d" | "30d" | "90d";

export interface TrendSpike {
    id: string;
    keyword: string;
    niche: string;
    location: string;
    score: number;
    impact: string;
    current_value: number;
    detected_at: string;
    is_spike?: boolean;
    label?: string;
    sentiment?: string;
    confidence?: number;
    rising_queries?: string[];
    profitability?: number;
    time_diff?: string;
    is_real_social?: boolean;
    is_real_saturation?: boolean;
    
    // Enhancement Fields (All 10 Features)
    z_score_spike?: number;           // Z-Score spike indicator
    arbitrage_score?: number;         // Arbitrage opportunity score
    saturation_score?: number;        // Market saturation percentage
    social_score?: number;            // Social media engagement score
    lifecycle_stage?: LifecycleStage; // Current lifecycle phase
    predicted_growth_pct?: number;    // 7-day growth prediction %
    breakout_probability?: number;    // Probability of breakout (0-100)
    profit_score?: number;            // Profit potential score (0-100)
    forecast_series?: number[];       // 7-day forecast data points
    timeframe?: Timeframe;            // Time window for analysis
}

export interface PlatformReach {
    google: number;
    instagram: number;
    facebook: number;
    total_reach: string;
}

export interface GeoTrend {
    keyword: string;
    city: string;
    intensity: number;
    x?: number;
    y?: number;
    delta?: string;
    velocity?: string;
}

export interface SpikeTimeline {
    date: string;
    count: number;
    avg_z: number;
}

export interface MarketGap {
    keyword: string;
    velocity: number;       // Y-axis (Z-Score)
    saturation: number;     // X-axis (Current Value)
    arbitrage_score: number;// Bubble size
    quadrant: string;       // Color logic
    impact: string;
    is_real_social?: boolean;
    is_real_saturation?: boolean;
    
    // Enhancement Fields
    lifecycle_stage?: LifecycleStage;
    profit_score?: number;
    predicted_growth_pct?: number;
    breakout_probability?: number;
}

export interface CampaignRecommendation {
    trend_name: string;
    campaign_idea: string;
    recommended_platform: string;
    reasoning: string;
    expected_marketing_goal: string;
    suggested_hooks: string[];
    estimated_effort: string;
    priority: number;
}

export interface ArbitrageRecommendationResponse {
    recommendations: CampaignRecommendation[];
    context: string;
}

export interface WatchlistItem {
    id: string;
    keyword: string;
    niche: string;
    location: string;
    last_velocity: number;
    last_saturation: number;
    last_arbitrage_score: number;
    is_active: boolean;
    created_at: string;
}

export interface ContentSuggestion {
    keyword: string;
    video_ideas: string[];
    hooks: string[];
    hashtags: string[];
    campaign_angle: string;
    influencer_strategy: string;
    lifecycle_stage: string;
    profit_score: number;
}

export interface TrendExplainRequest {
    keyword: string;
    niche: string;
    location?: string;
    lifecycle_stage?: string;
    breakout_probability?: number;
    profit_score?: number;
    competition?: number;
    buzz?: number;
}

export interface TrendExplainResponse {
    keyword: string;
    explanation: string;
    why_now: string;
    content_prompt: string;
}

export interface TrendStatusResponse {
    trend_id: string;
    status: string;
    error_message?: string | null;
}

export const trendService = {
    getLiveTrends: async (location?: string): Promise<TrendSpike[]> => {
        const query = location ? `?location=${location}` : '';
        const data = await apiClient.get<{ trends: TrendSpike[]; count: number }>(`/trends/live${query}`);
        console.log('[trendService] getLiveTrends raw response:', data);
        const trends = (data as any)?.trends ?? (Array.isArray(data) ? data : []);
        console.log(`[trendService] getLiveTrends parsed: ${trends.length} trends`);
        return trends;
    },

    getGeoHeatmap: async (location?: string): Promise<GeoTrend[]> => {
        const query = location ? `?location=${location}` : '';
        const data = await apiClient.get<{ regions: GeoTrend[]; count: number }>(`/trends/heatmap${query}`);
        console.log('[trendService] getGeoHeatmap raw response:', data);
        const regions = (data as any)?.regions ?? (Array.isArray(data) ? data : []);
        console.log(`[trendService] getGeoHeatmap parsed: ${regions.length} regions`);
        return regions;
    },

    getSpikeTimeline: async (days: number = 30, location?: string): Promise<SpikeTimeline[]> => {
        const query = `?days=${days}${location ? `&location=${location}` : ''}`;
        const data = await apiClient.get<{ timeline: SpikeTimeline[]; count: number }>(`/trends/spike_timeline${query}`);
        console.log('[trendService] getSpikeTimeline raw response:', data);
        const timeline = (data as any)?.timeline ?? (Array.isArray(data) ? data : []);
        console.log(`[trendService] getSpikeTimeline parsed: ${timeline.length} entries`);
        return timeline;
    },

    getMarketGapData: async (location?: string): Promise<MarketGap[]> => {
        const query = location ? `?location=${location}` : '';
        const data = await apiClient.get<{ opportunities: MarketGap[]; count: number }>(`/trends/bubble_chart${query}`);
        console.log('[trendService] getMarketGapData raw response:', data);
        const opportunities = (data as any)?.opportunities ?? (Array.isArray(data) ? data : []);
        console.log(`[trendService] getMarketGapData parsed: ${opportunities.length} opportunities`);
        return opportunities;
    },

    getPlatformReach: async (location?: string): Promise<PlatformReach> => {
        const query = location ? `?location=${location}` : '';
        const data = await apiClient.get<PlatformReach>(`/trends/platform_reach${query}`);
        console.log('[trendService] getPlatformReach raw response:', data);
        return data;
    },

    getRecommendations: async (user_profile: any, trend_signals: any[]): Promise<ArbitrageRecommendationResponse> => {
        return apiClient.post('/arbitrage/recommendations', { user_profile, trend_signals });
    },

    triggerFetch: async (niche: string, location: string, category: string = "all"): Promise<any> => {
        return apiClient.post('/trends/fetch', { niche, location, category });
    },

    getTrendStatus: async (trendId: string): Promise<TrendStatusResponse> => {
        return apiClient.get<TrendStatusResponse>(`/trends/${trendId}/status`);
    },

    // --- WATCHLIST ---
    getWatchlist: async (): Promise<WatchlistItem[]> => {
        return apiClient.get<WatchlistItem[]>('/trends/watchlist/');
    },

    addTrendToWatchlist: async (data: { keyword: string, niche?: string, location?: string }): Promise<WatchlistItem> => {
        return apiClient.post<WatchlistItem>('/trends/watchlist/', data);
    },

    removeFromWatchlist: async (keyword: string): Promise<any> => {
        return apiClient.delete(`/trends/watchlist/${keyword}`);
    },

    // --- CONTENT SUGGESTIONS ---
    getContentSuggestions: async (keyword: string): Promise<ContentSuggestion> => {
        return apiClient.post<ContentSuggestion>('/trends/suggest', { keyword });
    },

    // --- TREND EXPLANATION ---
    getTrendExplanation: async (req: TrendExplainRequest): Promise<TrendExplainResponse> => {
        return apiClient.post<TrendExplainResponse>('/trends/explain', req);
    },

    // --- BUSINESS SPECIALTIES ---
    getBusinessSpecialties: async (): Promise<{ success: boolean; message: string; specialties: string[] }> => {
        return apiClient.get('/settings/business/specialties');
    },

    updateBusinessSpecialties: async (specialties: string[]): Promise<{ success: boolean; message: string; specialties: string[] }> => {
        return apiClient.patch('/settings/business/specialties', { specialties });
    }
};
