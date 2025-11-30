import { useState } from "react";
import { Button } from "@/components/ui/button";
import Layout from "@/components/Layout";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Zap, MessageSquare, Lightbulb, AlertCircle, CheckCircle, Play } from "lucide-react";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeInUp, hoverScale, blurInUp, hoverLift } from "@/utils/animations";

const RAAMPAssistant = () => {
  const [message, setMessage] = useState("");

  const diagnostics = [
    { name: "Ad Account Health Check", status: "Advice", variant: "secondary" as const },
    { name: "Budget Allocation Discrepancies", status: "Review", variant: "default" as const },
    { name: "Pixel Implementation Verification", status: "Pending", variant: "secondary" as const },
    { name: "Creative Asset Compliance", status: "Failed", variant: "destructive" as const }
  ];

  return (
    <Layout>
      <div className="space-y-8">
          {/* Header */}
          <Reveal variant="blurInUp">
            <div>
              <h1 className="text-4xl font-bold mb-2">RAAMP Assistant</h1>
              <p className="text-muted-foreground">
                Your AI Marketing Co-Pilot for insights, guidance, and troubleshooting
              </p>
            </div>
          </Reveal>

          <div className="grid lg:grid-cols-3 gap-6">
            {/* Interactive Chat Window */}
            <Reveal variant="fadeInUp" delay={0.2} className="lg:col-span-2">
              <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10 h-full">
                <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
                  <MessageSquare className="w-6 h-6 text-primary" />
                  Interactive Chat Window
                </h2>
                <p className="text-sm text-muted-foreground mb-4">
                  Chat with your AI Marketing Co-Pilot for insights and support
                </p>

                <div className="h-96 bg-muted/30 rounded-lg p-4 mb-4 overflow-y-auto space-y-4">
                  {/* AI Message */}
                  <motion.div 
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3 }}
                    className="flex gap-3"
                  >
                    <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center flex-shrink-0">
                      <Zap className="w-4 h-4 text-primary" />
                    </div>
                    <div className="flex-1 bg-card p-3 rounded-lg">
                      <p className="text-sm">
                        Welcome! I'm RAAMP Assistant, your AI Marketing Co-Pilot. How can I assist you today with your campaign performance?
                      </p>
                    </div>
                  </motion.div>

                  {/* User Message */}
                  <motion.div 
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.6 }}
                    className="flex gap-3 justify-end"
                  >
                    <div className="bg-primary/20 p-3 rounded-lg max-w-[80%]">
                      <p className="text-sm">
                        I need to understand why my recent Facebook campaign underperformed last week.
                      </p>
                    </div>
                  </motion.div>

                  {/* AI Response */}
                  <motion.div 
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 1.2 }}
                    className="flex gap-3"
                  >
                    <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center flex-shrink-0">
                      <Zap className="w-4 h-4 text-primary" />
                    </div>
                    <div className="flex-1 bg-card p-3 rounded-lg">
                      <p className="text-sm mb-2">
                        Analyzing Facebook campaign 'WinterSale2023' (ID: 12345)...
                      </p>
                      <p className="text-sm">
                        Initial causal analysis suggests a significant negative causal effect from 'Audience Overlap with Q4 Retargeting' and a positive causal effect from 'Creative Variant B - Dynamic Carousel'. I'm actively processing more granular data.
                      </p>
                    </div>
                  </motion.div>
                </div>

                <div className="flex gap-2">
                  <Input
                    placeholder="Ask me anything about your campaigns..."
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    className="bg-background/50"
                  />
                  <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                    <Button variant="hero">
                      <MessageSquare className="w-4 h-4" />
                    </Button>
                  </motion.div>
                </div>
              </Card>
            </Reveal>

            {/* Right Column - Guidance & Actions */}
            <div className="space-y-6">
              {/* Contextual Guidance */}
              <Reveal variant="fadeInUp" delay={0.3}>
                <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
                  <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                    <Lightbulb className="w-5 h-5 text-primary" />
                    Contextual Guidance
                  </h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Proactive tips and advice based on your current conversation
                  </p>

                  <motion.div 
                    className="space-y-3"
                    variants={staggerContainer}
                    initial="hidden"
                    animate="visible"
                  >
                    <motion.div variants={fadeInUp} className="p-3 bg-primary/5 rounded-lg border border-primary/20">
                      <h4 className="font-bold text-sm mb-2">What is Causal Inference in Marketing?</h4>
                      <p className="text-xs text-muted-foreground">
                        Causal inference helps you understand not just what happened, but why it happened. It identifies true cause-and-effect relationships.
                      </p>
                    </motion.div>

                    <motion.div variants={fadeInUp} className="p-3 bg-primary/5 rounded-lg border border-primary/20">
                      <h4 className="font-bold text-sm mb-2 flex items-center gap-2">
                        <Lightbulb className="w-3 h-3 text-primary" />
                        Tip: Reduce Audience Overlap Risk
                      </h4>
                      <p className="text-xs text-muted-foreground">
                        When launching new campaigns, actively exclude audiences from previous campaigns to avoid saturation and wasted ad spend.
                      </p>
                    </motion.div>
                  </motion.div>
                </Card>
              </Reveal>

              {/* Quick Actions */}
              <Reveal variant="fadeInUp" delay={0.4}>
                <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
                  <h3 className="text-lg font-bold mb-3">Quick Actions</h3>
                  <div className="space-y-2">
                    {[
                      { icon: MessageSquare, text: "Campaign Health Summary" },
                      { icon: AlertCircle, text: "Recent Alerts" },
                      { icon: CheckCircle, text: "Best Practices Guide" }
                    ].map((action, idx) => (
                      <motion.div key={idx} variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                        <Button variant="outline" className="w-full justify-start" size="sm">
                          <action.icon className="w-4 h-4 mr-2" />
                          {action.text}
                        </Button>
                      </motion.div>
                    ))}
                  </div>
                </Card>
              </Reveal>
            </div>
          </div>

          {/* Troubleshooting & Diagnostics */}
          <Reveal variant="fadeInUp" delay={0.5}>
            <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
              <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
                <AlertCircle className="w-6 h-6 text-primary" />
                Troubleshooting & Diagnostics
              </h2>
              <p className="text-sm text-muted-foreground mb-6">
                Run health checks and get quick fixes for common campaign issues
              </p>

              <motion.div 
                className="grid md:grid-cols-2 gap-4"
                variants={staggerContainer}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
              >
                {diagnostics.map((item, idx) => (
                  <motion.div key={idx} variants={fadeInUp}>
                    <motion.div 
                      variants={hoverLift} 
                      initial="rest" 
                      whileHover="hover"
                      className="p-4 bg-muted/50 rounded-lg border border-primary/10"
                    >
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="font-bold text-sm">{item.name}</h3>
                        <Badge variant={item.variant}>{item.status}</Badge>
                      </div>
                      <div className="flex gap-2">
                        <motion.div className="flex-1" variants={hoverScale} whileTap="tap">
                          <Button variant="outline" size="sm" className="w-full">
                            <Play className="w-3 h-3 mr-1" />
                            Run Check
                          </Button>
                        </motion.div>
                        <motion.div className="flex-1" variants={hoverScale} whileTap="tap">
                          <Button variant="hero" size="sm" className="w-full">
                            Fix Issue
                          </Button>
                        </motion.div>
                      </div>
                    </motion.div>
                  </motion.div>
                ))}
              </motion.div>
            </Card>
          </Reveal>
      </div>
    </Layout>
  );
};

export default RAAMPAssistant;