import { isRetryableError, getRetryDelay } from '@/utils/errorHandler';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

// API Client
class ApiClient {
  private baseURL: string;
  private maxRetries: number;

  constructor(baseURL: string, maxRetries: number = 3) {
    this.baseURL = baseURL;
    this.maxRetries = maxRetries;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retryAttempt: number = 0
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    // Log Instagram posting requests (DISABLED to reduce duplicate notifications)
    // if (endpoint.includes('/instagram/posting')) {
    //   console.log(`🌐 API REQUEST: ${options.method || 'GET'} ${endpoint}`, {
    //     body: options.body ? JSON.parse(options.body as string) : undefined,
    //     attempt: retryAttempt + 1
    //   });
    // }

    // Development-only mock switch. Set VITE_USE_MOCK_API=true in .env to enable.
    const useMock = import.meta.env.VITE_USE_MOCK_API === 'true';
    if (useMock && endpoint === '/auth/signup' && options.method === 'POST') {
      // Simulate network latency and return a successful signup response
      await new Promise((res) => setTimeout(res, 600));
      // eslint-disable-next-line @typescript-eslint/consistent-type-assertions
      return {
        id: 'mock-id-123',
        username: 'mockuser',
        email: JSON.parse(options.body as string).email,
        created_at: new Date().toISOString(),
        message: 'Mock account created',
      } as unknown as T;
    }

    const isFormData = options.body instanceof FormData;

    const headers: HeadersInit = {
      ...options.headers,
    };

    if (!isFormData) {
      headers['Content-Type'] = 'application/json';
    }

    // Add Authorization header if token exists
    const token = localStorage.getItem('token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const config: RequestInit = {
      ...options,
      headers,
      credentials: 'include', // Include cookies for CORS
    };

    // Allow configuring timeout via Vite env var VITE_API_TIMEOUT (ms)
    // Use longer timeout for signup/auth endpoints that send emails
    const isAuthEndpoint = endpoint.includes('/auth/signup') || endpoint.includes('/auth/verify');
    const isSocialPosting = endpoint.includes('/instagram/posting/post') ||
      endpoint.includes('/facebook/posting/post') ||
      endpoint.includes('/social/post'); // Unified social posting endpoint

    // Social media posting can take up to 45s-60s on the backend
    const defaultTimeout = isAuthEndpoint ? 30000 : (isSocialPosting ? 60000 : 10000);
    const timeoutMs = Number(import.meta.env.VITE_API_TIMEOUT) || defaultTimeout;

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
            errorMessage = `Validation Error: ${data.detail.map((e: any) => e.msg || JSON.stringify(e)).join(', ')}`;
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
              } else {
                // Generic 401/422 for login
                errorMessage = 'Incorrect email or password.';
              }
            } else if (response.status === 400) {
              const lowerError = errorMessage.toLowerCase();
              if (lowerError.includes('email')) {
                errorMessage = 'Please enter a valid email address.';
              } else if (lowerError.includes('password')) {
                errorMessage = 'Password is required.';
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
          errorMessage = typeof data === 'string' ? data : 'Unknown network error';
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
          return this.request<T>(endpoint, options, retryAttempt + 1);
        }

        throw error;
      }

      return data;
    } catch (error: any) {
      clearTimeout(id);

      // Don't log 404 errors for expected endpoints (like hyperlocal-setup/current when no data exists)
      const is404Expected = error?.status === 404 && (
        endpoint.includes('/hyperlocal-setup/current')
      );

      if (!is404Expected) {
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

        // Retry on timeout if we haven't exceeded max retries
        if (retryAttempt < this.maxRetries && !isSocialPosting) {
          const delay = getRetryDelay(retryAttempt);
          await new Promise(resolve => setTimeout(resolve, delay));
          return this.request<T>(endpoint, options, retryAttempt + 1);
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
          return this.request<T>(endpoint, options, retryAttempt + 1);
        }

        throw networkError;
      }

      // If it's a retryable error and we haven't exceeded max retries, retry
      if (isRetryableError(error) && retryAttempt < this.maxRetries) {
        const delay = getRetryDelay(retryAttempt);
        await new Promise(resolve => setTimeout(resolve, delay));
        return this.request<T>(endpoint, options, retryAttempt + 1);
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

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  async upload<T>(endpoint: string, formData: FormData): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: formData,
    });
  }
}

export const apiClient = new ApiClient(API_BASE_URL);
