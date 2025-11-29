import { useState, useEffect } from "react";
import HeatmapMap from "@/components/HeatmapMap";
import { Link } from "react-router-dom";
import Layout from "@/components/Layout";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { authService } from "@/services/authService";
import { apiClient } from "@/services/api";
import { useToast } from "@/hooks/use-toast";
import CommandPalette from "@/components/CommandPalette";
import RecentPages from "@/components/RecentPages";
import { 
  ArrowUp,
  DollarSign,
  TrendingUp as TrendIcon,
  Sparkles,
  FlaskConical as Flask,
  MapPin,
  MessageSquare
} from "lucide-react";
import { getErrorMessage } from "@/utils/errorHandler";
import type { DashboardMetrics, GeoLocation, HighIntentArea, OnboardingData } from "@/types";

const Dashboard = () => {
  const { toast } = useToast();
  const [userLocation, setUserLocation] = useState<GeoLocation | null>(null);
  const [highIntentAreas, setHighIntentAreas] = useState<HighIntentArea[]>([]);
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  const [isLoadingMaps, setIsLoadingMaps] = useState(true);
  const [isLoadingDashboard, setIsLoadingDashboard] = useState(true);
  const [isLoadingMetrics, setIsLoadingMetrics] = useState(true);
  const [dashboardMetrics, setDashboardMetrics] = useState<DashboardMetrics | null>(null);

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

        // Fetch user location and high intent areas from onboarding data
        try {
          const onboardingData = await apiClient.get<OnboardingData>('/profile/onboarding');
          if (onboardingData?.connections?.google_business) {
            const googleBusiness = onboardingData.connections.google_business;
            if (googleBusiness.latitude && googleBusiness.longitude) {
              setUserLocation({
                lat: googleBusiness.latitude,
                lng: googleBusiness.longitude,
                name: googleBusiness.business_name || 'Your Location',
              });
            }
          }

          // Mock high intent areas (in production, this would come from Python backend analytics)
          // Example: DHA area in Karachi
          setHighIntentAreas([
            { lat: 24.8138, lng: 67.0700, name: 'DHA Phase 5', intensity: 0.95 },
            { lat: 24.8000, lng: 67.0500, name: 'DHA Phase 6', intensity: 0.85 },
            { lat: 24.8200, lng: 67.0800, name: 'DHA Phase 4', intensity: 0.75 },
          ]);
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
  }, [toast]);

  return (
    <Layout showBreadcrumbs={false}>
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
            <div>
              <h1 className="text-3xl font-bold mb-1">Autonomous Marketing Command Center</h1>
            </div>

          {/* Actionable Overview Section */}
          <div>
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">
              ACTIONABLE OVERVIEW
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* ROAS Card */}
              <Card className="bg-card/50 backdrop-blur-sm border-primary/20 p-5 hover:border-primary/40 transition-all">
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

              {/* Conversion Rate Card */}
              <Card className="bg-card/50 backdrop-blur-sm border-primary/20 p-5 hover:border-primary/40 transition-all">
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

              {/* Total Ad Spend Card */}
              <Card className="bg-card/50 backdrop-blur-sm border-primary/20 p-5 hover:border-primary/40 transition-all">
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

              {/* Budget Allocation Card */}
              <Card className="bg-card/50 backdrop-blur-sm border-primary/20 p-5 hover:border-primary/40 transition-all relative overflow-hidden">
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
                      <div 
                        className="h-full bg-gradient-to-r from-primary to-accent rounded-full transition-all duration-500"
                        style={{ width: `${dashboardMetrics?.budgetAllocation?.percentage || 0}%` }}
                      ></div>
                    </div>
                  </div>
                )}
              </Card>
            </div>
          </div>

          {/* Visual & Strategic Analysis Section */}
          <div>
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">
              VISUAL & STRATEGIC ANALYSIS
            </h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Lead Heatmap Card */}
              <Card className="bg-card/50 backdrop-blur-sm border-primary/20 p-6 hover:border-primary/40 transition-all">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold">Lead Heatmap & Demographics</h3>
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

              {/* Causal Insights Card */}
              <Card className="bg-card/50 backdrop-blur-sm border-primary/20 p-6 hover:border-primary/40 transition-all">
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
            </div>
          </div>

          {/* Module Status & Quick Actions Section */}
          <div>
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">
              MODULE STATUS & QUICK ACTIONS
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Trend Arbitrage */}
              <Card className="bg-card/50 backdrop-blur-sm border-primary/20 p-5 hover:border-primary/40 transition-all group cursor-pointer">
                <Link to="/dashboard/trends" className="block">
                  <div className="flex items-start justify-between mb-3">
                    <div className="w-10 h-10 rounded-lg bg-amber-500/20 flex items-center justify-center">
                      <TrendIcon className="w-5 h-5 text-amber-400" />
                    </div>
                    <div className="text-xs bg-amber-500/20 text-amber-400 px-2 py-1 rounded">
                      NEW ALERT
                    </div>
                  </div>
                  <h3 className="font-semibold mb-1 group-hover:text-primary transition-colors">Trend Arbitrage</h3>
                  <div className="text-sm text-muted-foreground mb-1">Tasty Posts' shalwaar-shorts surge</div>
                  <div className="text-xs text-primary hover:underline mb-2">Launch Champaign Now →</div>
                </Link>
              </Card>

              {/* Creative Studio */}
              <Card className="bg-card/50 backdrop-blur-sm border-primary/20 p-5 hover:border-primary/40 transition-all group cursor-pointer">
                <Link to="/dashboard/creative" className="block">
                  <div className="flex items-start justify-between mb-3">
                    <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center">
                      <Sparkles className="w-5 h-5 text-primary" />
                    </div>
                  </div>
                  <h3 className="font-semibold mb-1 group-hover:text-primary transition-colors">Creative Studio</h3>
                  <div className="text-sm text-muted-foreground mb-2">Export Conversion-Ready Ad</div>
                  <div className="text-xs text-primary hover:underline">Create</div>
                </Link>
              </Card>

              {/* A/B Testing */}
              <Card className="bg-card/50 backdrop-blur-sm border-primary/20 p-5 hover:border-primary/40 transition-all group cursor-pointer">
                <Link to="/dashboard/ab-testing" className="block">
                  <div className="flex items-start justify-between mb-3">
                    <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                      <Flask className="w-5 h-5 text-blue-400" />
                    </div>
                  </div>
                  <h3 className="font-semibold mb-1 group-hover:text-primary transition-colors">A/B Testing</h3>
                  <div className="text-sm text-muted-foreground mb-1">It's Worth It. Promise</div>
                  <div className="text-xs text-primary hover:underline">Initiate Live Test</div>
                </Link>
              </Card>

              {/* Geo-Intent Engine */}
              <Card className="bg-card/50 backdrop-blur-sm border-primary/20 p-5 hover:border-primary/40 transition-all group cursor-pointer">
                <Link to="/dashboard/geo-intent" className="block">
                  <div className="flex items-start justify-between mb-3">
                    <div className="w-10 h-10 rounded-lg bg-red-500/20 flex items-center justify-center">
                      <MapPin className="w-5 h-5 text-red-400" />
                    </div>
                  </div>
                  <h3 className="font-semibold mb-1 group-hover:text-primary transition-colors">Geo-Intent Engine</h3>
                  <div className="text-sm text-muted-foreground mb-1">Hyper-Local Reach, Stellar Results</div>
                  <div className="text-xs text-primary hover:underline">Draw Zones</div>
                </Link>
              </Card>

              {/* RAAMP Assistant */}
              <Card className="bg-card/50 backdrop-blur-sm border-primary/20 p-5 hover:border-primary/40 transition-all group cursor-pointer">
                <Link to="/dashboard/assistant" className="block">
                  <div className="flex items-start justify-between mb-3">
                    <div className="w-10 h-10 rounded-lg bg-cyan-500/20 flex items-center justify-center">
                      <MessageSquare className="w-5 h-5 text-cyan-400" />
                    </div>
                  </div>
                  <h3 className="font-semibold mb-1 group-hover:text-primary transition-colors">RAAMP Assistant</h3>
                  <div className="text-sm text-muted-foreground mb-1">Your Omnipresent Module Concierge</div>
                  <div className="text-xs text-primary hover:underline">Converse</div>
                </Link>
              </Card>

              {/* Billing & Finance */}
              <Card className="bg-card/50 backdrop-blur-sm border-primary/20 p-5 hover:border-primary/40 transition-all group cursor-pointer">
                <Link to="/billing" className="block">
                  <div className="flex items-start justify-between mb-3">
                    <div className="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                      <DollarSign className="w-5 h-5 text-emerald-400" />
                    </div>
                  </div>
                  <h3 className="font-semibold mb-1 group-hover:text-primary transition-colors">Billing & Finance</h3>
                  <div className="text-sm text-muted-foreground mb-1">View Overview</div>
                  <div className="text-primary text-lg font-semibold mb-2">€25,999</div>
                </Link>
              </Card>
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
