/**
 * User-related type definitions
 */

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
  business_domain?: string | null;
  created_at: string;
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

export interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
  confirm_password: string;
}
