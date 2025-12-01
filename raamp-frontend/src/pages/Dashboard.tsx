import { useState, useEffect, useCallback, useMemo } from "react";
import HeatmapMap from "@/components/HeatmapMap";
import { Link } from "react-router-dom";
import Layout from "@/components/Layout";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { apiClient } from "@/services/api";
import { useToast } from "@/hooks/use-toast";
import CommandPalette from "@/components/CommandPalette";
import { 
  ArrowUp,
  DollarSign,
  MapPin
} from "lucide-react";
import { getErrorMessage } from "@/utils/errorHandler";
import type { DashboardMetrics, GeoLocation, HighIntentArea, OnboardingData } from "@/types";

// Animation Imports
import { motion, AnimatePresence } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeInUp, blurInUp, zoomIn } from "@/utils/animations";

const Dashboard = () => {
  const { toast } = useToast();
  const [userLocation, setUserLocation] = useState<GeoLocation | null>(null);
  const [highIntentAreas, setHighIntentAreas] = useState<HighIntentArea[]>([]);
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  const [isLoadingMaps, setIsLoadingMaps] = useState(true);
  const [isLoadingDashboard, setIsLoadingDashboard] = useState(true);
  const [isLoadingMetrics, setIsLoadingMetrics] = useState(true);
  const [dashboardMetrics, setDashboardMetrics] = useState<DashboardMetrics | null>(null);
  const [userName, setUserName] = useState<string>("");
  const [showWelcome, setShowWelcome] = useState(false);
  const [locationName, setLocationName] = useState<string>("");

  // Welcome animation variants
  const welcomeVariants = {
    hidden: { 
      opacity: 0, 
      y: -50,
      scale: 0.8
    },
    visible: { 
      opacity: 1, 
      y: 0,
      scale: 1,
      transition: {
        type: "spring" as const,
        stiffness: 100,
        damping: 15,
        duration: 0.8
      }
    },
    exit: { 
      opacity: 0, 
      y: -30,
      scale: 0.95,
      transition: {
        duration: 0.5,
        ease: "easeOut" as const
      }
    }
  };

  // Fetch user name for welcome message
  useEffect(() => {
    const userData = localStorage.getItem("user");
    if (userData) {
      try {
        const user = JSON.parse(userData);
        const name = user.first_name || user.username || user.email?.split("@")[0] || "there";
        setUserName(name);
        
        // Show welcome animation on first load of this session
        const hasSeenWelcome = sessionStorage.getItem("hasSeenWelcome");
        if (!hasSeenWelcome) {
          setShowWelcome(true);
          sessionStorage.setItem("hasSeenWelcome", "true");
          // Auto-hide welcome after 4 seconds
          setTimeout(() => setShowWelcome(false), 4000);
        }
      } catch (e) {
        console.error("Error parsing user data:", e);
      }
    }
  }, []);

  // Generate high intent areas based on user location
  const generateHighIntentAreas = useCallback((location: GeoLocation): HighIntentArea[] => {
    const areas: HighIntentArea[] = [];
    const areaNames = [
      "High Traffic Zone", "Commercial Hub", "Residential Elite", 
      "Shopping District", "Business Center", "Entertainment Area"
    ];
    
    // Generate 4-6 high intent areas around the user's location
    const numAreas = 4 + Math.floor(Math.random() * 3);
    for (let i = 0; i < numAreas; i++) {
      const angle = (2 * Math.PI * i) / numAreas;
      const distance = 0.008 + Math.random() * 0.015; // ~0.8-2.3 km
      areas.push({
        lat: location.lat + distance * Math.cos(angle),
        lng: location.lng + distance * Math.sin(angle),
        name: areaNames[i % areaNames.length],
        intensity: 0.6 + Math.random() * 0.35 // 60-95% intensity
      });
    }
    
    return areas;
  }, []);

  // Fetch dashboard data
  useEffect(() => {
    const fetchDashboardData = async () => {
      setIsLoadingDashboard(true);

      try {
        // Fetch dashboard metrics
        setIsLoadingMetrics(true);
        try {
          // TODO: Replace with actual Python backend API endpoint when available
          // For now, simulate API call with timeout
          await new Promise(resolve => setTimeout(resolve, 800));
          
          // Mock metrics - replace with actual API call to Python backend:
          // const metrics = await apiClient.get('/dashboard/metrics');
          setDashboardMetrics({
            roas: 4.75,
            conversionRate: 3.2,
            totalAdSpend: 7500,
            budgetAllocation: { used: 7500, total: 20000, percentage: 37.5 },
            projectedROI: 18.5,
          });
        } catch (err) {
          console.error("Failed to fetch dashboard metrics:", err);
          const errorMessage = getErrorMessage(err);
          toast({
            title: "Failed to Load Metrics",
            description: errorMessage,
            variant: "destructive",
          });
          // Set default/fallback metrics
          setDashboardMetrics({
            roas: 0,
            conversionRate: 0,
            totalAdSpend: 0,
            budgetAllocation: { used: 0, total: 0, percentage: 0 },
            projectedROI: 0,
          });
        } finally {
          setIsLoadingMetrics(false);
        }

        // Fetch user location and high intent areas from hyperlocal setup
        try {
          setIsLoadingMaps(true);
          let locationData: GeoLocation | null = null;
          
          // First try to get from hyperlocal setup (business location)
          try {
            const hyperlocalData = await apiClient.get<{ 
              has_location?: boolean;
              latitude?: number; 
              longitude?: number; 
              business_name?: string;
              formatted_address?: string;
            }>('/hyperlocal-setup/location');
            
            if (hyperlocalData?.has_location && hyperlocalData?.latitude && hyperlocalData?.longitude) {
              locationData = {
                lat: hyperlocalData.latitude,
                lng: hyperlocalData.longitude,
                name: hyperlocalData.business_name || 'Your Business Location',
              };
              setLocationName(hyperlocalData.formatted_address || hyperlocalData.business_name || 'Your Location');
            }
          } catch {
            // Hyperlocal setup not found, try onboarding
          }

          // Fallback to onboarding data if no hyperlocal location
          if (!locationData) {
            try {
              const onboardingData = await apiClient.get<OnboardingData>('/profile/onboarding');
              if (onboardingData?.connections?.google_business) {
                const googleBusiness = onboardingData.connections.google_business;
                if (googleBusiness.latitude && googleBusiness.longitude) {
                  locationData = {
                    lat: googleBusiness.latitude,
                    lng: googleBusiness.longitude,
                    name: googleBusiness.business_name || 'Your Location',
                  };
                  setLocationName(googleBusiness.address || googleBusiness.business_name || 'Your Location');
                }
              }
            } catch {
              // Onboarding data not found
            }
          }

          // Set location and generate related data
          if (locationData) {
            setUserLocation(locationData);
            // Generate high intent areas dynamically based on user location
            setHighIntentAreas(generateHighIntentAreas(locationData));
          } else {
            // No location found - set empty state
            setUserLocation(null);
            setLocationName('');
            setHighIntentAreas([]);
          }
          
          setIsLoadingMaps(false);
        } catch (err) {
          console.error("Failed to fetch location data:", err);
          const errorMessage = getErrorMessage(err);
          toast({
            title: "Failed to Load Location Data",
            description: errorMessage,
            variant: "destructive",
          });
          setIsLoadingMaps(false);
        }
      } catch (err) {
        console.error("Failed to fetch dashboard data:", err);
        const errorMessage = getErrorMessage(err);
        toast({
          title: "Error Loading Dashboard",
          description: errorMessage,
          variant: "destructive",
        });
      } finally {
        setIsLoadingDashboard(false);
      }
    };

    fetchDashboardData();
  }, [toast, generateHighIntentAreas]);

  return (
    <Layout showBreadcrumbs={false}>
      {/* Animated Welcome Message */}
      <AnimatePresence>
        {showWelcome && (
          <motion.div
            variants={welcomeVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="fixed top-20 left-1/2 -translate-x-1/2 z-50"
          >
            <div className="bg-gradient-to-r from-primary/90 to-accent/90 text-white px-8 py-4 rounded-2xl shadow-2xl backdrop-blur-sm border border-white/20">
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
                className="flex items-center gap-3"
              >
                <motion.span
                  animate={{ 
                    rotate: [0, 14, -8, 14, -4, 10, 0],
                  }}
                  transition={{ 
                    duration: 2.5,
                    ease: "easeInOut",
                    repeat: 1
                  }}
                  className="text-3xl"
                >
                  👋
                </motion.span>
                <div>
                  <motion.h2 
                    className="text-2xl font-bold"
                    initial={{ x: -20, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: 0.4, type: "spring" }}
                  >
                    Welcome, {userName}!
                  </motion.h2>
                  <motion.p
                    className="text-sm text-white/80"
                    initial={{ x: -20, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: 0.6 }}
                  >
                    Your marketing command center is ready
                  </motion.p>
                </div>
              </motion.div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {isLoadingDashboard ? (
          <div className="space-y-6">
            {/* Page Header Skeleton */}
            <div>
              <Skeleton className="h-9 w-96 mb-1" />
            </div>
            
            {/* Metrics Section Skeleton */}
            <div>
              <Skeleton className="h-4 w-48 mb-4" />
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {[1, 2, 3, 4].map((i) => (
                  <Card key={i} className="bg-card/50 backdrop-blur-sm border-primary/20 p-5">
                    <div className="space-y-2">
                      <Skeleton className="h-3 w-32" />
                      <Skeleton className="h-9 w-20" />
                      <Skeleton className="h-4 w-24" />
                      <Skeleton className="h-3 w-40 mt-2" />
                    </div>
                  </Card>
                ))}
              </div>
            </div>
            
            {/* Analysis Section Skeleton */}
            <div>
              <Skeleton className="h-4 w-56 mb-4" />
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <Card className="bg-card/50 backdrop-blur-sm border-primary/20 p-6">
                  <Skeleton className="h-6 w-48 mb-4" />
                  <Skeleton className="h-[400px] w-full rounded-lg" />
                </Card>
                <Card className="bg-card/50 backdrop-blur-sm border-primary/20 p-6">
                  <Skeleton className="h-6 w-48 mb-4" />
                  <div className="space-y-3">
                    <Skeleton className="h-16 w-full rounded-lg" />
                    <Skeleton className="h-16 w-full rounded-lg" />
                    <Skeleton className="h-16 w-full rounded-lg" />
                  </div>
                </Card>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Page Header */}
            <Reveal variant="blurInUp">
              <div>
                <h1 className="text-3xl font-bold mb-1">Autonomous Marketing Command Center</h1>
              </div>
            </Reveal>

          {/* Actionable Overview Section */}
          <div>
            <Reveal variant="fadeInUp" delay={0.1}>
              <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">
                ACTIONABLE OVERVIEW
              </h2>
            </Reveal>
            <motion.div 
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
              variants={staggerContainer}
              initial="hidden"
              animate="visible"
            >
              {/* ROAS Card */}
              <motion.div variants={fadeInUp}>
                <Card className="bg-card/50 backdrop-blur-sm border-primary/20 p-5 hover:border-primary/40 transition-all h-full">
                  {isLoadingMetrics ? (
                    <div className="space-y-2">
                      <Skeleton className="h-3 w-32" />
                      <Skeleton className="h-9 w-20" />
                      <Skeleton className="h-4 w-24" />
                      <Skeleton className="h-3 w-40 mt-2" />
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <div className="text-xs text-muted-foreground">Return on Ad Spend (ROAS)</div>
                      <div className="text-3xl font-bold text-primary">
                        {dashboardMetrics?.roas?.toFixed(2) || '0.00'}
                      </div>
                      <div className="flex items-center gap-2 text-xs">
                        <div className="flex items-center text-emerald-400">
                          <ArrowUp className="w-3 h-3" />
                          <span>+12.5%</span>
                        </div>
                        <span className="text-muted-foreground">(Last 30 days)</span>
                      </div>
                      <div className="text-xs text-muted-foreground mt-2">
                        Overall campaign effectiveness.
                      </div>
                    </div>
                  )}
                </Card>
              </motion.div>

              {/* Conversion Rate Card */}
              <motion.div variants={fadeInUp}>
                <Card className="bg-card/50 backdrop-blur-sm border-primary/20 p-5 hover:border-primary/40 transition-all h-full">
                  {isLoadingMetrics ? (
                    <div className="space-y-2">
                      <Skeleton className="h-3 w-28" />
                      <Skeleton className="h-9 w-16" />
                      <Skeleton className="h-4 w-24" />
                      <Skeleton className="h-3 w-40 mt-2" />
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <div className="text-xs text-muted-foreground">Conversion Rate</div>
                      <div className="text-3xl font-bold text-primary">
                        {dashboardMetrics?.conversionRate?.toFixed(1) || '0.0'}%
                      </div>
                      <div className="flex items-center gap-2 text-xs">
                        <div className="flex items-center text-emerald-400">
                          <ArrowUp className="w-3 h-3" />
                          <span>0.1%</span>
                        </div>
                        <span className="text-muted-foreground">(Last 30 days)</span>
                      </div>
                      <div className="text-xs text-muted-foreground mt-2">
                        Rate of customers completing desired action.
                      </div>
                    </div>
                  )}
                </Card>
              </motion.div>

              {/* Total Ad Spend Card */}
              <motion.div variants={fadeInUp}>
                <Card className="bg-card/50 backdrop-blur-sm border-primary/20 p-5 hover:border-primary/40 transition-all h-full">
                  {isLoadingMetrics ? (
                    <div className="space-y-2">
                      <Skeleton className="h-3 w-24" />
                      <Skeleton className="h-9 w-24" />
                      <Skeleton className="h-3 w-36 mt-2" />
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <div className="text-xs text-muted-foreground">Total Ad Spend</div>
                      <div className="text-3xl font-bold text-primary">
                        ${dashboardMetrics?.totalAdSpend?.toLocaleString() || '0'}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Cumulative spending this cycle.
                      </div>
                    </div>
                  )}
                </Card>
              </motion.div>

              {/* Budget Allocation Card */}
              <motion.div variants={fadeInUp}>
                <Card className="bg-card/50 backdrop-blur-sm border-primary/20 p-5 hover:border-primary/40 transition-all relative overflow-hidden h-full">
                  {isLoadingMetrics ? (
                    <div className="space-y-2">
                      <Skeleton className="h-3 w-28" />
                      <Skeleton className="h-7 w-32" />
                      <Skeleton className="h-3 w-28" />
                      <Skeleton className="h-1.5 w-full mt-3 rounded-full" />
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="text-xs text-muted-foreground">Budget Allocation</div>
                      </div>
                      <div className="text-xl font-bold">
                        ${dashboardMetrics?.budgetAllocation?.used.toLocaleString() || '0'} / ${dashboardMetrics?.budgetAllocation?.total.toLocaleString() || '0'}
                      </div>
                      <div className="text-xs text-emerald-400 flex items-center gap-1">
                        <ArrowUp className="w-3 h-3" />
                        Projected ROI: +{dashboardMetrics?.projectedROI?.toFixed(1) || '0.0'}%
                      </div>
                      {/* Progress bar */}
                      <div className="w-full h-1.5 bg-muted rounded-full mt-3">
                        <motion.div 
                          initial={{ width: 0 }}
                          animate={{ width: `${dashboardMetrics?.budgetAllocation?.percentage || 0}%` }}
                          transition={{ duration: 1, ease: "easeOut" }}
                          className="h-full bg-gradient-to-r from-primary to-accent rounded-full"
                        ></motion.div>
                      </div>
                    </div>
                  )}
                </Card>
              </motion.div>
            </motion.div>
          </div>

          {/* Visual & Strategic Analysis Section */}
          <div>
            <Reveal variant="fadeInUp" delay={0.2}>
              <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">
                VISUAL & STRATEGIC ANALYSIS
              </h2>
            </Reveal>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Lead Heatmap Card */}
              <Reveal variant="zoomIn" delay={0.3}>
                <Card className="bg-card/50 backdrop-blur-sm border-primary/20 p-6 hover:border-primary/40 transition-all h-full">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-lg font-semibold">Lead Heatmap & Demographics</h3>
                        {locationName && (
                          <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
                            <MapPin className="w-3 h-3" />
                            <span>{locationName}</span>
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">{highIntentAreas.length} zones</span>
                      </div>
                    </div>
                    
                    {/* Heatmap Map with user location (yellow) and high intent areas (red) */}
                    {isLoadingMaps ? (
                      <div className="h-[400px] bg-muted/30 flex items-center justify-center rounded-lg">
                        <div className="text-center space-y-2">
                          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
                          <p className="text-sm text-muted-foreground">Loading heatmap...</p>
                        </div>
                      </div>
                    ) : (
                      <HeatmapMap
                        userLocation={userLocation || undefined}
                        highIntentAreas={highIntentAreas}
                        height="400px"
                      />
                    )}
                    
                    {/* Legend */}
                    <div className="flex items-center space-x-4 text-xs">
                      <div className="flex items-center space-x-2">
                        <span className="inline-block w-3 h-3 rounded-full bg-[#FFD700] border border-muted" />
                        <span>Your Location</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="inline-block w-3 h-3 rounded-full bg-[#FF0000] border border-muted" />
                        <span>High-Intent Areas</span>
                      </div>
                    </div>
                    
                    <Link to="/dashboard/geo-intent" className="text-xs text-primary hover:underline">
                      Explore Geo-Intent Module →
                    </Link>
                  </div>
                </Card>
              </Reveal>

              {/* Causal Insights Card */}
              <Reveal variant="fadeInUp" delay={0.4}>
                <Card className="bg-card/50 backdrop-blur-sm border-primary/20 p-6 hover:border-primary/40 transition-all h-full">
                  {isLoadingMetrics ? (
                    <div className="space-y-4">
                      <Skeleton className="h-6 w-48" />
                      <div className="space-y-3">
                        <Skeleton className="h-16 w-full rounded-lg" />
                        <Skeleton className="h-16 w-full rounded-lg" />
                        <Skeleton className="h-16 w-full rounded-lg" />
                      </div>
                      <Skeleton className="h-4 w-40" />
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <h3 className="text-lg font-semibold">Causal Insights & Actions</h3>
                      <div className="space-y-3">
                        <div className="flex items-start gap-3 p-3 bg-primary/5 rounded-lg border border-primary/10">
                          <div className="w-2 h-2 rounded-full bg-amber-400 mt-1.5"></div>
                          <div className="flex-1 text-sm">
                            <span className="font-medium">Action:</span> Increase Budget for Social Media Ads
                            <span className="text-muted-foreground"> (highest positive impact on ROAS this week)</span>
                          </div>
                        </div>
                        <div className="flex items-start gap-3 p-3 bg-destructive/5 rounded-lg border border-destructive/20">
                          <div className="w-2 h-2 rounded-full bg-red-400 mt-1.5"></div>
                          <div className="flex-1 text-sm">
                            <span className="font-medium">Caution:</span> Review Legacy Ad Spend
                            <span className="text-muted-foreground"> (showing a -.8% negative influence on Conversion Rate)</span>
                          </div>
                        </div>
                        <div className="flex items-start gap-3 p-3 bg-emerald-500/5 rounded-lg border border-emerald-500/20">
                          <div className="w-2 h-2 rounded-full bg-emerald-400 mt-1.5"></div>
                          <div className="flex-1 text-sm">
                            <span className="font-medium">Suggestion:</span> Explore better performing age
                            <span className="text-muted-foreground"> aligned with the "Early Adopter" segment for maximum reach.</span>
                          </div>
                        </div>
                      </div>
                      <Link to="/dashboard/performance" className="text-xs text-primary hover:underline">
                        View Complete Insights Log →
                      </Link>
                    </div>
                  )}
                </Card>
              </Reveal>
            </div>
          </div>
          </div>
        )}
      
      {/* Command Palette for Quick Navigation */}
      <CommandPalette open={showCommandPalette} onOpenChange={setShowCommandPalette} />
    </Layout>
  );
};

export default Dashboard;