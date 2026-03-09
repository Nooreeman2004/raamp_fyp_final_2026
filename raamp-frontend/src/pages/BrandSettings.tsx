import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "@/components/Layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import {
    Palette,
    Save,
    Upload,
    Trash2,
    Plus,
    Sparkles,
    RefreshCcw,
    Check,
    X,
    ImageIcon,
    Shield
} from "lucide-react";
import { toast as sonner } from "sonner";
import { useFormPersistence } from "@/hooks/useFormPersistence";
import { businessService } from "@/services/businessService";
import { authService } from "@/services/authService";
import { useAuth } from "@/hooks/useAuth";
import { useOnboardingStatus } from "@/hooks/useOnboardingStatus";
import { cn } from "@/lib/utils";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";

// Animation Imports
import { motion, AnimatePresence } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { BlurText } from "@/components/ui/text-reveal";
import { InputSpotlight } from "@/components/ui/input-spotlight";
import { MagneticButton } from "@/components/ui/magnetic-button";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

const PALETTE_TEMPLATES = [
    { name: "Neon Cyan", colors: ["#00E0D0", "#00A396", "#09151E", "#FFFFFF"], source: "template" },
    { name: "Deep Aurora", colors: ["#7928CA", "#FF0080", "#000000", "#FFFFFF"], source: "template" },
    { name: "Eco Leaf", colors: ["#059669", "#10B981", "#064E3B", "#FFFFFF"], source: "template" },
    { name: "Solar Orange", colors: ["#F59E0B", "#D97706", "#78350F", "#FFFFFF"], source: "template" },
    { name: "Midnight Steel", colors: ["#111827", "#374151", "#9CA3AF", "#FFFFFF"], source: "template" },
];

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const BrandSettings = () => {
    const navigate = useNavigate();
    const [isLoading, setIsLoading] = useState(false);
    const [isFetching, setIsFetching] = useState(true);
    const [isExtracting, setIsExtracting] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const [hasExistingData, setHasExistingData] = useState(false);
    const { refreshUser, user } = useAuth();
    const { isFullyOnboarded } = useOnboardingStatus();
    const fileInputRef = useRef<HTMLInputElement>(null);
    const logoRef = useRef<HTMLImageElement>(null);

    // OTP Dialog State
    const [showOtpDialog, setShowOtpDialog] = useState(false);
    const [otp, setOtp] = useState("");
    const [otpError, setOtpError] = useState("");

    // Use form persistence
    const { values: formData, handleChange, clearPersistence, setValues } = useFormPersistence("brand_settings_form", {
        brandName: "",
        tagline: "",
        primaryColor: "#00E0D0",
        secondaryColor: "#09151E",
        toneOfVoice: "",
        restaurant_theme: "",
        brandLogoUrl: "",
        brand_colors: ["#00E0D0", "#09151E"],
        palette_source: "custom"
    });

    const [touched, setTouched] = useState({
        brandName: false,
        restaurant_theme: false,
        toneOfVoice: false
    });

    useEffect(() => {
        const fetchBrandSettings = async () => {
            try {
                const data = await businessService.getBrandAlignment();
                if (data) {
                    setValues({
                        brandName: "",
                        tagline: data.tagline || "",
                        primaryColor: data.primary_color || "#00E0D0",
                        secondaryColor: data.secondary_color || "#09151E",
                        toneOfVoice: data.tone_of_voice || "",
                        restaurant_theme: data.restaurant_theme || "",
                        brandLogoUrl: data.brand_logo_url || "",
                        brand_colors: data.brand_colors && data.brand_colors.length > 0 ? data.brand_colors : ["#00E0D0", "#09151E"],
                        palette_source: data.palette_source || "custom"
                    });
                    
                    // Check if has meaningful data (theme, tone, or logo)
                    const hasData = !!(data.restaurant_theme || data.tone_of_voice || data.brand_logo_url);
                    setHasExistingData(hasData);
                    
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
                console.error("Failed to fetch brand settings:", error);
                // If fetch fails, allow editing (assume new user)
                setIsEditing(true);
            } finally {
                setIsFetching(false);
            }
        };
        fetchBrandSettings();
    }, [isFullyOnboarded]);

    const handleEdit = async () => {
        if (isEditing || !user?.email) return;

        try {
            // Send OTP to email
            await authService.sendProfileEditOtp({ email: user.email });
            sonner.info("Verification Required", {
                description: `A security code has been sent to ${user.email}`,
            });
            setShowOtpDialog(true);
        } catch (err: any) {
            const cooldownMsg = err?.errors?.cooldown || err?.errors?.message || err?.message;
            if (cooldownMsg) {
                sonner.error("Cooldown active", { description: cooldownMsg });
            } else {
                sonner.error("Error", { description: err?.message || 'Failed to send OTP' });
            }
        }
    };

    const handleVerifyOtp = async () => {
        if (!user?.email) return;
        
        setOtpError("");
        try {
            await authService.verifyProfileEditOtp({ email: user.email, code: otp });
            setShowOtpDialog(false);
            setIsEditing(true);
            setOtp("");
            sonner.success("Verified", {
                description: "You can now edit your brand settings",
            });
        } catch (err: any) {
            setOtpError(err?.message || "Invalid OTP. Please try again.");
        }
    };

    const handleLogoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const file = e.target.files[0];
            setIsLoading(true);
            try {
                const result = await businessService.uploadLogo(file);
                if (result.success) {
                    setValues({ ...formData, brandLogoUrl: result.logo_url });
                    sonner.success("Logo Uploaded & Preview Ready");
                }
            } catch (error) {
                console.error("Logo upload failed", error);
                sonner.error("Upload Failed");
            } finally {
                setIsLoading(false);
            }
        }
    };

    const extractColorsFromLogo = async () => {
        if (!formData.brandLogoUrl) {
            sonner.error("Missing Logo", { description: "Upload a logo first to extract colors." });
            return;
        }

        setIsExtracting(true);
        try {
            // Simplified color extraction using Canvas
            const img = new Image();
            img.crossOrigin = "Anonymous";
            // Prefix with API_BASE_URL if it's a relative path starting with /api
            const fullUrl = formData.brandLogoUrl.startsWith("/api")
                ? `${API_BASE_URL}${formData.brandLogoUrl}`
                : formData.brandLogoUrl;

            img.src = fullUrl;

            await new Promise((resolve, reject) => {
                img.onload = resolve;
                img.onerror = reject;
            });

            const canvas = document.createElement("canvas");
            const ctx = canvas.getContext("2d");
            if (!ctx) throw new Error("Could not get canvas context");

            canvas.width = img.width;
            canvas.height = img.height;
            ctx.drawImage(img, 0, 0);

            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
            const colorMap: { [key: string]: number } = {};

            // Sample pixels (every 10th to be faster)
            for (let i = 0; i < imageData.length; i += 40) {
                const r = imageData[i];
                const g = imageData[i + 1];
                const b = imageData[i + 2];
                const a = imageData[i + 3];

                // Skip transparent or too dark/light pixels
                if (a < 128) continue;

                const hex = `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1).toUpperCase()}`;
                colorMap[hex] = (colorMap[hex] || 0) + 1;
            }

            // Sort by frequency and take top 4
            const sortedColors = Object.entries(colorMap)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 4)
                .map(entry => entry[0]);

            if (sortedColors.length > 0) {
                setValues({
                    ...formData,
                    brand_colors: sortedColors,
                    primaryColor: sortedColors[0],
                    secondaryColor: sortedColors[1] || formData.secondaryColor,
                    palette_source: "logo"
                });
                sonner.success("Colors Extracted", { description: "Primary and secondary colors updated based on your logo." });
            }
        } catch (error) {
            console.error("Extraction failed", error);
            sonner.error("Extraction Error", { description: "Failed to read logo data. Ensure the server permits CORS if it's an external URL." });
        } finally {
            setIsExtracting(false);
        }
    };

    const applyTemplate = (template: typeof PALETTE_TEMPLATES[0]) => {
        setValues({
            ...formData,
            brand_colors: [...template.colors],
            primaryColor: template.colors[0],
            secondaryColor: template.colors[1],
            palette_source: "template"
        });
        sonner.success(`Applied ${template.name}`);
    };

    const addColor = () => {
        if (formData.brand_colors.length >= 6) {
            sonner.warning("Max Colors Reached", { description: "You can keep up to 6 colors in your palette." });
            return;
        }
        setValues({ ...formData, brand_colors: [...formData.brand_colors, "#CCCCCC"] });
    };

    const updateColor = (index: number, value: string) => {
        const newColors = [...formData.brand_colors];
        newColors[index] = value;
        setValues({ ...formData, brand_colors: newColors });
    };

    const removeColor = (index: number) => {
        if (formData.brand_colors.length <= 1) return;
        const newColors = formData.brand_colors.filter((_, i) => i !== index);
        setValues({ ...formData, brand_colors: newColors });
    };

    const isFormValid = () => {
        return (
            formData.restaurant_theme?.trim().length > 0 &&
            formData.toneOfVoice?.trim().length > 0 &&
            formData.brandLogoUrl
        );
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        setTouched({
            brandName: true,
            restaurant_theme: true,
            toneOfVoice: true
        });

        if (!isFormValid()) {
            sonner.error("Incomplete Setup", {
                description: "Logo, Theme, and Tone of Voice parameters are required.",
            });
            return;
        }

        setIsLoading(true);

        try {
            await businessService.saveBrandAlignment({
                brand_logo_url: formData.brandLogoUrl,
                primary_color: formData.brand_colors[0] || formData.primaryColor,
                secondary_color: formData.brand_colors[1] || formData.secondaryColor,
                tagline: formData.tagline,
                tone_of_voice: formData.toneOfVoice,
                restaurant_theme: formData.restaurant_theme,
                brand_colors: formData.brand_colors,
                palette_source: formData.palette_source
            });

            clearPersistence();
            await refreshUser();
            
            // Disable editing after successful save
            if (isFullyOnboarded) {
                setIsEditing(false);
            }

            sonner.success("Brand DNA Locked In", {
                description: "Your autonomous marketing identity is ready and synchronized.",
            });

            // Only navigate to dashboard if user is NOT fully onboarded (new user in onboarding flow)
            if (!isFullyOnboarded) {
                setTimeout(() => navigate("/dashboard"), 1000);
            }
        } catch (error) {
            console.error("Failed to save brand settings", error);
            sonner.error("Sync Failed");
        } finally {
            setIsLoading(false);
        }
    };

    if (isFetching) {
        return (
            <Layout>
                <div className="h-[60vh] flex items-center justify-center">
                    <RefreshCcw className="w-8 h-8 animate-spin text-primary" />
                </div>
            </Layout>
        );
    }

    return (
        <Layout breadcrumbItems={[{ label: "Profile", href: "/profile/user" }, { label: "Brand Settings" }]}>
            <motion.div
                className="space-y-6 max-w-5xl mx-auto pb-20"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
            >
                <Reveal variant="blurInUp">
                    <div className="flex items-center justify-between gap-4 mb-8">
                        <div className="flex items-center gap-4">
                            <div className="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center border border-primary/20">
                                <Palette className="w-7 h-7 text-primary" />
                            </div>
                            <div>
                                <h1 className="text-3xl font-bold font-bebas tracking-wide">
                                    <BlurText text="Brand Identity Matrix" />
                                </h1>
                                <p className="text-muted-foreground font-mono text-xs uppercase tracking-widest">
                                    Configure the DNA of your autonomous marketing agent.
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

                <div className="grid gap-6 lg:grid-cols-3">
                    {/* Left Column: Assets & Colors */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Logo Management */}
                        <Card className="p-6 bg-card/70 backdrop-blur-sm border-white/5 relative overflow-hidden group">
                            <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
                                <ImageIcon size={80} />
                            </div>

                            <Label className="text-[10px] font-mono text-muted-foreground uppercase tracking-[0.2em] mb-4 block">
                                Visual DNA (Logo) <span className="text-red-500">*</span>
                            </Label>

                            <div className="flex flex-col md:flex-row gap-6 items-center">
                                <div className="relative w-full md:w-56 h-40 rounded-xl bg-black/40 border border-white/10 flex items-center justify-center p-4 overflow-hidden group-hover:border-primary/30 transition-all duration-500">
                                    {formData.brandLogoUrl ? (
                                        <img
                                            src={formData.brandLogoUrl.startsWith("/api") ? `${API_BASE_URL}${formData.brandLogoUrl}` : formData.brandLogoUrl}
                                            alt="Logo Preview"
                                            className="max-w-full max-h-full object-contain z-10 drop-shadow-2xl"
                                            ref={logoRef}
                                        />
                                    ) : (
                                        <div className="flex flex-col items-center gap-2 text-muted-foreground">
                                            <Upload size={24} className="animate-pulse" />
                                            <p className="text-[10px] uppercase font-mono">No Asset Detected</p>
                                        </div>
                                    )}
                                    <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                                </div>

                                <div className="flex-1 space-y-4 w-full">
                                    <div className="flex flex-wrap gap-2">
                                        <input
                                            type="file"
                                            ref={fileInputRef}
                                            className="hidden"
                                            accept="image/*"
                                            onChange={handleLogoUpload}
                                        />
                                        <Button
                                            onClick={() => fileInputRef.current?.click()}
                                            variant="outline"
                                            disabled={!isEditing}
                                            className={cn(
                                                "font-mono text-[11px] uppercase tracking-tighter h-9 gap-2 border-white/10 hover:border-primary/50",
                                                !isEditing && "opacity-50 cursor-not-allowed"
                                            )}
                                        >
                                            <Upload size={14} />
                                            {formData.brandLogoUrl ? "Change Logo" : "Upload Logo"}
                                        </Button>

                                        {formData.brandLogoUrl && (
                                            <Button
                                                onClick={extractColorsFromLogo}
                                                disabled={isExtracting || !isEditing}
                                                variant="secondary"
                                                className={cn(
                                                    "font-mono text-[11px] uppercase tracking-tighter h-9 gap-2 bg-primary/10 text-primary hover:bg-primary/20 border-none",
                                                    !isEditing && "opacity-50 cursor-not-allowed"
                                                )}
                                            >
                                                {isExtracting ? <RefreshCcw size={14} className="animate-spin" /> : <Sparkles size={14} />}
                                                Extract Colors
                                            </Button>
                                        )}
                                    </div>
                                    <p className="text-[10px] text-muted-foreground leading-relaxed font-mono">
                                        * Transparent PNG or vector SVG recommended for best AI generation results.
                                    </p>
                                </div>
                            </div>
                        </Card>

                        {/* Color Management */}
                        <Card className="p-6 bg-card/70 backdrop-blur-sm border-white/5">
                            <div className="flex items-center justify-between mb-6">
                                <Label className="text-[10px] font-mono text-muted-foreground uppercase tracking-[0.2em]">Color Frequency Matrix</Label>
                                <div className="flex items-center gap-2">
                                    <span className={cn(
                                        "text-[9px] font-mono px-2 py-0.5 rounded-full uppercase tracking-tighter",
                                        formData.palette_source === "logo" ? "bg-primary/20 text-primary border border-primary/20" :
                                            formData.palette_source === "template" ? "bg-blue-500/20 text-blue-400 border border-blue-500/20" :
                                                "bg-neutral-800 text-neutral-400"
                                    )}>
                                        Source: {formData.palette_source}
                                    </span>
                                </div>
                            </div>

                            <div className="space-y-8">
                                {/* Current Palette */}
                                <div className="flex flex-wrap gap-4">
                                    <AnimatePresence mode="popLayout">
                                        {formData.brand_colors.map((color, index) => (
                                            <motion.div
                                                key={`color-${index}`}
                                                layout
                                                initial={{ opacity: 0, scale: 0.8 }}
                                                animate={{ opacity: 1, scale: 1 }}
                                                exit={{ opacity: 0, scale: 0.8 }}
                                                className="group relative"
                                            >
                                                <div
                                                    className="w-16 h-16 rounded-2xl border border-white/5 shadow-xl cursor-crosshair relative overflow-hidden ring-offset-2 ring-primary/20 transition-all hover:ring-2"
                                                    style={{ backgroundColor: color }}
                                                >
                                                    <Input
                                                        type="color"
                                                        value={color}
                                                        onChange={(e) => updateColor(index, e.target.value)}
                                                        disabled={!isEditing}
                                                        className={cn(
                                                            "absolute inset-0 opacity-0 cursor-pointer h-full w-full",
                                                            !isEditing && "cursor-not-allowed"
                                                        )}
                                                    />
                                                </div>
                                                <div className="mt-2 text-center">
                                                    <span className="text-[9px] font-mono uppercase text-muted-foreground tracking-tighter block mb-1">
                                                        {index === 0 ? "PRIMARY" : index === 1 ? "SECONDARY" : "ACCENT"}
                                                    </span>
                                                    <Input
                                                        value={color}
                                                        onChange={(e) => updateColor(index, e.target.value)}
                                                        readOnly={!isEditing}
                                                        className={cn(
                                                            "h-6 w-16 text-[9px] font-mono text-center bg-black/40 border-white/5 p-0",
                                                            !isEditing && "cursor-not-allowed opacity-60"
                                                        )}
                                                    />
                                                </div>
                                                {index > 1 && isEditing && (
                                                    <button
                                                        onClick={() => removeColor(index)}
                                                        className="absolute -top-1 -right-1 w-5 h-5 bg-destructive text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity z-20 shadow-lg"
                                                    >
                                                        <X size={10} />
                                                    </button>
                                                )}
                                            </motion.div>
                                        ))}

                                        {formData.brand_colors.length < 6 && isEditing && (
                                            <motion.button
                                                layout
                                                onClick={addColor}
                                                className="w-16 h-16 rounded-2xl border-2 border-dashed border-white/10 flex flex-col items-center justify-center gap-1 hover:border-primary/50 hover:bg-primary/5 transition-all text-muted-foreground hover:text-primary group"
                                            >
                                                <Plus size={16} />
                                                <span className="text-[8px] font-mono uppercase tracking-tighter">Add</span>
                                            </motion.button>
                                        )}
                                    </AnimatePresence>
                                </div>

                                {/* Templates */}
                                <div className="pt-4 border-t border-white/5">
                                    <Label className="text-[9px] font-mono text-muted-foreground/60 uppercase tracking-[0.2em] mb-4 block">Engineered Presets</Label>
                                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
                                        {PALETTE_TEMPLATES.map((tmpl) => (
                                            <button
                                                key={tmpl.name}
                                                onClick={() => applyTemplate(tmpl)}
                                                disabled={!isEditing}
                                                className={cn(
                                                    "group p-2 rounded-xl bg-black/20 border border-white/5 hover:border-white/10 transition-all text-left",
                                                    !isEditing && "opacity-50 cursor-not-allowed"
                                                )}
                                            >
                                                <div className="flex h-3 w-full rounded-sm overflow-hidden mb-2">
                                                    {tmpl.colors.map((c, i) => (
                                                        <div key={i} className="flex-1" style={{ backgroundColor: c }} />
                                                    ))}
                                                </div>
                                                <span className="text-[8px] font-mono text-muted-foreground uppercase truncate block group-hover:text-white transition-colors">{tmpl.name}</span>
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </Card>
                    </div>

                    {/* Right Column: AI Parameters */}
                    <div className="space-y-6">
                        <Card className="p-6 bg-card/70 backdrop-blur-sm border-white/5 h-full">
                            <Label className="text-[10px] font-mono text-muted-foreground uppercase tracking-[0.2em] mb-6 block">Semantic Parameters</Label>

                            <form onSubmit={handleSubmit} className="space-y-6">
                                <div className="space-y-2">
                                    <Label className="text-[10px] font-mono text-muted-foreground uppercase">Tagline</Label>
                                    <InputSpotlight
                                        name="tagline"
                                        value={formData.tagline}
                                        onChange={handleChange}
                                        readOnly={!isEditing}
                                        placeholder="Enter the catchphrase"
                                        className={cn(
                                            "bg-black/40 h-10 text-xs font-mono",
                                            !isEditing && "cursor-not-allowed opacity-60"
                                        )}
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label className="text-[10px] font-mono text-muted-foreground uppercase">
                                        Restaurant Theme <span className="text-red-500">*</span>
                                    </Label>
                                    <InputSpotlight
                                        name="restaurant_theme"
                                        value={formData.restaurant_theme}
                                        onChange={handleChange}
                                        onBlur={() => setTouched(prev => ({ ...prev, restaurant_theme: true }))}
                                        readOnly={!isEditing}
                                        placeholder="e.g. Minimalist Tokyo Street"
                                        className={cn(
                                            "bg-black/40 h-10 text-xs font-mono",
                                            touched.restaurant_theme && !formData.restaurant_theme && "border-destructive/50",
                                            !isEditing && "cursor-not-allowed opacity-60"
                                        )}
                                    />
                                    {touched.restaurant_theme && !formData.restaurant_theme && (
                                        <p className="text-[9px] text-destructive font-mono uppercase tracking-tighter mt-1">Input Required</p>
                                    )}
                                </div>

                                <div className="space-y-2">
                                    <Label className="text-[10px] font-mono text-muted-foreground uppercase">
                                        Tone of Voice <span className="text-red-500">*</span>
                                    </Label>
                                    <Textarea
                                        name="toneOfVoice"
                                        value={formData.toneOfVoice}
                                        onChange={handleChange}
                                        onBlur={() => setTouched(prev => ({ ...prev, toneOfVoice: true }))}
                                        readOnly={!isEditing}
                                        className={cn(
                                            "w-full h-40 bg-black/40 border-white/10 resize-none font-mono text-[11px] p-4 focus:border-primary/50 transition-colors scrollbar-none",
                                            touched.toneOfVoice && !formData.toneOfVoice && "border-destructive/50",
                                            !isEditing && "cursor-not-allowed opacity-60"
                                        )}
                                        placeholder="How should your AI speak? Friendly, Elite, Sarcastic, Professional..."
                                    />
                                    {touched.toneOfVoice && !formData.toneOfVoice && (
                                        <p className="text-[9px] text-destructive font-mono uppercase tracking-tighter mt-1">Semantics Required</p>
                                    )}
                                </div>

                                <TooltipProvider>
                                    <Tooltip>
                                        <TooltipTrigger asChild>
                                            <div className="pt-4">
                                                <MagneticButton
                                                    type="submit"
                                                    disabled={isLoading || !isFormValid() || !isEditing}
                                                    className={cn(
                                                        "w-full bg-primary text-black font-bold h-12 rounded-xl shadow-[0_0_30px_rgba(0,224,208,0.2)]",
                                                        (!isFormValid() || isLoading || !isEditing) && "opacity-20 grayscale-0"
                                                    )}
                                                >
                                                    {isLoading ? (
                                                        <RefreshCcw className="w-5 h-5 animate-spin" />
                                                    ) : (
                                                        <div className="flex items-center justify-center gap-2 font-bebas tracking-widest text-lg">
                                                            <Check size={20} strokeWidth={3} />
                                                            {isFullyOnboarded ? "Save Changes" : "Commit Matrix"}
                                                        </div>
                                                    )}
                                                </MagneticButton>
                                            </div>
                                        </TooltipTrigger>
                                        {!isFormValid() && (
                                            <TooltipContent className="bg-destructive text-destructive-foreground border-none font-mono text-[10px]">
                                                IDENTIFY CORE PARAMETERS TO CONTINUE
                                            </TooltipContent>
                                        )}
                                    </Tooltip>
                                </TooltipProvider>
                            </form>
                        </Card>
                    </div>
                </div>

                {/* OTP Verification Dialog */}
                <Dialog open={showOtpDialog} onOpenChange={setShowOtpDialog}>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Verify Your Identity</DialogTitle>
                            <DialogDescription>
                                Enter the verification code sent to your email to unlock editing.
                            </DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4 py-4">
                            <div className="space-y-2">
                                <Label htmlFor="otp">Verification Code</Label>
                                <Input
                                    id="otp"
                                    value={otp}
                                    onChange={(e) => {
                                        setOtp(e.target.value);
                                        setOtpError("");
                                    }}
                                    placeholder="Enter 6-digit code"
                                    maxLength={6}
                                    className={cn("font-mono", otpError && "border-destructive")}
                                />
                                {otpError && (
                                    <p className="text-sm text-destructive">{otpError}</p>
                                )}
                            </div>
                        </div>
                        <DialogFooter>
                            <Button variant="outline" onClick={() => {
                                setShowOtpDialog(false);
                                setOtp("");
                                setOtpError("");
                            }}>
                                Cancel
                            </Button>
                            <Button onClick={handleVerifyOtp} disabled={otp.length !== 6}>
                                Verify
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </motion.div>
        </Layout>
    );
};

export default BrandSettings;
