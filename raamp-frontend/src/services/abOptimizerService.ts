/**
 * A/B Optimizer Service
 * Handles API calls for restaurant marketing image analysis and A/B test recommendations
 */

const API_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/api\/?$/, '');

// Helper to get auth token from storage
const getAuthToken = (): string | null => {
    return localStorage.getItem('token') || sessionStorage.getItem('token');
};

// TypeScript interfaces

export interface ImageScore {
    restaurant_relevance: number;
    viral_potential: number;
    aesthetic_quality: number;
    composite_score: number;
}

export interface ImageAnalysis {
    image_id: string;
    filename: string;
    content_type: 'food' | 'poster' | 'interior' | 'menu' | 'people' | 'other';
    scores: ImageScore;
    why_good: string;
    why_bad: string;
    recommendation: string;
    relevance_level?: 'relevant' | 'weak' | 'not_relevant';
    score_grade?: 'excellent' | 'good' | 'poor';
    image_url?: string;
}

export interface BatchAnalysisResponse {
    batch_id: string;
    images: ImageAnalysis[];
    total_images: number;
    recommended_pair?: string[];  // Top 2 image IDs to A/B test
    score_gap?: number;
    test_advice?: string;
    irrelevant_images: Array<{
        filename: string;
        relevance_score: number;
        reason: string;
    }>;
}

export interface BatchSummary {
    batch_id: string;
    image_count: number;
    created_at: string;
    recommended_pair?: string[];
    score_gap?: number;
    schedule_id?: string;
}

export interface CostEstimate {
    num_images: number;
    estimated_cost_usd: number;
    cost_per_image_usd: number;
    model: string;
}

export interface HealthCheckResponse {
    status: 'healthy' | 'unavailable' | 'error';
    service?: string;
    model?: string;
    features?: string[];
    error?: string;
}

export interface ScoringConfig {
    thresholds: {
        relevance: { good: number; weak: number };
        composite: { excellent: number; good: number };
    };
    levels: {
        relevance: string[];
        grade: string[];
    };
}

// =====================================================
// Stage 2-6 Interfaces
// =====================================================

export interface ScheduleRecommendation {
    days: string;   // backend returns comma-separated string
    time_range: string;
    confidence: string;
    source: string;
    next_optimal: {
        day: string;
        time: string;
    };
}

export interface ScheduleConfirmation {
    schedule_id: string;
    status: string;
    post_time: string;
    message: string;
}

export interface ScheduleStatus {
    schedule_id: string;
    batch_id: string;
    variant_a_image_id: string;
    variant_b_image_id: string;
    platform: string;
    post_time: string;
    variant_a_post_time: string;
    variant_b_post_time: string;
    test_duration_hours: number;
    status: string;
    created_at: string;
    monitoring_start_time?: string;
    monitoring_end_time?: string;
    caption_a?: string;
    caption_b?: string;
    pre_ranking?: {
        recommended_variant: 'variant_a' | 'variant_b';
        score_gap: number;
        confidence: 'close' | 'moderate' | 'strong';
        variant_a_composite: number;
        variant_b_composite: number;
    };
    variant_a_analysis?: {
        filename?: string | null;
        image_url?: string | null;
        composite_score: number;
        restaurant_relevance: number;
        viral_potential: number;
        aesthetic_quality: number;
    };
    variant_b_analysis?: {
        filename?: string | null;
        image_url?: string | null;
        composite_score: number;
        restaurant_relevance: number;
        viral_potential: number;
        aesthetic_quality: number;
    };
    stats_template?: {
        fields: string[];
        formula: string;
        notes: string;
    };
    meta_ads_link?: string;
    variant_a_ads_link?: string;
    variant_b_ads_link?: string;
    result?: {
        result_id: string;
        winner_image_id: string;
        winner?: string;
        delta_percentage?: number;
        confidence_level?: string;
        variant_a_metrics?: Record<string, number>;
        variant_b_metrics?: Record<string, number>;
    } | null;
}

export interface EngagementMetrics {
    likes: number;
    comments: number;
    shares: number;
    saves: number;
    reach: number;
    ctr: number;
}

export interface WinnerResult {
    result_id: string;
    winner: 'variant_a' | 'variant_b';
    winner_image_id: string;
    loser_image_id: string;
    delta_percentage: number;
    confidence_level: 'too_close' | 'moderate' | 'clear_winner';
    variant_a_composite: number;
    variant_b_composite: number;
    recommendation: string;
}

export interface AdBrief {
    brief_id: string;
    winning_image_id: string;
    target_geo: string;
    audience_segment: string;
    suggested_budget_daily: number;
    suggested_duration_days: number;
    total_spend: number;
    estimated_reach: number;
    estimated_clicks: number;
    estimated_ctr: number;
    estimated_cost_per_click: number;
    creative_hook: string;
    cta_recommendation: string;
    what_not_to_change: string;
    platform: string;
    meta_ads_link: string;
}

export const abOptimizerService = {
    /**
     * Upload and analyze 2-5 images for A/B testing
     */
    async uploadAndAnalyze(files: File[]): Promise<BatchAnalysisResponse> {
        const token = getAuthToken();
        if (!token) {
            throw new Error('Authentication required');
        }

        if (files.length < 2 || files.length > 5) {
            throw new Error('Please upload 2-5 images');
        }

        const formData = new FormData();
        files.forEach(file => {
            formData.append('files', file);
        });

        const response = await fetch(`${API_URL}/api/ab-optimizer/upload-and-analyze`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
            },
            body: formData,
        });

        if (!response.ok) {
            let errorMessage = 'Failed to analyze images';
            try {
                const error = await response.json();
                errorMessage = error.detail || error.message || errorMessage;
            } catch (e) {
                // If response is not JSON, use status text
                errorMessage = response.statusText || errorMessage;
            }
            throw new Error(errorMessage);
        }

        return response.json();
    },

    /**
     * Get centralized scoring configuration
     */
    async getConfig(): Promise<ScoringConfig> {
        const response = await fetch(`${API_URL}/api/ab-optimizer/config`);
        if (!response.ok) throw new Error('Failed to fetch scoring config');
        return response.json();
    },

    /**
     * Analyze images from the user's asset library (TODO: implement)
     */
    async analyzeFromLibrary(imageIds: string[]): Promise<BatchAnalysisResponse> {
        const token = getAuthToken();
        if (!token) {
            throw new Error('Authentication required');
        }

        const response = await fetch(`${API_URL}/api/ab-optimizer/analyze-from-library`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ image_ids: imageIds }),
        });

        if (!response.ok) {
            let errorMessage = 'Failed to analyze images from library';
            try {
                const error = await response.json();
                errorMessage = error.detail || error.message || errorMessage;
            } catch (e) {
                errorMessage = response.statusText || errorMessage;
            }
            throw new Error(errorMessage);
        }

        return response.json();
    },

    /**
     * Get results of a previously analyzed batch
     */
    async getBatchResults(batchId: string): Promise<BatchAnalysisResponse> {
        const token = getAuthToken();
        if (!token) {
            throw new Error('Authentication required');
        }

        const response = await fetch(`${API_URL}/api/ab-optimizer/batch/${batchId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Batch not found');
        }

        return response.json();
    },

    /**
     * Get all batches for the current user
     */
    async getUserBatches(limit: number = 20): Promise<BatchSummary[]> {
        const token = getAuthToken();
        if (!token) {
            throw new Error('Authentication required');
        }

        const response = await fetch(`${API_URL}/api/ab-optimizer/batches?limit=${limit}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        });

        if (!response.ok) {
            throw new Error('Failed to fetch batches');
        }

        return response.json();
    },

    /**
     * Estimate cost for analyzing images
     */
    async estimateCost(numImages: number): Promise<CostEstimate> {
        const token = getAuthToken();
        if (!token) {
            throw new Error('Authentication required');
        }

        const response = await fetch(`${API_URL}/api/ab-optimizer/cost-estimate?num_images=${numImages}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        });

        if (!response.ok) {
            throw new Error('Failed to estimate cost');
        }

        return response.json();
    },

    /**
     * Health check for A/B Optimizer service
     */
    async healthCheck(): Promise<HealthCheckResponse> {
        try {
            const response = await fetch(`${API_URL}/api/ab-optimizer/health`, {
                method: 'GET',
            });

            return response.json();
        } catch (error) {
            return {
                status: 'error',
                error: error instanceof Error ? error.message : 'Service unavailable'
            };
        }
    },
    
    // =====================================================
    // STAGE 2: Schedule Recommendation
    // =====================================================
    
    /**
     * Get optimal posting schedule for platform and niche
     */
    async getScheduleRecommendation(
        batchId: string,
        platform: string = 'instagram',
        niche: string = 'restaurant'
    ): Promise<ScheduleRecommendation> {
        const token = getAuthToken();
        if (!token) throw new Error('Authentication required');
        
        const response = await fetch(`${API_URL}/api/ab-optimizer/schedule-recommendation`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                batch_id: batchId,
                platform,
                niche,
            }),
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to get schedule recommendation');
        }
        
        return response.json();
    },
    
    // =====================================================
    // STAGE 3: Confirm Schedule
    // =====================================================
    
    /**
     * Confirm and schedule A/B test
     */
    async confirmSchedule(
        batchId: string,
        variantAImageId: string,
        variantBImageId: string,
        platform: string,
        postTimeA: Date,
        postTimeB: Date,
        captionA?: string,
        captionB?: string,
        testDurationHours: number = 48
    ): Promise<ScheduleConfirmation> {
        const token = getAuthToken();
        if (!token) throw new Error('Authentication required');
        
        const response = await fetch(`${API_URL}/api/ab-optimizer/confirm-schedule`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                batch_id: batchId,
                variant_a_image_id: variantAImageId,
                variant_b_image_id: variantBImageId,
                platform,
                post_time: postTimeA.toISOString(),  // Keep for backward compatibility
                variant_a_post_time: postTimeA.toISOString(),
                variant_b_post_time: postTimeB.toISOString(),
                caption: captionA,  // Keep for backward compatibility
                caption_a: captionA,
                caption_b: captionB,
                test_duration_hours: testDurationHours,
            }),
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to confirm schedule');
        }
        
        return response.json();
    },
    
    // =====================================================
    // STAGE 4: Get Schedule Status
    // =====================================================
    
    /**
     * Get schedule status
     */
    async getScheduleStatus(scheduleId: string): Promise<ScheduleStatus> {
        const token = getAuthToken();
        if (!token) throw new Error('Authentication required');
        
        const response = await fetch(`${API_URL}/api/ab-optimizer/schedule/${scheduleId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to get schedule status');
        }
        
        return response.json();
    },
    
    // =====================================================
    // STAGE 5: Calculate Winner
    // =====================================================
    
    /**
     * Calculate A/B test winner from engagement metrics
     */
    async calculateWinner(
        scheduleId: string,
        variantAMetrics: {
            likes: number;
            comments: number;
            shares: number;
            saves: number;
            reach: number;
            ctr: number;
        },
        variantBMetrics: {
            likes: number;
            comments: number;
            shares: number;
            saves: number;
            reach: number;
            ctr: number;
        }
    ): Promise<WinnerResult> {
        const token = getAuthToken();
        if (!token) throw new Error('Authentication required');
        
        const response = await fetch(`${API_URL}/api/ab-optimizer/calculate-winner`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                schedule_id: scheduleId,
                variant_a_metrics: variantAMetrics,
                variant_b_metrics: variantBMetrics,
            }),
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to calculate winner');
        }
        
        return response.json();
    },
    
    // =====================================================
    // STAGE 6: Generate Ad Brief
    // =====================================================
    
    /**
     * Generate paid ad campaign brief from winner
     */
    async generateAdBrief(
        resultId: string,
        platform: string = 'instagram',
        customBudgetDaily?: number,
        customDurationDays?: number
    ): Promise<AdBrief> {
        const token = getAuthToken();
        if (!token) throw new Error('Authentication required');
        
        const response = await fetch(`${API_URL}/api/ab-optimizer/generate-ad-brief`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                result_id: resultId,
                platform,
                custom_budget_daily: customBudgetDaily,
                custom_duration_days: customDurationDays,
            }),
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate ad brief');
        }
        
        return response.json();
    },
};
