import { useState, useEffect } from "react";
import HeatmapMap from "@/components/HeatmapMap";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { SettingsPopup } from "@/components/ui/settings-popup";
import { authService } from "@/services/authService";
import { useNavigate } from "react-router-dom";
import { Card } from "@/components/ui/card";
import raampIcon from "@/assets/raamp-icon-transparent.png";
import ProfileSidebar from "@/components/ProfileSidebar";
import { apiClient } from "@/services/api";
import ConfirmationDialog from "@/components/ConfirmationDialog";
import { useToast } from "@/hooks/use-toast";
import Breadcrumbs from "@/components/Breadcrumbs";
import CommandPalette from "@/components/CommandPalette";
import RecentPages from "@/components/RecentPages";
import { 
  LayoutDashboard, 
  MapPin, 
  Sparkles, 
  BarChart3,
  MessageSquare,
  Bell,
  Settings,
  User,
  ArrowUp,
  TrendingUp as TrendIcon,
  FlaskConical as Flask,
  DollarSign
} from "lucide-react";

const Dashboard = () => {
  const { toast } = useToast();
  const [profileOpen, setProfileOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [user, setUser] = useState<any>(null);
  const [userLocation, setUserLocation] = useState<{
    lat: number;
    lng: number;
    name?: string;
  } | null>(null);
  const [highIntentAreas, setHighIntentAreas] = useState<Array<{
    lat: number;
    lng: number;
    name?: string;
    intensity?: number;
  }>>([]);
  const [showLogoutDialog, setShowLogoutDialog] = useState(false);
  const [showBudgetDialog, setShowBudgetDialog] = useState(false);
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  const [isLoadingMaps, setIsLoadingMaps] = useState(true);
  const navigate = useNavigate();

  // Fetch user and restaurant location data
  useEffect(() => {
    // Example: get user from localStorage or API
    const stored = localStorage.getItem("user");
    if (stored) {
      setUser(JSON.parse(stored));
    }

    // Fetch user profile and restaurant location
    (async () => {
      try {
        const u = await authService.getProfile();
        if (u) {
          setUser(u);
          try { localStorage.setItem('user', JSON.stringify(u)); } catch {}
        }

        // Fetch user location and high intent areas from onboarding data
        try {
          const onboardingData: any = await apiClient.get('/profile/onboarding');
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

          // Mock high intent areas (in production, this would come from analytics/backend)
          // Example: DHA area in Karachi
          setHighIntentAreas([
            { lat: 24.8138, lng: 67.0700, name: 'DHA Phase 5', intensity: 0.95 },
            { lat: 24.8000, lng: 67.0500, name: 'DHA Phase 6', intensity: 0.85 },
            { lat: 24.8200, lng: 67.0800, name: 'DHA Phase 4', intensity: 0.75 },
          ]);
          setIsLoadingMaps(false);
        } catch (err) {
          // Ignore - location data not available
          setIsLoadingMaps(false);
        }
      } catch (err) {
        // Ignore - user is not authenticated or endpoint missing
      }
    })();
  }, []);

  const handleLogout = async () => {
    try {
      await authService.logout();
      setUser(null);
      localStorage.removeItem("user");
      toast({
        title: "Logged Out",
        description: "You have been successfully logged out.",
      });
      navigate("/login");
    } catch (e) {
      toast({
        title: "Error",
        description: "Failed to logout. Please try again.",
        variant: "destructive",
      });
    }
  };

  const handleBudgetReallocation = () => {
    // TODO: Implement actual budget reallocation
    toast({
      title: "Budget Reallocated",
      description: "Your budget has been successfully optimized based on AI recommendations.",
    });
  };
  
  const navItems = [
    { label: "Dashboard", icon: LayoutDashboard, href: "/dashboard" },
    { label: "Geo-Intent", icon: MapPin, href: "/dashboard/geo-intent" },
    { label: "Creative Studio", icon: Sparkles, href: "/dashboard/creative" },
    { label: "Trend Arbitrage", icon: TrendIcon, href: "/dashboard/trends" },
    { label: "A/B Testing", icon: Flask, href: "/dashboard/ab-testing" },
    { label: "Performance", icon: BarChart3, href: "/dashboard/performance" },
    { label: "RAAMP Assistant", icon: MessageSquare, href: "/dashboard/assistant" },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-[#0f1c26] to-background">
      {/* Top Navigation */}
      <nav className="border-b border-primary/20 bg-card/30">
        <div className="container mx-auto px-6">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="flex items-center gap-3">
              <img src={raampIcon} alt="RAAMP" className="h-10 w-10" />
              <span className="text-xl font-bold text-primary">RAAMP</span>
            </Link>

            <div className="flex items-center gap-2">
              <Button variant="ghost" size="icon" className="hover:bg-primary/10">
                <Bell className="w-5 h-5" />
              </Button>
              <div className="relative">
                <Button
                  variant="ghost"
                  size="icon"
                  className="hover:bg-primary/10"
                  onClick={() => setSettingsOpen((v) => !v)}
                >
                  <Settings className="w-5 h-5" />
                </Button>
                {settingsOpen && <SettingsPopup onLogout={handleLogout} />}
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="gap-2 hover:bg-primary/10"
                onClick={() => setProfileOpen(true)}
              >
                <User className="w-4 h-4" />
                <span className="font-medium">
                  {user
                    ? ((user.first_name?.[0] || "") + (user.last_name?.[0] || user.first_name?.[1] || user.username?.[0] || user.email?.[0] || "")).toUpperCase()
                    : "JD"}
                </span>
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Module Navigation Tabs */}
      <div className="border-b border-primary/10 bg-card/20 backdrop-blur-sm">
        <div className="container mx-auto px-6">
          <div className="flex gap-1 overflow-x-auto py-1">
            {navItems.map((item, index) => {
              const Icon = item.icon;
              const isActive = index === 0;
              return (
                <Link key={item.href} to={item.href}>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className={`gap-2 relative px-4 py-2 ${
                      isActive 
                        ? 'text-primary bg-primary/10 after:absolute after:bottom-0 after:left-0 after:right-0 after:h-0.5 after:bg-primary' 
                        : 'hover:bg-primary/5 hover:text-primary'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {item.label}
                  </Button>
                </Link>
              );
            })}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
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
                <div className="space-y-2">
                  <div className="text-xs text-muted-foreground">Return on Ad Spend (ROAS)</div>
                  <div className="text-3xl font-bold text-primary">4.75</div>
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
              </Card>

              {/* Conversion Rate Card */}
              <Card className="bg-card/50 backdrop-blur-sm border-primary/20 p-5 hover:border-primary/40 transition-all">
                <div className="space-y-2">
                  <div className="text-xs text-muted-foreground">Conversion Rate</div>
                  <div className="text-3xl font-bold text-primary">3.2%</div>
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
              </Card>

              {/* Total Ad Spend Card */}
              <Card className="bg-card/50 backdrop-blur-sm border-primary/20 p-5 hover:border-primary/40 transition-all">
                <div className="space-y-2">
                  <div className="text-xs text-muted-foreground">Total Ad Spend</div>
                  <div className="text-3xl font-bold text-primary">$7,500</div>
                  <div className="text-xs text-muted-foreground">
                    Cumulative spending this cycle.
                  </div>
                </div>
              </Card>

              {/* Budget Allocation Card */}
              <Card className="bg-card/50 backdrop-blur-sm border-primary/20 p-5 hover:border-primary/40 transition-all relative overflow-hidden">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="text-xs text-muted-foreground">Budget Allocation</div>
                  </div>
                  <div className="text-xl font-bold">$7,500 / $20,000</div>
                  <div className="text-xs text-emerald-400 flex items-center gap-1">
                    <ArrowUp className="w-3 h-3" />
                    Projected ROI: +18.5%
                  </div>
                  {/* Progress bar */}
                  <div className="w-full h-1.5 bg-muted rounded-full mt-3">
                    <div className="h-full w-[37.5%] bg-gradient-to-r from-primary to-accent rounded-full"></div>
                  </div>
                </div>
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
                <Link to="/profile/billing" className="block">
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
      </main>

      <ProfileSidebar open={profileOpen} onOpenChange={setProfileOpen} />

      {/* Confirmation Dialog for Logout */}
      <ConfirmationDialog
        open={showLogoutDialog}
        onOpenChange={setShowLogoutDialog}
        onConfirm={handleLogout}
        title="Confirm Logout"
        description="Are you sure you want to logout? You'll need to sign in again to access your account."
        confirmText="Logout"
        cancelText="Cancel"
        variant="default"
      />

      {/* Command Palette for Quick Navigation */}
      <CommandPalette open={showCommandPalette} onOpenChange={setShowCommandPalette} />
    </div>
  );
};

export default Dashboard;
