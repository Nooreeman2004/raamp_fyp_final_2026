import { apiClient } from "@/services/api";

export type Sentiment = "POSITIVE" | "NEUTRAL" | "NEGATIVE";

export interface AnalyzedComment {
  id: string;
  comment_id: string;
  post_id: string;
  text: string;
  is_spam: boolean;
  spam_confidence: number;
  sentiment: Sentiment;
  sentiment_score: number;
  analyzed_at: string | null;
}

export interface CommentModerationResponse {
  total: number;
  spam_count: number;
  sentiment_summary: {
    POSITIVE: number;
    NEUTRAL: number;
    NEGATIVE: number;
  };
  comments: AnalyzedComment[];
}

export interface SingleCommentAnalysisResponse {
  is_spam: boolean;
  spam_confidence: number;
  sentiment: Sentiment;
  sentiment_score: number;
}

// Backend response wrapper
interface BackendResponse<T> {
  success: boolean;
  data: T;
}

class CommentModerationService {
  /**
   * Fetch all analyzed comments with optional filtering for the moderation dashboard
   */
  async getModerationComments(
    sentiment?: Sentiment,
    limit: number = 100
  ): Promise<CommentModerationResponse> {
    const params = new URLSearchParams();
    if (sentiment) params.set("sentiment", sentiment);
    params.set("limit", limit.toString());

    const response = await apiClient.get<BackendResponse<CommentModerationResponse>>(
      `/comments/moderation?${params.toString()}`
    );
    return response.data;
  }

  /**
   * Analyze a single comment in real-time
   */
  async analyzeComment(text: string): Promise<SingleCommentAnalysisResponse> {
    const response = await apiClient.post<BackendResponse<SingleCommentAnalysisResponse>>(
      "/comments/analyse",
      { text }
    );
    return response.data;
  }

  /**
   * Get comment analysis summary for a specific post
   */
  async getPostCommentSummary(postId: string): Promise<CommentModerationResponse> {
    const response = await apiClient.get<BackendResponse<CommentModerationResponse>>(
      `/api/comments/summary/${postId}`
    );
    return response.data;
  }
}

export const commentModerationService = new CommentModerationService();
