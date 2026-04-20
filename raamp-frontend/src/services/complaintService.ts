import { apiClient } from "./api";

export interface ComplaintSubmitRequest {
  subject: string;
  description: string;
  priority: string;
}

export interface ComplaintSubmitResponse {
  id: string;
}

export interface Complaint {
  id: string;
  userId: string;
  subject: string;
  description: string;
  status: string;
  priority: string;
  adminResponse?: string;
  adminId?: string;
  resolvedAt?: string;
  createdAt: string;
  updatedAt: string;
  statusUpdates?: any[];
  comments?: any[];
  rating?: number;
  attachments?: string[];
}

export const complaintService = {
  submitComplaint: async (data: ComplaintSubmitRequest): Promise<ComplaintSubmitResponse> => {
    return apiClient.post<ComplaintSubmitResponse>("/complaints/submit", data);
  },

  getUserComplaints: async (): Promise<Complaint[]> => {
    return apiClient.get<Complaint[]>("/complaints/user");
  },

  getUserComplaintsPaginated: async (limit: number, offset: number): Promise<Complaint[]> => {
    const qs = new URLSearchParams();
    qs.set("limit", String(limit));
    qs.set("offset", String(offset));
    return apiClient.get<Complaint[]>(`/complaints/user?${qs.toString()}`);
  },

  addComment: async (complaintId: string, text: string) => {
    return apiClient.post<unknown>(`/complaints/${complaintId}/comments`, { text });
  },

  updateComplaint: async (complaintId: string, data: ComplaintSubmitRequest) => {
    return apiClient.put<{ success: boolean }>(`/complaints/${complaintId}`, data);
  },

  submitRating: async (complaintId: string, rating: number) => {
    return apiClient.post<unknown>(`/complaints/${complaintId}/rating`, { rating });
  },

  deleteComplaint: async (complaintId: string) => {
    return apiClient.delete<unknown>(`/complaints/${complaintId}`);
  },

  uploadAttachment: async (complaintId: string, file: File): Promise<{ success: boolean; url?: string }> => {
    const form = new FormData();
    form.append("file", file);
    return apiClient.upload<{ success: boolean; url?: string }>(`/complaints/${complaintId}/attachments`, form);
  }
};
