import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
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
import ProfileHub from "./pages/ProfileHub";
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
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Index />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/verify-email" element={<EmailVerification />} />
          <Route path="/reset-password/:token" element={<ResetPassword />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/dashboard/geo-intent" element={<GeoIntent />} />
          <Route path="/dashboard/creative" element={<CreativeStudio />} />
          <Route path="/dashboard/trends" element={<TrendArbitrage />} />
          <Route path="/dashboard/ab-testing" element={<ABTesting />} />
          <Route path="/dashboard/performance" element={<Performance />} />
          <Route path="/dashboard/assistant" element={<RAAMPAssistant />} />
          <Route path="/profile" element={<ProfileHub />} />
          <Route path="/profile/user" element={<UserProfile />} />
          <Route path="/profile/restaurant" element={<RestaurantProfile />} />
          <Route path="/profile/personal-details" element={<PersonalDetails />} />
          <Route path="/profile/onboarding" element={<Onboarding />} />
          <Route path="/profile/business-setup" element={<BusinessSetup />} />
          <Route path="/profile/brand-settings" element={<BrandSettings />} />
          <Route path="/billing" element={<Billing />} />
          <Route path="/billing/add-funds" element={<AddFunds />} />
          <Route path="/billing/transactions" element={<Transactions />} />
          <Route path="/terms" element={<TermsAndConditions />} />
          <Route path="/privacy" element={<PrivacyPolicy />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
