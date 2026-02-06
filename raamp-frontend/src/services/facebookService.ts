/**
 * Facebook Posting Service
 * Handles all API calls related to Facebook posting, scheduling, and history
 */

import { apiClient } from './api';

export interface FacebookPostRequest {
    mode: 'POST_NOW' | 'SCHEDULE_POST';
    page_id: string;
    media_type: 'PHOTO' | 'VIDEO' | 'TEXT';
    media_url?: string;
    message?: string;
    scheduled_time?: string;
}

export interface FacebookPostResponse {
    status: string;
    post_id?: string;
    facebook_post_id?: string;
    scheduled_time?: string;
    error?: string;
}

export interface ScheduledFacebookPostItem {
    post_id: string;
    media_url?: string;
    message?: string;
    scheduled_time: string;
    status: string;
    created_at: string;
}

export interface ScheduledFacebookPostListResponse {
    posts: ScheduledFacebookPostItem[];
    total: number;
}

export interface FacebookPostHistoryItem {
    post_id: string;
    media_url?: string;
    message?: string;
    status: string;
    facebook_post_id?: string;
    created_at: string;
    published_at?: string;
    error_message?: string;
}

export interface FacebookPostHistoryResponse {
    posts: FacebookPostHistoryItem[];
    total: number;
}

class FacebookService {
    /**
     * Create a Facebook post (immediate or scheduled)
     */
    async createPost(request: FacebookPostRequest): Promise<FacebookPostResponse> {
        return apiClient.post<FacebookPostResponse>('/facebook/posting/post', request);
    }

    /**
     * Get all scheduled Facebook posts for the current user
     */
    async getScheduledPosts(): Promise<ScheduledFacebookPostListResponse> {
        return apiClient.get<ScheduledFacebookPostListResponse>('/facebook/posting/scheduled');
    }

    /**
     * Cancel a scheduled Facebook post
     */
    async cancelScheduledPost(postId: string): Promise<{ success: boolean; message: string }> {
        return apiClient.post('/facebook/posting/scheduled/cancel', { post_id: postId });
    }

    /**
     * Get Facebook posting history
     */
    async getPostHistory(limit: number = 50): Promise<FacebookPostHistoryResponse> {
        return apiClient.get<FacebookPostHistoryResponse>(`/facebook/posting/history?limit=${limit}`);
    }
}

export const facebookService = new FacebookService();
