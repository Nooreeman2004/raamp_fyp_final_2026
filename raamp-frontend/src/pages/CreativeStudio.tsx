import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Zap, Sparkles, Image, FileText, Video, Share2 } from "lucide-react";

const CreativeStudio = () => {
  const [campaignIdea, setCampaignIdea] = useState("");

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
            <h1 className="text-4xl font-bold mb-2">Generative Creative Studio</h1>
            <p className="text-muted-foreground">
              Transform ideas into high-performing campaigns with AI-powered creative generation
            </p>
          </div>

          <div className="grid lg:grid-cols-2 gap-6">
            {/* Campaign Idea Input */}
            <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10 lg:col-span-2">
              <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
                <Sparkles className="w-6 h-6 text-primary" />
                Campaign Idea Input
              </h2>
              <p className="text-sm text-muted-foreground mb-4">
                Describe your campaign vision in natural language. Our AI will transform it into actionable creative assets.
              </p>
              <Textarea
                placeholder="E.g., 'Create a summer promotion campaign for our new smoothie line targeting health-conscious millennials in urban areas. Emphasize organic ingredients and sustainability.'"
                value={campaignIdea}
                onChange={(e) => setCampaignIdea(e.target.value)}
                className="min-h-32 mb-4 bg-background/50"
              />
              <Button variant="hero" size="lg" className="w-full">
                <Sparkles className="w-4 h-4 mr-2" />
                Generate Creative Brief
              </Button>
            </Card>

            {/* Generated Assets Preview */}
            <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
              <h3 className="text-xl font-bold mb-4">AI-Generated Assets</h3>
              <div className="space-y-3">
                {[
                  { icon: Image, title: "Instagram Story", status: "Ready" },
                  { icon: Video, title: "Instagram Reel", status: "Generating..." },
                  { icon: FileText, title: "Ad Copy Variations", status: "Ready" },
                  { icon: Share2, title: "WhatsApp Campaign", status: "Ready" }
                ].map((asset, idx) => (
                  <div key={idx} className="flex items-center justify-between p-4 bg-muted/50 rounded-lg hover:bg-muted/70 transition-colors">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                        <asset.icon className="w-5 h-5 text-primary" />
                      </div>
                      <div>
                        <p className="font-medium">{asset.title}</p>
                        <p className="text-xs text-muted-foreground">{asset.status}</p>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm">Preview</Button>
                  </div>
                ))}
              </div>
            </Card>

            {/* Brand Voice Settings */}
            <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
              <h3 className="text-xl font-bold mb-4">Active Brand Voice</h3>
              <div className="space-y-4">
                <div className="p-4 bg-primary/5 rounded-lg border border-primary/20">
                  <p className="font-medium mb-2">Tone: Professional & Innovative</p>
                  <p className="text-sm text-muted-foreground mb-3">
                    "Empowering, slightly futuristic, data-driven yet approachable"
                  </p>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">Brand Adherence</span>
                    <span className="text-sm font-bold text-primary">92%</span>
                  </div>
                </div>
                <Link to="/profile/brand-settings">
                  <Button variant="outline" className="w-full">
                    Adjust Brand Settings
                  </Button>
                </Link>
              </div>
            </Card>
          </div>

          {/* Creative Variations */}
          <Card className="p-6 card-shadow bg-card/70 backdrop-blur-sm border-primary/10">
            <h3 className="text-xl font-bold mb-4">Campaign Variations (A/B Test Ready)</h3>
            <div className="grid md:grid-cols-3 gap-4">
              {[1, 2, 3].map((variant) => (
                <div key={variant} className="p-4 bg-muted/50 rounded-lg border border-primary/10">
                  <div className="aspect-square bg-background rounded-lg mb-3 flex items-center justify-center">
                    <Sparkles className="w-8 h-8 text-primary/50" />
                  </div>
                  <p className="font-medium mb-1">Variant {variant}</p>
                  <p className="text-xs text-muted-foreground mb-3">Headline: "Summer Refresh"</p>
                  <Button variant="outline" size="sm" className="w-full">Select</Button>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default CreativeStudio;
