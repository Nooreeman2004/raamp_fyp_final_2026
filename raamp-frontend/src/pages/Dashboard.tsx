import { useState, useEffect } from "react";
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
  ArrowRight
} from "lucide-react";
import { motion } from "framer-motion";
import { HolographicCard } from "@/components/ui/holographic-card";
import { BlurText } from "@/components/ui/text-reveal";
import { MaskedTextReveal } from "@/components/ui/masked-text-reveal";
import { MagneticButton } from "@/components/ui/magnetic-button";
import { NumberTicker } from "@/components/ui/number-ticker";
import { LineChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid } from "recharts";
import { authService } from "@/services/authService";
import { businessService } from "@/services/businessService";
import type { UserResponse } from "@/types";
import GoogleMap from "@/components/GoogleMap";
import { CardSkeleton, ChartSkeleton } from "@/components/ui/card-skeleton";

// Mock Data
const performanceData = [
  { name: "Mon", value: 4000 },
  { name: "Tue", value: 3000 },
  { name: "Wed", value: 5000 },
  { name: "Thu", value: 2780 },
  { name: "Fri", value: 1890 },
  { name: "Sat", value: 2390 },
  { name: "Sun", value: 3490 },
];

type MapLocation = {
  lat: number;
  lng: number;
  name?: string;
  address?: string;
};

const Dashboard = () => {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [mapCenter, setMapCenter] = useState<{ lat: number; lng: number }>({
    lat: 24.8607,
    lng: 67.0011,
  });
  const [mapLocations, setMapLocations] = useState<MapLocation[]>([]);
  const [timeRange, setTimeRange] = useState(() => {
    return localStorage.getItem("dashboard_time_range") || "Last 7 Days";
  });

  useEffect(() => {
    localStorage.setItem("dashboard_time_range", timeRange);
  }, [timeRange]);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const userData = await authService.getProfile();
        setUser(userData);
      } catch (error) {
        console.error("Failed to fetch user", error);
      } finally {
        setLoading(false);
      }
    };
    fetchUser();
  }, []);

  useEffect(() => {
    const fetchHyperlocalLocation = async () => {
      try {
        const data = await businessService.getHyperlocalSetup();
        console.log('Dashboard: Fetched hyperlocal setup:', data);
        
        if (data && typeof data.latitude === "number" && typeof data.longitude === "number" && data.latitude !== 0 && data.longitude !== 0) {
          const base = { lat: data.latitude, lng: data.longitude };
          console.log('Dashboard: Setting map center to:', base);
          setMapCenter(base);

          const businessName = data.business_name || "Your Business Location";
          const address = data.formatted_address || undefined;

          // Single red pin at the saved business location
          setMapLocations([
            { lat: base.lat, lng: base.lng, name: businessName, address },
          ]);
          console.log('Dashboard: Set map location with marker');
        } else {
          console.log('Dashboard: No valid location data found');
        }
      } catch (error: any) {
        // 404 is expected when no location setup exists yet
        if (error?.status !== 404 && error?.response?.status !== 404) {
          console.error("Failed to fetch hyperlocal setup", error);
        } else {
          console.log('Dashboard: No hyperlocal setup found (404 - this is expected for new users)');
        }
      }
    };

    fetchHyperlocalLocation();
  }, []);

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05 // Tightened from 0.1
      }
    }
  };

  const item = {
    hidden: { opacity: 0, y: 10 }, // Reduced y offset for snappier feel
    show: { opacity: 1, y: 0 }
  };

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <MaskedTextReveal
              text={`Welcome back, ${user?.first_name || "Commander"}`}
              className="text-3xl font-bold tracking-tight text-white"
              tag="h1"
            />
            <p className="text-muted-foreground mt-1">
              Here's what's happening with your campaigns today.
            </p>
          </div>
          <div className="flex gap-3">
            <MagneticButton
              onClick={() => {
                const nextRange = timeRange === "Last 7 Days" ? "Last 30 Days" : "Last 7 Days";
                setTimeRange(nextRange);
              }}
              className="px-4 py-2 border border-white/10 text-white hover:bg-white/5 bg-transparent"
            >
              {timeRange}
            </MagneticButton>
            <MagneticButton className="px-4 py-2 bg-primary text-primary-foreground hover:bg-primary/90 shadow-[0_0_15px_rgba(0,224,208,0.3)]">
              <Zap className="w-4 h-4 mr-2" />
              Quick Action
            </MagneticButton>
          </div>
        </div>

        {/* Metrics Grid */}
        <motion.div
          variants={container}
          initial="hidden"
          animate="show"
          className="grid gap-4 md:grid-cols-2 lg:grid-cols-4"
        >
          {loading ? (
            Array.from({ length: 4 }).map((_, i) => (
              <motion.div key={i} variants={item}>
                <CardSkeleton />
              </motion.div>
            ))
          ) : (
            [
              { title: "Total Revenue", value: 45231, prefix: "$", change: "+20.1%", icon: DollarSignIcon, trend: "up" },
              { title: "Active Campaigns", value: 12, change: "+3", icon: Activity, trend: "up" },
              { title: "Total Leads", value: 573, change: "+12.5%", icon: Users, trend: "up" },
              { title: "Avg. CPC", value: 1.24, prefix: "$", change: "-4.3%", icon: Target, trend: "down" },
            ].map((metric, i) => (
              <motion.div key={i} variants={item}>
                <HolographicCard className="p-6">
                  <div className="flex items-center justify-between space-y-0 pb-2">
                    <p className="text-sm font-medium text-muted-foreground">{metric.title}</p>
                    <metric.icon className="h-4 w-4 text-primary" />
                  </div>
                  <div className="flex items-baseline justify-between pt-2">
                    <div className="text-2xl font-bold text-white flex items-center">
                      {metric.prefix && <span>{metric.prefix}</span>}
                      <NumberTicker value={metric.value} />
                    </div>
                    <Badge variant="outline" className={`border-0 ${metric.trend === 'up' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-red-500/10 text-red-500'}`}>
                      {metric.trend === 'up' ? <ArrowUpRight className="h-3 w-3 mr-1" /> : <ArrowDownRight className="h-3 w-3 mr-1" />}
                      {metric.change}
                    </Badge>
                  </div>
                </HolographicCard>
              </motion.div>
            ))
          )}
        </motion.div>

        {/* Main Content Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">

          {/* Chart Section - Now Full Width */}
          <div className="col-span-7">
            {loading ? (
              <ChartSkeleton />
            ) : (
              <HolographicCard className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h3 className="text-lg font-semibold text-white">Revenue Overview</h3>
                    <p className="text-sm text-muted-foreground">Compare against previous period</p>
                  </div>
                  <Button variant="ghost" size="sm" className="text-primary hover:text-primary/80">
                    View Report
                  </Button>
                </div>
                <div className="h-[300px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={performanceData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                      <XAxis
                        dataKey="name"
                        stroke="#64748b"
                        fontSize={12}
                        tickLine={false}
                        axisLine={false}
                      />
                      <YAxis
                        stroke="#64748b"
                        fontSize={12}
                        tickLine={false}
                        axisLine={false}
                        tickFormatter={(value) => `$${value}`}
                      />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#09151E', borderColor: '#1e293b', color: '#fff' }}
                        itemStyle={{ color: '#00E0D0' }}
                      />
                      <Line
                        type="monotone"
                        dataKey="value"
                        stroke="#00E0D0"
                        strokeWidth={3}
                        dot={{ r: 4, fill: "#09151E", strokeWidth: 2 }}
                        activeDot={{ r: 6, fill: "#00E0D0" }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </HolographicCard>
            )}
          </div>
        </div>

        {/* Visual & Strategic Analysis Section */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-white/90 tracking-wide uppercase text-sm">Visual & Strategic Analysis</h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">

            {/* Lead Heatmap & Demographics (Map) */}
            <HolographicCard
              className="col-span-4 p-0 overflow-hidden h-[400px]"
              contentClassName="h-full flex flex-col"
            >
              <div className="p-6 pb-2 z-10">
                <h3 className="text-lg font-semibold text-white">Lead Heatmap & Demographics</h3>
              </div>
              <div className="flex-1 relative w-full h-full min-h-0">
                <GoogleMap
                  center={mapCenter}
                  zoom={12}
                  locations={mapLocations}
                  height="100%"
                />
                {/* Custom Legend Overlay */}
                <div className="absolute bottom-4 left-4 bg-[#09151E]/90 backdrop-blur-md border border-white/10 p-3 rounded-lg flex gap-4 text-xs z-10">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-red-500"></div>
                    <span className="text-white">Pinned Business Location</span>
                  </div>
                  <div className="flex items-center gap-1 text-primary cursor-pointer hover:underline ml-2">
                    <span>Explore Geo-Intent Module</span>
                    <ArrowUpRight className="w-3 h-3" />
                  </div>
                </div>
              </div>
            </HolographicCard>

            {/* Causal Insights & Actions */}
            <HolographicCard
              className="col-span-3 p-6 h-[400px]"
              contentClassName="h-full flex flex-col"
            >
              <h3 className="text-lg font-semibold text-white mb-6">Causal Insights & Actions</h3>
              <div className="space-y-4 overflow-y-auto pr-2 custom-scrollbar flex-1 min-h-0">

                {/* Insight 1: Action */}
                <div className="p-4 rounded-lg bg-white/5 border border-white/5 hover:bg-white/10 transition-colors">
                  <div className="flex gap-3">
                    <div className="mt-1.5 w-2 h-2 rounded-full bg-yellow-400 shrink-0 shadow-[0_0_8px_rgba(250,204,21,0.5)]" />
                    <div>
                      <p className="text-sm text-white leading-relaxed">
                        <span className="font-bold text-white">Action:</span> Increase Budget for Social Media Ads <span className="text-muted-foreground">(highest positive impact on ROAS this week)</span>
                      </p>
                    </div>
                  </div>
                </div>

                {/* Insight 2: Caution */}
                <div className="p-4 rounded-lg bg-white/5 border border-white/5 hover:bg-white/10 transition-colors">
                  <div className="flex gap-3">
                    <div className="mt-1.5 w-2 h-2 rounded-full bg-red-500 shrink-0 shadow-[0_0_8px_rgba(239,68,68,0.5)]" />
                    <div>
                      <p className="text-sm text-white leading-relaxed">
                        <span className="font-bold text-white">Caution:</span> Review Legacy Ad Spend <span className="text-muted-foreground">(showing a -.8% negative influence on Conversion Rate)</span>
                      </p>
                    </div>
                  </div>
                </div>

                {/* Insight 3: Suggestion */}
                <div className="p-4 rounded-lg bg-white/5 border border-white/5 hover:bg-white/10 transition-colors">
                  <div className="flex gap-3">
                    <div className="mt-1.5 w-2 h-2 rounded-full bg-emerald-500 shrink-0 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
                    <div>
                      <p className="text-sm text-white leading-relaxed">
                        <span className="font-bold text-white">Suggestion:</span> Explore better performing age <span className="text-muted-foreground">aligned with the "Early Adopter" segment for maximum reach.</span>
                      </p>
                    </div>
                  </div>
                </div>

                <div className="pt-2">
                  <Button variant="link" className="text-primary p-0 h-auto text-sm hover:text-primary/80">
                    View Complete Insights Log <ArrowRight className="w-4 h-4 ml-1" />
                  </Button>
                </div>

              </div>
            </HolographicCard>
          </div>
        </div>
      </div>
    </Layout>
  );
};

// Helper Icon
const DollarSignIcon = ({ className }: { className?: string }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <line x1="12" x2="12" y1="2" y2="22" />
    <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
  </svg>
);

export default Dashboard;
