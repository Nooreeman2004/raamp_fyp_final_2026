/**
 * Business-related type definitions
 */

export interface BusinessDomain {
  id: string;
  business: string;
  description: string;
}

export interface BusinessLocation {
  latitude: number;
  longitude: number;
  business_name?: string;
  address?: string;
}

export interface GoogleBusinessConnection {
  connected: boolean;
  business_name?: string;
  latitude?: number;
  longitude?: number;
  address?: string;
}

export interface FacebookConnection {
  connected: boolean;
  page_id?: string;
  page_name?: string;
}

export interface InstagramConnection {
  connected: boolean;
  username?: string;
  account_id?: string;
}

export interface OnboardingStatus {
  facebook_connected: boolean;
  instagram_connected: boolean;
  google_maps_connected: boolean;
}

export interface OnboardingData {
  connections?: {
    facebook?: FacebookConnection;
    instagram?: InstagramConnection;
    google_business?: GoogleBusinessConnection;
  };
}
