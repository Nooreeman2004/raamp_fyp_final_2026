import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";
import { Zap, MapPin, Target, TrendingUp, Users } from "lucide-react";

const GeoIntent = () => {
  const [radius, setRadius] = useState([5]);
  const [businessName, setBusinessName] = useState("Artisan Coffee House");

  return (
    <div className="min-h-screen bg-background">
      {/* Top Navigation */}
      <nav className="border-b border-primary/10 bg-card/50 backdrop-blur-sm">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            <Link to="/dashboard" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                <Zap className="w-5 h-5 text-primary" />
              </div>
              <span className="text-xl font-bold">RAAMP</span>
            </Link>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="space-y-8">
          <div>
            <h1 className="text-4xl font-bold mb-2">Intelligent Geo-Intent Marketing Engine</h1>
            <p className="text-muted-foreground">
              Define hyper-local targeting zones and discover high-intent areas for maximum campaign impact
            </p>
          </div>

          <div className="grid lg:grid-cols-2 gap-6">
            {/* Targeting Zone Builder */}
            <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
              <h2 className="text-2xl font-bold mb-4">Targeting Zone Builder</h2>
              
              {/* Mock Map */}
              <div className="aspect-video bg-muted rounded-lg mb-4 relative overflow-hidden">
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <MapPin className="w-12 h-12 text-primary mx-auto mb-2 breathing-glow" />
                    <p className="text-sm text-muted-foreground">Interactive Map View</p>
                    <p className="text-xs text-muted-foreground mt-1">{businessName}</p>
                  </div>
                </div>
                <div className="absolute inset-0 bg-primary/5 animate-pulse"></div>
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

                <Button variant="hero" className="w-full">
                  <Target className="w-4 h-4 mr-2" />
                  Custom Zone Drawing
                </Button>
              </div>
            </Card>

            {/* Geo-Intent Insights */}
            <div className="space-y-6">
              <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
                <h3 className="text-xl font-bold mb-4">Live Geo-Intent Heatmap</h3>
                <div className="space-y-4">
                  {[
                    { area: "Downtown Core", score: 92, trend: "+12%" },
                    { area: "University District", score: 87, trend: "+8%" },
                    { area: "Tech Park Area", score: 81, trend: "+15%" },
                    { area: "Waterfront Zone", score: 76, trend: "+5%" }
                  ].map((zone, idx) => (
                    <div key={idx} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
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

              <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
                <h3 className="text-xl font-bold mb-4">Target Audience Insights</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-muted/50 rounded-lg">
                    <Users className="w-6 h-6 text-primary mb-2" />
                    <p className="text-2xl font-bold">12.4K</p>
                    <p className="text-xs text-muted-foreground">High-Intent Users</p>
                  </div>
                  <div className="p-4 bg-muted/50 rounded-lg">
                    <TrendingUp className="w-6 h-6 text-primary mb-2" />
                    <p className="text-2xl font-bold">+23%</p>
                    <p className="text-xs text-muted-foreground">Weekly Growth</p>
                  </div>
                </div>
              </Card>
            </div>
          </div>

          <Button variant="hero" size="lg" className="w-full">
            Deploy Geo-Targeted Campaign
          </Button>
        </div>
      </main>
    </div>
  );
};

export default GeoIntent;
