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
  escalation_ticket_id?: string | null;
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

export interface SocialEscalationTicket {
  id: string;
  business_id: string;
  social_account_id: string;
  owner_user_id?: string | null;
  external_ref: string;
  comment_event_id: string;
  draft_id?: string | null;
  platform: "instagram" | "facebook" | string;
  comment_id: string;
  intent?: string | null;
  confidence?: number | null;
  priority: "critical" | "high" | "medium" | string;
  status: "open" | "acknowledged" | "resolved" | string;
  created_at: string;
  updated_at: string;
  first_viewed_at?: string | null;
  acknowledged_at?: string | null;
  resolved_at?: string | null;
  sla_seconds: number;
  sla_due_at?: string | null;
  admin_notification_sent_at?: string | null;
  context?: Record<string, any>;
}

export interface AutoReplyDashboardStats {
  window_hours: number;
  comments: { total: number; facebook: number; instagram: number };
  escalations: { open: number; soonest_sla_due_at?: string | null };
  generated_at: string;
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

  getEscalationTicket: async (ticketId: string): Promise<SocialEscalationTicket> => {
    return apiClient.get(`/social-escalations/${ticketId}`);
  },

  ackEscalationTicket: async (ticketId: string): Promise<{ ok: boolean; status: string }> => {
    return apiClient.post(`/social-escalations/${ticketId}/ack`, {});
  },

  resolveEscalationTicket: async (ticketId: string): Promise<{ ok: boolean; status: string }> => {
    return apiClient.post(`/social-escalations/${ticketId}/resolve`, {});
  },

  getDashboardStats: async (): Promise<AutoReplyDashboardStats> => {
    return apiClient.get(`/auto-replies/dashboard-stats`);
  },
};

