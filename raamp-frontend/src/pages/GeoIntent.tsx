import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { MapPin, Target, TrendingUp, Users, Globe, Radar, Crosshair, Scan, RefreshCw } from "lucide-react";
import Layout from "@/components/Layout";
import { apiClient } from "@/services/api";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeInUp, hoverScale, hoverLift } from "@/utils/animations";
import { HolographicCard } from "@/components/ui/holographic-card";
import { BlurText } from "@/components/ui/text-reveal";

interface HotRegion {
  region_name: string;
  coordinates: { lat: number; lng: number };
  heat_score: number;
  predicted_high_intent_customers: number;
  peak_hours: string[];
  dominant_demographics: string[];
}

interface GeoIntentData {
  hot_regions: HotRegion[];
  analysis_metadata: {
    total_predicted_customers: number;
    average_heat_score: number;
    top_region: string;
    coverage_area_km2: number;
    confidence_level: string;
    [key: string]: any;
  };
}

const GeoIntent = () => {
  const [radius, setRadius] = useState([5]);
  const [businessName, setBusinessName] = useState("Artisan Coffee House");
  const [data, setData] = useState<GeoIntentData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      setRefreshing(true);
      const response = await apiClient.get<GeoIntentData>('/dashboard/geo-intent');
      if (response) {
        setData(response);
      }
    } catch (error) {
      console.error("Failed to fetch geo intent data", error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <Reveal variant="blurInUp">
          <div className="flex items-center justify-between gap-4 mb-2">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-primary/10 rounded border border-primary/30">
                <Globe className="w-8 h-8 text-primary animate-spin-slow" />
              </div>
              <div>
                <h1 className="text-4xl font-bold mb-1 font-bebas tracking-wider text-white">
                  <BlurText text="GEO-INTENT TARGETING ENGINE" />
                </h1>
                <p className="text-muted-foreground font-mono text-sm">
                    // HYPER-LOCAL ZONES // HIGH-INTENT DISCOVERY // REAL-TIME TRACKING
                </p>
              </div>
            </div>
            <Button
              variant="outline"
              size="icon"
              onClick={fetchData}
              disabled={loading || refreshing}
              className="bg-black/40 border-primary/30 text-primary hover:bg-primary/20"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            </Button>
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
                <h2 className="text-xl font-bold font-bebas tracking-wide text-white flex items-center gap-2">
                  <Target className="w-5 h-5 text-primary" />
                  TARGETING ZONE BUILDER
                </h2>
                <div className="flex items-center gap-2 text-[10px] font-mono text-primary border border-primary/30 px-2 py-1 rounded bg-primary/5">
                  <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                  SATELLITE LINK ACTIVE
                </div>
              </div>

              {/* Mock Map / Radar View */}
              <div className="aspect-video bg-black/60 rounded border border-white/10 mb-6 relative overflow-hidden group cursor-crosshair">
                {/* Grid Overlay */}
                <div className="absolute inset-0 bg-[linear-gradient(rgba(0,224,208,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(0,224,208,0.05)_1px,transparent_1px)] bg-[size:40px_40px]" />

                {/* Radar Sweep */}
                <div className="absolute inset-0 bg-[conic-gradient(from_0deg,transparent_0deg,rgba(0,224,208,0.1)_360deg)] animate-spin-slow opacity-30 rounded-full scale-150" />

                <div className="absolute inset-0 flex items-center justify-center z-10">
                  <div className="text-center relative">
                    <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full animate-pulse" />
                    <Reveal variant="zoomIn" delay={0.4}>
                      <MapPin className="w-12 h-12 text-primary mx-auto mb-2 relative z-10 drop-shadow-[0_0_10px_rgba(0,224,208,0.8)]" />
                    </Reveal>
                    <div className="bg-black/80 backdrop-blur border border-primary/30 px-3 py-1 rounded text-[10px] font-mono text-primary mt-2">
                      TARGET: {businessName.toUpperCase()}
                    </div>
                  </div>
                </div>

                {/* Corner Markers */}
                <div className="absolute top-2 left-2 w-4 h-4 border-t border-l border-primary/50" />
                <div className="absolute top-2 right-2 w-4 h-4 border-t border-r border-primary/50" />
                <div className="absolute bottom-2 left-2 w-4 h-4 border-b border-l border-primary/50" />
                <div className="absolute bottom-2 right-2 w-4 h-4 border-b border-r border-primary/50" />
              </div>

              <div className="space-y-6">
                <div>
                  <div className="flex justify-between mb-2">
                    <label className="text-xs font-mono text-white/70 uppercase tracking-wider">Zone Radius</label>
                    <span className="text-xs font-mono text-primary font-bold">{radius[0]} KM</span>
                  </div>
                  <Slider
                    value={radius}
                    onValueChange={setRadius}
                    max={50}
                    min={1}
                    step={1}
                    className="mb-2 [&>.relative>.absolute]:bg-primary [&>.relative]:bg-white/10"
                  />
                </div>

                <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                  <Button className="w-full bg-primary/10 text-primary border border-primary/50 hover:bg-primary hover:text-primary-foreground font-mono font-bold tracking-wider transition-all h-12">
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
                <h3 className="text-lg font-bold mb-4 font-bebas tracking-wide text-white flex items-center gap-2">
                  <Radar className="w-5 h-5 text-primary" />
                  LIVE GEO-INTENT HEATMAP
                </h3>
                <div className="space-y-2 h-[280px] overflow-y-auto pr-2 custom-scrollbar">
                  {loading ? (
                    <div className="flex flex-col items-center justify-center h-full space-y-4">
                      <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                      <p className="text-xs font-mono text-primary animate-pulse">Scanning frequencies...</p>
                    </div>
                  ) : (data?.hot_regions || []).map((zone, idx) => (
                    <motion.div
                      key={idx}
                      variants={hoverLift}
                      initial="rest"
                      whileHover="hover"
                      className="flex items-center justify-between p-3 bg-black/40 rounded border border-white/10 hover:border-primary/50 transition-all group"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-2 h-2 rounded-full bg-primary shadow-[0_0_8px_rgba(0,224,208,0.8)] animate-pulse"></div>
                        <div>
                          <p className="font-bold text-xs font-mono text-white group-hover:text-primary transition-colors">{zone.region_name}</p>
                          <div className="flex items-center gap-2">
                            <div className="h-1 w-16 bg-white/10 rounded-full overflow-hidden mt-1">
                              <div className="h-full bg-primary" style={{ width: `${zone.heat_score}%` }} />
                            </div>
                            <p className="text-[10px] text-white/40 font-mono">SCORE: {zone.heat_score}</p>
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-xs font-bold font-mono text-primary">{zone.predicted_high_intent_customers} <span className="text-[10px] opacity-70">users</span></p>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </HolographicCard>
            </motion.div>

            {/* Target Audience Insights */}
            <motion.div variants={fadeInUp}>
              <HolographicCard className="p-6">
                <h3 className="text-lg font-bold mb-4 font-bebas tracking-wide text-white flex items-center gap-2">
                  <Users className="w-5 h-5 text-primary" />
                  AUDIENCE METRICS
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-white/5 rounded border border-white/10 hover:border-primary/30 transition-colors">
                    <Users className="w-5 h-5 text-primary mb-2" />
                    <p className="text-2xl font-bold font-bebas tracking-wider text-white">
                      <BlurText text={loading ? "..." : (data?.analysis_metadata.total_predicted_customers.toString() || "0")} />
                    </p>
                    <p className="text-[10px] text-muted-foreground font-mono uppercase">High-Intent Users</p>
                  </div>
                  <div className="p-4 bg-white/5 rounded border border-white/10 hover:border-primary/30 transition-colors">
                    <TrendingUp className="w-5 h-5 text-primary mb-2" />
                    <p className="text-2xl font-bold font-bebas tracking-wider text-white">
                      <BlurText text={loading ? "..." : (data?.analysis_metadata.confidence_level || "0%")} />
                    </p>
                    <p className="text-[10px] text-muted-foreground font-mono uppercase">Confidence Level</p>
                  </div>
                </div>
              </HolographicCard>
            </motion.div>
          </div>
        </motion.div>

        <Reveal variant="fadeInUp" delay={0.6}>
          <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
            <Button size="lg" className="w-full bg-primary text-primary-foreground hover:bg-primary/90 font-bold font-bebas tracking-wider text-xl shadow-[0_0_30px_rgba(0,224,208,0.4)] h-14">
              <Scan className="w-6 h-6 mr-3" />
              DEPLOY GEO-TARGETED CAMPAIGN
            </Button>
          </motion.div>
        </Reveal>
      </div>
    </Layout>
  );
};

export default GeoIntent;