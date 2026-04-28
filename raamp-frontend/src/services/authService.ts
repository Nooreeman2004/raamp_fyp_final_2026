import { apiClient } from './api';
import type {
  SignupRequest,
  SignupResponse,
  GoogleSignupRequest,
  VerifyEmailRequest,
  VerifyEmailResponse,
  ResendVerificationRequest,
  ResendVerificationResponse,
  LoginRequest,
  LoginResponse,
  UserResponse,
  UpdateProfileRequest,
  UpdateProfileResponse,
  NotificationSettingsRequest,
  NotificationSettingsResponse
} from '@/types';

// Re-export ErrorResponse for backward compatibility
export type { ErrorResponse } from '@/types/api.types';

// Auth API Service
export const authService = {
  /**
   * Sign up a new user
   */
  signup: async (data: SignupRequest): Promise<SignupResponse> => {
    return apiClient.post<SignupResponse>('/auth/signup', data);
  },

  /**
   * Sign up with Google OAuth
   */
  signupWithGoogle: async (data: GoogleSignupRequest): Promise<SignupResponse> => {
    return apiClient.post<SignupResponse>('/auth/signup/google', data);
  },

  /**
   * Sign in with Google OAuth
   */
  signinWithGoogle: async (data: GoogleSignupRequest): Promise<LoginResponse> => {
    return apiClient.post<LoginResponse>('/auth/signin/google', data);
  },

  /**
   * Verify email with OTP code
   */
  verifyEmail: async (data: VerifyEmailRequest): Promise<VerifyEmailResponse> => {
    return apiClient.post<VerifyEmailResponse>('/auth/verify-email', data);
  },

  /**
   * Resend verification code
   */
  resendVerification: async (data: ResendVerificationRequest): Promise<ResendVerificationResponse> => {
    return apiClient.post<ResendVerificationResponse>('/auth/resend-verification', data);
  },

  /**
   * Check whether a given email is already verified
   */
  getVerificationStatus: async (email: string): Promise<{ is_verified: boolean; message: string }> => {
    return apiClient.get<{ is_verified: boolean; message: string }>(`/auth/verification-status?email=${encodeURIComponent(email)}`);
  },

  /**
   * Sign in with email and password
   */
  signin: async (data: LoginRequest): Promise<LoginResponse> => {
    return apiClient.post<LoginResponse>('/auth/signin', data);
  },

  /**
   * Update user profile
   */
  updateProfile: async (data: UpdateProfileRequest): Promise<UpdateProfileResponse> => {
    return apiClient.put<UpdateProfileResponse>('/auth/profile', data);
  },

  /**
   * Get current authenticated user's profile
   */
  getProfile: async (): Promise<UserResponse> => {
    return apiClient.get<UserResponse>('/auth/profile');
  },

  /**
   * Rotate access token while the current one is still valid (same as proactive refresh).
   */
  refreshSession: async (): Promise<LoginResponse> => {
    return apiClient.post<LoginResponse>('/auth/refresh', {});
  },
  /**
   * Send OTP for password change
   */
  sendChangePasswordOtp: async (data: { email: string }): Promise<{ success: boolean; message: string }> => {
    return apiClient.post<{ success: boolean; message: string }>('/auth/change-password/send-otp', data);
  },
  /**
   * Change current user's password (requires OTP)
   */
  changePassword: async (data: { current_password: string; otp_code: string; new_password: string; confirm_password: string; }): Promise<{ success: boolean; message: string }> => {
    return apiClient.post<{ success: boolean; message: string }>('/auth/change-password', data);
  },
  /**
   * Send OTP for profile edit verification
   */
  sendProfileEditOtp: async (data: { email: string }): Promise<{ success: boolean; message: string }> => {
    return apiClient.post<{ success: boolean; message: string }>('/auth/profile/send-edit-otp', data);
  },
  /**
   * Verify OTP for profile edit
   */
  verifyProfileEditOtp: async (data: { email: string; code: string }): Promise<{ success: boolean; message: string }> => {
    return apiClient.post<{ success: boolean; message: string }>('/auth/profile/verify-edit-otp', data);
  },
  /**
   * Logout user
   */
  logout: async (): Promise<{ message: string }> => {
    return apiClient.post<{ message: string }>("/auth/logout", {});
  },

  /**
   * Get notification settings
   */
  getNotificationSettings: async (): Promise<NotificationSettingsResponse> => {
    return apiClient.get<NotificationSettingsResponse>('/settings/notifications');
  },

  /**
   * Update notification settings
   */
  updateNotificationSettings: async (data: NotificationSettingsRequest): Promise<NotificationSettingsResponse> => {
    return apiClient.post<NotificationSettingsResponse>('/settings/notifications', data);
  },
};
