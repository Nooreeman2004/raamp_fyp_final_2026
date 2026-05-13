import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CreditCard, DollarSign, Zap, Calendar, AlertTriangle, Loader2, Settings } from "lucide-react";
import { HolographicCard } from "@/components/ui/holographic-card";
import { PricingCard3D } from "@/components/ui/pricing-card-3d";
import Layout from "@/components/Layout";
import { useAuth } from "@/hooks/useAuth";
import { apiClient } from "@/services/api";
import { toast } from "sonner";
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeInUp, hoverScale } from "@/utils/animations";
import { BlurText } from "@/components/ui/text-reveal";
import { PasswordVerificationDialog } from "@/components/PasswordVerificationDialog";

interface UserProfile {
  subscriptionTier: string;
  adCreditsRemaining: number;
  subscriptionEndDate?: string | null;
  email?: string;
  stripeCustomerId?: string | null;
}

const getTierColor = (tier: string) => {
  switch (tier?.toLowerCase()) {
    case "pro": return "bg-blue-500";
    case "premium": return "bg-primary";
    default: return "bg-zinc-500";
  }
};

const formatDate = (dateStr: string | null | undefined) => {
  if (!dateStr) return "N/A";
  return new Date(dateStr).toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });
};

const Billing = () => {
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [showPasswordGate, setShowPasswordGate] = useState(false);
  const [planLoading, setPlanLoading] = useState<string | null>(null);

  const fetchProfile = useCallback(async () => {
    if (!user) { setLoading(false); return; }
    try {
      const data = await apiClient.get<any>("/auth/profile");
      setProfile({
        subscriptionTier: data.subscriptionTier || data.subscription?.type || "free",
        adCreditsRemaining: data.adCreditsRemaining ?? data.subscription?.credits ?? 5,
        subscriptionEndDate: data.subscription?.end_date ?? null,
        email: data.email,
        stripeCustomerId: data.stripeCustomerId,
      });
    } catch {
      const sub = user?.subscription as any;
      setProfile({
        subscriptionTier: sub?.type || "free",
        adCreditsRemaining: sub?.credits ?? 5,
        email: user?.email,
        stripeCustomerId: null,
      });
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  useEffect(() => {
    if (searchParams.get("success") === "true") {
      toast.success("Subscription activated!", {
        description: "Your plan has been updated. Welcome to your new tier!",
      });
      setSearchParams({}, { replace: true });
      // Re-fetch after a short delay so Stripe webhook has time to update the DB
      setTimeout(() => fetchProfile(), 1500);
    } else if (searchParams.get("funds_added") === "true") {
      const amount = searchParams.get("amount");
      toast.success("Credits added!", {
        description: amount ? `$${amount} in ad credits have been added to your account.` : "Your ad credits have been updated.",
      });
      setSearchParams({}, { replace: true });
      setTimeout(() => fetchProfile(), 1500);
    } else if (searchParams.get("canceled") === "true") {
      toast.info("Checkout canceled.", { description: "No changes were made to your subscription." });
      setSearchParams({}, { replace: true });
    }
  }, [searchParams]);

  const handlePortalVerify = async () => {
    try {
      const res = await apiClient.post<{ url: string }>("/stripe/create-portal-session", {});
      if (res.url) { window.location.href = res.url; }
      else { toast.error("Could not open Stripe portal"); }
      setShowPasswordGate(false);
    } catch {
      toast.error("Could not open portal. Please try again.");
    }
  };

  const handleManageClick = () => {
    if (!profile?.stripeCustomerId) {
      toast.error("Cannot manage subscription. Please contact support.");
      return;
    }
    setShowPasswordGate(true);
  };

  const tierOrder: Record<string, number> = { free: 0, pro: 1, premium: 2 };

  const getPlanButtonText = (plan: string): string => {
    const currentOrder = tierOrder[tier] ?? 0;
    const planOrder = tierOrder[plan] ?? 0;
    if (tier === plan) {
      if (tier === "free") return "Current Plan";
      return profile?.stripeCustomerId ? "Manage Plan" : "Current Plan";
    }
    return planOrder > currentOrder
      ? `Upgrade to ${plan.charAt(0).toUpperCase() + plan.slice(1)}`
      : `Downgrade to ${plan.charAt(0).toUpperCase() + plan.slice(1)}`;
  };

  const handlePlanClick = async (plan: string) => {
    // Free user on free plan — no action
    if (tier === "free" && plan === "free") return;

    // Current plan without Stripe customer ID — no action
    if (tier === plan && !profile?.stripeCustomerId) return;

    if (tier === "free") {
      // No Stripe customer yet — start a new checkout session
      setPlanLoading(plan);
      try {
        const res = await apiClient.post<{ url: string }>("/stripe/create-checkout-session", { plan });
        if (res.url) { window.location.href = res.url; }
        else { toast.error("Could not start checkout. Please try again."); }
      } catch {
        toast.error("Failed to start checkout. Please try again.");
      } finally {
        setPlanLoading(null);
      }
    } else {
      // Existing subscriber — Stripe Portal handles upgrades, downgrades & cancellations
      if (profile?.stripeCustomerId) {
        setShowPasswordGate(true);
      } else {
        toast.error("Cannot manage subscription. Please contact support.");
      }
    }
  };

  const isCurrentPlan = (plan: string) =>
    (profile?.subscriptionTier || "free").toLowerCase() === plan;

  if (loading) {
    return (
      <Layout breadcrumbItems={[{ label: "Dashboard", href: "/dashboard" }, { label: "Billing & Subscription" }]}>
        <div className="flex items-center justify-center min-h-[50vh]">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      </Layout>
    );
  }

  const tier = (profile?.subscriptionTier || "free").toLowerCase();

  return (
    <Layout breadcrumbItems={[{ label: "Dashboard", href: "/dashboard" }, { label: "Billing & Subscription" }]}>
      <motion.div className="space-y-10 max-w-6xl mx-auto" variants={staggerContainer} initial="hidden" animate="visible">

        {/* Header */}
        <Reveal variant="blurInUp">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center">
              <CreditCard className="w-7 h-7 text-primary" />
            </div>
            <div>
              <h1 className="text-3xl font-bold font-bebas tracking-wide"><BlurText text="Billing & Subscription" /></h1>
              <p className="text-primary/80 font-mono text-sm font-medium">Manage your plan, credits, and payment methods</p>
            </div>
          </div>
        </Reveal>

        {/* Current Plan Summary */}
        <motion.div variants={fadeInUp}>
          <div className="grid md:grid-cols-2 gap-6">

            {/* Plan Info Card */}
            <HolographicCard className="p-6 border-primary/30">
              <motion.div 
                className="flex items-center gap-3 mb-6"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
              >
                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                  <Zap className="w-5 h-5 text-primary" />
                </div>
                <h2 className="text-lg font-bold font-bebas tracking-wide text-foreground">CURRENT PLAN</h2>
                <Badge className={`${getTierColor(tier)} text-black font-mono text-xs px-3 py-1 uppercase ml-2 font-bold`}>{tier}</Badge>
              </motion.div>
              <div className="space-y-4">
                <motion.div 
                  className="bg-gradient-to-br from-primary/5 to-primary/10 border border-primary/30 rounded-lg p-4 hover:border-primary/50 transition-all"
                  whileHover={{ scale: 1.02 }}
                  transition={{ type: "spring", stiffness: 300 }}
                >
                  <div className="flex items-center gap-3 mb-2">
                    <Calendar className="w-5 h-5 text-primary" />
                    <span className="font-mono text-sm text-primary font-semibold">NEXT BILLING DATE</span>
                  </div>
                  <div className="text-lg font-bold text-foreground font-mono pl-8">{tier === "free" ? "—" : formatDate(profile?.subscriptionEndDate)}</div>
                </motion.div>
                <motion.div 
                  className="bg-gradient-to-br from-primary/5 to-primary/10 border border-primary/30 rounded-lg p-4 hover:border-primary/50 transition-all"
                  whileHover={{ scale: 1.02 }}
                  transition={{ type: "spring", stiffness: 300 }}
                >
                  <div className="flex items-center gap-3 mb-2">
                    <DollarSign className="w-5 h-5 text-primary" />
                    <span className="font-mono text-sm text-primary font-semibold">AD CREDITS REMAINING</span>
                  </div>
                  <div className="text-2xl font-bold text-primary font-mono pl-8">
                    {profile?.adCreditsRemaining === 999999999 || profile?.adCreditsRemaining === -1 ? "Unlimited" : (profile?.adCreditsRemaining ?? 0)}
                  </div>
                </motion.div>
              </div>
              {tier !== "free" && (
                <motion.div 
                  className="mt-6"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 }}
                >
                  <motion.div 
                    whileHover={{ scale: 1.02 }} 
                    whileTap={{ scale: 0.98 }}
                    transition={{ type: "spring", stiffness: 400, damping: 10 }}
                  >
                    <Button 
                      variant="outline" 
                      onClick={handleManageClick} 
                      className="w-full justify-center border-2 border-primary bg-primary/10 text-primary hover:bg-primary hover:text-black font-mono text-sm h-12 font-bold transition-all"
                    >
                      <Settings className="w-5 h-5 mr-2" /> MANAGE SUBSCRIPTION
                    </Button>
                  </motion.div>
                </motion.div>
              )}
            </HolographicCard>

            {/* Payment Method Card */}
            <HolographicCard className="p-6 border-primary/20">
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 }}
              >
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                    <CreditCard className="w-5 h-5 text-primary" />
                  </div>
                  <h2 className="text-xl font-bold font-bebas tracking-wide text-foreground">PAYMENT METHOD</h2>
                </div>
                <p className="text-xs text-muted-foreground mb-6 font-mono pl-13">// PRIMARY SOURCE FOR SUBSCRIPTIONS & AD SPEND</p>
              </motion.div>
              {tier !== "free" ? (
                <motion.div 
                  className="p-5 bg-gradient-to-br from-primary/5 to-primary/10 rounded-lg border border-primary/30 flex flex-col gap-4 hover:border-primary/50 transition-all"
                  whileHover={{ scale: 1.01 }}
                >
                  <div>
                    <span className="text-sm font-mono text-primary block mb-1 font-semibold">Connected via Stripe</span>
                    <span className="text-xs text-muted-foreground font-mono">Your payment methods are securely stored in the Stripe portal. Update your card, download invoices, and manage billing there.</span>
                  </div>
                  <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                    <Button 
                      variant="default" 
                      onClick={handleManageClick} 
                      className="w-full bg-primary hover:bg-primary/90 text-black border-0 font-mono font-bold h-12 transition-all"
                    >
                      <CreditCard className="w-5 h-5 mr-2" /> MANAGE PAYMENT METHODS
                    </Button>
                  </motion.div>
                </motion.div>
              ) : (
                <motion.div 
                  className="p-4 bg-foreground/5 rounded border border-border/50 flex items-center justify-between hover:border-primary/30 transition-colors"
                  whileHover={{ scale: 1.01 }}
                >
                  <div><span className="text-sm font-mono text-foreground block">No Payment Method</span><span className="text-xs text-muted-foreground font-mono">Upgrade to a paid plan to add payment methods</span></div>
                  <AlertTriangle className="w-8 h-8 text-muted-foreground/50" />
                </motion.div>
              )}
            </HolographicCard>
          </div>
        </motion.div>

        {/* Available Plans */}
        <Reveal variant="blurInUp">
          <div className="pb-12">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold mb-2 font-bebas tracking-wide text-foreground">{tier === "free" ? "CHOOSE YOUR PLAN" : "AVAILABLE PLANS"}</h2>
              <p className="text-sm text-muted-foreground font-mono">{tier === "free" ? "// START YOUR JOURNEY WITH THE PERFECT PLAN" : "// UPGRADE OR SWITCH YOUR SUBSCRIPTION"}</p>
            </div>
            <motion.div className="grid md:grid-cols-3 gap-8 pt-12" variants={staggerContainer} initial="hidden" animate="visible">
              {/* Free */}
              <div className="relative">
                <PricingCard3D
                  title="Free"
                  price="$0"
                  features={["Create up to 5 advertisements", "Access basic templates", "Basic AI generation", "Basic analytics", "Standard email support"]}
                  isCurrentPlan={isCurrentPlan("free")}
                  buttonText={planLoading === "free" ? "Loading..." : getPlanButtonText("free")}
                  onClick={tier === "free" ? undefined : () => handlePlanClick("free")}
                  className={isCurrentPlan("free") ? "border-primary/60" : ""}
                />
              </div>

              {/* Pro */}
              <div className="relative">
                <PricingCard3D
                  title="Pro"
                  price="$10"
                  isPopular={true}
                  features={["Up to 50 ads per month", "Premium templates", "Faster AI generation", "Advanced editing tools", "Campaign management", "Advanced analytics dashboard", "Priority email support"]}
                  isCurrentPlan={isCurrentPlan("pro")}
                  buttonText={planLoading === "pro" ? "Loading..." : getPlanButtonText("pro")}
                  onClick={() => handlePlanClick("pro")}
                  className={isCurrentPlan("pro") ? "border-primary/60" : ""}
                />
              </div>

              {/* Premium */}
              <div className="relative">
                <PricingCard3D
                  title="Premium"
                  price="$25"
                  features={["Unlimited advertisements", "Unlimited ad credits", "All templates", "Advanced AI generation", "Campaign performance insights", "Team collaboration", "API access", "24/7 priority support"]}
                  isCurrentPlan={isCurrentPlan("premium")}
                  buttonText={planLoading === "premium" ? "Loading..." : getPlanButtonText("premium")}
                  onClick={() => handlePlanClick("premium")}
                  className={isCurrentPlan("premium") ? "border-primary/60" : ""}
                />
              </div>
            </motion.div>
          </div>
        </Reveal>
      </motion.div>

      {/* Password Gate */}
      <PasswordVerificationDialog
        isOpen={showPasswordGate}
        onClose={() => setShowPasswordGate(false)}
        onVerified={handlePortalVerify}
      />
    </Layout>
  );
};

export default Billing;
