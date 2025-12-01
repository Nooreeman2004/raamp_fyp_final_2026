import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { MapPin, Building2, Loader2, CheckCircle2 } from "lucide-react";
import Layout from "@/components/Layout";
import { toast } from "@/hooks/use-toast";
import { apiClient } from "@/services/api";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { hoverScale } from "@/utils/animations";

interface LocationData {
  has_location?: boolean;
  business_name?: string;
  formatted_address?: string;
  latitude?: number;
  longitude?: number;
  place_id?: string;
}

interface BusinessDomain {
  business: string;
  [key: string]: unknown;
}

interface DomainsResponse {
  domains: BusinessDomain[];
}

interface HyperlocalSetupResponse {
  business_name?: string;
  business_type?: string;
  latitude?: number;
  longitude?: number;
  place_id?: string;
  formatted_address?: string;
  has_setup?: boolean;
}

interface ApiError {
  status?: number;
  detail?: string;
  message?: string;
}

const RequiredLabel = ({ htmlFor, children }: { htmlFor: string; children: React.ReactNode }) => (
  <Label htmlFor={htmlFor} className="flex items-center gap-1">
    {children}
    <span className="text-destructive">*</span>
  </Label>
);

const BusinessSetup = () => {
  const navigate = useNavigate();
  const [businessName, setBusinessName] = useState("");
  const [businessType, setBusinessType] = useState<string>("");
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  const [categories, setCategories] = useState<string[]>([]);
  const [loadingCategories, setLoadingCategories] = useState(false);
  const [categoriesError, setCategoriesError] = useState<string | null>(null);

  const [location, setLocation] = useState<LocationData>({});

  // Validation: all required fields must be filled
  // Required: businessName, businessType, and location (lat/lng OR place_id/address)
  const canSave = useMemo(() => {
    const hasName = !!businessName.trim();
    const hasType = !!businessType && businessType !== "__loading__";
    // Location can be valid with coordinates OR with place_id/address (for existing data)
    const hasLocation = !!(
      (location?.latitude && location?.longitude) || 
      location?.place_id || 
      location?.formatted_address
    );
    return hasName && hasType && hasLocation;
  }, [businessName, businessType, location]);

  useEffect(() => {
    let mounted = true;
    const fetchInitial = async () => {
      setLoading(true);
      setLoadingCategories(true);
      setCategoriesError(null);
      
      try {
        // 1) Load categories from backend business domains first
        let labels: string[] = [];
        try {
          const domainsResp = await apiClient.get('/business-domains') as DomainsResponse;
          if (!mounted) return;
          const domains = Array.isArray(domainsResp?.domains) ? domainsResp.domains : [];
          labels = domains.map((d: BusinessDomain) => String(d.business));
          setCategories(labels);
        } catch (err) {
          console.error('Failed to load categories:', err);
          if (mounted) setCategoriesError('Could not load categories — using defaults');
        }

        // 2) Try to load current setup (includes location from onboarding if no setup done yet)
        try {
          const current = await apiClient.get('/hyperlocal-setup/current') as HyperlocalSetupResponse;
          if (!mounted) return;
          
          // Set location data
          if (current?.latitude && current?.longitude) {
            setLocation({
              has_location: true,
              latitude: current.latitude,
              longitude: current.longitude,
              place_id: current.place_id,
              formatted_address: current.formatted_address,
              business_name: current.business_name
            });
          }
          
          // Set business name if available
          if (current?.business_name) {
            setBusinessName(current.business_name);
          }
          
          // Set business type if available
          if (current?.business_type) {
            const match = labels.find((lbl: string) => 
              lbl.toLowerCase() === String(current.business_type).toLowerCase()
            );
            setBusinessType(match || current.business_type);
          } else if (labels.length > 0) {
            // Default to first category if none selected
            setBusinessType(labels[0]);
          }
        } catch (err: unknown) {
          const apiError = err as ApiError;
          // If /current returns 404, try to load just the location from onboarding
          if (apiError?.status === 404) {
            try {
              const loc = await apiClient.get('/hyperlocal-setup/location') as LocationData;
              if (!mounted) return;
              if (loc?.has_location) {
                setLocation(loc);
                if (loc?.business_name) {
                  setBusinessName(loc.business_name);
                }
              }
            } catch (_) {
              // No location saved at all
            }
          }
          
          // Set default business type if not set
          if (labels.length > 0) {
            setBusinessType(labels[0]);
          }
        }
      } catch (err: unknown) {
        console.error('Error loading initial data:', err);
      } finally {
        if (mounted) {
          setLoading(false);
          setLoadingCategories(false);
        }
      }
    };

    fetchInitial();

    return () => {
      mounted = false;
    };
  }, []);

  const handleSave = async () => {
    if (!canSave) {
      toast({ 
        title: 'Missing required fields', 
        description: 'Please fill in all required fields.', 
        variant: 'destructive' 
      });
      return;
    }

    setSaving(true);
    try {
      const payload = {
        business_name: businessName.trim(),
        business_type: businessType,
        latitude: location?.latitude || 0,
        longitude: location?.longitude || 0,
        place_id: location?.place_id || null,
        formatted_address: location?.formatted_address || null,
      };
      
      await apiClient.post('/hyperlocal-setup/save', payload);
      toast({ title: 'Saved', description: 'Business setup saved successfully.' });
      navigate("/profile/brand-settings");
    } catch (err: unknown) {
      const apiError = err as ApiError;
      console.error('Save error:', err);
      toast({ 
        title: 'Save failed', 
        description: apiError?.detail || apiError?.message || 'Failed to save business setup', 
        variant: 'destructive' 
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center space-y-4">
            <Loader2 className="w-8 h-8 animate-spin text-primary mx-auto" />
            <p className="text-muted-foreground">Loading business setup...</p>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <motion.div 
        className="space-y-8 max-w-4xl mx-auto"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* Header with Location Display */}
        <Reveal variant="blurInUp">
          <div className="space-y-4">
            <div>
              <h1 className="text-4xl font-bold mb-2">Hyperlocal Business Setup</h1>
              <p className="text-muted-foreground">
                Define your business location and targeting parameters for hyper-local campaigns
              </p>
            </div>
            
            {/* Location Display below title */}
            {location?.formatted_address && (
              <div className="flex items-center gap-2 p-3 bg-primary/10 rounded-lg border border-primary/20">
                <CheckCircle2 className="w-5 h-5 text-primary flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-primary">Location from Onboarding</p>
                  <p className="text-sm text-muted-foreground truncate">{location.formatted_address}</p>
                </div>
              </div>
            )}
          </div>
        </Reveal>

        {/* Grid */}
        <motion.div 
          className="grid lg:grid-cols-2 gap-6"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          {/* Map Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.5 }}
          >
            <div className="h-full">
              <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10 h-full">
                <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <MapPin className="w-5 h-5 text-primary" />
                  Pin Your Location
                  <span className="text-destructive">*</span>
                </h2>
                
                <div className="aspect-square bg-muted rounded-lg mb-4 relative overflow-hidden group">
                  {location?.latitude && location?.longitude && location.latitude !== 0 && location.longitude !== 0 ? (
                    /* Show actual map when coordinates are available */
                    <iframe
                      title="Business Location Map"
                      width="100%"
                      height="100%"
                      style={{ border: 0 }}
                      loading="lazy"
                      allowFullScreen
                      referrerPolicy="no-referrer-when-downgrade"
                      src={`https://www.google.com/maps/embed/v1/place?key=AIzaSyCONBvkHkY1P6CRKJ5x4UhClo4zPhxpovM&q=${location.latitude},${location.longitude}&zoom=15`}
                      className="rounded-lg"
                    />
                  ) : (
                    /* Show placeholder when no coordinates */
                    <>
                      <div className="absolute inset-0 flex items-center justify-center z-10">
                        <div className="text-center">
                          <Reveal variant="zoomIn" delay={0.4}>
                            <MapPin className="w-12 h-12 text-primary mx-auto mb-2 breathing-glow group-hover:scale-110 transition-transform duration-300" />
                          </Reveal>
                          <p className="text-sm text-muted-foreground">Interactive Map</p>
                          <p className="text-xs text-muted-foreground mt-1">
                            Set location during onboarding
                          </p>
                        </div>
                      </div>
                      <div className="absolute inset-0 bg-primary/5 animate-pulse group-hover:bg-primary/10 transition-colors"></div>
                    </>
                  )}
                </div>

                <div className="space-y-2 text-sm">
                  {location?.formatted_address ? (
                    <>
                      <div className="flex items-start gap-2">
                        <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                        <div>
                          <p className="font-medium text-foreground">Saved Address:</p>
                          <p className="text-muted-foreground">{location.formatted_address}</p>
                        </div>
                      </div>
                      {location?.latitude && location?.longitude && location.latitude !== 0 && location.longitude !== 0 && (
                        <p className="text-xs text-muted-foreground ml-6">
                          Coordinates: {location.latitude.toFixed(5)}, {location.longitude.toFixed(5)}
                        </p>
                      )}
                    </>
                  ) : location?.place_id ? (
                    <div className="flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="font-medium text-foreground">Location Set</p>
                        <p className="text-muted-foreground text-xs">Place ID: {location.place_id}</p>
                      </div>
                    </div>
                  ) : location?.latitude && location?.longitude && location.latitude !== 0 && location.longitude !== 0 ? (
                    <div className="flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="font-medium text-foreground">Location Set</p>
                        <p className="text-muted-foreground">
                          Coordinates: {location.latitude.toFixed(5)}, {location.longitude.toFixed(5)}
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-start gap-2 p-3 bg-destructive/10 rounded-lg">
                      <MapPin className="w-4 h-4 text-destructive mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="font-medium text-destructive">No location saved</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          Please go back to onboarding and set your business location using Google Maps.
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </Card>
            </div>
          </motion.div>

          {/* Business Details Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.5 }}
          >
            <div className="h-full">
              <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10 h-full">
                <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <Building2 className="w-5 h-5 text-primary" />
                  Business Details
                </h2>
                
                <div className="space-y-4">
                  <div className="space-y-2">
                    <RequiredLabel htmlFor="businessName">Business Name</RequiredLabel>
                    <Input
                      id="businessName"
                      value={businessName}
                      onChange={(e) => setBusinessName(e.target.value)}
                      className="bg-background/50"
                      placeholder="Enter your business name"
                    />
                    {!businessName.trim() && (
                      <p className="text-xs text-destructive">Business name is required</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <RequiredLabel htmlFor="businessType">Business Type</RequiredLabel>
                    <Select value={businessType} onValueChange={(val) => setBusinessType(val)}>
                      <SelectTrigger className="bg-background/50">
                        <SelectValue placeholder="Select business type" />
                      </SelectTrigger>
                      <SelectContent>
                        {loadingCategories ? (
                          <SelectItem value="__loading__" disabled>
                            Loading categories...
                          </SelectItem>
                        ) : categories.length > 0 ? (
                          categories.map((c) => (
                            <SelectItem key={c} value={c}>
                              {c}
                            </SelectItem>
                          ))
                        ) : (
                          <>
                            <SelectItem value="Restaurant">Restaurant</SelectItem>
                            <SelectItem value="Retail">Retail Store</SelectItem>
                            <SelectItem value="Services">Professional Services</SelectItem>
                            <SelectItem value="Healthcare">Healthcare</SelectItem>
                            <SelectItem value="Fitness">Fitness & Wellness</SelectItem>
                            <SelectItem value="Other">Other</SelectItem>
                          </>
                        )}
                      </SelectContent>
                    </Select>
                    {categoriesError && <p className="text-xs text-destructive mt-1">{categoriesError}</p>}
                    {!businessType && (
                      <p className="text-xs text-destructive">Business type is required</p>
                    )}
                  </div>

                  {/* Validation Summary */}
                  {!canSave && (
                    <div className="p-3 bg-muted/50 rounded-lg text-sm">
                      <p className="font-medium text-muted-foreground mb-2">Required fields:</p>
                      <ul className="space-y-1 text-xs text-muted-foreground">
                        <li className={`flex items-center gap-2 ${businessName.trim() ? 'text-green-500' : 'text-destructive'}`}>
                          {businessName.trim() ? '✓' : '•'} Business Name
                        </li>
                        <li className={`flex items-center gap-2 ${businessType && businessType !== '__loading__' ? 'text-green-500' : 'text-destructive'}`}>
                          {businessType && businessType !== '__loading__' ? '✓' : '•'} Business Type
                        </li>
                        <li className={`flex items-center gap-2 ${(location?.latitude && location?.longitude) || location?.place_id || location?.formatted_address ? 'text-green-500' : 'text-destructive'}`}>
                          {(location?.latitude && location?.longitude) || location?.place_id || location?.formatted_address ? '✓' : '•'} Location (set during onboarding)
                        </li>
                      </ul>
                    </div>
                  )}

                  <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                    <Button
                      variant="hero" 
                      className="w-full mt-4"
                      disabled={!canSave || saving}
                      onClick={handleSave}
                    >
                      {saving ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Saving...
                        </>
                      ) : (
                        'Continue to Brand Alignment'
                      )}
                    </Button>
                  </motion.div>
                </div>
              </Card>
            </div>
          </motion.div>
        </motion.div>
      </motion.div>
    </Layout>
  );
};

export default BusinessSetup;