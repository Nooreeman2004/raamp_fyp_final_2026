import { apiClient } from "@/services/api";

export type PlannerObjective = "awareness" | "engagement" | "foot_traffic" | "sales" | "leads";
export type PlannerFrequency = "daily" | "3_per_week" | "5_per_week" | "custom";
export type PlannedPostType = "reel" | "carousel" | "story" | "static";
export type PlannedPostStatus =
  | "planned"
  | "draft_created"
  | "approval_requested"
  | "approved"
  | "scheduled"
  | "published"
  | "failed";

export interface CampaignPlannerCreateRequest {
  idea: string;
  objective: PlannerObjective;
  budget_min?: number | null;
  budget_max?: number | null;
  start_date: string; // ISO
  end_date: string; // ISO
  timezone: string; // IANA
  posting_frequency: PlannerFrequency;
  platforms: Array<"instagram" | "facebook" | "both">;
  target_audience?: string | null;
  offer_or_cta?: string | null;
  constraints?: string | null;
}

export interface CampaignPlannerCreateResponse {
  plan_id: string;
  generation_status: string;
}

export interface PlannedPostItem {
  id: string;
  campaign_plan_id: string;
  scheduled_time: string;
  timezone: string;
  title: string;
  post_type: PlannedPostType;
  status: PlannedPostStatus;
  prompts: any;
  cta?: string | null;
  hashtags: string[];
  why_it_fits_brand?: string | null;
  draft_id?: string | null;
  launch_request_id?: string | null;
  last_error?: string | null;
  last_error_at?: string | null;
}

export interface CampaignPlanListItem {
  id: string;
  name: string;
  objective?: string | null;
  start_date: string;
  end_date: string;
  timezone: string;
  generation_status: string;
  created_at: string;
}

export interface CampaignPlanListResponse {
  plans: CampaignPlanListItem[];
  total: number;
}

export interface CampaignPlanDetailResponse {
  id: string;
  input_brief: any;
  generated: any;
  start_date: string;
  end_date: string;
  timezone: string;
  posting_frequency: string;
  generation_status: string;
  generation_error?: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  posts: PlannedPostItem[];
}

export interface CalendarResponse {
  items: PlannedPostItem[];
}

export interface ConvertToDraftResponse {
  success: boolean;
  draft_id: string;
}

export interface RequestApprovalResponse {
  success: boolean;
  request_id: string;
  status: string;
}

export const campaignPlannerService = {
  createPlan: async (payload: CampaignPlannerCreateRequest): Promise<CampaignPlannerCreateResponse> => {
    return apiClient.post<CampaignPlannerCreateResponse>("/campaign-planner/plans", payload);
  },

  listPlans: async (limit: number = 50, skip: number = 0): Promise<CampaignPlanListResponse> => {
    return apiClient.get<CampaignPlanListResponse>(`/campaign-planner/plans?limit=${limit}&skip=${skip}`);
  },

  getPlan: async (planId: string): Promise<CampaignPlanDetailResponse> => {
    return apiClient.get<CampaignPlanDetailResponse>(`/campaign-planner/plans/${planId}`);
  },

  deletePlan: async (planId: string): Promise<void> => {
    return apiClient.delete(`/campaign-planner/plans/${planId}`);
  },

  getCalendar: async (startIso: string, endIso: string, params?: { campaign_ids?: string[]; tz?: string; status?: string }) => {
    const tz = params?.tz || "UTC";
    const ids = params?.campaign_ids?.length ? `&campaign_ids=${encodeURIComponent(params.campaign_ids.join(","))}` : "";
    const st = params?.status ? `&status=${encodeURIComponent(params.status)}` : "";
    return apiClient.get<CalendarResponse>(
      `/campaign-planner/calendar?start=${encodeURIComponent(startIso)}&end=${encodeURIComponent(endIso)}&tz=${encodeURIComponent(tz)}${ids}${st}`
    );
  },

  convertToDraft: async (postId: string): Promise<ConvertToDraftResponse> => {
    return apiClient.post<ConvertToDraftResponse>(`/campaign-planner/planned-posts/${postId}/convert-to-draft`, {});
  },

  requestApproval: async (
    postId: string,
    params: { mode: "post_now" | "schedule_post" | "post_story"; platform: "instagram" | "facebook" | "both"; media_url: string }
  ): Promise<RequestApprovalResponse> => {
    const query =
      `mode=${encodeURIComponent(params.mode)}` +
      `&platform=${encodeURIComponent(params.platform)}` +
      `&media_url=${encodeURIComponent(params.media_url)}`;
    return apiClient.post<RequestApprovalResponse>(`/campaign-planner/planned-posts/${postId}/request-approval?${query}`, {});
  },
};

