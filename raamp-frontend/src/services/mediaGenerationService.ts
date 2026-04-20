/**
 * Media Generation Service
 * =========================
 * Service for generating Reels and Videos using the backend API.
 * Uses apiClient for shared timeout, retry, and auth behavior.
 */

import { apiClient } from '@/services/api';
import { API_BASE_URL } from '@/config/apiBase';

// ==================== Types ====================

export interface MediaPromptRequest {
  idea: string;
  brand_context?: {
    business_name?: string;
    business_type?: string;
    tone_of_voice?: string;
    primary_color?: string;
  };
  aspect_ratio?: '16:9' | '1:1';
}

export interface MediaPromptResponse {
  success: boolean;
  reel_prompt?: string;
  video_prompt?: string;
  aspect_ratio?: string;
  timestamp: string;
}

export interface MediaGenerationRequest {
  reel_prompt?: string;
  video_prompt?: string;
  campaign_id?: string;
  count?: number;
  duration_seconds?: number;
  aspect_ratio?: '16:9' | '1:1';
}

export interface MediaGenerationResponse {
  success: boolean;
  message: string;
  media_paths: string[];
  asset_ids?: string[];  // Asset IDs for usage tracking
  campaign_id: string;
  duration_seconds: number;
  count: number;
  timestamp: string;
  aspect_ratio?: string;
}

export interface QuickReelRequest {
  idea: string;
  duration_seconds?: number;
}

export type MediaGenerationError = {
  success: false;
  error: string;
  detail?: string;
};

// ==================== Service Class ====================

class MediaGenerationService {
  /**
   * Map a resolved media URL (under API prefix) to an apiClient path (no duplicate /api).
   */
  private urlToEndpoint(fullPath: string): string {
    const base = API_BASE_URL;
    if (fullPath.startsWith(base)) {
      const rest = fullPath.slice(base.length);
      return rest.startsWith('/') ? rest : `/${rest}`;
    }
    if (fullPath.startsWith('/api')) {
      return fullPath.slice('/api'.length) || '/';
    }
    return fullPath.startsWith('/') ? fullPath : `/${fullPath}`;
  }

  // ==================== Reel Generation ====================

  /**
   * Generate a Reel script/prompt using Gemini AI
   */
  async generateReelPrompt(request: MediaPromptRequest): Promise<MediaPromptResponse> {
    return apiClient.post<MediaPromptResponse>('/media/reels/generate-prompt', request);
  }

  /**
   * Generate Reel videos from a prompt
   */
  async generateReels(request: MediaGenerationRequest): Promise<MediaGenerationResponse> {
    return apiClient.post<MediaGenerationResponse>('/media/reels/generate', request);
  }

  /**
   * Quick Reel generation - combines prompt + video in one step
   */
  async generateQuickReel(request: QuickReelRequest): Promise<MediaGenerationResponse> {
    return apiClient.post<MediaGenerationResponse>('/media/generate-quick-reel', request);
  }

  // ==================== Video Generation ====================

  /**
   * Generate a video script/prompt using Gemini AI
   */
  async generateVideoPrompt(request: MediaPromptRequest): Promise<MediaPromptResponse> {
    return apiClient.post<MediaPromptResponse>('/media/videos/generate-prompt', request);
  }

  /**
   * Generate videos from a prompt
   */
  async generateVideos(request: MediaGenerationRequest): Promise<MediaGenerationResponse> {
    return apiClient.post<MediaGenerationResponse>('/media/videos/generate', request);
  }

  // ==================== Helper Methods ====================

  /**
   * Get the full URL for a media file
   */
  getMediaUrl(path: string): string {
    if (!path) return '';
    if (path.startsWith('http')) return path;

    // If path already starts with /api, just return it (browser will resolve relative to origin)
    if (path.startsWith('/api')) return path;

    // Normalise path (handle Windows backslashes) and prepend base URL
    const normalizedPath = path.replace(/\\/g, '/');
    const cleanPath = normalizedPath.startsWith('/') ? normalizedPath.substring(1) : normalizedPath;

    // Handle special folders if needed (backend serving rules)
    if (cleanPath.startsWith('generated_reels/')) {
      return `${API_BASE_URL}/reels/${cleanPath.replace('generated_reels/', '')}`;
    }
    if (cleanPath.startsWith('generated_videos/')) {
      return `${API_BASE_URL}/videos/${cleanPath.replace('generated_videos/', '')}`;
    }

    return `${API_BASE_URL}/${cleanPath}`;
  }

  /**
   * Download a media file
   */
  async downloadMedia(path: string, filename: string): Promise<void> {
    const mediaUrl = this.getMediaUrl(path);
    let blob: Blob;
    if (mediaUrl.startsWith('http')) {
      const token = localStorage.getItem('token');
      const response = await fetch(mediaUrl, {
        credentials: 'include',
        ...(token ? { headers: { Authorization: `Bearer ${token}` } } : {}),
      });
      if (!response.ok) {
        throw new Error('Failed to download media');
      }
      blob = await response.blob();
    } else {
      const endpoint = this.urlToEndpoint(mediaUrl);
      blob = await apiClient.getBlob(endpoint);
    }

    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  }
}

// Export singleton instance
export const mediaGenerationService = new MediaGenerationService();
