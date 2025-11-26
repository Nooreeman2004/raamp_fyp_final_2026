// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

// API Client
class ApiClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
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
    const timeoutMs = Number(import.meta.env.VITE_API_TIMEOUT) || 10000;

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
        throw {
          status: response.status,
          message: isJson ? data.message : data,
          ...(isJson ? data : {}),
        };
      }

      return data;
    } catch (error: any) {
      clearTimeout(id);
      console.error('API Error:', error);

      // Handle aborted requests (timeout)
      if (error instanceof DOMException && error.name === 'AbortError') {
        throw {
          status: 0,
          message: `Request timed out after ${timeoutMs}ms. Please check your network or backend server.`,
          errors: { timeout: 'request aborted' },
        };
      }

      // Handle network errors (failed to fetch)
      if (error instanceof TypeError && error.message === 'Failed to fetch') {
        throw {
          status: 0,
          message: 'Unable to connect to server. Please check if the backend is running.',
          errors: { network: 'Failed to fetch' }
        };
      }

      throw error;
    }
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async put<T>(endpoint: string, data: any): Promise<T> {
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
