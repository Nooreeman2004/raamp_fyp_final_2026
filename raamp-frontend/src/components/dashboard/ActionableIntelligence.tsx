import { useQuery } from "@tanstack/react-query";
import { HolographicCard } from "@/components/ui/holographic-card";
import { Badge } from "@/components/ui/badge";
import { Sparkles, Clock, Star, ArrowRight, Zap, Trophy, Flame } from "lucide-react";
import { instagramService } from "@/services/instagramService";
import { geoIntentService } from "@/services/geoIntentService";
import { Skeleton } from "@/components/ui/skeleton";
import { Link } from "react-router-dom";

interface ActionableIntelligenceProps {
  businessId: string;
}

export const ActionableIntelligence = ({ businessId }: ActionableIntelligenceProps) => {
  // 1. ROI Summary for Top Content
  const { data: roiSummary, isLoading: roiLoading } = useQuery({
    queryKey: ['roi-summary-intel', businessId],
    queryFn: () => instagramService.getROISummary(businessId),
    enabled: !!businessId
  });

  // 2. Best Posting Time
  const { data: bestTime, isLoading: timeLoading } = useQuery({
    queryKey: ['best-posting-time', businessId],
    queryFn: () => geoIntentService.getBestPostingTime(businessId),
    enabled: !!businessId
  });

  // 3. Recent Opportunity Spikes
  const { data: geoHistory, isLoading: geoLoading } = useQuery({
    queryKey: ['geo-history-intel', businessId],
    queryFn: () => geoIntentService.getHistory(businessId, 5),
    enabled: !!businessId
  });

  const highUrgencyLogs = geoHistory?.logs?.filter(l => l.urgency === 'High' || l.urgency === 'Critical') || [];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      {/* Best Posting Window */}
      <HolographicCard className="p-6 relative overflow-hidden group">
        <Badge variant="outline" className="mb-4 bg-teal-500/5 text-teal-500 border-teal-500/20">
          Optimal Timing
        </Badge>
        <h3 className="text-lg font-bold flex items-center gap-2 mb-4 group-hover:text-teal-400 transition-colors">
          <Clock className="w-5 h-5" />
          Best Posting Window
        </h3>
        {timeLoading ? (
          <Skeleton className="h-20 w-full" />
        ) : bestTime && bestTime.best_day !== "N/A" ? (
          <div className="space-y-4">
            <div>
              <p className="text-2xl font-bold text-foreground">{bestTime.best_day}</p>
              <div className="flex flex-wrap gap-2 mt-2">
                {bestTime.best_hours.map((h, i) => (
                   <div key={i} className="px-2 py-1 bg-teal-500/10 rounded text-xs font-medium text-teal-400">
                    {h.hour > 12 ? `${h.hour-12} PM` : h.hour === 0 ? "12 AM" : h.hour === 12 ? "12 PM" : `${h.hour} AM`}
                   </div>
                ))}
              </div>
            </div>
            <p className="text-xs text-muted-foreground">Based on {bestTime.based_on_days} days of regional engagement analysis.</p>
          </div>
        ) : (
          <div className="py-4">
             <p className="text-sm text-muted-foreground italic">Insufficient signal data for predictive timing. Run more scans.</p>
          </div>
        )}
        <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity">
          <Clock className="w-24 h-24 rotate-12" />
        </div>
      </HolographicCard>

      {/* Top Performing Asset */}
      <HolographicCard className="p-6 relative overflow-hidden group">
        <Badge variant="outline" className="mb-4 bg-purple-500/5 text-purple-500 border-purple-500/20">
          Leaderboard
        </Badge>
        <h3 className="text-lg font-bold flex items-center gap-2 mb-4 group-hover:text-purple-400 transition-colors">
          <Trophy className="w-5 h-5" />
          Highest Impact Content
        </h3>
        {roiLoading ? (
          <Skeleton className="h-20 w-full" />
        ) : roiSummary?.best_performing_post ? (
          <div className="space-y-4">
             <div>
               <p className="text-sm text-muted-foreground mb-1">Top Reach Reach:</p>
               <p className="text-2xl font-bold text-foreground">{roiSummary.best_performing_post.reach.toLocaleString()}</p>
             </div>
             <Link to="/dashboard/assets" className="flex items-center gap-1 text-xs text-purple-400 hover:text-purple-300 font-medium group/link">
               View Strategy <ArrowRight className="w-3 h-3 group-hover/link:translate-x-1 transition-transform" />
             </Link>
          </div>
        ) : (
          <div className="py-4">
             <p className="text-sm text-muted-foreground italic">Map your published ROI first.</p>
          </div>
        )}
        <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity">
          <Star className="w-24 h-24 -rotate-12" />
        </div>
      </HolographicCard>

      {/* Recent Heat Spikes */}
      <HolographicCard className="p-6 relative overflow-hidden group border-rose-500/10">
        <Badge variant="outline" className="mb-4 bg-rose-500/5 text-rose-500 border-rose-500/20">
          Market Pulse
        </Badge>
        <h3 className="text-lg font-bold flex items-center gap-2 mb-4 group-hover:text-rose-400 transition-colors">
          <Flame className="w-5 h-5" />
          Active Heat Spikes
        </h3>
        {geoLoading ? (
          <Skeleton className="h-20 w-full" />
        ) : highUrgencyLogs.length > 0 ? (
          <div className="space-y-3">
            {highUrgencyLogs.slice(0, 2).map((log, i) => (
              <div key={i} className="flex justify-between items-center p-2 rounded-lg bg-rose-500/5 border border-rose-500/10">
                <div>
                   <p className="text-xs font-bold text-rose-400">{log.urgency.toUpperCase()} SPIKE</p>
                   <p className="text-xs text-muted-foreground">{new Date(log.timestamp).toLocaleTimeString()}</p>
                </div>
                <div className="text-lg font-bold text-foreground">{log.final_score}</div>
              </div>
            ))}
            <Link to="/geo-intent" className="flex items-center gap-1 text-xs text-rose-400 hover:text-rose-300 font-medium group/link">
               Open Radar <ArrowRight className="w-3 h-3 group-hover/link:translate-x-1 transition-transform" />
            </Link>
          </div>
        ) : (
          <div className="py-4">
             <p className="text-sm text-muted-foreground italic">Signals are currently stable.</p>
          </div>
        )}
        <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity">
          <Zap className="w-24 h-24 rotate-45" />
        </div>
      </HolographicCard>
    </div>
  );
};
