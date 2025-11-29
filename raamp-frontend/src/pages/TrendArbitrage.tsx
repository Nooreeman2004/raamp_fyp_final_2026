import { Button } from "@/components/ui/button";
import Layout from "@/components/Layout";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Zap, TrendingUp, Flame, Target, Users, MapPin } from "lucide-react";

const TrendArbitrage = () => {
  const trends = [
    {
      title: "AI-Powered Home Assistants",
      impact: "High",
      virality: 94,
      timeframe: "6-8 weeks peak",
      sentiment: "Positive (87%)"
    },
    {
      title: "Sustainable Fashion Movement",
      impact: "Medium",
      virality: 78,
      timeframe: "12+ weeks sustained",
      sentiment: "Very Positive (92%)"
    },
    {
      title: "Remote Work Tech Solutions",
      impact: "High",
      virality: 86,
      timeframe: "4-6 weeks peak",
      sentiment: "Positive (81%)"
    }
  ];

  return (
    <Layout>
      <div className="space-y-8">
          <div>
            <h1 className="text-4xl font-bold mb-2">Trend Arbitrage Detector</h1>
            <p className="text-muted-foreground">
              Capitalize on emerging trends before your competition with real-time predictive analytics
            </p>
          </div>

          {/* Live Trend Feed */}
          <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
            <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
              <Flame className="w-6 h-6 text-primary breathing-glow" />
              Live Trend Feed
            </h2>
            <div className="space-y-4">
              {trends.map((trend, idx) => (
                <div key={idx} className="p-4 bg-muted/50 rounded-lg border border-primary/10 hover:border-primary/30 transition-all group">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="text-lg font-bold group-hover:text-primary transition-colors">{trend.title}</h3>
                      <div className="flex gap-2 mt-2">
                        <Badge variant={trend.impact === "High" ? "default" : "secondary"}>
                          {trend.impact} Impact
                        </Badge>
                        <Badge variant="outline">Virality: {trend.virality}%</Badge>
                      </div>
                    </div>
                    <TrendingUp className="w-5 h-5 text-primary" />
                  </div>
                  <div className="grid md:grid-cols-2 gap-4 text-sm">
                    <p className="text-muted-foreground">
                      <span className="font-medium">Timeframe:</span> {trend.timeframe}
                    </p>
                    <p className="text-muted-foreground">
                      <span className="font-medium">Sentiment:</span> {trend.sentiment}
                    </p>
                  </div>
                  <Button variant="hero" size="sm" className="mt-3">
                    View Full Analysis
                  </Button>
                </div>
              ))}
            </div>
          </Card>

          {/* Trend Breakdown (Example for first trend) */}
          <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
            <h2 className="text-2xl font-bold mb-6">Detailed Trend Analysis: AI-Powered Home Assistants</h2>
            
            <div className="grid md:grid-cols-2 gap-6 mb-6">
              <div>
                <h3 className="text-lg font-bold mb-3 flex items-center gap-2">
                  <Target className="w-5 h-5 text-primary" />
                  Lifecycle Projection
                </h3>
                <p className="text-sm text-muted-foreground mb-2">
                  Advanced algorithms project a 6-8 week peak engagement period, followed by gradual decline over 3 months.
                </p>
                <div className="p-3 bg-muted/50 rounded-lg">
                  <div className="h-24 flex items-end gap-1">
                    {[30, 50, 75, 95, 100, 90, 70, 50, 30, 20].map((height, i) => (
                      <div key={i} className="flex-1 bg-primary/70 rounded-t" style={{ height: `${height}%` }}></div>
                    ))}
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-bold mb-3 flex items-center gap-2">
                  <MapPin className="w-5 h-5 text-primary" />
                  Geographic Hotspots
                </h3>
                <p className="text-sm text-muted-foreground mb-3">
                  Concentrated adoption in metropolitan areas with sustained growth in suburbs.
                </p>
                <div className="space-y-2">
                  {[
                    { area: "Urban Centers", intensity: 92 },
                    { area: "Tech Hubs", intensity: 88 },
                    { area: "Suburbs", intensity: 65 }
                  ].map((zone, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <span className="text-sm flex-1">{zone.area}</span>
                      <div className="w-32 h-2 bg-muted rounded-full overflow-hidden">
                        <div className="h-full bg-primary" style={{ width: `${zone.intensity}%` }}></div>
                      </div>
                      <span className="text-sm font-medium">{zone.intensity}%</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="p-4 bg-primary/5 rounded-lg border border-primary/20">
                <h4 className="font-bold mb-2 flex items-center gap-2">
                  <Users className="w-4 h-4 text-primary" />
                  Sentiment Analysis
                </h4>
                <p className="text-sm text-muted-foreground">
                  Positive sentiment prevails (87%), driven by convenience and novelty. Minor privacy concerns (13%) present opportunity for trust-focused messaging.
                </p>
              </div>

              <div className="p-4 bg-primary/5 rounded-lg border border-primary/20">
                <h4 className="font-bold mb-2">Competitive Landscape</h4>
                <p className="text-sm text-muted-foreground">
                  Tech startups and niche brands are early adopters, indicating a window for larger brands to gain market share.
                </p>
              </div>
            </div>

            <div className="mt-6 p-6 bg-primary/10 rounded-lg border border-primary/30">
              <h3 className="text-xl font-bold mb-2">Instant Campaign Launcher</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Capitalize on this trend immediately with AI-powered creative generation.
              </p>
              <Button variant="hero" size="lg" className="w-full">
                <Flame className="w-4 h-4 mr-2" />
                Launch Campaign Now
              </Button>
            </div>
          </Card>
      </div>
    </Layout>
  );
};

export default TrendArbitrage;
