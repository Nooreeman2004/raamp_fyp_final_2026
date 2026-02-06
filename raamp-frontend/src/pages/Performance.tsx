import { Button } from "@/components/ui/button";
import Layout from "@/components/Layout";
import { Badge } from "@/components/ui/badge";
import { BarChart3, TrendingUp, Target, DollarSign, Users, Activity } from "lucide-react";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeInUp, hoverLift, hoverScale } from "@/utils/animations";
import { HolographicCard } from "@/components/ui/holographic-card";
import { BlurText } from "@/components/ui/text-reveal";

const Performance = () => {
  const campaigns = [
    { name: "Loyalty Program Relaunch", period: "09/01/2023 - 10/31/2023", status: "COMPLETED" },
    { name: "Spring Engagement Boost", period: "03/01/2024 - 05/31/2024", status: "COMPLETED" },
    { name: "Summer Conversion Drive", period: "06/01/2023 - 08/15/2023", status: "COMPLETED" },
    { name: "Back-to-School Promo", period: "08/01/2023 - 09/15/2023", status: "COMPLETED" },
    { name: "Holiday Sales Blitz 2023", period: "11/15/2023 - 12/31/2023", status: "COMPLETED" },
    { name: "New Market Expansion", period: "04/01/2024 - 06/30/2024", status: "COMPLETED" }
  ];

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <Reveal variant="blurInUp">
          <div className="flex items-center gap-4 mb-2">
            <div className="p-3 bg-primary/10 rounded border border-primary/30">
              <Activity className="w-8 h-8 text-primary animate-pulse" />
            </div>
            <div>
              <h1 className="text-4xl font-bold mb-1 font-bebas tracking-wider text-white">
                <BlurText text="PERFORMANCE ATTRIBUTION ENGINE" />
              </h1>
              <p className="text-muted-foreground font-mono text-sm">
                  // CAUSAL AI ANALYSIS // ROAS OPTIMIZATION // DRIVER IDENTIFICATION
              </p>
            </div>
          </div>
        </Reveal>

        {/* Campaign Selection - Staggered Grid */}
        <Reveal variant="fadeInUp" delay={0.2}>
          <HolographicCard className="p-6 border-primary/30">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2 font-bebas tracking-wide text-white">
              <Target className="w-5 h-5 text-primary" />
              CAMPAIGN SELECTION
            </h2>
            <p className="text-xs text-muted-foreground mb-6 font-mono">
                // SELECT COMPLETED CAMPAIGN FOR DEEP DIVE ANALYSIS
            </p>
            <motion.div
              className="grid md:grid-cols-2 lg:grid-cols-3 gap-4"
              variants={staggerContainer}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
            >
              {campaigns.map((campaign, idx) => (
                <motion.div key={idx} variants={fadeInUp}>
                  <motion.div
                    variants={hoverLift}
                    initial="rest"
                    whileHover="hover"
                    className="p-4 bg-white/5 rounded border border-white/10 hover:border-primary/50 transition-all group cursor-pointer h-full flex flex-col justify-between relative overflow-hidden"
                  >
                    {/* Hover Glow */}
                    <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />

                    <div className="relative z-10">
                      <div className="mb-3">
                        <h3 className="font-bold mb-1 text-white group-hover:text-primary transition-colors font-bebas tracking-wide text-lg">{campaign.name.toUpperCase()}</h3>
                        <p className="text-[10px] text-muted-foreground font-mono">{campaign.period}</p>
                      </div>
                      <Badge variant="outline" className="mb-3 border-primary/30 text-primary bg-primary/5 font-mono text-[10px] rounded-sm">{campaign.status}</Badge>
                    </div>
                    <motion.div variants={hoverScale} whileTap="tap" className="relative z-10">
                      <Button size="sm" className="w-full bg-white/10 hover:bg-primary hover:text-primary-foreground text-white border border-white/20 hover:border-primary font-mono font-bold text-xs h-8">
                        ANALYZE DRIVERS
                      </Button>
                    </motion.div>
                  </motion.div>
                </motion.div>
              ))}
            </motion.div>
          </HolographicCard>
        </Reveal>

        {/* Strategic Recommendations - Staggered List */}
        <Reveal variant="fadeInUp" delay={0.3}>
          <HolographicCard className="p-6">
            <h2 className="text-xl font-bold mb-6 flex items-center gap-2 font-bebas tracking-wide text-white">
              <TrendingUp className="w-5 h-5 text-primary" />
              STRATEGIC RECOMMENDATIONS
            </h2>
            <motion.div
              className="space-y-4"
              variants={staggerContainer}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
            >
              {[
                {
                  title: "INCREASE SOCIAL MEDIA AD BUDGET",
                  description: "Social Media Ads show the highest positive impact on ROAS",
                  impact: "HIGH",
                  icon: TrendingUp
                },
                {
                  title: "OPTIMIZE EMAIL CAMPAIGNS",
                  description: "A/B test subject lines and CTA placement to boost performance",
                  impact: "MEDIUM",
                  icon: Target
                },
                {
                  title: "REALLOCATE LEGACY AD SPEND",
                  description: "Legacy channels exhibit negative influence on ROAS",
                  impact: "HIGH",
                  icon: DollarSign
                },
                {
                  title: "EXPLORE INFLUENCER PARTNERSHIPS",
                  description: "New influencer partnerships aligned with demographics to maximize reach",
                  impact: "MEDIUM",
                  icon: Users
                }
              ].map((rec, idx) => (
                <motion.div key={idx} variants={fadeInUp}>
                  <motion.div
                    whileHover={{ scale: 1.01, backgroundColor: "rgba(0, 224, 208, 0.05)" }}
                    className="p-4 bg-black/40 rounded border border-white/10 hover:border-primary/30 transition-colors"
                  >
                    <div className="flex items-start gap-4">
                      <div className="w-10 h-10 rounded bg-primary/10 border border-primary/20 flex items-center justify-center flex-shrink-0">
                        <rec.icon className="w-5 h-5 text-primary" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-bold text-white font-bebas tracking-wide">{rec.title}</h3>
                          <Badge variant={rec.impact === "HIGH" ? "default" : "secondary"} className={`font-mono text-[10px] rounded-sm ${rec.impact === "HIGH" ? "bg-primary text-primary-foreground hover:bg-primary/90" : "bg-white/10 text-white hover:bg-white/20"}`}>
                            {rec.impact} IMPACT
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground font-mono">{rec.description}</p>
                      </div>
                    </div>
                  </motion.div>
                </motion.div>
              ))}
            </motion.div>
            <Button variant="outline" className="w-full mt-4 border-white/10 text-muted-foreground hover:text-primary hover:border-primary/30 hover:bg-primary/5 font-mono text-xs">
              VIEW COMPLETE INSIGHTS LOG →
            </Button>
          </HolographicCard>
        </Reveal>

        {/* Performance Dashboard */}
        <Reveal variant="fadeInUp" delay={0.4}>
          <HolographicCard className="p-6">
            <h2 className="text-xl font-bold mb-6 flex items-center gap-2 font-bebas tracking-wide text-white">
              <BarChart3 className="w-5 h-5 text-primary" />
              CAMPAIGN PERFORMANCE DASHBOARD
            </h2>

            {/* Metrics Grid */}
            <div className="grid md:grid-cols-4 gap-4 mb-6">
              {[
                { label: "ROAS", value: "4.2x", trend: "+12%" },
                { label: "CONVERSION RATE", value: "8.3%", trend: "+18%" },
                { label: "TOTAL LEADS", value: "2,847", trend: "+24%" },
                { label: "COST PER LEAD", value: "$12.50", trend: "-15%" }
              ].map((metric, idx) => (
                <motion.div
                  key={idx}
                  whileHover={{ y: -5 }}
                  className="p-4 bg-white/5 rounded border border-white/10 hover:border-primary/30 transition-colors"
                >
                  <p className="text-[10px] text-muted-foreground font-mono mb-1">{metric.label}</p>
                  <p className="text-2xl font-bold mb-1 text-white font-bebas tracking-wider">{metric.value}</p>
                  <p className={`text-xs font-mono font-bold ${metric.trend.startsWith('+') ? 'text-primary' : 'text-red-400'}`}>{metric.trend}</p>
                </motion.div>
              ))}
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-bold mb-3 text-white font-bebas tracking-wide text-lg">LEAD GENERATION HEATMAP</h3>
                <Reveal variant="zoomIn" delay={0.5}>
                  <div className="aspect-square bg-black/40 rounded border border-white/10 flex items-center justify-center relative overflow-hidden group">
                    {/* Grid Overlay */}
                    <div className="absolute inset-0 bg-[linear-gradient(rgba(0,224,208,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(0,224,208,0.05)_1px,transparent_1px)] bg-[size:20px_20px]" />

                    <div className="text-center relative z-10">
                      <div className="w-20 h-20 rounded-full bg-primary/10 border border-primary/30 flex items-center justify-center mx-auto mb-4 animate-pulse">
                        <BarChart3 className="w-10 h-10 text-primary" />
                      </div>
                      <p className="text-xs text-primary font-mono">HEATMAP VISUALIZATION ACTIVE</p>
                    </div>
                  </div>
                </Reveal>
              </div>

              <div>
                <h3 className="font-bold mb-3 text-white font-bebas tracking-wide text-lg">CHANNEL ATTRIBUTION</h3>
                <div className="space-y-4">
                  {[
                    { channel: "SOCIAL MEDIA", contribution: 42, color: "bg-primary" },
                    { channel: "SEARCH ADS", contribution: 28, color: "bg-primary/70" },
                    { channel: "EMAIL", contribution: 18, color: "bg-primary/50" },
                    { channel: "DISPLAY", contribution: 12, color: "bg-primary/30" }
                  ].map((item, i) => (
                    <div key={i}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-mono text-muted-foreground">{item.channel}</span>
                        <span className="text-xs font-mono font-bold text-primary">{item.contribution}%</span>
                      </div>
                      <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          whileInView={{ width: `${item.contribution}%` }}
                          transition={{ duration: 1, delay: 0.2 + (i * 0.1), ease: "easeOut" }}
                          className={`h-full ${item.color} shadow-[0_0_10px_rgba(0,224,208,0.3)]`}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </HolographicCard>
        </Reveal>
      </div>
    </Layout>
  );
};

export default Performance;