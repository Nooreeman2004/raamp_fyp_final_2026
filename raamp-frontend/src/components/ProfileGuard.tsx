import { ReactNode } from "react";
import { useLocation } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { useOnboardingStatus } from "@/hooks/useOnboardingStatus";
import OnboardingGating from "./OnboardingGating";

interface ProfileGuardProps {
  children: ReactNode;
}

export default function ProfileGuard({ children }: ProfileGuardProps) {
  const { isLoading: authLoading } = useAuth();
  const { isFullyOnboarded, nextStep, steps, isLoading: statusLoading } = useOnboardingStatus();
  const location = useLocation();

  if (authLoading || statusLoading) {
    return null; // Or a loading spinner
  }

  // If fully onboarded, allow everything
  if (isFullyOnboarded) {
    return <>{children}</>;
  }

  // --- Strict Onboarding Gating Logic ---

  // Allow access to the onboarding steps themselves regardless of completion status
  // (though usually nextStep logic handles the flow, we shouldn't block these routes if they are in ProfileGuard)
  const currentPath = location.pathname;
  const isOnboardingRoute = steps.some(step => currentPath === step.route);

  if (isOnboardingRoute) {
    return <>{children}</>;
  }

  // For any other "Protected" route (like /dashboard), if not fully onboarded,
  // show the intentional gating UI instead of a silent redirect.
  return <OnboardingGating steps={steps} nextStep={nextStep} />;
}
