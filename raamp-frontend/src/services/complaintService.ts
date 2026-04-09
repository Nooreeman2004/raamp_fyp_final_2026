import api from "./api";

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
    const response = await api.post("/complaints/submit", data);
    return response.data;
  },

  getUserComplaints: async (): Promise<Complaint[]> => {
    const response = await api.get("/complaints/user");
    return response.data;
  },

  addComment: async (complaintId: string, text: string) => {
    const response = await api.post(`/complaints/${complaintId}/comments`, { text });
    return response.data;
  },

  submitRating: async (complaintId: string, rating: number) => {
    const response = await api.post(`/complaints/${complaintId}/rating`, { rating });
    return response.data;
  },

  deleteComplaint: async (complaintId: string) => {
    const response = await api.delete(`/complaints/${complaintId}`);
    return response.data;
  }
};
