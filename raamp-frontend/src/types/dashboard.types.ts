/**
 * Dashboard-related type definitions
 */

export interface DashboardMetrics {
  roas?: number;
  conversionRate?: number;
  totalAdSpend?: number;
  budgetAllocation?: {
    used: number;
    total: number;
    percentage: number;
  };
  projectedROI?: number;
}

export interface GeoLocation {
  lat: number;
  lng: number;
  name?: string;
}

export interface HighIntentArea extends GeoLocation {
  intensity?: number;
}
