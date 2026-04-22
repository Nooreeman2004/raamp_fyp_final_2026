import { useQuery } from "@tanstack/react-query";
import { HolographicCard } from "@/components/ui/holographic-card";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, LineChart, Line } from "recharts";
import { instagramService } from "@/services/instagramService";
import { geoIntentService } from "@/services/geoIntentService";
import { businessService } from "@/services/businessService";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { MapPin, Zap, RefreshCw, MapPinned } from "lucide-react";

interface PerformanceChartsProps {
  businessId: string;
}

const GEO_ZONE_CACHE_KEY = "raamp_geo_top_zones_cache_v1";

function readZoneCache(): { timestamp: string; zones: Array<{ label: string; score: number }> } | null {
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

export const PerformanceCharts = ({ businessId }: PerformanceChartsProps) => {
  // 1. 7-Day Geo Heat History
  const { data: geoHistory, isLoading: geoLoading } = useQuery({
    queryKey: ['geo-history-timeseries', businessId, 7],
    queryFn: () => geoIntentService.getHeatScoreHistory(businessId, 7),
    enabled: !!businessId
  });

  // 2. Connection Statuses
  const { data: socialStatus, isLoading: statusLoading } = useQuery({
    queryKey: ['social-status-charts'],
    queryFn: () => instagramService.getSocialConnectionStatus(),
  });

  const { data: hyperlocalSetup, isLoading: setupLoading } = useQuery({
    queryKey: ['hyperlocal-setup-charts'],
    queryFn: () => businessService.getHyperlocalSetup(),
  });

  const hasGeoData = geoHistory && geoHistory.length > 0;
  const zoneCache = readZoneCache();
  const topZone = zoneCache?.zones?.[0];

  return (
    <div className="grid grid-cols-1 gap-6 h-full">
      {/* Regional Heat Score Trends removed from dashboard */}
    </div>
  );
};
