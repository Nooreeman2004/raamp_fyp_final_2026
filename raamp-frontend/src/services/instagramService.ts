/**
 * Instagram Posting Service
 * Handles all API calls related to Instagram posting, scheduling, and history
 */

import { apiClient } from './api';
import type {
    InstagramPostRequest,
    InstagramPostResponse,
    ScheduledPostListResponse,
    CancelScheduledPostRequest,
    CancelScheduledPostResponse,
    PostHistoryResponse,
    ConnectionStatus,
    SocialConnectionStatus,
    MediaAsset,
    CaptionAsset,
} from '@/types/instagram.types';
import { PostMode } from '@/types/instagram.types';

export interface UnifiedPostResponse {
    success: boolean;
    results: Array<{
        platform: string;
        status: string;
        post_id?: string;
        external_id?: string;
        error?: string;
    }>;
    message: string;
}

export interface ROIMetrics {
  reach: number;
  impressions: number;
  engagement: number;
  likes: number;
  comments: number;
  shares: number;
  saved: number;
  engagement_rate: number;
  last_fetched_at: string | null;
  fetch_status: 'pending' | 'success' | 'failed';
}

export interface ROISummary {
  total_posts: number;
  total_reach: number;
  prev_week_reach: number;
  total_impressions: number;
  avg_engagement_rate: number;
  best_performing_post: { post_id: string; reach: number; engagement_rate: number } | null;
  worst_performing_post: { post_id: string; reach: number; engagement_rate: number } | null;
  posts_pending: number;
  posts_failed: number;
}

class InstagramService {
    /**
     * Create an Instagram post (immediate, scheduled, or story)
     */
    async createPost(request: InstagramPostRequest): Promise<InstagramPostResponse> {
        return apiClient.post<InstagramPostResponse>('/instagram/posting/post', request);
    }

    /**
     * Alias for createPost to support legacy deployment naming
     * Accepts imageUrl, caption, and optional mode/time
     */
    async publishPost(params: {
        imageUrl: string;
        caption?: string;
        mode?: PostMode;
        scheduledTime?: string;
    }): Promise<InstagramPostResponse> {
        return this.createPost({
            media_url: params.imageUrl,
            caption: params.caption,
            mode: params.mode || PostMode.POST_NOW,
            scheduled_time: params.scheduledTime
        });
    }

    /**
     * Unified social post (multi-platform)
     */
    async unifiedPost(request: {
        platform: 'instagram' | 'facebook' | 'both';
        mode: PostMode;
        media_url: string;
        caption?: string;
        scheduled_time?: string;
        facebook_page_id?: string;
    }): Promise<UnifiedPostResponse> {
        return apiClient.post<UnifiedPostResponse>('/social/post', request);
    }

    /**
     * Get all scheduled posts for the current user
     */
    async getScheduledPosts(): Promise<ScheduledPostListResponse> {
        return apiClient.get<ScheduledPostListResponse>('/instagram/posting/scheduled');
    }

    /**
     * Cancel a scheduled post
     */
    async cancelScheduledPost(postId: string): Promise<CancelScheduledPostResponse> {
        return apiClient.post<CancelScheduledPostResponse>(
            '/instagram/posting/scheduled/cancel',
            { post_id: postId } as CancelScheduledPostRequest
        );
    }

    /**
     * Get posting history (feed posts)
     */
    async getPostHistory(limit: number = 50): Promise<PostHistoryResponse> {
        return apiClient.get<PostHistoryResponse>(`/instagram/posting/history?limit=${limit}`);
    }

    /**
     * Get story posting history
     */
    async getStoryHistory(limit: number = 50): Promise<PostHistoryResponse> {
        return apiClient.get<PostHistoryResponse>(`/instagram/posting/stories?limit=${limit}`);
    }

    /**
     * Get combined posting history (both feed posts and stories)
     */
    async getCombinedHistory(limit: number = 50): Promise<PostHistoryResponse> {
        try {
            // Run in parallel but handle individual failures
            const [postResult, storyResult] = await Promise.allSettled([
                this.getPostHistory(limit),
                this.getStoryHistory(limit),
            ]);

            const postHistory = postResult.status === 'fulfilled'
                ? postResult.value
                : { posts: [], total: 0 };

            const storyHistory = storyResult.status === 'fulfilled'
                ? storyResult.value
                : { posts: [], total: 0 };

            if (postResult.status === 'rejected') {
                console.error("Failed to fetch post history:", postResult.reason);
            }
            if (storyResult.status === 'rejected') {
                console.error("Failed to fetch story history:", storyResult.reason);
            }

            // Combine and sort by created_at (newest first)
            const allPosts = [...postHistory.posts, ...storyHistory.posts].sort((a, b) => {
                return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
            });

            return {
                posts: allPosts.slice(0, limit),
                total: postHistory.total + storyHistory.total,
            };
        } catch (error) {
            console.error("Error in getCombinedHistory:", error);
            return { posts: [], total: 0 };
        }
    }

    /**
     * Check Instagram connection status
     */
    async getConnectionStatus(): Promise<ConnectionStatus> {
        return apiClient.get<ConnectionStatus>('/instagram/posting/connection-status');
    }

    /**
     * Get social connection status (Instagram + Facebook)
     */
    async getSocialConnectionStatus(): Promise<SocialConnectionStatus> {
        return apiClient.get<SocialConnectionStatus>('/social/status');
    }

    /**
     * Get media assets from Creative Studio
     */
    async getMediaAssets(assetType?: 'image' | 'video'): Promise<{ assets: MediaAsset[]; total: number }> {
        const params = assetType ? `?asset_type=${assetType}` : '';
        return apiClient.get(`/assets/media${params}`);
    }

    /**
     * Get caption assets from AI Creative Studio
     */
    async getCaptionAssets(platform?: string): Promise<{ captions: CaptionAsset[]; total: number }> {
        const params = platform ? `?platform=${platform}` : '';
        return apiClient.get(`/assets/captions${params}`);
    }

    /**
     * Log posting activity
     */
    async logPostingActivity(data: {
        action: string;
        media_url: string;
        status: string;
        caption?: string;
        error_message?: string;
        instagram_post_id?: string;
    }): Promise<{ success: boolean; message: string }> {
        return apiClient.post('/instagram/posting/logs', data);
    }

    /**
     * Get posting activity logs
     */
    async getPostingLogs(statusFilter?: 'success' | 'failed' | 'pending'): Promise<{
        logs: Array<{
            id: string;
            action: string;
            media_url: string;
            status: string;
            created_at: string;
            error_message?: string;
        }>;
        total: number;
    }> {
        const params = statusFilter ? `?status_filter=${statusFilter}` : '';
        return apiClient.get(`/instagram/posting/logs${params}`);
    }

    /**
     * Upload media file to Firebase Storage and local storage
     */
    async uploadMedia(file: File): Promise<{
        asset_id: string;
        firebase_url?: string;
        cloudinary_url?: string;
        public_url: string;
        local_path: string;
        filename: string;
        content_type: string;
        size_bytes: number;
        is_auto_cropped?: boolean;
        original_dims?: { w: number; h: number; ratio: number };
        transformed_dims?: { w: number; h: number; ratio: number; target: string };
        cloudinary_original_url?: string;
    }> {
        const formData = new FormData();
        formData.append('file', file);

        // Use fetch directly for FormData upload with credentials to include cookies
        // Use configured base URL (with /api prefix for proxy)
        const baseUrl = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, "");
        const token = localStorage.getItem('token');
        const response = await fetch(`${baseUrl}/assets/upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
            throw new Error(error.detail || 'Upload failed');
        }

        return response.json();
    }

    /**
     * Get ROI metrics for a specific post
     */
    async getPostROI(postId: string): Promise<ROIMetrics> {
        return apiClient.get<ROIMetrics>(`/instagram/roi/${postId}`);
    }

    /**
     * Manually refresh ROI metrics for a specific post
     */
    async refreshPostROI(postId: string): Promise<ROIMetrics> {
        return apiClient.post<ROIMetrics>(`/instagram/roi/refresh/${postId}`, {});
    }

    /**
     * Get aggregate ROI summary for a business
     */
    async getROISummary(businessId: string): Promise<ROISummary> {
        return apiClient.get<ROISummary>(`/instagram/roi/summary/${businessId}`);
    }

    /**
     * Get ROI timeseries for a business
     */
    async getROITimeseries(businessId: string, days: number = 30): Promise<Array<{date: string, reach: number, impressions: number}>> {
        return apiClient.get<Array<{date: string, reach: number, impressions: number}>>(`/instagram/roi/timeseries/${businessId}?days=${days}`);
    }
}

export const instagramService = new InstagramService();

