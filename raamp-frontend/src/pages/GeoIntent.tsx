import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";
import { MapPin, Target, TrendingUp, Users } from "lucide-react";
import Layout from "@/components/Layout";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeInUp, hoverScale, blurInUp, hoverLift, zoomIn } from "@/utils/animations";

const GeoIntent = () => {
  const [radius, setRadius] = useState([5]);
  const [businessName, setBusinessName] = useState("Artisan Coffee House");

  return (
    <Layout>
      <div className="space-y-8">
          {/* Header */}
          <Reveal variant="blurInUp">
            <div>
              <h1 className="text-4xl font-bold mb-2">Intelligent Geo-Intent Marketing Engine</h1>
              <p className="text-muted-foreground">
                Define hyper-local targeting zones and discover high-intent areas for maximum campaign impact
              </p>
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
              <motion.div variants={hoverLift} initial="rest" whileHover="hover" className="h-full">
                <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10 h-full">
                  <h2 className="text-2xl font-bold mb-4">Targeting Zone Builder</h2>
                  
                  {/* Mock Map */}
                  <div className="aspect-video bg-muted rounded-lg mb-4 relative overflow-hidden group cursor-crosshair">
                    <div className="absolute inset-0 flex items-center justify-center z-10">
                      <div className="text-center">
                        <Reveal variant="zoomIn" delay={0.4}>
                          <MapPin className="w-12 h-12 text-primary mx-auto mb-2 breathing-glow group-hover:scale-110 transition-transform" />
                        </Reveal>
                        <p className="text-sm text-muted-foreground">Interactive Map View</p>
                        <p className="text-xs text-muted-foreground mt-1">{businessName}</p>
                      </div>
                    </div>
                    <div className="absolute inset-0 bg-primary/5 animate-pulse group-hover:bg-primary/10 transition-colors"></div>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium mb-2 block">Zone Radius: {radius[0]} km</label>
                      <Slider
                        value={radius}
                        onValueChange={setRadius}
                        max={50}
                        min={1}
                        step={1}
                        className="mb-2"
                      />
                    </div>

                    <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                      <Button variant="hero" className="w-full">
                        <Target className="w-4 h-4 mr-2" />
                        Custom Zone Drawing
                      </Button>
                    </motion.div>
                  </div>
                </Card>
              </motion.div>
            </motion.div>

            {/* Right Column - Insights */}
            <div className="space-y-6">
              {/* Geo-Intent Insights */}
              <motion.div variants={fadeInUp}>
                <motion.div variants={hoverLift} initial="rest" whileHover="hover">
                  <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
                    <h3 className="text-xl font-bold mb-4">Live Geo-Intent Heatmap</h3>
                    <div className="space-y-4">
                      {[
                        { area: "Downtown Core", score: 92, trend: "+12%" },
                        { area: "University District", score: 87, trend: "+8%" },
                        { area: "Tech Park Area", score: 81, trend: "+15%" },
                        { area: "Waterfront Zone", score: 76, trend: "+5%" }
                      ].map((zone, idx) => (
                        <div key={idx} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg hover:bg-muted transition-colors">
                          <div className="flex items-center gap-3">
                            <div className="w-2 h-2 rounded-full bg-primary breathing-glow"></div>
                            <div>
                              <p className="font-medium">{zone.area}</p>
                              <p className="text-xs text-muted-foreground">Intent Score: {zone.score}/100</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="text-sm font-bold text-primary">{zone.trend}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </Card>
                </motion.div>
              </motion.div>

              {/* Target Audience Insights */}
              <motion.div variants={fadeInUp}>
                <motion.div variants={hoverLift} initial="rest" whileHover="hover">
                  <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
                    <h3 className="text-xl font-bold mb-4">Target Audience Insights</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-4 bg-muted/50 rounded-lg hover:bg-muted transition-colors">
                        <Users className="w-6 h-6 text-primary mb-2" />
                        <p className="text-2xl font-bold">12.4K</p>
                        <p className="text-xs text-muted-foreground">High-Intent Users</p>
                      </div>
                      <div className="p-4 bg-muted/50 rounded-lg hover:bg-muted transition-colors">
                        <TrendingUp className="w-6 h-6 text-primary mb-2" />
                        <p className="text-2xl font-bold">+23%</p>
                        <p className="text-xs text-muted-foreground">Weekly Growth</p>
                      </div>
                    </div>
                  </Card>
                </motion.div>
              </motion.div>
            </div>
          </motion.div>

        <Reveal variant="fadeInUp" delay={0.6}>
          <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
            <Button variant="hero" size="lg" className="w-full">
              Deploy Geo-Targeted Campaign
            </Button>
          </motion.div>
        </Reveal>
      </div>
    </Layout>
  );
};

export default GeoIntent;