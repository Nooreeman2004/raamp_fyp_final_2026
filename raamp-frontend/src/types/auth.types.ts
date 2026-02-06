/**
 * Authentication-related type definitions
 */

import { UserResponse } from './user.types';

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

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  user: UserResponse;
  message: string;
}

export interface GoogleAuthResult {
  uid: string;
  idToken: string;
  email: string;
  displayName: string;
  photoURL: string | null;
}

export interface AuthContextType {
  user: UserResponse | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  refreshUser: () => Promise<void>;
  logout: () => Promise<void>;
}
