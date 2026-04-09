import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Users, Activity, Target, Zap, ExternalLink } from "lucide-react";
import { useQuery } from '@tanstack/react-query';
import { instagramService } from '@/services/instagramService';
import { geoIntentService } from '@/services/geoIntentService';
import { trendService } from '@/services/trendService';
import { businessService } from '@/services/businessService';
import { NumberTicker } from "@/components/ui/number-ticker";
import { cn } from "@/lib/utils";
import { Link } from "react-router-dom";

interface KPIStripProps {
  businessId: string;
}

export const KPIStrip = ({ businessId }: KPIStripProps) => {
  // 1. ROI & Reach
  const { data: roiSummary, isLoading: roiLoading } = useQuery({
    queryKey: ['roi-summary', businessId],
    queryFn: () => instagramService.getROISummary(businessId),
    enabled: !!businessId,
    refetchInterval: 60000 
  });

  // 2. Active Trends Count
  const { data: watchlist, isLoading: trendsLoading } = useQuery({
    queryKey: ['watchlist-count'],
    queryFn: () => trendService.getWatchlist(),
    refetchInterval: 30000
  });

  // 3. Current Heat Score
  const { data: geoHistory, isLoading: geoLoading } = useQuery({
    queryKey: ['geo-history-recent', businessId],
    queryFn: () => geoIntentService.getHistory(businessId, 1),
    enabled: !!businessId
  });
  const recentHeat = geoHistory?.[0];

  // 4. Connection Statuses
  const { data: socialStatus, isLoading: statusLoading } = useQuery({
    queryKey: ['social-status-kpi'],
    queryFn: () => instagramService.getSocialConnectionStatus(),
  });

  const { data: hyperlocalSetup, isLoading: setupLoading } = useQuery({
    queryKey: ['hyperlocal-setup-kpi'],
    queryFn: () => businessService.getHyperlocalSetup(),
  });

  const kpis = [
    {
      label: "Total Reach",
      value: roiSummary?.total_reach || 0,
      subValue: roiSummary?.total_reach ? "Syncing..." : (socialStatus?.instagram_connected ? "No data found" : null),
      cta: !socialStatus?.instagram_connected && !statusLoading ? { label: "Connect Instagram", route: "/profile/onboarding" } : null,
      icon: Users,
      color: "text-teal-400",
      bg: "bg-teal-500/10",
      loading: roiLoading || statusLoading
    },
    {
      label: "Avg Engagement",
      value: roiSummary?.avg_engagement_rate || 0,
      suffix: "%",
      subValue: roiSummary?.avg_engagement_rate ? "Monitoring signals..." : (socialStatus?.instagram_connected ? "Awaiting insights" : null),
      cta: !socialStatus?.instagram_connected && !statusLoading ? { label: "Verify Connections", route: "/profile/onboarding" } : null,
      icon: Activity,
      color: "text-emerald-400",
      bg: "bg-emerald-500/10",
      loading: roiLoading || statusLoading
    },

    {
      label: "Market Heat Index",
      value: recentHeat?.max_score || 0,
      subValue: recentHeat?.urgency ? `Urgency: ${recentHeat.urgency}` : (hyperlocalSetup?.has_setup ? "No active scans" : null),
      cta: !hyperlocalSetup?.has_setup && !setupLoading ? { label: "Configure Location", route: "/profile/onboarding" } : (!recentHeat?.max_score && !geoLoading ? { label: "Run Market Scan", route: "/dashboard/geo-intent" } : null),
      icon: Zap,
      color: "text-indigo-400",
      bg: "bg-indigo-500/10",
      loading: geoLoading || setupLoading
    },
    {
      label: "Active Trends",
      value: watchlist?.length || 0,
      subValue: (watchlist?.length || 0) > 0 ? `${watchlist?.filter((t: any) => t.last_arbitrage_score > 70).length} high velocity` : "Monitoring global trends",
      cta: !(watchlist?.length) && !trendsLoading ? { label: "Explore Trends", route: "/dashboard/trends" } : null,
      icon: Target,
      color: "text-amber-400",
      bg: "bg-amber-500/10",
      loading: trendsLoading
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {kpis.map((kpi, idx) => (
        <Card key={idx} className="p-6 bg-card/40 backdrop-blur-md border-border/10 hover:border-primary/20 transition-all group relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
            <kpi.icon className="w-24 h-24" />
          </div>
          
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-4">
              <div className={cn("p-2 rounded-lg", kpi.bg)}>
                <kpi.icon className={cn("w-5 h-5", kpi.color)} />
              </div>
              {kpi.subValue && !kpi.loading && (
                <span className="text-[10px] font-mono font-medium uppercase tracking-wider text-muted-foreground bg-muted/30 px-2 py-0.5 rounded">
                  {kpi.subValue}
                </span>
              )}
            </div>
            
            <p className="text-sm font-medium text-muted-foreground/80 uppercase tracking-widest">{kpi.label}</p>
            
            {kpi.loading ? (
              <Skeleton className="h-9 w-24 mb-2 mt-2" />
            ) : (
              <div className="flex items-baseline gap-1 mt-1 mb-2">
                <span className="text-4xl lg:text-5xl font-black text-foreground tracking-tighter drop-shadow-sm">
                  <NumberTicker value={kpi.value} />
                </span>
                {kpi.suffix && <span className="text-lg font-bold text-muted-foreground/50">{kpi.suffix}</span>}
              </div>
            )}
            
            {!kpi.loading && kpi.cta && (
              <Link 
                to={kpi.cta.route}
                className="mt-4 flex items-center gap-1.5 text-xs font-bold text-primary hover:text-accent transition-colors group/link"
              >
                {kpi.cta.label}
                <ExternalLink className="w-3 h-3 transition-transform group-hover/link:translate-x-0.5 group-hover/link:-translate-y-0.5" />
              </Link>
            )}
          </div>
        </Card>
      ))}
    </div>
  );
}
