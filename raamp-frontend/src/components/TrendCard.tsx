import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ThemeEmoji } from "@/components/ui/emoji";
import { TrendSpike, trendService, TrendExplainResponse } from "@/services/trendService";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  TrendingUp, Flame, Zap, Target, Activity, Sparkles,
  TrendingDown, AlertCircle, CheckCircle, Clock, MapPin, ChevronDown, ChevronUp, Loader2, ArrowRight
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface TrendCardProps {
  trend: TrendSpike;
  onClick?: () => void;
  onGenerateContent?: (keyword: string) => void;
}

// Lifecycle Badge Component with plain-language labels
const LifecycleBadge = ({ stage }: { stage: string }) => {
  const stageConfig = {
    "Emerging": { color: "bg-emerald-500/20 text-emerald-400 border-emerald-500/50", icon: Sparkles, label: <><ThemeEmoji name="emerging" className="mr-1" /> Just Starting</>, tip: "This topic is new — great time to get in early before everyone else." },
    "Breakout": { color: "bg-orange-500/20 text-orange-400 border-orange-500/50", icon: Flame, label: <><ThemeEmoji name="breakout" className="mr-1" /> Taking Off</>, tip: "This topic is growing fast right now. Post about it soon!" },
    "Mainstream": { color: "bg-blue-500/20 text-blue-400 border-blue-500/50", icon: TrendingUp, label: <><ThemeEmoji name="mainstream" className="mr-1" /> Popular Now</>, tip: "Lots of people are interested. Good reach but more competition." },
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
        <TooltipContent className="max-w-[200px]">
          <p className="text-xs">{config.tip}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

// Opportunity Score Gauge Component
const ProfitScoreGauge = ({ score }: { score: number }) => {
  const getScoreColor = (val: number) => {
    if (val >= 80) return { bg: "bg-emerald-500", text: "text-emerald-400", label: "🔥 Act Now" };
    if (val >= 60) return { bg: "bg-blue-500", text: "text-blue-400", label: "👍 Worth It" };
    if (val >= 40) return { bg: "bg-amber-500", text: "text-amber-400", label: "🤔 Maybe" };
    return { bg: "bg-red-500", text: "text-red-400", label: "⏭ Skip" };
  };

  const colorConfig = getScoreColor(score);

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground font-mono">Opportunity Score</span>
              <span className={`font-bold ${colorConfig.text}`}>{score}/100</span>
            </div>
            <Progress value={score} className="h-2 bg-deep-teal-700">
              <div className={`h-full ${colorConfig.bg} rounded-full transition-all duration-500`} style={{ width: `${score}%` }} />
            </Progress>
            <p className={`text-[10px] ${colorConfig.text} font-medium text-right`}>{colorConfig.label}</p>
          </div>
        </TooltipTrigger>
        <TooltipContent className="max-w-[200px]">
          <p className="text-xs">How much potential this trend has for your business right now.</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

// Sparkline Chart Component for Growth Predictions
const GrowthSparkline = ({ forecast, predicted_growth }: { forecast?: number[], predicted_growth?: number }) => {
  if (!forecast || forecast.length === 0) return null;

  const max = Math.max(...forecast);
  const min = Math.min(...forecast);
  const range = max - min;

  const points = forecast.map((value, index) => {
    const x = (index / (forecast.length - 1)) * 100;
    const y = 100 - ((value - min) / range) * 100;
    return `${x},${y}`;
  }).join(' ');

  const isPositive = predicted_growth && predicted_growth > 0;

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground font-mono">Next 7 Days</span>
              {predicted_growth !== undefined && (
                <span className={`font-bold ${isPositive ? 'text-emerald-400' : 'text-red-400'} flex items-center gap-1`}>
                  {isPositive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                  {predicted_growth > 0 ? '+' : ''}{predicted_growth.toFixed(1)}%
                </span>
              )}
            </div>
            <div className="relative h-10 bg-deep-teal-700 rounded-md overflow-hidden">
              <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="w-full h-full">
                <polyline
                  points={points}
                  fill="none"
                  stroke={isPositive ? "#10b981" : "#ef4444"}
                  strokeWidth="3"
                  className="drop-shadow-lg"
                />
                <polyline
                  points={points}
                  fill={isPositive ? "rgba(16, 185, 129, 0.1)" : "rgba(239, 68, 68, 0.1)"}
                  stroke="none"
                />
              </svg>
            </div>
          </div>
        </TooltipTrigger>
        <TooltipContent className="max-w-[200px]">
          <p className="text-xs">Predicted interest level over the next 7 days.</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

// Main Trend Card Component
export const TrendCard = ({ trend, onClick, onGenerateContent }: TrendCardProps) => {
  const navigate = useNavigate();
  const [isExpanded, setIsExpanded] = useState(false);
  const [isLoadingExplanation, setIsLoadingExplanation] = useState(false);
  const [explanation, setExplanation] = useState<TrendExplainResponse | null>(null);

  const handleViewDetails = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onClick) onClick();

    if (isExpanded) {
      setIsExpanded(false);
      return;
    }

    setIsExpanded(true);

    if (!explanation) {
      setIsLoadingExplanation(true);
      try {
        const result = await trendService.getTrendExplanation({
          keyword: trend.keyword,
          niche: trend.niche,
          location: trend.location || "PK",
          lifecycle_stage: trend.lifecycle_stage,
          breakout_probability: trend.breakout_probability,
          profit_score: trend.profit_score,
          competition: trend.saturation_score,
          buzz: trend.social_score,
        });
        setExplanation(result);
      } catch {
        setExplanation({
          keyword: trend.keyword,
          explanation: "Could not load AI explanation at this time.",
          why_now: "",
          content_prompt: "",
        });
      } finally {
        setIsLoadingExplanation(false);
      }
    }
  };

  const handleUsePrompt = () => {
    if (!explanation?.content_prompt) return;
    navigate("/dashboard/creative", {
      state: { prefillPrompt: explanation.content_prompt },
    });
  };

  // Determine if this is trending or a steady topic
  const isSpike = trend.is_spike === true;
  const cardBorderClass = isSpike
    ? "border-primary/50 hover:border-primary"
    : "border-blue-500/30 hover:border-blue-500/50";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      whileHover={{ scale: 1.02, boxShadow: isSpike ? "0 0 25px rgba(0, 224, 208, 0.15)" : "0 0 15px rgba(59, 130, 246, 0.1)" }}
      className={`bg-deep-teal-800 border rounded-lg p-5 space-y-4 transition-all ${cardBorderClass}`}
    >
      {/* Spike/Baseline Badge */}
      <div className="flex items-center justify-between">
        {isSpike ? (
          <Badge className="bg-primary/20 text-primary border-primary/30 font-mono text-xs flex items-center gap-1.5 px-2 py-1">
            <Flame className="w-3 h-3" />
            TRENDING NOW
          </Badge>
        ) : (
          <Badge className="bg-blue-500/10 text-blue-400 border-blue-500/30 font-mono text-xs flex items-center gap-1.5 px-2 py-1">
            <Activity className="w-3 h-3" />
            {trend.label || 'RISING'}
          </Badge>
        )}
      </div>

      {/* Header Section */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 space-y-2">
          <h3 className="text-lg font-semibold text-white font-bebas tracking-wide">{trend.keyword}</h3>
          <div className="flex items-center gap-2 flex-wrap">
            <Badge variant="outline" className="text-xs text-muted-foreground border-deep-teal-700">
              {trend.niche}
            </Badge>
            {trend.location && (
              <Badge variant="outline" className="text-xs text-muted-foreground border-deep-teal-700 flex items-center gap-1">
                <MapPin className="w-3 h-3" />
                {trend.location}
              </Badge>
            )}
            {trend.timeframe && (
              <Badge variant="outline" className="text-xs text-muted-foreground border-deep-teal-700 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {trend.timeframe}
              </Badge>
            )}
          </div>
        </div>

        {/* Lifecycle Badge */}
        {trend.lifecycle_stage && <LifecycleBadge stage={trend.lifecycle_stage} />}
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-4">
        {/* Trend Speed (was Z-Score Spike) */}
        {trend.z_score_spike !== undefined && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground font-mono">Trend Speed</p>
                  <div className="flex items-center gap-2">
                    <Zap className={`w-4 h-4 ${trend.z_score_spike > 7 ? 'text-orange-400' : 'text-yellow-400'}`} />
                    <span className="text-xl font-bold text-white">{trend.z_score_spike.toFixed(1)}x</span>
                  </div>
                </div>
              </TooltipTrigger>
              <TooltipContent className="max-w-[200px]">
                <p className="text-xs">How much faster this topic is growing compared to normal. Higher = moving faster.</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}

        {/* Viral Potential (was Breakout Probability) */}
        {trend.breakout_probability !== undefined && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground font-mono">Viral Potential</p>
                  <div className="flex items-center gap-2">
                    <Target className="w-4 h-4 text-emerald-400" />
                    <span className="text-xl font-bold text-emerald-400">{trend.breakout_probability}%</span>
                  </div>
                </div>
              </TooltipTrigger>
              <TooltipContent className="max-w-[200px]">
                <p className="text-xs">Chance this topic goes viral in the next few days. Above 70% is a strong signal to post now.</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </div>

      {/* Opportunity Score Progress */}
      {trend.profit_score !== undefined && <ProfitScoreGauge score={trend.profit_score} />}

      {/* Growth Prediction Sparkline */}
      {trend.forecast_series && trend.forecast_series.length > 0 && (
        <GrowthSparkline forecast={trend.forecast_series} predicted_growth={trend.predicted_growth_pct} />
      )}

      {/* Secondary Scores Row */}
      <div className="grid grid-cols-3 gap-2 pt-3 border-t border-deep-teal-700">
        {/* Gap Score (was Arbitrage) */}
        {trend.arbitrage_score !== undefined && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="text-center space-y-1">
                  <p className="text-[10px] text-muted-foreground font-mono uppercase">Gap Score</p>
                  <p className="text-sm font-bold text-blue-400">{trend.arbitrage_score.toFixed(0)}</p>
                </div>
              </TooltipTrigger>
              <TooltipContent className="max-w-[200px]">
                <p className="text-xs">How much demand exists vs. how little content is out there. Higher = less competition for a hot topic.</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}

        {/* Competition (was Saturation) */}
        {trend.saturation_score !== undefined && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="text-center space-y-1">
                  <p className="text-[10px] text-muted-foreground font-mono uppercase">Competition</p>
                  <p className="text-sm font-bold text-amber-400">{trend.saturation_score.toFixed(0)}%</p>
                </div>
              </TooltipTrigger>
              <TooltipContent className="max-w-[200px]">
                <p className="text-xs">How many other brands are already posting about this. Lower % = easier to stand out.</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}

        {/* Buzz (was Social Score) */}
        {trend.social_score !== undefined && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="text-center space-y-1">
                  <p className="text-[10px] text-muted-foreground font-mono uppercase">Buzz</p>
                  <p className="text-sm font-bold text-purple-400">{trend.social_score.toFixed(0)}</p>
                </div>
              </TooltipTrigger>
              <TooltipContent className="max-w-[200px]">
                <p className="text-xs">How much people are talking about this on social media right now.</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </div>

      {/* Rising Queries */}
      {trend.rising_queries && trend.rising_queries.length > 0 && (
        <div className="pt-3 border-t border-deep-teal-700 space-y-2">
          <p className="text-xs text-muted-foreground font-mono">People are searching for</p>
          <div className="flex flex-wrap gap-1.5">
            {trend.rising_queries.slice(0, 3).map((query, idx) => (
              <Badge key={idx} variant="secondary" className="text-[10px] bg-deep-teal-700/50 text-neon-teal border-neon-teal/20">
                #{query}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="pt-3 border-t border-deep-teal-700 grid grid-cols-2 gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={handleViewDetails}
          className="border-deep-teal-700 hover:bg-deep-teal-700 text-white/80 hover:text-white font-mono text-xs"
        >
          {isExpanded ? <ChevronUp className="w-3 h-3 mr-1" /> : <ChevronDown className="w-3 h-3 mr-1" />}
          {isExpanded ? "Hide Details" : "View Details"}
        </Button>
        <Button
          variant="default"
          size="sm"
          onClick={(e) => {
            e.stopPropagation();
            if (onGenerateContent) onGenerateContent(trend.keyword);
          }}
          className="bg-neon-teal/20 hover:bg-neon-teal text-neon-teal hover:text-black border border-neon-teal/50 font-mono text-xs"
        >
          <Sparkles className="w-3 h-3 mr-1" />
          AI Content
        </Button>
      </div>

      {/* Inline AI Explanation Panel */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            key="explanation-panel"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="pt-3 border-t border-deep-teal-700 space-y-3">
              {isLoadingExplanation ? (
                <div className="flex items-center gap-2 py-4 justify-center text-white/50 font-mono text-xs">
                  <Loader2 className="w-4 h-4 animate-spin text-neon-teal" />
                  AI is analysing this trend for you...
                </div>
              ) : explanation ? (
                <>
                  <p className="text-sm text-white/80 leading-relaxed">{explanation.explanation}</p>
                  {explanation.why_now && (
                    <p className="text-xs text-neon-teal font-mono border-l-2 border-neon-teal/50 pl-3">
                      {explanation.why_now}
                    </p>
                  )}
                  {explanation.content_prompt && (
                    <div className="space-y-2">
                      <p className="text-[10px] text-muted-foreground font-mono uppercase">Campaign Idea</p>
                      <div className="p-3 bg-purple-500/10 rounded-lg border border-purple-500/30 text-xs font-mono text-purple-100">
                        {explanation.content_prompt}
                      </div>
                      <Button
                        size="sm"
                        onClick={handleUsePrompt}
                        className="w-full bg-primary/20 hover:bg-primary text-primary hover:text-black border border-primary/50 font-mono text-xs"
                      >
                        Use This Prompt
                        <ArrowRight className="w-3 h-3 ml-1" />
                      </Button>
                    </div>
                  )}
                </>
              ) : null}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};
