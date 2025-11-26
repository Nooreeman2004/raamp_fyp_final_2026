import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Zap, BarChart3, TrendingUp, Target, DollarSign, Users } from "lucide-react";

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
            <h1 className="text-4xl font-bold mb-2">Performance Attribution Engine</h1>
            <p className="text-muted-foreground">
              Understand what truly drives campaign success with causal AI analysis
            </p>
          </div>

          {/* Campaign Selection */}
          <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
            <h2 className="text-2xl font-bold mb-4">Campaign Selection</h2>
            <p className="text-sm text-muted-foreground mb-6">
              Select a completed campaign to analyze its performance drivers
            </p>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {campaigns.map((campaign, idx) => (
                <div key={idx} className="p-4 bg-muted/50 rounded-lg border border-primary/10 hover:border-primary/30 transition-all group">
                  <div className="mb-3">
                    <h3 className="font-bold mb-1 group-hover:text-primary transition-colors">{campaign.name}</h3>
                    <p className="text-xs text-muted-foreground">{campaign.period}</p>
                  </div>
                  <Badge variant="secondary" className="mb-3">{campaign.status}</Badge>
                  <Button variant="hero" size="sm" className="w-full">
                    Analyze Drivers
                  </Button>
                </div>
              ))}
            </div>
          </Card>

          {/* Strategic Recommendations */}
          <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
            <h2 className="text-2xl font-bold mb-6">Strategic Recommendations</h2>
            <div className="space-y-4">
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
                <div key={idx} className="p-4 bg-primary/5 rounded-lg border border-primary/20 hover:bg-primary/10 transition-colors">
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
                </div>
              ))}
            </div>
            <Button variant="outline" className="w-full mt-4">
              View Complete Insights Log →
            </Button>
          </Card>

          {/* Performance Dashboard */}
          <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
            <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
              <BarChart3 className="w-6 h-6 text-primary" />
              Campaign Performance Dashboard
            </h2>
            <div className="grid md:grid-cols-4 gap-4 mb-6">
              {[
                { label: "ROAS", value: "4.2x", trend: "+12%" },
                { label: "Conversion Rate", value: "8.3%", trend: "+18%" },
                { label: "Total Leads", value: "2,847", trend: "+24%" },
                { label: "Cost Per Lead", value: "$12.50", trend: "-15%" }
              ].map((metric, idx) => (
                <div key={idx} className="p-4 bg-muted/50 rounded-lg">
                  <p className="text-sm text-muted-foreground mb-1">{metric.label}</p>
                  <p className="text-2xl font-bold mb-1">{metric.value}</p>
                  <p className="text-sm text-primary font-medium">{metric.trend}</p>
                </div>
              ))}
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-bold mb-3">Lead Generation Heatmap</h3>
                <div className="aspect-square bg-muted/30 rounded-lg flex items-center justify-center">
                  <div className="text-center">
                    <BarChart3 className="w-12 h-12 text-primary mx-auto mb-2" />
                    <p className="text-sm text-muted-foreground">Heatmap Visualization</p>
                  </div>
                </div>
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
                        <div className={`h-full ${item.color}`} style={{ width: `${item.contribution}%` }}></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default Performance;
