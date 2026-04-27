import { useRef } from "react";
import { TrendCard } from "@/components/TrendCard";
import { RefreshCw, Zap, Rocket } from "lucide-react";
import { Button } from "@/components/ui/button";

interface SignalsCarouselProps {
  liveTrends: any[];
  isLoading: boolean;
  showAllTrends: boolean;
  lifecycleFilter: string;
  watchlist: any[];
  compare?: any[];
  location: string;
  activeKeyword?: string | null;
  onToggleWatchlist: (keyword: string) => void;
  onSelectTrend: (trend: any) => void;
  onMagicBridge: (keyword: string) => void;
  onToggleCompare?: (trend: any) => void;
  onTriggerScan: () => void;
}

export function SignalsCarousel({
  liveTrends,
  isLoading,
  showAllTrends,
  lifecycleFilter,
  watchlist,
  compare,
  location,
  activeKeyword,
  onToggleWatchlist,
  onSelectTrend,
  onMagicBridge,
  onToggleCompare,
  onTriggerScan,
}: SignalsCarouselProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  if (isLoading) {
    return (
      <div className="w-full py-20 flex flex-col items-center justify-center gap-6 text-center border border-dashed border-border/30 rounded-2xl">
        <div className="relative">
          <RefreshCw className="w-16 h-16 animate-spin text-primary/20" />
          <div className="absolute inset-0 flex items-center justify-center">
             <Rocket className="w-6 h-6 text-primary animate-pulse" />
          </div>
        </div>
        <div className="space-y-2">
          <p className="font-mono text-xs uppercase tracking-[0.3em] font-black text-primary/80">Connecting to signal network</p>
          <p className="font-mono text-[10px] text-muted-foreground/40 uppercase">Synchronizing nodes...</p>
        </div>
      </div>
    );
  }

  if (liveTrends.length === 0) {
    return (
      <div className="w-full py-24 flex flex-col items-center justify-center gap-6 text-center border border-dashed border-primary/20 rounded-3xl bg-primary/5">
         <Zap className="w-16 h-16 text-primary/30 animate-pulse" />
         <div className="space-y-3">
           <p className="font-mono text-sm uppercase tracking-[0.2em] font-black text-foreground">No trends detected</p>
           <p className="font-mono text-[10px] uppercase tracking-widest leading-relaxed text-muted-foreground max-w-sm mx-auto">
             We haven't found any major trends for your niche in <span className="text-primary">{location}</span> yet.
           </p>
           <Button 
             onClick={onTriggerScan} 
             className="mt-4 bg-primary text-black font-black tracking-widest text-[10px] h-10 px-8 rounded-xl hover:scale-105 transition-transform"
           >
             INITIALIZE SIGNAL SCAN
           </Button>
         </div>
      </div>
    );
  }

  const items = showAllTrends ? liveTrends : liveTrends.slice(0, 8);
  const filteredItems = items.filter(t => lifecycleFilter === "all" || t.lifecycle_stage === lifecycleFilter);

  return (
    <div 
      ref={scrollRef}
      className="flex flex-row overflow-x-auto gap-4 pb-4 snap-x snap-mandatory"
      style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
    >
      <style
        dangerouslySetInnerHTML={{
          __html: `
            .flex::-webkit-scrollbar { display: none; }
          `,
        }}
      />
      
      {filteredItems.map((trend) => (
        <div key={trend.id} className="min-w-[320px] max-w-[320px] snap-center flex-shrink-0 h-full">
          <TrendCard
            trend={trend}
            isActive={Boolean(activeKeyword) && String(activeKeyword).toLowerCase() === String(trend.keyword || "").toLowerCase()}
            isWatchlisted={watchlist.some(w => w.keyword.toLowerCase() === trend.keyword.toLowerCase())}
            isCompared={Array.isArray(compare) && compare.some((c) => (c?.keyword || "").toLowerCase() === (trend.keyword || "").toLowerCase())}
            onToggleWatchlist={onToggleWatchlist}
            onToggleCompare={onToggleCompare}
            onClick={() => onSelectTrend(trend)}
            onMagicBridge={onMagicBridge}
          />
        </div>
      ))}
    </div>
  );
}
