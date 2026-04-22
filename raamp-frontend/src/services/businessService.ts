import { apiClient } from './api';

// Types aligning with Backend Schemas

export interface HyperlocalBusinessSetupRequest {
    business_name: string;
    business_type: string;
    latitude?: number;
    longitude?: number;
    place_id?: string;
    formatted_address?: string;
    website?: string;
    phone?: string;
    description?: string;
    city?: string;
    country?: string;
}

export interface HyperlocalBusinessSetupResponse {
    success: boolean;
    message: string;
    business_name: string;
    business_type: string;
    latitude: number;
    longitude: number;
    place_id?: string;
    formatted_address?: string;
    website?: string;
    phone?: string;
    description?: string;
    city?: string;
    country?: string;
}

export interface BrandAlignmentRequest {
    brand_logo_url?: string | null;
    primary_color?: string | null;
    secondary_color?: string | null;
    tagline?: string | null;
    tone_of_voice?: string | null;
    tone_profile?: {
        personality: string;
        audience: string;
        language_rules: string;
        platforms?: string[];
        content_types?: string[];
    } | null;
    restaurant_theme?: string | null;
    brand_colors?: string[];
    palette_source?: string;
}

export interface BrandAlignmentResponse {
    brand_logo_url?: string | null;
    primary_color?: string | null;
    secondary_color?: string | null;
    tagline?: string | null;
    tone_of_voice?: string | null;
    tone_profile?: {
        personality: string;
        audience: string;
        language_rules: string;
        platforms?: string[];
        content_types?: string[];
    } | null;
    restaurant_theme?: string | null;
    brand_colors?: string[];
    palette_source?: string;
    updated_at?: string;
}

export const businessService = {
    /**
     * Save hyperlocal business setup
     */
    saveHyperlocalSetup: async (data: HyperlocalBusinessSetupRequest): Promise<HyperlocalBusinessSetupResponse> => {
        return apiClient.post<HyperlocalBusinessSetupResponse>('/hyperlocal-setup/save', data);
    },

    /**
     * Get current hyperlocal setup
     */
    getHyperlocalSetup: async (): Promise<any> => {
        return apiClient.get('/hyperlocal-setup/current');
    },

    /**
     * Upload brand logo
     */
    uploadLogo: async (file: File): Promise<{ success: boolean; logo_url: string }> => {
        const formData = new FormData();
        formData.append('logo', file);
        return apiClient.upload<{ success: boolean; logo_url: string }>('/brand-alignment/upload-logo', formData);
    },

    /**
     * Save brand alignment settings
     */
    saveBrandAlignment: async (data: BrandAlignmentRequest): Promise<BrandAlignmentResponse> => {
        return apiClient.post<BrandAlignmentResponse>('/brand-alignment/save', data);
    },

    /**
     * Get brand alignment settings
     */
    getBrandAlignment: async (): Promise<BrandAlignmentResponse> => {
        return apiClient.get<BrandAlignmentResponse>('/brand-alignment/settings');
    }
};
