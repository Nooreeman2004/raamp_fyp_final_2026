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
