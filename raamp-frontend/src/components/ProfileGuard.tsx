import { ReactNode } from "react";
import { useLocation } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { useOnboardingStatus } from "@/hooks/useOnboardingStatus";
import OnboardingGating from "./OnboardingGating";

interface ProfileGuardProps {
  children: ReactNode;
}

export default function ProfileGuard({ children }: ProfileGuardProps) {
  const { isLoading: authLoading, user } = useAuth();
  const { isFullyOnboarded, nextStep, steps, isLoading: statusLoading } = useOnboardingStatus();
  const location = useLocation();

  if (authLoading || (statusLoading && !user)) {
    return null; // Or a loading spinner
  }

  // 1. If already completed (via API or Cache), allow everything immediately
  if (isFullyOnboarded) {
    return <>{children}</>;
  }

  // 2. Allow access to the onboarding steps themselves regardless of completion status
  // This prevents the back button from getting stuck if we navigate between steps.
  const currentPath = location.pathname;
  const isOnboardingRoute = steps.some(step => currentPath === step.route);

  if (isOnboardingRoute) {
    return <>{children}</>;
  }

  // 3. For any other "Protected" route (like /dashboard or /settings), 
  // show the gating UI if not onboarded.
  return <OnboardingGating steps={steps} nextStep={nextStep} />;
}
