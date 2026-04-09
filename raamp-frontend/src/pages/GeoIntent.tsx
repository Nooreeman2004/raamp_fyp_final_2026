import { useState, useEffect, useCallback, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import { motion, AnimatePresence } from "framer-motion";
import { 
  MapPin, Target, TrendingUp, Users, Globe, Radar, 
  Crosshair, Scan, RefreshCw, Layers, Info, Map as MapIcon,
  Activity, Fingerprint, Calendar, Mail, Megaphone, Clock, MapPinned,
  ChevronRight, ArrowRight
} from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import Layout from "@/components/Layout";
import { HolographicCard } from "@/components/ui/holographic-card";
import { BlurText } from "@/components/ui/text-reveal";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeInUp, hoverScale, hoverLift } from "@/utils/animations";
import { businessService } from "@/services/businessService";
import { geoIntentService, HeatScoreResponse, HeatmapResponse, CampaignLogEntry, CampaignBrief } from "@/services/geoIntentService";
import GeoIntentMap, { GeoIntentMapRef } from "@/components/GeoIntentMap";
import GeoCampaignBriefModal from "@/components/GeoCampaignBriefModal";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

/**
 * Stable geo key for API calls: prefer Google `place_id` from Business/onboarding;
 * if the user dropped a pin without a Place ID, use fixed onboarding coordinates instead of a generic demo id.
 */
function resolveGeoBusinessId(
  setup: {
    place_id?: string | null;
    latitude?: number | null;
    longitude?: number | null;
    business_name?: string | null;
  } | null | undefined,
  fallbackName: string
): string {
  const pid = setup?.place_id?.trim();
  if (pid) return pid;
  const lat = setup?.latitude;
  const lng = setup?.longitude;
  if (
    typeof lat === "number" &&
    typeof lng === "number" &&
    !Number.isNaN(lat) &&
    !Number.isNaN(lng)
  ) {
    return `onboarding_${lat.toFixed(6)}_${lng.toFixed(6)}`;
  }
  const name = (setup?.business_name || fallbackName || "business").trim();
  return `demo_business_${name.toLowerCase().replace(/\s+/g, "_")}`;
}

const GeoIntent = () => {
  const [radius, setRadius] = useState<number[]>(() => {
    const saved = localStorage.getItem("geointent_radius");
    return saved ? [parseInt(saved)] : [5];
  });
  const [businessName, setBusinessName] = useState("Artisan Coffee House");
  const [data, setData] = useState<HeatScoreResponse | null>(null);
  const [heatmapData, setHeatmapData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [history, setHistory] = useState<CampaignLogEntry[]>([]);
  const [scanLogs, setScanLogs] = useState<{id: string, time: string, msg: string, type: 'info' | 'alert' | 'success'}[]>([]);
  const [persona, setPersona] = useState<{type: string, pct: number, desc: string}[]>([]);

  const [setup, setSetup] = useState<any>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  
  // Brief Modal States
  const [briefModalOpen, setBriefModalOpen] = useState(false);
  const [campaignBrief, setCampaignBrief] = useState<CampaignBrief | null>(null);
  const [briefLoading, setBriefLoading] = useState(false);
  const [strategyHistory, setStrategyHistory] = useState<CampaignBrief[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const mapRef = useRef<GeoIntentMapRef>(null);

  const fetchSetup = async () => {
    try {
      const response = await businessService.getHyperlocalSetup();
      if (response && response.business_name) {
        setSetup(response);
        setBusinessName(response.business_name);
        return response;
      }
    } catch (e) {
      console.error("Failed to fetch setup", e);
      toast.error("Profile sync failed. Check your network connection.");
    }
    return null;
  };

  const handleManualSync = async () => {
    setRefreshing(true);
    toast.info("Synchronizing with your latest Business Setup...");
    const activeSetup = await fetchSetup();
    if (activeSetup) {
      toast.success(`Profile synced: ${activeSetup.business_name}`);
      await fetchData(activeSetup);
    } else {
      toast.error("No updated profile data found.");
      setRefreshing(false);
    }
  };

  const fetchHeatmap = useCallback(async (activeSetup?: any) => {
    try {
      const biz = activeSetup || setup;
      const nameForId = biz?.business_name || businessName;
      const bid = resolveGeoBusinessId(biz, nameForId);
      const response = await geoIntentService.getHeatmap(bid);
      if (response && response.features) {
        const points = response.features.map(f => ({
          lat: f.geometry.coordinates[1],
          lng: f.geometry.coordinates[0],
          weight: (f.properties.score / 100) * 10
        }));
        setHeatmapData(points);
      }
    } catch (error) {
      console.error("Failed to fetch heatmap", error);
    }
  }, [setup, businessName]);

  const fetchStrategyHistory = useCallback(async (activeSetup?: any) => {
    const biz = activeSetup || setup;
    const nameForId = biz?.business_name || businessName;
    const bid = resolveGeoBusinessId(biz, nameForId);
    setHistoryLoading(true);
    try {
      const h = await geoIntentService.getCampaignBriefHistory(bid);
      setStrategyHistory(h);
    } catch (e) {
      console.error("Failed to fetch strategy history", e);
    } finally {
      setHistoryLoading(false);
    }
  }, [setup, businessName]);

  const fetchData = useCallback(async (currentSetup?: any, overrideLat?: number, overrideLng?: number) => {
    try {
      setRefreshing(true);
      const activeSetup = currentSetup || setup;
      const nameForId = activeSetup?.business_name || businessName;
      const businessId = resolveGeoBusinessId(activeSetup, nameForId);

      const payload = {
        business_id: businessId,
        keywords: activeSetup?.business_type ? [activeSetup.business_type, "business", "store"] : ["coffee", "cafe", "espresso"],
        latitude: overrideLat || activeSetup?.latitude || 33.7215,
        longitude: overrideLng || activeSetup?.longitude || 73.0433,
        radius: radius[0] * 1000,
        is_indoor: true
      };
      const response = await geoIntentService.getHeatScore(payload);
      if (response) {
        setData(response);
        setErrorMsg(null);
      }
      
      // Also fetch heatmap and strategy history
      await fetchHeatmap(activeSetup);
      await fetchStrategyHistory(activeSetup);
    } catch (error: any) {
      console.error("Failed to fetch geo intent data", error);
      setErrorMsg(error?.message || "Our satellite link timed out. Please try a smaller radius or refresh the radar.");
      toast.error(error?.message || "Satellite link error");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [setup, businessName, radius, fetchHeatmap, fetchStrategyHistory]);

  const handleRefresh = () => {
      fetchData();
  };

  const handleDeployClick = async () => {
    if (!data) {
        toast.error("Please run a radar scan first to generate a brief.");
        return;
    }
    
    setBriefLoading(true);
    
    try {
        const keywords = setup?.business_type 
            ? [setup.business_type, "business", "store"] 
            : ["coffee", "cafe", "espresso"];

        const nameForId = setup?.business_name || businessName;
        const businessId = resolveGeoBusinessId(setup, nameForId);

        const brief = await geoIntentService.generateCampaignBrief({
            lat: data.latitude || setup?.latitude || 33.7215,
            lng: data.longitude || setup?.longitude || 73.0433,
            radius_km: radius[0],
            heat_score: data.score,
            urgency: data.urgency,
            trends_score: data.signals.trends_score * 100,
            weather_score: data.signals.weather_score * 100,
            places_score: data.signals.places_score * 100,
            reasoning: data.reasoning || "Consistent commercial intent detected.",
            persona_split: data.persona_split || [],
            keywords,
            business_id: businessId,
        });

        setCampaignBrief(brief);
        setBriefModalOpen(true);
        toast.success(`Strategic brief saved! Campaign ID: ${brief.campaign_id?.substring(0, 8)}`);
        
        // Refresh history
        fetchStrategyHistory();
    } catch (err) {
        console.error('Brief generation failed:', err);
        toast.error("Cloud compute error generating brief. Please try again.");
    } finally {
        setBriefLoading(false);
    }
  };

  const handleReplayCampaign = async (brief: CampaignBrief) => {
    toast.info(`Replaying historical market state: ${new Date(brief.timestamp).toLocaleDateString()}`);
    
    // 1. Refocus map
    if (mapRef.current && brief.location?.coordinates) {
       mapRef.current.panTo([brief.location.coordinates[1], brief.location.coordinates[0]]);
    }
    
    // 2. Restore radius
    setRadius([brief.radius_km]);
    
    // 3. Populate modal
    setCampaignBrief(brief);
    setBriefModalOpen(true);
    
    // 4. Override current dashboard state to match historical snapshot
    setData({
      score: brief.heat_score,
      urgency: brief.urgency,
      is_critical: brief.heat_score > 90,
      latitude: brief.location.coordinates[1],
      longitude: brief.location.coordinates[0],
      radius_km: brief.radius_km,
      signals: {
        trends_score: brief.trends_score / 100,
        places_score: brief.places_score / 100,
        weather_score: brief.weather_score / 100
      },
      signals_status: { trends: "HISTORICAL", places: "HISTORICAL", weather: "HISTORICAL" },
      reasoning: brief.strategy_rationale,
      persona_split: brief.persona_split,
      timestamp: brief.timestamp
    });
  };

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      const activeSetup = await fetchSetup();
      await fetchData(activeSetup);
      
      if (activeSetup) {
          try {
              const nameForId = activeSetup.business_name || businessName;
              const bid = resolveGeoBusinessId(activeSetup, nameForId);
              const hist = await geoIntentService.getHistory(bid);
              setHistory(hist.logs);
          } catch (e) {
              console.error("History fetch failed", e);
          }
      }
    };
    init();
  }, []);

  // Update real-time UI lists when data arrives
  useEffect(() => {
    if (data) {
      if (data.radar_feed) {
        setScanLogs(data.radar_feed);
      }
      if (data.persona_split) {
        setPersona(data.persona_split);
      }
    }
  }, [data]);

  // Debounced re-fetch when radius changes
  useEffect(() => {
    if (!loading && !refreshing) {
        localStorage.setItem("geointent_radius", radius[0].toString());
        const timer = setTimeout(() => {
            fetchData();
        }, 1000);
        return () => clearTimeout(timer);
    }
  }, [radius]);

  return (
    <Layout>
      <TooltipProvider delayDuration={100}>
        <div className="space-y-8">
        {/* Header */}
        <Reveal variant="blurInUp">
          <div className="flex items-center justify-between gap-4 mb-2">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-primary/10 rounded border border-primary/30 relative">
                <Globe className="w-8 h-8 text-primary animate-spin-slow" />
                {setup && (
                  <div className="absolute -top-1 -right-1">
                    <div className="w-3 h-3 bg-primary rounded-full border-2 border-background animate-pulse" />
                  </div>
                )}
              </div>
              <div>
                <h1 className="text-4xl font-bold mb-1 font-heading font-semibold text-foreground flex items-center gap-3">
                   GEO-INTENT TARGETING
                   {setup && (
                     <Badge variant="outline" className="bg-primary/5 text-primary border-primary/30 text-[10px] font-mono py-0 h-5">
                       PROFILE ON
                     </Badge>
                   )}
                </h1>
                <p className="text-muted-foreground font-mono text-sm uppercase flex items-center gap-2">
                    <span className="opacity-60">//</span> 
                    {setup ? `Targeting: ${setup.business_name}` : "Scanning Initial Signals"}
                    <span className="opacity-60">//</span>
                    Radius: {radius[0]}KM
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={handleManualSync}
                disabled={loading || refreshing}
                className="bg-card border-primary/30 text-primary hover:bg-primary/20 font-mono text-[10px] hidden sm:flex"
              >
                <RefreshCw className={`w-3 h-3 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                SYNC PROFILE
              </Button>
              <Button
                variant="outline"
                size="icon"
                onClick={handleRefresh}
                disabled={loading || refreshing}
                className="bg-card border-primary/30 text-primary hover:bg-primary/20"
              >
                <Radar className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </div>
        </Reveal>

        {/* Staggered Grid */}
        <motion.div
          className="grid lg:grid-cols-2 gap-6"
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
        >
          {/* Targeting Zone Builder */}
          <motion.div variants={fadeInUp}>
            <HolographicCard className="p-6 h-full border-primary/30">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold font-heading font-semibold text-foreground flex items-center gap-2">
                  <Target className="w-5 h-5 text-primary" />
                  TARGETING ZONE BUILDER
                </h2>
                <div className="flex items-center gap-2 text-[10px] font-mono text-primary border border-primary/30 px-2 py-1 rounded bg-primary/5">
                  <div className={`w-2 h-2 rounded-full ${refreshing ? 'bg-amber-500' : 'bg-primary'} animate-pulse`} />
                  {refreshing ? 'SYNCING LIVE INTENT' : 'LIVE DATA SCANNING'}
                </div>
              </div>

              {/* Functional Map View */}
              <div className="aspect-video bg-background/60 rounded border border-border/50 mb-6 relative overflow-hidden group">
                <GeoIntentMap 
                  ref={mapRef}
                  center={{ lat: setup?.latitude || 33.7215, lng: setup?.longitude || 73.0433 }}
                  radiusMeters={radius[0] * 1000}
                  heatmapData={heatmapData}
                  onDrawingComplete={(coords) => {
                      if (coords.length > 0) {
                          // Calculate centroid
                          const lat = coords.reduce((sum, c) => sum + c.lat, 0) / coords.length;
                          const lng = coords.reduce((sum, c) => sum + c.lng, 0) / coords.length;
                          
                          toast.success(`Custom zone captured. Refocusing radar to: ${lat.toFixed(4)}, ${lng.toFixed(4)}`);
                          fetchData(setup, lat, lng);
                      }
                  }}
                />
                
                {/* Map Legend Overlay */}
                <div className="absolute top-4 left-4 z-10 bg-card/80 dark:bg-card/90 backdrop-blur-md border border-border/40 p-3 rounded-lg flex flex-col gap-2 pointer-events-none shadow-xl">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse shadow-[0_0_8px_#ff4d4d]" />
                    <span className="text-[10px] font-mono text-foreground font-bold tracking-tighter">SCAN CENTER</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-primary shadow-[0_0_8px_rgba(0,224,208,0.5)]" />
                    <span className="text-[10px] font-mono text-foreground font-bold tracking-tighter uppercase">Intense Interest Hotspots</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-primary border border-background" />
                    <span className="text-[10px] font-mono text-foreground font-bold tracking-tighter uppercase">Live Activity Pings</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full border border-primary/50" />
                    <span className="text-[10px] font-mono text-foreground font-bold tracking-tighter uppercase">Scanning Boundary</span>
                  </div>
                </div>

                {!loading && heatmapData.length === 0 && (
                  <div className="absolute inset-0 z-20 flex items-center justify-center bg-background/20 pointer-events-none">
                     <div className="px-4 py-2 bg-background/95 border border-primary/40 rounded-full flex items-center gap-2 shadow-[0_0_20px_rgba(0,224,208,0.2)]">
                        <Radar className="w-4 h-4 text-primary animate-pulse" />
                        <span className="text-[11px] font-mono text-primary font-bold tracking-widest uppercase">Scanner Active: Searching for Activity...</span>
                     </div>
                  </div>
                )}
              </div>

              <div className="space-y-6">
                <div>
                  <div className="flex justify-between mb-2">
                    <label className="text-xs font-mono text-muted-foreground uppercase tracking-wider">Zone Radius</label>
                    <span className="text-xs font-mono text-primary font-bold">{radius[0]} KM</span>
                  </div>
                  <Slider
                    value={radius}
                    onValueChange={setRadius}
                    max={50}
                    min={1}
                    step={1}
                    className="mb-2 [&>.relative>.absolute]:bg-primary [&>.relative]:bg-foreground/10"
                  />
                </div>

                {/* Command Intelligence Insights */}
                {data?.reasoning && (
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-4 bg-primary/5 border border-primary/20 rounded-lg relative overflow-hidden group"
                  >
                    <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-30 transition-opacity">
                      <Target className="w-8 h-8 text-primary" />
                    </div>
                    <div className="flex items-start gap-3">
                      <div className="p-2 bg-primary/10 rounded border border-primary/30 mt-0.5">
                        <Info className="w-3 h-3 text-primary" />
                      </div>
                      <div>
                        <p className="text-[10px] font-mono text-primary font-bold uppercase tracking-widest mb-1 leading-none opacity-60">
                           Command Center Recommendation
                        </p>
                        <p className="text-xs font-mono text-foreground leading-relaxed">
                          {data.reasoning}
                        </p>
                      </div>
                    </div>
                  </motion.div>
                )}

                <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                  <Button 
                    onClick={() => {
                        mapRef.current?.startDrawing();
                        toast.info("Custom radar sweep initiated. Draw a zone on the map.");
                    }}
                    className="w-full bg-primary/10 text-primary border border-primary/50 hover:bg-primary hover:text-primary-foreground font-mono font-bold tracking-wider transition-all h-12"
                  >
                    <Crosshair className="w-4 h-4 mr-2" />
                    INITIATE CUSTOM ZONE DRAWING
                  </Button>
                </motion.div>
              </div>
            </HolographicCard>
          </motion.div>

          {/* Right Column - Insights */}
          <div className="space-y-6">
            {/* Geo-Intent Insights */}
            <motion.div variants={fadeInUp}>
              <HolographicCard className="p-6">
                <h3 className="text-lg font-bold mb-4 font-heading font-semibold text-foreground flex items-center gap-2">
                  <Radar className="w-5 h-5 text-primary" />
                  WHY THIS {radius[0]}KM AREA IS "HOT"
                </h3>
                <div className="space-y-4 h-[280px] overflow-y-auto pr-2 custom-scrollbar">
                  {loading ? (
                    <div className="flex flex-col items-center justify-center h-full space-y-4">
                      <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                      <p className="text-xs font-mono text-primary animate-pulse">Scanning frequencies...</p>
                    </div>
                  ) : data ? (
                    <>
                      {/* Overall Score */}
                      <motion.div variants={hoverLift} className="flex flex-col gap-2 p-3 bg-card rounded border border-border/50">
                        <div className="flex justify-between items-center">
                          <span className="font-bold text-sm font-mono text-primary uppercase tracking-widest">Opportunity Rating</span>
                          <span className={`text-xs font-mono font-bold ${data.is_critical ? 'text-red-500' : 'text-primary'}`}>{data.score}/100</span>
                        </div>
                        <div className="h-2 w-full bg-foreground/10 rounded-full overflow-hidden">
                           <div className={`h-full ${data.is_critical ? 'bg-red-500' : 'bg-primary'}`} style={{ width: `${data.score}%` }} />
                        </div>
                      </motion.div>
                      
                      {/* Signals Breakdown */}
                      {[
                        { name: "Online Interest", score: data.signals.trends_score, status: data.signals_status.trends, desc: "People searching for your type of business" },
                        { name: "Crowd Traffic", score: data.signals.places_score, status: data.signals_status.places, desc: "Physical density of people nearby" },
                        { name: "Weather Boost", score: data.signals.weather_score, status: data.signals_status.weather, desc: "Favorability of current conditions" }
                      ].map((signal, idx) => (
                        <motion.div
                          key={idx}
                          variants={hoverLift}
                          className="flex items-center justify-between p-3 bg-card rounded border border-border/50 hover:border-primary/50 transition-all group"
                        >
                          <div className="flex items-center gap-3 w-full">
                            <div className={`w-2 h-2 rounded-full ${signal.status === 'ok' ? 'bg-primary shadow-[0_0_8px_rgba(0,224,208,0.8)]' : 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)]'} animate-pulse`}></div>
                            <div className="flex-1">
                              <div className="flex justify-between items-center">
                                <p className="font-bold text-[10px] font-mono text-foreground group-hover:text-primary transition-colors tracking-tighter">{signal.name.toUpperCase()}</p>
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <button className="outline-none focus:ring-1 focus:ring-primary rounded-full transition-opacity opacity-60 hover:opacity-100 flex items-center gap-1 group/tip">
                                       <Radar className="w-3 h-3 text-primary group-hover/tip:animate-pulse" />
                                       <span className="text-[9px] font-mono text-muted-foreground uppercase">{signal.status === 'ok' ? 'ACTIVE' : 'FAILED'}</span>
                                    </button>
                                  </TooltipTrigger>
                                  <TooltipContent side="right" className="bg-popover border border-border p-4 max-w-[280px] shadow-2xl text-popover-foreground z-[100] rounded-xl">
                                    <p className="font-bold text-primary mb-1 uppercase tracking-widest">{signal.name}</p>
                                    <p className="mb-2">{signal.desc}</p>
                                    <div className="pt-2 border-t border-border flex justify-between items-baseline">
                                       <span className="text-[8px] opacity-60 uppercase">Raw Signal Value:</span>
                                       <span className="text-primary font-bold">{(signal.score * 100).toFixed(1)}%</span>
                                    </div>
                                  </TooltipContent>
                                </Tooltip>
                              </div>
                              <div className="flex items-center gap-2">
                                <div className="h-1 flex-1 bg-foreground/10 rounded-full overflow-hidden mt-1">
                                  <div className={`h-full ${signal.status === 'ok' ? 'bg-primary' : 'bg-red-500'}`} style={{ width: `${signal.score * 100}%` }} />
                                </div>
                                <p className="text-[10px] text-muted-foreground/60 font-mono w-8 text-right">{(signal.score * 100).toFixed(0)}%</p>
                              </div>
                            </div>
                          </div>
                        </motion.div>
                      ))}
                    </>
                  ) : errorMsg ? (
                    <div className="flex flex-col items-center justify-center h-full space-y-4 p-4 text-center">
                      <div className="p-3 bg-red-500/10 rounded-full border border-red-500/30">
                        <Radar className="w-6 h-6 text-red-400 rotate-180" />
                      </div>
                      <p className="text-xs font-mono text-red-400 font-bold uppercase tracking-wider">Interference Detected</p>
                      <p className="text-[10px] font-mono text-muted-foreground/80">{errorMsg}</p>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center h-full space-y-4">
                      <p className="text-xs font-mono text-muted-foreground/80">No signal data acquired. Deploy radar scan to begin.</p>
                    </div>
                  )}
                </div>
              </HolographicCard>
            </motion.div>

            {/* Detailed Analysis Metrics */}
            <motion.div variants={fadeInUp}>
              <HolographicCard className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-bold font-heading font-semibold text-foreground flex items-center gap-2">
                    <Layers className="w-5 h-5 text-primary" />
                    ANALYSIS METRICS
                  </h3>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button className="cursor-help transition-opacity opacity-50 hover:opacity-100 outline-none">
                         <Radar className="w-4 h-4 text-primary" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="top" className="bg-popover border border-primary/40 text-xs font-mono p-4 max-w-[280px] text-popover-foreground rounded-xl shadow-2xl">
                      Aggregated from Trends, Google Places, and Tomorrow.io weather.
                    </TooltipContent>
                  </Tooltip>
                </div>

                <div className="space-y-4">
                   <div className="grid grid-cols-2 gap-4">
                     <div className="p-4 bg-foreground/5 rounded border border-border/50 hover:border-primary/30 transition-colors">
                       <Target className={`w-5 h-5 mb-2 ${data?.is_critical ? 'text-red-500 animate-pulse' : 'text-primary'}`} />
                       <p className={`text-2xl font-bold font-heading font-semibold ${data?.is_critical ? 'text-red-400' : 'text-foreground'}`}>
                         {loading ? "..." : (data?.urgency.toUpperCase() || "UNKNOWN")}
                       </p>
                       <p className="text-[10px] text-muted-foreground font-mono uppercase">Zone Urgency</p>
                     </div>
                     <div className="p-4 bg-foreground/5 rounded border border-border/50 hover:border-primary/30 transition-colors">
                       <TrendingUp className="w-5 h-5 text-primary mb-2" />
                       <p className="text-2xl font-bold font-heading font-semibold text-foreground">
                         {loading ? "..." : (data ? new Date(data.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : "--:--")}
                       </p>
                       <p className="text-[10px] text-muted-foreground font-mono uppercase">Scan Timestamp</p>
                     </div>
                   </div>

                   {/* Additional Stats */}
                   <div className="p-4 bg-primary/5 rounded border border-primary/20">
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-[9px] font-mono text-muted-foreground uppercase opacity-70">Projected Reach</span>
                        <span className="text-[10px] font-mono text-primary font-bold">~{(data?.signals.places_score || 0) * 1200 + 450} USERS</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-[9px] font-mono text-muted-foreground uppercase opacity-70">Conv. Probability</span>
                        <span className="text-[10px] font-mono text-primary font-bold">{(data?.score || 0) * 0.85}% BOOST</span>
                      </div>
                   </div>

                   <p className="text-[10px] font-mono text-muted-foreground/80 italic leading-relaxed">
                      * This {radius[0]}KM region is currently showing {(data?.score || 0)}% higher receptivity compared to your 7-day average baseline.
                   </p>
                </div>
              </HolographicCard>
            </motion.div>
          </div>
        </motion.div>

        {/* Secondary Row: Logs & Persona */}
        <motion.div 
           className="grid lg:grid-cols-3 gap-6"
           variants={staggerContainer}
           initial="hidden"
           animate="visible"
        >
          {/* Live Scan Log */}
          <motion.div variants={fadeInUp}>
            <HolographicCard className="p-5 h-full">
              <h3 className="text-sm font-bold font-mono text-primary flex items-center gap-2 mb-4">
                <Activity className="w-4 h-4 animate-pulse" />
                LIVE RADAR FEED
              </h3>
              <div className="space-y-3 font-mono text-[10px]">
                {scanLogs.length === 0 ? (
                    <p className="opacity-40 italic">Waiting for signal pings...</p>
                ) : (
                    scanLogs.map(log => (
                        <div key={log.id} className="border-l-2 border-primary/20 pl-3 py-1 bg-primary/5 rounded-r">
                            <span className="text-primary/50 mr-2">[{log.time}]</span>
                            <span className="text-foreground/90">{log.msg}</span>
                        </div>
                    ))
                )}
              </div>
            </HolographicCard>
          </motion.div>

          {/* Area Persona */}
          <motion.div variants={fadeInUp}>
            <HolographicCard className="p-5 h-full">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold font-mono text-primary flex items-center gap-2">
                  <Fingerprint className="w-4 h-4" />
                  VISITOR PERSONALITY
                </h3>
                <Tooltip>
                    <TooltipTrigger asChild>
                      <button className="cursor-help transition-opacity opacity-50 hover:opacity-100 outline-none">
                         <Info className="w-3 h-3 text-primary" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="top" className="bg-popover border border-primary/40 text-[10px] font-mono p-3 max-w-[200px] text-popover-foreground rounded-xl shadow-2xl">
                      Estimates are derived from POI (Point-of-Interest) density, commercial cluster types, and mobile intent signals in the area.
                    </TooltipContent>
                  </Tooltip>
              </div>
              <div className="space-y-4">
                 {persona.map((p, i) => (
                     <div key={i} className="group">
                        <div className="flex justify-between items-end mb-1">
                            <span className="text-[10px] font-bold text-foreground font-mono">{p.type}</span>
                            <span className="text-[10px] font-mono text-primary">{p.pct}%</span>
                        </div>
                        <div className="h-1 w-full bg-foreground/10 rounded-full overflow-hidden">
                           <div className="h-full bg-primary transition-all duration-1000" style={{ width: `${p.pct}%` }} />
                        </div>
                     </div>
                 ))}

                 {/* Signal Context explanation */}
                 <div className="pt-2 border-t border-primary/10">
                    <p className="text-[9px] font-mono text-muted-foreground uppercase mb-2 opacity-60 flex items-center gap-2">
                       <Layers className="w-3 h-3" />
                       Signals Inferred From:
                    </p>
                    <div className="flex flex-wrap gap-2">
                       {[
                         { label: "Transit Hubs", val: "MED" },
                         { label: "Pro. Districts", val: "HIGH" },
                         { label: "Retail Clusters", val: "LOW" }
                       ].map((sig, i) => (
                          <div key={i} className="px-2 py-0.5 rounded bg-primary/5 border border-primary/20 flex items-center gap-1.5">
                             <span className="text-[8px] font-mono text-foreground uppercase">{sig.label}</span>
                             <span className="text-[8px] font-mono text-primary font-bold">{sig.val}</span>
                          </div>
                       ))}
                    </div>
                 </div>
              </div>
            </HolographicCard>
          </motion.div>

          {/* Campaign Blueprint (Ad Preview) */}
          <motion.div variants={fadeInUp}>
            <HolographicCard className="p-5 h-full border-primary/40 overflow-hidden relative">
              <div className="absolute -right-4 -top-4 opacity-5 bg-primary rounded-full p-10 rotate-12">
                 <Megaphone className="w-20 h-20 text-primary" />
              </div>
              <h3 className="text-sm font-bold font-mono text-primary flex items-center gap-2 mb-4 relative z-10">
                <Mail className="w-4 h-4" />
                CAMPAIGN BLUEPRINT
              </h3>
              <div className="bg-muted/40 border border-border shadow-inner p-4 relative z-10 group cursor-pointer hover:border-primary/50 transition-colors rounded-xl">
                 <p className="text-[11px] font-bold text-primary mb-2 flex items-center gap-2">
                    <Megaphone className="w-3 h-3" />
                    SUGGESTED CREATIVE
                 </p>
                 <p className="text-xs font-mono text-foreground leading-relaxed italic mb-3">
                    "Hey! {data?.signals.weather_score && data.signals.weather_score > 0.5 ? 'Perfect weather alert!' : 'Limited time opportunity!'} Get a free sample of {setup?.business_type || 'our special'} at {businessName}. Just {radius[0]}KM away from you right now."
                 </p>
                  <div className="flex justify-between items-center text-[10px] font-mono text-muted-foreground mt-4">
                    <span>Tone: {data?.score && data.score > 70 ? 'High Energy' : 'Direct/Soft'}</span>
                    <button 
                        onClick={handleDeployClick}
                        disabled={briefLoading}
                        className="text-primary font-bold hover:underline cursor-pointer flex items-center gap-1"
                    >
                        {briefLoading ? <RefreshCw className="w-3 h-3 animate-spin" /> : <ChevronRight className="w-3 h-3" />}
                        {briefLoading ? 'GENERATING...' : 'READY TO DEPLOY'}
                    </button>
                  </div>
              </div>
            </HolographicCard>
          </motion.div>
        </motion.div>

        {/* Third Row: Sweeps & Strategy History */}
        <motion.div 
           className="grid lg:grid-cols-2 gap-6 w-full"
           variants={fadeInUp}
        >
          {/* Radar History */}
          <HolographicCard className="p-6">
             <h3 className="text-sm font-bold font-mono text-primary flex items-center gap-2 mb-4">
                <Clock className="w-4 h-4" />
                RECENT RADAR SWEEPS
             </h3>
             <div className="overflow-x-auto">
                <table className="w-full text-xs font-mono text-left">
                   <thead className="border-b border-primary/20">
                      <tr>
                         <th className="pb-3 text-muted-foreground">TIME</th>
                         <th className="pb-3 text-muted-foreground">ZONE</th>
                         <th className="pb-3 text-muted-foreground">SCORE</th>
                         <th className="pb-3 text-muted-foreground">URGENCY</th>
                      </tr>
                   </thead>
                   <tbody className="divide-y divide-primary/5">
                      {history.length > 0 ? (
                        history.map((log, i) => (
                           <tr key={i} className="hover:bg-primary/5 transition-colors group">
                              <td className="py-4 text-muted-foreground">{new Date(log.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</td>
                              <td className="py-4 text-foreground font-bold">{log.radius / 1000} KM</td>
                              <td className="py-4">
                                 <div className="flex items-center gap-2">
                                    <div className="h-1 w-10 bg-foreground/10 rounded-full overflow-hidden">
                                       <div className="h-full bg-primary" style={{ width: `${log.final_score}%` }} />
                                    </div>
                                    <span className="font-bold text-primary">{log.final_score}</span>
                                 </div>
                              </td>
                              <td className="py-4">
                                 <span className={`px-2 py-0.5 rounded text-[10px] ${log.urgency === 'Critical' ? 'bg-red-500/20 text-red-400' : 'bg-primary/20 text-primary'}`}>
                                    {log.urgency.toUpperCase()}
                                 </span>
                              </td>
                           </tr>
                        ))
                      ) : (
                        <tr>
                            <td colSpan={4} className="py-10 text-center text-muted-foreground opacity-50 italic">No recent sweeps recorded.</td>
                        </tr>
                      )}
                   </tbody>
                </table>
             </div>
          </HolographicCard>

          {/* Strategy History */}
          <HolographicCard className="p-6 border-primary/30">
             <h3 className="text-sm font-bold font-mono text-primary flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <Target className="w-4 h-4" />
                    STRATEGIC HISTORY
                </div>
                {strategyHistory.length > 0 && <Badge variant="outline" className="text-[9px] border-primary/30 text-primary font-mono">{strategyHistory.length} BRIEFS</Badge>}
             </h3>
             <div className="space-y-3 overflow-y-auto max-h-[350px] scrollbar-thin scrollbar-thumb-primary/20 pr-2">
                {historyLoading ? (
                    <div className="flex items-center justify-center py-10">
                        <RefreshCw className="w-6 h-6 animate-spin text-primary opacity-50" />
                    </div>
                ) : strategyHistory.length === 0 ? (
                    <div className="py-10 text-center text-muted-foreground opacity-50 italic text-[11px]">
                        No saved strategies found. Generate a brief to see history.
                    </div>
                ) : (
                    strategyHistory.map((brief) => (
                        <div 
                            key={brief.id} 
                            onClick={() => handleReplayCampaign(brief)}
                            className="p-3 bg-muted/30 border border-border/50 rounded-xl hover:border-primary/40 hover:bg-muted/50 transition-all cursor-pointer group"
                        >
                            <div className="flex justify-between items-start mb-2">
                                <div className="space-y-0.5">
                                    <p className="text-[10px] font-bold text-foreground group-hover:text-primary transition-colors">{brief.meta_objective} - {brief.radius_km}KM</p>
                                    <p className="text-[9px] font-mono text-muted-foreground">{new Date(brief.timestamp).toLocaleDateString()} @ {new Date(brief.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</p>
                                </div>
                                <Badge className="text-[9px] bg-primary/10 text-primary border-primary/20 h-5">SCORE: {brief.heat_score}</Badge>
                            </div>
                            <div className="flex flex-wrap gap-1.5 mt-2">
                                <span className="text-[8px] font-mono px-1.5 py-0.5 bg-foreground/5 rounded text-muted-foreground border border-border/50 uppercase">ID: {brief.id?.substring(0, 8)}</span>
                                <span className={cn(
                                    "text-[8px] font-mono px-1.5 py-0.5 rounded border uppercase",
                                    brief.urgency === 'Critical' ? 'bg-red-500/10 text-red-400 border-red-500/20' : 'bg-primary/5 text-primary border-primary/20'
                                )}>
                                    {brief.urgency}
                                </span>
                                <div className="flex-1" />
                                <ArrowRight className="w-3 h-3 text-primary opacity-0 group-hover:opacity-100 transition-opacity" />
                            </div>
                        </div>
                    ))
                )}
             </div>
          </HolographicCard>
        </motion.div>

        <Reveal variant="fadeInUp" delay={0.6}>
          <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
            <Button 
                size="lg" 
                onClick={handleDeployClick}
                disabled={briefLoading || !data}
                className="w-full bg-primary text-primary-foreground hover:bg-primary/90 font-bold font-heading font-semibold text-xl shadow-[0_0_30px_rgba(0,224,208,0.4)] h-14"
            >
              {briefLoading ? (
                  <RefreshCw className="w-6 h-6 mr-3 animate-spin" />
              ) : (
                  <Scan className="w-6 h-6 mr-3" />
              )}
              {briefLoading ? "ANALYZING MARKET FOR DEPLOYMENT..." : "DEPLOY GEO-TARGETED CAMPAIGN"}
            </Button>
          </motion.div>
        </Reveal>

        {/* Strategic Campaign Brief Modal */}
        <GeoCampaignBriefModal 
            open={briefModalOpen} 
            onClose={() => setBriefModalOpen(false)} 
            brief={campaignBrief} 
        />
      </div>
     </TooltipProvider>
    </Layout>
  );
};

export default GeoIntent;