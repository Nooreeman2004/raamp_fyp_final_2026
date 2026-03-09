import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import Layout from "@/components/Layout";
import { Badge } from "@/components/ui/badge";
import { TrendCard } from "@/components/TrendCard";
import {
  Tooltip as TooltipUI,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Zap, TrendingUp, Flame, Target, MapPin,
  Globe, ArrowRight, RefreshCw, AlertCircle,
  Activity, Wind, Sparkles, ChevronRight, Check, Search, Database,
  Info, Lightbulb
} from "lucide-react";

// Animation Imports
import { motion, AnimatePresence } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { toast } from "sonner";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useAuth } from "@/hooks/useAuth";

// Chart Imports
import {
  XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, BarChart, Bar, ScatterChart,
  Scatter, ZAxis, Cell, Area, ComposedChart,
  PieChart, Pie, Line, ReferenceArea, ReferenceLine, LabelList, Label
} from 'recharts';

import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";

import { trendService, TrendSpike, GeoTrend, SpikeTimeline, MarketGap, PlatformReach, CampaignRecommendation, WatchlistItem, ContentSuggestion } from "@/services/trendService";
import { ContentSuggestionsModal } from "@/components/ContentSuggestionsModal";

const TrendArbitrage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [liveTrends, setLiveTrends] = useState<TrendSpike[]>([]);
  const [geoData, setGeoData] = useState<GeoTrend[]>([]);
  const [timelineData, setTimelineData] = useState<SpikeTimeline[]>([]);
  const [marketGapData, setMarketGapData] = useState<MarketGap[]>([]);
  const [platformReach, setPlatformReach] = useState<PlatformReach | null>(null);
  const [recommendations, setRecommendations] = useState<CampaignRecommendation[]>([]);
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [recContext, setRecContext] = useState<string>("");
  const [isLoading, setIsLoading] = useState(true);
  const [isGeneratingRecs, setIsGeneratingRecs] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [scanStep, setScanStep] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [lastSync, setLastSync] = useState<Date>(new Date());
  const [isOffline, setIsOffline] = useState(false);
  const [expandedReasonings, setExpandedReasonings] = useState<Set<number>>(new Set());
  const [deploySheetOpen, setDeploySheetOpen] = useState(false);
  const [deployPrompt, setDeployPrompt] = useState("");
  const [deployContentType, setDeployContentType] = useState<"carousel" | "reel" | "story">("carousel");

  // Filter States
  const [location, setLocation] = useState<string>("PK");
  const [searchQuery, setSearchQuery] = useState<string>("PK");
  const [category, setCategory] = useState<string>("all");
  const [timeframe, setTimeframe] = useState<string>("30");
  const [lifecycleFilter, setLifecycleFilter] = useState<string>("all");
  const [showAllTrends, setShowAllTrends] = useState(false);
  const [selectedCity, setSelectedCity] = useState<GeoTrend | null>(null);
  const [campaignModalOpen, setCampaignModalOpen] = useState(false);
  const [selectedTrend, setSelectedTrend] = useState<TrendSpike | null>(null);
  const [gapAnalysisOpen, setGapAnalysisOpen] = useState(false);

  // Content Suggestions States
  const [contentSuggestions, setContentSuggestions] = useState<ContentSuggestion | null>(null);
  const [contentModalOpen, setContentModalOpen] = useState(false);
  const [isGeneratingContent, setIsGeneratingContent] = useState(false);

  // Debounce location search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchQuery !== location) {
        setLocation(searchQuery);
      }
    }, 1000);
    return () => clearTimeout(timer);
  }, [searchQuery, location]);

  const fetchRecommendations = async (trends: TrendSpike[]) => {
    if (trends.length === 0) return;
    setIsGeneratingRecs(true);
    try {
      const userProfile = {
        niche: user?.business_domain || "SMB",
        location: location,
        target_audience: user?.business_domain ? `${user.business_domain} customers` : "General Audience"
      };

      const trendSignals = trends.slice(0, 3).map(t => ({
        keyword: t.keyword,
        velocity_label: t.score > 7 ? "Extreme" : t.score > 4 ? "High" : "Moderate",
        saturation_label: t.current_value > 70 ? "Saturated" : t.current_value > 40 ? "Competitive" : "Emerging",
        arbitrage_potential: (t.profit_score ?? 0) > 80 ? "Gold Mine" : (t.profit_score ?? 0) > 60 ? "High" : "Moderate",
        platform_fit: (t.social_score ?? 0) > 60 ? ["Instagram", "Facebook", "Google Search"] : (t.social_score ?? 0) > 30 ? ["Instagram", "Google Search"] : ["Google Search"],
        hashtags: t.rising_queries || []
      }));

      const res = await trendService.getRecommendations(userProfile, trendSignals);
      setRecommendations(res.recommendations);
      setRecContext(res.context);
    } catch (err) {
      console.error("Failed to generate recommendations", err);
    } finally {
      setIsGeneratingRecs(false);
    }
  };

  const handleGenerateContent = async (keyword: string) => {
    setIsGeneratingContent(true);
    setContentModalOpen(true);
    setContentSuggestions(null);
    
    try {
      const suggestions = await trendService.getContentSuggestions(keyword);
      setContentSuggestions(suggestions);
      toast.success("AI Content Generated", {
        description: `Got ${suggestions.video_ideas.length} video ideas for "${keyword}"`
      });
    } catch (err: any) {
      console.error("Failed to generate content suggestions", err);
      toast.error("Content Generation Failed", {
        description: err.response?.data?.detail || "Please try again"
      });
      setContentModalOpen(false);
    } finally {
      setIsGeneratingContent(false);
    }
  };

  // MOCK DATA REMOVED - All data now comes from real backend APIs

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [live, geo, timeline, gap, reach, saved] = await Promise.all([
        trendService.getLiveTrends(location),
        trendService.getGeoHeatmap(location),
        trendService.getSpikeTimeline(parseInt(timeframe), location),
        trendService.getMarketGapData(location),
        trendService.getPlatformReach(location),
        trendService.getWatchlist()
      ]);

      setWatchlist(saved || []);

      const hasData = live && live.length > 0;
      console.log('[TrendArbitrage] fetchData results:', {
        live: live?.length ?? 'n/a',
        geo: geo?.length ?? 'n/a',
        timeline: timeline?.length ?? 'n/a',
        gap: gap?.length ?? 'n/a',
        reach,
        hasData
      });

      if (!hasData) {
        // DO NOT load mock data automatically anymore.
        // Instead, keep state empty so we can show the "Initial Scan" UI.
        setLiveTrends([]);
        setError(null);
      } else {
        setLiveTrends(live || []);
        setGeoData(geo || []);
        setTimelineData(timeline || []);
        setMarketGapData(gap || []);
        setPlatformReach(reach || { google: 0, instagram: 0, facebook: 0, total_reach: "0%" });
        setError(null);
        fetchRecommendations(live);
      }

      setLastSync(new Date());
      setIsOffline(false);

    } catch (err: any) {
      console.error("Failed to fetch trend data", err);
      setError("Unable to reach the signal network. Please check your connection to the RAAMP server.");
      setIsOffline(true);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, [location, timeframe]);

  const handleTriggerScan = async () => {
    if (isScanning) return;
    setIsScanning(true);

    try {
      setScanStep("Global Node Sync Initialized...");
      console.log(`🚀 SCAN INITIATED for niche: ${user?.business_domain || 'marketing'}, location: ${location}`);
      toast.info("Vector Scan Initiated", {
        description: `Establishing connection to global signal nodes for ${location}...`
      });

      const response = await trendService.triggerFetch(user?.business_domain || 'marketing', location, category);
      const trendId = response.trend_id;
      console.log(`✅ Scan registered on backend. TrendID: ${trendId}`);

      // Poll for completion
      let attempts = 0;
      const maxAttempts = 20;

      const poll = async () => {
        if (attempts >= maxAttempts) {
          toast.warning("Network Latency High", { description: "Signal analysis is taking longer than expected. Update will occur in the background." });
          setIsScanning(false);
          setScanStep("");
          fetchData();
          return;
        }

        try {
          const statusRes = await trendService.getTrendStatus(trendId);
          console.log(`🔍 Scan Status [Attempt ${attempts}]:`, statusRes.status);

          // Show progress based on status if backend provides it, otherwise simulate phases
          if (attempts < 5) setScanStep("Scraping Local Search Intensity (Google)...");
          else if (attempts < 12) setScanStep("Interpreting Social Engagement Velocity (Meta)...");
          else setScanStep("Finalizing Vector Arbitrage Calculations...");

          if (statusRes.status === 'completed') {
            setScanStep("Vector Grid Acquired.");
            toast.success("Signal Acquired", { description: "The Vector Grid has been successfully updated with live market data." });
            await fetchData();
            setIsScanning(false);
            setScanStep("");
          } else if (statusRes.status === 'failed') {
            setError(`SCAN ERROR: ${statusRes.error_message || "Unknown signal processing failure."}`);
            toast.error("Signal Interpretation Failure", { description: "The scan failed to resolve correctly. Check your niche/location parameters." });
            setIsScanning(false);
            setScanStep("");
          } else {
            attempts++;
            setTimeout(poll, 3000);
          }
        } catch (e) {
          console.error("Polling error", e);
          setError("COMMUNICATION ERROR: Lost contact with scanning node during polling.");
          setIsScanning(false);
          setScanStep("");
        }
      };

      // Start polling
      setTimeout(poll, 3000);

    } catch (err: any) {
      console.error("Scan initiation error:", err);
      
      // Handle location not configured error
      if (err.response?.status === 400 && err.response?.data?.detail?.includes("Location not configured")) {
        toast.error("Location Not Configured", { 
          description: "Please complete your onboarding or set your business location in settings before scanning trends.",
          duration: 5000
        });
      } else {
        // Generic error handling
        const errorMessage = err.response?.data?.detail || err.message || "Unable to initiate scan";
        toast.error("Scan Launch Failed", { 
          description: errorMessage,
          duration: 4000
        });
      }
      
      setIsScanning(false);
      setScanStep("");
    }
  };

  const handleAddToWatchlist = async (keyword: string) => {
    try {
      await trendService.addTrendToWatchlist({
        keyword,
        niche: user?.business_domain || 'marketing',
        location: location
      });
      toast.success("Watchlist Updated", { description: `${keyword} is now being tracked for spikes.` });
      const updated = await trendService.getWatchlist();
      setWatchlist(updated);
    } catch (err: any) {
      toast.error(err.message || "Failed to add to watchlist");
    }
  };

  const handleRemoveFromWatchlist = async (keyword: string) => {
    try {
      await trendService.removeFromWatchlist(keyword);
      toast.success("Removed from Watchlist");
      setWatchlist(prev => prev.filter(item => item.keyword !== keyword));
    } catch (err) {
      toast.error("Failed to remove item");
    }
  };

  const tickerItems = liveTrends.length > 0
    ? liveTrends.map(t => `${t.keyword.toUpperCase()} [${t.location}] ${t.is_spike ? 'SPIKE' : t.label || 'TREND'}: ${t.is_spike ? `+${t.score}σ` : `+${t.score}%`}`)
    : ["SCANNING GLOBAL SIGNAL VECTORS...", "WAITING FOR MARKET SPIKES..."];

  const gapInsights = useMemo(() => {
    type GapInsight = {
      keyword: string; title: string; suggestion: string; hook: string;
      platform: string; format: string; prompt: string; badge: string;
      badgeClass: string; borderClass: string; interest: number; coverage: number;
    };
    const results: GapInsight[] = [];

    const pickHook = (keyword: string, fmt: string): string => {
      const rec = recommendations.find(r =>
        r.trend_name?.toLowerCase().includes(keyword.toLowerCase()) ||
        r.campaign_idea?.toLowerCase().includes(keyword.toLowerCase())
      );
      if (rec?.suggested_hooks?.length) return `"${rec.suggested_hooks[0]}"`;
      const hooks: Record<string, string> = {
        carousel: `"Here's what most people don't know about ${keyword}..."`,
        reel:     `"Wait — did you know ${keyword} can do this? 👀"`,
        story:    `"The truth about ${keyword} that no one talks about"`,
      };
      return hooks[fmt] ?? `"Everything you need to know about ${keyword}"`;
    };

    marketGapData
      .filter(g => g.saturation < 40 && g.velocity > 1)
      .slice(0, 3)
      .forEach(g => {
        const fmt = g.saturation < 20 ? 'reel' : 'carousel';
        const hook = pickHook(g.keyword, fmt);
        results.push({
          keyword: g.keyword,
          title: `Engagement for "${g.keyword}" is low`,
          suggestion: `Consider creating a ${fmt} post with hook: ${hook}`,
          hook, platform: g.velocity > 3 ? 'Instagram & Google' : 'Instagram',
          format: fmt,
          prompt: `Create a ${fmt === 'reel' ? 'short Reel script' : '5-slide carousel post'} about "${g.keyword}" for a ${user?.business_domain || 'business'} in ${location}. Open with the hook: ${hook}. Keep it simple, engaging, and easy to share.`,
          badge: g.velocity > 3 ? 'ACT NOW' : 'OPPORTUNITY',
          badgeClass: g.velocity > 3 ? 'text-red-400 bg-red-500/20 border-red-500/20' : 'text-emerald-400 bg-emerald-500/20 border-emerald-500/20',
          borderClass: g.velocity > 3 ? 'border-red-500/20' : 'border-emerald-500/20',
          interest: Math.min(100, Math.round(g.velocity * 20)),
          coverage: Math.min(100, Math.round(g.saturation)),
        });
      });

    liveTrends
      .filter(t => t.is_spike && (t.profit_score ?? 0) > 60)
      .slice(0, 2)
      .forEach(t => {
        const hook = pickHook(t.keyword, 'reel');
        results.push({
          keyword: t.keyword,
          title: `"${t.keyword}" is peaking in ${t.location} — no one is posting about it`,
          suggestion: `Consider creating a Reel with hook: ${hook}`,
          hook, platform: 'Instagram Reels', format: 'reel',
          prompt: `Write an Instagram Reel script about "${t.keyword}" for ${t.location}. Niche: ${t.niche || user?.business_domain || 'marketing'}. Open with: ${hook}. Keep it under 30 seconds and end with a clear call-to-action.`,
          badge: 'TRENDING',
          badgeClass: 'text-primary bg-primary/20 border-primary/20',
          borderClass: 'border-primary/20',
          interest: Math.min(100, Math.round((t.score ?? 5) * 8)),
          coverage: Math.min(100, Math.round(t.saturation_score ?? 20)),
        });
      });

    liveTrends
      .filter(t => t.lifecycle_stage === 'Emerging' && !t.is_spike)
      .slice(0, 1)
      .forEach(t => {
        const hook = pickHook(t.keyword, 'carousel');
        results.push({
          keyword: t.keyword,
          title: `"${t.keyword}" is just starting to trend — be one of the first`,
          suggestion: `Post a carousel with hook: ${hook} to reach early followers before competitors catch on.`,
          hook, platform: 'Instagram & Facebook', format: 'carousel',
          prompt: `Create a 5-slide educational carousel about "${t.keyword}" for ${t.location}. Niche: ${t.niche || user?.business_domain || 'marketing'}. Open with: ${hook}. Position the brand as an early expert on this emerging topic.`,
          badge: 'EARLY MOVER',
          badgeClass: 'text-amber-400 bg-amber-500/20 border-amber-500/20',
          borderClass: 'border-amber-500/20',
          interest: Math.min(100, Math.round((t.score ?? 3) * 8)),
          coverage: Math.min(100, Math.round(t.saturation_score ?? 15)),
        });
      });

    return results.slice(0, 5);
  }, [marketGapData, liveTrends, recommendations, user, location]);

  const ImpactNode = (props: any) => {
    const { cx, cy, payload } = props;
    const z = payload.avg_z || 0;
    if (z >= 4) {
      return (
        <g className="filter drop-shadow-[0_0_12px_rgba(0,224,208,1)]">
          <circle cx={cx} cy={cy} r={6} fill="#00E0D0" />
          <circle cx={cx} cy={cy} r={6} fill="#00E0D0" opacity="0.6">
            <animate attributeName="r" from="6" to="14" dur="1.5s" repeatCount="indefinite" />
            <animate attributeName="opacity" from="0.6" to="0" dur="1.5s" repeatCount="indefinite" />
          </circle>
          <circle cx={cx} cy={cy} r={2} fill="#fff" />
        </g>
      );
    }
    if (z >= 3) return <circle cx={cx} cy={cy} r={4} fill="#00E0D0" className="filter drop-shadow-[0_0_6px_rgba(0,224,208,0.8)]" />;
    return <circle cx={cx} cy={cy} r={3} fill="#00E0D0" opacity={0.3} />;
  };

  return (
    <Layout>
      <div className="space-y-0 pb-24 overflow-x-hidden bg-background relative">
        <div className="absolute top-0 left-1/4 w-1/2 h-1/2 bg-primary/5 blur-[160px] rounded-full pointer-events-none -z-10" />

        <div className="space-y-0">

          {/* Ticker Strip */}
          <div className="w-full overflow-hidden bg-white/5 border-y border-white/5 py-1 backdrop-blur-md relative z-20">
            <motion.div
              className="flex gap-12 whitespace-nowrap cursor-pointer hover:pause"
              animate={{ x: [0, -3000] }}
              transition={{ repeat: Infinity, duration: 80, ease: "linear" }}
              onHoverStart={() => { }} // Could dispatch a pause action
            >
              {[...tickerItems, ...tickerItems, ...tickerItems].map((item, i) => (
                <div
                  key={i}
                  onClick={() => {
                    const match = liveTrends.find(t =>
                      item.toUpperCase().startsWith(t.keyword.toUpperCase())
                    );
                    if (match) {
                      setSelectedTrend(match);
                      setCampaignModalOpen(true);
                    }
                  }}
                  className="flex items-center gap-2 text-[11px] font-mono font-bold tracking-tight text-white/40 hover:text-primary transition-colors hover:scale-105 transform duration-200"
                >
                  <div className="w-1 h-1 rounded-full bg-primary animate-pulse" />
                  {item}
                </div>
              ))}
            </motion.div>
          </div>

          <div className="space-y-8 px-6 pt-6">
            {/* Header Strip */}
            <div className="flex flex-col gap-6">
              <div className="flex justify-between items-center py-3 px-5 bg-black/20 backdrop-blur-xl border border-white/5 rounded-xl shadow-2xl">
                <div className="flex items-center gap-4">
                  <div className="p-2 bg-primary/20 rounded-lg border border-primary/40">
                    <Globe className="w-5 h-5 text-primary" />
                  </div>
                  <div className="hidden sm:block">
                    <h1 className="text-2xl font-bold font-bebas tracking-[0.1em] text-white uppercase leading-none mb-1">Profit Windows</h1>
                    <div className="flex items-center gap-4 text-[9px] font-mono font-black text-white/30 tracking-[0.1em] uppercase">
                      <div className="flex items-center gap-1.5">
                        <span>PK.VEC.NODE: {isOffline ? 'CACHE' : 'ACTIVE'}</span>
                        <div className={`w-1.5 h-1.5 rounded-full ${isOffline ? 'bg-amber-500' : 'bg-primary'} animate-pulse`} />
                      </div>
                      <div className="flex items-center gap-2 border-l border-white/10 pl-3 uppercase">
                        <RefreshCw className="w-2.5 h-2.5 text-white/20" />
                        <span>LAST SYNC: {Math.floor((new Date().getTime() - lastSync.getTime()) / 60000)}m AGO</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-6">


                  <div className="hidden lg:flex items-center gap-2 bg-white/5 border border-white/10 rounded-xl px-2 h-10">
                    <div className="flex items-center gap-2 px-3 h-8 text-white/40">
                      <Search className="w-4 h-4" />
                      <input
                        type="text"
                        placeholder="LOCATION..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value.toUpperCase())}
                        className="bg-transparent border-none outline-none text-sm font-mono font-bold text-white w-32 placeholder:text-white/20"
                      />
                    </div>
                    <Select value={timeframe} onValueChange={setTimeframe}>
                      <SelectTrigger className="w-[100px] border-none bg-transparent h-8 focus:ring-0 text-white/90 font-bold text-xs uppercase">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-950 border-white/10 text-white">
                        <SelectItem value="7">7D</SelectItem>
                        <SelectItem value="30">30D</SelectItem>
                        <SelectItem value="90">90D</SelectItem>
                      </SelectContent>
                    </Select>
                    <Select value={lifecycleFilter} onValueChange={setLifecycleFilter}>
                      <SelectTrigger className="w-[130px] border-none bg-transparent h-8 focus:ring-0 text-white/90 font-bold text-xs uppercase">
                        <SelectValue placeholder="LIFECYCLE" />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-950 border-white/10 text-white">
                        <SelectItem value="all">ALL STAGES</SelectItem>
                        <SelectItem value="Emerging">🌱 EMERGING</SelectItem>
                        <SelectItem value="Breakout">🚀 BREAKOUT</SelectItem>
                        <SelectItem value="Mainstream">📈 MAINSTREAM</SelectItem>
                        <SelectItem value="Saturated">⚠️ SATURATED</SelectItem>
                        <SelectItem value="Declining">📉 DECLINING</SelectItem>
                      </SelectContent>
                    </Select>

                    <div className="w-px h-5 bg-white/10" />
                    <div className="flex items-center gap-1.5 px-2 h-8">
                      <Database className="w-3.5 h-3.5 text-white/30 shrink-0" />
                      <input
                        type="text"
                        placeholder="SUB-NICHE..."
                        value={category === 'all' ? '' : category}
                        onChange={(e) => setCategory(e.target.value.trim().toLowerCase() || 'all')}
                        className="bg-transparent border-none outline-none text-xs font-mono font-bold text-white w-24 placeholder:text-white/20"
                      />
                    </div>
                  </div>

                  <Button
                    variant="outline"
                    onClick={handleTriggerScan}
                    disabled={isScanning || isLoading}
                    className="bg-primary/20 border-primary/40 text-primary hover:bg-primary hover:text-black font-bebas tracking-widest text-sm px-5 h-10"
                  >
                    <Zap className="w-4 h-4 mr-2" />
                    {isScanning ? "SCANNING..." : "SCAN WORLD"}
                  </Button>
                </div>
              </div>

              <AnimatePresence>
                {/* Subtle Offline Indicator (Pulse) */}
                {(isOffline || error) && (
                  <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="absolute top-20 right-6 flex flex-col gap-2 z-[100]"
                  >
                    <div className="flex items-center gap-3 bg-red-500/20 border border-red-500/40 px-4 py-3 rounded-xl backdrop-blur-3xl shadow-2xl max-w-sm">
                      <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
                      <div className="flex flex-col">
                        <span className="text-[10px] font-mono font-black text-red-500 uppercase tracking-[0.2em]">System Alert</span>
                        <span className="text-[11px] font-mono text-white/80 leading-tight">{error || "Connection failure detected."}</span>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Hero Trend / Empty State */}
              {liveTrends.length === 0 && !isLoading ? (
                <Reveal variant="fadeInUp">
                  <div className="relative overflow-hidden group p-12 bg-white/[0.02] border border-white/10 rounded-3xl backdrop-blur-3xl flex flex-col items-center text-center space-y-8">
                    <div className="w-20 h-20 bg-primary/20 rounded-full flex items-center justify-center animate-pulse">
                      <Globe className="w-10 h-10 text-primary" />
                    </div>
                    <div className="space-y-4 max-w-2xl">
                      <h2 className="text-4xl font-bold font-bebas tracking-[0.2em] text-white uppercase">No Trends Found</h2>
                      <p className="text-sm font-mono text-white/40 leading-relaxed uppercase">
                        No trend data detected for your niche yet. RAAMP needs to scan the global signal network
                        using your <span className="text-primary">Instagram Business Identity</span> and <span className="text-primary">Google Search Spikes</span>.
                      </p>
                      <div className="bg-primary/5 border border-primary/20 rounded-lg p-4 mt-4">
                        <p className="text-xs font-mono text-primary/80">
                          💡 <strong>Tip:</strong> Try adding business specialties (like "bubble tea", "vegan", "streetwear") in{' '}
                          <span className="underline hover:text-primary cursor-pointer" onClick={() => navigate('/settings/business-specialties')}>Settings</span>{' '}
                          to get more relevant trend detection.
                        </p>
                      </div>
                    </div>
                    <Button
                      onClick={handleTriggerScan}
                      disabled={isScanning}
                      className={`font-bebas text-2xl tracking-[0.2em] px-12 py-8 h-auto rounded-2xl transition-all shadow-[0_0_30px_rgba(0,224,208,0.3)] ${isScanning ? 'bg-primary/20 text-primary cursor-not-allowed' : 'bg-primary text-black hover:scale-105'
                        }`}
                    >
                      {isScanning ? (
                        <div className="flex flex-col items-center">
                          <div className="flex items-center gap-3">
                            <RefreshCw className="w-6 h-6 animate-spin" /> SCANNING...
                          </div>
                        </div>
                      ) : (
                        <div className="flex items-center gap-3">
                          <Zap className="w-6 h-6" /> INITIALIZE GLOBAL SCAN
                        </div>
                      )}
                    </Button>

                    {isScanning && (
                      <div className="flex flex-col items-center gap-2">
                        <div className="w-64 h-1 bg-white/5 rounded-full overflow-hidden">
                          <motion.div
                            className="h-full bg-primary"
                            animate={{ x: [-256, 256] }}
                            transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                          />
                        </div>
                        <span className="text-[10px] font-mono text-primary animate-pulse uppercase tracking-[0.2em]">{scanStep}</span>
                      </div>
                    )}

                    <div className="flex gap-8 text-[10px] font-mono font-black text-white/20 uppercase">
                      <span className="flex items-center gap-2">
                        <div className={`w-1.5 h-1.5 rounded-full ${isOffline ? 'bg-red-500' : 'bg-emerald-500'}`} />
                        {isOffline ? 'API Unreachable' : 'API Connected'}
                      </span>
                      <span className="flex items-center gap-2">
                        <div className={`w-1.5 h-1.5 rounded-full ${user?.business_domain ? 'bg-emerald-500' : 'bg-amber-500'}`} />
                        {user?.business_domain ? `Niche: ${user.business_domain}` : 'Niche Not Set'}
                      </span>
                      <span className="flex items-center gap-2">
                        <div className={`w-1.5 h-1.5 rounded-full ${isScanning ? 'bg-primary animate-ping' : 'bg-white/20'}`} />
                        {isScanning ? 'Active Syncing' : 'Waiting for Command'}
                      </span>
                    </div>
                  </div>
                </Reveal>
              ) : liveTrends.length > 0 && (
                <Reveal variant="fadeInUp">
                  <motion.div whileHover={{ y: -3 }} className="relative overflow-hidden group">
                    <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-primary/5 opacity-50 backdrop-blur-3xl rounded-2xl border border-white/10 group-hover:border-primary/50 transition-all duration-500" />
                    <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 blur-[80px] rounded-full -translate-y-1/2 translate-x-1/2" />
                    <div className="relative z-10 p-6 md:p-8 flex flex-col md:flex-row items-center gap-8">
                      <div className="flex-1 space-y-3">
                        <div className="flex items-center gap-3">
                          <Badge className={`${liveTrends[0].is_spike ? 'bg-primary/20 text-primary border-primary/30' : 'bg-blue-500/20 text-blue-400 border-blue-500/30'} py-1 px-4 font-mono font-black text-[10px] tracking-widest`}>
                            {liveTrends[0].is_spike ? 'FEATURED VEC SIGNAL' : liveTrends[0].label || 'BASELINE TREND'}
                          </Badge>
                          <div className="flex items-center gap-2 text-white/20 font-mono text-[10px] font-black uppercase tracking-widest">
                            <TrendingUp className="w-3 h-3" /> STRENGTH: {liveTrends[0].score}σ
                          </div>
                        </div>
                        <h2 className="text-4xl md:text-6xl font-bold font-bebas tracking-[0.1em] text-white leading-tight mb-4">{liveTrends[0].keyword}</h2>
                        <p className="text-base text-white/40 font-mono italic max-w-2xl">
                          {liveTrends[0].is_spike && liveTrends[0].score > 8
                            ? `High-velocity delta detected in ${liveTrends[0].location}. Arbitrage window critical.`
                            : liveTrends[0].is_spike 
                            ? `Emerging interest pattern in ${liveTrends[0].location} vector grid. Monitoring velocity.`
                            : `Current trend baseline in ${liveTrends[0].location}. No significant spikes detected yet—market stability observed.`}
                          {liveTrends[0].niche ? ` Sector: ${liveTrends[0].niche}.` : ''}
                        </p>
                        <div className="flex gap-4 pt-4">
                          <Button
                            className="bg-primary text-black hover:opacity-90 font-bebas text-lg px-8 h-12 rounded-xl"
                            onClick={() => {
                              const base = liveTrends[0];
                              setDeployContentType("carousel");
                              setDeployPrompt(`Create a 5-slide carousel post about "${base.keyword}" for ${base.location}. Niche: ${base.niche}. Make each slide educational and easy to share.`);
                              setDeploySheetOpen(true);
                            }}
                          >DEPLOY AI ASSETS</Button>
                          <Button
                            variant="outline"
                            className="border-white/10 bg-white/[0.03] text-white/60 hover:text-white font-bebas text-lg px-8 h-12 rounded-xl"
                            onClick={() => setGapAnalysisOpen(true)}
                          >AI GAP INSIGHTS</Button>
                        </div>
                      </div>
                      <div className="w-40 h-40 flex items-center justify-center relative">
                        <div className={`w-32 h-32 rounded-full ${liveTrends[0].is_spike ? 'bg-gradient-to-br from-primary/50 to-emerald-500/50' : 'bg-gradient-to-br from-blue-500/30 to-cyan-500/30'} p-[1px]`}>
                          <div className="w-full h-full rounded-full bg-background flex flex-col items-center justify-center p-4 text-center">
                            {liveTrends[0].is_spike ? (
                              <>
                                <Flame className="w-8 h-8 text-primary mb-1" />
                                <span className="text-xl font-bold font-bebas text-white tracking-widest">SPIKE</span>
                                <span className="text-[8px] font-mono text-primary/60 tracking-widest uppercase">{liveTrends[0].score > 10 ? 'CRITICAL' : 'DETECTED'}</span>
                              </>
                            ) : (
                              <>
                                <Activity className="w-8 h-8 text-blue-400 mb-1" />
                                <span className="text-xl font-bold font-bebas text-white tracking-widest">BASELINE</span>
                                <span className="text-[8px] font-mono text-blue-400/60 tracking-widest uppercase">MONITORING</span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                </Reveal>
              )}

              {/* Arbitrage Intelligence Strategy Brief */}
              {recContext && recommendations.length > 0 && (
                <Reveal variant="fadeIn">
                  <div className="bg-primary/5 border-l-4 border-l-primary p-4 rounded-r-xl backdrop-blur-md mb-2">
                    <div className="flex items-start gap-4">
                      <div className="p-2 bg-primary/20 rounded-full mt-1">
                        <Info className="w-4 h-4 text-primary" />
                      </div>
                      <div className="space-y-1">
                        <h4 className="text-[10px] font-mono font-black text-primary/60 uppercase tracking-widest">Market Strategy Brief</h4>
                        <p className="text-sm text-white/80 font-mono italic leading-relaxed">
                          {recContext}
                        </p>
                      </div>
                    </div>
                  </div>
                </Reveal>
              )}

              {/* Arbitrage Intelligence Cards (Layer 2 Output) */}
              {(recommendations.length > 0 || isGeneratingRecs) && (
                <div className="space-y-6">
                  <div className="flex justify-between items-end">
                    <div className="space-y-1">
                      <h2 className="text-2xl font-bold font-bebas tracking-wider text-white flex items-center gap-3">
                        <Sparkles className="w-6 h-6 text-primary animate-pulse" /> ARBITRAGE STRATEGY
                      </h2>
                      <p className="text-[10px] font-mono font-bold text-white/20 uppercase tracking-[0.2em]">Deployment-Ready Campaign Vectors</p>
                    </div>
                    {isGeneratingRecs && (
                      <div className="flex items-center gap-2 text-[10px] font-mono text-primary font-black uppercase animate-pulse">
                        <RefreshCw className="w-3 h-3 animate-spin" /> GENUINE AI REASONING...
                      </div>
                    )}
                  </div>

                  <div className="flex gap-6 overflow-x-auto pb-6 -mx-2 px-2 scrollbar-none snap-x">
                    {recommendations.map((rec, i) => (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: i * 0.1 }}
                        whileHover={{ y: -5 }}
                        className="min-w-[320px] max-w-[320px] bg-white/[0.03] border border-white/10 rounded-2xl overflow-hidden group snap-center flex flex-col relative"
                      >
                        <div className="absolute top-0 right-0 p-4">
                          <Badge className="bg-primary/20 text-primary border-primary/30 font-mono font-black text-[9px]">PRIORITY {rec.priority}/10</Badge>
                        </div>

                        <div className="p-6 space-y-4 flex-1">
                          <div className="space-y-1">
                            <div className="flex items-center gap-2 text-[9px] font-mono text-primary/60 font-black uppercase tracking-tighter">
                              <Target className="w-3 h-3" /> {rec.recommended_platform} STRATEGY
                            </div>
                            <h3 className="text-xl font-bold font-bebas text-white tracking-wider group-hover:text-primary transition-colors uppercase">{rec.campaign_idea}</h3>
                          </div>

                          <div className="space-y-2">
                            <div className="flex flex-wrap gap-2 pt-1">
                              {rec.suggested_hooks.slice(0, 2).map((hook, h) => (
                                <div key={h} className="text-[9px] font-mono bg-white/5 border border-white/10 rounded-md px-2 py-1 text-white/40 italic flex items-center gap-1.5">
                                  <Zap className="w-2 h-2 text-primary" /> {hook}
                                </div>
                              ))}
                            </div>
                            {rec.reasoning && (
                              <div className="space-y-1.5 pt-1">
                                <button
                                  className="text-[9px] font-mono text-white/30 hover:text-primary flex items-center gap-1 transition-colors"
                                  onClick={() => {
                                    setExpandedReasonings(prev => {
                                      const next = new Set(prev);
                                      if (next.has(i)) next.delete(i); else next.add(i);
                                      return next;
                                    });
                                  }}
                                >
                                  WHY THIS WORKS {expandedReasonings.has(i) ? '▴' : '▾'}
                                </button>
                                {expandedReasonings.has(i) && (
                                  <p className="text-[10px] font-mono text-white/50 italic border-l-2 border-primary/30 pl-3 leading-relaxed">
                                    {rec.reasoning}
                                  </p>
                                )}
                              </div>
                            )}
                          </div>
                        </div>

                        <div className="p-4 bg-white/5 border-t border-white/5 flex items-center justify-between">
                          <div className="flex flex-col">
                            <span className="text-[8px] font-mono text-white/20 uppercase font-black">Goal</span>
                            <span className="text-[10px] font-mono text-white/60 font-bold uppercase">{rec.expected_marketing_goal}</span>
                          </div>
                          <Button
                            className="h-8 rounded-lg bg-primary text-black font-bebas text-xs tracking-wider px-4"
                            onClick={() => {
                              const hooks = rec.suggested_hooks.length > 0 ? ` Use hook: "${rec.suggested_hooks[0]}".` : '';
                              const prompt = `${rec.campaign_idea} on ${rec.recommended_platform}.${hooks} Goal: ${rec.expected_marketing_goal}.`;
                              navigate("/dashboard/creative", { state: { prefillPrompt: prompt } });
                            }}
                          >EXECUTE</Button>
                        </div>
                      </motion.div>
                    ))}

                    {isGeneratingRecs && Array(3).fill(0).map((_, i) => (
                      <div key={i} className="min-w-[320px] bg-white/5 border border-white/10 rounded-2xl h-[240px] animate-pulse flex items-center justify-center">
                        <Wind className="w-8 h-8 text-white/10 animate-bounce" />
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {error && (
                <div className="bg-red-500/10 border border-red-500/20 p-4 rounded-xl flex items-center gap-3 text-red-100/60 text-[10px] font-mono uppercase">
                  <AlertCircle className="w-4 h-4 text-red-400" />
                  <span>{error}</span>
                </div>
              )}

              {/* Content Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Column 1: Timeline & Feed */}
                <div className="lg:col-span-8 space-y-8">
                  {/* Timeline */}
                  <Reveal variant="fadeInUp" delay={0.3}>
                    <div className="p-8 bg-white/[0.03] backdrop-blur-xl border border-white/10 rounded-2xl shadow-xl overflow-hidden relative">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <h2 className="text-xl font-bold flex items-center gap-3 font-bebas tracking-[0.1em] text-white">
                            <Activity className="w-6 h-6 text-primary" /> Trend Activity
                          </h2>
                          <p className="text-[10px] font-mono font-bold text-white/20 tracking-widest mt-1 uppercase">How search interest changes over time</p>
                        </div>
                        {timelineData.length > 0 && (
                          <div className="hidden sm:flex gap-5 text-right">
                            <div>
                              <p className="text-[10px] font-mono text-white/30 uppercase tracking-wider">Days Tracked</p>
                              <p className="text-2xl font-bebas text-white">{timelineData.length}</p>
                            </div>
                            <div>
                              <p className="text-[10px] font-mono text-white/30 uppercase tracking-wider">Peak Activity</p>
                              <p className="text-2xl font-bebas text-primary">{Math.max(...timelineData.map(d => d.count))}</p>
                            </div>
                          </div>
                        )}
                      </div>

                      <div className="h-[300px] w-full relative">
                        {/* Background Scan Grid Visualization */}
                        <div className="absolute inset-0 bg-[linear-gradient(rgba(0,224,208,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(0,224,208,0.03)_1px,transparent_1px)] bg-[size:20px_20px] pointer-events-none" />

                        {timelineData.length === 0 ? (
                          <div className="h-full w-full flex flex-col items-center justify-center gap-4 text-center">
                            <Database className="w-10 h-10 text-white/10" />
                            <p className="text-xs font-mono text-white/20 uppercase tracking-widest">Data will appear here after your first scan</p>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={handleTriggerScan}
                              disabled={isScanning}
                              className="border-white/10 text-white/30 hover:text-primary hover:border-primary/30 font-mono text-xs"
                            >
                              {isScanning ? "Scanning..." : "Run Scan Now"}
                            </Button>
                          </div>
                        ) : (
                          <ResponsiveContainer width="100%" height="100%">
                            <ComposedChart data={timelineData}>
                              <defs>
                                <linearGradient id="velocityFill" x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="5%" stopColor="#00E0D0" stopOpacity={0.2} />
                                  <stop offset="95%" stopColor="#00E0D0" stopOpacity={0} />
                                </linearGradient>
                              </defs>
                              <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" vertical={false} />
                              <XAxis
                                dataKey="date"
                                stroke="#ffffff40"
                                fontSize={11}
                                tickFormatter={(str) => new Date(str).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                                tickLine={false}
                                axisLine={{ stroke: '#ffffff15' }}
                                dy={10}
                              />
                              <YAxis
                                stroke="#ffffff40"
                                fontSize={11}
                                tickLine={false}
                                axisLine={{ stroke: '#ffffff15' }}
                                dx={-10}
                                label={{ value: 'Activity Level', angle: -90, position: 'insideLeft', fill: '#ffffff30', fontSize: 10, dy: 50 }}
                              />
                              <Tooltip
                                contentStyle={{ backgroundColor: '#09090b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', padding: '12px' }}
                                formatter={(value: number | string) => [value, 'Trend Activity']}
                                labelFormatter={(label) => new Date(label).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })}
                                itemStyle={{ color: '#00E0D0', fontSize: '12px', fontFamily: 'monospace' }}
                                labelStyle={{ color: '#ffffff60', fontSize: '11px', fontFamily: 'monospace', marginBottom: '6px' }}
                              />
                              <Area type="monotone" dataKey="count" stroke="none" fill="url(#velocityFill)" />
                              <Line
                                type="monotone"
                                dataKey="count"
                                stroke="#00E0D0"
                                strokeWidth={2.5}
                                dot={(props: { cx: number; cy: number; payload: { avg_z: number } }) => {
                                  const { cx, cy, payload } = props;
                                  const isHot = payload.avg_z > 4;
                                  return <circle cx={cx} cy={cy} r={isHot ? 5 : 3} fill={isHot ? "#F59E0B" : "#00E0D0"} />;
                                }}
                                activeDot={{ r: 6, fill: '#00E0D0' }}
                                animationDuration={1500}
                              />
                            </ComposedChart>
                          </ResponsiveContainer>
                        )}
                      </div>
                    </div>
                  </Reveal>

                  {/* Arbitrage Sweet Spot Scatter Chart */}
                  <Reveal variant="fadeInUp" delay={0.35}>
                    <div className="p-8 bg-white/[0.03] backdrop-blur-xl border border-white/10 rounded-2xl shadow-xl overflow-hidden relative">
                      <div className="flex items-center justify-between mb-6">
                        <div>
                          <h2 className="text-xl font-bold flex items-center gap-3 font-bebas tracking-[0.1em] text-white">
                            <Target className="w-6 h-6 text-primary" /> ARBITRAGE SWEET SPOT
                          </h2>
                          <p className="text-[10px] font-mono font-bold text-white/10 tracking-widest mt-1 uppercase">Saturation vs Velocity Matrix</p>
                        </div>
                        <Badge className="bg-primary/10 text-primary border-primary/20 font-mono text-[9px] px-2 py-0.5 uppercase tracking-widest font-black">AI GRID ACTIVE</Badge>
                      </div>

                      <div className="h-[350px] w-full relative">
                        {/* Matrix Quadrant Labels */}
                        <div className="absolute top-4 right-4 text-[11px] font-mono text-white/40 font-black uppercase text-right leading-relaxed bg-black/40 backdrop-blur-md px-3 py-1 rounded-lg border border-white/5">
                          <span className="text-red-400">CROWDED</span><br />(High Saturation)
                        </div>
                        <div className="absolute top-4 left-4 text-[11px] font-mono text-white/40 font-black uppercase leading-relaxed bg-black/40 backdrop-blur-md px-3 py-1 rounded-lg border border-white/5">
                          <span className="text-primary">GOLD MINE</span><br />(High Velocity)
                        </div>
                        <div className="absolute bottom-12 left-4 text-[11px] font-mono text-white/40 font-black uppercase leading-relaxed bg-black/40 backdrop-blur-md px-3 py-1 rounded-lg border border-white/5">
                          EMERGING
                        </div>
                        <div className="absolute bottom-12 right-4 text-[11px] font-mono text-white/40 font-black uppercase text-right leading-relaxed bg-black/40 backdrop-blur-md px-3 py-1 rounded-lg border border-white/5">
                          FADING
                        </div>

                        {marketGapData.length === 0 && (
                          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 z-10 pointer-events-none">
                            <Target className="w-10 h-10 text-white/10" />
                            <p className="text-xs font-mono text-white/20 uppercase tracking-widest text-center">Arbitrage matrix populates after scan</p>
                          </div>
                        )}
                        <ResponsiveContainer width="100%" height="100%">
                          <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" />
                            {/* Quadrant background fills */}
                            <ReferenceArea x1={0} x2={50} y1={5} y2={10} fill="#00E0D0" fillOpacity={0.04} />
                            <ReferenceArea x1={50} x2={100} y1={5} y2={10} fill="#ef4444" fillOpacity={0.04} />
                            <ReferenceArea x1={0} x2={50} y1={0} y2={5} fill="#F59E0B" fillOpacity={0.03} />
                            <XAxis
                              type="number"
                              dataKey="saturation"
                              name="Status"
                              unit="%"
                              domain={[0, 100]}
                              stroke="#ffffff50"
                              fontSize={11}
                              axisLine={{ stroke: '#ffffff15' }}
                              tickLine={false}
                              label={{ value: 'Competition Level →', position: 'insideBottomRight', fill: '#ffffff50', fontSize: 11, dy: 10 }}
                            />
                            <YAxis
                              type="number"
                              dataKey="velocity"
                              name="Velocity"
                              domain={[0, 10]}
                              stroke="#ffffff50"
                              fontSize={11}
                              axisLine={{ stroke: '#ffffff15' }}
                              tickLine={false}
                              label={{ value: 'Growth Speed ↑', angle: -90, position: 'insideLeft', fill: '#ffffff50', fontSize: 11, dy: 50 }}
                            />
                            <ZAxis type="number" dataKey="arbitrage_score" range={[100, 1000]} />
                            <Tooltip
                              cursor={{ strokeDasharray: '3 3' }}
                              content={({ active, payload }) => {
                                if (active && payload && payload.length) {
                                  const data = payload[0].payload;
                                  const isGoldMine = data.quadrant === 'Gold Mine';
                                  const isCrowded = data.quadrant === 'Crowded';
                                  return (
                                    <div className="bg-black/95 border border-white/10 p-4 rounded-xl shadow-2xl backdrop-blur-md min-w-[200px]">
                                      <p className="font-bebas text-white text-xl tracking-wider uppercase mb-1">{data.keyword}</p>
                                      <p className={`text-xs font-mono font-bold mb-3 ${
                                        isGoldMine ? 'text-primary' :
                                        isCrowded ? 'text-red-400' :
                                        data.quadrant === 'Emerging' ? 'text-amber-400' : 'text-white/30'
                                      }`}>
                                        {isGoldMine ? '🔥 Great opportunity — post now!' :
                                         isCrowded ? '⚠️ Very competitive right now' :
                                         data.quadrant === 'Emerging' ? '🌱 Early stage — keep an eye on it' :
                                         '📉 Interest is fading'}
                                      </p>
                                      <div className="space-y-1.5 text-[11px] font-mono">
                                        <div className="flex justify-between"><span className="text-white/40">Growth Speed:</span><span className="text-primary font-bold">{data.velocity}×</span></div>
                                        <div className="flex justify-between"><span className="text-white/40">Competition:</span><span className="text-white/70">{data.saturation}%</span></div>
                                        {data.profit_score !== undefined && (
                                          <div className="flex justify-between">
                                            <span className="text-white/40">Opportunity:</span>
                                            <span className={`font-bold ${data.profit_score >= 80 ? 'text-emerald-400' : data.profit_score >= 60 ? 'text-blue-400' : 'text-amber-400'}`}>
                                              {data.profit_score}/100
                                            </span>
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  );
                                }
                                return null;
                              }}
                            />
                            <Scatter name="Trends" data={marketGapData}>
                              {marketGapData.map((entry, index) => (
                                <Cell
                                  key={`cell-${index}`}
                                  fill={entry.quadrant === 'Gold Mine' ? '#00E0D0' : entry.quadrant === 'Crowded' ? '#ef4444' : '#ffffff20'}
                                  className="filter drop-shadow-[0_0_8px_rgba(0,224,208,0.3)] transition-all duration-500 hover:opacity-100"
                                  opacity={0.7}
                                />
                              ))}
                            </Scatter>
                          </ScatterChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  </Reveal>

                  {/* Live Feed */}
                  <Reveal variant="fadeInUp" delay={0.4}>
                    <div className="p-8 bg-white/[0.03] backdrop-blur-xl border border-white/10 rounded-2xl shadow-xl space-y-6">
                      <div className="flex justify-between items-center">
                        <h2 className="text-xl font-bold font-bebas tracking-[0.1em] text-white uppercase flex items-center gap-3">
                          <div className="w-1.5 h-6 bg-primary rounded-full" /> Signals Feed
                        </h2>
                        <Button variant="ghost" onClick={() => setShowAllTrends(!showAllTrends)} className="text-[10px] font-mono font-bold text-primary/60 hover:text-primary uppercase h-8 px-4">
                          {showAllTrends ? "COLLAPSE" : "VIEW ALL"}
                        </Button>
                      </div>

                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        {(showAllTrends ? liveTrends : liveTrends.slice(0, 4))
                          .filter(trend => lifecycleFilter === "all" || trend.lifecycle_stage === lifecycleFilter)
                          .map((trend) => (
                          <TrendCard
                            key={trend.id}
                            trend={trend}
                            onClick={() => {
                              setSelectedTrend(trend);
                              setCampaignModalOpen(true);
                            }}
                            onGenerateContent={handleGenerateContent}
                          />
                        ))}
                      </div>
                    </div>
                  </Reveal>

                  {/* Watchlist Section */}
                  {watchlist.length > 0 && (
                    <Reveal variant="fadeInUp" delay={0.5}>
                      <div className="p-8 bg-white/[0.03] backdrop-blur-xl border border-white/10 rounded-2xl shadow-xl space-y-6">
                        <h2 className="text-xl font-bold font-bebas tracking-[0.1em] text-white uppercase flex items-center gap-3">
                          <div className="w-1.5 h-6 bg-amber-500 rounded-full" /> Tracked Vectors
                        </h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {watchlist.map((item) => (
                            <div key={item.id} className="p-4 bg-white/5 border border-white/10 rounded-xl relative group">
                              <button
                                onClick={() => handleRemoveFromWatchlist(item.keyword)}
                                className="absolute top-2 right-2 text-white/20 hover:text-red-500 transition-colors"
                              >
                                <AlertCircle className="w-4 h-4" />
                              </button>
                              <div className="flex flex-col gap-1">
                                <span className="text-sm font-bold font-bebas text-white tracking-widest uppercase">{item.keyword}</span>
                                <div className="flex gap-4 items-center">
                                  <div className="text-[10px] font-mono text-primary flex gap-1 items-center">
                                    <Wind className="w-3 h-3" /> {item.last_velocity}σ
                                  </div>
                                  <div className="text-[10px] font-mono text-white/40 flex gap-1 items-center">
                                    <Database className="w-3 h-3" /> {item.last_saturation}%
                                  </div>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </Reveal>
                  )}
                </div>

                {/* Column 2: Geography & Analytics */}
                <div className="lg:col-span-4 space-y-8">
                  {/* Geo Intensity */}
                  <Reveal variant="fadeInUp" delay={0.5}>
                    <div className="p-8 bg-white/[0.03] backdrop-blur-xl border border-white/10 rounded-2xl shadow-xl space-y-6">
                      <h2 className="text-xl font-bold font-bebas tracking-[0.1em] text-white flex items-center gap-3"><MapPin className="w-6 h-6 text-primary" /> GEO INTENSITY</h2>
                      {geoData.length === 0 ? (
                        <div className="h-[200px] flex flex-col items-center justify-center gap-3 text-center">
                          <MapPin className="w-8 h-8 text-white/10" />
                          <p className="text-xs font-mono text-white/20 uppercase tracking-widest">Regional data loads after scan</p>
                        </div>
                      ) : (
                        <div className="space-y-3 max-h-[260px] overflow-y-auto pr-1 scrollbar-none">
                          {[...geoData]
                            .sort((a, b) => b.intensity - a.intensity)
                            .map((region, idx) => (
                              <div
                                key={idx}
                                className={`flex items-center gap-3 cursor-pointer group rounded-lg transition-colors ${
                                  selectedCity?.city === region.city ? 'bg-primary/10 px-2 -mx-2' : ''
                                }`}
                                onClick={() => setSelectedCity(prev => prev?.city === region.city ? null : region)}
                              >
                                <span className="text-[10px] font-mono text-white/20 w-4 shrink-0 text-right">{idx + 1}</span>
                                <div className="flex-1 space-y-1">
                                  <div className="flex items-center justify-between text-xs font-mono">
                                    <span className="text-white/70 group-hover:text-white transition-colors flex items-center gap-1.5">
                                      <MapPin className={`w-3 h-3 shrink-0 ${selectedCity?.city === region.city ? 'text-primary' : 'text-primary'}`} />
                                      {region.city}
                                    </span>
                                    <span className={`font-bold shrink-0 ml-2 ${
                                      region.intensity > 80 ? 'text-amber-400' :
                                      region.intensity > 50 ? 'text-primary' : 'text-white/30'
                                    }`}>
                                      {region.intensity}%
                                    </span>
                                  </div>
                                  <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                                    <div
                                      className={`h-full rounded-full transition-all duration-700 ${
                                        region.intensity > 80 ? 'bg-amber-400' : 'bg-primary'
                                      }`}
                                      style={{ width: `${region.intensity}%` }}
                                    />
                                  </div>
                                  {selectedCity?.city === region.city && (
                                    <div className="pt-1.5 pb-1 flex flex-wrap gap-x-4 gap-y-1">
                                      {region.keyword && (
                                        <span className="text-[10px] font-mono text-white/40">
                                          <span className="text-white/20">KEYWORD</span> {region.keyword}
                                        </span>
                                      )}
                                      {region.velocity && (
                                        <span className="text-[10px] font-mono text-primary">
                                          <span className="text-white/20">VELOCITY</span> {region.velocity}
                                        </span>
                                      )}
                                      {region.delta && (
                                        <span className="text-[10px] font-mono text-emerald-400">
                                          <span className="text-white/20">Δ</span> {region.delta}
                                        </span>
                                      )}
                                    </div>
                                  )}
                                </div>
                              </div>
                            ))}
                          <div className="pt-2 border-t border-white/5 flex justify-between text-[10px] font-mono text-white/20 uppercase">
                            <span>Pakistan</span>
                            <span>{geoData.filter(g => g.intensity > 80).length} hotspot{geoData.filter(g => g.intensity > 80).length !== 1 ? 's' : ''}</span>
                          </div>
                        </div>
                      )}
                    </div>
                  </Reveal>

                  {/* Market Arbitrage Depth */}
                  <Reveal variant="fadeInUp" delay={0.6}>
                    <div className="p-8 bg-white/[0.03] backdrop-blur-xl border border-white/10 rounded-2xl shadow-xl space-y-6">
                      <h2 className="text-xl font-bold font-bebas tracking-[0.1em] text-white flex items-center gap-3"><Target className="w-6 h-6 text-primary" /> OPPORTUNITIES</h2>
                      <div className="h-40 flex items-center justify-center relative">
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Tooltip contentStyle={{ backgroundColor: '#000', borderRadius: '8px', border: '1px solid #333' }} itemStyle={{ fontSize: '12px', fontFamily: 'monospace' }} />
                            <Pie
                              data={[
                                { name: "Google", value: platformReach?.google ?? 0, fill: "#00E0D0" },
                                { name: "Instagram", value: platformReach?.instagram ?? 0, fill: "#C084FC" },
                                { name: "Facebook", value: platformReach?.facebook ?? 0, fill: "#F59E0B" }
                              ]}
                              innerRadius={45}
                              outerRadius={60}
                              paddingAngle={5}
                              dataKey="value"
                              stroke="none"
                            >
                              <Cell fill="#00E0D0" /><Cell fill="#C084FC" /><Cell fill="#F59E0B" />
                            </Pie>
                          </PieChart>
                        </ResponsiveContainer>
                        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                          <span className="text-2xl font-bebas text-white">{platformReach?.total_reach || '0%'}</span>
                          <span className="text-[8px] font-mono text-white/30 uppercase font-black">Reach</span>
                        </div>
                      </div>
                      <div className="flex justify-center gap-4 py-2">
                        <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-[#00E0D0]" /><span className="text-[9px] font-mono text-white/60 uppercase">Google</span></div>
                        <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-[#C084FC]" /><span className="text-[9px] font-mono text-white/60 uppercase">Insta</span></div>
                        <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-[#F59E0B]" /><span className="text-[9px] font-mono text-white/60 uppercase">Facebook</span></div>
                      </div>
                      <Sheet open={gapAnalysisOpen} onOpenChange={setGapAnalysisOpen}>
                        <SheetTrigger asChild>
                          <Button className="w-full bg-white/5 border border-primary/30 text-primary font-bebas text-xl h-14 rounded-xl hover:bg-primary hover:text-black">ANALYZE GAPS</Button>
                        </SheetTrigger>
                        <SheetContent className="bg-[#0a0a0a] border-l border-white/10 text-white w-[440px] flex flex-col gap-0 p-0">
                          {/* Header */}
                          <div className="px-6 pt-6 pb-4 border-b border-white/5 shrink-0">
                            <div className="flex items-start justify-between gap-3">
                              <div className="space-y-0.5">
                                <SheetTitle className="font-bebas text-2xl tracking-wide flex items-center gap-2 text-white">
                                  <Lightbulb className="w-5 h-5 text-primary" /> AI GAP INSIGHTS
                                </SheetTitle>
                                <SheetDescription className="text-xs text-white/40 leading-relaxed">
                                  Topics your audience is searching for that you haven't created content about yet.
                                </SheetDescription>
                              </div>
                              {gapInsights.length > 0 && (
                                <div className="shrink-0 text-center bg-primary/10 border border-primary/20 rounded-xl px-3 py-2">
                                  <div className="text-2xl font-bebas text-primary leading-none">{gapInsights.length}</div>
                                  <div className="text-[8px] font-mono text-primary/60 uppercase tracking-wider">gaps found</div>
                                </div>
                              )}
                            </div>

                            {/* Platform reach bars */}
                            {platformReach && (
                              <div className="mt-4 space-y-1.5">
                                <p className="text-[9px] font-mono text-white/30 uppercase tracking-widest mb-2">Where your audience is active</p>
                                {([
                                  { label: 'Google',    value: platformReach.google,    color: 'bg-[#00E0D0]', textColor: 'text-[#00E0D0]' },
                                  { label: 'Instagram', value: platformReach.instagram, color: 'bg-[#C084FC]', textColor: 'text-[#C084FC]' },
                                  { label: 'Facebook',  value: platformReach.facebook,  color: 'bg-[#F59E0B]', textColor: 'text-[#F59E0B]' },
                                ]).map(p => (
                                  <div key={p.label} className="flex items-center gap-3">
                                    <span className="text-[9px] font-mono text-white/40 w-16 shrink-0">{p.label}</span>
                                    <div className="flex-1 h-1.5 bg-white/5 rounded-full overflow-hidden">
                                      <div className={`h-full ${p.color} rounded-full`} style={{ width: `${p.value}%` }} />
                                    </div>
                                    <span className={`text-[10px] font-mono font-bold ${p.textColor} w-8 text-right`}>{p.value}%</span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>

                          {/* Gap cards */}
                          <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
                            {gapInsights.length > 0 ? gapInsights.map((insight, idx) => (
                              <div key={idx} className={`bg-white/[0.02] border ${insight.borderClass} rounded-2xl overflow-hidden`}>
                                {/* Card header */}
                                <div className="px-4 pt-4 pb-2 space-y-2">
                                  <div className="flex justify-between items-start gap-2">
                                    <p className="text-sm font-semibold text-white leading-snug">{insight.title}</p>
                                    <Badge className={`${insight.badgeClass} border text-[9px] font-mono font-black shrink-0`}>{insight.badge}</Badge>
                                  </div>
                                  <p className="text-xs text-white/60 leading-relaxed">{insight.suggestion}</p>
                                </div>

                                {/* Interest vs coverage bars */}
                                <div className="px-4 pb-3 space-y-2 pt-1">
                                  {[
                                    { label: 'Audience interest', value: insight.interest, barClass: 'bg-primary' },
                                    { label: 'Current coverage',  value: insight.coverage,  barClass: 'bg-white/25' },
                                  ].map(bar => (
                                    <div key={bar.label} className="space-y-1">
                                      <div className="flex justify-between text-[9px] font-mono text-white/30">
                                        <span>{bar.label}</span>
                                        <span>{bar.value}%</span>
                                      </div>
                                      <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                                        <div className={`h-full ${bar.barClass} rounded-full`} style={{ width: `${bar.value}%` }} />
                                      </div>
                                    </div>
                                  ))}
                                </div>

                                {/* Format + platform tags */}
                                <div className="px-4 pb-3 flex items-center gap-2">
                                  <span className="text-[9px] font-mono bg-white/5 border border-white/10 rounded-md px-2 py-1 text-white/40">
                                    {insight.format === 'reel' ? '🎬 Reel' : insight.format === 'story' ? '✨ Story' : '📸 Carousel'}
                                  </span>
                                  <span className="text-[9px] font-mono bg-white/5 border border-white/10 rounded-md px-2 py-1 text-white/40">{insight.platform}</span>
                                </div>

                                {/* CTA */}
                                <div className="px-3 pb-3">
                                  <Button
                                    size="sm"
                                    className="w-full bg-white/5 hover:bg-primary hover:text-black text-white/60 border border-white/10 hover:border-primary text-xs font-mono transition-all rounded-xl h-9"
                                    onClick={() => {
                                      setGapAnalysisOpen(false);
                                      navigate("/dashboard/creative", { state: { prefillPrompt: insight.prompt } });
                                    }}
                                  >
                                    Create this post — prompt ready to edit →
                                  </Button>
                                </div>
                              </div>
                            )) : (
                              <div className="flex flex-col items-center justify-center py-16 gap-4 text-center">
                                <div className="w-14 h-14 bg-white/5 rounded-full flex items-center justify-center">
                                  <Sparkles className="w-7 h-7 text-white/20" />
                                </div>
                                <div className="space-y-1">
                                  <p className="text-sm font-bebas text-white/40 tracking-wide">No gaps detected yet</p>
                                  <p className="text-xs font-mono text-white/20">Run a scan first to find content opportunities.</p>
                                </div>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="border-white/10 text-white/40 font-mono text-xs"
                                  onClick={() => { setGapAnalysisOpen(false); handleTriggerScan(); }}
                                >
                                  Run a scan
                                </Button>
                              </div>
                            )}
                          </div>
                        </SheetContent>
                      </Sheet>
                    </div>
                  </Reveal>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Deploy AI Assets Sheet */}
      <Sheet open={deploySheetOpen} onOpenChange={setDeploySheetOpen}>
        <SheetContent className="bg-black/95 border-l border-white/10 text-white w-[420px] flex flex-col">
          <SheetHeader className="mb-6">
            <SheetTitle className="font-bebas text-3xl tracking-wide flex items-center gap-2">
              <Zap className="w-6 h-6 text-primary" /> DEPLOY AI ASSETS
            </SheetTitle>
            <SheetDescription className="font-mono text-xs text-white/40">
              Pick a content type, review the prompt, then open it in Creative Studio.
            </SheetDescription>
          </SheetHeader>

          <div className="flex-1 overflow-y-auto space-y-6">
            {liveTrends[0] && (
              <div className="p-4 bg-primary/5 border border-primary/20 rounded-xl space-y-1">
                <div className="text-[9px] font-mono text-primary/60 uppercase tracking-widest">Currently Trending · {liveTrends[0].location}</div>
                <div className="text-2xl font-bebas text-white tracking-wide">{liveTrends[0].keyword}</div>
                <div className="text-xs font-mono text-white/40">{liveTrends[0].niche} · Signal: {liveTrends[0].score}σ</div>
              </div>
            )}

            <div className="space-y-2">
              <p className="text-[10px] font-mono text-white/40 uppercase tracking-widest">What do you want to create?</p>
              <div className="grid grid-cols-3 gap-2">
                {([
                  { key: "carousel", label: "📸 Carousel", hint: "Tips & education" },
                  { key: "reel",     label: "🎬 Reel",     hint: "Reach & discovery" },
                  { key: "story",    label: "✨ Story",    hint: "Promos & offers" },
                ] as const).map(({ key, label, hint }) => (
                  <button
                    key={key}
                    onClick={() => {
                      setDeployContentType(key);
                      const base = liveTrends[0];
                      if (!base) return;
                      const prompts: Record<string, string> = {
                        carousel: `Create a 5-slide carousel post about "${base.keyword}" for ${base.location}. Niche: ${base.niche}. Make each slide educational and easy to share.`,
                        reel:     `Write a short Reel script about "${base.keyword}" for ${base.location}. Niche: ${base.niche}. Hook viewers in the first 3 seconds. Keep it under 30 seconds.`,
                        story:    `Create an Instagram Story for "${base.keyword}" targeting ${base.location}. Niche: ${base.niche}. Include a clear call-to-action and urgency.`,
                      };
                      setDeployPrompt(prompts[key]);
                    }}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      deployContentType === key
                        ? 'border-primary bg-primary/10 text-white'
                        : 'border-white/10 bg-white/[0.02] text-white/50 hover:border-white/20'
                    }`}
                  >
                    <div className="text-sm font-bebas tracking-wide">{label}</div>
                    <div className="text-[9px] font-mono text-white/30 mt-0.5">{hint}</div>
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <p className="text-[10px] font-mono text-white/40 uppercase tracking-widest">AI-suggested prompt (edit freely)</p>
              <textarea
                value={deployPrompt}
                onChange={(e) => setDeployPrompt(e.target.value)}
                rows={5}
                className="w-full bg-white/[0.03] border border-white/10 rounded-xl p-4 text-sm font-mono text-white/80 resize-none focus:outline-none focus:border-primary/50 leading-relaxed"
              />
            </div>
          </div>

          <div className="pt-4 border-t border-white/5 space-y-2 mt-4">
            <Button
              className="w-full bg-primary text-black font-bebas text-lg h-12 rounded-xl hover:opacity-90"
              onClick={() => {
                setDeploySheetOpen(false);
                navigate("/dashboard/creative", { state: { prefillPrompt: deployPrompt } });
              }}
            >
              OPEN IN CREATIVE STUDIO →
            </Button>
            <p className="text-center text-[10px] font-mono text-white/20">You can edit and refine before publishing.</p>
          </div>
        </SheetContent>
      </Sheet>

      {/* Content Suggestions Modal */}
      <ContentSuggestionsModal
        isOpen={contentModalOpen}
        onClose={() => setContentModalOpen(false)}
        suggestions={contentSuggestions}
        isLoading={isGeneratingContent}
      />

      {/* Trend Detail Dialog */}
      <Dialog open={campaignModalOpen} onOpenChange={setCampaignModalOpen}>
        <DialogContent className="bg-slate-950 border border-white/10 text-white max-w-lg rounded-2xl">
          <DialogHeader>
            <DialogTitle className="font-bebas text-2xl tracking-[0.15em] text-primary uppercase">
              {selectedTrend?.keyword ?? "Trend Detail"}
            </DialogTitle>
            <DialogDescription className="text-white/40 font-mono text-xs uppercase tracking-wider">
              {selectedTrend?.lifecycle_stage ?? ""} · {selectedTrend?.location ?? ""}
            </DialogDescription>
          </DialogHeader>

          {selectedTrend && (
            <div className="space-y-4 pt-2">
              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: "SIGNAL SCORE", value: `${selectedTrend.score?.toFixed(1) ?? "—"}σ` },
                  { label: "PROFIT SCORE", value: `${selectedTrend.profit_score ?? "—"}` },
                  { label: "SATURATION", value: `${selectedTrend.saturation_score ?? "—"}%` },
                  { label: "SOCIAL SCORE", value: `${selectedTrend.social_score ?? "—"}` },
                ].map(({ label, value }) => (
                  <div key={label} className="p-3 bg-white/5 border border-white/10 rounded-xl">
                    <p className="text-[9px] font-mono font-black text-white/30 uppercase tracking-wider mb-1">{label}</p>
                    <p className="text-lg font-bebas text-white">{value}</p>
                  </div>
                ))}
              </div>

              {selectedTrend.niche && (
                <div className="p-3 bg-white/5 border border-white/10 rounded-xl">
                  <p className="text-[9px] font-mono font-black text-white/30 uppercase tracking-wider mb-1">NICHE</p>
                  <p className="text-sm font-mono text-white/80">{selectedTrend.niche}</p>
                </div>
              )}

              {(selectedTrend.rising_queries?.length ?? 0) > 0 && (
                <div className="p-3 bg-white/5 border border-white/10 rounded-xl">
                  <p className="text-[9px] font-mono font-black text-white/30 uppercase tracking-wider mb-2">RISING QUERIES</p>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedTrend.rising_queries!.slice(0, 6).map((q, i) => (
                      <span key={i} className="text-[10px] font-mono text-primary bg-primary/10 border border-primary/20 px-2 py-0.5 rounded-full">{q}</span>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex gap-3 pt-2">
                <Button
                  className="flex-1 bg-primary text-black font-bebas text-base h-10 rounded-xl hover:opacity-90"
                  onClick={() => {
                    setCampaignModalOpen(false);
                    const prompt = `Create an Instagram Reel script about "${selectedTrend.keyword}" targeting ${selectedTrend.location}. Niche: ${selectedTrend.niche || user?.business_domain || 'marketing'}. Keep it under 30 seconds with a strong hook and clear call-to-action.`;
                    navigate("/dashboard/creative", { state: { prefillPrompt: prompt } });
                  }}
                >
                  CREATE CONTENT →
                </Button>
                <Button
                  variant="outline"
                  className="border-white/10 text-white/60 font-bebas text-base h-10 rounded-xl hover:bg-white/5"
                  onClick={() => handleAddToWatchlist(selectedTrend.keyword)}
                >
                  + WATCHLIST
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </Layout>
  );
};


export default TrendArbitrage;
