import React from "react";
import { Clock, AlertTriangle, Zap, Flame, Info, TrendingUp } from "lucide-react";
import { motion } from "framer-motion";

interface UrgencyWidgetProps {
  urgency: number; // 0-100
  windowStatus: string; // e.g., "Rising High"
  className?: string;
}

export function UrgencyWidget({ urgency, windowStatus, className = "" }: UrgencyWidgetProps) {
  // Determine color and icon based on urgency
  let colorClass = "from-teal-500 to-emerald-500";
  let textColor = "text-teal-400";
  let label = "Stable Opportunity";
  let icon = <Zap className="w-4 h-4" />;

  if (urgency >= 80) {
    colorClass = "from-red-500 to-orange-500";
    textColor = "text-red-400";
    label = "CRITICAL: ACT NOW";
    icon = <Flame className="w-4 h-4" />;
  } else if (urgency >= 60) {
    colorClass = "from-orange-500 to-amber-500";
    textColor = "text-amber-400";
    label = "Window Closing";
    icon = <Clock className="w-4 h-4" />;
  } else if (urgency >= 30) {
    colorClass = "from-teal-500 to-emerald-500";
    textColor = "text-emerald-400";
    label = "Growth Phase";
    icon = <TrendingUp className="w-4 h-4" />;
  }

  return (
    <div className={`rounded-2xl bg-white/[0.03] border border-white/10 p-4 ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className={`p-1.5 rounded-lg bg-white/5 ${textColor}`}>
            {icon}
          </div>
          <div>
            <span className="text-[10px] uppercase tracking-widest text-muted-foreground block leading-none mb-1">Market Window</span>
            <span className={`text-sm font-bold leading-none ${textColor}`}>{windowStatus || label}</span>
          </div>
        </div>
        <div className="text-right">
          <span className="text-[10px] uppercase tracking-widest text-muted-foreground block mb-1">Opportunity Score</span>
          <span className="text-lg font-black font-mono leading-none">{urgency}%</span>
        </div>
      </div>

      {/* The Visual Bar */}
      <div className="relative h-3 w-full bg-white/5 rounded-full overflow-hidden mb-2">
        <motion.div 
          initial={{ width: 0 }}
          animate={{ width: `${urgency}%` }}
          transition={{ duration: 1, ease: "easeOut" }}
          className={`absolute inset-y-0 left-0 bg-gradient-to-r ${colorClass} rounded-full`}
        />
        {/* Market Saturation Threshold marker */}
        <div className="absolute top-0 bottom-0 left-[75%] w-0.5 bg-white/20 border-l border-dashed border-white/40" />
      </div>

      <div className="flex justify-between text-[9px] font-medium text-muted-foreground/60 uppercase tracking-tight">
        <span>Early Access</span>
        <span>Mainstream Peak</span>
        <span>Saturated</span>
      </div>

      <div className="mt-4 flex items-start gap-2 p-2 bg-white/5 rounded-lg border border-white/5">
        <Info className="w-3 h-3 text-muted-foreground mt-0.5 shrink-0" />
        <p className="text-[10px] text-muted-foreground leading-relaxed">
          {urgency > 80 
            ? "Massive competition arriving soon. Post within 24 hours to maximize reach." 
            : urgency > 50 
              ? "High engagement zone. Ideal time to launch campaigns for maximum conversion."
              : "Safe to experiment. Use this trend to build authority before it goes mainstream."
          }
        </p>
      </div>
    </div>
  );
}
