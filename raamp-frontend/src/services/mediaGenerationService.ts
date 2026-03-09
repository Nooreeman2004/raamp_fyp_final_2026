/**
 * Media Generation Service
 * =========================
 * Service for generating Reels and Videos using the backend API.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

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
  private getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem('token');
    return {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    };
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const error = await response.json().catch(() => ({
        error: 'Network error',
        detail: response.statusText,
      }));
      throw new Error(error.detail || error.error || 'Request failed');
    }
    return response.json();
  }

  // ==================== Reel Generation ====================

  /**
   * Generate a Reel script/prompt using Gemini AI
   */
  async generateReelPrompt(request: MediaPromptRequest): Promise<MediaPromptResponse> {
    const response = await fetch(`${API_BASE_URL}/media/reels/generate-prompt`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(request),
    });

    return this.handleResponse<MediaPromptResponse>(response);
  }

  /**
   * Generate Reel videos from a prompt
   */
  async generateReels(request: MediaGenerationRequest): Promise<MediaGenerationResponse> {
    const response = await fetch(`${API_BASE_URL}/media/reels/generate`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(request),
    });

    return this.handleResponse<MediaGenerationResponse>(response);
  }

  /**
   * Quick Reel generation - combines prompt + video in one step
   */
  async generateQuickReel(request: QuickReelRequest): Promise<MediaGenerationResponse> {
    const response = await fetch(`${API_BASE_URL}/media/generate-quick-reel`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(request),
    });

    return this.handleResponse<MediaGenerationResponse>(response);
  }

  // ==================== Video Generation ====================

  /**
   * Generate a video script/prompt using Gemini AI
   */
  async generateVideoPrompt(request: MediaPromptRequest): Promise<MediaPromptResponse> {
    const response = await fetch(`${API_BASE_URL}/media/videos/generate-prompt`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(request),
    });

    return this.handleResponse<MediaPromptResponse>(response);
  }

  /**
   * Generate videos from a prompt
   */
  async generateVideos(request: MediaGenerationRequest): Promise<MediaGenerationResponse> {
    const response = await fetch(`${API_BASE_URL}/media/videos/generate`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(request),
    });

    return this.handleResponse<MediaGenerationResponse>(response);
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
    const url = this.getMediaUrl(path);
    const response = await fetch(url, {
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Failed to download media');
    }

    const blob = await response.blob();
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
