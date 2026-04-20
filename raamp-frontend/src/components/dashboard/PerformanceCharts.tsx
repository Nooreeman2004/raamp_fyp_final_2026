import { useQuery } from "@tanstack/react-query";
import { HolographicCard } from "@/components/ui/holographic-card";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, LineChart, Line } from "recharts";
import { instagramService } from "@/services/instagramService";
import { geoIntentService } from "@/services/geoIntentService";
import { businessService } from "@/services/businessService";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, Activity, MapPin, Map, Zap, RefreshCw } from "lucide-react";

interface PerformanceChartsProps {
  businessId: string;
}

export const PerformanceCharts = ({ businessId }: PerformanceChartsProps) => {
  // 1. 30-Day Reach & Impressions
  const { data: roiHistory, isLoading: roiLoading } = useQuery({
    queryKey: ['roi-timeseries', businessId, 30],
    queryFn: () => instagramService.getROITimeseries(businessId, 30),
    enabled: !!businessId
  });

  // 2. 7-Day Geo Heat History
  const { data: geoHistory, isLoading: geoLoading } = useQuery({
    queryKey: ['geo-history-timeseries', businessId, 7],
    queryFn: () => geoIntentService.getHeatScoreHistory(businessId, 7),
    enabled: !!businessId
  });

  // 3. Connection Statuses
  const { data: socialStatus, isLoading: statusLoading } = useQuery({
    queryKey: ['social-status-charts'],
    queryFn: () => instagramService.getSocialConnectionStatus(),
  });

  const { data: hyperlocalSetup, isLoading: setupLoading } = useQuery({
    queryKey: ['hyperlocal-setup-charts'],
    queryFn: () => businessService.getHyperlocalSetup(),
  });

  const hasInstagramData = roiHistory && roiHistory.some((d: any) => d.reach > 0 || d.impressions > 0);
  const hasGeoData = geoHistory && geoHistory.length > 0;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-full">
      {/* Reach Growth Chart */}
      <HolographicCard className="p-6 flex flex-col min-h-[400px]">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h3 className="text-lg font-black font-heading tracking-tight text-foreground flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-teal-500" />
              Audience Reach Growth
            </h3>
            <p className="text-xs text-muted-foreground mt-1 pl-7">30-day cross-platform metrics</p>
          </div>
          <Badge variant="outline" className="bg-teal-500/5 text-teal-500 border-teal-500/20">
            Real-time
          </Badge>
        </div>

        {roiLoading || statusLoading ? (
          <div className="flex-1 w-full bg-slate-900/10 animate-pulse rounded-lg" />
        ) : hasInstagramData ? (
          <div className="flex-1 w-full min-h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={roiHistory.map((d: any) => ({ ...d, reach: d.reach || 0, impressions: d.impressions || 0 }))}>
                <defs>
                  <linearGradient id="colorReach" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#14b8a6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#14b8a6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                <XAxis 
                  dataKey="date" 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fontSize: 10, fill: '#888' }}
                  tickFormatter={(str) => {
                    const date = new Date(str);
                    return `${date.getMonth() + 1}/${date.getDate()}`;
                  }}
                  minTickGap={30}
                />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#888' }} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(20, 184, 166, 0.2)', borderRadius: '8px' }}
                  itemStyle={{ color: '#14b8a6' }}
                />
                <Area 
                  type="monotone" 
                  dataKey="reach" 
                  stroke="#14b8a6" 
                  fillOpacity={1} 
                  fill="url(#colorReach)" 
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-8 bg-foreground/5 rounded-xl border border-border/50">
             <div className="p-4 rounded-full bg-teal-500/10 mb-4 animate-pulse">
               {socialStatus?.instagram_connected ? (
                 <RefreshCw className="w-12 h-12 text-teal-400 animate-spin-slow" />
               ) : (
                 <Activity className="w-12 h-12 text-teal-400" />
               )}
             </div>
             <h3 className="text-lg font-semibold text-foreground mb-2">
               {socialStatus?.instagram_connected ? "Awaiting Reach Data" : "Growth Map Inactive"}
             </h3>
             <p className="text-sm text-muted-foreground max-w-[280px] mb-6">
               {socialStatus?.instagram_connected 
                 ? "Your Instagram account is connected. We're waiting for reach signals to populate your dashboard."
                 : "We haven't detected any audience reach signals. Connect your accounts to begin monitoring."}
             </p>
             <div className="flex flex-col gap-2 w-full max-w-[200px]">
               <button 
                 onClick={() => window.location.href = '/dashboard/creative'}
                 className="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white text-xs font-bold rounded-lg transition-all shadow-[0_0_15px_rgba(20,184,166,0.2)]"
               >
                 Deploy New Post
               </button>
               {!socialStatus?.instagram_connected && (
                 <button 
                   onClick={() => window.location.href = '/profile/onboarding'}
                    className="px-4 py-2 bg-foreground/5 hover:bg-foreground/10 text-muted-foreground text-xs font-bold rounded-lg transition-all"
                 >
                   Connect Instagram
                 </button>
               )}
             </div>
          </div>
        )}
      </HolographicCard>

      {/* Market Heat History */}
      <HolographicCard className="p-6 flex flex-col min-h-[400px]">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-indigo-500/10">
              <MapPin className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-foreground tracking-tight">Regional Heat Score Trends</h2>
              <p className="text-[10px] text-muted-foreground uppercase tracking-widest">Last 30 Market Scans</p>
            </div>
          </div>
          <div className="px-2 py-1 bg-white/5 rounded text-[10px] text-muted-foreground font-mono">
            LIVE ANALYTICS
          </div>
        </div>

        {geoLoading || setupLoading ? (
          <div className="flex-1 w-full bg-slate-900/10 animate-pulse rounded-lg" />
        ) : hasGeoData ? (
          <div className="flex-1 w-full min-h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={geoHistory}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                <XAxis 
                  dataKey="date" 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fontSize: 10, fill: '#888' }}
                  tickFormatter={(str) => {
                    const date = new Date(str);
                    return `${date.getHours()}:${date.getMinutes()}`;
                  }}
                  minTickGap={30}
                />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#888' }} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(99, 102, 241, 0.2)', borderRadius: '8px' }}
                  itemStyle={{ color: '#818cf8' }}
                />
                <Line 
                  type="monotone" 
                  dataKey="max_score" 
                  stroke="#6366f1" 
                  strokeWidth={3} 
                  dot={{ fill: '#6366f1', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6, strokeWidth: 0 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-8 bg-foreground/5 rounded-xl border border-border/50">
             <div className="p-4 rounded-full bg-indigo-500/10 mb-4 animate-pulse">
               {hyperlocalSetup?.has_setup ? (
                 <RefreshCw className="w-12 h-12 text-indigo-400 animate-spin-slow" />
               ) : (
                 <Zap className="w-12 h-12 text-indigo-400" />
               )}
             </div>
             <h3 className="text-lg font-semibold text-foreground mb-2">
               {hyperlocalSetup?.has_setup ? "Awaiting Scan Results" : "No Regional Signals"}
             </h3>
             <p className="text-sm text-muted-foreground max-w-[280px] mb-6">
               {hyperlocalSetup?.has_setup 
                 ? "Location configuration found. Run your first Hyperlocal scan to map arbitrage opportunities."
                 : "Configure your business location to map arbitrage opportunities in your area."}
             </p>
             <button 
               onClick={() => window.location.href = hyperlocalSetup?.has_setup ? '/dashboard/geo-intent' : '/profile/onboarding'}
               className="px-6 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-lg transition-all shadow-[0_0_15px_rgba(99,102,241,0.2)]"
             >
               {hyperlocalSetup?.has_setup ? "Start Geo-Intent Scan" : "Configure Location"}
             </button>
          </div>
        )}
      </HolographicCard>
    </div>
  );
};
