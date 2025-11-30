import { Button } from "@/components/ui/button";
import Layout from "@/components/Layout";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Zap, BarChart3, TrendingUp, Target, DollarSign, Users } from "lucide-react";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeInUp, hoverLift, blurInUp, zoomIn, hoverScale } from "@/utils/animations";

const Performance = () => {
  const campaigns = [
    { name: "Loyalty Program Relaunch", period: "09/01/2023 - 10/31/2023", status: "Completed" },
    { name: "Spring Engagement Boost", period: "03/01/2024 - 05/31/2024", status: "Completed" },
    { name: "Summer Conversion Drive", period: "06/01/2023 - 08/15/2023", status: "Completed" },
    { name: "Back-to-School Promo", period: "08/01/2023 - 09/15/2023", status: "Completed" },
    { name: "Holiday Sales Blitz 2023", period: "11/15/2023 - 12/31/2023", status: "Completed" },
    { name: "New Market Expansion", period: "04/01/2024 - 06/30/2024", status: "Completed" }
  ];

  return (
    <Layout>
      <div className="space-y-8">
          {/* Header */}
          <Reveal variant="blurInUp">
            <div>
              <h1 className="text-4xl font-bold mb-2">Performance Attribution Engine</h1>
              <p className="text-muted-foreground">
                Understand what truly drives campaign success with causal AI analysis
              </p>
            </div>
          </Reveal>

          {/* Campaign Selection - Staggered Grid */}
          <Reveal variant="fadeInUp" delay={0.2}>
            <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
              <h2 className="text-2xl font-bold mb-4">Campaign Selection</h2>
              <p className="text-sm text-muted-foreground mb-6">
                Select a completed campaign to analyze its performance drivers
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
                      className="p-4 bg-muted/50 rounded-lg border border-primary/10 hover:border-primary/30 transition-colors group cursor-pointer h-full flex flex-col justify-between"
                    >
                      <div>
                        <div className="mb-3">
                          <h3 className="font-bold mb-1 group-hover:text-primary transition-colors">{campaign.name}</h3>
                          <p className="text-xs text-muted-foreground">{campaign.period}</p>
                        </div>
                        <Badge variant="secondary" className="mb-3">{campaign.status}</Badge>
                      </div>
                      <motion.div variants={hoverScale} whileTap="tap">
                        <Button variant="hero" size="sm" className="w-full">
                          Analyze Drivers
                        </Button>
                      </motion.div>
                    </motion.div>
                  </motion.div>
                ))}
              </motion.div>
            </Card>
          </Reveal>

          {/* Strategic Recommendations - Staggered List */}
          <Reveal variant="fadeInUp" delay={0.3}>
            <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
              <h2 className="text-2xl font-bold mb-6">Strategic Recommendations</h2>
              <motion.div 
                className="space-y-4"
                variants={staggerContainer}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
              >
                {[
                  {
                    title: "Increase Social Media Ad Budget",
                    description: "Social Media Ads show the highest positive impact on ROAS",
                    impact: "High",
                    icon: TrendingUp
                  },
                  {
                    title: "Optimize Email Campaigns",
                    description: "A/B test subject lines and CTA placement to boost performance",
                    impact: "Medium",
                    icon: Target
                  },
                  {
                    title: "Reallocate Legacy Ad Spend",
                    description: "Legacy channels exhibit negative influence on ROAS",
                    impact: "High",
                    icon: DollarSign
                  },
                  {
                    title: "Explore Influencer Partnerships",
                    description: "New influencer partnerships aligned with demographics to maximize reach",
                    impact: "Medium",
                    icon: Users
                  }
                ].map((rec, idx) => (
                  <motion.div key={idx} variants={fadeInUp}>
                    <motion.div 
                      whileHover={{ scale: 1.01, backgroundColor: "rgba(var(--primary), 0.08)" }}
                      className="p-4 bg-primary/5 rounded-lg border border-primary/20 transition-colors"
                    >
                      <div className="flex items-start gap-4">
                        <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center flex-shrink-0">
                          <rec.icon className="w-5 h-5 text-primary" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-bold">{rec.title}</h3>
                            <Badge variant={rec.impact === "High" ? "default" : "secondary"}>
                              {rec.impact} Impact
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground">{rec.description}</p>
                        </div>
                      </div>
                    </motion.div>
                  </motion.div>
                ))}
              </motion.div>
              <Button variant="outline" className="w-full mt-4">
                View Complete Insights Log →
              </Button>
            </Card>
          </Reveal>

          {/* Performance Dashboard */}
          <Reveal variant="fadeInUp" delay={0.4}>
            <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
              <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
                <BarChart3 className="w-6 h-6 text-primary" />
                Campaign Performance Dashboard
              </h2>
              
              {/* Metrics Grid */}
              <div className="grid md:grid-cols-4 gap-4 mb-6">
                {[
                  { label: "ROAS", value: "4.2x", trend: "+12%" },
                  { label: "Conversion Rate", value: "8.3%", trend: "+18%" },
                  { label: "Total Leads", value: "2,847", trend: "+24%" },
                  { label: "Cost Per Lead", value: "$12.50", trend: "-15%" }
                ].map((metric, idx) => (
                  <motion.div 
                    key={idx} 
                    whileHover={{ y: -5 }}
                    className="p-4 bg-muted/50 rounded-lg hover:bg-muted transition-colors"
                  >
                    <p className="text-sm text-muted-foreground mb-1">{metric.label}</p>
                    <p className="text-2xl font-bold mb-1">{metric.value}</p>
                    <p className="text-sm text-primary font-medium">{metric.trend}</p>
                  </motion.div>
                ))}
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-bold mb-3">Lead Generation Heatmap</h3>
                  <Reveal variant="zoomIn" delay={0.5}>
                    <div className="aspect-square bg-muted/30 rounded-lg flex items-center justify-center border border-primary/10">
                      <div className="text-center">
                        <BarChart3 className="w-12 h-12 text-primary mx-auto mb-2 opacity-50" />
                        <p className="text-sm text-muted-foreground">Heatmap Visualization</p>
                      </div>
                    </div>
                  </Reveal>
                </div>

                <div>
                  <h3 className="font-bold mb-3">Channel Attribution</h3>
                  <div className="space-y-3">
                    {[
                      { channel: "Social Media", contribution: 42, color: "bg-primary" },
                      { channel: "Search Ads", contribution: 28, color: "bg-primary/70" },
                      { channel: "Email", contribution: 18, color: "bg-primary/50" },
                      { channel: "Display", contribution: 12, color: "bg-primary/30" }
                    ].map((item, i) => (
                      <div key={i}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm">{item.channel}</span>
                          <span className="text-sm font-medium">{item.contribution}%</span>
                        </div>
                        <div className="h-2 bg-muted rounded-full overflow-hidden">
                          <motion.div 
                            initial={{ width: 0 }}
                            whileInView={{ width: `${item.contribution}%` }}
                            transition={{ duration: 1, delay: 0.2 + (i * 0.1), ease: "easeOut" }}
                            className={`h-full ${item.color}`} 
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </Card>
          </Reveal>
      </div>
    </Layout>
  );
};

export default Performance;