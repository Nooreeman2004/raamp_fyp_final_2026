import { apiClient } from "@/services/api";

export type CampaignLaunchPlatform = "instagram" | "facebook" | "both";
export type CampaignLaunchMode = "post_now" | "schedule_post" | "post_story";

export interface CampaignLaunchCreateRequest {
  platform: CampaignLaunchPlatform;
  mode: CampaignLaunchMode;
  media_url: string;
  caption?: string | null;
  scheduled_time?: string | null;
  facebook_page_id?: string | null;
  source?: "trend" | "planner" | null;
  campaign_plan_id?: string | null;
  planned_post_id?: string | null;
  trend_keyword?: string | null;
  trend_signal_id?: string | null;
}

export interface CampaignLaunchCreateResponse {
  success: boolean;
  request_id: string;
  status: string;
  message: string;
}

export interface CampaignLaunchItem {
  id: string;
  status: string;
  platform: CampaignLaunchPlatform;
  mode: CampaignLaunchMode;
  media_url: string;
  caption?: string | null;
  scheduled_time?: string | null;
  source?: "trend" | "planner" | null;
  campaign_plan_id?: string | null;
  planned_post_id?: string | null;
  trend_keyword?: string | null;
  trend_signal_id?: string | null;
  created_at: string;
  updated_at: string;
  result?: any;
}

export interface CampaignLaunchListResponse {
  requests: CampaignLaunchItem[];
  total: number;
}

export interface CampaignLaunchApproveResponse {
  success: boolean;
  request_id: string;
  status: string;
  result: any;
}

export interface CampaignLaunchRejectRequest {
  reason: string;
}

export const campaignLaunchService = {
  createRequest: async (payload: CampaignLaunchCreateRequest): Promise<CampaignLaunchCreateResponse> => {
    return apiClient.post<CampaignLaunchCreateResponse>("/campaign-launch/request", payload);
  },

  listRequests: async (limit: number = 50, skip: number = 0): Promise<CampaignLaunchListResponse> => {
    return apiClient.get<CampaignLaunchListResponse>(`/campaign-launch?limit=${limit}&skip=${skip}`);
  },

  approveRequest: async (requestId: string): Promise<CampaignLaunchApproveResponse> => {
    return apiClient.post<CampaignLaunchApproveResponse>(`/campaign-launch/${requestId}/approve`, {});
  },

  rejectRequest: async (requestId: string, reason: string): Promise<CampaignLaunchApproveResponse> => {
    const payload: CampaignLaunchRejectRequest = { reason };
    return apiClient.post<CampaignLaunchApproveResponse>(`/campaign-launch/${requestId}/reject`, payload);
  },
};

