import { API_BASE_URL } from '@/config/apiBase';

function decodeJwtPayload(token: string): { exp?: number } | null {
  try {
    const parts = token.split('.');
    if (parts.length < 2) return null;
    let b64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    const pad = b64.length % 4;
    if (pad) b64 += '='.repeat(4 - pad);
    return JSON.parse(atob(b64)) as { exp?: number };
  } catch {
    return null;
  }
}

/** JWT `exp` claim in milliseconds, or null if missing/invalid. */
export function getAccessTokenExpiryMs(token: string | null): number | null {
  if (!token) return null;
  const payload = decodeJwtPayload(token);
  if (!payload || typeof payload.exp !== 'number') return null;
  return payload.exp * 1000;
}

let refreshInFlight: Promise<string | null> | null = null;

/**
 * Exchange a still-valid access token for a new one. Uses fetch (not apiClient) to avoid recursion.
 * Updates localStorage `token` and `user` when successful.
 */
export async function refreshAccessToken(): Promise<string | null> {
  if (refreshInFlight) {
    return refreshInFlight;
  }
  const token = localStorage.getItem('token');
  if (!token) {
    return null;
  }
  refreshInFlight = (async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        credentials: 'include',
      });
      if (!response.ok) {
        return null;
      }
      const data = (await response.json()) as { token?: string; user?: unknown };
      if (data.token) {
        localStorage.setItem('token', data.token);
        if (data.user) {
          try {
            localStorage.setItem('user', JSON.stringify(data.user));
          } catch {
            /* ignore quota */
          }
        }
        window.dispatchEvent(new CustomEvent('raamp-token-refreshed'));
        return data.token;
      }
      return null;
    } catch {
      return null;
    } finally {
      refreshInFlight = null;
    }
  })();
  return refreshInFlight;
}

/** True if the token exists and expires within `withinMs` (and is not already expired). */
export function shouldProactivelyRefresh(token: string | null, withinMs: number): boolean {
  const exp = getAccessTokenExpiryMs(token);
  if (!exp) return false;
  const ttl = exp - Date.now();
  return ttl > 0 && ttl < withinMs;
}
