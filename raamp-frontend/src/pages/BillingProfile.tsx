import { useState, useEffect } from "react";
import Layout from "@/components/Layout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { 
  Building2, 
  Mail, 
  Phone, 
  MapPin, 
  Globe, 
  FileText, 
  CreditCard,
  Save,
  Loader2,
  AlertCircle,
  CheckCircle2
} from "lucide-react";
import { apiClient } from "@/services/api";
import { toast } from "sonner";
import { BillingProfileRequest, BillingProfileGetResponse } from "@/types/api.types";
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { fadeInUp, staggerContainer } from "@/utils/animations";
import { BlurText } from "@/components/ui/text-reveal";
import { HolographicCard } from "@/components/ui/holographic-card";

const BillingProfile = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState<BillingProfileRequest>({
    full_name: "",
    company_name: "",
    email: "",
    phone: "",
    address_line1: "",
    address_line2: "",
    city: "",
    state: "",
    postal_code: "",
    country: "",
    tax_id: "",
    payment_method_type: "credit_card",
    card_last_four: "0000",
    card_expiry_month: 1,
    card_expiry_year: 2025,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    const fetchBillingProfile = async () => {
      try {
        const data = await apiClient.get<BillingProfileGetResponse>("/api/billing");
        if (data) {
          setFormData({
            full_name: data.full_name,
            company_name: data.company_name,
            email: data.email,
            phone: data.phone,
            address_line1: data.address_line1,
            address_line2: data.address_line2,
            city: data.city,
            state: data.state,
            postal_code: data.postal_code,
            country: data.country,
            tax_id: data.tax_id,
            payment_method_type: data.payment_method_type as any,
            card_last_four: data.card_last_four,
            card_expiry_month: data.card_expiry_month,
            card_expiry_year: data.card_expiry_year,
          });
        }
      } catch (error) {
        console.error("Failed to fetch billing profile:", error);
        // If 404, it means profile hasn't been created yet, which is fine
      } finally {
        setLoading(false);
      }
    };

    fetchBillingProfile();
  }, []);

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    
    if (!formData.full_name) newErrors.full_name = "Full name is required";
    if (!formData.company_name) newErrors.company_name = "Company name is required";
    
    if (!formData.email) {
      newErrors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = "Invalid email format";
    }
    
    if (!formData.phone) newErrors.phone = "Phone number is required";
    if (!formData.address_line1) newErrors.address_line1 = "Address is required";
    if (!formData.city) newErrors.city = "City is required";
    if (!formData.state) newErrors.state = "State is required";
    if (!formData.postal_code) newErrors.postal_code = "Postal code is required";
    if (!formData.country) newErrors.country = "Country is required";
    if (!formData.tax_id) newErrors.tax_id = "Tax ID is required";

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) {
      toast.error("Please fix the errors in the form");
      return;
    }

    setSaving(true);
    try {
      await apiClient.post("/api/billing", formData);
      toast.success("Billing profile updated successfully");
    } catch (error: any) {
      toast.error(error.message || "Failed to update billing profile");
    } finally {
      setSaving(true);
      // Small delay for UX
      setTimeout(() => setSaving(false), 500);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear error when user types
    if (errors[name]) {
      setErrors((prev) => {
        const { [name]: _, ...rest } = prev;
        return rest;
      });
    }
  };

  if (loading) {
    return (
      <Layout breadcrumbItems={[{ label: "Settings", href: "/settings" }, { label: "Billing Profile" }]}>
        <div className="flex items-center justify-center min-h-[50vh]">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout breadcrumbItems={[{ label: "Settings", href: "/settings" }, { label: "Billing Profile" }]}>
      <motion.div 
        className="max-w-4xl mx-auto space-y-8 pb-12"
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
      >
        {/* Header */}
        <Reveal variant="blurInUp">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center">
              <Building2 className="w-7 h-7 text-primary" />
            </div>
            <div>
              <h1 className="text-3xl font-bold font-heading font-semibold">
                <BlurText text="Billing Profile" />
              </h1>
              <p className="text-muted-foreground font-mono text-sm">
                Manage your business identity and invoicing details
              </p>
            </div>
          </div>
        </Reveal>

        <form onSubmit={handleSubmit} className="space-y-6">
          <motion.div variants={fadeInUp} className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* Business Information */}
            <HolographicCard className="p-6 space-y-6">
              <div className="flex items-center gap-2 border-b border-primary/10 pb-4">
                <Building2 className="w-5 h-5 text-primary" />
                <h3 className="font-bold font-heading font-semibold uppercase tracking-wider text-sm">Business Identity</h3>
              </div>

              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="full_name" className="font-mono text-xs text-muted-foreground uppercase">Contact Name</Label>
                  <div className="relative">
                    <FileText className="absolute left-3 top-3 w-4 h-4 text-muted-foreground" />
                    <Input 
                      id="full_name" 
                      name="full_name"
                      placeholder="e.g. John Doe" 
                      className={`pl-10 bg-background/50 border-primary/10 focus:border-primary/40 ${errors.full_name ? 'border-red-500' : ''}`}
                      value={formData.full_name}
                      onChange={handleChange}
                    />
                  </div>
                  {errors.full_name && <p className="text-[10px] text-red-500 font-mono mt-1 uppercase tracking-tighter">{errors.full_name}</p>}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="company_name" className="font-mono text-xs text-muted-foreground uppercase">Company Name</Label>
                  <div className="relative">
                    <Building2 className="absolute left-3 top-3 w-4 h-4 text-muted-foreground" />
                    <Input 
                      id="company_name" 
                      name="company_name"
                      placeholder="e.g. Acme Corp" 
                      className={`pl-10 bg-background/50 border-primary/10 focus:border-primary/40 ${errors.company_name ? 'border-red-500' : ''}`}
                      value={formData.company_name}
                      onChange={handleChange}
                    />
                  </div>
                  {errors.company_name && <p className="text-[10px] text-red-500 font-mono mt-1 uppercase tracking-tighter">{errors.company_name}</p>}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="email" className="font-mono text-xs text-muted-foreground uppercase">Billing Email</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-3 w-4 h-4 text-muted-foreground" />
                      <Input 
                        id="email" 
                        name="email"
                        type="email"
                        placeholder="billing@acme.com" 
                        className={`pl-10 bg-background/50 border-primary/10 focus:border-primary/40 ${errors.email ? 'border-red-500' : ''}`}
                        value={formData.email}
                        onChange={handleChange}
                      />
                    </div>
                    {errors.email && <p className="text-[10px] text-red-500 font-mono mt-1 uppercase tracking-tighter">{errors.email}</p>}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="phone" className="font-mono text-xs text-muted-foreground uppercase">Billing Phone</Label>
                    <div className="relative">
                      <Phone className="absolute left-3 top-3 w-4 h-4 text-muted-foreground" />
                      <Input 
                        id="phone" 
                        name="phone"
                        placeholder="+1 (555) 000-0000" 
                        className={`pl-10 bg-background/50 border-primary/10 focus:border-primary/40 ${errors.phone ? 'border-red-500' : ''}`}
                        value={formData.phone}
                        onChange={handleChange}
                      />
                    </div>
                    {errors.phone && <p className="text-[10px] text-red-500 font-mono mt-1 uppercase tracking-tighter">{errors.phone}</p>}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="tax_id" className="font-mono text-xs text-muted-foreground uppercase">Tax ID / VAT Number</Label>
                  <div className="relative">
                    <CheckCircle2 className="absolute left-3 top-3 w-4 h-4 text-muted-foreground" />
                    <Input 
                      id="tax_id" 
                      name="tax_id"
                      placeholder="e.g. US123456789" 
                      className={`pl-10 bg-background/50 border-primary/10 focus:border-primary/40 ${errors.tax_id ? 'border-red-500' : ''}`}
                      value={formData.tax_id}
                      onChange={handleChange}
                    />
                  </div>
                  {errors.tax_id && <p className="text-[10px] text-red-500 font-mono mt-1 uppercase tracking-tighter">{errors.tax_id}</p>}
                </div>
              </div>
            </HolographicCard>

            {/* Business Address */}
            <HolographicCard className="p-6 space-y-6">
              <div className="flex items-center gap-2 border-b border-primary/10 pb-4">
                <MapPin className="w-5 h-5 text-primary" />
                <h3 className="font-bold font-heading font-semibold uppercase tracking-wider text-sm">Location Details</h3>
              </div>

              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="address_line1" className="font-mono text-xs text-muted-foreground uppercase">Street Address</Label>
                  <div className="relative">
                    <MapPin className="absolute left-3 top-3 w-4 h-4 text-muted-foreground" />
                    <Input 
                      id="address_line1" 
                      name="address_line1"
                      placeholder="123 Business Way" 
                      className={`pl-10 bg-background/50 border-primary/10 focus:border-primary/40 ${errors.address_line1 ? 'border-red-500' : ''}`}
                      value={formData.address_line1}
                      onChange={handleChange}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="address_line2" className="font-mono text-xs text-muted-foreground uppercase text-[10px]">Suite / Apartment (Optional)</Label>
                  <div className="relative">
                    <div className="absolute left-3 top-3 w-4 h-4" />
                    <Input 
                      id="address_line2" 
                      name="address_line2"
                      placeholder="Suite 400" 
                      className="pl-10 bg-background/50 border-primary/10 focus:border-primary/40"
                      value={formData.address_line2}
                      onChange={handleChange}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="city" className="font-mono text-xs text-muted-foreground uppercase">City</Label>
                    <Input 
                      id="city" 
                      name="city"
                      placeholder="San Francisco" 
                      className={`bg-background/50 border-primary/10 focus:border-primary/40 ${errors.city ? 'border-red-500' : ''}`}
                      value={formData.city}
                      onChange={handleChange}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="state" className="font-mono text-xs text-muted-foreground uppercase">State / Province</Label>
                    <Input 
                      id="state" 
                      name="state"
                      placeholder="California" 
                      className={`bg-background/50 border-primary/10 focus:border-primary/40 ${errors.state ? 'border-red-500' : ''}`}
                      value={formData.state}
                      onChange={handleChange}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="postal_code" className="font-mono text-xs text-muted-foreground uppercase">Postal / ZIP</Label>
                    <Input 
                      id="postal_code" 
                      name="postal_code"
                      placeholder="94103" 
                      className={`bg-background/50 border-primary/10 focus:border-primary/40 ${errors.postal_code ? 'border-red-500' : ''}`}
                      value={formData.postal_code}
                      onChange={handleChange}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="country" className="font-mono text-xs text-muted-foreground uppercase">Country</Label>
                    <Input 
                      id="country" 
                      name="country"
                      placeholder="United States" 
                      className={`bg-background/50 border-primary/10 focus:border-primary/40 ${errors.country ? 'border-red-500' : ''}`}
                      value={formData.country}
                      onChange={handleChange}
                    />
                  </div>
                </div>

                <p className="flex items-center gap-2 text-[10px] text-muted-foreground font-mono mt-4">
                  <Globe className="w-3 h-3" />
                  Address will be used for official tax invoices.
                </p>
              </div>
            </HolographicCard>
          </motion.div>

          {/* Payment Method - Read Only for now as handled by Stripe */}
          <Reveal variant="fadeInUp" delay={0.4}>
            <Card className="p-6 bg-muted/20 border-dashed border-primary/20">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                  <CreditCard className="w-5 h-5 text-primary" />
                </div>
                <div className="flex-1">
                  <h3 className="font-bold font-heading font-semibold uppercase text-sm mb-1">Active Payment Method</h3>
                  <p className="text-xs text-muted-foreground font-mono mb-4 italic">// Synchronized with Stripe Security Layer</p>
                  
                  <div className="flex items-center gap-3 font-mono text-sm">
                    <div className="px-3 py-1 bg-background/80 rounded border border-primary/20">
                      •••• •••• •••• {formData.card_last_four}
                    </div>
                    <div className="text-muted-foreground">
                      Exp: {formData.card_expiry_month.toString().padStart(2, '0')}/{formData.card_expiry_year}
                    </div>
                  </div>
                  <p className="mt-4 text-[10px] text-muted-foreground font-mono">
                    To update your credit card, please use the <a href="/billing" className="text-primary hover:underline underline-offset-4">Subscription Billing Portal</a>.
                  </p>
                </div>
              </div>
            </Card>
          </Reveal>

          {/* Actions */}
          <Reveal variant="fadeInUp" delay={0.5}>
            <div className="flex justify-end pt-4">
              <Button 
                type="submit" 
                variant="hero" 
                size="lg" 
                className="w-full sm:w-auto min-w-[200px] h-14 font-heading font-semibold"
                disabled={saving}
              >
                {saving ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    SAVING CHANGES...
                  </>
                ) : (
                  <>
                    <Save className="w-5 h-5 mr-3" />
                    UPDATE BILLING PROFILE
                  </>
                )}
              </Button>
            </div>
          </Reveal>
        </form>

        {/* Global Warnings */}
        <Reveal variant="fadeIn" delay={0.6}>
          <div className="flex items-center gap-3 p-4 rounded-lg bg-orange-500/10 border border-orange-500/20 text-orange-200">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <p className="text-xs font-mono tracking-tight leading-relaxed">
              <strong>SECURITY NOTICE:</strong> Changes to your billing profile may trigger a re-verification of your payment methods. 
              Ensure the company name matches your registered tax entity to avoid invoicing delays.
            </p>
          </div>
        </Reveal>
      </motion.div>
    </Layout>
  );
};

export default BillingProfile;
