import { useQuery } from "@tanstack/react-query";
import { HolographicCard } from "@/components/ui/holographic-card";
import { Badge } from "@/components/ui/badge";
import { activityService, ActivityEvent } from "@/services/activityService";
import { instagramService } from "@/services/instagramService";
import { businessService } from "@/services/businessService";
import { Radio, Zap, Activity, Users, FileCheck, ArrowRight, TrendingUp, FileText } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";

interface ActivityFeedProps {
  businessId: string;
}

const getEventIcon = (type: string) => {
  switch (type) {
    case 'post_published': return { icon: Radio, bg: 'bg-teal-500/10', text: 'text-teal-500', link: '/assets' };
    case 'heat_spike': return { icon: FlameActivity, bg: 'bg-rose-500/10', text: 'text-rose-500', link: '/geo-intent' };
    case 'scan_completed': return { icon: Zap, bg: 'bg-teal-500/10', text: 'text-teal-500', link: '/trend-arbitrage' };
    case 'insight_updated': return { icon: Activity, bg: 'bg-purple-500/10', text: 'text-purple-500', link: '/assets' };
    case 'trend_detected': return { icon: TrendingUp, bg: 'bg-teal-500/10', text: 'text-teal-500', link: '/trend-arbitrage' };
    default: return { icon: FileCheck, bg: 'bg-slate-500/10', text: 'text-slate-500', link: '#' };
  }
};

const FlameActivity = ({ className }: { className?: string }) => (
    <div className={`relative ${className}`}>
        <Activity className={className} />
        <Zap className="absolute -top-1 -right-1 w-3 h-3 text-rose-500" />
    </div>
);

export const ActivityFeed = ({ businessId }: ActivityFeedProps) => {
  const { data: activities, isLoading: activitiesLoading } = useQuery({
    queryKey: ['activity-feed', businessId],
    queryFn: () => activityService.getActivityFeed(businessId, 6),
    enabled: !!businessId,
    refetchInterval: 30000 // Poll every 30 seconds
  });

  const { data: socialStatus, isLoading: statusLoading } = useQuery({
    queryKey: ['social-status-feed'],
    queryFn: () => instagramService.getSocialConnectionStatus(),
  });

  const { data: hyperlocalSetup, isLoading: setupLoading } = useQuery({
    queryKey: ['hyperlocal-setup-feed'],
    queryFn: () => businessService.getHyperlocalSetup(),
  });

  const isLoading = activitiesLoading || statusLoading || setupLoading;

  return (
    <HolographicCard className="p-6 h-full flex flex-col">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h3 className="text-lg font-black font-heading tracking-tight text-foreground truncate pl-1">Activity Feed</h3>
          <p className="text-xs text-muted-foreground mt-1 pl-1">Real-time system events</p>
        </div>
        <Badge variant="outline" className="animate-pulse bg-emerald-500/5 text-emerald-500 border-emerald-500/20">
          LIVE
        </Badge>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-16 w-full rounded-xl" />)}
        </div>
      ) : activities && activities.length > 0 ? (
        <div className="flex-1 overflow-y-auto pr-2 space-y-4 custom-scrollbar">
          <AnimatePresence initial={false}>
            {activities.map((event, idx) => {
              const config = getEventIcon(event.event_type);
              return (
                <motion.div
                  key={event.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.05 }}
                >
                  <Link 
                    to={config.link}
                    className="flex items-start gap-4 p-3 rounded-xl hover:bg-white/5 transition-colors border border-white/5 hover:border-white/10 group"
                  >
                    <div className={`p-2.5 rounded-xl ${config.bg} ${config.text}`}>
                       <config.icon className="w-5 h-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex justify-between items-start mb-0.5">
                        <p className="text-sm font-bold text-foreground truncate pr-4">{event.title}</p>
                        <p className="text-[10px] text-muted-foreground whitespace-nowrap">
                          {new Date(event.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </p>
                      </div>
                      <p className="text-xs text-muted-foreground line-clamp-1">{event.subtitle}</p>
                    </div>
                    <div className="self-center opacity-0 group-hover:opacity-100 transition-opacity">
                      <ArrowRight className="w-4 h-4 text-muted-foreground/30" />
                    </div>
                  </Link>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center text-center p-6 bg-muted/10 rounded-2xl border border-border mx-auto w-full overflow-hidden">
           <div className={`p-4 rounded-full bg-teal-500/5 mb-6 border border-teal-500/10 ${socialStatus?.instagram_connected ? 'animate-pulse' : ''}`}>
             <Radio className="w-10 h-10 text-teal-400/50" />
           </div>
           
           <div className="space-y-4 max-w-[240px]">
             <h3 className="text-sm font-bold text-foreground uppercase tracking-wider">
               {socialStatus?.instagram_connected ? "Engine Initialized" : "Engine Initialization"}
             </h3>
             <p className="text-xs text-muted-foreground/80 leading-relaxed">
               {socialStatus?.instagram_connected 
                 ? "Your system is live and awaiting signals. Take action to populate your feed:"
                 : "Your real-time audit trail is awaiting signal clusters. Start here:"}
             </p>
             
             <div className="space-y-2 text-left mt-6">
                {[
                  { label: "Trigger Market Scan", route: "/dashboard/geo-intent", icon: Zap, show: true },
                  { label: "Connect Instagram", route: "/profile/onboarding", icon: Users, show: !socialStatus?.instagram_connected },
                  { label: "Analyze Trends", route: "/dashboard/trends", icon: TrendingUp, show: true },
                  { label: "Create AI Post", route: "/dashboard/creative", icon: FileText, show: socialStatus?.instagram_connected }
                ].filter(item => item.show).map((item, i) => (
                  <Link 
                    key={i} 
                    to={item.route}
                    className="flex items-center gap-3 p-2.5 rounded-lg bg-foreground/5 border border-border hover:border-teal-500/30 hover:bg-teal-500/5 transition-all group"
                  >
                    <item.icon className="w-4 h-4 text-teal-400/40 group-hover:text-teal-400" />
                    <span className="text-[11px] font-bold text-foreground/70 group-hover:text-foreground transition-colors">
                      {item.label}
                    </span>
                  </Link>
                ))}
             </div>
           </div>
        </div>
      )}
    </HolographicCard>
  );
};
