import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import { motion, AnimatePresence } from "framer-motion";
import { 
  MapPin, Target, TrendingUp, Users, Globe, Radar, 
  Scan, RefreshCw, Layers, Info, Map as MapIcon,
  Activity, Fingerprint, Calendar, Mail, Megaphone, Clock, MapPinned,
  ChevronRight, ArrowRight, Loader2, X
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
import { geoIntentService, HeatScoreResponse, HeatmapResponse, CampaignLogEntry, CampaignBrief, ZoneResult } from "@/services/geoIntentService";
import GeoIntentMap, { GeoIntentMapRef } from "@/components/GeoIntentMap";
import GeoCampaignBriefModal from "@/components/GeoCampaignBriefModal";
import MetaDeployModal from "@/components/MetaDeployModal";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { getErrorMessage } from "@/utils/errorHandler";
import { useAuth } from "@/hooks/useAuth";
import { apiClient } from "@/services/api";

/** Stable id so loading toast updates in place (success/error). */
const FIND_ZONES_TOAST_ID = "geo-intent-find-zones";

const GEO_ZONE_CACHE_KEY = "raamp_geo_top_zones_cache_v1";

function readZoneCache(): {
  business_id: string;
  radius_m: number;
  timestamp: string;
  zones: ZoneResult[];
} | null {
  try {
    const raw = localStorage.getItem(GEO_ZONE_CACHE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") return null;
    if (!Array.isArray((parsed as any).zones)) return null;
    return parsed as any;
  } catch {
    return null;
  }
}

function writeZoneCache(payload: {
  business_id: string;
  radius_m: number;
  timestamp: string;
  zones: ZoneResult[];
}) {
  try {
    localStorage.setItem(GEO_ZONE_CACHE_KEY, JSON.stringify(payload));
  } catch {
    // ignore
  }
}

/** Maps API status strings to UI — free tier uses `limited` for trends/weather. */
function signalUi(status: string | undefined) {
  const s = (status || "").toLowerCase();
  if (s === "ok") {
    return { dot: "bg-primary shadow-[0_0_8px_rgba(0,224,208,0.8)]", label: "ACTIVE", bar: "bg-primary" };
  }
  if (s === "limited") {
    return { dot: "bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.6)]", label: "PLAN", bar: "bg-amber-500/80" };
  }
  return { dot: "bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)]", label: "DEGRADED", bar: "bg-red-500" };
}

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

function sanitizeCaptionNoDashes(raw: string): string {
  // Convert dash-bullets to dot-bullets and remove lone leading dashes.
  // Keeps hyphenated words (e.g. "end-to-end") intact by only targeting line-start bullets.
  return String(raw || "")
    .split("\n")
    .map((line) => {
      const l = line.replace(/\s+$/g, "");
      if (/^\s*-\s+/.test(l)) return l.replace(/^\s*-\s+/, "• ");
      if (/^\s*-\s*$/.test(l)) return "";
      return l;
    })
    .filter((l) => l.trim().length > 0)
    .join("\n");
}

type AreaCacheEntry = { label: string; updated_at: number };
const GEO_AREA_CACHE_KEY = "raamp_geo_area_cache_v1";

function coordKey(lat: number, lng: number) {
  // Round to reduce cache fragmentation but keep neighborhood-level accuracy.
  return `${lat.toFixed(4)},${lng.toFixed(4)}`;
}

function readAreaCache(): Record<string, AreaCacheEntry> {
  try {
    const raw = localStorage.getItem(GEO_AREA_CACHE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" ? (parsed as any) : {};
  } catch {
    return {};
  }
}

function writeAreaCache(cache: Record<string, AreaCacheEntry>) {
  try {
    localStorage.setItem(GEO_AREA_CACHE_KEY, JSON.stringify(cache));
  } catch {
    // ignore
  }
}

async function reverseGeocodeAreaLabel(lat: number, lng: number): Promise<string | null> {
  // Best-effort: uses Google Maps JS Geocoder if available.
  // If Maps key/script isn’t available, we return null.
  const g = (window as any)?.google;
  if (!g?.maps?.Geocoder) return null;

  const geocoder = new g.maps.Geocoder();
  const result: any = await new Promise((resolve) => {
    geocoder.geocode({ location: { lat, lng } }, (results: any, status: string) => {
      if (status !== "OK" || !results?.length) return resolve(null);
      resolve(results[0]);
    });
  });
  if (!result) return null;

  // Prefer neighborhood-ish labels.
  const comps: any[] = Array.isArray(result.address_components) ? result.address_components : [];
  const pick = (types: string[]) =>
    comps.find((c) => Array.isArray(c.types) && types.every((t) => c.types.includes(t)))?.long_name;

  const neighborhood =
    pick(["neighborhood"]) ||
    pick(["sublocality", "sublocality_level_1"]) ||
    pick(["locality"]) ||
    pick(["administrative_area_level_2"]) ||
    pick(["administrative_area_level_1"]);

  const country = pick(["country"]);
  const label = [neighborhood, country].filter(Boolean).join(", ");
  return label || null;
}

const GeoIntent = () => {
  const { user } = useAuth();
  const [showSignalBanner, setShowSignalBanner] = useState(() => {
    try {
      return localStorage.getItem("raamp_hide_signal_banner") !== "1";
    } catch {
      return true;
    }
  });
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
  const [recommendedZones, setRecommendedZones] = useState<ZoneResult[]>([]);
  const [zoneScanMeta, setZoneScanMeta] = useState<{ radius_m: number; timestamp: string } | null>(null);
  const [zonesLoading, setZonesLoading] = useState(false);
  const mapRef = useRef<GeoIntentMapRef>(null);
  const skipRadiusDebounceOnce = useRef(true);
  const [deployZone, setDeployZone] = useState<ZoneResult | null>(null);
  const [deployBrief, setDeployBrief] = useState<CampaignBrief | null>(null);
  const [fbPages, setFbPages] = useState<Array<{ id: string; name?: string | null }>>([]);
  const [selectedPageId, setSelectedPageId] = useState<string | null>(null);

  const [areaLabels, setAreaLabels] = useState<Record<string, AreaCacheEntry>>(() => readAreaCache());
  const pendingAreaKeys = useRef<Set<string>>(new Set());

  const getAreaLabel = useCallback((lat?: number, lng?: number) => {
    if (typeof lat !== "number" || typeof lng !== "number") return null;
    const key = coordKey(lat, lng);
    return areaLabels[key]?.label || null;
  }, [areaLabels]);

  const formatLatLngShort = useCallback((lat?: number, lng?: number) => {
    if (typeof lat !== "number" || typeof lng !== "number") return null;
    const ns = lat >= 0 ? "N" : "S";
    const ew = lng >= 0 ? "E" : "W";
    return `${Math.abs(lat).toFixed(2)}°${ns}, ${Math.abs(lng).toFixed(2)}°${ew}`;
  }, []);

  const getAreaDisplay = useCallback(
    (lat?: number, lng?: number) => getAreaLabel(lat, lng) || formatLatLngShort(lat, lng),
    [getAreaLabel, formatLatLngShort]
  );

  const ensureAreaLabel = useCallback(async (lat: number, lng: number) => {
    const key = coordKey(lat, lng);
    if (areaLabels[key]?.label) return;
    if (pendingAreaKeys.current.has(key)) return;
    pendingAreaKeys.current.add(key);
    try {
      const label = await Promise.race<string | null>([
        reverseGeocodeAreaLabel(lat, lng),
        new Promise<null>((resolve) => setTimeout(() => resolve(null), 3000)),
      ]);
      if (!label) return;
      setAreaLabels((prev) => {
        if (prev[key]?.label) return prev;
        const next = { ...prev, [key]: { label, updated_at: Date.now() } };
        writeAreaCache(next);
        return next;
      });
    } finally {
      pendingAreaKeys.current.delete(key);
    }
  }, [areaLabels]);

  const personaValidity = useMemo(() => {
    const list = Array.isArray(persona) ? persona : [];
    const cleaned = list
      .map((p) => ({ type: String(p?.type || "").trim(), pct: Number(p?.pct ?? 0) || 0 }))
      .filter((p) => p.type && p.pct > 0);
    if (cleaned.length < 2) return { valid: false, reason: "insufficient" as const };
    const sum = cleaned.reduce((a, b) => a + b.pct, 0);
    const max = Math.max(...cleaned.map((p) => p.pct));
    if (max >= 95) return { valid: false, reason: "single_dominant" as const };
    if (sum < 80 || sum > 120) return { valid: false, reason: "sum_off" as const };
    return { valid: true, reason: null as any };
  }, [persona]);

  const topPersonaSummary = useMemo(() => {
    if (!personaValidity.valid) return null;
    const sorted = [...persona].sort((a, b) => b.pct - a.pct);
    const top = sorted[0];
    if (!top) return null;
    return `${top.type} ${top.pct}%`;
  }, [persona, personaValidity.valid]);

  const tier = (user as any)?.subscriptionTier || "free";
  const isPremium = String(tier).toLowerCase() === "premium";

  const latestBrief = campaignBrief || (strategyHistory.length > 0 ? strategyHistory[0] : null);

  const heuristicCaption = useMemo(() => {
    const centerLat = setup?.latitude;
    const centerLng = setup?.longitude;
    const area = getAreaDisplay(
      typeof centerLat === "number" ? centerLat : undefined,
      typeof centerLng === "number" ? centerLng : undefined
    );

    const sig = ((data as any)?.signals || {}) as any;
    const st = ((data as any)?.signals_status || {}) as any;
    const placesOk = String(st?.places || "ok").toLowerCase() === "ok";
    const trendsOk = String(st?.trends || "ok").toLowerCase() === "ok";
    const weatherOk = String(st?.weather || "ok").toLowerCase() === "ok";

    const places = Number(sig?.places_score ?? 0) || 0;
    const trends = Number(sig?.trends_score ?? 0) || 0;
    const weather = Number(sig?.weather_score ?? 0) || 0;

    const candidates: Array<{ k: "places" | "trends" | "weather"; v: number; ok: boolean }> = [
      { k: "places", v: places, ok: placesOk },
      { k: "trends", v: trends, ok: trendsOk },
      { k: "weather", v: weather, ok: weatherOk },
    ];

    // Prefer signals that are actually healthy.
    const dominant =
      [...candidates]
        .filter((c) => c.ok)
        .sort((a, b) => b.v - a.v)[0] ||
      [...candidates].sort((a, b) => b.v - a.v)[0] ||
      { k: "places" as const, v: 0, ok: false };

    const km = radius?.[0] ?? 10;
    const businessType = String(setup?.business_type || "").trim();
    const offer =
      businessType.toLowerCase().includes("fashion") || businessType.toLowerCase().includes("clothing")
        ? "new arrivals"
        : businessType
          ? businessType
          : "today’s offer";

    const personaHint = topPersonaSummary ? ` Built for ${topPersonaSummary}.` : "";

    if (dominant.k === "places") {
      return `High local foot traffic detected${area ? ` near ${area}` : ""}. ${businessName} is optimized for walk-ins within ${km}km — promote ${offer} with a clear “visit now” CTA.${personaHint}`;
    }
    if (dominant.k === "trends") {
      return `Search interest is trending up${area ? ` around ${area}` : ""}. Run a short, direct creative within ${km}km and anchor it with your strongest offer (${offer}).${personaHint}`;
    }
    if (dominant.k === "weather") {
      return `Conditions look favorable for going out${area ? ` near ${area}` : ""}. Keep the message simple: highlight ${offer} and drive immediate walk-ins within ${km}km.${personaHint}`;
    }
    return `Run a simple local offer within ${km}km and optimize for walk-ins. Lead with what’s verifiable on-ground (places density) and keep claims conservative.${personaHint}`;
  }, [data?.signals, data?.signals_status, setup?.latitude, setup?.longitude, setup?.business_type, businessName, radius, topPersonaSummary, getAreaDisplay]);

  const previewCaption =
    sanitizeCaptionNoDashes(
      latestBrief?.caption ||
      latestBrief?.caption_variants?.aggressive ||
      latestBrief?.caption_variants?.urgency ||
      heuristicCaption
    );

  const status = data?.signals_status;
  const hasAnySignalIssues =
    Boolean(status) &&
    (status?.trends !== "ok" || status?.places !== "ok" || status?.weather !== "ok");
  const hasLimitedSignals =
    Boolean(status) &&
    (String(status?.trends).toLowerCase() === "limited" ||
      String(status?.places).toLowerCase() === "limited" ||
      String(status?.weather).toLowerCase() === "limited");
  const signalMsg = hasLimitedSignals
    ? isPremium
      ? "One or more sources are limited (quota/rate limits). The score blends what we could fetch — ~50% often means neutral fallback, not weak market."
      : "One or more sources are limited (free plan limits, API quota, or rate limits). The score blends what we could fetch — ~50% often means neutral fallback, not weak market."
    : "One or more sources are unavailable (API key missing, quota/rate limits, or upstream outage). The score blends what we could fetch — ~50% often means neutral fallback, not weak market.";

  const fetchSetup = async () => {
    try {
      const response = await businessService.getHyperlocalSetup();
      if (response && response.business_name) {
        setSetup(response);
        setBusinessName(response.business_name);
        return response;
      }
    } catch (e: unknown) {
      const status = (e as { status?: number })?.status;
      // Backend returns 404 when no business / hyperlocal row exists — expected until onboarding is done.
      if (status === 404) {
        return null;
      }
      console.error("Failed to fetch setup", e);
      toast.error("Profile sync failed. Check your network connection.");
    }
    return null;
  };

  const fetchFacebookPages = useCallback(async () => {
    try {
      const resp = await apiClient.get<{ connected: boolean; details?: { fb_pages?: Array<{ id: string; name?: string | null }> } }>(
        "/profile/connections/facebook"
      );
      const pages = Array.isArray(resp?.details?.fb_pages) ? resp.details!.fb_pages! : [];
      setFbPages(pages);
      if (!selectedPageId) {
        const first = pages[0]?.id;
        setSelectedPageId(first || null);
      }
    } catch {
      setFbPages([]);
    }
  }, [selectedPageId]);

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
      
      // Restore Top Zones from cache if they match current business (preserve zones during refresh)
      const cached = readZoneCache();
      if (
        cached &&
        cached.business_id === businessId &&
        Array.isArray(cached.zones) &&
        cached.zones.length > 0
      ) {
        setRecommendedZones(cached.zones);
        setZoneScanMeta({ radius_m: cached.radius_m, timestamp: cached.timestamp });
      }
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

  const handleRecommendZones = async () => {
    if (zonesLoading) return;

    const activeSetup = setup;
    const nameForId = activeSetup?.business_name || businessName;
    const businessId = resolveGeoBusinessId(activeSetup, nameForId);
    const keywords = activeSetup?.business_type
      ? [activeSetup.business_type, "business", "store"]
      : ["coffee", "cafe", "espresso"];
    const lat = activeSetup?.latitude ?? 33.7215;
    const lng = activeSetup?.longitude ?? 73.0433;

    setZonesLoading(true);
    toast.loading("Finding best zones… scoring compass points (can take 1–2 min).", {
      id: FIND_ZONES_TOAST_ID,
      duration: 600_000,
    });
    try {
      const result = await geoIntentService.recommendZones({
        business_id: businessId,
        keywords,
        latitude: lat,
        longitude: lng,
        radius: radius[0] * 1000,
        is_indoor: true,
      });
      const zones = Array.isArray(result?.zones) ? result.zones : [];
      setRecommendedZones(zones);
      // Resolve friendly area labels in background.
      zones.forEach((z) => {
        ensureAreaLabel(z.latitude, z.longitude).catch(() => {});
      });
      setZoneScanMeta({
        radius_m: radius[0] * 1000,
        timestamp: result?.timestamp || new Date().toISOString(),
      });
      writeZoneCache({
        business_id: businessId,
        radius_m: radius[0] * 1000,
        timestamp: result?.timestamp || new Date().toISOString(),
        zones,
      });
      toast.success(`Ranked ${result.zones.length} high-intent zones around your scan radius.`, {
        id: FIND_ZONES_TOAST_ID,
      });
    } catch (e: unknown) {
      toast.error(getErrorMessage(e), { id: FIND_ZONES_TOAST_ID });
    } finally {
      setZonesLoading(false);
    }
  };

  const handleDeployZone = async (zone: ZoneResult) => {
    if (briefLoading) return;
    setBriefLoading(true);
    setCampaignBrief(null);
    setBriefModalOpen(true);
    toast.loading("Generating brief for this zone…", { id: "geo-brief" });
    try {
      const keywords = setup?.business_type
        ? [setup.business_type, "business", "store"]
        : ["coffee", "cafe", "espresso"];
      const nameForId = setup?.business_name || businessName;
      const businessId = resolveGeoBusinessId(setup, nameForId);

      const brief = await geoIntentService.generateCampaignBrief({
        lat: zone.latitude,
        lng: zone.longitude,
        radius_km: radius[0],
        heat_score: zone.score,
        urgency: zone.urgency ?? "Medium",
        trends_score: (zone.signals?.trends_score ?? 0) * 100,
        weather_score: (zone.signals?.weather_score ?? 0) * 100,
        places_score: (zone.signals?.places_score ?? 0) * 100,
        reasoning: zone.reason,
        persona_split: data?.persona_split || [],
        keywords,
        business_id: businessId,
      });

      setCampaignBrief(brief);
      toast.success(`Brief ready for zone ${zone.label}.`, { id: "geo-brief" });
      fetchStrategyHistory();
    } catch (err) {
      console.error("Brief generation failed:", err);
      toast.error(getErrorMessage(err), { id: "geo-brief" });
      setBriefModalOpen(false);
    } finally {
      setBriefLoading(false);
    }
  };

  const handleMetaDeployOpen = async (zone: ZoneResult) => {
    if (briefLoading) return;
    setDeployZone(zone);
    setDeployBrief(null);
    await fetchFacebookPages();
    setBriefLoading(true);
    toast.loading("Preparing Meta deploy brief…", { id: "meta-deploy-brief" });
    try {
      const keywords = setup?.business_type
        ? [setup.business_type, "business", "store"]
        : ["coffee", "cafe", "espresso"];
      const nameForId = setup?.business_name || businessName;
      const businessId = resolveGeoBusinessId(setup, nameForId);

      const brief = await geoIntentService.generateCampaignBrief({
        lat: zone.latitude,
        lng: zone.longitude,
        radius_km: radius[0],
        heat_score: zone.score,
        urgency: zone.urgency ?? "Medium",
        trends_score: (zone.signals?.trends_score ?? 0) * 100,
        weather_score: (zone.signals?.weather_score ?? 0) * 100,
        places_score: (zone.signals?.places_score ?? 0) * 100,
        reasoning: zone.reason,
        persona_split: data?.persona_split || [],
        keywords,
        business_id: businessId,
      });

      setDeployBrief(brief);
      toast.success("Meta deploy ready.", { id: "meta-deploy-brief" });
    } catch (err) {
      toast.error(getErrorMessage(err), { id: "meta-deploy-brief" });
      setDeployZone(null);
    } finally {
      setBriefLoading(false);
    }
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
            urgency: data.urgency ?? "Medium",
            trends_score: (data.signals?.trends_score ?? 0) * 100,
            weather_score: (data.signals?.weather_score ?? 0) * 100,
            places_score: (data.signals?.places_score ?? 0) * 100,
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
      // Restore last Top Zones (if it matches current business + radius).
      const nameForId = activeSetup?.business_name || businessName;
      const bid = resolveGeoBusinessId(activeSetup, nameForId);
      const cached = readZoneCache();
      if (
        cached &&
        cached.business_id === bid &&
        Array.isArray(cached.zones) &&
        cached.zones.length > 0
      ) {
        setRecommendedZones(cached.zones);
        setZoneScanMeta({ radius_m: cached.radius_m, timestamp: cached.timestamp });
        cached.zones.forEach((z) => {
          ensureAreaLabel(z.latitude, z.longitude).catch(() => {});
        });
      }
      await fetchData(activeSetup);
      
      if (activeSetup) {
          try {
              const nameForId = activeSetup.business_name || businessName;
              const bid = resolveGeoBusinessId(activeSetup, nameForId);
              const hist = await geoIntentService.getHistory(bid);
              const rawLogs = Array.isArray(hist?.logs) ? hist.logs : [];
              const sorted = [...rawLogs].sort((a, b) => {
                const at = Number(new Date(a.timestamp).getTime());
                const bt = Number(new Date(b.timestamp).getTime());
                return (Number.isNaN(bt) ? 0 : bt) - (Number.isNaN(at) ? 0 : at);
              });

              // De-dupe repeats (common during demo runs / replays)
              const seen = new Set<string>();
              const deduped = sorted.filter((log) => {
                const t = new Date(log.timestamp);
                const bucket = Number.isNaN(t.getTime())
                  ? String(log.timestamp)
                  : t.toISOString().slice(0, 16); // minute-bucket
                const key = `${bucket}|${log.radius}|${log.final_score}|${log.urgency ?? ""}`;
                if (seen.has(key)) return false;
                seen.add(key);
                return true;
              });

              setHistory(deduped.slice(0, 12));
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
      const nextLogs = Array.isArray(data.radar_feed) ? data.radar_feed : [];
      // Add actionable system notes about signal quality (trust-critical).
      const status = data?.signals_status as any;
      if (status) {
        const bad = ["trends", "places", "weather"]
          .filter((k) => String(status?.[k] || "").toLowerCase() !== "ok")
          .map((k) => `${k.toUpperCase()}: ${String(status?.[k] || "UNKNOWN").toUpperCase()}`);
        if (bad.length) {
          nextLogs.unshift({
            id: `sig-${Date.now()}`,
            time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
            msg: `Signal quality: ${bad.join(" • ")}. Score may be conservative.`,
            type: "alert",
          });
        }
      }

      setScanLogs(nextLogs.slice(0, 14));

      const split = Array.isArray(data.persona_split) ? data.persona_split : [];
      setPersona(split);
    }
  }, [data]);

  // Reverse geocode strategic history brief locations (for human-readable history rows).
  useEffect(() => {
    const list = Array.isArray(strategyHistory) ? strategyHistory : [];
    list.slice(0, 20).forEach((b) => {
      const lat = b?.location?.coordinates?.[1];
      const lng = b?.location?.coordinates?.[0];
      if (typeof lat === "number" && typeof lng === "number") {
        ensureAreaLabel(lat, lng).catch(() => {});
      }
    });
  }, [strategyHistory, ensureAreaLabel]);

  // Debounced re-fetch when radius changes (skip once after initial load — init already scanned)
  useEffect(() => {
    if (!loading && !refreshing) {
      localStorage.setItem("geointent_radius", radius[0].toString());
      if (skipRadiusDebounceOnce.current) {
        skipRadiusDebounceOnce.current = false;
        return;
      }
      const timer = setTimeout(() => {
        fetchData();
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [radius, loading, refreshing, fetchData]);

  return (
    <Layout>
      <TooltipProvider delayDuration={100}>
        <div className="space-y-8">
        {data && hasAnySignalIssues && showSignalBanner && (
          <Alert className="border-amber-500/40 bg-amber-500/10 text-foreground relative pr-10">
            <Radar className="h-4 w-4 text-amber-600" />
            <AlertTitle className="text-amber-900 dark:text-amber-100">Signal quality</AlertTitle>
            <AlertDescription className="text-sm text-amber-950/90 dark:text-amber-50/90">
              {signalMsg}
            </AlertDescription>
            <button
              type="button"
              className="absolute right-2 top-2 inline-flex h-7 w-7 items-center justify-center rounded-md border border-amber-500/30 bg-background/40 hover:bg-background/70"
              onClick={() => {
                setShowSignalBanner(false);
                try {
                  localStorage.setItem("raamp_hide_signal_banner", "1");
                } catch {
                  // ignore
                }
              }}
              aria-label="Dismiss signal quality banner"
            >
              <X className="h-4 w-4 text-amber-700 dark:text-amber-300" aria-hidden />
            </button>
          </Alert>
        )}

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
                size="sm"
                onClick={handleRecommendZones}
                disabled={loading || refreshing || zonesLoading}
                aria-busy={zonesLoading}
                className="bg-card border-primary/30 text-primary hover:bg-primary/20 font-mono text-[10px] hidden md:flex min-w-[9rem]"
              >
                {zonesLoading ? (
                  <Loader2 className="w-3 h-3 mr-2 animate-spin shrink-0" aria-hidden />
                ) : (
                  <Layers className="w-3 h-3 mr-2 shrink-0" aria-hidden />
                )}
                {zonesLoading ? "SCANNING…" : "FIND BEST ZONES"}
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
                  <div
                    className={`w-2 h-2 rounded-full animate-pulse ${
                      zonesLoading ? "bg-amber-500" : refreshing ? "bg-amber-500" : "bg-primary"
                    }`}
                  />
                  {zonesLoading
                    ? "RANKING ZONES…"
                    : refreshing
                      ? "SYNCING LIVE INTENT"
                      : "LIVE DATA SCANNING"}
                </div>
              </div>

              {/* Functional Map View */}
              <div className="h-[360px] md:h-[420px] lg:h-[520px] bg-background/60 rounded border border-border/50 mb-6 relative overflow-hidden group">
                <GeoIntentMap 
                  ref={mapRef}
                  center={{ lat: setup?.latitude || 33.7215, lng: setup?.longitude || 73.0433 }}
                  radiusMeters={radius[0] * 1000}
                  heatmapData={heatmapData}
                  zonePins={recommendedZones.map((z) => ({
                    lat: z.latitude,
                    lng: z.longitude,
                    label: z.label,
                  }))}
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
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-amber-500 shadow-[0_0_6px_rgba(245,158,11,0.6)]" />
                    <span className="text-[10px] font-mono text-foreground font-bold tracking-tighter uppercase">Recommended zone</span>
                  </div>
                </div>

                {loading && !data && (
                  <div className="absolute inset-0 z-20 flex items-center justify-center bg-background/40 pointer-events-none">
                    <div className="px-4 py-2 bg-background/95 border border-primary/40 rounded-full flex items-center gap-2 shadow-[0_0_20px_rgba(0,224,208,0.2)]">
                      <Radar className="w-4 h-4 text-primary animate-pulse" />
                      <span className="text-[11px] font-mono text-primary font-bold tracking-widest uppercase">
                        Running radar scan…
                      </span>
                    </div>
                  </div>
                )}
                {zonesLoading && (
                  <div className="absolute inset-0 z-[25] flex items-center justify-center bg-background/55 backdrop-blur-[2px]">
                    <div className="mx-3 max-w-sm rounded-lg border border-amber-500/40 bg-card/95 px-4 py-3 shadow-lg flex flex-col items-center gap-2 text-center pointer-events-none">
                      <Loader2 className="h-8 w-8 text-amber-500 animate-spin" aria-hidden />
                      <p className="text-xs font-mono font-bold text-foreground uppercase tracking-wide">
                        Finding best zones…
                      </p>
                      <p className="text-[10px] font-mono text-muted-foreground leading-snug">
                        Scoring several directions in parallel. Please wait — do not click again.
                      </p>
                    </div>
                  </div>
                )}
                {!loading && data && heatmapData.length === 0 && (
                  <div className="absolute bottom-3 left-3 right-3 z-10 pointer-events-none">
                    <div className="px-3 py-2 bg-card/95 border border-border/60 rounded-lg text-[10px] font-mono text-muted-foreground text-center">
                      Heatmap dots appear as we accumulate saved scans. Your heat score above is from this run.
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
                    type="button"
                    variant="outline"
                    onClick={handleRecommendZones}
                    disabled={zonesLoading || loading || refreshing}
                    aria-busy={zonesLoading}
                    className="w-full border-amber-500/40 text-amber-700 dark:text-amber-300 hover:bg-amber-500/10 font-mono font-bold tracking-wider h-12"
                  >
                    {zonesLoading ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin shrink-0" aria-hidden />
                    ) : (
                      <Layers className="w-4 h-4 mr-2 shrink-0" aria-hidden />
                    )}
                    {zonesLoading ? "SCANNING ZONES…" : "FIND BEST ZONES"}
                  </Button>
                </motion.div>
                <p className="text-[10px] text-muted-foreground font-mono">
                  Tip: adjust the radius slider or use Find Best Zones to explore intent.
                </p>
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
                  ) : (data || recommendedZones.length > 0) ? (
                    <>
                      {data && (
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
                      {data.signals && data.signals_status ? [
                        { name: "Regional Intent", score: data.signals.trends_score, status: data.signals_status.trends, desc: "Macro search volume for your business type at a regional/city level." },
                        { name: "Local Density", score: data.signals.places_score, status: data.signals_status.places, desc: "Hyper-local physical commercial activity in your exact search radius." },
                        { name: "Weather Boost", score: data.signals.weather_score, status: data.signals_status.weather, desc: "Real-time weather favorability for target audience mobility." }
                      ].map((signal, idx) => {
                        const sui = signalUi(signal.status);
                        return (
                        <motion.div
                          key={idx}
                          variants={hoverLift}
                          className="flex items-center justify-between p-3 bg-card rounded border border-border/50 hover:border-primary/50 transition-all group"
                        >
                          <div className="flex items-center gap-3 w-full">
                            <div className={`w-2 h-2 rounded-full ${sui.dot} animate-pulse`} />
                            <div className="flex-1">
                              <div className="flex justify-between items-center">
                                <p className="font-bold text-[10px] font-mono text-foreground group-hover:text-primary transition-colors tracking-tighter">{signal.name.toUpperCase()}</p>
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <button type="button" className="outline-none focus:ring-1 focus:ring-primary rounded-full transition-opacity opacity-60 hover:opacity-100 flex items-center gap-1 group/tip">
                                       <Radar className="w-3 h-3 text-primary group-hover/tip:animate-pulse" />
                                       <span className="text-[9px] font-mono text-muted-foreground uppercase">{sui.label}</span>
                                    </button>
                                  </TooltipTrigger>
                                  <TooltipContent side="right" className="bg-popover border border-border p-4 max-w-[280px] shadow-2xl text-popover-foreground z-[100] rounded-xl">
                                    <p className="font-bold text-primary mb-1 uppercase tracking-widest">{signal.name}</p>
                                    <p className="mb-2">{signal.desc}</p>
                                    {signal.name === "Regional Intent" && (
                                      <p className="text-[10px] text-muted-foreground border-t border-border/50 pt-2 mt-2 italic">
                                        Note: Intent is measured at city/state scale and grounded by your local POI density to ensure hyper-local relevance.
                                      </p>
                                    )}
                                    <div className="pt-2 border-t border-border flex justify-between items-baseline">
                                       <span className="text-[8px] opacity-60 uppercase">Normalized Score:</span>
                                       <span className="text-primary font-bold">{(signal.score * 100).toFixed(1)}%</span>
                                    </div>
                                  </TooltipContent>
                                </Tooltip>
                              </div>
                              <div className="flex items-center gap-2">
                                <div className="h-1 flex-1 bg-foreground/10 rounded-full overflow-hidden mt-1">
                                  <div className={`h-full ${sui.bar}`} style={{ width: `${signal.score * 100}%` }} />
                                </div>
                                <p className="text-[10px] text-muted-foreground/60 font-mono w-8 text-right">{(signal.score * 100).toFixed(0)}%</p>
                              </div>
                            </div>
                          </div>
                        </motion.div>
                      );
                      }) : null}
                        </>
                      )}

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

            {/* Top Zones (dedicated card, separate from "WHY HOT") */}
            <motion.div variants={fadeInUp}>
              <HolographicCard className="p-6 border-amber-500/30">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-bold font-mono text-amber-600 dark:text-amber-300 flex items-center gap-2">
                    <Layers className="w-4 h-4" />
                    TOP ZONES (MULTI-ZONE SCAN)
                  </h3>
                  <Badge
                    variant="outline"
                    className="text-[9px] font-mono border-amber-500/30 text-amber-700 dark:text-amber-300"
                  >
                    {recommendedZones.length > 0
                      ? `${recommendedZones.length} ZONES${zoneScanMeta?.radius_m ? ` • ${(zoneScanMeta.radius_m / 1000).toFixed(0)}KM` : ""}`
                      : "NOT RUN"}
                  </Badge>
                </div>

                {recommendedZones.length === 0 ? (
                  <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-4">
                    <p className="text-[11px] font-mono text-foreground mb-2">
                      Run a multi-zone scan to rank the best areas inside your radius.
                    </p>
                    <p className="text-[10px] font-mono text-muted-foreground mb-3 leading-relaxed">
                      Click <span className="text-amber-700 dark:text-amber-300 font-bold">Find Best Zones</span> and wait for the scan to finish. The results will appear here and as pins on the map.
                    </p>
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={handleRecommendZones}
                      disabled={loading || refreshing || zonesLoading}
                      aria-busy={zonesLoading}
                      className="w-full border-amber-500/40 text-amber-700 dark:text-amber-300 hover:bg-amber-500/10 font-mono font-bold tracking-wider h-9"
                    >
                      {zonesLoading ? (
                        <Loader2 className="w-4 h-4 mr-2 animate-spin shrink-0" aria-hidden />
                      ) : (
                        <Layers className="w-4 h-4 mr-2 shrink-0" aria-hidden />
                      )}
                      {zonesLoading ? "SCANNING ZONES…" : "FIND BEST ZONES"}
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-3 max-h-[240px] overflow-y-auto pr-1 custom-scrollbar">
                    {recommendedZones.map((zone) => (
                      <div
                        key={`${zone.label}-${zone.latitude.toFixed(4)}`}
                        className="p-3 rounded border border-amber-500/30 bg-amber-500/5 space-y-2"
                      >
                        <div className="flex justify-between items-start gap-2">
                          <div>
                            <span className="text-xs font-mono font-bold text-foreground">{zone.label}</span>
                            <span className="text-[10px] font-mono text-muted-foreground ml-2">
                              {zone.score}/100
                            </span>
                            <div className="mt-1 text-[9px] font-mono text-muted-foreground/80">
                              {getAreaDisplay(zone.latitude, zone.longitude)}{" "}
                              <a
                                className="ml-2 text-primary hover:underline"
                                href={`https://www.google.com/maps?q=${zone.latitude},${zone.longitude}`}
                                target="_blank"
                                rel="noreferrer"
                              >
                                View on map
                              </a>
                            </div>
                          </div>
                          <Badge
                            variant="outline"
                            className={cn(
                              "text-[9px] font-mono",
                              zone.urgency === "Critical" || zone.urgency === "High"
                                ? "border-red-500/50 text-red-600"
                                : "border-primary/40 text-primary"
                            )}
                          >
                            {zone.urgency}
                          </Badge>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-background/50 border border-border/60 text-muted-foreground">
                            Trends {(zone.signals?.trends_score ?? 0) * 100 | 0}%
                          </span>
                          <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-background/50 border border-border/60 text-muted-foreground">
                            Places {(zone.signals?.places_score ?? 0) * 100 | 0}%
                          </span>
                          <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-background/50 border border-border/60 text-muted-foreground">
                            Weather {(zone.signals?.weather_score ?? 0) * 100 | 0}%
                          </span>
                        </div>
                        <p className="text-[10px] font-mono text-muted-foreground leading-snug">{zone.reason}</p>
                        <Button
                          type="button"
                          size="sm"
                          variant="secondary"
                          className="w-full font-mono text-[10px] h-8"
                          disabled={briefLoading}
                          onClick={() => handleMetaDeployOpen(zone)}
                        >
                          <MapPinned className="w-3 h-3 mr-2" />
                          Deploy Here
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
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
                         {loading ? "..." : (data?.urgency?.toUpperCase() ?? "UNKNOWN")}
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
                        <span className="text-[9px] font-mono text-muted-foreground uppercase opacity-70">Projected reach (est.)</span>
                        <span className="text-[10px] font-mono text-primary font-bold">
                          {(() => {
                            const raw = (data?.signals?.places_score ?? 0) * 1200 + 450;
                            const rounded = Math.max(0, Math.round(raw / 50) * 50);
                            return `~${rounded} users`;
                          })()}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-[9px] font-mono text-muted-foreground uppercase opacity-70">Expected lift (est.)</span>
                        <span className="text-[10px] font-mono text-primary font-bold">
                          {(() => {
                            const raw = (data?.score || 0) * 0.85;
                            const rounded = Math.max(0, Math.round(raw / 5) * 5);
                            return `+${rounded}%`;
                          })()}
                        </span>
                      </div>
                   </div>

                   <p className="text-[10px] font-mono text-muted-foreground/80 italic leading-relaxed">
                      Estimates are derived from the current scan’s signal mix (especially Places density) and score. They are not measured conversions.
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
                    scanLogs
                      .filter((l) => l.type !== "info" || String(l.msg || "").toLowerCase().includes("signal"))
                      .map(log => (
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
                 {(!personaValidity.valid || persona.length === 0) && (
                   <p className="text-[10px] font-mono text-muted-foreground leading-relaxed">
                     {loading
                       ? "Inferring visitor mix from POI signals…"
                       : data
                        ? "Visitor personality is unavailable for this scan (low signal confidence). Try rescan or a smaller radius."
                         : "Run a radar scan to estimate visitor personas from local POI density."}
                   </p>
                 )}
                 {personaValidity.valid && persona.map((p, i) => (
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

                {/* Signal Context explanation (only when split is valid) */}
                {personaValidity.valid && (
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
                )}
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
                 <p className="text-xs text-foreground leading-relaxed italic mb-3">
                    {previewCaption}
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
                     {history.length > 0 ? (() => {
                        // Collapse identical repeated scans (trust: avoid 10 identical lines).
                        const groups: Array<{ key: string; last: CampaignLogEntry; count: number }> = [];
                        const mk = (l: CampaignLogEntry) => `${l.radius}|${l.final_score}|${l.urgency || ""}`;
                        for (const l of history) {
                          const key = mk(l);
                          const last = groups[groups.length - 1];
                          if (last && last.key === key) {
                            last.count += 1;
                            last.last = l;
                          } else {
                            groups.push({ key, last: l, count: 1 });
                          }
                        }
                        return groups.slice(0, 12).map((g, i) => {
                          const log = g.last;
                          return (
                           <tr key={i} className="hover:bg-primary/5 transition-colors group">
                              <td className="py-4 text-muted-foreground">{new Date(log.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</td>
                              <td className="py-4 text-foreground font-bold">{log.radius / 1000} KM</td>
                              <td className="py-4">
                                 <div className="flex items-center gap-2">
                                    <div className="h-1 w-10 bg-foreground/10 rounded-full overflow-hidden">
                                       <div className="h-full bg-primary" style={{ width: `${log.final_score}%` }} />
                                    </div>
                                    <span className="font-bold text-primary">{log.final_score}</span>
                                    {g.count > 1 && (
                                      <span className="text-[10px] text-muted-foreground/70 font-mono">×{g.count}</span>
                                    )}
                                 </div>
                              </td>
                              <td className="py-4">
                                 <span className={`px-2 py-0.5 rounded text-[10px] ${log.urgency === 'Critical' ? 'bg-red-500/20 text-red-400' : 'bg-primary/20 text-primary'}`}>
                                    {(log.urgency ?? "").toUpperCase()}
                                 </span>
                              </td>
                           </tr>
                          );
                        });
                      })() : (
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
                    <>
                    {strategyHistory.map((brief) => {
                      const lat = brief?.location?.coordinates?.[1];
                      const lng = brief?.location?.coordinates?.[0];
                      const inferTone = (b: any) => {
                        const cap = String(b?.caption || "").trim();
                        const v = b?.caption_variants || {};
                        const soft = String(v?.soft || "").trim();
                        const urgency = String(v?.urgency || "").trim();
                        const aggressive = String(v?.aggressive || "").trim();
                        if (cap && soft && cap === soft) return "SOFT";
                        if (cap && urgency && cap === urgency) return "URGENCY";
                        if (cap && aggressive && cap === aggressive) return "AGGRESSIVE";
                        // Fallback: prefer the first non-empty variant as the implied tone.
                        if (soft) return "SOFT";
                        if (urgency) return "URGENCY";
                        if (aggressive) return "AGGRESSIVE";
                        return "—";
                      };
                      const tone = inferTone(brief);
                      const zoneDir = String(brief?.zone_label || "").trim() || "—";
                      const personaTop = (() => {
                        const split = Array.isArray((brief as any)?.persona_split) ? (brief as any).persona_split : [];
                        const cleaned = split
                          .map((p: any) => ({ type: String(p?.type || "").trim(), pct: Number(p?.pct ?? 0) || 0 }))
                          .filter((p: any) => p.type && p.pct > 0)
                          .sort((a: any, b: any) => b.pct - a.pct);
                        if (cleaned.length < 2) return null;
                        if (cleaned[0].pct >= 95) return null;
                        return `${cleaned[0].type} ${cleaned[0].pct}%`;
                      })();
                      const area =
                        typeof lat === "number" && typeof lng === "number"
                          ? (getAreaLabel(lat, lng) || formatLatLngShort(lat, lng) || "—")
                          : "—";
                      const objective = String(brief.meta_objective || "BRIEF").toUpperCase();
                      const title = `${objective} • ${zoneDir} • ${area} • ${brief.radius_km}km • ${tone}${personaTop ? ` • ${personaTop}` : ""}`;
                      return (
                        <div 
                            key={brief.id} 
                            onClick={() => handleReplayCampaign(brief)}
                            className="p-3 bg-muted/30 border border-border/50 rounded-xl hover:border-primary/40 hover:bg-muted/50 transition-all cursor-pointer group"
                        >
                            <div className="flex justify-between items-start mb-2">
                                <div className="space-y-0.5">
                                    <p className="text-[10px] font-bold text-foreground group-hover:text-primary transition-colors line-clamp-2">
                                      {title}
                                    </p>
                                    <p className="text-[9px] font-mono text-muted-foreground">{new Date(brief.timestamp).toLocaleDateString()} @ {new Date(brief.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</p>
                                </div>
                                <Badge className="text-[9px] bg-primary/10 text-primary border-primary/20 h-5">SCORE: {brief.heat_score}</Badge>
                            </div>
                            <div className="flex flex-wrap gap-1.5 mt-2">
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
                      );
                    })}
                    </>
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

        {deployZone && (
          <MetaDeployModal
            zone={deployZone}
            brief={deployBrief}
            radiusMeters={radius[0] * 1000}
            personaSplit={persona}
            areaName={getAreaLabel(deployZone.latitude, deployZone.longitude)}
            onClose={() => {
              setDeployZone(null);
              setDeployBrief(null);
            }}
          />
        )}
      </div>
     </TooltipProvider>
    </Layout>
  );
};

export default GeoIntent;