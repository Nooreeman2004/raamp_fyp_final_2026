import { isRetryableError, getRetryDelay } from '@/utils/errorHandler';
import { API_BASE_URL } from '@/config/apiBase';
import { refreshAccessToken } from '@/services/tokenRefresh';

export { API_BASE_URL } from '@/config/apiBase';

// API Client
class ApiClient {
  private baseURL: string;
  private maxRetries: number;

  constructor(baseURL: string, maxRetries: number = 3) {
    this.baseURL = baseURL;
    this.maxRetries = maxRetries;
  }

  private shouldAttemptJwtRefresh(endpoint: string): boolean {
    const skip = [
      '/auth/signin',
      '/auth/signup',
      '/auth/refresh',
      '/auth/logout',
      '/auth/forgot-password',
      '/auth/reset-password',
      '/auth/verify-email',
      '/auth/resend-verification',
      '/auth/register',
    ];
    const lower = endpoint.toLowerCase();
    return !skip.some((s) => lower.includes(s));
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retryAttempt: number = 0,
    didTryJwtRefresh: boolean = false
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    // Log Instagram posting requests (DISABLED to reduce duplicate notifications)
    // if (endpoint.includes('/instagram/posting')) {
    //   console.log(`🌐 API REQUEST: ${options.method || 'GET'} ${endpoint}`, {
    //     body: options.body ? JSON.parse(options.body as string) : undefined,
    //     attempt: retryAttempt + 1
    //   });
    // }

    const isFormData = options.body instanceof FormData;

    const headers: HeadersInit = {
      ...options.headers,
    };

    if (!isFormData) {
      headers['Content-Type'] = 'application/json';
    }

    // Add Authorization header if token exists
    const token = localStorage.getItem('token') || sessionStorage.getItem('token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const config: RequestInit = {
      ...options,
      headers,
      credentials: 'include', // Include cookies for CORS
    };

    // Allow configuring timeout via Vite env var VITE_API_TIMEOUT (ms)
    // Use longer timeout for signup/auth endpoints that send emails, and for session checks (profile/refresh).
    const isAuthEndpoint =
      endpoint.includes('/auth/signup') ||
      endpoint.includes('/auth/verify') ||
      endpoint.includes('/auth/profile') ||
      endpoint.includes('/auth/refresh');
    const isSocialPosting = endpoint.includes('/instagram/posting/post') ||
      endpoint.includes('/facebook/posting/post') ||
      endpoint.includes('/social/post'); // Unified social posting endpoint
    const isTrending = endpoint.includes('/trends/') || endpoint.includes('/arbitrage/');
    const isChatbot = endpoint.includes('/chatbot/chat'); // Chatbot RAG pipeline needs time
    const isMediaGeneration =
      endpoint.includes('/media/reels/') ||
      endpoint.includes('/media/videos/') ||
      endpoint.includes('/media/generate-quick-reel');

    // Geo-intent (Trends + Places + Weather in parallel, or multi-zone recommend) often exceeds 20s under API latency.
    const isGeoEndpoint = endpoint.includes('/v1/geo/');
    const isCampaignPlanner = endpoint.includes('/campaign-planner/');

    // Social posting, trends, chatbot RAG, and media generation can run 60s+ on the backend
    const baseDefault = isAuthEndpoint
      ? 30000
      : isSocialPosting || isTrending || isChatbot
        ? 60000
        : isMediaGeneration
          ? 120000
          : isCampaignPlanner
            ? 25000
          : 20000;

    // recommend-zones runs 4–8 parallel full signal ingests — often slower than a single heat-score.
    const isGeoRecommendZones = endpoint.includes('/v1/geo/recommend-zones');
    const geoTimeoutEnv = Number(import.meta.env.VITE_GEO_API_TIMEOUT);
    const defaultGeoFloor = isGeoRecommendZones ? 120000 : 30000;
    const geoFloorMs =
      !Number.isNaN(geoTimeoutEnv) && geoTimeoutEnv > 0 ? geoTimeoutEnv : defaultGeoFloor;
    const defaultTimeout = isGeoEndpoint ? geoFloorMs : baseDefault;

    const globalOverride = Number(import.meta.env.VITE_API_TIMEOUT);
    const timeoutMs =
      !Number.isNaN(globalOverride) && globalOverride > 0
        ? isGeoEndpoint
          ? Math.max(globalOverride, defaultTimeout)
          : globalOverride
        : defaultTimeout;

    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(url, { ...config, signal: controller.signal });

      clearTimeout(id);

      // Check if response is JSON
      const contentType = response.headers.get('content-type');
      const isJson = contentType && contentType.includes('application/json');

      const data = isJson ? await response.json() : await response.text();

      // Log Instagram posting responses (DISABLED to reduce duplicate notifications)
      // if (endpoint.includes('/instagram/posting')) {
      //   console.log(`🌐 API RESPONSE: ${options.method || 'GET'} ${endpoint}`, {
      //     status: response.status,
      //     ok: response.ok,
      //     data: isJson ? data : 'non-JSON response'
      //   });
      // }

      if (!response.ok) {
        if (
          response.status === 401 &&
          !didTryJwtRefresh &&
          this.shouldAttemptJwtRefresh(endpoint)
        ) {
          const newToken = await refreshAccessToken();
          if (newToken) {
            return this.request<T>(endpoint, options, retryAttempt, true);
          }
        }

        // Extract error data
        let errorMessage = 'An unexpected error occurred';
        const errorData = isJson ? data : {};

        if (isJson) {
          // Priority 1: Explicit 'errors' object (e.g. from 400 Bad Request)
          if (data.errors && typeof data.errors === 'object') {
            errorMessage = `${data.message || 'Validation Error'}: ${Object.entries(data.errors).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`).join(' | ')}`;
          }
          // Priority 2: 'detail' array (e.g. from Pydantic 422)
          else if (Array.isArray(data.detail)) {
            const hasRadiusError = data.detail.some((e: any) => e.loc?.includes('radius'));
            const hasKeywordError = data.detail.some((e: any) => e.loc?.includes('keywords'));
            
            if (hasRadiusError) {
              errorMessage = "The selected radar radius exceeds the maximum allowable scan distance. Please pull back the radius and try again.";
            } else if (hasKeywordError) {
               errorMessage = "Invalid audience keywords detected. Please update your business setup.";
            } else {
              errorMessage = "We encountered an issue with the provided form data. Please review your inputs and try again.";
            }
          }
          // Priority 3: 'detail' string
          else if (typeof data.detail === 'string') {
            errorMessage = data.detail;
          }
          // Priority 4: 'message' string
          else if (data.message) {
            errorMessage = data.message;
          }

          // Auth-specific error handling with detailed messages
          if (endpoint.includes('/auth/signin') || endpoint.includes('/auth/login')) {
            if (response.status === 401 || response.status === 422) {
              // Check backend error message for specific issues
              const lowerError = errorMessage.toLowerCase();

              if (lowerError.includes('email not found') ||
                lowerError.includes('user not found') ||
                lowerError.includes('account not found') ||
                lowerError.includes('no account') ||
                lowerError.includes('does not exist')) {
                errorMessage = 'No account found with this email.';
              } else if (lowerError.includes('not verified') ||
                lowerError.includes('unverified') ||
                lowerError.includes('verify your email')) {
                errorMessage = 'Email not verified. Please check your inbox for the verification link.';
              } else if (lowerError.includes('wrong password') ||
                lowerError.includes('incorrect password') ||
                lowerError.includes('invalid credentials') ||
                lowerError.includes('invalid email or password')) {
                errorMessage = 'Incorrect email or password.';
              } else if (lowerError.includes('sign in failed') || lowerError.includes('signin failed')) {
                errorMessage = 'Incorrect email or password.';
              } else {
                // Generic 401/422 for login
                errorMessage = 'Incorrect email or password.';
              }
            } else if (response.status === 400) {
              const lowerError = errorMessage.toLowerCase();
              // Sign-in: unverified email must be detected before generic "email" checks
              // (otherwise "verify your email" is misread as invalid email format).
              if (
                lowerError.includes('verify your email') ||
                lowerError.includes('not verified') ||
                lowerError.includes('unverified')
              ) {
                errorMessage =
                  'Email not verified. Enter the verification code we sent to your inbox.';
              } else if (lowerError.includes('invalid email or password')) {
                errorMessage = 'Incorrect email or password.';
              } else if (lowerError.includes('email')) {
                errorMessage = 'Please enter a valid email address.';
              } else if (lowerError.includes('password')) {
                errorMessage = 'Password is required.';
              } else if (lowerError.includes('sign in failed') || lowerError.includes('signin failed')) {
                errorMessage = 'Incorrect email or password.';
              } else {
                errorMessage = 'Invalid input. Please check your email and password.';
              }
            } else if (response.status === 403) {
              errorMessage = 'Account is locked or disabled. Please contact support.';
            } else if (response.status === 429) {
              errorMessage = 'Too many login attempts. Please try again later.';
            } else if (response.status >= 500) {
              errorMessage = 'Server error. Please try again later.';
            }
          }

          // Signup-specific error handling
          if (endpoint.includes('/auth/signup') || endpoint.includes('/auth/register')) {
            if (response.status === 409 || response.status === 400) {
              const lowerError = errorMessage.toLowerCase();
              if (lowerError.includes('email') && lowerError.includes('exists')) {
                errorMessage = 'An account with this email already exists. Please login instead.';
              } else if (lowerError.includes('username') && lowerError.includes('exists')) {
                errorMessage = 'This username is already taken. Please choose another.';
              }
            } else if (response.status >= 500) {
              errorMessage = 'Server error. Please try again later.';
            }
          }
        } else {
          // Vite proxy / upstream failures often return a non-JSON empty body.
          // Ensure we still surface a useful message to the UI/logs.
          if (typeof data === 'string' && data.trim().length > 0) {
            errorMessage = data;
          } else {
            errorMessage = `${response.status} ${response.statusText}`.trim();
          }
        }

        // Never expose raw server/internal errors to end-users.
        // Backend may include exception details in development; we intentionally hide them.
        if (response.status >= 500) {
          errorMessage = 'Something went wrong on our side. Please try again.';
        }

        const error = {
          status: response.status,
          message: errorMessage,
          ...(isJson ? data : {}),
        };

        // Retry on retryable errors
        const skipRetry = isSocialPosting && (error.status === 0 || error.errors?.timeout);
        if (isRetryableError(error) && retryAttempt < this.maxRetries && !skipRetry) {
          const delay = getRetryDelay(retryAttempt);
          await new Promise(resolve => setTimeout(resolve, delay));
          return this.request<T>(endpoint, options, retryAttempt + 1, didTryJwtRefresh);
        }

        throw error;
      }

      return data;
    } catch (error: any) {
      clearTimeout(id);

      // Don't log 404 errors for expected endpoints (like hyperlocal-setup/current when no data exists)
      const name = error?.name || (error instanceof DOMException ? error.name : '');
      const isAbortError = name === 'AbortError';
      const is404Expected = error?.status === 404 && (
        endpoint.includes('/hyperlocal-setup/current') ||
        endpoint.includes('/trends/spike_timeline')
      );

      if (!is404Expected && !isAbortError) {
        console.error('API Error:', error);
      }

      // Handle aborted requests (timeout)
      if (error instanceof DOMException && error.name === 'AbortError') {
        const timeoutError = {
          status: 0,
          message: endpoint.includes('/auth/signin') || endpoint.includes('/auth/login')
            ? 'Request timed out. Please check your connection and try again.'
            : 'Server took too long to respond. Please try again.',
          errors: { timeout: 'request aborted' },
        };

        // Retry on timeout if we haven't exceeded max retries (avoid triple-wait on slow geo endpoints)
        const skipTimeoutRetry =
          isSocialPosting || (isGeoEndpoint && isGeoRecommendZones);
        if (retryAttempt < this.maxRetries && !skipTimeoutRetry) {
          const delay = getRetryDelay(retryAttempt);
          await new Promise(resolve => setTimeout(resolve, delay));
          return this.request<T>(endpoint, options, retryAttempt + 1, didTryJwtRefresh);
        }

        throw timeoutError;
      }

      // Handle network errors (failed to fetch)
      if (error instanceof TypeError && error.message === 'Failed to fetch') {
        const networkError = {
          status: 0,
          message: endpoint.includes('/auth/signin') || endpoint.includes('/auth/login')
            ? 'Network error. Please check your connection and try again.'
            : 'Unable to connect to server. Please check your internet connection.',
          errors: { network: 'Failed to fetch' }
        };

        // Retry on network errors if we haven't exceeded max retries
        if (retryAttempt < this.maxRetries && !isSocialPosting) {
          const delay = getRetryDelay(retryAttempt);
          await new Promise(resolve => setTimeout(resolve, delay));
          return this.request<T>(endpoint, options, retryAttempt + 1, didTryJwtRefresh);
        }

        throw networkError;
      }

      // If it's a retryable error and we haven't exceeded max retries, retry
      if (isRetryableError(error) && retryAttempt < this.maxRetries) {
        const delay = getRetryDelay(retryAttempt);
        await new Promise(resolve => setTimeout(resolve, delay));
        return this.request<T>(endpoint, options, retryAttempt + 1, didTryJwtRefresh);
      }

      throw error;
    }
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async put<T>(endpoint: string, data: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async patch<T>(endpoint: string, data: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  async upload<T>(endpoint: string, formData: FormData): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: formData,
    });
  }

  /**
   * GET binary response (e.g. media download) with the same auth, timeout, and retry behavior as JSON requests.
   */
  async getBlob(endpoint: string): Promise<Blob> {
    const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = `${this.baseURL}${path}`;
    const token = localStorage.getItem('token') || sessionStorage.getItem('token');
    const headers: HeadersInit = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const defaultTimeout =
      path.includes('/reels/') || path.includes('/videos/') ? 120000 : 60000;
    const timeoutMs = Number(import.meta.env.VITE_API_TIMEOUT) || defaultTimeout;
    return this.blobFetch(url, headers, timeoutMs, 0);
  }

  private async blobFetch(
    url: string,
    headers: HeadersInit,
    timeoutMs: number,
    retryAttempt: number
  ): Promise<Blob> {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(url, {
        method: 'GET',
        headers,
        credentials: 'include',
        signal: controller.signal,
      });
      clearTimeout(id);

      if (!response.ok) {
        const err = {
          status: response.status,
          message: `${response.status} ${response.statusText}`.trim() || 'Download failed',
        };
        if (isRetryableError(err) && retryAttempt < this.maxRetries) {
          const delay = getRetryDelay(retryAttempt);
          await new Promise((resolve) => setTimeout(resolve, delay));
          return this.blobFetch(url, headers, timeoutMs, retryAttempt + 1);
        }
        throw err;
      }

      return response.blob();
    } catch (error: unknown) {
      clearTimeout(id);
      const name =
        error instanceof DOMException ? error.name : (error as { name?: string })?.name;
      const isAbortError = name === 'AbortError';

      if (!isAbortError) {
        console.error('API getBlob error:', error);
      }

      if (isAbortError) {
        const timeoutError = {
          status: 0,
          message: 'Server took too long to respond. Please try again.',
          errors: { timeout: 'request aborted' },
        };
        if (retryAttempt < this.maxRetries) {
          const delay = getRetryDelay(retryAttempt);
          await new Promise((resolve) => setTimeout(resolve, delay));
          return this.blobFetch(url, headers, timeoutMs, retryAttempt + 1);
        }
        throw timeoutError;
      }

      if (error instanceof TypeError && error.message === 'Failed to fetch') {
        const networkError = {
          status: 0,
          message: 'Unable to connect to server. Please check your internet connection.',
          errors: { network: 'Failed to fetch' },
        };
        if (retryAttempt < this.maxRetries) {
          const delay = getRetryDelay(retryAttempt);
          await new Promise((resolve) => setTimeout(resolve, delay));
          return this.blobFetch(url, headers, timeoutMs, retryAttempt + 1);
        }
        throw networkError;
      }

      if (isRetryableError(error) && retryAttempt < this.maxRetries) {
        const delay = getRetryDelay(retryAttempt);
        await new Promise((resolve) => setTimeout(resolve, delay));
        return this.blobFetch(url, headers, timeoutMs, retryAttempt + 1);
      }

      throw error;
    }
  }
}

export const apiClient = new ApiClient(API_BASE_URL);
