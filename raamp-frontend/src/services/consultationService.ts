import { apiClient } from './api';

export interface ConsultationRequest {
  first_name: string;
  last_name: string;
  business_email: string;
  company_name: string;
}

export interface ConsultationResponse {
  message: string;
}

export const consultationService = {
  async submitConsultation(data: ConsultationRequest): Promise<ConsultationResponse> {
    return await apiClient.post<ConsultationResponse>('/consultation/submit', data);
  },
};
