/**
 * TypeScript types for Instagram posting functionality
 * Matches backend schemas from instagram_posting_schemas.py
 */

export enum PostMode {
    POST_NOW = "post_now",
    SCHEDULE_POST = "schedule_post",
    POST_STORY = "post_story",
}

export interface InstagramPostRequest {
    mode: PostMode;
    media_url: string;
    caption?: string;
    scheduled_time?: string; // ISO 8601 datetime
}

export interface InstagramPostResponse {
    status: string;
    post_id?: string;
    instagram_post_id?: string;
    scheduled_time?: string;
    error?: string;
}

export interface ScheduledPostItem {
    post_id: string;
    media_url: string;
    caption?: string;
    scheduled_time: string;
    status: string;
    created_at: string;
}

export interface ScheduledPostListResponse {
    posts: ScheduledPostItem[];
    total: number;
}

export interface PostHistoryItem {
    post_id: string;
    internal_id?: string;
    platform: string;
    media_url: string;
    caption?: string;
    status: string;
    instagram_post_id?: string;
    facebook_post_id?: string; // For Facebook posts
    created_at: string;
    published_at?: string;
    error_message?: string;
}

export interface PostHistoryResponse {
    posts: PostHistoryItem[];
    total: number;
}

export interface CancelScheduledPostRequest {
    post_id: string;
}

export interface CancelScheduledPostResponse {
    success: boolean;
    message: string;
}

export interface ConnectionStatus {
    connected: boolean;
    can_post: boolean;
    ig_business_id?: string;
    page_name?: string;
    token_valid?: boolean;
    expires_soon?: boolean;
    expires_at?: string;
    message?: string;
}

export interface SocialConnectionStatus {
    instagram_connected: boolean;
    facebook_connected: boolean;
    instagram_details?: {
        ig_business_id: string;
        username?: string;
        connected_at?: string;
        token_valid?: boolean;
        error?: string;
    } | null;
    facebook_details?: {
        page_id: string;
        page_name?: string;
        connected_at?: string;
        token_valid?: boolean;
        error?: string;
    } | null;
}

export interface MediaAsset {
    id: string;
    url: string;
    type: 'image' | 'video';
    title: string;
    created_at: string;
    width?: number;
    height?: number;
    size_bytes?: number;
}

export interface CaptionAsset {
    id: string;
    text: string;
    platform: string;
    created_at: string;
    campaign_name?: string;
    tone?: string;
}
