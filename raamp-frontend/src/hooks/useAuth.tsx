import { useState, useEffect, useCallback, createContext, useContext, ReactNode } from "react";
import { authService } from "@/services/authService";
import { refreshAccessToken, shouldProactivelyRefresh } from "@/services/tokenRefresh";
import type { UserResponse, AuthContextType } from "@/types";

interface ExtendedAuthContextType extends AuthContextType {
  login: (userData: UserResponse, remember: boolean) => void;
}

const AuthContext = createContext<ExtendedAuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [sessionUncertain, setSessionUncertain] = useState(false);

  const dismissSessionWarning = useCallback(() => setSessionUncertain(false), []);
  const reportSessionUncertain = useCallback(() => setSessionUncertain(true), []);

  const loadUser = useCallback(async () => {
    try {
      // Check storage (Local first, then Session)
      const stored = localStorage.getItem("user") || sessionStorage.getItem("user");

      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          setUser(parsed);
        } catch {
          localStorage.removeItem("user");
          sessionStorage.removeItem("user");
        }
      }

      // Only verify with backend if we have a stored user or token
      // This prevents unnecessary API calls on initial load when not logged in
      const hasToken = localStorage.getItem("token") || sessionStorage.getItem("token");
      if (!stored && !hasToken) {
        setIsLoading(false);
        return;
      }

      // Verify with backend if we have a token (usually handled by cookies/interceptor)
      // But we call getProfile to ensure user data is fresh
      const profile = await authService.getProfile();
      if (profile) {
        setUser(profile);
        setSessionUncertain(false);
        // Update the storage that was already in use
        if (localStorage.getItem("user")) {
          localStorage.setItem("user", JSON.stringify(profile));
        } else if (sessionStorage.getItem("user")) {
          sessionStorage.setItem("user", JSON.stringify(profile));
        }
      } else {
        // If backend says no user, clear everything
        setUser(null);
        setSessionUncertain(false);
        localStorage.removeItem("user");
        sessionStorage.removeItem("user");
      }
    } catch (error: unknown) {
      const apiError = error as { status?: number };
      if (apiError?.status === 401 || apiError?.status === 403) {
        setUser(null);
        setSessionUncertain(false);
        localStorage.removeItem("user");
        localStorage.removeItem("token");
        sessionStorage.removeItem("user");
      } else {
        // Network / 5xx / timeout: keep cached user but warn — actions may fail until server is reachable
        if (localStorage.getItem("user") || sessionStorage.getItem("user")) {
          setSessionUncertain(true);
        }
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  const login = (userData: UserResponse, remember: boolean) => {
    setUser(userData);
    setSessionUncertain(false);
    if (remember) {
      localStorage.setItem("user", JSON.stringify(userData));
      sessionStorage.removeItem("user");
    } else {
      sessionStorage.setItem("user", JSON.stringify(userData));
      localStorage.removeItem("user");
    }
  };

  const refreshUser = useCallback(async () => {
    await loadUser();
  }, [loadUser]);

  const logout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      setUser(null);
      setSessionUncertain(false);
      localStorage.removeItem("user");
      localStorage.removeItem("token");
      sessionStorage.removeItem("user");
    }
  };

  useEffect(() => {
    void loadUser();
  }, [loadUser]);

  // Keep React state in sync when apiClient/tokenRefresh rotates the JWT outside of login()
  useEffect(() => {
    const onTokenRefreshed = () => {
      void loadUser();
    };
    window.addEventListener("raamp-token-refreshed", onTokenRefreshed);
    return () => window.removeEventListener("raamp-token-refreshed", onTokenRefreshed);
  }, [loadUser]);

  // Proactive rotation before access token expires (requires still-valid token)
  useEffect(() => {
    const WINDOW_MS = 10 * 60 * 1000;
    const tick = () => {
      const token = localStorage.getItem("token") || sessionStorage.getItem("token");
      if (shouldProactivelyRefresh(token, WINDOW_MS)) {
        void refreshAccessToken();
      }
    };
    tick();
    const id = window.setInterval(tick, 2 * 60 * 1000);
    return () => window.clearInterval(id);
  }, []);

  const value: ExtendedAuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    refreshUser,
    logout,
    login,
    sessionUncertain,
    dismissSessionWarning,
    reportSessionUncertain,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
