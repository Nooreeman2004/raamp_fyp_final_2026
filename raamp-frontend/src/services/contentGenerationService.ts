/**
 * Content Generation Service
 * Handles AI-powered content generation for social media campaigns
 */

const API_URL = import.meta.env.VITE_API_BASE_URL || '/api';

// Helper to get auth token from storage
const getAuthToken = (): string | null => {
    return localStorage.getItem('token');
};

// TypeScript interfaces matching backend schemas
export interface MLScore {
    engagement_rate: number;
    score_label: string;
    confidence: string;
    feature_importances: Record<string, number>;
    model_available: boolean;
}

export interface ContentVariant {
    id: number;
    caption_id?: string;  // Caption ID for usage tracking
    tone: string;
    caption: string;
    hashtags: string[];
    predicted_performance?: string;
    ml_score?: MLScore;
    hashtag_source?: string;
}

export interface MessageVariant {
    id: number;
    message_id?: string;  // Message ID for usage tracking
    tone: string;
    message: string;
    predicted_performance?: string;
    ml_score?: MLScore;
}

export interface BrandContext {
    business_name?: string;
    tagline?: string;
    tone_of_voice?: string;
    restaurant_theme?: string;
    business_type?: string;
    primary_color?: string;
    secondary_color?: string;
}

export interface ContentGenerationRequest {
    campaign_idea: string;
    target_audience?: string;
    campaign_tone?: string;
    aspect_ratio?: '1:1' | '9:16' | '4:5';
    /** Content type: what to generate.
     * 'captions'  → social media captions + per-caption hashtags
     * 'hashtags'  → standalone hashtag sets
     * 'whatsapp'  → WhatsApp broadcast messages + images
     * 'emails'    → email campaign messages
     * 'all'       → everything (default)
     */
    content_type?: 'captions' | 'hashtags' | 'whatsapp' | 'emails' | 'images' | 'all';
    campaign_id?: string;
}

export interface HashtagSet {
    id: number;
    hashtag_id: string;
    hashtags: string[];
}

export interface ContentGenerationResponse {
    success: boolean;
    brand_context: BrandContext;
    caption_variants: ContentVariant[];
    best_caption_id: number;
    hashtag_sets: HashtagSet[];
    best_hashtag_set_id: number;
    whatsapp_variants: MessageVariant[];
    email_variants: MessageVariant[];
    message_variants: MessageVariant[];
    best_message_id: number;
    image_prompts: string[];
    image_paths: string[];
    asset_ids: string[];
    image_generation_prompt?: string;
    reasoning?: string;
    generated_at: string;
    aspect_ratio?: string;   // Aspect ratio used (1:1, 9:16, 4:5)
    content_type?: string;   // Content type used (image, caption, video)
    platform_type?: string;  // Derived platform type (kept for backward compat)
}

export interface VariantRecommendationRequest {
    variant_type: 'captions' | 'hashtags' | 'whatsapp' | 'emails';
    variants: Array<{
        id: number;
        tone: string;
        caption?: string;
        hashtags?: string;
        variant_copy?: string;
    }>;
}

export interface VariantRecommendationResponse {
    recommended_variant_id: number;
    score: number;
    reason: string;
}

export const contentGenerationService = {
    /**
     * Generate AI-powered content for a campaign
     */
    async generateContent(request: ContentGenerationRequest): Promise<ContentGenerationResponse> {
        try {
            const token = getAuthToken();
            if (!token) {
                throw new Error('Authentication required. Please log in again.');
            }

            console.log('🔐 Token present:', token ? 'Yes' : 'No');
            console.log('📤 Sending request to:', `${API_URL}/content/generate`);

            const response = await fetch(`${API_URL}/content/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify(request),
            });

            console.log('📥 Response status:', response.status, response.statusText);

            if (!response.ok) {
                let errorMessage = 'Failed to generate content';
                try {
                    const error = await response.json();
                    // Handle different error response formats
                    if (typeof error.detail === 'string') {
                        errorMessage = error.detail;
                    } else if (error.detail?.error) {
                        errorMessage = error.detail.error;
                    } else if (error.error) {
                        errorMessage = error.error;
                    } else if (error.message) {
                        errorMessage = error.message;
                    }
                } catch {
                    errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                }
                throw new Error(errorMessage);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Content generation error:', error);
            const message = error instanceof Error ? error.message : String(error);
            throw new Error(message);
        }
    },

    /**
     * Get brand context for the current user
     */
    async getBrandContext(): Promise<BrandContext> {
        try {
            const token = getAuthToken();
            if (!token) {
                throw new Error('Authentication required');
            }

            const response = await fetch(`${API_URL}/content/brand-context`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                throw new Error('Failed to fetch brand context');
            }

            const data = await response.json();
            return data;
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Failed to fetch brand context';
            throw new Error(message);
        }
    },

    /**
     * Get AI recommendation for which variant is best
     */
    async getVariantRecommendation(request: VariantRecommendationRequest): Promise<VariantRecommendationResponse> {
        try {
            const response = await fetch(`${API_URL}/variants/recommend`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request),
            });

            if (!response.ok) {
                throw new Error('Failed to get variant recommendation');
            }

            const data = await response.json();
            return data;
        } catch (error) {
            // Silently fail for recommendations - not critical
            const message = error instanceof Error ? error.message : 'Unable to fetch recommendation';
            console.warn('Variant recommendation failed:', message);
            return {
                recommended_variant_id: 1,
                score: 0,
                reason: 'Unable to fetch recommendation',
            };
        }
    },
};
