/**
 * Profile completion guard component
 * Redirects users to profile setup if their profile is incomplete
 */

import { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { User, AlertCircle } from "lucide-react";
import { Link } from "react-router-dom";

interface ProfileGuardProps {
  children: ReactNode;
  allowIncomplete?: boolean; // If true, shows warning but doesn't block
}

export default function ProfileGuard({ children, allowIncomplete = false }: ProfileGuardProps) {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  // Don't guard profile-related pages
  const isProfilePage = 
    location.pathname.startsWith('/profile/') || 
    location.pathname === '/profile' ||
    location.pathname === '/onboarding';

  if (isLoading) {
    return null; // ProtectedRoute handles loading state
  }

  // If profile is incomplete and not on a profile page
  if (user && !user.profile_completed && !isProfilePage) {
    if (allowIncomplete) {
      // Show warning banner but allow access
      return (
        <>
          <Alert className="mb-4 border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20">
            <AlertCircle className="h-4 w-4 text-yellow-600" />
            <AlertDescription className="text-yellow-800 dark:text-yellow-200">
              <div className="flex items-center justify-between">
                <span>Please complete your profile to access all features.</span>
                <Link to="/profile/personal-details">
                  <Button variant="outline" size="sm" className="ml-4">
                    <User className="w-4 h-4 mr-2" />
                    Complete Profile
                  </Button>
                </Link>
              </div>
            </AlertDescription>
          </Alert>
          {children}
        </>
      );
    }

    // Force redirect to profile completion
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-card to-background p-4">
        <Card className="w-full max-w-md p-8 card-shadow bg-card/80 backdrop-blur-sm border-primary/20">
          <div className="text-center space-y-6">
            <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
              <User className="w-8 h-8 text-primary" />
            </div>
            
            <div className="space-y-2">
              <h2 className="text-2xl font-bold">Complete Your Profile</h2>
              <p className="text-muted-foreground">
                Before accessing RAAMP features, please complete your profile setup. 
                This helps us personalize your experience and optimize your campaigns.
              </p>
            </div>

            <div className="space-y-3">
              <Link to="/profile/personal-details" className="block">
                <Button className="w-full" size="lg">
                  <User className="w-4 h-4 mr-2" />
                  Complete Profile Now
                </Button>
              </Link>
              
              <Link to="/logout">
                <Button variant="ghost" className="w-full">
                  Logout
                </Button>
              </Link>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  return <>{children}</>;
}
