import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "@/components/Layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import raampIcon from "@/assets/raamp-icon-transparent.png";
import { Phone, Building, Briefcase, Loader2, HelpCircle } from "lucide-react";
import { authService } from "@/services/authService";
import { toast as sonner } from "sonner";
import { BlurText } from "@/components/ui/text-reveal";
import ProgressIndicator from "@/components/ProgressIndicator";
import { useUnsavedChanges } from "@/hooks/useUnsavedChanges";
import { cn } from "@/lib/utils";
import { useFormPersistence } from "@/hooks/useFormPersistence";
import { useAuth } from "@/hooks/useAuth";
import { useOnboardingStatus } from "@/hooks/useOnboardingStatus";

interface BusinessDomain {
  id: string;
  business: string;
  description: string;
}

const PersonalDetails = () => {
  const navigate = useNavigate();
  const { refreshUser } = useAuth();
  const { isFullyOnboarded } = useOnboardingStatus();

  // Use persistence hook for form data
  const { values: formData, setValues: setFormData, handleChange, clearPersistence } = useFormPersistence("personal_details_form", {
    firstName: "",
    lastName: "",
    phone: "",
    company: "",
    role: "",
    bio: "",
    businessDomain: ""
  });

  const [businessDomains, setBusinessDomains] = useState<BusinessDomain[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingDomains, setIsLoadingDomains] = useState(true);
  const [touched, setTouched] = useState({
    firstName: false,
    lastName: false,
    phone: false,
    company: false,
    role: false,
    bio: false,
    businessDomain: false,
  });
  const [initialData, setInitialData] = useState("");

  // Track unsaved changes
  const hasUnsavedChanges = JSON.stringify(formData) !== initialData;

  useUnsavedChanges({
    hasUnsavedChanges: hasUnsavedChanges && initialData !== "",
    message: "You have unsaved changes. Are you sure you want to leave?"
  });

  // Profile setup steps
  const profileSteps = [
    { id: 'personal', label: 'Personal', description: 'Basic Info' },
    { id: 'business', label: 'Business', description: 'Company Details' },
    { id: 'onboarding', label: 'Connections', description: 'Link Accounts' },
  ];

  useEffect(() => {
    const fetchBusinessDomains = async () => {
      try {
        const response = await fetch("http://localhost:8000/api/business-domains");
        const data = await response.json();
        setBusinessDomains(data.domains || []);
      } catch (error) {
        console.error("Failed to fetch business domains:", error);
        sonner.error("Warning", {
          description: "Could not load business categories. Please refresh the page.",
        });
      } finally {
        setIsLoadingDomains(false);
      }
    };

    fetchBusinessDomains();

    // Load existing profile data ONLY if form is empty (to prefer persisted data over fetched data if user was typing)
    // Actually, usually we prefer fetched DB data, but here we want persistence.
    // Strategy: If persistence has data that differs from DB, keep persistence? 
    // Best practice: If form is dirty (in session), keep session. If clean session, load DB.
    // For simplicity, we will hydrate from DB only if session is "default/empty" OR we explicitly handle it.
    // However, useFormPersistence handles hydration on mount.
    // So here we only fetch existing profile if we want to pre-fill for a NEW session. 

    (async () => {
      try {
        const profile = await authService.getProfile();
        // Only override if no local changes? 
        // Or better: load profile into 'initialData'.
        // If 'formData' is deep equal to default, update it with profile.

        const dbData = {
          firstName: profile?.first_name || "",
          lastName: profile?.last_name || "",
          phone: profile?.phone_number || "",
          company: profile?.company || "",
          role: profile?.role || "",
          bio: profile?.bio || "",
          businessDomain: profile?.business_domain || "",
        };

        setInitialData(JSON.stringify(dbData));

        // If current form data is empty, fill with DB data
        const isEmpty = !formData.firstName && !formData.lastName;
        if (isEmpty && profile) {
          setFormData(dbData);
        }
      } catch (err) {
        // Ignore - user might not have profile yet
      }
    })();
  }, []); // Run on mount

  // Real-time validation
  const validateField = (field: string, value: string): string => {
    switch (field) {
      case 'firstName':
      case 'lastName':
        return value.trim().length < 1 ? 'Field is required' : '';
      case 'phone': {
        const trimmed = value.trim();
        if (!trimmed) return 'Phone number is required';
        if (!/^\d{11}$/.test(trimmed)) return 'Must be exactly 11 digits';
        return '';
      }
      case 'company':
      case 'role':
        return value.trim().length < 1 ? 'Field is required' : '';
      case 'businessDomain':
        return !value ? 'Selection required' : '';
      case 'bio':
        return value.trim().length < 10 ? 'Minimum 10 characters required' : '';
      default:
        return '';
    }
  };

  const getFieldError = (field: string): string => {
    if (!touched[field as keyof typeof touched]) return '';
    const value = (formData as any)[field] || '';
    return validateField(field, value);
  };

  const isFormValid = () => {
    return (
      formData.firstName.trim().length > 0 &&
      formData.lastName.trim().length > 0 &&
      /^\d{11}$/.test(formData.phone.trim()) &&
      formData.company.trim().length > 0 &&
      formData.role.trim().length > 0 &&
      formData.bio.trim().length >= 10 &&
      !!formData.businessDomain
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    setTouched({
      firstName: true,
      lastName: true,
      phone: true,
      company: true,
      role: true,
      bio: true,
      businessDomain: true,
    });

    if (!isFormValid()) {
      sonner.error("Incomplete Profile", {
        description: "Please fulfill all required fields marked with *",
      });
      return;
    }

    setIsLoading(true);

    try {
      const response = await authService.updateProfile({
        first_name: formData.firstName,
        last_name: formData.lastName,
        phone_number: formData.phone,
        company: formData.company,
        role: formData.role,
        bio: formData.bio,
        business_domain: formData.businessDomain,
      });

      setInitialData(JSON.stringify(formData));
      await refreshUser();
      clearPersistence();

      sonner.success("Matrix Synchronized", {
        description: "Your professional parameters have been locked in.",
      });

      // Only navigate to next onboarding step if user is NOT fully onboarded (new user in onboarding flow)
      // If user is fully onboarded (editing from Settings), just save and stay
      if (!isFullyOnboarded) {
        setTimeout(() => navigate("/profile/onboarding"), 1000);
      }
    } catch (error: any) {
      console.error("Profile update error:", error);
      sonner.error("Sync Failed", {
        description: error.message || "Unable to update profile. Please check your connection.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Manual change handler for complex inputs (Select, etc)
  const handleValueChange = (name: string, value: string) => {
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  return (
    <Layout breadcrumbItems={[
      { label: 'Dashboard', href: '/dashboard' },
      { label: 'Personal Details' },
    ]}>

      <div className="flex items-center justify-center">
        <Card className="w-full max-w-3xl p-8 card-shadow bg-card/80 backdrop-blur-sm border-primary/20">
          <div className="space-y-6">
            <div className="text-center space-y-2">
              <div className="flex justify-center mb-4">
                <img src={raampIcon} alt="RAAMP" className="h-24 w-24" />
              </div>
              <h1 className="text-3xl font-bold font-bebas tracking-wide">
                <BlurText text="CREATE PROFILE" />
              </h1>
              <p className="text-muted-foreground">
                Set up your account details.
              </p>
            </div>

            {/* Progress Indicator */}
            <ProgressIndicator
              steps={profileSteps}
              currentStep={0}
              completedSteps={[]}
            />

            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="firstName">
                    First Name <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="firstName"
                    name="firstName"
                    type="text"
                    placeholder="Jane"
                    value={formData.firstName}
                    onChange={handleChange}
                    onBlur={() => setTouched(prev => ({ ...prev, firstName: true }))}
                    required
                    className={cn(
                      "bg-background/50",
                      getFieldError('firstName') && "border-destructive"
                    )}
                  />
                  {getFieldError('firstName') && (
                    <p className="text-[10px] text-destructive font-mono uppercase tracking-tighter mt-1">{getFieldError('firstName')}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="lastName">
                    Last Name <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="lastName"
                    name="lastName"
                    type="text"
                    placeholder="Doe"
                    value={formData.lastName}
                    onChange={handleChange}
                    onBlur={() => setTouched(prev => ({ ...prev, lastName: true }))}
                    required
                    className={cn(
                      "bg-background/50",
                      getFieldError('lastName') && "border-destructive"
                    )}
                  />
                  {getFieldError('lastName') && (
                    <p className="text-[10px] text-destructive font-mono uppercase tracking-tighter mt-1">{getFieldError('lastName')}</p>
                  )}
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="phone">
                  Phone Number <span className="text-red-500">*</span>
                </Label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    id="phone"
                    name="phone"
                    type="tel"
                    placeholder="03001234567"
                    value={formData.phone}
                    onChange={handleChange}
                    onBlur={() => setTouched(prev => ({ ...prev, phone: true }))}
                    required
                    className={cn(
                      "bg-background/50 pl-10",
                      getFieldError('phone') && "border-destructive"
                    )}
                  />
                </div>
                {getFieldError('phone') && (
                  <p className="text-[10px] text-destructive font-mono uppercase tracking-tighter mt-1">{getFieldError('phone')}</p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="company">
                    Company <span className="text-red-500">*</span>
                  </Label>
                  <div className="relative">
                    <Building className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                      id="company"
                      name="company"
                      type="text"
                      placeholder="Acme Marketing Solutions"
                      value={formData.company}
                      onChange={handleChange}
                      onBlur={() => setTouched(prev => ({ ...prev, company: true }))}
                      required
                      className={cn(
                        "bg-background/50 pl-10",
                        getFieldError('company') && "border-destructive"
                      )}
                    />
                  </div>
                  {getFieldError('company') && (
                    <p className="text-[10px] text-destructive font-mono uppercase tracking-tighter mt-1">{getFieldError('company')}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="role">
                    Role <span className="text-red-500">*</span>
                  </Label>
                  <div className="relative">
                    <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                      id="role"
                      name="role"
                      type="text"
                      placeholder="Head of Digital Marketing"
                      value={formData.role}
                      onChange={handleChange}
                      onBlur={() => setTouched(prev => ({ ...prev, role: true }))}
                      required
                      className={cn(
                        "bg-background/50 pl-10",
                        getFieldError('role') && "border-destructive"
                      )}
                    />
                  </div>
                  {getFieldError('role') && (
                    <p className="text-[10px] text-destructive font-mono uppercase tracking-tighter mt-1">{getFieldError('role')}</p>
                  )}
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Label htmlFor="businessDomain">
                    Business Domain <span className="text-red-500">*</span>
                  </Label>
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger>
                        <HelpCircle className="w-4 h-4 text-muted-foreground" />
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>Select the category that best describes your business</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </div>
                {isLoadingDomains ? (
                  <div className="flex items-center justify-center p-4 bg-background/50 rounded-md">
                    <Loader2 className="w-5 h-5 animate-spin text-primary" />
                    <span className="ml-2 text-sm text-muted-foreground">Loading categories...</span>
                  </div>
                ) : (
                  <Select
                    value={formData.businessDomain}
                    onValueChange={(value) => {
                      handleValueChange('businessDomain', value);
                      setTouched(prev => ({ ...prev, businessDomain: true }));
                    }}
                    required
                  >
                    <SelectTrigger className={cn(
                      "bg-background/50",
                      touched.businessDomain && !formData.businessDomain && "border-destructive"
                    )}>
                      <SelectValue placeholder="Select your business category" />
                    </SelectTrigger>
                    <SelectContent>
                      {businessDomains.map((domain) => (
                        <SelectItem key={domain.id} value={domain.id}>
                          <div>
                            <div className="font-medium">{domain.business}</div>
                            <div className="text-xs text-muted-foreground">{domain.description}</div>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
                {touched.businessDomain && !formData.businessDomain && (
                  <p className="text-[10px] text-destructive font-mono uppercase tracking-tighter mt-1">Selection required</p>
                )}
              </div>

              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Label htmlFor="bio">
                    Bio <span className="text-red-500">*</span>
                  </Label>
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger>
                        <HelpCircle className="w-4 h-4 text-muted-foreground" />
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>Write a brief description about yourself (minimum 10 characters)</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </div>
                <Textarea
                  id="bio"
                  name="bio"
                  placeholder="A dedicated digital marketing professional with over 10 years of experience, passionate about leveraging AI to optimize campaign performance and drive ROI."
                  value={formData.bio}
                  onChange={handleChange}
                  onBlur={() => setTouched(prev => ({ ...prev, bio: true }))}
                  required
                  className={cn(
                    "bg-background/50 min-h-[120px]",
                    getFieldError('bio') && "border-destructive"
                  )}
                />
                {getFieldError('bio') && (
                  <p className="text-[10px] text-destructive font-mono uppercase tracking-tighter mt-1">{getFieldError('bio')}</p>
                )}
                {formData.bio && !getFieldError('bio') && (
                  <p className="text-xs text-muted-foreground">
                    {formData.bio.length} characters (minimum 10 required)
                  </p>
                )}
              </div>

              <Button
                type="submit"
                className={cn(
                  "w-full",
                  (!isFormValid() || isLoading) && "opacity-50 grayscale cursor-not-allowed"
                )}
                variant="hero"
                size="lg"
                disabled={isLoading || !isFormValid()}
              >
                {isLoading ? (
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
                    Saving Profile...
                  </div>
                ) : (
                  "Continue to Ecosystem Connection"
                )}
              </Button>
            </form>
          </div>
        </Card>
      </div>
    </Layout>
  );
};

export default PersonalDetails;
