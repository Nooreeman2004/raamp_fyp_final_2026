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
import { Phone, Building, Briefcase, Loader2, ArrowLeft, ArrowRight, HelpCircle } from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { authService } from "@/services/authService";
import ProgressIndicator from "@/components/ProgressIndicator";
import { useUnsavedChanges } from "@/hooks/useUnsavedChanges";
import { cn } from "@/lib/utils";

interface BusinessDomain {
  id: string;
  business: string;
  description: string;
}

const PersonalDetails = () => {
  const navigate = useNavigate();
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [phone, setPhone] = useState("");
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [bio, setBio] = useState("");
  const [businessDomain, setBusinessDomain] = useState("");
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
  const hasUnsavedChanges = JSON.stringify({
    firstName, lastName, phone, company, role, bio, businessDomain
  }) !== initialData;

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
        toast({
          title: "Warning",
          description: "Could not load business categories. Please refresh the page.",
          variant: "destructive",
        });
      } finally {
        setIsLoadingDomains(false);
      }
    };

    fetchBusinessDomains();

    // Load existing profile data
    (async () => {
      try {
        const profile = await authService.getProfile();
        if (profile) {
          setFirstName(profile.first_name || "");
          setLastName(profile.last_name || "");
          setPhone(profile.phone_number || "");
          setCompany(profile.company || "");
          setRole(profile.role || "");
          setBio(profile.bio || "");
          setBusinessDomain(profile.business_domain || "");
          setInitialData(JSON.stringify({
            firstName: profile.first_name || "",
            lastName: profile.last_name || "",
            phone: profile.phone_number || "",
            company: profile.company || "",
            role: profile.role || "",
            bio: profile.bio || "",
            businessDomain: profile.business_domain || "",
          }));
        }
      } catch (err) {
        // Ignore - user might not have profile yet
      }
    })();
  }, []);

  // Real-time validation
  const validateField = (field: string, value: string): string => {
    switch (field) {
      case 'firstName':
      case 'lastName':
        return value.trim().length < 1 ? 'This field is required' : '';
      case 'phone': {
        const trimmed = value.trim();
        if (!trimmed) {
          return 'Phone number is required';
        }
        if (!/^\d{11}$/.test(trimmed)) {
          return 'Phone number must be exactly 11 digits';
        }
        return '';
      }
      case 'company':
      case 'role':
        return value.trim().length < 1 ? 'This field is required' : '';
      case 'bio':
        return value.trim().length < 10 ? 'Bio must be at least 10 characters' : '';
      default:
        return '';
    }
  };

  const getFieldError = (field: string): string => {
    if (!touched[field as keyof typeof touched]) return '';
    const value = {
      firstName, lastName, phone, company, role, bio
    }[field] || '';
    return validateField(field, value);
  };

  const isFormValid = () => {
    return (
      firstName.trim().length > 0 &&
      lastName.trim().length > 0 &&
      /^\d{11}$/.test(phone.trim()) &&
      company.trim().length > 0 &&
      role.trim().length > 0 &&
      bio.trim().length >= 10 &&
      !!businessDomain
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Mark all fields as touched
    setTouched({
      firstName: true,
      lastName: true,
      phone: true,
      company: true,
      role: true,
      bio: true,
      businessDomain: true,
    });

    // Validate all required fields
    if (!isFormValid()) {
      toast({
        title: "Validation Error",
        description: "Please fill in all required fields correctly.",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);

    try {
      const response = await authService.updateProfile({
        first_name: firstName,
        last_name: lastName,
        phone_number: phone,
        company: company,
        role: role,
        bio: bio,
        business_domain: businessDomain,
      });

      // Update initial data to clear unsaved changes warning
      setInitialData(JSON.stringify({
        firstName, lastName, phone, company, role, bio, businessDomain
      }));

      toast({
        title: "Profile Created",
        description: response.message || "Your profile has been created successfully.",
      });

      // Navigate to onboarding step
      setTimeout(() => navigate("/profile/onboarding"), 1000);
    } catch (error: any) {
      console.error("Profile update error:", error);

      toast({
        title: "Update Failed",
        description: error.message || "Unable to update profile. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Layout breadcrumbItems={[
      { label: 'Profile', href: '/profile' },
      { label: 'Personal Details' },
    ]}>

      <div className="flex items-center justify-center">
        <Card className="w-full max-w-3xl p-8 card-shadow bg-card/80 backdrop-blur-sm border-primary/20">
          <div className="space-y-6">
            <div className="text-center space-y-2">
              <div className="flex justify-center mb-4">
                <img src={raampIcon} alt="RAAMP" className="h-24 w-24" />
              </div>
              <h1 className="text-3xl font-bold">Create Profile</h1>
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

            {/* Navigation - removed Back/Skip buttons per design request */}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="firstName">
                  First Name <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="firstName"
                  type="text"
                  placeholder="Jane"
                  value={firstName}
                  onChange={(e) => {
                    setFirstName(e.target.value);
                    setTouched(prev => ({ ...prev, firstName: true }));
                  }}
                  onBlur={() => setTouched(prev => ({ ...prev, firstName: true }))}
                  required
                  className={cn(
                    "bg-background/50",
                    getFieldError('firstName') && "border-destructive"
                  )}
                />
                {getFieldError('firstName') && (
                  <p className="text-sm text-destructive">{getFieldError('firstName')}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="lastName">
                  Last Name <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="lastName"
                  type="text"
                  placeholder="Doe"
                  value={lastName}
                  onChange={(e) => {
                    setLastName(e.target.value);
                    setTouched(prev => ({ ...prev, lastName: true }));
                  }}
                  onBlur={() => setTouched(prev => ({ ...prev, lastName: true }))}
                  required
                  className={cn(
                    "bg-background/50",
                    getFieldError('lastName') && "border-destructive"
                  )}
                />
                {getFieldError('lastName') && (
                  <p className="text-sm text-destructive">{getFieldError('lastName')}</p>
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
                  type="tel"
                  placeholder="03001234567"
                  value={phone}
                  onChange={(e) => {
                    setPhone(e.target.value);
                    setTouched(prev => ({ ...prev, phone: true }));
                  }}
                  onBlur={() => setTouched(prev => ({ ...prev, phone: true }))}
                  required
                  className={cn(
                    "bg-background/50 pl-10",
                    getFieldError('phone') && "border-destructive"
                  )}
                />
              </div>
              {getFieldError('phone') && (
                <p className="text-sm text-destructive">{getFieldError('phone')}</p>
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
                    type="text"
                    placeholder="Acme Marketing Solutions"
                    value={company}
                    onChange={(e) => {
                      setCompany(e.target.value);
                      setTouched(prev => ({ ...prev, company: true }));
                    }}
                    onBlur={() => setTouched(prev => ({ ...prev, company: true }))}
                    required
                    className={cn(
                      "bg-background/50 pl-10",
                      getFieldError('company') && "border-destructive"
                    )}
                  />
                </div>
                {getFieldError('company') && (
                  <p className="text-sm text-destructive">{getFieldError('company')}</p>
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
                    type="text"
                    placeholder="Head of Digital Marketing"
                    value={role}
                    onChange={(e) => {
                      setRole(e.target.value);
                      setTouched(prev => ({ ...prev, role: true }));
                    }}
                    onBlur={() => setTouched(prev => ({ ...prev, role: true }))}
                    required
                    className={cn(
                      "bg-background/50 pl-10",
                      getFieldError('role') && "border-destructive"
                    )}
                  />
                </div>
                {getFieldError('role') && (
                  <p className="text-sm text-destructive">{getFieldError('role')}</p>
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
                  value={businessDomain} 
                  onValueChange={(value) => {
                    setBusinessDomain(value);
                    setTouched(prev => ({ ...prev, businessDomain: true }));
                  }}
                  required
                >
                  <SelectTrigger className={cn(
                    "bg-background/50",
                    touched.businessDomain && !businessDomain && "border-destructive"
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
              {touched.businessDomain && !businessDomain && (
                <p className="text-sm text-destructive">Please select a business category</p>
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
                placeholder="A dedicated digital marketing professional with over 10 years of experience, passionate about leveraging AI to optimize campaign performance and drive ROI."
                value={bio}
                onChange={(e) => {
                  setBio(e.target.value);
                  setTouched(prev => ({ ...prev, bio: true }));
                }}
                onBlur={() => setTouched(prev => ({ ...prev, bio: true }))}
                required
                className={cn(
                  "bg-background/50 min-h-[120px]",
                  getFieldError('bio') && "border-destructive"
                )}
              />
              {getFieldError('bio') && (
                <p className="text-sm text-destructive">{getFieldError('bio')}</p>
              )}
              {bio && !getFieldError('bio') && (
                <p className="text-xs text-muted-foreground">
                  {bio.length} characters (minimum 10 required)
                </p>
              )}
            </div>

            <Button 
              type="submit" 
              className="w-full" 
              variant="hero" 
              size="lg"
              disabled={isLoading}
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
