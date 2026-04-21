import { apiClient } from "@/services/api";

export type AutoReplyDraftStatus = "active" | "expired" | "sent" | "skipped";

export interface AutoReplyDraftItem {
  id: string;
  platform: "instagram" | "facebook";
  comment_id: string;
  suggested_reply: string;
  alternatives: string[];
  requires_user_action: boolean;
  status: AutoReplyDraftStatus | string;
  expires_at: string;
  created_at: string;
  updated_at: string;
  approval_nonce: string;
  comment_text?: string | null;
}

export interface AutoReplyDraftListResponse {
  drafts: AutoReplyDraftItem[];
  total: number;
}

export interface AutoReplyApproveResponse {
  success: boolean;
  status: string;
  reply_id?: string | null;
  sent_id?: string | null;
  message?: string | null;
}

export interface AutoReplySkipResponse {
  success: boolean;
  status: string;
}

export const autoReplyService = {
  listDrafts: async (
    status_filter: AutoReplyDraftStatus | string = "active",
    limit: number = 50,
    skip: number = 0
  ): Promise<AutoReplyDraftListResponse> => {
    const qs = new URLSearchParams();
    qs.set("status_filter", String(status_filter));
    qs.set("limit", String(limit));
    qs.set("skip", String(skip));
    return apiClient.get<AutoReplyDraftListResponse>(`/auto-replies/drafts?${qs.toString()}`);
  },

  approveDraft: async (
    draftId: string,
    payload: { approval_nonce: string; message?: string | null }
  ): Promise<AutoReplyApproveResponse> => {
    return apiClient.post<AutoReplyApproveResponse>(`/auto-replies/drafts/${draftId}/approve`, payload);
  },

  skipDraft: async (draftId: string, reason?: string): Promise<AutoReplySkipResponse> => {
    return apiClient.post<AutoReplySkipResponse>(`/auto-replies/drafts/${draftId}/skip`, { reason: reason || null });
  },

  getSettings: async (): Promise<{
    instagram_auto_replies_enabled: boolean;
    instagram_mode: "review_only" | "hybrid_auto" | string;
    facebook_auto_replies_enabled: boolean;
    facebook_mode: "review_only" | "hybrid_auto" | string;
    thread_context_depth: number;
    updated_at: string;
  }> => {
    return apiClient.get(`/auto-replies/settings`);
  },

  patchSettings: async (payload: Partial<{
    instagram_auto_replies_enabled: boolean;
    instagram_mode: "review_only" | "hybrid_auto";
    facebook_auto_replies_enabled: boolean;
    facebook_mode: "review_only" | "hybrid_auto";
    thread_context_depth: number;
  }>): Promise<{
    instagram_auto_replies_enabled: boolean;
    instagram_mode: string;
    facebook_auto_replies_enabled: boolean;
    facebook_mode: string;
    thread_context_depth: number;
    updated_at: string;
  }> => {
    return apiClient.patch(`/auto-replies/settings`, payload);
  },
};

