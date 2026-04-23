/**
 * src/services/commentAnalysisService.ts
 * Bridge for Comment Spam + Sentiment Intelligence
 */

import { apiClient } from './api';

export interface CommentAnalysisResult {
  is_spam: boolean;
  spam_confidence: number;
  sentiment: 'POSITIVE' | 'NEUTRAL' | 'NEGATIVE';
  sentiment_score: number;
}

export interface PostCommentAnalysisSummary {
  post_id: string;
  total: number;
  spam_count: number;
  sentiment_summary: {
    POSITIVE: number;
    NEUTRAL: number;
    NEGATIVE: number;
  };
  comments: Array<{
    id: string;
    text: string;
    timestamp: string;
    is_spam: boolean;
    spam_confidence: number;
    sentiment: 'POSITIVE' | 'NEUTRAL' | 'NEGATIVE';
    sentiment_score: number;
  }>;
}

class CommentAnalysisService {
  /**
   * Get spam + sentiment summary for a post's comments
   */
  async getPostSummary(postId: string): Promise<PostCommentAnalysisSummary> {
    const response = await apiClient.get<{ success: boolean; data: PostCommentAnalysisSummary }>(
      `/comments/summary/${postId}`
    );
    return response.data;
  }

  /**
   * Analyse a single piece of text for spam and sentiment
   */
  async analyseText(text: string): Promise<CommentAnalysisResult> {
    const response = await apiClient.post<{ success: boolean; data: CommentAnalysisResult }>(
      '/comments/analyse',
      { text }
    );
    return response.data;
  }
}

export const commentAnalysisService = new CommentAnalysisService();
