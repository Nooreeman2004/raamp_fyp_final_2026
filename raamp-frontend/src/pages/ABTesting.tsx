import { Button } from "@/components/ui/button";
import Layout from "@/components/Layout";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Zap, FlaskConical, TrendingUp, CheckCircle, Play, Eye, HelpCircle } from "lucide-react";
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
import { staggerContainer, fadeInUp, hoverLift, blurInUp, zoomIn } from "@/utils/animations";

const ABTesting = () => {
  const { toast } = useToast();
  const [showBudgetDialog, setShowBudgetDialog] = useState(false);
  const [showCelebration, setShowCelebration] = useState(false);
  const [isLoadingChart, setIsLoadingChart] = useState(true);

  // Variant preview data
  const variants = [
    { 
      name: "Ad Creative Alpha", 
      type: "Creative Preview 1",
      conversion: "12.3%", 
      ctr: "1.8%",
      status: "Running",
      tag: "HIGH POTENTIAL",
      tagColor: "bg-amber-500/20 text-amber-400"
    },
    { 
      name: "Landing Page V2", 
      type: "Creative Preview 2",
      conversion: "8.9%", 
      ctr: "0.9%",
      status: "Running",
      tag: "Health Fair",
      tagColor: "bg-emerald-500/20 text-emerald-400",
      trend: "up"
    },
    { 
      name: "Email Subject Line", 
      type: "Text Snippet Preview",
      conversion: "15.1%", 
      ctr: "2.5%",
      status: "Concluded",
      tag: "PAST WINNER",
      tagColor: "bg-blue-500/20 text-blue-400"
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
          message="Budget Optimized! 🎉"
          type="achievement"
          onComplete={() => setShowCelebration(false)}
        />
      )}
      
      {/* Breadcrumbs - Fade In */}
      <Reveal variant="fadeIn" delay={0.1} className="mb-6">
        <Breadcrumbs items={[
          { label: 'Home', href: '/dashboard' },
          { label: 'A/B Testing' },
        ]} />
      </Reveal>

      <div className="space-y-6">
          {/* Header - Blur Effect */}
          <Reveal variant="blurInUp" duration={0.6}>
            <div className="mb-2">
              <h1 className="text-4xl font-bold mb-2">A/B Auto-Optimization Layer</h1>
              <p className="text-muted-foreground">
                Continuous AI-driven testing to identify winning variants and maximize campaign performance
              </p>
            </div>
          </Reveal>

          {/* Variant Previews - Staggered Grid */}
          <motion.div 
            className="grid md:grid-cols-3 gap-4"
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
          >
            {variants.map((variant, idx) => (
              <motion.div key={idx} variants={fadeInUp}>
                <motion.div variants={hoverLift} initial="rest" whileHover="hover" className="h-full">
                  <Card className="bg-card/50 backdrop-blur-sm border-primary/20 p-4 hover:border-primary/40 transition-colors h-full">
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-xs text-muted-foreground mb-1">{variant.type}</p>
                          <h3 className="font-bold text-sm">{variant.name}</h3>
                        </div>
                        <Badge className={variant.tagColor}>
                          {variant.status === "Running" ? <Play className="w-3 h-3 mr-1" /> : <CheckCircle className="w-3 h-3 mr-1" />}
                          {variant.tag}
                        </Badge>
                      </div>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Conversion Rate:</span>
                          <span className="font-bold text-primary">{variant.conversion}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">CTR:</span>
                          <span className="font-medium">{variant.ctr}</span>
                        </div>
                      </div>
                    </div>
                  </Card>
                </motion.div>
              </motion.div>
            ))}
          </motion.div>

          {/* View All Experiments - Fade In */}
          <Reveal variant="fadeInUp" delay={0.3}>
            <Card className="bg-card/50 backdrop-blur-sm border-primary/20 p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <FlaskConical className="w-5 h-5 text-primary" />
                  <div>
                    <h3 className="font-semibold">View All Experiments</h3>
                    <p className="text-xs text-muted-foreground">View & Manage (FR20.3)</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm">View All Experiments</Button>
                  <Button variant="hero" size="sm">View & Manage</Button>
                </div>
              </div>
            </Card>
          </Reveal>

          {/* Main Analytics Grid */}
          <div className="grid lg:grid-cols-2 gap-6">
            
            {/* Comparative Conversion Trend - Zoom In */}
            <Reveal variant="zoomIn" delay={0.4}>
              <Card className="bg-card/50 backdrop-blur-sm border-primary/20 p-6 hover:border-primary/40 transition-all h-full">
                <h3 className="text-lg font-semibold mb-4">Comparative Conversion Trend: Conversion Rate (%)</h3>
                <div className="h-64">
                  {isLoadingChart ? (
                    <ChartSkeleton height="256px" />
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={conversionData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                      <XAxis dataKey="day" stroke="rgba(255,255,255,0.5)" />
                      <YAxis domain={[0, 16]} stroke="rgba(255,255,255,0.5)" />
                      <RechartsTooltip 
                        contentStyle={{ 
                          backgroundColor: 'rgba(0,0,0,0.8)', 
                          border: '1px solid rgba(255,255,255,0.1)',
                          borderRadius: '8px'
                        }} 
                      />
                      <Legend />
                      <Line 
                        type="monotone" 
                        dataKey="Variant A" 
                        stroke="#a855f7" 
                        strokeWidth={2}
                        dot={{ r: 4 }}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="Variant B (Winner)" 
                        stroke="#60a5fa" 
                        strokeWidth={2}
                        dot={{ r: 4 }}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="Variant C (Stale)" 
                        stroke="#ef4444" 
                        strokeWidth={2}
                        dot={{ r: 4 }}
                      />
                      </LineChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </Card>
            </Reveal>

            {/* Causal Impact Summary - Slide In */}
            <Reveal variant="fadeInUp" delay={0.5}>
              <Card className="bg-card/50 backdrop-blur-sm border-primary/20 p-6 hover:border-primary/40 transition-all h-full">
                <div className="flex items-center gap-2 mb-4">
                  <h3 className="text-lg font-semibold">Causal Insights & Actions</h3>
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <HelpCircle className="w-4 h-4 text-muted-foreground cursor-help" />
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>AI analyzes variant performance to identify key factors driving success</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </div>
                <div className="space-y-4">
                  <div className="p-4 bg-primary/5 rounded-lg border border-primary/20">
                    <p className="text-sm mb-3">
                      <strong>Variant B++</strong>'s superior performance is driven by its high engagement and clear value proposition, increasing conversion intent (FE-2).
                    </p>
                    <div className="space-y-3">
                      <div className="flex items-start gap-2">
                        <div className="w-2 h-2 rounded-full bg-amber-400 mt-1.5 flex-shrink-0"></div>
                        <div className="text-sm">
                          <strong>Creative Optimization:</strong> High-contrast visuals in Variant B resonate better with the target audience.
                        </div>
                      </div>
                      <div className="flex items-start gap-2">
                        <div className="w-2 h-2 rounded-full bg-amber-400 mt-1.5 flex-shrink-0"></div>
                        <div className="text-sm">
                          <strong>CTA Clarity:</strong> Direct and prominent Call-to-Action reduces friction in the user journey.
                        </div>
                      </div>
                      <div className="flex items-start gap-2">
                        <div className="w-2 h-2 rounded-full bg-emerald-400 mt-1.5 flex-shrink-0"></div>
                        <div className="text-sm">
                          <strong>Audience Fit:</strong> Messaging strongly aligns with the <strong>"Early Adopter"</strong> segment identified by user intent data.
                        </div>
                      </div>
                    </div>
                  </div>
                  <Button 
                    variant="hero" 
                    className="w-full"
                    onClick={() => {
                      toast({
                        title: "Scaling Variant",
                        description: "Winning variant is being scaled across all campaigns.",
                      });
                    }}
                  >
                    Scale Winning Variant
                  </Button>
                </div>
              </Card>
            </Reveal>
          </div>

          {/* Budget Reallocation Visualizer - Fade In Up */}
          <Reveal variant="fadeInUp" delay={0.6}>
            <Card className="bg-card/50 backdrop-blur-sm border-primary/20 p-6 hover:border-primary/40 transition-all">
              <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
                <TrendingUp className="w-6 h-6 text-primary" />
                Budget Reallocation Visualizer
              </h3>
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <p className="text-sm text-muted-foreground mb-4">Initial Allocation</p>
                  <div className="space-y-3">
                    {[
                      { variant: "Variant A", budget: 40, color: "bg-purple-500" },
                      { variant: "Variant B", budget: 35, color: "bg-blue-500" },
                      { variant: "Variant C", budget: 25, color: "bg-red-500" },
                    ].map((item, i) => (
                      <div key={i} className="flex items-center gap-3">
                        <span className="text-sm w-20">{item.variant}</span>
                        <div className="flex-1 h-8 bg-muted rounded-full overflow-hidden">
                          <motion.div 
                            initial={{ width: 0 }}
                            whileInView={{ width: `${item.budget}%` }}
                            transition={{ duration: 1, delay: 0.5 }}
                            className={`h-full ${item.color}`} 
                          />
                        </div>
                        <span className="text-sm font-medium w-12 text-right">{item.budget}%</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground mb-1">AI-Optimized Allocation</p>
                  <p className="text-xs text-emerald-400 mb-4">Projected ROI: +18.5%</p>
                  <div className="space-y-3">
                    {[
                      { variant: "Variant A", budget: 20, color: "bg-purple-500" },
                      { variant: "Variant B", budget: 60, color: "bg-blue-500" },
                      { variant: "Variant C", budget: 20, color: "bg-red-500" },
                    ].map((item, i) => (
                      <div key={i} className="flex items-center gap-3">
                        <span className="text-sm w-20">{item.variant}</span>
                        <div className="flex-1 h-8 bg-muted rounded-full overflow-hidden">
                          <motion.div 
                            initial={{ width: 0 }}
                            whileInView={{ width: `${item.budget}%` }}
                            transition={{ duration: 1, delay: 0.5 }}
                            className={`h-full ${item.color}`} 
                          />
                        </div>
                        <span className="text-sm font-medium w-12 text-right">{item.budget}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              <Button 
                variant="hero" 
                size="lg" 
                className="w-full mt-6"
                onClick={() => setShowBudgetDialog(true)}
              >
                Execute Dynamic Budget Reallocation
              </Button>
            </Card>
          </Reveal>
        </div>

        {/* Confirmation Dialog for Budget Reallocation */}
        <ConfirmationDialog
        open={showBudgetDialog}
        onOpenChange={setShowBudgetDialog}
        onConfirm={() => {
          toast({
            title: "Budget Reallocated",
            description: "Your budget has been successfully optimized. Projected ROI: +18.5%",
          });
          setShowCelebration(true);
        }}
        title="Confirm Budget Reallocation"
        description="This will reallocate your budget based on AI recommendations. Variant B will receive 60% of the budget, while Variants A and C will be reduced to 20% each. This action cannot be easily undone."
        confirmText="Execute Reallocation"
        cancelText="Cancel"
        variant="default"
      />
    </Layout>
  );
};

export default ABTesting;