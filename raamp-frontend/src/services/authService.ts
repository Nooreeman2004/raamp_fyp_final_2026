import { apiClient } from './api';

// Types
export interface SignupRequest {
  username: string;
  email: string;
  password: string;
  agreed_to_terms: boolean;
}

export interface SignupResponse {
  id: string;
  username: string;
  email: string;
  created_at: string;
  message: string;
}

export interface GoogleSignupRequest {
  id_token: string;
  email: string;
  display_name: string;
  photo_url?: string | null;
}

export interface ErrorResponse {
  success: false;
  errors: Record<string, string | string[]>;
  message: string;
}

export interface VerifyEmailRequest {
  email: string;
  code: string;
  profile_picture?: string | null;
}

export interface VerifyEmailResponse {
  message: string;
}

export interface ResendVerificationRequest {
  email: string;
}

export interface ResendVerificationResponse {
  message: string;
}

export interface SignInRequest {
  email: string;
  password: string;
}

export interface UserResponse {
  id: string;
  username: string;
  email: string;
  is_verified: boolean;
  profile_completed: boolean;
  first_name?: string | null;
  last_name?: string | null;
  phone_number?: string | null;
  company?: string | null;
  role?: string | null;
  bio?: string | null;
  profile_picture?: string | null;
  created_at: string;
}

export interface SignInResponse {
  user: UserResponse;
  message: string;
}

export interface UpdateProfileRequest {
  first_name?: string;
  last_name?: string;
  phone_number?: string;
  company?: string;
  role?: string;
  bio?: string;
  business_domain?: string;
}

export interface UpdateProfileResponse {
  user: UserResponse;
  message: string;
}

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
  signin: async (data: SignInRequest): Promise<SignInResponse> => {
    return apiClient.post<SignInResponse>('/auth/signin', data);
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
   * Send OTP for password change
   */
  sendChangePasswordOtp: async (data: { email: string }): Promise<{ success: boolean; message: string }> => {
    return apiClient.post<{ success: boolean; message: string }>('/auth/change-password/send-otp', data);
  },
  /**
   * Change current user's password (requires OTP)
   */
  changePassword: async (data: { otp_code: string; new_password: string; confirm_password: string; }): Promise<{ success: boolean; message: string }> => {
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
};
