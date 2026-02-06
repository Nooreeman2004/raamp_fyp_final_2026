import { useState, useEffect, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import Layout from "@/components/Layout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Link2, Check, ArrowRight, RefreshCw, MapPin, Search, Building2, Globe, Phone, Save, X } from "lucide-react";
import { toast } from "sonner";
import { apiClient } from "@/services/api";
import { businessService } from "@/services/businessService";
import { cn } from "@/lib/utils";
import LocationPicker from "@/components/LocationPicker";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog";

// Animation Imports
import { motion, AnimatePresence } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeInUp, hoverScale } from "@/utils/animations";
import { BlurText } from "@/components/ui/text-reveal";

interface OnboardingStatus {
    facebook_connected: boolean;
    instagram_connected: boolean;
    google_maps_connected: boolean;
    ready_to_continue: boolean;
    redirect: string | null;
}

const Onboarding = () => {
    const { refreshUser, user } = useAuth();
    const navigate = useNavigate();
    const [status, setStatus] = useState<OnboardingStatus>({
        facebook_connected: false,
        instagram_connected: false,
        google_maps_connected: false,
        ready_to_continue: false,
        redirect: null
    });
    const [loading, setLoading] = useState(true);
    const [connecting, setConnecting] = useState<string | null>(null);
    const [isSavingLocation, setIsSavingLocation] = useState(false);
    const [disconnectDialogOpen, setDisconnectDialogOpen] = useState(false);
    const [platformToDisconnect, setPlatformToDisconnect] = useState<'facebook' | 'instagram' | null>(null);
    const [disconnecting, setDisconnecting] = useState(false);

    // Location States
    const [locationData, setLocationData] = useState({
        address: "",
        city: "",
        country: "",
        latitude: 0,
        longitude: 0,
        place_id: ""
    });
    const [suggestions, setSuggestions] = useState<LocationSuggestion[]>([]);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [isTyping, setIsTyping] = useState(false);
    const [showLocationForm, setShowLocationForm] = useState(false);

    interface LocationSuggestion {
        place_id: string;
        name: string;
        formatted_address: string;
        lat: number;
        lng: number;
    }

    const fetchStatus = useCallback(async () => {
        try {
            const response = await apiClient.get<OnboardingStatus>('/profile/onboarding/status');
            setStatus(response);
        } catch (error) {
            console.error("Failed to fetch onboarding status", error);
        } finally {
            setLoading(false);
        }
    }, []);

    const fetchCurrentLocation = useCallback(async () => {
        try {
            const data = await businessService.getHyperlocalSetup();
            if (data && data.has_setup) {
                setLocationData({
                    address: data.formatted_address || "",
                    city: data.city || "",
                    country: data.country || "",
                    latitude: data.latitude || 0,
                    longitude: data.longitude || 0,
                    place_id: data.google_place_id || ""
                });
            }
        } catch (error: any) {
            // 404 is expected when no location data exists yet - not an error
            if (error?.response?.status !== 404 && error?.status !== 404) {
                console.error("Failed to fetch location data", error);
            }
        }
    }, []);

    useEffect(() => {
        fetchStatus();
        fetchCurrentLocation();

        // Listen for messages from auth popups
        const handleMessage = (event: MessageEvent) => {
            if (event.data && (event.data.provider === 'facebook' || event.data.provider === 'instagram')) {
                if (event.data.success) {
                    toast.success("Connected!", {
                        description: `Successfully connected to ${event.data.provider}.`,
                    });
                    fetchStatus(); // Refresh status
                    refreshUser(); // Refresh global auth status
                } else if (event.data.error) {
                    toast.error("Connection Failed", {
                        description: event.data.error,
                    });
                }
            }
        };

        window.addEventListener('message', handleMessage);
        return () => window.removeEventListener('message', handleMessage);
    }, [fetchStatus, fetchCurrentLocation, refreshUser]);

    const handleConnect = async (platform: 'facebook' | 'instagram' | 'google') => {
        setConnecting(platform);
        if (platform === 'facebook') {
            const width = 600;
            const height = 700;
            const left = window.screen.width / 2 - width / 2;
            const top = window.screen.height / 2 - height / 2;

            window.open('/api/profile/onboarding/facebook/auth', 'facebook_auth', `width=${width},height=${height},left=${left},top=${top}`);
        } else if (platform === 'instagram') {
            if (!status.facebook_connected) {
                toast.error("Prerequisite Required", {
                    description: "Please connect Facebook Ads first.",
                });
                return;
            }
            const width = 600;
            const height = 800;
            const left = window.screen.width / 2 - width / 2;
            const top = window.screen.height / 2 - height / 2;
            window.open('/api/profile/onboarding/instagram/auth', 'instagram_auth', `width=${width},height=${height},left=${left},top=${top}`);
        } else if (platform === 'google') {
            setShowLocationForm(!showLocationForm);
        }
        setConnecting(null);
    };

    const handleDisconnectClick = (platform: 'facebook' | 'instagram') => {
        setPlatformToDisconnect(platform);
        setDisconnectDialogOpen(true);
    };

    const handleDisconnectConfirm = async () => {
        if (!platformToDisconnect) return;

        setDisconnecting(true);
        try {
            const response = await apiClient.delete(`/profile/onboarding/${platformToDisconnect}/disconnect`);
            
            toast.success("Disconnected Successfully", {
                description: `${platformToDisconnect === 'facebook' ? 'Facebook' : 'Instagram'} account has been disconnected.`,
            });
            
            await fetchStatus();
            await refreshUser();
        } catch (error: any) {
            console.error(`Disconnect ${platformToDisconnect} error:`, error);
            const errorMessage = error?.response?.data?.detail || error?.message || `Failed to disconnect ${platformToDisconnect}`;
            toast.error("Disconnect Failed", {
                description: errorMessage,
            });
        } finally {
            setDisconnecting(false);
            setDisconnectDialogOpen(false);
            setPlatformToDisconnect(null);
        }
    };

    const fetchSuggestions = async (query: string) => {
        if (!query || query.length < 3) {
            setSuggestions([]);
            return;
        }
        try {
            const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || '/api'}/maps/search?query=${encodeURIComponent(query)}`);
            if (response.ok) {
                const data = await response.json();
                setSuggestions(data);
                setShowSuggestions(true);
            }
        } catch (error) {
            console.error("Failed to fetch suggestions", error);
        }
    };

    // Debounce suggestions
    useEffect(() => {
        const timer = setTimeout(() => {
            if (isTyping) {
                fetchSuggestions(locationData.address);
            }
        }, 500);
        return () => clearTimeout(timer);
    }, [locationData.address, isTyping]);

    const handleSuggestionSelect = (suggestion: LocationSuggestion) => {
        setLocationData(prev => ({
            ...prev,
            address: suggestion.formatted_address || suggestion.name,
            latitude: suggestion.lat,
            longitude: suggestion.lng,
            place_id: suggestion.place_id || ""
        }));

        setShowSuggestions(false);
        setIsTyping(false);
        toast.success("Location Selected", {
            description: `Selected: ${suggestion.name}`,
        });
    };

    const handleSaveLocation = async () => {
        if (!locationData.address || locationData.latitude === 0) {
            toast.error("Incomplete Location", {
                description: "Please select a location and pin it on the map.",
            });
            return;
        }

        setIsSavingLocation(true);
        try {
            // Try to get existing setup data, but provide defaults if it doesn't exist
            let business_name = user?.company || "My Business"; // Use user's company name if available
            let business_type = "General";
            
            try {
                const currentSetup = await businessService.getHyperlocalSetup();
                if (currentSetup.business_name) business_name = currentSetup.business_name;
                if (currentSetup.business_type) business_type = currentSetup.business_type;
            } catch (error: any) {
                // If 404, that's fine - we'll use the defaults from above
                if (error?.response?.status !== 404 && error?.status !== 404) {
                    throw error; // Re-throw if it's not a 404
                }
            }
            
            await businessService.saveHyperlocalSetup({
                business_name: business_name,
                business_type: business_type,
                formatted_address: locationData.address,
                latitude: locationData.latitude,
                longitude: locationData.longitude,
                place_id: locationData.place_id,
                city: locationData.city,
                country: locationData.country
            });

            toast.success("Location Synced", {
                description: "Your business coordinates have been locked.",
            });
            await fetchStatus();
            await refreshUser(); // Refresh user context to update connection flags
            setShowLocationForm(false);
        } catch (error: unknown) {
            const errorMessage = error instanceof Error ? error.message : "Unable to save location.";
            toast.error("Save Failed", {
                description: errorMessage,
            });
            console.error("Save location error:", error);
        } finally {
            setIsSavingLocation(false);
        }
    };

    return (
        <Layout breadcrumbItems={[{ label: "Profile", href: "/profile/user" }, { label: "Integrations" }]}>
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
                                <Link2 className="w-7 h-7 text-primary" />
                            </div>
                            <div>
                                <h1 className="text-3xl font-bold font-bebas tracking-wide">
                                    <BlurText text="Integrations & Onboarding" />
                                </h1>
                                <p className="text-muted-foreground font-mono text-sm">
                                    Connect your social media and ad accounts
                                </p>
                            </div>
                        </div>
                        <Button variant="outline" size="icon" onClick={fetchStatus} disabled={loading} title="Refresh Status">
                            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                        </Button>
                    </div>
                </Reveal>

                <motion.div
                    className="grid gap-4"
                    variants={staggerContainer}
                    initial="hidden"
                    animate="visible"
                >
                    <AnimatePresence mode="popLayout">
                        {loading ? (
                            Array.from({ length: 3 }).map((_, i) => (
                                <motion.div
                                    key={`skeleton-${i}`}
                                    variants={fadeInUp}
                                    exit={{ opacity: 0, scale: 0.95 }}
                                >
                                    <div className="h-[96px] w-full bg-card/40 rounded-xl border border-white/5 animate-pulse flex items-center px-6 gap-4">
                                        <div className="w-12 h-12 rounded-full bg-white/5" />
                                        <div className="flex-1 space-y-2">
                                            <div className="h-4 w-32 bg-white/5 rounded" />
                                            <div className="h-3 w-48 bg-white/5 rounded" />
                                        </div>
                                        <div className="h-10 w-24 bg-white/5 rounded" />
                                    </div>
                                </motion.div>
                            ))
                        ) : (
                            <>
                                {/* Facebook */}
                                <motion.div variants={fadeInUp} key="facebook">
                                    <Card className="p-6 bg-card/70 backdrop-blur-sm border-primary/10 flex items-center justify-between group">
                                        <div className="flex items-center gap-4">
                                            <div className={cn(
                                                 connecting === 'facebook' ? "bg-blue-600/40 animate-pulse scale-110" : "bg-blue-600/20"
                                            )}>
                                                <span className="text-blue-500 font-bold text-xl">f</span>
                                            </div>
                                            <div>
                                                <h3 className="font-bold font-bebas tracking-wide text-lg">Facebook Ads</h3>
                                                <p className="text-sm text-muted-foreground font-mono">Connect your ad account</p>
                                            </div>
                                        </div>
                                        <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                                            {status.facebook_connected ? (
                                                <Button
                                                    variant="outline"
                                                    className="border-emerald-500 text-emerald-500 hover:bg-emerald-500/10 min-w-[120px]"
                                                    onClick={() => handleDisconnectClick('facebook')}
                                                    disabled={disconnecting}
                                                >
                                                    <Check className="w-4 h-4 mr-2" />
                                                    Disconnect
                                                </Button>
                                            ) : (
                                                <Button
                                                    variant="default"
                                                    className="min-w-[100px] transition-all duration-300"
                                                    onClick={() => handleConnect('facebook')}
                                                    disabled={loading || connecting === 'facebook'}
                                                >
                                                    {connecting === 'facebook' ? (
                                                        <span className="flex items-center gap-2">
                                                            <RefreshCw className="w-4 h-4 animate-spin" />
                                                            Connecting
                                                        </span>
                                                    ) : (
                                                        "Connect"
                                                    )}
                                                </Button>
                                            )}
                                        </motion.div>
                                    </Card>
                                </motion.div>

                                {/* Instagram */}
                                <motion.div variants={fadeInUp} key="instagram">
                                    <Card className="p-6 bg-card/70 backdrop-blur-sm border-primary/10 flex items-center justify-between">
                                        <div className="flex items-center gap-4">
                                            <div className={cn(
                                                "w-12 h-12 rounded-full flex items-center justify-center transition-all duration-500",
                                                connecting === 'instagram' ? "bg-pink-600/40 animate-pulse scale-110" : "bg-pink-600/20"
                                            )}>
                                                <span className="text-pink-500 font-bold text-xl">Ig</span>
                                            </div>
                                            <div>
                                                <h3 className="font-bold font-bebas tracking-wide text-lg">Instagram</h3>
                                                <div className="flex flex-col">
                                                    <p className="text-sm text-muted-foreground font-mono">Connect for organic insights</p>
                                                    {!status.facebook_connected && (
                                                        <span className="text-[10px] text-amber-500/80 uppercase mt-1 font-mono">Requires Facebook Ads Connection First</span>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                        <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                                            {status.instagram_connected ? (
                                                <Button
                                                    variant="outline"
                                                    className="border-emerald-500 text-emerald-500 hover:bg-emerald-500/10 min-w-[120px]"
                                                    onClick={() => handleDisconnectClick('instagram')}
                                                    disabled={disconnecting}
                                                >
                                                    <Check className="w-4 h-4 mr-2" />
                                                    Disconnect
                                                </Button>
                                            ) : (
                                                <Button
                                                    variant="default"
                                                    className="min-w-[100px] transition-all duration-300"
                                                    onClick={() => handleConnect('instagram')}
                                                    disabled={loading || !status.facebook_connected || connecting === 'instagram'}
                                                >
                                                    {connecting === 'instagram' ? (
                                                        <span className="flex items-center gap-2">
                                                            <RefreshCw className="w-4 h-4 animate-spin" />
                                                            Connecting
                                                        </span>
                                                    ) : (
                                                        "Connect"
                                                    )}
                                                </Button>
                                            )}
                                        </motion.div>
                                    </Card>
                                </motion.div>

                                {/* Google */}
                                <motion.div variants={fadeInUp} key="google">
                                    <Card className={cn(
                                        "p-6 bg-card/70 backdrop-blur-sm border-primary/10 transition-all duration-500 overflow-hidden",
                                        showLocationForm ? "ring-1 ring-primary/30" : ""
                                    )}>
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-4">
                                                <div className="w-12 h-12 rounded-full bg-red-600/20 flex items-center justify-center">
                                                    <span className="text-red-500 font-bold text-xl">G</span>
                                                </div>
                                                <div>
                                                    <h3 className="font-bold font-bebas tracking-wide text-lg">Google Business</h3>
                                                    <p className="text-sm text-muted-foreground font-mono">Connect for search intent</p>
                                                </div>
                                            </div>
                                            <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                                                <Button
                                                    variant={status.google_maps_connected ? "outline" : "default"}
                                                    className={cn(
                                                        "min-w-[100px]",
                                                        status.google_maps_connected ? "border-emerald-500 text-emerald-500" : ""
                                                    )}
                                                    onClick={() => !status.google_maps_connected && setShowLocationForm(!showLocationForm)}
                                                    disabled={loading || status.google_maps_connected}
                                                >
                                                    {status.google_maps_connected ? (
                                                        <>
                                                            <Check className="w-4 h-4 mr-2" />
                                                            Connected
                                                        </>
                                                    ) : showLocationForm ? "Cancel" : "Configure"}
                                                </Button>
                                            </motion.div>
                                        </div>

                                        <AnimatePresence>
                                            {showLocationForm && (
                                                <motion.div
                                                    initial={{ height: 0, opacity: 0 }}
                                                    animate={{ height: "auto", opacity: 1 }}
                                                    exit={{ height: 0, opacity: 0 }}
                                                    transition={{ duration: 0.3 }}
                                                    className="mt-6 pt-6 border-t border-primary/20 space-y-4 relative"
                                                >
                                                    <div className="space-y-2 relative">
                                                        <Label className="font-mono text-xs">Search Location</Label>
                                                        <div className="relative">
                                                            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground z-10" />
                                                            <Input
                                                                className="pl-9 bg-background/50 font-mono ring-1 ring-primary/10 focus:ring-primary/30 transition-all"
                                                                placeholder="Search for your business..."
                                                                value={locationData.address}
                                                                onChange={(e) => {
                                                                    setLocationData(prev => ({ ...prev, address: e.target.value }));
                                                                    setIsTyping(true);
                                                                    if (!e.target.value) setShowSuggestions(false);
                                                                }}
                                                                onFocus={() => {
                                                                    if (suggestions.length > 0) setShowSuggestions(true);
                                                                }}
                                                            />
                                                        </div>

                                                        {showSuggestions && suggestions.length > 0 && (
                                                            <div className="absolute z-50 w-full mt-1 bg-card/95 border border-primary/30 rounded-md shadow-[0_0_20px_rgba(0,224,208,0.2)] overflow-hidden backdrop-blur-xl">
                                                                {suggestions.map((s, i) => (
                                                                    <button
                                                                        key={i}
                                                                        type="button"
                                                                        className="w-full text-left px-4 py-2 hover:bg-primary/10 transition-colors text-sm border-b border-primary/10 last:border-0"
                                                                        onClick={() => handleSuggestionSelect(s)}
                                                                    >
                                                                        <div className="font-medium text-white">{s.name}</div>
                                                                        <div className="text-xs text-muted-foreground truncate">{s.formatted_address}</div>
                                                                    </button>
                                                                ))}
                                                            </div>
                                                        )}
                                                    </div>

                                                    <div className="grid grid-cols-2 gap-4">
                                                        <div className="space-y-2">
                                                            <Label className="font-mono text-xs">City</Label>
                                                            <Input
                                                                className="bg-background/50 font-mono"
                                                                placeholder="City"
                                                                value={locationData.city}
                                                                onChange={(e) => setLocationData(prev => ({ ...prev, city: e.target.value }))}
                                                            />
                                                        </div>
                                                        <div className="space-y-2">
                                                            <Label className="font-mono text-xs">Country</Label>
                                                            <Input
                                                                className="bg-background/50 font-mono"
                                                                placeholder="Country"
                                                                value={locationData.country}
                                                                onChange={(e) => setLocationData(prev => ({ ...prev, country: e.target.value }))}
                                                            />
                                                        </div>
                                                    </div>

                                                    <div className="space-y-2">
                                                        <Label className="font-mono text-xs">Pin Precise Location</Label>
                                                        <LocationPicker
                                                            initialLat={locationData.latitude}
                                                            initialLng={locationData.longitude}
                                                            onLocationSelect={(lat, lng) => {
                                                                setLocationData(prev => ({ ...prev, latitude: lat, longitude: lng }));
                                                            }}
                                                        />
                                                    </div>

                                                    <div className="flex justify-end pt-2">
                                                        <Button
                                                            onClick={handleSaveLocation}
                                                            disabled={isSavingLocation || !locationData.address || locationData.latitude === 0}
                                                            className="font-bebas tracking-wide"
                                                        >
                                                            {isSavingLocation ? (
                                                                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                                                            ) : (
                                                                <Save className="w-4 h-4 mr-2" />
                                                            )}
                                                            Save Location
                                                        </Button>
                                                    </div>
                                                </motion.div>
                                            )}
                                        </AnimatePresence>
                                    </Card>
                                </motion.div>
                            </>
                        )}
                    </AnimatePresence>
                </motion.div>

                <Reveal variant="fadeInUp" delay={0.4}>
                    <div className="flex justify-end">
                        <Button
                            variant="default"
                            className="gap-2 font-bebas text-xl bg-primary text-black hover:bg-primary/90 px-8 py-6 h-auto tracking-wider"
                            disabled={!status.facebook_connected || !status.instagram_connected || !status.google_maps_connected}
                            onClick={async () => {
                                try {
                                    // Mark onboarding as completed
                                    await apiClient.post('/profile/onboarding', {});
                                    
                                    // Refresh the user context to get updated onboarding_status
                                    await refreshUser();
                                    
                                    // Small delay to ensure state propagates
                                    await new Promise(resolve => setTimeout(resolve, 300));
                                    
                                    // Navigate to dashboard using React Router
                                    navigate('/dashboard', { replace: true });
                                } catch (error) {
                                    console.error("Failed to complete onboarding", error);
                                    toast.error("Launch Failed", {
                                        description: "Failed to complete onboarding",
                                    });
                                }
                            }}
                        >
                            Launch Dashboard <ArrowRight className="w-6 h-6 ml-2" />
                        </Button>
                    </div>
                </Reveal>

                {/* Disconnect Confirmation Dialog */}
                <AlertDialog open={disconnectDialogOpen} onOpenChange={setDisconnectDialogOpen}>
                    <AlertDialogContent>
                        <AlertDialogHeader>
                            <AlertDialogTitle>
                                Disconnect {platformToDisconnect === 'facebook' ? 'Facebook' : 'Instagram'}?
                            </AlertDialogTitle>
                            <AlertDialogDescription>
                                Are you sure you want to disconnect your {platformToDisconnect === 'facebook' ? 'Facebook' : 'Instagram'} account? 
                                {platformToDisconnect === 'facebook' && ' This will also disconnect Instagram if connected.'}
                                {' '}You will need to reconnect to use posting features again.
                            </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                            <AlertDialogCancel disabled={disconnecting}>Cancel</AlertDialogCancel>
                            <AlertDialogAction
                                onClick={(e) => {
                                    e.preventDefault();
                                    handleDisconnectConfirm();
                                }}
                                disabled={disconnecting}
                                className="bg-destructive hover:bg-destructive/90"
                            >
                                {disconnecting ? (
                                    <span className="flex items-center gap-2">
                                        <RefreshCw className="w-4 h-4 animate-spin" />
                                        Disconnecting...
                                    </span>
                                ) : (
                                    'Disconnect'
                                )}
                            </AlertDialogAction>
                        </AlertDialogFooter>
                    </AlertDialogContent>
                </AlertDialog>
            </motion.div>
        </Layout>
    );
};

export default Onboarding;
