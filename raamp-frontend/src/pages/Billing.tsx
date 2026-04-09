import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CreditCard, DollarSign, Zap, Calendar, AlertTriangle, Loader2, Settings, FileText } from "lucide-react";
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
}

const getTierColor = (tier: string) => {
  switch (tier?.toLowerCase()) {
    case "pro": return "bg-teal-500";
    case "premium": return "bg-purple-600";
    default: return "bg-zinc-500";
  }
};

const formatDate = (dateStr: string | null | undefined) => {
  if (!dateStr) return "N/A";
  return new Date(dateStr).toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });
};

const Billing = () => {
  const { user } = useAuth();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [showPasswordGate, setShowPasswordGate] = useState(false);
  const [planLoading, setPlanLoading] = useState<string | null>(null);

  useEffect(() => {
    const fetchProfile = async () => {
      if (!user) { setLoading(false); return; }
      try {
        const data = await apiClient.get<any>("/auth/profile");
        setProfile({
          subscriptionTier: data.subscriptionTier || "free",
          adCreditsRemaining: data.adCreditsRemaining ?? 0,
          subscriptionEndDate: data.subscription?.end_date ?? null,
          email: data.email,
        });
      } catch {
        // Fallback to user object
        const sub = user?.subscription as any;
        setProfile({
          subscriptionTier: sub?.subscriptionTier || "free",
          adCreditsRemaining: sub?.adCreditsRemaining ?? 0,
          email: user?.email,
        });
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, [user]);

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

  const tierOrder: Record<string, number> = { free: 0, pro: 1, premium: 2 };

  const getPlanButtonText = (plan: string): string => {
    const currentOrder = tierOrder[tier] ?? 0;
    const planOrder = tierOrder[plan] ?? 0;
    if (tier === plan) return tier === "free" ? "Current Plan" : "Manage Plan";
    return planOrder > currentOrder
      ? `Upgrade to ${plan.charAt(0).toUpperCase() + plan.slice(1)}`
      : `Downgrade to ${plan.charAt(0).toUpperCase() + plan.slice(1)}`;
  };

  const handlePlanClick = async (plan: string) => {
    // Free user on free plan — no action
    if (tier === "free" && plan === "free") return;

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
      setShowPasswordGate(true);
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
              <h1 className="text-3xl font-bold font-heading font-semibold"><BlurText text="Billing & Subscription" /></h1>
              <p className="text-muted-foreground font-mono text-sm">Manage your plan, credits, and payment methods</p>
            </div>
          </div>
        </Reveal>

        {/* Current Plan Summary */}
        <motion.div variants={fadeInUp}>
          <div className="grid md:grid-cols-2 gap-6">

            {/* Plan Info Card */}
            <HolographicCard className="p-6 border-primary/30">
              <div className="flex items-center gap-3 mb-6">
                <Zap className="w-5 h-5 text-primary" />
                <h2 className="text-lg font-bold font-heading font-semibold text-foreground">CURRENT PLAN</h2>
                <Badge className={`${getTierColor(tier)} text-foreground font-mono text-xs px-3 py-1 uppercase ml-2`}>{tier}</Badge>
              </div>
              <div className="space-y-4">
                <div className="bg-foreground/5 border border-border/50 rounded-lg p-4">
                  <div className="flex items-center gap-3 mb-2"><Calendar className="w-5 h-5 text-muted-foreground" /><span className="font-mono text-sm text-muted-foreground">NEXT BILLING DATE</span></div>
                  <div className="text-lg font-bold text-foreground font-mono pl-8">{tier === "free" ? "—" : formatDate(profile?.subscriptionEndDate)}</div>
                </div>
                <div className="bg-foreground/5 border border-border/50 rounded-lg p-4">
                  <div className="flex items-center gap-3 mb-2"><DollarSign className="w-5 h-5 text-muted-foreground" /><span className="font-mono text-sm text-muted-foreground">AD CREDITS REMAINING</span></div>
                  <div className="text-2xl font-bold text-foreground font-mono pl-8">
                    {profile?.adCreditsRemaining === 999999999 || profile?.adCreditsRemaining === -1 ? "Unlimited" : (profile?.adCreditsRemaining ?? 0)}
                  </div>
                </div>
              </div>
            </HolographicCard>

            {/* Billing Actions Card */}
            <HolographicCard className="p-6">
              <h2 className="text-xl font-bold mb-1 font-heading font-semibold text-foreground">BILLING ACTIONS</h2>
              <p className="text-xs text-muted-foreground mb-6 font-mono">// MANAGE INVOICES AND SUBSCRIPTION SETTINGS</p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                  <Link to="/billing/transactions">
                    <Button variant="hero" className="w-full h-14 font-heading font-semibold text-[13px]">
                      <FileText className="w-4 h-4 mr-2" /> VIEW TRANSACTION HISTORY
                    </Button>
                  </Link>
                </motion.div>

                <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                  <Link to="/billing/add-funds">
                    <Button variant="hero" className="w-full h-14 font-heading font-semibold text-[13px]">
                      <DollarSign className="w-4 h-4 mr-2" /> ADD FUNDS TO WALLET
                    </Button>
                  </Link>
                </motion.div>

                {tier !== "free" && (
                  <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap" className="sm:col-span-2">
                    <Button variant="outline" onClick={() => setShowPasswordGate(true)} className="w-full h-14 border-primary/30 text-foreground hover:bg-primary/10 font-heading font-semibold text-[13px]">
                      <Settings className="w-4 h-4 mr-2" /> MANAGE SUBSCRIPTION
                    </Button>
                  </motion.div>
                )}
              </div>

              <p className="mt-4 text-[10px] text-muted-foreground font-mono text-center">
                Need to update your payment method? It's available in the <strong>Manage Subscription</strong> portal.
              </p>
            </HolographicCard>
          </div>
        </motion.div>

        {/* Available Plans */}
        <Reveal variant="blurInUp">
          <div className="pb-12">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold mb-2 font-heading font-semibold text-foreground">{tier === "free" ? "CHOOSE YOUR PLAN" : "AVAILABLE PLANS"}</h2>
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
                  className={isCurrentPlan("free") ? "border-primary/60 shadow-[0_0_30px_rgba(0,224,208,0.2)]" : ""}
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
                  className={isCurrentPlan("pro") ? "border-primary/60 shadow-[0_0_30px_rgba(0,224,208,0.2)]" : ""}
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
                  className={isCurrentPlan("premium") ? "border-primary/60 shadow-[0_0_30px_rgba(0,224,208,0.2)]" : ""}
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