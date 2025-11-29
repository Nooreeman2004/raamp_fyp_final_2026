import { ReactNode, useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { authService } from "@/services/authService";
import { Skeleton } from "@/components/ui/skeleton";
import { Card } from "@/components/ui/card";
import type { UserResponse } from "@/types";

interface ProtectedRouteProps {
  children: ReactNode;
  requireProfile?: boolean; // If true, redirects to profile setup if profile incomplete
}

const ProtectedRoute = ({ children, requireProfile = false }: ProtectedRouteProps) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<UserResponse | null>(null);
  const location = useLocation();

  useEffect(() => {
    const checkAuth = async () => {
      try {
        // Check localStorage first for quick initial render
        const stored = localStorage.getItem("user");
        if (stored) {
          try {
            const parsed = JSON.parse(stored);
            setUser(parsed);
            setIsAuthenticated(true);
          } catch {
            localStorage.removeItem("user");
          }
        }

        // Verify with backend
        try {
          const profile = await authService.getProfile();
          if (profile) {
            setUser(profile);
            setIsAuthenticated(true);
            try {
              localStorage.setItem("user", JSON.stringify(profile));
            } catch {}
          } else {
            setIsAuthenticated(false);
          }
        } catch (error: unknown) {
          const apiError = error as { status?: number };
          // If 401/403, user is not authenticated
          if (apiError?.status === 401 || apiError?.status === 403) {
            setIsAuthenticated(false);
            localStorage.removeItem("user");
          } else {
            // Network error or other issue - allow access but log error
            console.error("Auth check failed:", error);
            // For network errors, we'll allow access if localStorage has user data
            setIsAuthenticated(stored ? true : false);
          }
        }
      } catch (error: unknown) {
        console.error("Auth check error:", error);
        setIsAuthenticated(false);
        localStorage.removeItem("user");
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-card to-background">
        <Card className="w-full max-w-md p-8 card-shadow bg-card/80 backdrop-blur-sm border-primary/20">
          <div className="space-y-4">
            <div className="flex justify-center">
              <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
            </div>
            <div className="space-y-2 text-center">
              <Skeleton className="h-4 w-32 mx-auto" />
              <Skeleton className="h-3 w-48 mx-auto" />
            </div>
          </div>
        </Card>
      </div>
    );
  }

  if (!isAuthenticated) {
    // Redirect to login with return URL
    return (
      <Navigate
        to="/login"
        state={{ from: location.pathname }}
        replace
      />
    );
  }

  // If profile is required but not completed, redirect to profile setup
  // Note: ProfileGuard component should be used for enforcing profile completion
  if (requireProfile && user && !user.profile_completed) {
    // Allow access to profile pages
    const isProfilePage = 
      location.pathname.startsWith('/profile/') || 
      location.pathname === '/profile' ||
      location.pathname === '/onboarding';
    
    if (!isProfilePage) {
      return <Navigate to="/profile/personal-details" replace />;
    }
  }

  return <>{children}</>;
};

export default ProtectedRoute;

