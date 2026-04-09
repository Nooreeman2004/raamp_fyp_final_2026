import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "@/components/Layout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Building2, Save, Globe, Phone, Briefcase, Shield } from "lucide-react";
import { toast as sonner } from "sonner";
import { useFormPersistence } from "@/hooks/useFormPersistence";
import { businessService } from "@/services/businessService";
import { authService } from "@/services/authService";
import { useAuth } from "@/hooks/useAuth";
import { useOnboardingStatus } from "@/hooks/useOnboardingStatus";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { hoverScale } from "@/utils/animations";
import { BlurText } from "@/components/ui/text-reveal";
import { PasswordVerificationDialog } from "@/components/PasswordVerificationDialog";

const BusinessSetup = () => {
    const navigate = useNavigate();
    const { refreshUser, user } = useAuth();
    const { isFullyOnboarded } = useOnboardingStatus();
    const [isLoading, setIsLoading] = useState(false);
    const [isFetching, setIsFetching] = useState(true);
    const [isEditing, setIsEditing] = useState(false);
    const [hasExistingData, setHasExistingData] = useState(false);

    // Verification Gate State
    const [showPasswordGate, setShowPasswordGate] = useState(false);

    // Use form persistence
    const { values: formData, handleChange, setValues, clearPersistence } = useFormPersistence("business_setup_form", {
        businessName: "",
        website: "",
        phone: "",
        description: "",
        businessType: "",
    });

    const [touched, setTouched] = useState({
        businessName: false,
        businessType: false,
        phone: false,
    });

    useEffect(() => {
        const fetchCurrentSetup = async () => {
            try {
                const data = await businessService.getHyperlocalSetup();
                if (data && data.has_setup) {
                    setValues({
                        businessName: data.business_name || "",
                        website: data.website || "",
                        phone: data.phone || "",
                        description: data.description || "",
                        businessType: data.business_type || "",
                    });
                    setHasExistingData(true);

                    // If user is fully onboarded (existing user), keep fields read-only
                    // New users (not fully onboarded) can edit immediately during onboarding
                    if (!isFullyOnboarded) {
                        setIsEditing(true);
                    }
                } else {
                    // No existing data, user can edit immediately (likely new user)
                    setIsEditing(true);
                }
            } catch (error) {
                console.error("Failed to fetch current setup:", error);
                // If fetch fails, allow editing (assume new user)
                setIsEditing(true);
            } finally {
                setIsFetching(false);
            }
        };
        fetchCurrentSetup();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isFullyOnboarded]);

    const handleEdit = () => {
        if (isEditing || !user?.email) return;
        setShowPasswordGate(true);
    };

    const handleVerified = () => {
        setShowPasswordGate(false);
        setIsEditing(true);
        sonner.success("Verified", {
            description: "You can now edit your business details",
        });
    };

    const setValue = (key: keyof typeof formData, value: string | number) => {
        setValues(prev => ({ ...prev, [key]: value }));
    };

    const validateField = (field: string, value: string | number): string => {
        const strValue = String(value);
        switch (field) {
            case 'businessName':
                return !strValue || strValue.trim().length < 1 ? 'Business Name required' : '';
            case 'businessType':
                return !value ? 'Selection required' : '';
            case 'phone':
                return !strValue || strValue.trim().length < 1 ? 'Contact required' : '';
            default:
                return '';
        }
    };

    const getFieldError = (field: string): string => {
        if (!touched[field as keyof typeof touched]) return '';
        const value = formData[field as keyof typeof formData];
        return validateField(field, value);
    };

    const isFormValid = () => {
        return (
            formData.businessName.trim().length > 0 &&
            formData.businessType.trim().length > 0 &&
            formData.phone.trim().length > 0
        );
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        setTouched({
            businessName: true,
            businessType: true,
            phone: true,
        });

        if (!isFormValid()) {
            sonner.error("Incomplete Setup", {
                description: "Please verify all required fields marked with *",
            });
            return;
        }

        setIsLoading(true);

        try {
            const response = await businessService.saveHyperlocalSetup({
                business_name: formData.businessName,
                business_type: formData.businessType,
                website: formData.website,
                phone: formData.phone,
                description: formData.description,
            });

            if (response) {
                clearPersistence();
                await refreshUser();

                // Disable editing after successful save
                if (isFullyOnboarded) {
                    setIsEditing(false);
                }

                sonner.success("Business Details Saved", {
                    description: "Your business profile has been updated.",
                });

                // Only navigate to next onboarding step if user is NOT fully onboarded (new user in onboarding flow)
                if (!isFullyOnboarded) {
                    setTimeout(() => navigate("/profile/brand-settings"), 1000);
                }
            }
        } catch (error: unknown) {
            const err = error as { message?: string };
            sonner.error("Save Failed", {
                description: err.message || "Unable to save business details.",
            });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Layout breadcrumbItems={[{ label: "Profile", href: "/profile/user" }, { label: "Business Setup" }]}>
            <motion.div
                className="space-y-6 max-w-3xl mx-auto"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
            >
                <Reveal variant="blurInUp">
                    <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-4">
                            <div className="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center">
                                <Building2 className="w-7 h-7 text-primary" />
                            </div>
                            <div>
                                <h1 className="text-3xl font-bold font-heading font-semibold">
                                    <BlurText text="Business Setup" />
                                </h1>
                                <p className="text-muted-foreground font-mono text-sm">
                                    Manage your business location and contact details
                                </p>
                            </div>
                        </div>

                        {/* Show Edit button only for fully onboarded users with existing data */}
                        {isFullyOnboarded && hasExistingData && !isEditing && !isFetching && (
                            <Button
                                variant="outline"
                                onClick={handleEdit}
                                className="font-mono text-xs gap-2"
                            >
                                <Shield className="w-4 h-4" />
                                Unlock Edit
                            </Button>
                        )}
                    </div>
                </Reveal>

                <Reveal variant="fadeInUp" delay={0.1}>
                    <Card className="p-6 bg-card/70 backdrop-blur-sm border-primary/10">
                        <form onSubmit={handleSubmit} className="space-y-6">
                            <div className="grid gap-6 md:grid-cols-2">
                                <div className="space-y-2">
                                    <Label htmlFor="businessName" className="font-mono text-xs">
                                        Business Name <span className="text-red-500">*</span>
                                    </Label>
                                    <div className="relative">
                                        <Building2 className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                        <Input
                                            id="businessName"
                                            name="businessName"
                                            value={formData.businessName}
                                            onChange={handleChange}
                                            onBlur={() => setTouched(prev => ({ ...prev, businessName: true }))}
                                            readOnly={!isEditing}
                                            className={cn(
                                                "pl-9 bg-background/50 font-mono",
                                                touched.businessName && !formData.businessName && "border-destructive",
                                                !isEditing && "cursor-not-allowed opacity-60"
                                            )}
                                            placeholder="Enter business name"
                                        />
                                    </div>
                                    {getFieldError('businessName') && (
                                        <p className="text-[10px] text-destructive font-mono uppercase tracking-tighter mt-1">{getFieldError('businessName')}</p>
                                    )}
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="businessType" className="font-mono text-xs">
                                        Industry <span className="text-red-500">*</span>
                                    </Label>
                                    <div className="relative">
                                        <Briefcase className="absolute left-3 top-3 h-4 w-4 text-muted-foreground z-10" />
                                        <Select
                                            value={formData.businessType}
                                            onValueChange={(val) => {
                                                setValue('businessType', val);
                                                setTouched(prev => ({ ...prev, businessType: true }));
                                            }}
                                            disabled={!isEditing}
                                        >
                                            <SelectTrigger className={cn(
                                                "pl-9 bg-background/50 font-mono w-full",
                                                touched.businessType && !formData.businessType && "border-destructive",
                                                !isEditing && "cursor-not-allowed opacity-60"
                                            )}>
                                                <SelectValue placeholder="Select industry" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="Retail">Retail</SelectItem>
                                                <SelectItem value="Hospitality">Hospitality</SelectItem>
                                                <SelectItem value="Services">Services</SelectItem>
                                                <SelectItem value="Fashion">Fashion</SelectItem>
                                                <SelectItem value="Restaurant">Restaurant</SelectItem>
                                                <SelectItem value="Technology">Technology</SelectItem>
                                                <SelectItem value="Health">Health & Wellness</SelectItem>
                                                <SelectItem value="Other">Other</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    {getFieldError('businessType') && (
                                        <p className="text-[10px] text-destructive font-mono uppercase tracking-tighter mt-1">{getFieldError('businessType')}</p>
                                    )}
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="website" className="font-mono text-xs">Website</Label>
                                    <div className="relative">
                                        <Globe className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                        <Input
                                            id="website"
                                            name="website"
                                            value={formData.website}
                                            onChange={handleChange}
                                            readOnly={!isEditing}
                                            className={cn(
                                                "pl-9 bg-background/50 font-mono",
                                                !isEditing && "cursor-not-allowed opacity-60"
                                            )}
                                            placeholder="https://..."
                                        />
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="phone" className="font-mono text-xs">
                                        Phone Number <span className="text-red-500">*</span>
                                    </Label>
                                    <div className="relative">
                                        <Phone className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                        <Input
                                            id="phone"
                                            name="phone"
                                            value={formData.phone}
                                            onChange={handleChange}
                                            onBlur={() => setTouched(prev => ({ ...prev, phone: true }))}
                                            readOnly={!isEditing}
                                            className={cn(
                                                "pl-9 bg-background/50 font-mono",
                                                touched.phone && !formData.phone && "border-destructive",
                                                !isEditing && "cursor-not-allowed opacity-60"
                                            )}
                                            placeholder="+1 (555) ..."
                                        />
                                    </div>
                                    {getFieldError('phone') && (
                                        <p className="text-[10px] text-destructive font-mono uppercase tracking-tighter mt-1">{getFieldError('phone')}</p>
                                    )}
                                </div>

                                <div className="space-y-2 md:col-span-2">
                                    <Label htmlFor="description" className="font-mono text-xs">Business Description</Label>
                                    <Textarea
                                        id="description"
                                        name="description"
                                        value={formData.description}
                                        onChange={handleChange}
                                        readOnly={!isEditing}
                                        className={cn(
                                            "bg-background/50 min-h-[100px] font-mono",
                                            !isEditing && "cursor-not-allowed opacity-60"
                                        )}
                                        placeholder="Tell us about your business..."
                                    />
                                </div>
                            </div>

                            <div className="flex justify-end pt-4">
                                <motion.div variants={hoverScale} initial="rest" whileHover={isFormValid() && isEditing ? "hover" : "rest"} whileTap={isFormValid() && isEditing ? "tap" : "rest"}>
                                    <Button
                                        type="submit"
                                        disabled={isLoading || !isFormValid() || !isEditing}
                                        className={cn(
                                            "font-heading font-semibold text-lg min-w-[150px]",
                                            (!isFormValid() || !isEditing) && "opacity-50 cursor-not-allowed grayscale"
                                        )}
                                    >
                                        {isLoading ? (
                                            <div className="flex items-center gap-2">
                                                <div className="w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
                                                Saving...
                                            </div>
                                        ) : (
                                            <>
                                                <Save className="w-4 h-4 mr-2" />
                                                {isFullyOnboarded ? "Save Changes" : "Save & Continue"}
                                            </>
                                        )}
                                    </Button>
                                </motion.div>
                            </div>
                        </form>
                    </Card>
                </Reveal>

                {/* Password Gate Dialog */}
                <PasswordVerificationDialog
                    isOpen={showPasswordGate}
                    onClose={() => setShowPasswordGate(false)}
                    onVerified={handleVerified}
                />
            </motion.div>
        </Layout>
    );
};

export default BusinessSetup;
