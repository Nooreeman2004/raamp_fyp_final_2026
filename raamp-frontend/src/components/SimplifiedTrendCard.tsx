import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { MapPin, Sparkles } from "lucide-react";

export interface SimplifiedTrend {
  id: string;
  topic: string;
  opportunity_level: "high" | "medium" | "low";
  why_relevant: string;
  suggested_action: string;
  location?: string;
  niche?: string;
  detected_at?: string;
}

export interface SimplifiedTrendCardProps {
  trend: SimplifiedTrend;
  onCreatePost: (topic: string) => void;
}

const OpportunityBadge = ({ level }: { level: "high" | "medium" | "low" }) => {
  const config = {
    high: { emoji: "🟢", label: "High Opportunity", className: "bg-emerald-500/20 text-emerald-400 border-emerald-500/50" },
    medium: { emoji: "🟡", label: "Medium Opportunity", className: "bg-amber-500/20 text-amber-400 border-amber-500/50" },
    low: { emoji: "🔴", label: "Low Opportunity", className: "bg-orange-500/20 text-orange-400 border-orange-500/50" },
  };

  const { emoji, label, className } = config[level];

  return (
    <Badge className={`${className} border font-semibold text-sm flex items-center gap-2 px-3 py-1.5`}>
      <span className="text-base">{emoji}</span>
      {label}
    </Badge>
  );
};

export const SimplifiedTrendCard = ({ trend, onCreatePost }: SimplifiedTrendCardProps) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="relative group rounded-2xl p-6 flex flex-col gap-5 transition-all overflow-hidden shadow-lg hover:shadow-xl ring-1 ring-border/60 hover:ring-border dark:ring-white/5 dark:hover:ring-white/10"
    >
      {/* Background */}
      <div className="absolute inset-0 rounded-2xl border backdrop-blur-xl border-border/60 bg-card/70 dark:border-white/10 dark:bg-white/[0.03]" />
      <div className="absolute -top-20 -right-20 h-48 w-48 rounded-full blur-[60px] bg-foreground/5 dark:bg-white/5" />
      
      <div className="relative z-10 flex flex-col gap-5">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-2 flex-1">
            <h3 className="text-2xl font-bold font-heading text-foreground tracking-tight capitalize leading-tight dark:text-white">
              {trend.topic}
            </h3>
            {trend.location && (
              <div className="flex items-center gap-2 text-xs text-muted-foreground dark:text-white/40">
                <MapPin className="w-3 h-3" />
                <span>{trend.location}</span>
              </div>
            )}
          </div>
          <OpportunityBadge level={trend.opportunity_level} />
        </div>

        {/* Why Relevant */}
        <div className="space-y-2">
          <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Why This Matters
          </div>
          <p className="text-sm text-foreground/90 dark:text-white/80 leading-relaxed">
            {trend.why_relevant}
          </p>
        </div>

        {/* Suggested Action */}
        <div className="space-y-2">
          <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            What To Do
          </div>
          <p className="text-sm text-foreground/90 dark:text-white/80 leading-relaxed">
            {trend.suggested_action}
          </p>
        </div>

        {/* Action Button */}
        <div className="pt-3 border-t border-border/60 dark:border-white/5">
          <Button
            onClick={() => onCreatePost(trend.topic)}
            className="w-full bg-primary hover:bg-primary/90 text-black rounded-xl font-bold text-sm h-11 shadow-lg hover:shadow-xl transition-all transform hover:-translate-y-0.5 active:translate-y-0 group"
          >
            <Sparkles className="w-4 h-4 mr-2 group-hover:scale-110 transition-transform" />
            Create Post
          </Button>
        </div>
      </div>
    </motion.div>
  );
};
