import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Users, Target, ExternalLink, MessageSquare, AlertTriangle } from "lucide-react";
import { useQuery } from '@tanstack/react-query';
import { instagramService } from '@/services/instagramService';
import { trendService } from '@/services/trendService';
import { autoReplyService } from "@/services/autoReplyService";
import { NumberTicker } from "@/components/ui/number-ticker";
import { cn } from "@/lib/utils";
import { Link } from "react-router-dom";

interface KPIStripProps {
  businessId: string;
}

type KPIItem = {
  label: string;
  value: number;
  subValue?: string | null;
  cta?: { label: string; route: string } | null;
  icon: any;
  color: string;
  bg: string;
  loading: boolean;
  suffix?: string;
};

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

  // 3. Comment & Escalation stats
  const { data: commentStats, isLoading: statsLoading } = useQuery({
    queryKey: ['auto-reply-dashboard-stats'],
    queryFn: () => autoReplyService.getDashboardStats(),
    refetchInterval: 30000,
  });

  // 4. Connection Statuses
  const { data: socialStatus, isLoading: statusLoading } = useQuery({
    queryKey: ['social-status-kpi'],
    queryFn: () => instagramService.getSocialConnectionStatus(),
  });

  const kpis: KPIItem[] = [
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
      label: "Total Comments",
      value: (commentStats as any)?.comments_all_time?.total || 0,
      subValue: `FB ${(commentStats as any)?.comments_all_time?.facebook || 0} · IG ${(commentStats as any)?.comments_all_time?.instagram || 0} · All-time`,
      cta: { label: "View Auto Replies", route: "/dashboard/auto-replies" },
      icon: MessageSquare,
      color: "text-cyan-400",
      bg: "bg-cyan-500/10",
      loading: statsLoading
    },

    {
      label: "Escalations (Open)",
      value: commentStats?.escalations?.open || 0,
      subValue: commentStats?.escalations?.soonest_sla_due_at
        ? `Next SLA: ${new Date(commentStats.escalations.soonest_sla_due_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
        : "No SLA due",
      cta: { label: "View Escalations", route: "/dashboard/escalations" },
      icon: AlertTriangle,
      color: "text-destructive",
      bg: "bg-destructive/10",
      loading: statsLoading
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
        <Card
          key={idx}
          className={cn(
            "p-6 bg-card/40 backdrop-blur-md border-border/10 group relative overflow-hidden",
            "transition-all duration-300 will-change-transform",
            "hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-[0_0_32px_rgba(0,224,208,0.14)]",
            // Edge highlight / glow
            "before:content-[''] before:absolute before:inset-0 before:rounded-xl before:pointer-events-none",
            "before:ring-1 before:ring-inset before:ring-primary/0 group-hover:before:ring-primary/35",
            "before:transition-[box-shadow,ring-color] before:duration-300",
            "group-hover:before:shadow-[inset_0_0_0_1px_rgba(0,224,208,0.12)]"
          )}
        >
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
