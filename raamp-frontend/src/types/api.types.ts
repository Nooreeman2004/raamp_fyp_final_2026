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
