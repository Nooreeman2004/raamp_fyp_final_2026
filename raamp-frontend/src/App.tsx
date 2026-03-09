import { Suspense, lazy } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import ErrorBoundary from "./components/ErrorBoundary";
import ProtectedRoute from "./components/ProtectedRoute";
import ProfileGuard from "./components/ProfileGuard";
import { AuthProvider } from "./hooks/useAuth";
import { NotificationProvider } from "./contexts/NotificationContext";
import { SmoothScroll } from "@/components/ui/smooth-scroll";
import { CustomCursor } from "@/components/ui/custom-cursor";
import { CommandMenu } from "@/components/ui/command-menu";
import { LoadingSpinner } from "@/components/ui/loading-spinner";

// Lazy Loaded Pages
const Index = lazy(() => import("./pages/Index"));
const Login = lazy(() => import("./pages/Login"));
const Signup = lazy(() => import("./pages/Signup"));
const ForgotPassword = lazy(() => import("./pages/ForgotPassword"));
const EmailVerification = lazy(() => import("./pages/EmailVerification"));
const ResetPassword = lazy(() => import("./pages/ResetPassword"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const GeoIntent = lazy(() => import("./pages/GeoIntent"));
const CreativeStudio = lazy(() => import("./pages/CreativeStudio"));
const TrendArbitrage = lazy(() => import("./pages/TrendArbitrage"));
const ABTesting = lazy(() => import("./pages/ABTesting"));
const Performance = lazy(() => import("./pages/Performance"));
const PersonalDetails = lazy(() => import("./pages/PersonalDetails"));
const BusinessSetup = lazy(() => import("./pages/BusinessSetup"));
const BrandSettings = lazy(() => import("./pages/BrandSettings"));
const Onboarding = lazy(() => import("./pages/Onboarding"));
const UserProfile = lazy(() => import("./pages/UserProfile"));
const RestaurantProfile = lazy(() => import("./pages/RestaurantProfile"));
const Billing = lazy(() => import("./pages/Billing"));
const AddFunds = lazy(() => import("./pages/AddFunds"));
const Transactions = lazy(() => import("./pages/Transactions"));
const TermsAndConditions = lazy(() => import("./pages/TermsAndConditions"));
const PrivacyPolicy = lazy(() => import("./pages/PrivacyPolicy"));
const About = lazy(() => import("./pages/About"));
const Resources = lazy(() => import("./pages/Resources"));
const Legal = lazy(() => import("./pages/Legal"));
const NotFound = lazy(() => import("./pages/NotFound"));
const Settings = lazy(() => import("./pages/Settings"));
const NotificationPreferences = lazy(() => import("./pages/NotificationPreferences"));
const AccountSecurity = lazy(() => import("./pages/AccountSecurity"));
const BusinessSpecialties = lazy(() => import("./pages/BusinessSpecialties"));
const Notifications = lazy(() => import("./pages/Notifications"));
const LusionDemo = lazy(() => import("./pages/LusionDemo"));
const RAAMPAssistant = lazy(() => import("./pages/RAAMPAssistant"));
const SmartScheduling = lazy(() => import("./pages/SmartScheduling"));
const AssetLibrary = lazy(() => import("./pages/AssetLibrary"));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});


const App = () => (
  <BrowserRouter>
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <NotificationProvider>
            <TooltipProvider>
              <SmoothScroll>
                <div className="noise-overlay" />
                <CustomCursor />
                <CommandMenu />
                <Toaster />
                <Sonner />
                <Suspense fallback={<LoadingSpinner />}>
                  <Routes>
                    {/* Public Routes */}
                    <Route path="/" element={<Index />} />
                    <Route path="/login" element={<Login />} />
                    <Route path="/signup" element={<Signup />} />
                    <Route path="/forgot-password" element={<ForgotPassword />} />
                    <Route path="/verify-email" element={<EmailVerification />} />
                    <Route path="/reset-password/:token" element={<ResetPassword />} />
                    <Route path="/terms" element={<TermsAndConditions />} />
                    <Route path="/privacy" element={<PrivacyPolicy />} />
                    <Route path="/about" element={<About />} />
                    <Route path="/resources" element={<Resources />} />
                    <Route path="/legal" element={<Legal />} />
                    <Route path="/lusion-demo" element={<LusionDemo />} />
                    <Route path="/pricing" element={<Navigate to="/#pricing" replace />} />

                    {/* Protected Routes - Dashboard & Modules (Require Profile Completion) */}
                    <Route
                      path="/dashboard"
                      element={
                        <ProtectedRoute>
                          <ProfileGuard>
                            <Dashboard />
                          </ProfileGuard>
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/dashboard/assistant"
                      element={
                        <ProtectedRoute>
                          <ProfileGuard>
                            <RAAMPAssistant />
                          </ProfileGuard>
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/dashboard/geo-intent"
                      element={
                        <ProtectedRoute>
                          <ProfileGuard>
                            <GeoIntent />
                          </ProfileGuard>
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/dashboard/creative"
                      element={
                        <ProtectedRoute>
                          <ProfileGuard>
                            <CreativeStudio />
                          </ProfileGuard>
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/dashboard/trends"
                      element={
                        <ProtectedRoute>
                          <ProfileGuard>
                            <TrendArbitrage />
                          </ProfileGuard>
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/dashboard/ab-testing"
                      element={
                        <ProtectedRoute>
                          <ProfileGuard>
                            <ABTesting />
                          </ProfileGuard>
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/dashboard/performance"
                      element={
                        <ProtectedRoute>
                          <ProfileGuard>
                            <Performance />
                          </ProfileGuard>
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/dashboard/smart-scheduling"
                      element={
                        <ProtectedRoute>
                          <ProfileGuard>
                            <SmartScheduling />
                          </ProfileGuard>
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/dashboard/assets"
                      element={
                        <ProtectedRoute>
                          <ProfileGuard>
                            <AssetLibrary />
                          </ProfileGuard>
                        </ProtectedRoute>
                      }
                    />

                    {/* Protected Routes - Profile */}
                    <Route
                      path="/profile/user"
                      element={
                        <ProtectedRoute>
                          <UserProfile />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/profile/restaurant"
                      element={
                        <ProtectedRoute>
                          <RestaurantProfile />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/profile/personal-details"
                      element={
                        <ProtectedRoute requireProfile={false}>
                          <PersonalDetails />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/profile/onboarding"
                      element={
                        <ProtectedRoute>
                          <Onboarding />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/profile/business-setup"
                      element={
                        <ProtectedRoute>
                          <BusinessSetup />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/profile/brand-settings"
                      element={
                        <ProtectedRoute>
                          <BrandSettings />
                        </ProtectedRoute>
                      }
                    />

                    {/* Protected Routes - Billing */}
                    <Route
                      path="/billing"
                      element={
                        <ProtectedRoute>
                          <ProfileGuard>
                            <Billing />
                          </ProfileGuard>
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/billing/add-funds"
                      element={
                        <ProtectedRoute>
                          <ProfileGuard>
                            <AddFunds />
                          </ProfileGuard>
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/billing/transactions"
                      element={
                        <ProtectedRoute>
                          <ProfileGuard>
                            <Transactions />
                          </ProfileGuard>
                        </ProtectedRoute>
                      }
                    />

                    {/* Protected Routes - Settings */}
                    <Route
                      path="/settings"
                      element={
                        <ProtectedRoute>
                          <ProfileGuard>
                            <Settings />
                          </ProfileGuard>
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/notifications"
                      element={
                        <ProtectedRoute>
                          <ProfileGuard>
                            <Notifications />
                          </ProfileGuard>
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/settings/notifications"
                      element={
                        <ProtectedRoute>
                          <ProfileGuard>
                            <NotificationPreferences />
                          </ProfileGuard>
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/settings/security"
                      element={
                        <ProtectedRoute>
                          <ProfileGuard>
                            <AccountSecurity />
                          </ProfileGuard>
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/settings/business-specialties"
                      element={
                        <ProtectedRoute>
                          <ProfileGuard>
                            <BusinessSpecialties />
                          </ProfileGuard>
                        </ProtectedRoute>
                      }
                    />
                    {/* 404 - Must be last */}
                    <Route path="*" element={<NotFound />} />
                  </Routes>
                </Suspense>
              </SmoothScroll>
            </TooltipProvider>
          </NotificationProvider>
        </AuthProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  </BrowserRouter>
);

export default App;
