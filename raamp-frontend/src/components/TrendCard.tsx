import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { ThemeEmoji } from "@/components/ui/emoji";
import { TrendSpike } from "@/services/trendService";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  TrendingUp, Flame, Zap, Target, Activity, Sparkles, Rocket,
  TrendingDown, AlertCircle, MapPin, ArrowRight, Star
} from "lucide-react";
import { motion } from "framer-motion";

export interface TrendCardProps {
  trend: TrendSpike;
  onClick?: () => void;
  onMagicBridge?: (keyword: string) => void;
  onToggleWatchlist?: (keyword: string) => void;
  onToggleCompare?: (trend: TrendSpike) => void;
  isWatchlisted?: boolean;
  isActive?: boolean;
  isCompared?: boolean;
  // Strategy should be rendered on the Trends page (sections), not inside the card.
  strategy?: unknown;
}

const isFiniteNumber = (v: unknown): v is number => typeof v === "number" && Number.isFinite(v);

const fmtFixed = (v: unknown, digits = 0): string => {
  if (!isFiniteNumber(v)) return "—";
  try {
    return v.toFixed(digits);
  } catch {
    return "—";
  }
};

const DataQualityPill = ({ live, labelLive = "Live", labelEst = "Est" }: { live: boolean; labelLive?: string; labelEst?: string }) => {
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-border/60 bg-foreground/5 px-1.5 py-0.5 text-[9px] font-mono text-muted-foreground dark:border-white/10 dark:bg-white/5">
      <span className={`inline-block h-1 w-1 rounded-full ${live ? "bg-emerald-500 dark:bg-emerald-400" : "bg-muted-foreground/30 dark:bg-white/20"}`} />
      {live ? labelLive : labelEst}
    </span>
  );
};

// Lifecycle Badge Component with plain-language labels
const LifecycleBadge = ({ stage }: { stage: string }) => {
  const stageConfig = {
    "Emerging": { color: "bg-emerald-500/20 text-emerald-400 border-emerald-500/50", icon: Sparkles, label: <><ThemeEmoji name="emerging" className="mr-1" /> Just Starting</>, tip: "This topic is new — great time to get in early before everyone else." },
    "Breakout": { color: "bg-orange-500/20 text-orange-400 border-orange-500/50", icon: Flame, label: <><ThemeEmoji name="breakout" className="mr-1" /> Taking Off</>, tip: "This topic is growing fast right now. Post about it soon!" },
    "Mainstream": { color: "bg-teal-500/20 text-teal-400 border-teal-500/50", icon: TrendingUp, label: <><ThemeEmoji name="mainstream" className="mr-1" /> Popular Now</>, tip: "Lots of people are interested. Good reach but more competition." },
    "Saturated": { color: "bg-amber-500/20 text-amber-400 border-amber-500/50", icon: AlertCircle, label: <><ThemeEmoji name="warning" className="mr-1" /> Very Crowded</>, tip: "Many brands are already posting about this. Hard to stand out." },
    "Declining": { color: "bg-red-500/20 text-red-400 border-red-500/50", icon: TrendingDown, label: <><ThemeEmoji name="declining" className="mr-1" /> Fading Out</>, tip: "Interest in this topic is dropping. Better to skip it." }
  };

  const config = stageConfig[stage as keyof typeof stageConfig] || stageConfig["Emerging"];
  const Icon = config.icon;

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge className={`${config.color} border font-mono text-xs flex items-center gap-1.5 px-2 py-1`}>
            <Icon className="w-3 h-3" />
            {config.label}
          </Badge>
        </TooltipTrigger>
        <TooltipContent className="max-w-[200px] bg-zinc-900 border-white/10 text-white">
          <p className="text-xs">{config.tip}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

// Opportunity Score Gauge Component
const ProfitScoreGauge = ({ score }: { score: number }) => {
  const getScoreColor = (val: number) => {
    if (val >= 80) return { bg: "bg-emerald-500", text: "text-emerald-400", label: "Act Now", emoji: "🚀" };
    if (val >= 60) return { bg: "bg-teal-500", text: "text-teal-400", label: "Worth It", emoji: "💎" };
    if (val >= 40) return { bg: "bg-amber-500", text: "text-amber-400", label: "Potential", emoji: "🤔" };
    return { bg: "bg-red-500", text: "text-red-400", label: "Skip", emoji: "⏭" };
  };

  const colorConfig = getScoreColor(score);
  const scoreInt = Math.round(score);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-mono font-black text-muted-foreground/70 uppercase tracking-[0.2em] dark:text-white/20">Opportunity Gap</span>
        <div className={`flex items-center gap-1.5 ${colorConfig.text} font-bold text-xs`}>
          <span>{colorConfig.emoji}</span>
          <span className="font-mono uppercase tracking-widest">{colorConfig.label}</span>
          <span className="opacity-40 ml-1">{scoreInt}/100</span>
        </div>
      </div>
      <div className="h-1 w-full bg-foreground/10 dark:bg-white/5 rounded-full overflow-hidden">
        <motion.div 
          initial={{ width: 0 }}
          animate={{ width: `${scoreInt}%` }}
          className={`h-full ${colorConfig.bg} shadow-[0_0_8px_rgba(0,224,208,0.2)] rounded-full transition-all duration-1000`} 
        />
      </div>
    </div>
  );
};

// Sparkline Chart Component for Growth Predictions
const GrowthSparkline = ({ forecast, predicted_growth }: { forecast?: number[], predicted_growth?: number }) => {
  if (!forecast || forecast.length === 0) return null;

  const max = Math.max(...forecast);
  const min = Math.min(...forecast);
  const range = (max - min) || 1;

  const points = forecast.map((value, index) => {
    const x = (index / (forecast.length - 1)) * 100;
    const y = 100 - ((value - min) / range) * 80 - 10; // Padding top/bottom
    return `${x},${y}`;
  }).join(' ');

  const isPositive = predicted_growth && predicted_growth > 0;

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground font-mono uppercase tracking-widest text-[9px]">Growth Outlook</span>
              {predicted_growth !== undefined && (
                <span className={`font-bold ${isPositive ? 'text-emerald-400' : 'text-red-400'} flex items-center gap-1 text-[10px]`}>
                  {isPositive ? <TrendingUp className="w-2.5 h-2.5" /> : <TrendingDown className="w-2.5 h-2.5" />}
                  {predicted_growth > 0 ? '+' : ''}{predicted_growth.toFixed(1)}%
                </span>
              )}
            </div>
            <div className="relative h-10 bg-white/[0.02] border border-white/5 rounded-lg overflow-hidden p-1">
              <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="w-full h-full">
                <polyline
                  points={points}
                  fill="none"
                  stroke={isPositive ? "#10b981" : "#ef4444"}
                  strokeWidth="4"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="drop-shadow-[0_0_5px_rgba(16,185,129,0.5)]"
                />
                <path
                  d={`M 0 100 L ${points} L 100 100 Z`}
                  fill={isPositive ? "url(#gradient-positive)" : "url(#gradient-negative)"}
                  fillOpacity="0.2"
                />
                <defs>
                  <linearGradient id="gradient-positive" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#10b981" stopOpacity="0.3" />
                    <stop offset="100%" stopColor="#10b981" stopOpacity="0" />
                  </linearGradient>
                  <linearGradient id="gradient-negative" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#ef4444" stopOpacity="0.3" />
                    <stop offset="100%" stopColor="#ef4444" stopOpacity="0" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
          </div>
        </TooltipTrigger>
        <TooltipContent className="max-w-[200px] bg-zinc-900 border-white/10 text-white">
          <p className="text-xs">Machine learning projection for interest over the next 7 days.</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

// Main Trend Card Component
export const TrendCard = ({ trend, onClick, onMagicBridge, onToggleWatchlist, onToggleCompare, isWatchlisted, isActive, isCompared }: TrendCardProps) => {
  const navigate = useNavigate();

  const displayTitle = useMemo(() => {
    // Always show the discovered trend keyword as the primary title.
    // Use rising queries only as supplemental context (subtitle).
    return trend.keyword;
  }, [trend]);

  const displaySubtitle = useMemo(() => {
    const rq = Array.isArray(trend.rising_queries) ? trend.rising_queries : [];
    const first = (rq[0] || "").toString().trim();
    if (!first) return null;
    if (first.toLowerCase() === (trend.keyword || "").toLowerCase()) return null;
    return first;
  }, [trend.keyword, trend.rising_queries]);

  const hasScore = (val?: number) => isFiniteNumber(val) && val > 0;

  const isSpike = trend.is_spike === true;
  const isSimulated = trend.is_simulated === true;
  const isRateLimited = (trend.error_message || "").toLowerCase().includes("rate_limited");
  const isFailed = (trend.fetch_status || "").toLowerCase() === "failed";
  // Keep card compact: related/rising queries are shown in the modal/strategy sections instead.

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className={`relative group rounded-3xl p-6 flex flex-col gap-6 transition-all overflow-hidden ${
        isSpike ? "shadow-[0_30px_90px_rgba(0,224,208,0.08)]" : "shadow-[0_30px_90px_rgba(0,0,0,0.55)]"
      } ${isActive ? "ring-2 ring-primary/40" : "ring-1 ring-border/60 hover:ring-border"} dark:${isActive ? "" : "ring-white/5 hover:ring-white/10"}`}
      role="button"
      tabIndex={0}
      onClick={() => onClick?.()}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") onClick?.();
      }}
    >
      {/* Premium glass background */}
      <div
        className={`absolute inset-0 rounded-3xl border backdrop-blur-3xl ${
          isSpike
            ? "border-primary/25 bg-gradient-to-br from-primary/10 via-card/60 to-transparent dark:via-white/[0.03]"
            : "border-border/60 bg-card/70 dark:border-white/10 dark:bg-white/[0.03]"
        }`}
      />
      <div className={`absolute -top-24 -right-24 h-56 w-56 rounded-full blur-[70px] ${isSpike ? "bg-primary/25" : "bg-foreground/10 dark:bg-white/10"}`} />
      <div className="absolute -bottom-28 -left-28 h-64 w-64 rounded-full blur-[90px] bg-teal-500/10" />
      <div className="absolute inset-0 rounded-3xl ring-1 ring-border/40 dark:ring-white/5 pointer-events-none" />

      <div className="relative z-10 flex flex-col gap-6">
      {/* Header Section */}
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            {isSpike ? (
              <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-primary/20 border border-primary/20 text-[9px] font-black font-mono text-primary tracking-tighter uppercase">
                <Flame className="w-2.5 h-2.5 fill-primary" />
                Live Spike
              </div>
            ) : (
              <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-foreground/5 border border-border/60 text-[9px] font-black font-mono text-muted-foreground tracking-tighter uppercase dark:bg-white/5 dark:border-white/5 dark:text-white/30">
                <Activity className="w-2.5 h-2.5" />
                Pulse Signal
              </div>
            )}
            <DataQualityPill live={trend.is_real_social === true} />
          </div>
          <h3 className="text-2xl font-bold font-heading text-foreground tracking-tight capitalize leading-tight dark:text-white">
            {displayTitle}
          </h3>
          {displaySubtitle && (
            <p className="text-[11px] font-mono text-muted-foreground italic line-clamp-1 dark:text-white/40">
              Related: {displaySubtitle}
            </p>
          )}
          <div className="flex items-center gap-2 flex-wrap pt-0.5">
             <span className="text-[10px] font-mono font-black text-primary/40 uppercase tracking-widest">{trend.niche}</span>
             <span className="w-1 h-1 rounded-full bg-foreground/10 dark:bg-white/10" />
             <span className="text-[10px] font-mono font-black text-muted-foreground uppercase tracking-widest flex items-center gap-1 dark:text-white/20">
                <MapPin className="w-2.5 h-2.5" /> {trend.location}
             </span>
          </div>
        </div>

        <div className="flex flex-col items-end gap-3">
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              className={`h-10 w-10 rounded-2xl transition-all ${isCompared ? "bg-primary/10 text-primary" : "text-muted-foreground/60 hover:text-foreground hover:bg-foreground/5 dark:text-white/10 dark:hover:text-white/40 dark:hover:bg-white/5"}`}
              onClick={(e) => {
                e.stopPropagation();
                onToggleCompare?.(trend);
              }}
              title={isCompared ? "Remove from compare" : "Add to compare"}
            >
              <Zap className="w-5 h-5" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className={`h-10 w-10 rounded-2xl transition-all ${isWatchlisted ? 'bg-amber-500/10 text-amber-500 dark:text-amber-400' : 'text-muted-foreground/60 hover:text-foreground hover:bg-foreground/5 dark:text-white/10 dark:hover:text-white/40 dark:hover:bg-white/5'}`}
              onClick={(e) => {
                e.stopPropagation();
                if (onToggleWatchlist) onToggleWatchlist(trend.keyword);
              }}
              title={isWatchlisted ? "Remove from watchlist" : "Add to watchlist"}
            >
              <Star className={`w-5 h-5 ${isWatchlisted ? 'fill-amber-400' : ''}`} />
            </Button>
          </div>
            {trend.lifecycle_stage && <LifecycleBadge stage={trend.lifecycle_stage} />}
        </div>
      </div>

      {/* Secondary metrics (collapsed by default) */}
      {(hasScore(trend.z_score_spike) || hasScore(trend.breakout_probability)) && (
        <div className={`grid grid-cols-2 gap-4 transition-all ${isActive ? "" : "hidden md:grid md:opacity-0 md:group-hover:opacity-100 md:group-hover:block"}`}>
          {hasScore(trend.z_score_spike) && (
            <div className="p-3.5 bg-background/50 border border-border/60 rounded-2xl space-y-1 dark:bg-white/[0.03] dark:border-white/5">
              <span className="text-[8px] font-mono font-black text-muted-foreground/70 uppercase tracking-[0.2em] flex items-center gap-1.5 dark:text-white/20">
                <Zap className="w-2.5 h-2.5 text-orange-400" /> Velocity
              </span>
              <div className="flex items-baseline gap-1">
                <span className="text-xl font-bold text-foreground dark:text-white">{fmtFixed(trend.z_score_spike, 1)}</span>
                <span className="text-[9px] font-mono text-muted-foreground/60 dark:text-white/10">σ-VEL</span>
              </div>
            </div>
          )}
          {hasScore(trend.breakout_probability) && (
            <div className="p-3.5 bg-background/50 border border-border/60 rounded-2xl space-y-1 dark:bg-white/[0.03] dark:border-white/5">
              <span className="text-[8px] font-mono font-black text-muted-foreground/70 uppercase tracking-[0.2em] flex items-center gap-1.5 dark:text-white/20">
                <Target className="w-2.5 h-2.5 text-emerald-400" /> Confidence
              </span>
              <div className="flex items-baseline gap-1">
                <span className="text-xl font-bold text-emerald-400">{trend.breakout_probability}%</span>
                <span className="text-[9px] font-mono text-emerald-400/30">ACC</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Analytics Visualizers */}
      <div className="space-y-5">
        {hasScore(trend.profit_score) && <ProfitScoreGauge score={trend.profit_score!} />}
        {trend.forecast_series && trend.forecast_series.length > 0 && (
          <GrowthSparkline forecast={trend.forecast_series} predicted_growth={trend.predicted_growth_pct} />
        )}
      </div>

      {/* Footer (single primary action) */}
      <div className="pt-2 border-t border-border/60 dark:border-white/5" />

      {/* Interaction Rail */}
      <div className="flex items-center justify-end">
        <Button
          onClick={(e) => {
            e.stopPropagation();
            if (onMagicBridge) onMagicBridge(trend.keyword);
          }}
          className="px-5 h-12 bg-primary hover:bg-primary/90 text-black rounded-2xl font-black font-heading text-[10px] uppercase tracking-[0.2em] shadow-[0_14px_50px_rgba(0,224,208,0.32)] hover:shadow-[0_18px_70px_rgba(0,224,208,0.45)] transition-all transform hover:-translate-y-1 active:translate-y-0 group"
        >
          <Rocket className="w-4 h-4 mr-2 group-hover:scale-110 group-hover:-rotate-12 transition-transform" />
          Create
        </Button>
      </div>

      {/* Status Messages */}
      {(isRateLimited || (isFailed && trend.error_message)) && (
        <div className="pt-2">
          {isRateLimited ? (
            <div className="text-[9px] font-mono font-bold text-primary/40 flex items-center gap-2 uppercase tracking-widest animate-pulse">
              <ArrowRight className="w-2.5 h-2.5" />
              Signal reconnecting...
            </div>
          ) : (
            <div className="text-[9px] font-mono font-black text-red-500/50 flex items-center gap-2 uppercase tracking-widest">
              <AlertCircle className="w-2.5 h-2.5" />
              Divergence: {trend.error_message?.toString().slice(0, 30)}
            </div>
          )}
        </div>
      )}
      </div>
    </motion.div>
  );
};
