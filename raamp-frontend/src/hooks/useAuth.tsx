import { useState, useEffect, createContext, useContext, ReactNode } from "react";
import { authService } from "@/services/authService";
import type { UserResponse, AuthContextType } from "@/types";

interface ExtendedAuthContextType extends AuthContextType {
  login: (user: UserResponse, remember: boolean) => void;
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

  const loadUser = async () => {
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

      // Verify with backend if we have a token (usually handled by cookies/interceptor)
      // But we call getProfile to ensure user data is fresh
      const profile = await authService.getProfile();
      if (profile) {
        setUser(profile);
        // Update the storage that was already in use
        if (localStorage.getItem("user")) {
          localStorage.setItem("user", JSON.stringify(profile));
        } else if (sessionStorage.getItem("user")) {
          sessionStorage.setItem("user", JSON.stringify(profile));
        }
      } else {
        // If backend says no user, clear everything
        setUser(null);
        localStorage.removeItem("user");
        sessionStorage.removeItem("user");
      }
    } catch (error: unknown) {
      const apiError = error as { status?: number };
      if (apiError?.status === 401 || apiError?.status === 403) {
        setUser(null);
        localStorage.removeItem("user");
        localStorage.removeItem("token");
        sessionStorage.removeItem("user");
      }
      // For other errors, keep existing user from storage if available
    } finally {
      setIsLoading(false);
    }
  };

  const login = (userData: UserResponse, remember: boolean) => {
    setUser(userData);
    if (remember) {
      localStorage.setItem("user", JSON.stringify(userData));
      sessionStorage.removeItem("user");
    } else {
      sessionStorage.setItem("user", JSON.stringify(userData));
      localStorage.removeItem("user");
    }
  };

  const refreshUser = async () => {
    await loadUser();
  };

  const logout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      setUser(null);
      localStorage.removeItem("user");
      localStorage.removeItem("token");
      sessionStorage.removeItem("user");
    }
  };

  useEffect(() => {
    loadUser();
  }, []);

  const value: ExtendedAuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    refreshUser,
    logout,
    login,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

