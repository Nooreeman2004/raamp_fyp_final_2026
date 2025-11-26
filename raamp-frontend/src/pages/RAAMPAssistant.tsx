import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Zap, MessageSquare, Lightbulb, AlertCircle, CheckCircle, Play } from "lucide-react";

const RAAMPAssistant = () => {
  const [message, setMessage] = useState("");

  const diagnostics = [
    { name: "Ad Account Health Check", status: "Advice", variant: "secondary" as const },
    { name: "Budget Allocation Discrepancies", status: "Review", variant: "default" as const },
    { name: "Pixel Implementation Verification", status: "Pending", variant: "secondary" as const },
    { name: "Creative Asset Compliance", status: "Failed", variant: "destructive" as const }
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
            <h1 className="text-4xl font-bold mb-2">RAAMP Assistant</h1>
            <p className="text-muted-foreground">
              Your AI Marketing Co-Pilot for insights, guidance, and troubleshooting
            </p>
          </div>

          <div className="grid lg:grid-cols-3 gap-6">
            {/* Interactive Chat Window */}
            <Card className="lg:col-span-2 p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
              <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
                <MessageSquare className="w-6 h-6 text-primary" />
                Interactive Chat Window
              </h2>
              <p className="text-sm text-muted-foreground mb-4">
                Chat with your AI Marketing Co-Pilot for insights and support
              </p>

              <div className="h-96 bg-muted/30 rounded-lg p-4 mb-4 overflow-y-auto space-y-4">
                {/* AI Message */}
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center flex-shrink-0">
                    <Zap className="w-4 h-4 text-primary" />
                  </div>
                  <div className="flex-1 bg-card p-3 rounded-lg">
                    <p className="text-sm">
                      Welcome! I'm RAAMP Assistant, your AI Marketing Co-Pilot. How can I assist you today with your campaign performance?
                    </p>
                  </div>
                </div>

                {/* User Message */}
                <div className="flex gap-3 justify-end">
                  <div className="bg-primary/20 p-3 rounded-lg max-w-[80%]">
                    <p className="text-sm">
                      I need to understand why my recent Facebook campaign underperformed last week.
                    </p>
                  </div>
                </div>

                {/* AI Response */}
                <div className="flex gap-3">
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
                </div>
              </div>

              <div className="flex gap-2">
                <Input
                  placeholder="Ask me anything about your campaigns..."
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  className="bg-background/50"
                />
                <Button variant="hero">
                  <MessageSquare className="w-4 h-4" />
                </Button>
              </div>
            </Card>

            {/* Contextual Guidance */}
            <div className="space-y-6">
              <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
                <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <Lightbulb className="w-5 h-5 text-primary" />
                  Contextual Guidance
                </h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Proactive tips and advice based on your current conversation
                </p>

                <div className="space-y-3">
                  <div className="p-3 bg-primary/5 rounded-lg border border-primary/20">
                    <h4 className="font-bold text-sm mb-2">What is Causal Inference in Marketing?</h4>
                    <p className="text-xs text-muted-foreground">
                      Causal inference helps you understand not just what happened, but why it happened. It identifies true cause-and-effect relationships.
                    </p>
                  </div>

                  <div className="p-3 bg-primary/5 rounded-lg border border-primary/20">
                    <h4 className="font-bold text-sm mb-2 flex items-center gap-2">
                      <Lightbulb className="w-3 h-3 text-primary" />
                      Tip: Reduce Audience Overlap Risk
                    </h4>
                    <p className="text-xs text-muted-foreground">
                      When launching new campaigns, actively exclude audiences from previous campaigns to avoid saturation and wasted ad spend.
                    </p>
                  </div>
                </div>
              </Card>

              {/* Quick Actions */}
              <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
                <h3 className="text-lg font-bold mb-3">Quick Actions</h3>
                <div className="space-y-2">
                  <Button variant="outline" className="w-full justify-start" size="sm">
                    <MessageSquare className="w-4 h-4 mr-2" />
                    Campaign Health Summary
                  </Button>
                  <Button variant="outline" className="w-full justify-start" size="sm">
                    <AlertCircle className="w-4 h-4 mr-2" />
                    Recent Alerts
                  </Button>
                  <Button variant="outline" className="w-full justify-start" size="sm">
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Best Practices Guide
                  </Button>
                </div>
              </Card>
            </div>
          </div>

          {/* Troubleshooting & Diagnostics */}
          <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
            <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
              <AlertCircle className="w-6 h-6 text-primary" />
              Troubleshooting & Diagnostics
            </h2>
            <p className="text-sm text-muted-foreground mb-6">
              Run health checks and get quick fixes for common campaign issues
            </p>

            <div className="grid md:grid-cols-2 gap-4">
              {diagnostics.map((item, idx) => (
                <div key={idx} className="p-4 bg-muted/50 rounded-lg border border-primary/10">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-bold text-sm">{item.name}</h3>
                    <Badge variant={item.variant}>{item.status}</Badge>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" className="flex-1">
                      <Play className="w-3 h-3 mr-1" />
                      Run Check
                    </Button>
                    <Button variant="hero" size="sm" className="flex-1">
                      Fix Issue
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default RAAMPAssistant;
