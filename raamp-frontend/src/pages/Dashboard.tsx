import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import Layout from "@/components/Layout";
import { Badge } from "@/components/ui/badge";
import {
  TrendingUp,
  Users,
  Target,
  ArrowUpRight,
  ArrowDownRight,
  Activity,
  Zap,
  Globe,
  BarChart3,
  Sparkles,
  PieChart,
  ArrowRight,
  RefreshCw,
  ShieldCheck,
  AlertTriangle,
  Radio,
  DollarSign as DollarSignIcon
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { HolographicCard } from "@/components/ui/holographic-card";
import { MaskedTextReveal } from "@/components/ui/masked-text-reveal";
import { MagneticButton } from "@/components/ui/magnetic-button";
import { NumberTicker } from "@/components/ui/number-ticker";
import { LineChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid } from "recharts";
import { authService } from "@/services/authService";
import { businessService } from "@/services/businessService";
import { dashboardService, type DashboardSummary, type ConversionPing } from "@/services/dashboardService";
import type { UserResponse } from "@/types";
import GoogleMap from "@/components/GoogleMap";
import { CardSkeleton, ChartSkeleton } from "@/components/ui/card-skeleton";
import { KPIStrip } from "@/components/dashboard/KPIStrip";
import { PerformanceCharts } from "@/components/dashboard/PerformanceCharts";
import { ActionableIntelligence } from "@/components/dashboard/ActionableIntelligence";
import { ActivityFeed } from "@/components/dashboard/ActivityFeed";
import { instagramService } from "@/services/instagramService";

type MapLocation = {
  lat: number;
  lng: number;
  name?: string;
  address?: string;
  type?: 'home' | 'ping';
  revenue?: number;
};

const Dashboard = () => {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [analytics, setAnalytics] = useState<DashboardSummary | null>(null);
  const [livePings, setLivePings] = useState<MapLocation[]>([]);
  const [mapCenter, setMapCenter] = useState<{ lat: number; lng: number }>({
    lat: 24.8607,
    lng: 67.0011,
  });
  const [mapLocations, setMapLocations] = useState<MapLocation[]>([]);
  const [timeRange, setTimeRange] = useState(() => {
    return localStorage.getItem("dashboard_time_range") || "Last 7 Days";
  });

  const [revenueFlash, setRevenueFlash] = useState(false);
  const [igBusinessId, setIgBusinessId] = useState<string | null>(null);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    localStorage.setItem("dashboard_time_range", timeRange);
  }, [timeRange]);

  // Initial Data Fetch
  useEffect(() => {
    const initDashboard = async () => {
      try {
        const [userData, summaryDataResult, hyperlocalData] = await Promise.all([
          authService.getProfile(),
          dashboardService.getSummary().catch(err => {
            console.warn("Dashboard: Summary fetch failed, using zero-state fallback.", err);
            return null;
          }),
          businessService.getHyperlocalSetup().catch(() => null)
        ]);

        setUser(userData);

        // Use default Zero-State if summary fetch fails
        const defaultSummary: DashboardSummary = {
          kpis: [
            { label: "Total Revenue", value: 0, prefix: "$", change: "STARTING", trend: "neutral", icon_type: "revenue" },
            { label: "Social Footprint", value: 0, suffix: " Posts", change: "WAITING", trend: "neutral", icon_type: "social" },
            { label: "Market Intelligence", value: 0, change: "SCANNING", trend: "neutral", icon_type: "trends" },
            { label: "Asset Storage", value: 0, suffix: " Files", change: "SYNCED", trend: "up", icon_type: "assets" }
          ],
          recent_pings: [],
          campaign_health: [],
          strategic_insights: [
            { id: "s-1", type: "suggestion", title: "Strategy Setup", message: "Initialize your first Regional Heat Signal to see live causal insights.", impact: "Initialization", color: "emerald" }
          ],
          top_regions: [],
          deployment_timeline: [],
          posting_cadence: [
            { day: "Mon", posts: 0 }, { day: "Tue", posts: 0 }, { day: "Wed", posts: 0 },
            { day: "Thu", posts: 0 }, { day: "Fri", posts: 0 }, { day: "Sat", posts: 0 }, { day: "Sun", posts: 0 }
          ],
          last_updated: new Date().toISOString()
        };

        setAnalytics(summaryDataResult || defaultSummary);

        if (hyperlocalData && hyperlocalData.latitude && hyperlocalData.longitude) {
          const base = { lat: hyperlocalData.latitude, lng: hyperlocalData.longitude };
          setMapCenter(base);
          setMapLocations([
            {
              lat: base.lat,
              lng: base.lng,
              name: hyperlocalData.business_name || "Headquarters",
              address: hyperlocalData.formatted_address,
              type: 'home'
            }
          ]);
        }
      } catch (error) {
        console.error("Dashboard: Initialization failed", error);
      } finally {
        setLoading(false);
      }
    };
    initDashboard();
  }, []);

  // Fetch IG Business ID for analytics
  useEffect(() => {
    instagramService.getConnectionStatus().then(status => {
      if (status.connected && status.ig_business_id) {
        setIgBusinessId(status.ig_business_id);
      }
    });
  }, []);

  const activeBusinessId = igBusinessId || user?.email || "";

  // WebSocket for Real-time Updates
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) return;

    const connectSocket = () => {
      const ws = dashboardService.getRealtimeSocket(token);
      socketRef.current = ws;

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);

          if (payload.type === "CONVERSION_PING") {
            const data: ConversionPing = payload.data;

            setRevenueFlash(true);
            setTimeout(() => setRevenueFlash(false), 1000);

            setAnalytics(prev => {
              if (!prev) return prev;
              const newKpis = [...prev.kpis];
              // First KPI is usually Revenue
              if (newKpis[0]) {
                newKpis[0] = { ...newKpis[0], value: newKpis[0].value + data.revenue };
              }
              return { ...prev, kpis: newKpis };
            });

            // 3. Add temporary map ping
            const newPing: MapLocation = {
              lat: data.latitude,
              lng: data.longitude,
              name: `Conversion: $${data.revenue}`,
              type: 'ping',
              revenue: data.revenue
            };

            setLivePings(prev => [newPing, ...prev].slice(0, 10)); // Keep last 10
          }
        } catch (e) {
          console.error("Dashboard WS: Error processing message", e);
        }
      };

      ws.onclose = () => {
        console.log("Dashboard WS: Closed. Reconnecting in 5s...");
        setTimeout(connectSocket, 5000);
      };
    };

    connectSocket();

    return () => {
      if (socketRef.current) socketRef.current.close();
    };
  }, []);

  const combinedLocations = [...mapLocations, ...livePings];

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const item = {
    hidden: { opacity: 0, scale: 0.95 },
    show: { opacity: 1, scale: 1 }
  };

  return (
    <Layout>
      <div className="relative min-h-screen bg-background overflow-hidden -m-6 p-6">
        {/* Advanced Mesh Background */}
        <div className="fixed inset-0 pointer-events-none z-0">
          <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-primary/15 dark:bg-primary/10 rounded-full blur-[160px] animate-pulse" />
          <div className="absolute bottom-[-10%] right-[-10%] w-[45%] h-[45%] bg-teal-500/10 dark:bg-indigo-500/10 rounded-full blur-[180px]" />
          <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-teal-600/15 dark:bg-teal-600/10 rounded-full blur-[160px] animate-pulse [animation-delay:2s]" />
        </div>

        <div className="relative z-10 space-y-8 max-w-[1700px] mx-auto">
          {/* Refined Header Area */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="space-y-1">
              <h1 className="text-4xl md:text-6xl font-black text-foreground tracking-tighter font-heading leading-tight translate-x-[-2px]">
                Welcome back, <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary via-cyan-400 to-indigo-500">{user?.first_name || "Agent"}</span>
              </h1>

              <div className="flex flex-wrap items-center gap-4 mt-4">
                <div className="flex items-center gap-2 px-3 py-1.5 bg-primary/5 dark:bg-muted/30 border border-primary/20 dark:border-border rounded-full backdrop-blur-xl shadow-inner">
                  <span className="relative flex h-2 w-2">
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-primary shadow-[0_0_8px_hsl(var(--primary))]"></span>
                  </span>
                  <p className="text-primary dark:text-muted-foreground text-[10px] font-mono uppercase tracking-[0.2em] font-bold">
                    Intelligence Stream Active
                  </p>
                </div>
                <div className="hidden sm:block h-4 w-[1px] bg-border/50" />
                <p className="text-muted-foreground dark:text-muted-foreground/40 text-[9px] font-mono uppercase tracking-[0.3em] font-medium italic">
                  Analyzing Real-Time Market Signals
                </p>
              </div>
            </div>

            <Button
              variant="outline"
              size="icon"
              onClick={() => {
                setLoading(true);
                dashboardService.getSummary().then(setAnalytics).finally(() => setLoading(false));
              }}
              className="bg-background dark:bg-card/20 border-border/50 hover:border-primary/50 text-foreground w-14 h-14 rounded-2xl group transition-all relative overflow-hidden backdrop-blur-3xl shadow-lg dark:shadow-xl"
              title="Refresh Dashboard"
            >
              <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity" />
              <RefreshCw className={`w-5 h-5 transition-transform group-hover:rotate-180 relative z-10 ${loading ? 'animate-spin' : ''}`} />
            </Button>
          </div>

          {/* 1. Real-time KPI Strip */}
          <KPIStrip businessId={activeBusinessId} />

          {/* 2. Intelligence & Activity Surface */}
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <PerformanceCharts businessId={activeBusinessId} />
            </div>
            <div>
              <ActivityFeed businessId={activeBusinessId} />
            </div>
          </div>

          {/* Deployment Lifecycle Timeline (Next 24h) */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <RefreshCw className="w-4 h-4 text-primary" />
                <h2 className="text-sm font-bold text-foreground/70 font-heading uppercase tracking-[0.4em]">Deployment Lifecycle // Next 24H</h2>
              </div>
              <Badge variant="outline" className="border-primary/20 text-primary font-mono text-[10px] uppercase">
                Synchronized: {analytics?.deployment_timeline.length || 0} Events
              </Badge>
            </div>

            <div className="flex gap-4 overflow-x-auto pb-4 custom-scrollbar">
              {loading ? (
                Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="min-w-[280px] h-32 rounded-xl bg-secondary/30 dark:bg-card/40 animate-pulse border border-border/10" />
                ))
              ) : (
                analytics?.deployment_timeline.map((post) => (
                  <HolographicCard key={post.id} className="min-w-[280px] p-3 border-primary/10 bg-secondary/20 dark:bg-card/20 group">
                    <div className="flex gap-4 h-full">
                      <div className="w-20 h-20 rounded-lg overflow-hidden shrink-0 border border-border/50">
                        <img src={post.media_url} alt="Post" className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" />
                      </div>
                      <div className="flex flex-col justify-between overflow-hidden">
                        <div>
                          <p className="text-[10px] font-mono font-bold text-primary uppercase">{post.platform}</p>
                          <p className="text-[11px] text-muted-foreground truncate w-full font-mono mt-1">{post.caption || "No caption"}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge className="bg-foreground/5 text-muted-foreground border-0 text-[10px] font-mono px-0">
                            {new Date(post.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </Badge>
                          <div className="w-1 h-1 rounded-full bg-primary" />
                          <span className="text-[10px] font-mono text-primary/80 uppercase tracking-tighter">Ready</span>
                        </div>
                      </div>
                    </div>
                  </HolographicCard>
                ))
              )}
              {!loading && analytics?.deployment_timeline.length === 0 && (
                <div className="w-full py-10 rounded-xl bg-foreground/5 border border-dashed border-border/30 flex items-center justify-center">
                  <p className="text-[10px] font-mono uppercase tracking-[0.3em] text-muted-foreground">No deployments pending for next 24H</p>
                </div>
              )}
            </div>
          </div>


          {/* Visual & Strategic Analysis Section */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 mb-2">
              <Radio className="w-4 h-4 text-primary" />
              <h2 className="text-sm font-bold text-foreground/70 font-heading uppercase tracking-[0.4em]">Live Attribution & Strategic Decisions</h2>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">

              {/* Lead Heatmap (Map) */}
              <HolographicCard
                className="md:col-span-2 lg:col-span-4 p-0 overflow-hidden h-[450px] border-primary/20 shadow-lg dark:shadow-2xl"
                contentClassName="h-full flex flex-col"
              >
                <div className="p-6 pb-2 z-10 flex justify-between items-center bg-secondary/50 dark:bg-black/20 backdrop-blur-sm">
                  <h3 className="text-lg font-bold text-foreground font-heading uppercase tracking-wide">Live Attribution Radar</h3>
                  <Badge className="bg-primary/10 text-primary border-primary/20 font-mono text-[9px] px-2 h-4">SIGNAL_SYNC: OK</Badge>
                </div>
                <div className="flex-1 relative w-full min-h-0 overflow-hidden rounded-b-xl border border-border">
                  <GoogleMap center={mapCenter} zoom={12} locations={combinedLocations} height="100%" />

                  {/* Custom Legend Overlay */}
                  <div className="absolute bottom-6 left-6 bg-card/90 backdrop-blur-md border border-border/50 p-4 rounded-xl flex flex-col gap-3 text-[10px] z-10 shadow-2xl">
                    <div className="flex items-center gap-3">
                      <span className="relative flex h-3 w-3">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                      </span>
                      <span className="text-foreground font-mono font-bold tracking-tight">HQ: {user?.first_name}'s Base</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="relative flex h-3 w-3">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-3 w-3 bg-primary"></span>
                      </span>
                      <span className="text-foreground font-mono font-bold tracking-tight uppercase">Active Conversion Ping</span>
                    </div>
                  </div>
                </div>
              </HolographicCard>

              {/* Strategic Decisions */}
              <HolographicCard
                className="md:col-span-2 lg:col-span-3 p-6 h-[450px] border-primary/10 bg-black/10"
                contentClassName="h-full flex flex-col"
              >
                <div className="flex items-center justify-between mb-8">
                  <h3 className="text-lg font-bold text-foreground font-heading uppercase tracking-widest">Strategic Decisions</h3>
                  <Sparkles className="w-4 h-4 text-primary animate-pulse" />
                </div>

                <div className="space-y-4 overflow-y-auto pr-2 custom-scrollbar flex-1 min-h-0">
                  <AnimatePresence initial={false}>
                    {(analytics?.strategic_insights || []).length > 0 ? (
                      analytics?.strategic_insights.map((insight) => (
                        <motion.div
                          key={insight.id}
                          initial={{ opacity: 0, x: 20 }}
                          animate={{ opacity: 1, x: 0 }}
                          className="p-5 rounded-xl bg-foreground/5 border border-border/40 hover:border-primary/50 transition-all group relative cursor-pointer"
                        >
                          <div className="flex justify-between items-start mb-2">
                            <div className="flex gap-3">
                              <div className={`mt-1.5 w-2 h-2 rounded-full shrink-0 shadow-lg ${insight.color === 'emerald' ? 'bg-emerald-500 shadow-emerald-500/50' :
                                  insight.color === 'yellow' ? 'bg-yellow-500 shadow-yellow-500/50' : 'bg-red-500 shadow-red-500/50'
                                }`} />
                              <div>
                                <p className="text-[11px] font-bold text-foreground uppercase tracking-widest font-mono mb-1">{insight.type}: {insight.title}</p>
                                <p className="text-[11px] text-muted-foreground font-mono leading-relaxed">{insight.message}</p>
                              </div>
                            </div>
                          </div>
                          <div className="mt-3 pt-3 border-t border-border/40 flex justify-between items-center text-[10px] font-mono">
                            <span className="text-muted-foreground uppercase opacity-80">IMPACT: <span className="text-primary font-bold">{insight.impact}</span></span>
                            <ArrowRight className="w-3 h-3 text-primary opacity-0 group-hover:opacity-100 transition-all translate-x-1 group-hover:translate-x-0" />
                          </div>
                        </motion.div>
                      ))
                    ) : (
                      <div className="flex flex-col items-center justify-center h-full opacity-40 py-10 space-y-2">
                        <BarChart3 className="w-10 h-10 mb-2" />
                        <p className="text-[9px] font-mono uppercase tracking-[0.4em] text-center">Awaiting signal inference...</p>
                      </div>
                    )}
                  </AnimatePresence>
                </div>
              </HolographicCard>
            </div>
          </div>

          {/* 4. Actionable Intelligence Strip */}
          <div className="pt-4">
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="w-4 h-4 text-primary" />
              <h2 className="text-sm font-bold text-foreground/70 font-heading uppercase tracking-[0.4em]">Recommended Operations</h2>
            </div>
            <ActionableIntelligence businessId={activeBusinessId} />
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Dashboard;
