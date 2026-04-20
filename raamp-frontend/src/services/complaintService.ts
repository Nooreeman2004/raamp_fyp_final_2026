import { apiClient } from "./api";

export interface ComplaintSubmitRequest {
  subject: string;
  description: string;
  priority: string;
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
  submitComplaint: async (data: ComplaintSubmitRequest) => {
    return apiClient.post<unknown>("/complaints/submit", data);
  },

  getUserComplaints: async (): Promise<Complaint[]> => {
    return apiClient.get<Complaint[]>("/complaints/user");
  },

  addComment: async (complaintId: string, text: string) => {
    return apiClient.post<unknown>(`/complaints/${complaintId}/comments`, { text });
  },

  submitRating: async (complaintId: string, rating: number) => {
    return apiClient.post<unknown>(`/complaints/${complaintId}/rating`, { rating });
  },

  deleteComplaint: async (complaintId: string) => {
    return apiClient.delete<unknown>(`/complaints/${complaintId}`);
  }
};
