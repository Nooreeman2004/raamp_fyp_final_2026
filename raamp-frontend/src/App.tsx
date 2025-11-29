import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import ErrorBoundary from "./components/ErrorBoundary";
import ProtectedRoute from "./components/ProtectedRoute";
import ProfileGuard from "./components/ProfileGuard";
import { AuthProvider } from "./hooks/useAuth";
import Index from "./pages/Index";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import ForgotPassword from "./pages/ForgotPassword";
import EmailVerification from "./pages/EmailVerification";
import ResetPassword from "./pages/ResetPassword";
import Dashboard from "./pages/Dashboard";
import GeoIntent from "./pages/GeoIntent";
import CreativeStudio from "./pages/CreativeStudio";
import TrendArbitrage from "./pages/TrendArbitrage";
import ABTesting from "./pages/ABTesting";
import Performance from "./pages/Performance";
import RAAMPAssistant from "./pages/RAAMPAssistant";
import PersonalDetails from "./pages/PersonalDetails";
import BusinessSetup from "./pages/BusinessSetup";
import BrandSettings from "./pages/BrandSettings";
import Onboarding from "./pages/Onboarding";
import UserProfile from "./pages/UserProfile";
import RestaurantProfile from "./pages/RestaurantProfile";
import Billing from "./pages/Billing";
import AddFunds from "./pages/AddFunds";
import Transactions from "./pages/Transactions";
import TermsAndConditions from "./pages/TermsAndConditions";
import PrivacyPolicy from "./pages/PrivacyPolicy";
import About from "./pages/About";
import Resources from "./pages/Resources";
import Legal from "./pages/Legal";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});

const App = () => (
  <ErrorBoundary>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <BrowserRouter>
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
                path="/dashboard/assistant"
                element={
                  <ProtectedRoute>
                    <ProfileGuard>
                      <RAAMPAssistant />
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
                    <Billing />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/billing/add-funds"
                element={
                  <ProtectedRoute>
                    <AddFunds />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/billing/transactions"
                element={
                  <ProtectedRoute>
                    <Transactions />
                  </ProtectedRoute>
                }
              />

              {/* 404 - Must be last */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
        </TooltipProvider>
      </AuthProvider>
    </QueryClientProvider>
  </ErrorBoundary>
);

export default App;
