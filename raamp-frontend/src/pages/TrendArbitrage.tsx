import { useState, useEffect, useMemo, useRef } from "react";
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
  Info, Lightbulb, Rocket
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
  ResponsiveContainer, Area, ComposedChart,
  Line
} from 'recharts';

import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";

import { trendService, TrendSpike, GeoTrend, SpikeTimeline, MarketGap, PlatformReach, WatchlistItem } from "@/services/trendService";
import { businessService } from "@/services/businessService";
import { apiClient } from "@/services/api";
import { AIStrategyDrawer } from "@/components/trends/AIStrategyDrawer";
import { IntelligenceGrid } from "@/components/trends/IntelligenceGrid";
import { SignalsCarousel } from "@/components/trends/SignalsCarousel";
import { TrendHistoryTable } from "@/components/trends/TrendHistoryTable";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { LaunchCampaignDialog } from "@/components/LaunchCampaignDialog";
import { UrgencyWidget } from "@/components/trends/UrgencyWidget";

const TrendArbitrage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const userPlatform = (user as any)?.primary_platform || "instagram";
  const [liveTrends, setLiveTrends] = useState<TrendSpike[]>([]);
  const [rawTrends, setRawTrends] = useState<TrendSpike[]>([]);
  const [geoData, setGeoData] = useState<GeoTrend[]>([]);
  const [isRealGeo, setIsRealGeo] = useState<boolean>(true);
  const [timelineData, setTimelineData] = useState<SpikeTimeline[]>([]);
  const [marketGapData, setMarketGapData] = useState<MarketGap[]>([]);
  const [platformReach, setPlatformReach] = useState<PlatformReach | null>(null);
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isScanning, setIsScanning] = useState(false);
  const [scanStep, setScanStep] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [lastSync, setLastSync] = useState<Date>(new Date());
  const [lastSuccessfulScanAt, setLastSuccessfulScanAt] = useState<string | null>(null);
  const [isOffline, setIsOffline] = useState(false);
  const [timelineFetchError, setTimelineFetchError] = useState<string | null>(null);
  const [geoFetchError, setGeoFetchError] = useState<string | null>(null);
  const [lastScanSummary, setLastScanSummary] = useState<{
    niche: string;
    location: string;
    category: string;
    timeframeDays: number;
    trendId?: string;
    completedAt?: number;
  } | null>(null);
  const [deploySheetOpen, setDeploySheetOpen] = useState(false);
  const [deployPrompt, setDeployPrompt] = useState("");
  const [deployContentType, setDeployContentType] = useState<"carousel" | "reel" | "story">("carousel");

  // Filter States
  const [location, setLocation] = useState<string>((user as any)?.business_location || "PK");
  const [searchQuery, setSearchQuery] = useState<string>((user as any)?.business_location || "PK");
  const [category, setCategory] = useState<string>("all");
  const [customKeywordInput, setCustomKeywordInput] = useState<string>("");
  const [customKeywords, setCustomKeywords] = useState<string[]>([]);
  const [useTrendingNow, setUseTrendingNow] = useState<boolean>(true);
  const [hasSpecialties, setHasSpecialties] = useState<boolean>(true);
  const [specialtiesLoading, setSpecialtiesLoading] = useState<boolean>(true);
  const [timeframe, setTimeframe] = useState<string>("30");
  const [lifecycleFilter, setLifecycleFilter] = useState<string>("all");
  const [showAllTrends, setShowAllTrends] = useState(false);
  const [selectedCity, setSelectedCity] = useState<GeoTrend | null>(null);
  const [campaignModalOpen, setCampaignModalOpen] = useState(false);
  const [selectedTrend, setSelectedTrend] = useState<TrendSpike | null>(null);
  const [activeTrend, setActiveTrend] = useState<TrendSpike | null>(null);
  const [gapAnalysisOpen, setGapAnalysisOpen] = useState(false);
  const [launchDialogOpen, setLaunchDialogOpen] = useState(false);
  const [compareTrends, setCompareTrends] = useState<TrendSpike[]>([]);
  const [compareOpen, setCompareOpen] = useState(false);

  // AI Content Suggestions removed (keep Trends page focused on signals + page sections)
  const [qualityBannerDismissed, setQualityBannerDismissed] = useState(false);
  const [brandProfile, setBrandProfile] = useState<any>(null);
  const [businessDetails, setBusinessDetails] = useState<any>(null);
  const [trendHistory, setTrendHistory] = useState<any[]>([]);
  const [execAnalysis, setExecAnalysis] = useState<{
    keyword: string;
    explanation: string;
    why_now: string;
    content_prompt: string;
    fetchedAt: number;
  } | null>(null);
  const [execAnalysisLoading, setExecAnalysisLoading] = useState(false);
  const [execAnalysisError, setExecAnalysisError] = useState<string | null>(null);
  const inflightFetchRef = useRef<AbortController | null>(null);
  const lastAnalyticsHydrateMsRef = useRef<number>(0);
  const [trendingNow, setTrendingNow] = useState<string[]>([]);
  const [trendingNowRelevant, setTrendingNowRelevant] = useState<{ term: string; score: number; matched_terms: string[] }[]>([]);
  const [trendingNowLoading, setTrendingNowLoading] = useState(false);
  const [industryTerms, setIndustryTerms] = useState<string[]>([]);
  const [industryGlobalNotes, setIndustryGlobalNotes] = useState<string | null>(null);
  const [industryLoading, setIndustryLoading] = useState(false);
  const [brandAlignedTerms, setBrandAlignedTerms] = useState<{ term: string; score: number; matched: string[] }[]>([]);

  // New AI Analysis State (Trend AI Analysis System)
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [activeDrawerTrend, setActiveDrawerTrend] = useState<string | null>(null);
  const [aiAnalysisStatus, setAiAnalysisStatus] = useState<"pending" | "ready" | "failed" | null>(null);
  const [aiAnalysisData, setAiAnalysisData] = useState<any>(null);
  const [aiPolling, setAiPolling] = useState(false);
  const aiKickoffRef = useRef<Set<string>>(new Set());
  const [topTrendExpanded, setTopTrendExpanded] = useState(false);

  const topTrend = useMemo(() => liveTrends?.[0] || null, [liveTrends]);
  const effectiveTrend = activeTrend || topTrend;

  const aiNextStep = useMemo(() => {
    const kw = String(effectiveTrend?.keyword || "").trim();
    const pkTop = String(trendingNowRelevant?.[0]?.term || trendingNow?.[0] || "").trim();
    const nicheTop = String(industryTerms?.[0] || "").trim();
    if (!kw) return "Run a scan to surface your top opportunity. AI analysis will appear automatically.";

    const platform = String(userPlatform || "instagram").toLowerCase();
    const fmt = platform === "instagram" ? "Reel" : platform === "facebook" ? "short video" : "post";
    const hook = pkTop ? `Hook it to what’s hot in PK (“${pkTop}”)` : "Lead with a fast, curiosity-driven hook";
    const angle = nicheTop ? `and position it within your niche (“${nicheTop}”).` : "and tie it tightly to your niche.";

    return `Next: publish a ${fmt} about “${kw}”. ${hook} ${angle}`;
  }, [effectiveTrend, trendingNowRelevant, trendingNow, industryTerms, userPlatform]);

  const toggleCompare = (trend: TrendSpike) => {
    setCompareTrends((prev) => {
      const key = String(trend?.keyword || "").toLowerCase();
      const exists = prev.some((t) => String(t?.keyword || "").toLowerCase() === key);
      if (exists) return prev.filter((t) => String(t?.keyword || "").toLowerCase() !== key);
      const next = [...prev, trend];
      return next.slice(0, 3);
    });
  };

  // Synchronize effectiveTrend with AI analysis auto-fetch
  useEffect(() => {
    const tid =
      (effectiveTrend as any)?.trend_signal_id ||
      (lastScanSummary as any)?.trendId ||
      (effectiveTrend as any)?.id;
    if (tid && tid !== activeDrawerTrend) {
      setActiveDrawerTrend(String(tid));
      setAiAnalysisStatus("pending");
      trendService.getAIAnalysis(String(tid)).then(doc => {
        setAiAnalysisData(doc);
        const st = (doc as any)?.status;
        setAiAnalysisStatus(st === "completed" ? "ready" : (st === "failed" ? "failed" : "pending"));
      }).catch(async () => {
        // If analysis doc doesn't exist yet, kick off generation once, then polling will pick it up.
        const key = String(tid);
        if (!aiKickoffRef.current.has(key)) {
          aiKickoffRef.current.add(key);
          try {
            await trendService.regenerateAIAnalysis(key);
          } catch {
            // ignore: polling + UI will handle empty/unavailable states
          }
        }
      });
    }
  }, [effectiveTrend, activeDrawerTrend, lastScanSummary]);

  // Poll AI analysis while pending
  useEffect(() => {
    if (!activeDrawerTrend) return;
    if (aiAnalysisStatus !== "pending") return;
    if (aiPolling) return;
    let cancelled = false;
    setAiPolling(true);
    const timer = setInterval(async () => {
      try {
        const doc = await trendService.getAIAnalysis(activeDrawerTrend);
        if (cancelled) return;
        setAiAnalysisData(doc);
        const st = (doc as any)?.status;
        if (st === "completed") setAiAnalysisStatus("ready");
        else if (st === "failed") setAiAnalysisStatus("failed");
      } catch {
        // keep polling until server has it
      }
    }, 3000);
    return () => {
      cancelled = true;
      clearInterval(timer);
      setAiPolling(false);
    };
  }, [activeDrawerTrend, aiAnalysisStatus, aiPolling]);

  // Debounce location search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchQuery !== location) {
        setLocation(searchQuery);
      }
    }, 1000);
    return () => clearTimeout(timer);
  }, [searchQuery, location]);

  useEffect(() => {
    let cancelled = false;
    const loadSpecialties = async () => {
      try {
        setSpecialtiesLoading(true);
        const res = await trendService.getBusinessSpecialties();
        const list = Array.isArray(res?.specialties) ? res.specialties : [];
        const cleaned = list.map((s) => (s || "").trim()).filter(Boolean);
        if (!cancelled) setHasSpecialties(cleaned.length > 0);
      } catch (e: any) {
        // If endpoint fails, don't hard-block scanning; backend will enforce.
        if (!cancelled) setHasSpecialties(true);
      } finally {
        if (!cancelled) setSpecialtiesLoading(false);
      }
    };
    loadSpecialties();

    const fetchGlobalData = async () => {
      try {
        const [brand, business] = await Promise.all([
          businessService.getBrandAlignment(),
          // This endpoint was removed/never existed in backend; use hyperlocal setup as best-effort business context.
          businessService.getHyperlocalSetup().catch(() => null),
        ]);
        setBrandProfile(brand);
        setBusinessDetails(business);
      } catch (err) {
        console.error("Failed to fetch brand/business profile", err);
      }
    };
    fetchGlobalData();

    return () => {
      cancelled = true;
    };
  }, []);

  const showQualityBanner = useMemo(() => {
    if (qualityBannerDismissed) return false;
    return liveTrends.some((t) => {
      const isSimulated = t.is_simulated === true;
      const rateLimited = (t.error_message || "").toLowerCase().includes("rate_limited");
      return isSimulated || rateLimited;
    });
  }, [liveTrends, qualityBannerDismissed]);

  const snapshotKey = useMemo(() => {
    const tf = String(timeframe || "30").trim();
    const loc = String(location || "GLOBAL").trim().toUpperCase();
    return `trend_arbitrage_snapshot:v1:${loc}:${tf}`;
  }, [location, timeframe]);

  const execAnalysisKey = useMemo(() => {
    const loc = String(location || "GLOBAL").trim().toUpperCase();
    return `trend_arbitrage_exec_analysis:v1:${loc}`;
  }, [location]);

  const saveSnapshot = (partial?: Partial<{
    liveTrends: TrendSpike[];
    geoData: GeoTrend[];
    isRealGeo: boolean;
    timelineData: SpikeTimeline[];
    marketGapData: MarketGap[];
    platformReach: PlatformReach | null;
    watchlist: WatchlistItem[];
    trendHistory: any[];
    lastSuccessfulScanAt: string | null;
    lastSyncMs: number;
  }>) => {
    try {
      const payload = {
        liveTrends,
        geoData,
        isRealGeo,
        timelineData,
        marketGapData,
        platformReach,
        watchlist,
        trendHistory,
        lastSuccessfulScanAt,
        lastSyncMs: Date.now(),
        ...(partial || {}),
      };
      localStorage.setItem(snapshotKey, JSON.stringify(payload));
    } catch {
      // best-effort cache only
    }
  };

  const loadSnapshot = () => {
    try {
      const raw = localStorage.getItem(snapshotKey);
      if (!raw) return false;
      const parsed = JSON.parse(raw);
      if (parsed?.liveTrends && Array.isArray(parsed.liveTrends)) setLiveTrends(parsed.liveTrends);
      if (parsed?.geoData && Array.isArray(parsed.geoData)) setGeoData(parsed.geoData);
      if (typeof parsed?.isRealGeo === "boolean") setIsRealGeo(parsed.isRealGeo);
      if (parsed?.timelineData && Array.isArray(parsed.timelineData)) setTimelineData(parsed.timelineData);
      if (parsed?.marketGapData && Array.isArray(parsed.marketGapData)) setMarketGapData(parsed.marketGapData);
      if (parsed?.platformReach !== undefined) setPlatformReach(parsed.platformReach);
      if (parsed?.watchlist && Array.isArray(parsed.watchlist)) setWatchlist(parsed.watchlist);
      if (parsed?.trendHistory && Array.isArray(parsed.trendHistory)) setTrendHistory(parsed.trendHistory);
      if (parsed?.lastSuccessfulScanAt !== undefined) setLastSuccessfulScanAt(parsed.lastSuccessfulScanAt ?? null);
      if (parsed?.lastSyncMs) setLastSync(new Date(Number(parsed.lastSyncMs)));
      return true;
    } catch {
      return false;
    }
  };

  const persistLocalStrategyHistory = (entry: {
    keyword: string;
    location: string;
    niche?: string;
    prompt: string;
    recommendations?: any;
    viral_audio?: any[];
    executive_analysis?: any;
    createdAt: number;
  }) => {
    try {
      const k = `trend_arbitrage_strategy_history:v1`;
      const raw = localStorage.getItem(k);
      const list = raw ? JSON.parse(raw) : [];
      const arr = Array.isArray(list) ? list : [];
      arr.unshift(entry);
      // dedupe by keyword+location and cap
      const seen = new Set<string>();
      const deduped = arr.filter((x: any) => {
        const kk = `${String(x?.keyword || "").toLowerCase()}|${String(x?.location || "").toUpperCase()}`;
        if (!kk || seen.has(kk)) return false;
        seen.add(kk);
        return true;
      });
      localStorage.setItem(k, JSON.stringify(deduped.slice(0, 50)));
    } catch {
      // ignore
    }
  };

  const buildDeployPrompt = (params: {
    keyword: string;
    niche?: string;
    trendLocation?: string;
    recommendations?: any;
    viralAudio?: any[];
    executiveAnalysis?: { explanation?: string; why_now?: string; content_prompt?: string } | null;
  }) => {
    const kw = params.keyword;
    const loc = params.trendLocation || location || "GLOBAL";
    const niche = params.niche || (user as any)?.business_domain_name || user?.business_domain || "general";
    const rec = params.recommendations || null;
    const audio = Array.isArray(params.viralAudio) ? params.viralAudio : [];
    const ea = params.executiveAnalysis || null;

    const ideas = (rec?.actionable_recommendations?.content_ideas || rec?.content_ideas || [])
      .slice?.(0, 3)
      ?.map?.((x: any) => (typeof x === "string" ? x : (x?.idea || x?.title || "")))
      .filter(Boolean);

    const hashtags = (rec?.actionable_recommendations?.hashtags || rec?.hashtags || [])
      .slice?.(0, 10)
      ?.map?.((h: any) => String(h || "").replace(/[#\s]+/g, ""))
      .filter(Boolean);

    const audioLines = audio.slice(0, 2).map((t: any) => {
      const name = t?.track_name || t?.name || "Unknown track";
      const artist = t?.artist || t?.artistName || "Unknown artist";
      const url = t?.url ? ` (${t.url})` : "";
      return `- ${name} — ${artist}${url}`;
    });

    return [
      `You are a marketing content AI assistant.`,
      ``,
      `Trend detected: "${kw}"`,
      `Location: ${loc}`,
      `Niche: ${niche}`,
      ``,
      ea?.explanation ? `Executive analysis: ${ea.explanation}` : null,
      ea?.why_now ? `Why act now: ${ea.why_now}` : null,
      ``,
      ideas?.length ? `Top content ideas:\n${ideas.map((x: string) => `- ${x}`).join("\n")}` : null,
      hashtags?.length ? `Suggested hashtags: ${hashtags.map((h: string) => `#${h}`).join(" ")}` : null,
      ``,
      audioLines.length ? `Audio candidates (verified feed):\n${audioLines.join("\n")}` : `Audio candidates: none available (use voiceover + on-screen captions).`,
      ``,
      ea?.content_prompt ? `Ready-to-use prompt:\n${ea.content_prompt}` : `Create 3 content ideas (Reel/Carousel/Story) that leverage "${kw}" in ${loc} for a ${niche} business. Include hooks, CTAs, and a posting plan for the next 48 hours.`,
      ``,
      `Return a concise, execution-ready plan.`,
    ]
      .filter((x) => typeof x === "string" && x.trim().length > 0)
      .join("\n");
  };

  const fetchExecutiveAnalysis = async (trend: TrendSpike | null) => {
    const kw = (trend?.keyword || "").trim();
    if (!kw) return;
    setExecAnalysisError(null);

    // local cache: per-location, per-keyword
    try {
      const raw = localStorage.getItem(execAnalysisKey);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed?.keyword?.toLowerCase?.() === kw.toLowerCase() && parsed?.explanation) {
          setExecAnalysis(parsed);
          // still refresh in background if stale
          if (Date.now() - Number(parsed?.fetchedAt || 0) < 10 * 60 * 1000) return;
        }
      }
    } catch {
      // ignore
    }

    setExecAnalysisLoading(true);
    try {
      const niche = (trend?.niche || (user as any)?.business_domain_name || user?.business_domain || "general").toString();
      const lifecycle_stage = (trend as any)?.lifecycle_stage || undefined;
      const breakout_probability = (trend as any)?.breakout_probability ?? undefined;
      const profit_score = (trend as any)?.profit_score ?? undefined;
      const competition = (trend as any)?.saturation_score ?? undefined;
      const buzz = (trend as any)?.social_score ?? undefined;

      const res = await trendService.getTrendExplanation({
        keyword: kw,
        niche,
        location: trend?.location || location || "GLOBAL",
        lifecycle_stage,
        breakout_probability,
        profit_score,
        competition,
        buzz,
      } as any);

      const payload = {
        keyword: kw,
        explanation: String((res as any)?.explanation || ""),
        why_now: String((res as any)?.why_now || ""),
        content_prompt: String((res as any)?.content_prompt || ""),
        fetchedAt: Date.now(),
      };
      setExecAnalysis(payload);
      try {
        localStorage.setItem(execAnalysisKey, JSON.stringify(payload));
      } catch {
        // ignore
      }
    } catch (e: any) {
      setExecAnalysisError(e?.message || "Failed to generate executive analysis.");
    } finally {
      setExecAnalysisLoading(false);
    }
  };

  const handleMagicBridge = async (keyword: string) => {
    try {
      const match =
        liveTrends.find((t) => (t.keyword || "").toLowerCase() === (keyword || "").toLowerCase()) ||
        (selectedTrend && (selectedTrend.keyword || "").toLowerCase() === (keyword || "").toLowerCase() ? selectedTrend : null);

      // Ensure executive analysis is available (best-effort, non-blocking)
      if (!execAnalysis || execAnalysis.keyword.toLowerCase() !== (keyword || "").toLowerCase()) {
        fetchExecutiveAnalysis(match || { keyword, niche: "", location: location, id: "", score: 0, impact: "", current_value: 0, detected_at: "" } as any).catch(() => {});
      }

      const richPrompt = buildDeployPrompt({
        keyword,
        niche: match?.niche,
        trendLocation: match?.location,
        recommendations: (match as any)?.recommendations,
        viralAudio: (match as any)?.recommendations?.viral_audio || (match as any)?.viral_audio,
        executiveAnalysis: execAnalysis && execAnalysis.keyword.toLowerCase() === (keyword || "").toLowerCase() ? execAnalysis : null,
      });

      // Persist local strategy history (frontend-only; does not change backend contracts)
      persistLocalStrategyHistory({
        keyword,
        location: (match?.location || location || "GLOBAL").toString(),
        niche: match?.niche,
        prompt: richPrompt,
        recommendations: (match as any)?.recommendations,
        viral_audio: (match as any)?.recommendations?.viral_audio,
        executive_analysis: execAnalysis,
        createdAt: Date.now(),
      });

      // ASYNC LOGGING (Don't block navigation) - backend persistence
      trendService.logTrendActivity({
        trend_keyword: keyword,
        trend_source: "Hyperlocal Scanner",
        generated_prompt: richPrompt,
        niche: match?.niche || (user as any)?.business_domain_name || user?.business_domain || "general",
        location: match?.location || location
      }).catch(e => console.error("History logging failed", e));

      navigate("/dashboard/creative", { state: { prefillPrompt: richPrompt } });
      toast.success("Ready to create assets!", {
        description: `Automatically pasted the best AI strategy for "${keyword}"`
      });
    } catch (err: any) {
      console.error("Magic Bridge failed", err);
      toast.error("Magic Bridge Failed", { description: "Please try again" });
    }
  };

  const selectedRecs = useMemo(() => {
    const rec = (selectedTrend as any)?.recommendations;
    if (!rec || typeof rec !== "object") return null;
    return rec as any;
  }, [selectedTrend]);

  // Ensure we always have a "selected" trend so Actionable Strategy can render for the top signal.
  useEffect(() => {
    if (!selectedTrend && liveTrends.length > 0) {
      setSelectedTrend(liveTrends[0]);
    }
    // If selected keyword disappears from feed, snap back to top signal.
    if (selectedTrend && liveTrends.length > 0) {
      const stillThere = liveTrends.some((t) => (t?.keyword || "").toLowerCase() === (selectedTrend?.keyword || "").toLowerCase());
      if (!stillThere) setSelectedTrend(liveTrends[0]);
    }
  }, [liveTrends, selectedTrend]);

  // Ensure we always have an "active" trend for the right-side intelligence surfaces.
  useEffect(() => {
    if (!activeTrend && topTrend) setActiveTrend(topTrend);
    if (activeTrend && liveTrends.length > 0) {
      const stillThere = liveTrends.some((t) => (t?.keyword || "").toLowerCase() === (activeTrend?.keyword || "").toLowerCase());
      if (!stillThere) setActiveTrend(liveTrends[0] || null);
    }
  }, [activeTrend, topTrend, liveTrends]);

  // Real data only - staged loading (fast first paint, then hydrate analytics)
  const fetchCoreData = async () => {
    // cancel previous inflight background refresh when filters change
    try {
      inflightFetchRef.current?.abort?.();
    } catch {}
    const controller = new AbortController();
    inflightFetchRef.current = controller;

    setTimelineFetchError(null);
    setGeoFetchError(null);

    // Phase 0: show cached snapshot immediately (if available)
    const hadCache = loadSnapshot();
    if (hadCache) {
      setIsLoading(false);
    } else {
      setIsLoading(true);
    }

    const withTimeout = async <T,>(p: Promise<T>, ms: number): Promise<T> => {
      return await Promise.race([
        p,
        new Promise<T>((_, reject) => setTimeout(() => reject(new Error("timeout")), ms)),
      ]);
    };

    // Phase 1: fetch ONLY live trends first (fastest visible win)
    try {
      // Give live trends a strict budget so UI doesn't "hang" behind non-critical calls.
      // If backend is slow, cached snapshot (if any) remains visible and user can retry.
      const [businessLive, rawLive] = await withTimeout(
        Promise.all([
          trendService.getLiveTrends(location, "business"),
          trendService.getLiveTrends(location, "raw"),
        ]),
        12000
      );
      const live = businessLive;
      setLiveTrends(live || []);
      setRawTrends(rawLive || []);
      setError(null);
      setIsOffline(false);
      setLastSync(new Date());
      saveSnapshot({ liveTrends: live || [], lastSyncMs: Date.now() });

      // Fetch executive analysis for featured trend (main screen requirement)
      const featured = (live || [])[0] || null;
      if (featured) {
        fetchExecutiveAnalysis(featured).catch(() => {});
      }
    } catch (err: any) {
      console.error("Failed to fetch core trend data", err);
      if (!hadCache) {
        setError("Unable to reach the signal network. Please check your connection.");
        setIsOffline(true);
      }
    } finally {
      setIsLoading(false);
    }

    // Phase 1b: fetch watchlist + history after trends are visible (background)
    // This avoids delaying initial feed render and keeps perceived load under 2s.
    try {
      const [saved, history] = await Promise.allSettled([
        trendService.getWatchlist(),
        trendService.getTrendHistory(20),
      ]).then((results) => {
        const w = results[0].status === "fulfilled" ? results[0].value : [];
        const h = results[1].status === "fulfilled" ? results[1].value : [];
        return [w, h] as const;
      });
      setWatchlist(saved || []);
      console.log("[TrendArbitrage] trend history:", history);
      setTrendHistory(history || []);
      saveSnapshot({ watchlist: saved || [], trendHistory: history || [], lastSyncMs: Date.now() });
    } catch {
      // non-fatal
    }

    // Phase 2: hydrate analytics in background (avoid blocking first paint)
    const hydrate = async () => {
      try {
        const settled = await Promise.allSettled([
          trendService.getGeoHeatmap(location),
          trendService.getSpikeTimeline(parseInt(timeframe), location),
          trendService.getMarketGapData(location),
          trendService.getPlatformReach(location),
        ]);

        const geoResp = settled[0].status === "fulfilled" ? settled[0].value : { regions: [], count: 0, is_real_geo: false };
        const geo = (geoResp as any)?.regions ?? [];
        const spikeTimeline = settled[1].status === "fulfilled" ? settled[1].value : { timeline: [], lastSuccessfulScanAt: null };
        const gap = settled[2].status === "fulfilled" ? settled[2].value : [];
        const reach = settled[3].status === "fulfilled" ? settled[3].value : { google: 0, instagram: 0, facebook: 0, total_reach: "0%" };

        if (settled[0].status === "rejected") setGeoFetchError("Unavailable");
        if (settled[1].status === "rejected") setTimelineFetchError("Unavailable");

        setGeoData(geo || []);
        setIsRealGeo(Boolean((geoResp as any)?.is_real_geo));
        setTimelineData(Array.isArray((spikeTimeline as any)?.timeline) ? (spikeTimeline as any).timeline : []);
        setLastSuccessfulScanAt((spikeTimeline as any)?.lastSuccessfulScanAt ?? null);
        setMarketGapData(gap || []);
        setPlatformReach(reach || null);

        saveSnapshot({
          geoData: geo || [],
          isRealGeo: Boolean((geoResp as any)?.is_real_geo),
          timelineData: Array.isArray((spikeTimeline as any)?.timeline) ? (spikeTimeline as any).timeline : [],
          lastSuccessfulScanAt: (spikeTimeline as any)?.lastSuccessfulScanAt ?? null,
          marketGapData: gap || [],
          platformReach: reach || null,
          lastSyncMs: Date.now(),
        });
      } catch (e: any) {
        // non-fatal; keep cached analytics
      }
    };

    // Do NOT hydrate analytics on every refresh tick.
    // Hydrate on first load, on filter changes (handled by useEffect), and then at a low frequency.
    const now = Date.now();
    const shouldHydrate = lastAnalyticsHydrateMsRef.current === 0 || (now - lastAnalyticsHydrateMsRef.current) > 5 * 60 * 1000;
    if (shouldHydrate) {
      lastAnalyticsHydrateMsRef.current = now;
      try {
        const ric = (window as any).requestIdleCallback;
        if (typeof ric === "function") {
          ric(() => hydrate(), { timeout: 1500 });
        } else {
          setTimeout(hydrate, 250);
        }
      } catch {
        setTimeout(hydrate, 250);
      }
    }
  };

  const fetchTrendingNow = async () => {
    setTrendingNowLoading(true);
    try {
      // Regional tab: always show what's trending in PK
      const resp = await trendService.getTrendingNow("PK", category || "all", 12);
      setTrendingNow(resp?.terms || []);
      setTrendingNowRelevant(resp?.relevant || []);
    } catch {
      setTrendingNow([]);
      setTrendingNowRelevant([]);
    } finally {
      setTrendingNowLoading(false);
    }
  };

  const deriveBusinessNiche = () => {
    const fromUser = ((user as any)?.business_domain_name || user?.business_domain || "").toString().trim();
    const fromBusiness = (businessDetails?.niche || businessDetails?.business_type || "").toString().trim();
    return fromUser || fromBusiness || "fashion";
  };

  const fetchIndustryTrending = async () => {
    setIndustryLoading(true);
    try {
      const niche = deriveBusinessNiche();
      const withTimeout = async <T,>(p: Promise<T>, ms: number): Promise<T> => {
        return await Promise.race([
          p,
          new Promise<T>((_, reject) => setTimeout(() => reject(new Error("timeout")), ms)),
        ]);
      };
      const globalResp = await withTimeout(trendService.getIndustryTrends(niche, "GLOBAL", "7d", 12), 12000);
      const gTerms =
        (Array.isArray((globalResp as any)?.terms) && (globalResp as any).terms.length ? (globalResp as any).terms : null) ||
        (Array.isArray((globalResp as any)?.seed_keywords) ? (globalResp as any).seed_keywords : []);
      setIndustryTerms(gTerms);
      setIndustryGlobalNotes((globalResp as any)?.data_quality?.notes ?? null);
    } catch {
      setIndustryTerms([]);
      setIndustryGlobalNotes("Failed to load global industry trends.");
    } finally {
      setIndustryLoading(false);
    }
  };

  const recomputeBrandAligned = () => {
    // Token-overlap scoring against brand profile + niche + specialties.
    const niche = deriveBusinessNiche();
    const specialties = Array.isArray((businessDetails as any)?.specialties) ? (businessDetails as any).specialties : [];
    const brandBits = [
      brandProfile?.tagline,
      brandProfile?.tone_of_voice,
      brandProfile?.restaurant_theme,
      (businessDetails as any)?.business_type,
      niche,
      ...(Array.isArray(specialties) ? specialties : []),
    ]
      .map((x: any) => String(x || "").trim())
      .filter(Boolean)
      .join(" ");

    const STOP = new Set(["vs", "v", "and", "or", "the", "a", "an", "in", "of", "for", "to", "with", "on", "at", "by", "from", "today", "now", "live", "pakistan"]);
    const tokenize = (s: string): string[] => {
      const raw = (s || "").toLowerCase().match(/[a-z0-9]+/g) || [];
      return raw.filter((t) => t.length >= 3 && !STOP.has(t));
    };

    const brandTokens = new Set(tokenize(brandBits));
    const pool = Array.from(
      new Set([
        ...(industryTerms || []),
        ...(trendingNow || []),
        ...(rawTrends || []).map((t) => t.keyword),
      ])
    )
      .map((t) => String(t || "").trim())
      .filter(Boolean);

    if (!brandTokens.size || pool.length === 0) {
      setBrandAlignedTerms([]);
      return;
    }

    const scored = pool
      .map((term) => {
        const toks = new Set(tokenize(term));
        const overlap = Array.from(toks).filter((t) => brandTokens.has(t));
        const score = overlap.length / Math.max(1, toks.size);
        return { term, score, matched: overlap.slice(0, 6) };
      })
      .filter((x) => x.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, 8);

    setBrandAlignedTerms(scored);
  };

  const handlePageRefresh = async () => {
    await Promise.allSettled([fetchCoreData(), fetchTrendingNow(), fetchIndustryTrending()]);
  };

  const loadLastVerifiedLiveTrends = (): TrendSpike[] | null => {
    try {
      const k = `trend_arbitrage_verified_live:v1:${String(location || "GLOBAL").toUpperCase()}`;
      const raw = localStorage.getItem(k);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed?.trends) ? (parsed.trends as TrendSpike[]) : null;
    } catch {
      return null;
    }
  };

  const saveLastVerifiedLiveTrends = (trends: TrendSpike[]) => {
    try {
      const k = `trend_arbitrage_verified_live:v1:${String(location || "GLOBAL").toUpperCase()}`;
      localStorage.setItem(k, JSON.stringify({ trends: trends.slice(0, 50), savedAt: Date.now() }));
    } catch {
      // ignore
    }
  };

  const isTrendRealEnough = (t: TrendSpike) => {
    // "Real" here means: not simulated + not failed + not rate-limited marker.
    // We intentionally do not require IG connection; we only avoid clearly simulated placeholders.
    const simulated = t.is_simulated === true;
    const failed = String(t.fetch_status || "").toLowerCase() === "failed";
    const rateLimited = (t.error_message || "").toLowerCase().includes("rate_limited");
    return !simulated && !failed && !rateLimited;
  };

  const fetchLiveOnly = async () => {
    const withTimeout = async <T,>(p: Promise<T>, ms: number): Promise<T> => {
      return await Promise.race([
        p,
        new Promise<T>((_, reject) => setTimeout(() => reject(new Error("timeout")), ms)),
      ]);
    };

    try {
      const [businessLive, rawLive] = await withTimeout(
        Promise.all([
          trendService.getLiveTrends(location, "business"),
          trendService.getLiveTrends(location, "raw"),
        ]),
        12000
      );
      const live = businessLive;
      const real = (live || []).filter(isTrendRealEnough);

      if (real.length > 0) {
        setLiveTrends(live || []);
        setRawTrends(rawLive || []);
        setError(null);
        setIsOffline(false);
        setLastSync(new Date());
        saveSnapshot({ liveTrends: live || [], lastSyncMs: Date.now() });
        saveLastVerifiedLiveTrends(real);
        return;
      }

      // If backend returns simulated/limited data, keep showing last verified real trends.
      const fallback = loadLastVerifiedLiveTrends();
      if (fallback && fallback.length > 0) {
        setLiveTrends(fallback);
        setError("Real-time providers are temporarily rate-limited. Showing last verified real trends.");
        setIsOffline(true);
        setLastSync(new Date());
        return;
      }

      // No fallback available; show what we got (still visible, but flagged)
      setLiveTrends(live || []);
      setRawTrends(rawLive || []);
      setError("Real-time providers are temporarily rate-limited. Some trends may be estimated.");
      setIsOffline(true);
      setLastSync(new Date());
      saveSnapshot({ liveTrends: live || [], lastSyncMs: Date.now() });
    } catch (e: any) {
      // If live refresh fails, keep existing UI; don't nuke feed.
      setError((prev) => prev || "Unable to refresh live trends right now.");
    }
  };


  useEffect(() => {
    fetchCoreData();
    fetchTrendingNow();
    fetchIndustryTrending();
    // Refresh ONLY the live feed frequently (perceived “live”).
    const liveInterval = setInterval(fetchLiveOnly, 30000);
    // Refresh analytics rarely (low perceived value, high cost).
    const analyticsInterval = setInterval(() => {
      // Force next core fetch to include a hydrate (every 10 minutes)
      lastAnalyticsHydrateMsRef.current = 0;
      fetchCoreData();
    }, 10 * 60 * 1000);
    return () => {
      try {
        inflightFetchRef.current?.abort?.();
      } catch {}
      clearInterval(liveInterval);
      clearInterval(analyticsInterval);
    };
  }, [location, timeframe]);

  useEffect(() => {
    recomputeBrandAligned();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [brandProfile, businessDetails, industryTerms, trendingNow, rawTrends]);

  const addCustomKeyword = (raw: string) => {
    const trimmed = (raw || "").trim().toLowerCase();
    if (!trimmed) return;
    if (trimmed.length > 60) return;
    setCustomKeywords((prev) => {
      const set = new Set(prev.map((k) => (k || "").trim().toLowerCase()).filter(Boolean));
      set.add(trimmed);
      return Array.from(set).slice(0, 20);
    });
  };

  const removeCustomKeyword = (kw: string) => {
    const t = (kw || "").trim().toLowerCase();
    setCustomKeywords((prev) => prev.filter((k) => (k || "").trim().toLowerCase() !== t));
  };

  const handleTriggerScan = async () => {
    if (isScanning) return;
    setIsScanning(true);

    try {
      setScanStep("Global Node Sync Initialized...");
      const niche = (user as any)?.business_domain_name || user?.business_domain || "marketing";
      const timeframeDays = parseInt(timeframe);
      console.log(`🚀 SCAN INITIATED for niche: ${niche}, location: ${location}`);
      toast.info("Vector Scan Initiated", {
        description: `Establishing connection to global signal nodes for ${location}...`
      });

      const cleanedCustom = Array.from(
        new Set(
          (customKeywords || [])
            .map((k) => (k || "").trim().toLowerCase())
            .filter(Boolean)
        )
      ).slice(0, 20);

      const response = await trendService.triggerFetch(niche, category, `${timeframeDays}d`, {
        discovery_mode: useTrendingNow,
        custom_keywords: cleanedCustom,
      });
      const trendId = response.trend_id;
      console.log(`✅ Scan registered on backend. TrendID: ${trendId}`);
      setLastScanSummary({ niche, location, category, timeframeDays, trendId });

      // Poll for completion
      let attempts = 0;
      const maxAttempts = 20;

      const poll = async () => {
        if (attempts >= maxAttempts) {
          toast.warning("Scan taking longer than expected", {
            description:
              "PyTrends may be rate limited. Results will appear when the scan completes.",
            duration: 6000,
          });
          setIsScanning(false);
          setScanStep("");
          fetchCoreData();
          return;
        }

        try {
          const statusRes = await trendService.getTrendStatus(trendId);
          console.log(`🔍 Scan Status [Attempt ${attempts}]:`, statusRes.status);

          // Show real-time progress step from backend
          if (statusRes.progress_step) {
            setScanStep(statusRes.progress_step);
          }

          if (statusRes.status === 'completed') {
            setScanStep("Vector Grid Acquired.");
            toast.success("Scan completed", {
              description: `Niche: ${niche} • Category: ${category || "all"} • Window: ${timeframeDays}d`
            });
            const after = await fetchCoreData();
            setLastScanSummary((prev) =>
              prev
                ? { ...prev, completedAt: Date.now() }
                : { niche, location, category, timeframeDays, trendId, completedAt: Date.now() }
            );
            // Fast Current Trends mode does not compute spikes/time-series.
            // The UI should show the latest current trends from the live feed + latest scan keywords.
            setIsScanning(false);
            setScanStep("");
          } else if (statusRes.status === 'failed') {
            const raw = (statusRes.error_message || "Unknown signal processing failure.").toString();
            const friendly =
              raw.includes("serpapi_no_timeline_data") || raw.includes("serpapi_empty_timeline")
                ? "No usable Google Trends timeline for these keywords. Try Trending Now ON, or add broader keywords."
                : raw;
            setError(`SCAN ERROR: ${friendly}`);
            toast.error("Scan Failed", { description: friendly });
            setIsScanning(false);
            setScanStep("");
          } else {
            attempts++;
            setTimeout(poll, 3000);
          }
        } catch (e: any) {
          console.error("Polling error", e);
          setIsScanning(false);
          setScanStep("");
          toast.error("Scan Interrupted", {
            description: e?.status === 429 
              ? `Cooldown active. Please wait ${e?.detail?.match(/\d+/)?.[0] || '60'}s.`
              : "Lost contact with scanning node. Check your internet."
          });
        }
      };

      // Start polling
      setTimeout(poll, 3000);

    } catch (err: any) {
      console.error("Scan initiation error:", err);
      
      const status = err?.response?.status;
      const detail = err?.response?.data?.detail;

      if (status === 412 && typeof detail === "string") {
        toast.warning("Action required before scanning", {
          description: detail,
          duration: 7000,
        });
        if (detail.toLowerCase().includes("specialt")) {
          navigate("/settings/business-specialties");
        }
      } else if (status === 400 && typeof detail === "string" && detail.includes("Location not configured")) {
        toast.error("Location Not Configured", {
          description: "Please complete onboarding or set your business location in settings before scanning trends.",
          duration: 5000,
        });
      } else {
        const errorMessage = detail || err.message || "Unable to initiate scan";
        toast.error("Scan Launch Failed", {
          description: errorMessage,
          duration: 4000,
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
        niche: (user as any)?.business_domain_name || user?.business_domain || 'marketing',
        location: location
      });
      toast.success("Watchlist Updated", { description: `${keyword} is now being tracked.` });
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

  const handleToggleWatchlist = async (keyword: string) => {
    const isWatchlisted = watchlist.some(item => item.keyword.toLowerCase() === keyword.toLowerCase());
    if (isWatchlisted) {
      await handleRemoveFromWatchlist(keyword);
    } else {
      await handleAddToWatchlist(keyword);
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
  }, [marketGapData, liveTrends, user, location]);

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
      <div className="space-y-0 pb-24 pt-6 overflow-x-hidden bg-background relative">
        <div className="absolute top-0 left-1/4 w-1/2 h-1/2 bg-primary/5 blur-[160px] rounded-full pointer-events-none -z-10" />

        <div className="space-y-0">

          {/* Ticker strip */}
          <div className="w-full overflow-hidden bg-foreground/5 border-y border-border py-1 backdrop-blur-md sticky top-0 z-50">
            <motion.div
              className="flex gap-12 whitespace-nowrap cursor-pointer hover:pause"
              animate={{ x: [0, -3000] }}
              transition={{ repeat: Infinity, duration: 80, ease: "linear" }}
              onHoverStart={() => { }} // Could dispatch a pause action
            >
              {[...tickerItems, ...tickerItems, ...tickerItems].map((item, i) => {
                // Use a more unique key combining index and item content
                const uniqueKey = `ticker-${i}-${item.substring(0, 10)}`;
                return (
                  <div
                    key={uniqueKey}
                    onClick={() => {
                      const match = liveTrends.find(t =>
                        item.toUpperCase().startsWith(t.keyword.toUpperCase())
                      );
                      if (match) {
                        setSelectedTrend(match);
                        setActiveTrend(match);
                        setCampaignModalOpen(true);
                      }
                    }}
                    className="flex items-center gap-2 text-[11px] font-mono font-bold tracking-tight text-muted-foreground/80 dark:text-muted-foreground/60 hover:text-primary transition-colors hover:scale-105 transform duration-200"
                  >
                    <div className="w-1 h-1 rounded-full bg-primary animate-pulse" />
                    {item}
                  </div>
                );
              })}
            </motion.div>
          </div>

          {/* Profit Windows strip (moved to top) */}
          <div className="px-6 pt-2">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 py-3 px-5 bg-card/50 backdrop-blur-xl border border-border rounded-xl shadow-2xl min-w-0">
              <div className="flex items-center gap-4 min-w-0">
                <div className="p-2 bg-primary/20 rounded-lg border border-primary/40">
                  <Globe className="w-5 h-5 text-primary" />
                </div>
                <div className="hidden sm:block">
                  <h1 className="text-2xl font-bold font-heading font-semibold tracking-[0.1em] text-foreground uppercase leading-none mb-1">
                    Profit Windows
                  </h1>
                  <div className="flex items-center gap-4 text-[9px] font-mono font-black text-foreground/40 dark:text-white/30 tracking-[0.1em] uppercase">
                    <div className="flex items-center gap-1.5">
                      <span>PK.VEC.NODE: {isOffline ? "CACHE" : "ACTIVE"}</span>
                      <div className={`w-1.5 h-1.5 rounded-full ${isOffline ? "bg-amber-500" : "bg-primary"} animate-pulse`} />
                    </div>
                    <div className="flex items-center gap-2 border-l border-border/50 pl-3 uppercase">
                      <RefreshCw className="w-2.5 h-2.5 text-foreground/20 dark:text-white/20" />
                      <span>LAST SYNC: {Math.floor((new Date().getTime() - lastSync.getTime()) / 60000)}m AGO</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3 lg:gap-6 flex-wrap justify-between lg:justify-end min-w-0">
                <div className="hidden lg:flex items-center gap-2 bg-foreground/5 border border-border/50 rounded-xl px-2 h-10 flex-wrap min-w-0 max-w-full">
                  <div className="flex items-center gap-2 px-3 h-8 text-muted-foreground/60">
                    <Search className="w-4 h-4" />
                    <input
                      type="text"
                      placeholder="LOCATION..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value.toUpperCase())}
                      className="bg-transparent border-none outline-none text-sm font-mono font-bold text-foreground w-28 xl:w-32 placeholder:text-muted-foreground/30 dark:placeholder:text-white/20"
                    />
                  </div>
                  <div className="w-px h-5 bg-foreground/10" />
                  <button
                    type="button"
                    onClick={() => setUseTrendingNow((v) => !v)}
                    style={{ flexShrink: 0 }}
                    className={`px-2 h-8 rounded-lg border text-[10px] font-mono font-black tracking-[0.15em] uppercase transition-colors ${
                      useTrendingNow
                        ? "bg-primary/20 border-primary/40 text-primary hover:bg-primary/30"
                        : "bg-foreground/5 border-border/50 text-muted-foreground/70 hover:text-foreground/80"
                    }`}
                    title="Discovery Mode: ON pulls fresh trending terms for your region to seed scans (faster discovery). OFF relies more on your specialties/custom keywords."
                  >
                    Discovery {useTrendingNow ? "ON" : "OFF"}
                  </button>
                </div>

                <Button
                  variant="outline"
                  onClick={handleTriggerScan}
                  disabled={isScanning || isLoading || specialtiesLoading}
                  className="bg-primary/20 border-primary/40 text-primary hover:bg-primary hover:text-black font-heading font-semibold text-sm px-5 h-10"
                >
                  <Zap className="w-4 h-4 mr-2" />
                  {specialtiesLoading ? "CHECKING..." : isScanning ? "SCANNING..." : "SCAN WORLD"}
                </Button>

                <Button
                  variant="outline"
                  onClick={() => handlePageRefresh()}
                  disabled={isScanning || isLoading || trendingNowLoading}
                  className="bg-foreground/5 border border-border/50 text-muted-foreground/80 hover:text-foreground font-mono font-black text-[10px] h-10 px-4 uppercase tracking-widest"
                  title="Refresh live feed + regional + industry trends"
                >
                  <RefreshCw className={`w-3.5 h-3.5 mr-2 ${(isLoading || trendingNowLoading) ? "animate-spin" : ""}`} />
                  REFRESH
                </Button>
              </div>
            </div>
          </div>

          {/* --- NEW: Above-the-fold 2-column intelligence layout --- */}
          <div className="w-full px-6 pt-6">
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 items-stretch">
              {/* Left (60%) */}
              <div className="lg:col-span-3 flex flex-col space-y-4">
                <div className="rounded-xl border border-border bg-foreground/5 p-4 flex-shrink-0">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="text-sm text-muted-foreground">Active trend</div>
                      <div className="mt-1 text-xl font-semibold truncate">
                        {effectiveTrend?.keyword || "—"}
                      </div>
                      <div className={`mt-2 text-sm text-muted-foreground ${topTrendExpanded ? "" : "line-clamp-2"}`}>
                        {execAnalysis?.keyword?.toLowerCase?.() === (effectiveTrend?.keyword || "").toLowerCase?.()
                          ? execAnalysis?.explanation
                          : "Run a scan to surface your top opportunity. AI analysis will appear automatically."}
                      </div>
                      <button
                        type="button"
                        className="mt-2 text-[10px] font-mono font-black uppercase tracking-widest text-primary/70 hover:text-primary transition-colors"
                        onClick={() => setTopTrendExpanded((v) => !v)}
                      >
                        {topTrendExpanded ? "Show less" : "Show more"}
                      </button>
                    </div>
                    <div className="flex flex-col items-end gap-2">
                      <Badge variant="secondary">
                        Urgency {Math.round(Number((effectiveTrend as any)?.profit_score ?? (effectiveTrend as any)?.score ?? 0) || 0)}
                      </Badge>
                      <Badge variant="outline">
                        {String((effectiveTrend as any)?.impact || "—")}
                      </Badge>
                    </div>
                  </div>
                </div>

                <div className="rounded-xl border border-border bg-foreground/5 p-4">
                  <div className="flex items-center justify-between">
                    <div className="text-sm font-semibold">Trends intelligence</div>
                    <Badge variant="outline">Tabs</Badge>
                  </div>
                  <Tabs defaultValue="regional" className="mt-3">
                    <TabsList className="w-full justify-start">
                      <TabsTrigger value="regional">Regional</TabsTrigger>
                      <TabsTrigger value="global">Business trends (global)</TabsTrigger>
                    </TabsList>

                    <TabsContent value="regional">
                      <div className="rounded-lg border border-border/60 bg-background/40 p-3">
                        <div className="text-xs text-muted-foreground">Trending now · PK</div>
                        <div className="mt-2 flex flex-wrap gap-1">
                          {(trendingNowRelevant?.length ? trendingNowRelevant.map((x) => x.term) : trendingNow)
                            .slice(0, 10)
                            .map((t) => (
                              <Badge
                                key={t}
                                variant="secondary"
                                className="cursor-pointer"
                                onClick={() => {
                                  addCustomKeyword(t);
                                  toast.success("Added keyword", { description: `"${t}" added to scan keywords.` });
                                }}
                              >
                                {t}
                              </Badge>
                            ))}
                        </div>
                      </div>
                    </TabsContent>

                    <TabsContent value="global">
                      <div className="rounded-lg border border-border/60 bg-background/40 p-3">
                        <div className="text-xs text-muted-foreground">Trending in your niche · Global</div>
                        {industryGlobalNotes ? (
                          <div className="mt-1 text-[10px] font-mono text-muted-foreground/60">
                            {industryGlobalNotes}
                          </div>
                        ) : null}
                        <div className="mt-2 flex flex-wrap gap-1">
                          {industryLoading ? (
                            <span className="text-xs text-muted-foreground/60">Loading…</span>
                          ) : industryTerms.length > 0 ? (
                            industryTerms.slice(0, 10).map((t) => (
                              <Badge
                                key={t}
                                variant="secondary"
                                className="cursor-pointer"
                                onClick={() => {
                                  addCustomKeyword(t);
                                  toast.success("Added keyword", { description: `"${t}" added to scan keywords.` });
                                }}
                              >
                                {t}
                              </Badge>
                            ))
                          ) : brandAlignedTerms.length > 0 ? (
                            brandAlignedTerms.slice(0, 10).map((x) => (
                              <Badge
                                key={x.term}
                                variant="secondary"
                                className="cursor-pointer"
                                onClick={() => {
                                  addCustomKeyword(x.term);
                                  toast.success("Added keyword", { description: `"${x.term}" added to scan keywords.` });
                                }}
                                title={x.matched?.length ? `Matched: ${x.matched.join(", ")}` : undefined}
                              >
                                {x.term}
                              </Badge>
                            ))
                          ) : (
                            <div className="flex items-center justify-between gap-3 w-full">
                              <span className="text-xs text-muted-foreground/60">
                                No niche trends yet. Try refresh (or add more Business Specialties).
                              </span>
                              <Button size="sm" variant="outline" onClick={() => fetchIndustryTrending()}>
                                Refresh
                              </Button>
                            </div>
                          )}
                        </div>
                      </div>
                    </TabsContent>
                  </Tabs>
                </div>
              </div>

              {/* Right (40%) */}
              <div className="lg:col-span-2 flex flex-col items-stretch">
                <div className="rounded-xl border border-border bg-foreground/5 p-4 flex flex-col">
                  <div className="flex items-center justify-between">
                    <div className="text-sm font-semibold">AI intelligence</div>
                    <Badge variant="outline">
                      {aiAnalysisStatus || (effectiveTrend as any)?.ai_analysis_status || "—"}
                    </Badge>
                  </div>
                  <div className="mt-3 text-sm text-muted-foreground">
                    {aiAnalysisStatus === "pending"
                      ? "Generating strategy…"
                      : (aiAnalysisData?.executive_summary || aiNextStep || execAnalysis?.explanation || "Open Full Strategy to view detailed AI guidance.")}
                  </div>
                  <div className="mt-4">
                     <UrgencyWidget 
                        urgency={aiAnalysisData?.opportunity_score?.urgency ?? (effectiveTrend as any)?.score ?? 0}
                        windowStatus={aiAnalysisData?.opportunity_window || (effectiveTrend as any)?.lifecycle_stage || "Checking Window..."}
                     />
                  </div>

                  <div className="mt-auto pt-4 grid grid-cols-1 gap-2">
                    <Button
                      onClick={() => {
                        const tid = (effectiveTrend as any)?.trend_signal_id || (lastScanSummary as any)?.trendId || null;
                        if (!tid) {
                          toast.error("No trend_id available yet. Run a scan first.");
                          return;
                        }
                        setDrawerOpen(true);
                      }}
                    >
                      Full Strategy →
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => {
                        if (effectiveTrend?.keyword) handleMagicBridge(effectiveTrend.keyword);
                        else toast.error("No trend selected.");
                      }}
                    >
                      Draft Content →
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => {
                        if (!effectiveTrend?.keyword) {
                          toast.error("No trend selected.");
                          return;
                        }
                        setLaunchDialogOpen(true);
                      }}
                    >
                      Launch Campaign →
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-8 px-6 pt-6">
            {showQualityBanner && (
              <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl flex items-start justify-between gap-4">
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-amber-300 mt-0.5 shrink-0" />
                  <div className="text-xs font-mono text-amber-200/90">
                    Some trends are showing estimated data while scans complete. Results will update automatically.
                  </div>
                </div>
                <Button
                  variant="ghost"
                  className="h-7 px-2 text-[10px] font-mono text-amber-200/70 hover:text-amber-200"
                  onClick={() => setQualityBannerDismissed(true)}
                >
                  Dismiss
                </Button>
              </div>
            )}
            {!specialtiesLoading && !hasSpecialties && (
              <div className="mt-3">
                <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl flex items-center justify-between gap-3">
                  <div className="text-xs font-mono text-amber-200/90">
                    Add at least 1 <span className="text-amber-200 font-black">Business Specialty</span> to enable scans.
                  </div>
                  <Button
                    variant="ghost"
                    className="h-8 px-3 text-[10px] font-mono text-amber-200/80 hover:text-amber-200"
                    onClick={() => navigate("/settings/business-specialties")}
                  >
                    Open Specialties
                  </Button>
                </div>
              </div>
            )}

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
                        <button
                          type="button"
                          className="ml-2 text-white/40 hover:text-white/80 transition-colors text-xs font-mono"
                          onClick={() => {
                            setError(null);
                            setIsOffline(false);
                          }}
                          aria-label="Dismiss system alert"
                          title="Dismiss"
                        >
                          ✕
                        </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Hero Trend / Empty State */}
              {liveTrends.length === 0 && !isLoading ? (
                <Reveal variant="fadeInUp">
                  <div className="relative overflow-hidden group p-12 bg-white/[0.02] border border-border/50 rounded-3xl backdrop-blur-3xl flex flex-col items-center text-center space-y-8">
                    <div className="w-20 h-20 bg-primary/20 rounded-full flex items-center justify-center animate-pulse">
                      <Globe className="w-10 h-10 text-primary" />
                    </div>
                    <div className="space-y-4 max-w-2xl">
                      <h2 className="text-4xl font-bold font-heading font-semibold tracking-[0.2em] text-foreground uppercase">No Trends Found</h2>
                      <p className="text-sm font-mono text-muted-foreground/60 leading-relaxed uppercase">
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
                      disabled={isScanning || specialtiesLoading}
                      className={`font-heading font-semibold text-2xl tracking-[0.2em] px-12 py-8 h-auto rounded-2xl transition-all shadow-[0_0_30px_rgba(0,224,208,0.3)] ${isScanning ? 'bg-primary/20 text-primary cursor-not-allowed' : 'bg-primary text-black hover:scale-105'
                        }`}
                    >
                      {specialtiesLoading ? (
                        <div className="flex items-center gap-3">
                          <RefreshCw className="w-6 h-6 animate-spin" /> CHECKING...
                        </div>
                      ) : isScanning ? (
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

                    {!specialtiesLoading && !hasSpecialties && (
                      <div className="text-[10px] font-mono text-amber-200/80 uppercase tracking-[0.2em]">
                        Add Business Specialties to enable scanning.
                        {" "}
                        <span
                          className="underline hover:text-amber-200 cursor-pointer"
                          onClick={() => navigate("/settings/business-specialties")}
                        >
                          Open Settings
                        </span>
                      </div>
                    )}

                    {isScanning && (
                      <div className="flex flex-col items-center gap-2">
                        <div className="w-64 h-1 bg-foreground/5 rounded-full overflow-hidden">
                          <motion.div
                            className="h-full bg-primary"
                            animate={{ x: [-256, 256] }}
                            transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                          />
                        </div>
                        <span className="text-[10px] font-mono text-primary animate-pulse uppercase tracking-[0.2em]">{scanStep}</span>
                      </div>
                    )}
                  </div>
                </Reveal>
              ) : null}

              

              {/* Market/strategy is shown inside the drawer tabs (source of truth: AI analysis). */}

              {/* AI Executive Analysis (Main Screen) */}
              


              {error && (
                <div className="bg-red-500/10 border border-red-500/20 p-4 rounded-xl flex items-center gap-3 text-red-100/60 text-[10px] font-mono uppercase">
                  <AlertCircle className="w-4 h-4 text-red-400" />
                  <span>{error}</span>
                </div>
              )}

              {(timelineFetchError || geoFetchError) && (
                <div className="bg-amber-500/10 border border-amber-500/20 p-4 rounded-xl flex items-center gap-3 text-amber-100/70 text-[10px] font-mono uppercase">
                  <AlertCircle className="w-4 h-4 text-amber-300" />
                  <span>
                    {timelineFetchError ? `Timeline: ${timelineFetchError} ` : ""}
                    {geoFetchError ? `Geo: ${geoFetchError}` : ""}
                  </span>
                </div>
              )}

              {lastScanSummary?.completedAt && timelineData.length === 0 && geoData.length === 0 && !timelineFetchError && !geoFetchError && (
                <div className="bg-primary/10 border border-primary/20 p-4 rounded-xl flex items-center gap-3 text-primary/80 text-[10px] font-mono uppercase">
                  <Info className="w-4 h-4 text-primary" />
                  <span>
                    Scan completed — showing current trends (fast scan). Open Live Feed / Notifications to see the top keywords and launch a campaign.
                  </span>
                </div>
              )}

              {/* Content Grid */}
              <div className="grid grid-cols-1 gap-8">
                {/* Single Column Feed & History */}
                <div className="space-y-8">

                  {/* Intelligence Grid */}
                  <Reveal variant="fadeInUp" delay={0.35}>
                    <div className="p-8 bg-white/[0.03] backdrop-blur-xl border border-border/50 rounded-2xl shadow-xl space-y-6">
                      <h2 className="text-xl font-bold font-heading font-semibold tracking-[0.1em] text-foreground uppercase flex items-center gap-3">
                        <div className="w-1.5 h-6 bg-teal-500 rounded-full" /> Intelligence Grid
                      </h2>
                      <IntelligenceGrid 
                        trendId={(effectiveTrend as any)?.trend_signal_id || lastScanSummary?.trendId || (effectiveTrend as any)?.id || null} 
                        aiAnalysisStatus={aiAnalysisStatus || (effectiveTrend as any)?.ai_analysis_status || null}
                        aiAnalysisData={aiAnalysisData} 
                        location={location} 
                        niche={(user as any)?.business_domain_name || user?.business_domain || 'marketing'} 
                        userPlatform={userPlatform}
                        keyword={effectiveTrend?.keyword || ""}
                      />
                    </div>
                  </Reveal>

                  {/* Signals Feed */}
                  <Reveal variant="fadeInUp" delay={0.4}>
                    <div className="p-8 bg-white/[0.03] backdrop-blur-xl border border-border/50 rounded-2xl shadow-xl space-y-6">
                      <div className="flex justify-between items-center">
                        <h2 className="text-xl font-bold font-heading font-semibold tracking-[0.1em] text-foreground uppercase flex items-center gap-3">
                          <div className="w-1.5 h-6 bg-primary rounded-full" /> Signals Feed
                        </h2>
                        <Button variant="ghost" onClick={() => setShowAllTrends(!showAllTrends)} className="text-[10px] font-mono font-bold text-primary/60 hover:text-primary uppercase h-8 px-4">
                          {showAllTrends ? "COLLAPSE" : "VIEW ALL"}
                        </Button>
                      </div>

                      {isScanning && (
                        <div className="p-4 bg-primary/10 border border-primary/20 rounded-xl flex items-center justify-between gap-4">
                          <div className="flex items-center gap-3">
                            <RefreshCw className="w-4 h-4 animate-spin text-primary/80" />
                            <div className="text-[10px] font-mono font-black uppercase tracking-[0.2em] text-primary/80">
                              Scanning…
                              <span className="ml-2 text-white/40 font-normal tracking-normal">
                                {scanStep || "Processing signal vectors"}
                              </span>
                            </div>
                          </div>
                          <div className="text-[10px] font-mono text-white/30 uppercase tracking-widest">
                            {location}
                          </div>
                        </div>
                      )}

                      <SignalsCarousel 
                        liveTrends={liveTrends} 
                        isLoading={isLoading} 
                        showAllTrends={showAllTrends} 
                        lifecycleFilter={lifecycleFilter} 
                        watchlist={watchlist} 
                        compare={compareTrends}
                        location={location} 
                        activeKeyword={effectiveTrend?.keyword || null}
                        onToggleWatchlist={handleToggleWatchlist} 
                        onToggleCompare={(t) => toggleCompare(t)}
                        onSelectTrend={(trend) => {
                          setSelectedTrend(trend);
                          setActiveTrend(trend);
                          setCampaignModalOpen(true);
                        }} 
                        onMagicBridge={handleMagicBridge} 
                        onTriggerScan={handleTriggerScan} 
                      />
                    </div>
                  </Reveal>

                  {/* Watchlist Section */}
                  {watchlist.length > 0 && (
                    <Reveal variant="fadeInUp" delay={0.5}>
                      <div className="p-8 bg-white/[0.03] backdrop-blur-xl border border-border/50 rounded-2xl shadow-xl space-y-6">
                        <h2 className="text-xl font-bold font-heading font-semibold tracking-[0.1em] text-foreground uppercase flex items-center gap-3">
                          <div className="w-1.5 h-6 bg-amber-500 rounded-full" /> Tracked Vectors
                        </h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                          {watchlist.map((item) => (
                            <div key={item.id} className="p-4 bg-foreground/5 border border-border/50 rounded-xl relative group">
                              <button
                                onClick={() => handleRemoveFromWatchlist(item.keyword)}
                                className="absolute top-2 right-2 text-white/20 hover:text-red-500 transition-colors"
                              >
                                <AlertCircle className="w-4 h-4" />
                              </button>
                              <div className="flex flex-col gap-1">
                                <span className="text-sm font-bold font-heading font-semibold text-foreground tracking-widest uppercase">{item.keyword}</span>
                                <div className="flex gap-4 items-center">
                                  <div className="text-[10px] font-mono text-primary flex gap-1 items-center">
                                    <Wind className="w-3 h-3" /> {item.last_velocity}σ
                                  </div>
                                  <div className="text-[10px] font-mono text-muted-foreground/60 flex gap-1 items-center">
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

                  {/* Trend History Matrix */}
                  <Reveal variant="fadeInUp" delay={0.6}>
                    <div className="p-8 bg-white/[0.03] backdrop-blur-xl border border-border/50 rounded-2xl shadow-xl space-y-8">
                       <h2 className="text-xl font-bold font-heading font-semibold tracking-[0.1em] text-foreground flex items-center gap-3">
                           <Activity className="w-6 h-6 text-primary" /> TREND HISTORY MATRIX
                        </h2>
                        
                        <TrendHistoryTable trendHistory={trendHistory} />
                    </div>
                  </Reveal>
                </div>
              </div>
            </div>
          </div>
      </div>

      {/* Deploy AI Assets Sheet */}
      <Sheet open={deploySheetOpen} onOpenChange={setDeploySheetOpen}>
        <SheetContent className="border-l border-border/50 text-foreground w-[420px] flex flex-col">
          <SheetHeader className="mb-6">
            <SheetTitle className="font-heading font-semibold text-3xl tracking-wide flex items-center gap-2">
              <Zap className="w-6 h-6 text-primary" /> DEPLOY AI ASSETS
            </SheetTitle>
            <SheetDescription className="font-mono text-xs text-muted-foreground/60">
              Pick a content type, review the prompt, then open it in Creative Studio.
            </SheetDescription>
          </SheetHeader>

          <div className="flex-1 overflow-y-auto space-y-6">
            {liveTrends[0] && (
              <div className="relative p-6 bg-zinc-900/80 border border-white/10 rounded-2xl space-y-4">
                <div className="text-[9px] font-mono text-primary/60 uppercase tracking-widest">Currently Trending · {liveTrends[0].location}</div>
                <div className="text-2xl font-heading font-semibold text-foreground tracking-wide">{liveTrends[0].keyword}</div>
                <div className="text-xs font-mono text-muted-foreground/60">{liveTrends[0].niche} · Signal: {liveTrends[0].score}σ</div>
              </div>
            )}

            <div className="space-y-2">
              <p className="text-[10px] font-mono text-muted-foreground/60 uppercase tracking-widest">What do you want to create?</p>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { key: "carousel", label: "Carousel", hint: "Tips & education" },
                  { key: "reel",     label: "Reel",     hint: "Reach & discovery" },
                  { key: "story",    label: "Story",    hint: "Promos & offers" },
                ].map(({ key, label, hint }) => (
                  <button
                    key={key}
                    onClick={() => {
                      setDeployContentType(key as any);
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
                        ? 'border-primary bg-primary/10 text-foreground'
                        : 'border-border/50 bg-white/[0.02] text-muted-foreground/80 hover:border-border/80'
                    }`}
                  >
                    <div className="text-sm font-heading font-semibold">{label}</div>
                    <div className="text-[9px] font-mono text-white/30 mt-0.5">{hint}</div>
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <p className="text-[10px] font-mono text-muted-foreground/60 uppercase tracking-widest">AI-suggested prompt (edit freely)</p>
              <textarea
                value={deployPrompt}
                onChange={(e) => setDeployPrompt(e.target.value)}
                rows={5}
                className="w-full bg-white/[0.03] border border-border/50 rounded-xl p-4 text-sm font-mono text-white/80 resize-none focus:outline-none focus:border-primary/50 leading-relaxed"
              />
            </div>
          </div>

          <div className="pt-4 border-t border-border space-y-2 mt-4">
            <Button
              className="w-full bg-primary text-black font-heading font-semibold text-lg h-12 rounded-xl hover:opacity-90"
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

      {/* Trend Detail Dialog */}
      <Dialog open={campaignModalOpen} onOpenChange={setCampaignModalOpen}>
        <DialogContent className="border border-border/50 text-foreground max-w-lg rounded-2xl">
          <DialogHeader>
            <DialogTitle className="font-heading font-semibold text-2xl tracking-[0.15em] text-primary uppercase">
              {(() => {
                  if (!selectedTrend) return "Trend Detail";
                  return selectedTrend.keyword;
              })()}
            </DialogTitle>
            <DialogDescription className="text-muted-foreground/60 font-mono text-xs uppercase tracking-wider">
              {selectedTrend?.lifecycle_stage ?? ""} · {selectedTrend?.location ?? ""}
            </DialogDescription>
          </DialogHeader>

          {selectedTrend && (
            <div className="space-y-4 pt-2">
              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: "SIGNAL SCORE", value: selectedTrend.score ? `${selectedTrend.score.toFixed(1)}σ` : null },
                  { label: "PROFIT SCORE", value: selectedTrend.profit_score || null },
                  { label: "SATURATION", value: selectedTrend.saturation_score ? `${selectedTrend.saturation_score}%` : null },
                  { label: "SOCIAL SCORE", value: selectedTrend.social_score || null },
                ].filter(m => m.value !== null).map(({ label, value }) => (
                  <div key={label} className="p-3 bg-foreground/5 border border-border/50 rounded-xl">
                    <p className="text-[9px] font-mono font-black text-white/30 uppercase tracking-wider mb-1">{label}</p>
                    <p className="text-lg font-heading font-semibold text-foreground">{value}</p>
                  </div>
                ))}
              </div>

              {selectedTrend.niche && (
                <div className="p-3 bg-foreground/5 border border-border/50 rounded-xl">
                  <p className="text-[9px] font-mono font-black text-white/30 uppercase tracking-wider mb-1">NICHE</p>
                  <p className="text-sm font-mono text-white/80">{selectedTrend.niche}</p>
                </div>
              )}

              {(selectedTrend.rising_queries?.length ?? 0) > 0 && (
                <div className="p-3 bg-foreground/5 border border-border/50 rounded-xl">
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
                  className="flex-1 bg-primary text-black font-heading font-semibold text-base h-10 rounded-xl hover:opacity-90"
                  onClick={() => {
                    setCampaignModalOpen(false);
                    const currentNiche = (user as any)?.business_domain_name || user?.business_domain || 'marketing';
                    const prompt = `Create an Instagram Reel script about "${selectedTrend.keyword}" targeting ${selectedTrend.location}. Niche: ${selectedTrend.niche || currentNiche}. Keep it under 30 seconds with a strong hook and clear call-to-action.`;
                    navigate("/dashboard/creative", { state: { prefillPrompt: prompt } });
                  }}
                >
                  CREATE CONTENT →
                </Button>
                <Button
                  variant="outline"
                  className="border-border/50 text-muted-foreground/80 font-heading font-semibold text-base h-10 rounded-xl hover:bg-foreground/5"
                  onClick={() => handleAddToWatchlist(selectedTrend.keyword)}
                >
                  + WATCHLIST
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <LaunchCampaignDialog
        open={launchDialogOpen}
        onOpenChange={setLaunchDialogOpen}
        prefill={{
          trend_id: (effectiveTrend as any)?.trend_signal_id || (lastScanSummary as any)?.trendId || (effectiveTrend as any)?.id || null,
          keyword: effectiveTrend?.keyword || null,
          niche: effectiveTrend?.niche || ((user as any)?.business_domain_name || user?.business_domain || null),
          location: effectiveTrend?.location || location || null,
          suggested_platforms: Array.isArray(aiAnalysisData?.platform_recommendations)
            ? Array.from(new Set(aiAnalysisData.platform_recommendations.map((x: any) => String(x?.platform || "").toLowerCase()).filter(Boolean)))
            : [userPlatform],
          hashtags: (() => {
            const pack = aiAnalysisData?.hashtag_pack || {};
            const out = [
              ...(Array.isArray(pack.primary) ? pack.primary : []),
              ...(Array.isArray(pack.secondary) ? pack.secondary : []),
              ...(Array.isArray(pack.niche) ? pack.niche : []),
            ];
            return out.filter((h: any) => typeof h === "string" && h.trim()).slice(0, 12);
          })(),
          lifecycle_stage: (topTrend as any)?.lifecycle_stage || null,
        }}
      />

      <AIStrategyDrawer
        open={drawerOpen}
        onOpenChange={setDrawerOpen}
        trendId={activeDrawerTrend}
        analysis={aiAnalysisData}
        onOpenInCreative={(text) => navigate("/dashboard/creative", { state: { prefillPrompt: text } })}
        onRegenerate={async () => {
          if (!activeDrawerTrend) return;
          setAiAnalysisStatus("pending");
          try {
            await trendService.regenerateAIAnalysis(activeDrawerTrend);
          } catch {
            // ignore
          }
        }}
      />
    </Layout>
  );
};

export default TrendArbitrage;
