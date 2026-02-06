import { Button } from "@/components/ui/button";
import Layout from "@/components/Layout";
import { Badge } from "@/components/ui/badge";
import { Zap, TrendingUp, Flame, Target, Users, MapPin, Globe, Radio, Filter, ArrowRight } from "lucide-react";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeInUp, hoverScale, hoverLift } from "@/utils/animations";
import { HolographicCard } from "@/components/ui/holographic-card";
import { BlurText } from "@/components/ui/text-reveal";

const TrendArbitrage = () => {
  const trends = [
    {
      title: "AI-POWERED HOME ASSISTANTS",
      impact: "HIGH",
      virality: 94,
      timeframe: "6-8 WEEKS PEAK",
      sentiment: "POSITIVE (87%)",
      color: "text-primary",
      borderColor: "border-primary/50",
      glow: "shadow-[0_0_20px_rgba(0,224,208,0.2)]"
    },
    {
      title: "SUSTAINABLE FASHION MOVEMENT",
      impact: "MEDIUM",
      virality: 78,
      timeframe: "12+ WEEKS SUSTAINED",
      sentiment: "VERY POSITIVE (92%)",
      color: "text-emerald-400",
      borderColor: "border-emerald-400/50",
      glow: "shadow-[0_0_20px_rgba(52,211,153,0.2)]"
    },
    {
      title: "REMOTE WORK TECH SOLUTIONS",
      impact: "HIGH",
      virality: 86,
      timeframe: "4-6 WEEKS PEAK",
      sentiment: "POSITIVE (81%)",
      color: "text-purple-400",
      borderColor: "border-purple-400/50",
      glow: "shadow-[0_0_20px_rgba(192,132,252,0.2)]"
    }
  ];

  const tickerItems = [
    "MARKET VOLATILITY DETECTED: +4.2%",
    "NEW TREND VECTOR: 'MICRO-LIVING' [RISING]",
    "COMPETITOR SIGNAL: LAUNCH DETECTED IN SECTOR 7",
    "SENTIMENT SHIFT: 'ECO-CONSCIOUS' → 'REGENERATIVE'",
    "VIRALITY SPIKE: REGION APAC [98%]",
  ];

  return (
    <Layout>
      <div className="space-y-8">
        {/* Ticker Tape */}
        <div className="w-full overflow-hidden bg-black/40 border-y border-white/10 py-2 mb-6 backdrop-blur-sm">
          <motion.div
            className="flex gap-12 whitespace-nowrap"
            animate={{ x: [0, -1000] }}
            transition={{ repeat: Infinity, duration: 20, ease: "linear" }}
          >
            {[...tickerItems, ...tickerItems, ...tickerItems].map((item, i) => (
              <div key={i} className="flex items-center gap-2 text-xs font-mono text-white/70">
                <Radio className="w-3 h-3 text-primary animate-pulse" />
                {item}
              </div>
            ))}
          </motion.div>
        </div>

        {/* Header */}
        <Reveal variant="blurInUp">
          <div className="flex items-center gap-4 mb-2">
            <div className="p-3 bg-primary/10 rounded border border-primary/30">
              <Globe className="w-8 h-8 text-primary animate-spin-slow" />
            </div>
            <div>
              <h1 className="text-4xl font-bold mb-1 font-bebas tracking-wider text-white">
                <BlurText text="TREND ARBITRAGE DETECTOR" />
              </h1>
              <p className="text-muted-foreground font-mono text-sm">
                  // REAL-TIME PREDICTIVE ANALYTICS // CAPITALIZE ON EMERGING VECTORS
              </p>
            </div>
          </div>
        </Reveal>

        {/* Cyber-Deck Filter Interface */}
        <Reveal variant="fadeInUp" delay={0.1}>
          <div className="flex flex-wrap gap-2 mb-6 p-4 bg-white/5 rounded-lg border border-white/10 backdrop-blur-md">
            <div className="flex items-center gap-2 mr-4 text-xs font-mono text-muted-foreground uppercase tracking-widest">
              <Filter className="w-4 h-4" />
              Signal Filters:
            </div>
            {["HIGH IMPACT", "RISING", "SUSTAINED", "VIRAL > 80%", "SENTIMENT +"].map((filter, i) => (
              <button
                key={i}
                className={`px-3 py-1.5 text-[10px] font-mono border transition-all hover:bg-primary/20 hover:text-primary hover:border-primary/50 ${i === 0 ? 'bg-primary/10 text-primary border-primary/50 shadow-[0_0_10px_rgba(0,224,208,0.2)]' : 'bg-black/40 text-white/70 border-white/10'}`}
              >
                [{filter}]
              </button>
            ))}
          </div>
        </Reveal>

        {/* Live Trend Feed */}
        <Reveal variant="fadeInUp" delay={0.2}>
          <HolographicCard className="p-6">
            <h2 className="text-xl font-bold mb-6 flex items-center gap-2 font-bebas tracking-wide text-white">
              <Flame className="w-5 h-5 text-primary" />
              LIVE TREND FEED
            </h2>
            <motion.div
              className="space-y-4"
              variants={staggerContainer}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
            >
              {trends.map((trend, idx) => (
                <motion.div key={idx} variants={fadeInUp}>
                  <motion.div
                    variants={hoverLift}
                    initial="rest"
                    whileHover="hover"
                    className={`p-5 bg-black/40 rounded border border-white/10 hover:border-primary/50 transition-all group relative overflow-hidden ${idx === 0 ? 'border-l-4 border-l-primary' : ''}`}
                  >
                    {/* Scanline effect on hover */}
                    <div className="absolute inset-0 bg-gradient-to-b from-transparent via-primary/5 to-transparent translate-y-[-100%] group-hover:translate-y-[100%] transition-transform duration-1000 pointer-events-none" />

                    <div className="flex items-start justify-between mb-4 relative z-10">
                      <div>
                        <h3 className={`text-lg font-bold font-bebas tracking-wide ${trend.color} group-hover:text-white transition-colors`}>{trend.title}</h3>
                        <div className="flex gap-2 mt-2">
                          <Badge className="bg-white/10 text-white border-white/20 hover:bg-white/20 font-mono text-[10px]">
                            {trend.impact} IMPACT
                          </Badge>
                          <Badge variant="outline" className="text-white/60 border-white/10 font-mono text-[10px]">VIRALITY: {trend.virality}%</Badge>
                        </div>
                      </div>
                      <div className={`p-2 rounded-full bg-white/5 border border-white/10 group-hover:${trend.borderColor} group-hover:${trend.color} transition-colors`}>
                        <TrendingUp className="w-5 h-5" />
                      </div>
                    </div>
                    <div className="grid md:grid-cols-2 gap-4 text-xs font-mono relative z-10">
                      <p className="text-white/60">
                        <span className="text-white/30 uppercase tracking-wider">Timeframe:</span> {trend.timeframe}
                      </p>
                      <p className="text-white/60">
                        <span className="text-white/30 uppercase tracking-wider">Sentiment:</span> {trend.sentiment}
                      </p>
                    </div>
                    <motion.div variants={hoverScale} whileTap="tap" className="mt-4 inline-block relative z-10">
                      <Button size="sm" className="bg-primary/10 text-primary border border-primary/50 hover:bg-primary hover:text-primary-foreground font-mono text-xs tracking-wider transition-all">
                        INITIATE ANALYSIS <ArrowRight className="w-3 h-3 ml-2" />
                      </Button>
                    </motion.div>
                  </motion.div>
                </motion.div>
              ))}
            </motion.div>
          </HolographicCard>
        </Reveal>

        {/* Trend Breakdown (Example for first trend) */}
        <Reveal variant="fadeInUp" delay={0.4}>
          <HolographicCard className="p-6 border-primary/30 shadow-[0_0_30px_rgba(0,224,208,0.1)]">
            <div className="flex items-center justify-between mb-8 border-b border-white/10 pb-4">
              <h2 className="text-2xl font-bold font-bebas tracking-wide text-white">
                DETAILED ANALYSIS: <span className="text-primary">AI-POWERED HOME ASSISTANTS</span>
              </h2>
              <Badge className="bg-primary text-primary-foreground font-bold animate-pulse">LIVE TRACKING</Badge>
            </div>

            <div className="grid md:grid-cols-2 gap-8 mb-8">
              <div>
                <h3 className="text-sm font-bold mb-4 flex items-center gap-2 text-white/80 font-mono uppercase tracking-widest">
                  <Target className="w-4 h-4 text-primary" />
                  Lifecycle Projection
                </h3>
                <p className="text-xs text-muted-foreground mb-4 font-mono">
                  {">"} ALGORITHM PROJECTION: 6-8 WEEK PEAK ENGAGEMENT.
                  {">"} POST-PEAK: GRADUAL DECLINE (-15% MoM).
                </p>
                <div className="p-4 bg-black/40 rounded border border-white/10 relative">
                  {/* Grid lines */}
                  <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.05)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.05)_1px,transparent_1px)] bg-[size:20px_20px]" />

                  <div className="h-32 flex items-end gap-1 relative z-10">
                    {[30, 50, 75, 95, 100, 90, 70, 50, 30, 20].map((height, i) => (
                      <motion.div
                        key={i}
                        initial={{ height: 0 }}
                        whileInView={{ height: `${height}%` }}
                        transition={{ duration: 0.8, delay: i * 0.05, type: "spring" }}
                        className="flex-1 bg-primary/80 hover:bg-primary transition-colors shadow-[0_0_10px_rgba(0,224,208,0.3)]"
                      />
                    ))}
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-sm font-bold mb-4 flex items-center gap-2 text-white/80 font-mono uppercase tracking-widest">
                  <MapPin className="w-4 h-4 text-primary" />
                  Geographic Hotspots
                </h3>
                <p className="text-xs text-muted-foreground mb-4 font-mono">
                  {">"} PRIMARY VECTOR: METROPOLITAN ZONES.
                  {">"} SECONDARY VECTOR: SUBURBAN EXPANSION (+12%).
                </p>
                <div className="space-y-3">
                  {[
                    { area: "URBAN CENTERS", intensity: 92 },
                    { area: "TECH HUBS", intensity: 88 },
                    { area: "SUBURBS", intensity: 65 }
                  ].map((zone, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <span className="text-[10px] w-24 font-mono text-white/60">{zone.area}</span>
                      <div className="flex-1 h-2 bg-white/5 rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          whileInView={{ width: `${zone.intensity}%` }}
                          transition={{ duration: 1, delay: 0.2 + (i * 0.1), ease: "easeOut" }}
                          className="h-full bg-primary shadow-[0_0_8px_rgba(0,224,208,0.5)]"
                        />
                      </div>
                      <span className="text-xs font-bold w-8 text-right font-mono text-primary">{zone.intensity}%</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-4 mb-8">
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.5 }}
                className="p-4 bg-white/5 rounded border-l-2 border-primary"
              >
                <h4 className="font-bold mb-2 flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-white">
                  <Users className="w-4 h-4 text-primary" />
                  Sentiment Analysis
                </h4>
                <p className="text-xs text-white/60 font-mono leading-relaxed">
                  POSITIVE SENTIMENT PREVAILS (87%). DRIVERS: CONVENIENCE, NOVELTY.
                  RISK FACTOR: PRIVACY CONCERNS (13%) → OPPORTUNITY: TRUST-FOCUSED MESSAGING.
                </p>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, x: 20 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.6 }}
                className="p-4 bg-white/5 rounded border-l-2 border-purple-500"
              >
                <h4 className="font-bold mb-2 flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-white">
                  <Target className="w-4 h-4 text-purple-500" />
                  Competitive Landscape
                </h4>
                <p className="text-xs text-white/60 font-mono leading-relaxed">
                  CURRENT SATURATION: LOW. EARLY ADOPTERS: TECH STARTUPS.
                  WINDOW OF OPPORTUNITY: 2-3 WEEKS BEFORE MAJOR BRAND ENTRY.
                </p>
              </motion.div>
            </div>

            <Reveal variant="zoomIn" delay={0.6}>
              <div className="p-6 bg-primary/10 rounded border border-primary/30 relative overflow-hidden group">
                <div className="absolute inset-0 bg-primary/5 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000 pointer-events-none" />

                <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-6">
                  <div>
                    <h3 className="text-xl font-bold mb-1 font-bebas tracking-wide text-white">INSTANT CAMPAIGN LAUNCHER</h3>
                    <p className="text-xs text-white/60 font-mono">
                      CAPITALIZE ON THIS TREND IMMEDIATELY. AI CREATIVE GENERATION READY.
                    </p>
                  </div>
                  <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                    <Button size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90 font-bold tracking-wider font-bebas text-lg shadow-[0_0_20px_rgba(0,224,208,0.4)]">
                      <Flame className="w-5 h-5 mr-2" />
                      LAUNCH CAMPAIGN SEQUENCE
                    </Button>
                  </motion.div>
                </div>
              </div>
            </Reveal>
          </HolographicCard>
        </Reveal>
      </div>
    </Layout>
  );
};

export default TrendArbitrage;
