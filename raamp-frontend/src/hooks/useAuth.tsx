import { useState, useEffect, createContext, useContext, ReactNode } from "react";
import { authService } from "@/services/authService";
import type { UserResponse, AuthContextType } from "@/types";

const AuthContext = createContext<AuthContextType | undefined>(undefined);

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
      // Check localStorage first
      const stored = localStorage.getItem("user");
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          setUser(parsed);
        } catch {
          localStorage.removeItem("user");
        }
      }

      // Verify with backend
      const profile = await authService.getProfile();
      if (profile) {
        setUser(profile);
        try {
          localStorage.setItem("user", JSON.stringify(profile));
        } catch {}
      } else {
        setUser(null);
        localStorage.removeItem("user");
      }
    } catch (error: unknown) {
      const apiError = error as { status?: number };
      if (apiError?.status === 401 || apiError?.status === 403) {
        setUser(null);
        localStorage.removeItem("user");
      }
      // For other errors, keep existing user from localStorage if available
    } finally {
      setIsLoading(false);
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
    }
  };

  useEffect(() => {
    loadUser();
  }, []);

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    refreshUser,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

