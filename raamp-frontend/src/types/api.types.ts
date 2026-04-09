/**
 * API-related type definitions
 */

export interface ApiError {
  status?: number;
  message?: string;
  errors?: Record<string, string | string[]>;
  detail?: string;
}

export interface ErrorResponse {
  success: false;
  errors: Record<string, string | string[]>;
  message: string;
}

export interface SuccessResponse<T = unknown> {
  success: true;
  data: T;
  message?: string;
}

export type ApiResponse<T = unknown> = SuccessResponse<T> | ErrorResponse;

export interface NotificationSettingsRequest {
  email_alerts: boolean;
  push_notifications: boolean;
  sms_alerts: boolean;
  marketing_alerts: boolean;
  campaign_alerts: boolean;
  performance_alerts: boolean;
  trend_alerts: boolean;
  billing_alerts: boolean;
}

export interface NotificationSettingsResponse {
  success: boolean;
  email_alerts: boolean;
  sms_alerts: boolean;
  push_notifications: boolean;
  marketing_alerts: boolean;
  campaign_alerts?: boolean;
  performance_alerts?: boolean;
  trend_alerts?: boolean;
  billing_alerts?: boolean;
  updated_at: string;
}

export interface BillingProfileRequest {
  full_name: string;
  company_name: string;
  email: string;
  phone: string;
  address_line1: string;
  address_line2: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  tax_id: string;
  payment_method_type: 'credit_card' | 'debit_card' | 'bank_transfer' | 'paypal';
  card_last_four: string;
  card_expiry_month: number;
  card_expiry_year: number;
}

export interface BillingProfileGetResponse {
  success: boolean;
  full_name: string;
  company_name: string;
  email: string;
  phone: string;
  address_line1: string;
  address_line2: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  tax_id: string;
  payment_method_type: string;
  card_last_four: string;
  card_expiry_month: number;
  card_expiry_year: number;
  updated_at: string;
}

export interface BillingProfileResponse {
  success: boolean;
  message: string;
  data: {
    full_name: string;
    company_name: string;
    email: string;
    phone: string;
    address: string;
    payment_method: string;
    card_expiry: string;
  };
  updated_at: string;
}
