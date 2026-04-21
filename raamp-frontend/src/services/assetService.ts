/**
 * Asset Service
 * Handles API calls for AI-generated and uploaded media assets
 */

// Remove trailing /api if present to avoid /api/api/assets
const API_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/api\/?$/, '');

// Helper to get auth token from storage
const getAuthToken = (): string | null => {
    return localStorage.getItem('token') || sessionStorage.getItem('token');
};

// TypeScript interfaces

export interface Asset {
    asset_id: string;
    storage_url: string;
    cloudinary_url?: string;
    firebase_url?: string;
    file_name: string;
    file_size_bytes: number;
    content_type: string;
    width?: number;
    height?: number;
    asset_type: 'generated_image' | 'uploaded_image' | 'uploaded_video' | 'generated_video' | 'generated_reel';
    generation_source: 'AI' | 'user_upload';
    generation_prompt?: string;
    campaign_idea?: string;
    variation_number?: number;
    model_used?: string;
    times_used: number;
    last_used_at?: string;
    instagram_post_id?: string;
    tags: string[];
    is_favorite: boolean;
    created_at: string;
    updated_at: string;
}

export interface AssetLibraryResponse {
    assets: Asset[];
    total: number;
    page: number;
    per_page: number;
}

export interface AssetFilters {
    page?: number;
    per_page?: number;
    asset_type?: string;
    source?: string;
}

export interface CaptionAsset {
    caption_id: string;
    caption_text: string;
    hashtags: string[];
    tone: string;
    asset_type: 'POST' | 'STORY' | 'REEL' | 'CAROUSEL' | 'AD_COPY' | 'WHATSAPP' | 'EMAIL';
    platform?: string;  // Deprecated, use asset_type instead
    created_at: string;
    campaign_id?: string;
    campaign_idea?: string;
    times_used: number;
    is_favorite: boolean;
    predicted_performance?: string;
}

export interface CaptionAssetsResponse {
    success: boolean;
    captions: CaptionAsset[];
    total: number;
}

export const assetService = {
    /**
     * Fetch assets for the current user with pagination and filtering
     */
    async getAssetLibrary(filters: AssetFilters = {}): Promise<AssetLibraryResponse> {
        try {
            const token = getAuthToken();
            if (!token) {
                throw new Error('Authentication required');
            }

            const params = new URLSearchParams();
            if (filters.page) params.append('page', filters.page.toString());
            if (filters.per_page) params.append('per_page', filters.per_page.toString());
            if (filters.asset_type) params.append('asset_type', filters.asset_type);
            if (filters.source) params.append('source', filters.source);

            const response = await fetch(`${API_URL}/api/assets/library?${params}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to fetch assets');
            }

            return await response.json();
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Failed to fetch assets';
            throw new Error(message);
        }
    },

    /**
     * Get details of a specific asset
     */
    async getAssetDetails(assetId: string): Promise<Asset> {
        try {
            const token = getAuthToken();
            if (!token) {
                throw new Error('Authentication required');
            }

            const response = await fetch(`${API_URL}/api/assets/${assetId}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to fetch asset details');
            }

            return await response.json();
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Failed to fetch asset details';
            throw new Error(message);
        }
    },

    /**
     * Download an asset file using fetch with auth header, then trigger browser download via blob
     */
    async downloadAsset(assetId: string, filename: string): Promise<void> {
        const token = getAuthToken();
        if (!token) {
            throw new Error('Authentication required');
        }

        const response = await fetch(`${API_URL}/api/assets/${assetId}/download`, {
            method: 'GET',
            headers: { 'Authorization': `Bearer ${token}` },
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error((error as { detail?: string }).detail || 'Download failed');
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    },

    /**
     * Mark an asset as used (increments usage counter)
     */
    async markAssetUsed(assetId: string): Promise<void> {
        try {
            const token = getAuthToken();
            if (!token) {
                throw new Error('Authentication required');
            }

            const response = await fetch(`${API_URL}/api/assets/${assetId}/use`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to mark asset as used');
            }
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Failed to mark asset as used';
            throw new Error(message);
        }
    },

    /**
     * Delete an asset
     */
    async deleteAsset(assetId: string): Promise<void> {
        try {
            const token = getAuthToken();
            if (!token) {
                throw new Error('Authentication required');
            }

            const response = await fetch(`${API_URL}/api/assets/${assetId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to delete asset');
            }
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Failed to delete asset';
            throw new Error(message);
        }
    },

    /**
     * Get AI-generated images only
     */
    async getGeneratedImages(page: number = 1, per_page: number = 50): Promise<AssetLibraryResponse> {
        return this.getAssetLibrary({
            page,
            per_page,
            asset_type: 'generated_image',
            source: 'AI'
        });
    },

    /**
     * Get uploaded images only
     */
    async getUploadedImages(page: number = 1, per_page: number = 50): Promise<AssetLibraryResponse> {
        return this.getAssetLibrary({
            page,
            per_page,
            asset_type: 'uploaded_image',
            source: 'user_upload'
        });
    },

    /**
     * Get saved captions from content generation history
     */
    async getCaptions(filters?: { asset_type?: string; campaign_id?: string }): Promise<CaptionAssetsResponse> {
        try {
            const token = getAuthToken();
            if (!token) {
                throw new Error('Authentication required');
            }

            const params = new URLSearchParams();
            if (filters?.asset_type) params.append('asset_type', filters.asset_type);
            if (filters?.campaign_id) params.append('campaign_id', filters.campaign_id);

            const response = await fetch(`${API_URL}/api/assets/captions?${params}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to fetch captions');
            }

            return await response.json();
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Failed to fetch captions';
            throw new Error(message);
        }
    },

    /**
     * Mark a caption as used (increments usage counter)
     */
    async markCaptionUsed(captionId: string): Promise<void> {
        try {
            const token = getAuthToken();
            if (!token) {
                throw new Error('Authentication required');
            }

            const response = await fetch(`${API_URL}/api/assets/captions/${captionId}/use`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to mark caption as used');
            }
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Failed to mark caption as used';
            throw new Error(message);
        }
    },

    /**
     * Toggle favorite status for an asset
     */
    async toggleAssetFavorite(assetId: string): Promise<{ is_favorite: boolean }> {
        try {
            const token = getAuthToken();
            if (!token) throw new Error('Authentication required');

            const response = await fetch(`${API_URL}/api/assets/${assetId}/favorite`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to toggle favorite');
            }

            return await response.json();
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Failed to toggle favorite';
            throw new Error(message);
        }
    },

    /**
     * Toggle favorite status for a caption
     */
    async toggleCaptionFavorite(captionId: string): Promise<{ is_favorite: boolean }> {
        try {
            const token = getAuthToken();
            if (!token) {
                throw new Error('Authentication required');
            }

            const response = await fetch(`${API_URL}/api/assets/captions/${captionId}/favorite`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to toggle favorite status');
            }

            return await response.json();
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Failed to toggle favorite status';
            throw new Error(message);
        }
    },

    /**
     * Scan generated_reels/ and generated_videos/ on disk and create
     * missing asset records in MongoDB for the current user.
     */
    async rescanFiles(): Promise<{ imported: number; skipped: number; errors: number; message: string }> {
        try {
            const token = getAuthToken();
            if (!token) {
                throw new Error('Authentication required');
            }

            const response = await fetch(`${API_URL}/api/assets/rescan`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Rescan failed');
            }

            return await response.json();
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Rescan failed';
            throw new Error(message);
        }
    },
};
