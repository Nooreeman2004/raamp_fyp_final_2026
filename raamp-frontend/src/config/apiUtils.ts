/**
 * Centralized API URL utilities.
 * Always import from here — never hardcode localhost or base URLs in components.
 */
import { API_BASE_URL } from '@/config/apiBase';

/**
 * The raw backend origin (no /api suffix).
 * e.g. "http://localhost:8000" or "https://api.raamp.com"
 */
export const API_ORIGIN = API_BASE_URL.replace(/\/api\/?$/, '');

/**
 * Build a full URL for a backend media/file path.
 * Handles paths that may or may not start with "/".
 *
 * @example getMediaUrl("/uploads/image.jpg") → "http://localhost:8000/uploads/image.jpg"
 */
export const getMediaUrl = (path: string): string => {
  if (!path) return '';
  // Already absolute URL — return as-is
  if (path.startsWith('http://') || path.startsWith('https://')) return path;
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_ORIGIN}${normalizedPath}`;
};

/**
 * Build a WebSocket URL from the API base URL.
 * Converts http → ws and https → wss automatically.
 *
 * @example getWebSocketUrl("/notifications/ws") → "ws://localhost:8000/api/notifications/ws"
 */
export const getWebSocketUrl = (path: string): string => {
  const wsBase = API_BASE_URL.replace(/^http/, 'ws');
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${wsBase}${normalizedPath}`;
};

/**
 * Build an OAuth redirect URL for social platform auth flows.
 * Uses the backend origin (not the /api prefix).
 *
 * @example getOAuthUrl("/profile/onboarding/facebook/auth") → "http://localhost:8000/profile/onboarding/facebook/auth"
 */
export const getOAuthUrl = (path: string): string => {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_ORIGIN}${normalizedPath}`;
};
