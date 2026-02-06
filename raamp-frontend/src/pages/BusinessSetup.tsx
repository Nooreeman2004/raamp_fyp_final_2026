import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "@/components/Layout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Building2, Save, Globe, Phone, Briefcase } from "lucide-react";
import { toast as sonner } from "sonner";
import { useFormPersistence } from "@/hooks/useFormPersistence";
import { businessService } from "@/services/businessService";
import { useAuth } from "@/hooks/useAuth";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { hoverScale } from "@/utils/animations";
import { BlurText } from "@/components/ui/text-reveal";

const BusinessSetup = () => {
    const navigate = useNavigate();
    const { refreshUser } = useAuth();
    const [isLoading, setIsLoading] = useState(false);
    const [isFetching, setIsFetching] = useState(true);

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
                }
            } catch (error) {
                console.error("Failed to fetch current setup:", error);
            } finally {
                setIsFetching(false);
            }
        };
        fetchCurrentSetup();
    }, []);

    const setValue = (key: keyof typeof formData, value: string | number) => {
        setValues(prev => ({ ...prev, [key]: value }));
    };

    const validateField = (field: string, value: any): string => {
        switch (field) {
            case 'businessName':
                return !value || value.trim().length < 1 ? 'Business Name required' : '';
            case 'businessType':
                return !value ? 'Selection required' : '';
            case 'phone':
                return !value || value.trim().length < 1 ? 'Contact required' : '';
            default:
                return '';
        }
    };

    const getFieldError = (field: string): string => {
        if (!touched[field as keyof typeof touched]) return '';
        const value = (formData as any)[field];
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
                sonner.success("Business Details Saved", {
                    description: "Your business profile has been updated.",
                });

                setTimeout(() => navigate("/profile/brand-settings"), 1000);
            }
        } catch (error: any) {
            sonner.error("Save Failed", {
                description: error.message || "Unable to save business details.",
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
                    <div className="flex items-center gap-4">
                        <div className="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center">
                            <Building2 className="w-7 h-7 text-primary" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold font-bebas tracking-wide">
                                <BlurText text="Business Setup" />
                            </h1>
                            <p className="text-muted-foreground font-mono text-sm">
                                Manage your business location and contact details
                            </p>
                        </div>
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
                                            className={cn(
                                                "pl-9 bg-background/50 font-mono",
                                                touched.businessName && !formData.businessName && "border-destructive"
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
                                        >
                                            <SelectTrigger className={cn(
                                                "pl-9 bg-background/50 font-mono w-full",
                                                touched.businessType && !formData.businessType && "border-destructive"
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
                                            className="pl-9 bg-background/50 font-mono"
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
                                            className={cn(
                                                "pl-9 bg-background/50 font-mono",
                                                touched.phone && !formData.phone && "border-destructive"
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
                                        className="bg-background/50 min-h-[100px] font-mono"
                                        placeholder="Tell us about your business..."
                                    />
                                </div>
                            </div>

                            <div className="flex justify-end pt-4">
                                <motion.div variants={hoverScale} initial="rest" whileHover={isFormValid() ? "hover" : "rest"} whileTap={isFormValid() ? "tap" : "rest"}>
                                    <Button
                                        type="submit"
                                        disabled={isLoading || !isFormValid()}
                                        className={cn(
                                            "font-bebas tracking-wide text-lg min-w-[150px]",
                                            !isFormValid() && "opacity-50 cursor-not-allowed grayscale"
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
                                                Save & Continue
                                            </>
                                        )}
                                    </Button>
                                </motion.div>
                            </div>
                        </form>
                    </Card>
                </Reveal>
            </motion.div>
        </Layout>
    );
};

export default BusinessSetup;
