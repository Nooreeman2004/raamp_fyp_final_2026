import { Button } from "@/components/ui/button";
import Layout from "@/components/Layout";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Zap, FlaskConical, TrendingUp, CheckCircle, Play, HelpCircle, Swords } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer } from "recharts";
import ConfirmationDialog from "@/components/ConfirmationDialog";
import { useState, useEffect } from "react";
import { useToast } from "@/hooks/use-toast";
import Breadcrumbs from "@/components/Breadcrumbs";
import Celebration from "@/components/Celebration";
import ChartSkeleton from "@/components/ChartSkeleton";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeInUp, blurInUp, zoomIn } from "@/utils/animations";
import { HolographicCard } from "@/components/ui/holographic-card";
import { BlurText } from "@/components/ui/text-reveal";

const ABTesting = () => {
  const { toast } = useToast();
  const [showBudgetDialog, setShowBudgetDialog] = useState(false);
  const [showCelebration, setShowCelebration] = useState(false);
  const [isLoadingChart, setIsLoadingChart] = useState(true);

  // Variant preview data
  const variants = [
    {
      name: "AD CREATIVE ALPHA",
      type: "CREATIVE PREVIEW 1",
      conversion: "12.3%",
      ctr: "1.8%",
      status: "Running",
      tag: "HIGH POTENTIAL",
      tagColor: "bg-amber-500/20 text-amber-400 border-amber-500/50",
      glitchColor: "hover:shadow-[0_0_20px_rgba(245,158,11,0.4)]"
    },
    {
      name: "LANDING PAGE V2",
      type: "CREATIVE PREVIEW 2",
      conversion: "8.9%",
      ctr: "0.9%",
      status: "Running",
      tag: "HEALTH FAIR",
      tagColor: "bg-emerald-500/20 text-emerald-400 border-emerald-500/50",
      trend: "up",
      glitchColor: "hover:shadow-[0_0_20px_rgba(16,185,129,0.4)]"
    },
    {
      name: "SUBJECT LINE: URGENT",
      type: "TEXT SNIPPET",
      conversion: "15.1%",
      ctr: "2.5%",
      status: "Concluded",
      tag: "PAST WINNER",
      tagColor: "bg-blue-500/20 text-blue-400 border-blue-500/50",
      glitchColor: "hover:shadow-[0_0_20px_rgba(59,130,246,0.4)]"
    },
  ];

  // Simulate chart loading
  useEffect(() => {
    const timer = setTimeout(() => setIsLoadingChart(false), 1000);
    return () => clearTimeout(timer);
  }, []);

  // Conversion trend data
  const conversionData = [
    { day: "Day 1", "Variant A": 5, "Variant B (Winner)": 7, "Variant C (Stale)": 6 },
    { day: "Day 2", "Variant A": 6, "Variant B (Winner)": 8.5, "Variant C (Stale)": 5.5 },
    { day: "Day 3", "Variant A": 6.5, "Variant B (Winner)": 10, "Variant C (Stale)": 6 },
    { day: "Day 4", "Variant A": 7, "Variant B (Winner)": 11.5, "Variant C (Stale)": 6.5 },
    { day: "Day 5", "Variant A": 7.5, "Variant B (Winner)": 13, "Variant C (Stale)": 6 },
    { day: "Day 6", "Variant A": 8, "Variant B (Winner)": 14.5, "Variant C (Stale)": 6.5 },
    { day: "Day 7", "Variant A": 8, "Variant B (Winner)": 15.1, "Variant C (Stale)": 6 },
  ];

  return (
    <Layout>
      {/* Celebration Modal */}
      {showCelebration && (
        <Celebration
          message="OPTIMIZATION COMPLETE"
          type="achievement"
          onComplete={() => setShowCelebration(false)}
        />
      )}

      {/* Breadcrumbs - Fade In */}
      <Reveal variant="fadeIn" delay={0.1} className="mb-6">
        <Breadcrumbs items={[
          { label: 'HOME', href: '/dashboard' },
          { label: 'THE LAB (A/B)' },
        ]} />
      </Reveal>

      <div className="space-y-8">
        {/* Header - Blur Effect */}
        <Reveal variant="blurInUp" duration={0.6}>
          <div className="mb-2 flex items-center gap-4">
            <div className="p-3 bg-primary/10 rounded border border-primary/30">
              <FlaskConical className="w-8 h-8 text-primary" />
            </div>
            <div>
              <h1 className="text-4xl font-bold mb-1 font-bebas tracking-wider text-white">
                <BlurText text="A/B AUTO-OPTIMIZATION LAYER" />
              </h1>
              <p className="text-muted-foreground font-mono text-sm">
                  // CONTINUOUS AI-DRIVEN TESTING // MAXIMIZE CAMPAIGN PERFORMANCE
              </p>
            </div>
          </div>
        </Reveal>

        {/* Variant Previews - Staggered Grid */}
        <motion.div
          className="grid md:grid-cols-3 gap-6"
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
        >
          {variants.map((variant, idx) => (
            <motion.div key={idx} variants={fadeInUp}>
              <HolographicCard
                className={`h-full p-0 group overflow-hidden border-white/10 ${variant.glitchColor} transition-shadow duration-500`}
                enableTilt
              >
                <div className="p-1 bg-gradient-to-r from-transparent via-white/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 absolute top-0 left-0 right-0 h-[1px]" />

                <div className="p-6 relative z-10">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <p className="text-[10px] text-white/40 font-mono mb-1 tracking-widest">{variant.type}</p>
                      <h3 className="font-bold text-lg text-white font-bebas tracking-wide">{variant.name}</h3>
                    </div>
                    <Badge className={`${variant.tagColor} border backdrop-blur-md`}>
                      {variant.status === "Running" ? <Play className="w-3 h-3 mr-1 animate-pulse" /> : <CheckCircle className="w-3 h-3 mr-1" />}
                      {variant.tag}
                    </Badge>
                  </div>

                  <div className="space-y-4 font-mono text-sm">
                    <div className="flex justify-between items-end border-b border-white/5 pb-2">
                      <span className="text-white/50 text-xs">CONVERSION RATE</span>
                      <span className="font-bold text-primary text-xl">{variant.conversion}</span>
                    </div>
                    <div className="flex justify-between items-end border-b border-white/5 pb-2">
                      <span className="text-white/50 text-xs">CTR</span>
                      <span className="font-medium text-white">{variant.ctr}</span>
                    </div>
                  </div>
                </div>

                {/* Glitch Overlay on Hover */}
                <div className="absolute inset-0 bg-white/5 opacity-0 group-hover:opacity-10 pointer-events-none mix-blend-overlay transition-opacity duration-100" />
              </HolographicCard>
            </motion.div>
          ))}
        </motion.div>

        {/* View All Experiments - Fade In */}
        <Reveal variant="fadeInUp" delay={0.3}>
          <HolographicCard className="p-4 border-dashed border-white/20 hover:border-primary/50 transition-colors group cursor-pointer">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                  <Swords className="w-5 h-5 text-white group-hover:text-primary transition-colors" />
                </div>
                <div>
                  <h3 className="font-bold text-white font-bebas tracking-wide text-lg">EXPERIMENT ARCHIVE</h3>
                  <p className="text-xs text-muted-foreground font-mono">ACCESS FULL EXPERIMENT HISTORY (FR20.3)</p>
                </div>
              </div>
              <div className="flex gap-3">
                <Button variant="outline" size="sm" className="border-white/10 hover:bg-white/5 hover:text-white font-mono text-xs">VIEW ARCHIVE</Button>
                <Button variant="hero" size="sm" className="bg-primary/20 text-primary border border-primary/50 hover:bg-primary/30 font-mono text-xs">
                  MANAGE EXPERIMENTS
                </Button>
              </div>
            </div>
          </HolographicCard>
        </Reveal>

        {/* Main Analytics Grid */}
        <div className="grid lg:grid-cols-2 gap-6">

          {/* Comparative Conversion Trend - Zoom In */}
          <Reveal variant="zoomIn" delay={0.4}>
            <HolographicCard className="p-6 h-full">
              <h3 className="text-lg font-bold text-white font-bebas tracking-wide mb-6 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-primary" />
                COMPARATIVE CONVERSION TREND
              </h3>
              <div className="h-64 w-full">
                {isLoadingChart ? (
                  <ChartSkeleton height="256px" />
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={conversionData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                      <XAxis
                        dataKey="day"
                        stroke="rgba(255,255,255,0.3)"
                        tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 10, fontFamily: 'monospace' }}
                        tickLine={false}
                        axisLine={false}
                      />
                      <YAxis
                        domain={[0, 16]}
                        stroke="rgba(255,255,255,0.3)"
                        tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 10, fontFamily: 'monospace' }}
                        tickLine={false}
                        axisLine={false}
                      />
                      <RechartsTooltip
                        contentStyle={{
                          backgroundColor: 'rgba(5, 5, 5, 0.9)',
                          border: '1px solid rgba(255,255,255,0.1)',
                          borderRadius: '4px',
                          boxShadow: '0 0 20px rgba(0,0,0,0.5)',
                          fontFamily: 'monospace',
                          fontSize: '12px'
                        }}
                        itemStyle={{ color: '#fff' }}
                      />
                      <Legend wrapperStyle={{ fontFamily: 'monospace', fontSize: '10px', paddingTop: '10px' }} />
                      <Line
                        type="monotone"
                        dataKey="Variant A"
                        stroke="#a855f7"
                        strokeWidth={2}
                        dot={{ r: 3, fill: '#a855f7', strokeWidth: 0 }}
                        activeDot={{ r: 6, stroke: '#fff', strokeWidth: 2 }}
                      />
                      <Line
                        type="monotone"
                        dataKey="Variant B (Winner)"
                        stroke="#00E0D0"
                        strokeWidth={3}
                        dot={{ r: 4, fill: '#00E0D0', strokeWidth: 0 }}
                        activeDot={{ r: 8, stroke: '#fff', strokeWidth: 2, strokeOpacity: 0.5 }}
                      />
                      <Line
                        type="monotone"
                        dataKey="Variant C (Stale)"
                        stroke="#ef4444"
                        strokeWidth={2}
                        dot={{ r: 3, fill: '#ef4444', strokeWidth: 0 }}
                        activeDot={{ r: 6, stroke: '#fff', strokeWidth: 2 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </div>
            </HolographicCard>
          </Reveal>

          {/* Causal Impact Summary - Slide In */}
          <Reveal variant="fadeInUp" delay={0.5}>
            <HolographicCard className="p-6 h-full flex flex-col">
              <div className="flex items-center gap-2 mb-6">
                <h3 className="text-lg font-bold text-white font-bebas tracking-wide">CAUSAL INSIGHTS & ACTIONS</h3>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <HelpCircle className="w-4 h-4 text-white/30 cursor-help hover:text-primary transition-colors" />
                    </TooltipTrigger>
                    <TooltipContent className="bg-black/90 border-white/10 text-white font-mono text-xs">
                      <p>AI analyzes variant performance to identify key factors driving success</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>

              <div className="flex-1 space-y-6">
                <div className="p-5 bg-primary/5 rounded border-l-2 border-primary relative overflow-hidden">
                  <div className="absolute top-0 right-0 p-2 opacity-10">
                    <Zap className="w-12 h-12 text-primary" />
                  </div>
                  <p className="text-sm mb-4 text-white/90 leading-relaxed">
                    <strong className="text-primary">VARIANT B++</strong> SUPERIOR PERFORMANCE IS DRIVEN BY HIGH ENGAGEMENT AND CLEAR VALUE PROPOSITION (FE-2).
                  </p>
                  <div className="space-y-3">
                    <div className="flex items-start gap-3">
                      <div className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 flex-shrink-0 shadow-[0_0_5px_#F59E0B]"></div>
                      <div className="text-xs text-white/70 font-mono">
                        <strong className="text-amber-400">CREATIVE OPTIMIZATION:</strong> High-contrast visuals resonate with target audience.
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <div className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 flex-shrink-0 shadow-[0_0_5px_#F59E0B]"></div>
                      <div className="text-xs text-white/70 font-mono">
                        <strong className="text-amber-400">CTA CLARITY:</strong> Direct Call-to-Action reduces friction.
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 flex-shrink-0 shadow-[0_0_5px_#10B981]"></div>
                      <div className="text-xs text-white/70 font-mono">
                        <strong className="text-emerald-400">AUDIENCE FIT:</strong> Aligns with "Early Adopter" segment.
                      </div>
                    </div>
                  </div>
                </div>

                <Button
                  variant="default"
                  className="w-full bg-primary text-primary-foreground hover:bg-primary/80 font-bold tracking-wider font-bebas text-lg h-12 shadow-[0_0_15px_rgba(0,224,208,0.3)]"
                  onClick={() => {
                    toast({
                      title: "SCALING PROTOCOL INITIATED",
                      description: "Winning variant is being scaled across all campaigns.",
                    });
                  }}
                >
                  <Zap className="w-4 h-4 mr-2 fill-black" />
                  SCALE WINNING VARIANT
                </Button>
              </div>
            </HolographicCard>
          </Reveal>
        </div>

        {/* Budget Reallocation Visualizer - Fade In Up */}
        <Reveal variant="fadeInUp" delay={0.6}>
          <HolographicCard className="p-6">
            <h3 className="text-lg font-bold text-white font-bebas tracking-wide mb-8 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-primary" />
              BUDGET REALLOCATION VISUALIZER
            </h3>
            <div className="grid md:grid-cols-2 gap-12">
              <div>
                <p className="text-xs text-white/40 font-mono mb-4 uppercase tracking-widest">Initial Allocation</p>
                <div className="space-y-4">
                  {[
                    { variant: "VARIANT A", budget: 40, color: "bg-purple-500", shadow: "shadow-[0_0_10px_#A855F7]" },
                    { variant: "VARIANT B", budget: 35, color: "bg-blue-500", shadow: "shadow-[0_0_10px_#3B82F6]" },
                    { variant: "VARIANT C", budget: 25, color: "bg-red-500", shadow: "shadow-[0_0_10px_#EF4444]" },
                  ].map((item, i) => (
                    <div key={i} className="flex items-center gap-4 group">
                      <span className="text-[10px] w-20 font-mono text-white/60">{item.variant}</span>
                      <div className="flex-1 h-2 bg-white/5 rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          whileInView={{ width: `${item.budget}%` }}
                          transition={{ duration: 1, delay: 0.5 }}
                          className={`h-full ${item.color} ${item.shadow}`}
                        />
                      </div>
                      <span className="text-xs font-bold w-12 text-right font-mono">{item.budget}%</span>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <div className="flex justify-between items-end mb-4">
                  <p className="text-xs text-white/40 font-mono uppercase tracking-widest">AI-Optimized Allocation</p>
                  <p className="text-xs text-primary font-bold font-mono animate-pulse">ROI PROJECTION: +18.5%</p>
                </div>
                <div className="space-y-4">
                  {[
                    { variant: "VARIANT A", budget: 20, color: "bg-purple-500/50", shadow: "" },
                    { variant: "VARIANT B", budget: 60, color: "bg-primary", shadow: "shadow-[0_0_15px_#00E0D0]" },
                    { variant: "VARIANT C", budget: 20, color: "bg-red-500/50", shadow: "" },
                  ].map((item, i) => (
                    <div key={i} className="flex items-center gap-4">
                      <span className="text-[10px] w-20 font-mono text-white/60">{item.variant}</span>
                      <div className="flex-1 h-2 bg-white/5 rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          whileInView={{ width: `${item.budget}%` }}
                          transition={{ duration: 1, delay: 0.5 }}
                          className={`h-full ${item.color} ${item.shadow}`}
                        />
                      </div>
                      <span className="text-xs font-bold w-12 text-right font-mono">{item.budget}%</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <Button
              variant="outline"
              size="lg"
              className="w-full mt-8 border-primary/30 text-primary hover:bg-primary/10 hover:text-white font-mono text-xs tracking-widest h-12"
              onClick={() => setShowBudgetDialog(true)}
            >
              EXECUTE DYNAMIC REALLOCATION
            </Button>
          </HolographicCard>
        </Reveal>
      </div>

      {/* Confirmation Dialog for Budget Reallocation */}
      <ConfirmationDialog
        open={showBudgetDialog}
        onOpenChange={setShowBudgetDialog}
        onConfirm={() => {
          toast({
            title: "PROTOCOL EXECUTED",
            description: "Budget optimized. Projected ROI: +18.5%",
          });
          setShowCelebration(true);
        }}
        title="CONFIRM REALLOCATION"
        description="This will reallocate budget based on AI recommendations. Variant B will receive 60% of the budget. This action cannot be easily undone."
        confirmText="EXECUTE"
        cancelText="ABORT"
        variant="default"
      />
    </Layout>
  );
};

export default ABTesting;
