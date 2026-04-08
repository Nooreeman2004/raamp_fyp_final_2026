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

    // Data quality / provenance (from /trends/live join)
    is_simulated?: boolean;
    is_real_events?: boolean;
    fetch_status?: string | null;
    error_message?: string | null;
    trend_signal_id?: string | null;
    event_score?: number;
    recommendations?: any;

    // AI analysis status (from /trends/latest join)
    ai_analysis_status?: "pending" | "ready" | "failed" | null;
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

export interface GeoHeatmapResponse {
    regions: GeoTrend[];
    count: number;
    is_real_geo: boolean;
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
    last_profit_score?: number;
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
    category?: string | null;
    category_confidence?: number | null;
    entities?: string[];
    matchup_hint?: string | null;
}

export type CampaignDraftKind = "carousel" | "reel" | "story";

export interface CampaignDraftItem {
    id: string;
    kind: CampaignDraftKind;
    title: string;
    trend_keyword?: string | null;
    niche?: string | null;
    location?: string | null;
    content: any;
    created_at: string;
    updated_at: string;
}

export interface TrendStatusResponse {
    trend_id: string;
    status: string;
    progress_step?: string;
    error_message?: string | null;
    ai_analysis_status?: "pending" | "ready" | "failed" | null;
}

export interface TrendingNowRelevantItem {
    term: string;
    score: number;
    matched_terms: string[];
}

export interface TrendingNowResponse {
    geo?: string | null;
    terms: string[];
    relevant: TrendingNowRelevantItem[];
    count: number;
}

export interface IndustryTrendsResponse {
    scope: string;
    niche: string;
    seed_keywords: string[];
    terms: string[];
    count: number;
    data_quality?: { is_real: boolean; source: string; notes?: string | null; flags?: Record<string, any> };
}

export interface TrendAIAnalysis {
    trend_id: string;
    user_id: string;
    trend_keyword: string;
    generated_at: string;
    status: "pending" | "completed" | "failed";

    executive_summary?: string | null;
    opportunity_score?: { urgency?: number; relevance?: number; competition?: number };
    market_context?: string | null;
    risk_level?: "flash" | "sustained" | "uncertain" | null;
    risk_explanation?: string | null;
    competitor_gap?: boolean | null;

    content_angles?: string[];
    platform_recommendations?: Array<{ platform: string; format: string; reason: string }>;
    hashtag_pack?: { primary?: string[]; secondary?: string[]; niche?: string[] };
    posting_window?: string | null;

    campaign_ideas?: Array<{ title: string; description: string; platform: string; urgency_tag: string }>;
    content_format_recommendation?: { primary_format?: string; secondary_format?: string; reasoning?: string[] };
    growth_hacks?: string[];
}

export const trendService = {
    getLiveTrends: async (location?: string, scope: "business" | "raw" = "business"): Promise<TrendSpike[]> => {
        const qs = new URLSearchParams();
        if (location) qs.set("location", location);
        if (scope) qs.set("scope", scope);
        const query = qs.toString() ? `?${qs.toString()}` : "";
        const data = await apiClient.get<{ trends: TrendSpike[]; count: number }>(`/trends/live${query}`);
        console.log('[trendService] getLiveTrends raw response:', data);
        const trends = (data as any)?.trends ?? (Array.isArray(data) ? data : []);
        console.log(`[trendService] getLiveTrends parsed: ${trends.length} trends`);
        return trends;
    },

    getTrendingNow: async (location?: string, category: string = "all", limit: number = 12): Promise<TrendingNowResponse> => {
        const qs = new URLSearchParams();
        if (location) qs.set("location", location);
        if (category) qs.set("category", category);
        if (limit) qs.set("limit", String(limit));
        const query = qs.toString() ? `?${qs.toString()}` : "";
        const data = await apiClient.get<TrendingNowResponse>(`/trends/trending_now${query}`);
        return {
            geo: (data as any)?.geo ?? null,
            terms: Array.isArray((data as any)?.terms) ? (data as any).terms : [],
            relevant: Array.isArray((data as any)?.relevant) ? (data as any).relevant : [],
            count: Number((data as any)?.count ?? 0) || 0,
        };
    },

    getIndustryTrends: async (niche: string, scope: string = "GLOBAL", timeframe: string = "7d", limit: number = 12): Promise<IndustryTrendsResponse> => {
        const qs = new URLSearchParams();
        qs.set("niche", niche);
        qs.set("scope", scope);
        qs.set("timeframe", timeframe);
        qs.set("limit", String(limit));
        const data = await apiClient.get<IndustryTrendsResponse>(`/trends/industry_trends?${qs.toString()}`);
        return {
            scope: String((data as any)?.scope || scope),
            niche: String((data as any)?.niche || niche),
            seed_keywords: Array.isArray((data as any)?.seed_keywords) ? (data as any).seed_keywords : [],
            terms: Array.isArray((data as any)?.terms) ? (data as any).terms : [],
            count: Number((data as any)?.count ?? 0) || 0,
            data_quality: (data as any)?.data_quality || undefined,
        };
    },

    getGeoHeatmap: async (location?: string): Promise<GeoHeatmapResponse> => {
        const query = location ? `?location=${location}` : '';
        const data = await apiClient.get<GeoHeatmapResponse>(`/trends/heatmap${query}`);
        console.log('[trendService] getGeoHeatmap raw response:', data);
        const regions = (data as any)?.regions ?? (Array.isArray(data) ? data : []);
        const isReal = Boolean((data as any)?.is_real_geo);
        console.log(`[trendService] getGeoHeatmap parsed: ${regions.length} regions (is_real_geo=${isReal})`);
        return {
            regions,
            count: Number((data as any)?.count ?? regions.length) || regions.length,
            is_real_geo: isReal,
        };
    },

    getSpikeTimeline: async (
        days: number = 30,
        location?: string
    ): Promise<{ timeline: SpikeTimeline[]; lastSuccessfulScanAt: string | null }> => {
        const query = `?days=${days}${location ? `&location=${location}` : ''}`;
        const data = await apiClient.get<{
            timeline: SpikeTimeline[];
            count: number;
            last_successful_scan_at?: string | null;
        }>(`/trends/spike_timeline${query}`);
        console.log('[trendService] getSpikeTimeline raw response:', data);
        const timeline = (data as any)?.timeline ?? (Array.isArray(data) ? data : []);
        const lastSuccessfulScanAt =
            (data as any)?.last_successful_scan_at !== undefined && (data as any)?.last_successful_scan_at !== null
                ? String((data as any).last_successful_scan_at)
                : null;
        console.log(`[trendService] getSpikeTimeline parsed: ${timeline.length} entries`);
        return { timeline, lastSuccessfulScanAt };
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

    triggerFetch: async (
        niche: string,
        category: string = "all",
        timeframe?: string,
        opts?: { discovery_mode?: boolean; custom_keywords?: string[] }
    ): Promise<any> => {
        return apiClient.post('/trends/fetch', {
            niche,
            category,
            timeframe,
            discovery_mode: Boolean(opts?.discovery_mode),
            custom_keywords: Array.isArray(opts?.custom_keywords) ? opts?.custom_keywords : [],
        });
    },

    getTrendStatus: async (trendId: string): Promise<TrendStatusResponse> => {
        return apiClient.get<TrendStatusResponse>(`/trends/${trendId}/status`);
    },

    // --- AI ANALYSIS ---
    getAIAnalysis: async (trendId: string): Promise<TrendAIAnalysis> => {
        return apiClient.get<TrendAIAnalysis>(`/trends/${trendId}/ai-analysis`);
    },

    regenerateAIAnalysis: async (trendId: string): Promise<{ success: boolean; status: string }> => {
        return apiClient.post(`/trends/${trendId}/ai-analysis/regenerate`, {});
    },

    // --- INTELLIGENCE ---
    getViralAudio: async (platform: string, geo: string, niche: string): Promise<any> => {
        const qs = new URLSearchParams({ platform, geo, niche }).toString();
        return apiClient.get(`/trends/viral-audio?${qs}`);
    },

    getInfluencerRadar: async (geo: string, niche: string, keyword?: string): Promise<any> => {
        const qs = new URLSearchParams({ geo, niche, ...(keyword ? { keyword } : {}) }).toString();
        return apiClient.get(`/trends/influencer-radar?${qs}`);
    },

    // --- EXECUTE (STREAMING) ---
    streamExecute: async (
        trendId: string,
        kind: "draft-caption" | "generate-hooks" | "blog-outline" | "ad-copy",
        opts?: { tone_override?: string; onChunk?: (chunk: string) => void }
    ): Promise<string> => {
        const token = localStorage.getItem("token");
        const res = await fetch(`${(import.meta as any).env.VITE_API_BASE_URL || "/api"}/trends/${trendId}/execute/${kind}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
            body: JSON.stringify({ tone_override: opts?.tone_override }),
            credentials: "include",
        });
        if (!res.ok) {
            const txt = await res.text();
            throw new Error(txt || `Execute failed (${res.status})`);
        }
        const reader = res.body?.getReader();
        if (!reader) {
            const txt = await res.text();
            return txt;
        }
        const decoder = new TextDecoder();
        let out = "";
        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value, { stream: true });
            out += chunk;
            opts?.onChunk?.(chunk);
        }
        return out;
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
    },

    // --- ACTIVITY HISTORY ---
    getTrendHistory: async (limit: number = 50): Promise<any[]> => {
        return apiClient.get<any[]>(`/trends/activity/history?limit=${limit}`);
    },

    logTrendActivity: async (data: {
        trend_keyword: string;
        trend_source: string;
        generated_prompt: string;
        niche: string;
        location: string;
    }): Promise<any> => {
        const query = new URLSearchParams(data).toString();
        return apiClient.post(`/trends/activity/log?${query}`, {});
    },

    // --- DRAFTS / CREATE PACK ---
    createPackDrafts: async (payload: {
        trend_keyword: string;
        niche: string;
        location: string;
        suggested_hashtags?: string[];
        suggested_caption?: string;
        platform?: string;
    }): Promise<{ drafts: CampaignDraftItem[] }> => {
        return apiClient.post(`/campaign-drafts/create-pack`, payload);
    },

    listCampaignDrafts: async (params?: { kind?: CampaignDraftKind; limit?: number; skip?: number }): Promise<{ drafts: CampaignDraftItem[]; total: number }> => {
        const qs = new URLSearchParams();
        if (params?.kind) qs.set("kind", params.kind);
        if (typeof params?.limit === "number") qs.set("limit", String(params.limit));
        if (typeof params?.skip === "number") qs.set("skip", String(params.skip));
        const query = qs.toString() ? `?${qs.toString()}` : "";
        return apiClient.get(`/campaign-drafts${query}`);
    },
};
