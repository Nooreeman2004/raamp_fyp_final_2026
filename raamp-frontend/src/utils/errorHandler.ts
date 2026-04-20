/**
 * Utility functions for handling and displaying user-friendly error messages
 */

import type { ApiError } from '@/types/api.types';

/**
 * Extracts a user-friendly error message from an API error
 */
export const getErrorMessage = (error: unknown): string => {
  const apiError = error as ApiError;

  // Network errors
  if (apiError?.status === 0 || (error instanceof TypeError && error.message === 'Failed to fetch')) {
    return "Unable to connect to the server. Please check your internet connection and try again.";
  }

  // Timeout errors
  if (apiError?.errors?.timeout) {
    return "Request timed out. The server is taking too long to respond. Please try again.";
  }

  // HTTP status code errors
  if (apiError?.status) {
    switch (apiError.status) {
      case 400:
        return apiError.message || "Invalid request. Please check your input and try again.";
      case 401:
        return "You are not authenticated. Please login again.";
      case 402:
        return apiError.message || "Not enough ad credits for this action. Add funds or upgrade to continue.";
      case 403:
        return "You don't have permission to perform this action.";
      case 404:
        return "The requested resource was not found.";
      case 409:
        return apiError.message || "A conflict occurred. This resource may already exist.";
      case 422:
        // Validation errors
        if (apiError.errors) {
          const errorMessages = Object.values(apiError.errors)
            .flat()
            .filter((msg): msg is string => typeof msg === 'string')
            .join(', ');
          return errorMessages || "Validation failed. Please check your input.";
        }
        return apiError.message || "Validation failed. Please check your input.";
      case 429:
        return "Too many requests. Please wait a moment and try again.";
      case 500:
        return "A server error occurred. Please try again later or contact support.";
      case 502:
      case 503:
        return "The service is temporarily unavailable. Please try again later.";
      case 504:
        return "The server took too long to respond. Please try again.";
      default:
        return apiError.message || `An error occurred (${apiError.status}). Please try again.`;
    }
  }

  // Error with message
  if (apiError?.message) {
    return apiError.message;
  }

  // Error with detail
  if (apiError?.detail) {
    return apiError.detail;
  }

  // Error with errors object
  if (apiError?.errors) {
    const errorMessages = Object.values(apiError.errors)
      .flat()
      .filter((msg): msg is string => typeof msg === 'string')
      .join(', ');
    if (errorMessages) {
      return errorMessages;
    }
  }

  // Generic fallback
  return "An unexpected error occurred. Please try again or contact support if the problem persists.";
};

/**
 * Checks if an error is retryable
 */
export const isRetryableError = (error: unknown): boolean => {
  const apiError = error as ApiError;

  // Network errors are retryable
  if (apiError?.status === 0 || (error instanceof TypeError && error.message === 'Failed to fetch')) {
    return true;
  }

  // Timeout errors are retryable
  if (apiError?.errors?.timeout) {
    return true;
  }

  // Server errors (5xx) are retryable, except 501 (Not Implemented)
  if (apiError?.status && apiError.status >= 500 && apiError.status !== 501) {
    return true;
  }

  // Rate limiting (429) is retryable
  if (apiError?.status === 429) {
    return true;
  }

  // Gateway errors are retryable
  if (apiError?.status === 502 || apiError?.status === 503 || apiError?.status === 504) {
    return true;
  }

  return false;
};

/**
 * Gets a retry delay in milliseconds based on attempt number
 */
export const getRetryDelay = (attempt: number, baseDelay: number = 1000): number => {
  // Exponential backoff: baseDelay * 2^attempt, with max of 10 seconds
  return Math.min(baseDelay * Math.pow(2, attempt), 10000);
};

