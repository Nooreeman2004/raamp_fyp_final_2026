import { isRetryableError, getRetryDelay } from '@/utils/errorHandler';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

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
    
    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      credentials: 'include', // Include cookies for CORS
    };

    // Allow configuring timeout via Vite env var VITE_API_TIMEOUT (ms)
    // Use longer timeout for signup/auth endpoints that send emails
    const isAuthEndpoint = endpoint.includes('/auth/signup') || endpoint.includes('/auth/verify');
    const defaultTimeout = isAuthEndpoint ? 30000 : 10000; // 30s for auth, 10s for others
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

      if (!response.ok) {
        const error = {
          status: response.status,
          message: isJson ? data.message : data,
          ...(isJson ? data : {}),
        };

        // Retry on retryable errors
        if (isRetryableError(error) && retryAttempt < this.maxRetries) {
          const delay = getRetryDelay(retryAttempt);
          await new Promise(resolve => setTimeout(resolve, delay));
          return this.request<T>(endpoint, options, retryAttempt + 1);
        }

        throw error;
      }

      return data;
    } catch (error: any) {
      clearTimeout(id);
      console.error('API Error:', error);

      // Handle aborted requests (timeout)
      if (error instanceof DOMException && error.name === 'AbortError') {
        const timeoutError = {
          status: 0,
          message: `Request timed out after ${timeoutMs}ms. Please check your network or backend server.`,
          errors: { timeout: 'request aborted' },
        };

        // Retry on timeout if we haven't exceeded max retries
        if (retryAttempt < this.maxRetries) {
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
          message: 'Unable to connect to server. Please check if the backend is running.',
          errors: { network: 'Failed to fetch' }
        };

        // Retry on network errors if we haven't exceeded max retries
        if (retryAttempt < this.maxRetries) {
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
}

export const apiClient = new ApiClient(API_BASE_URL);
