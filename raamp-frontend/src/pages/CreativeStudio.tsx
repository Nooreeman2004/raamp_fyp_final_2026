import { useState } from "react";
import { Button } from "@/components/ui/button";
import Layout from "@/components/Layout";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Zap, Sparkles, Image, FileText, MessageSquare, X } from "lucide-react";

type Variant = {
  id: number;
  tone: string;
  caption?: string;
  hashtags?: string;
  copy?: string;
  imageColor?: string;
  imageLabel?: string;
};

type AssetType = "instagram" | "adcopy" | "whatsapp";

const CreativeStudio = () => {
  const [campaignIdea, setCampaignIdea] = useState("");
  const [selectedAsset, setSelectedAsset] = useState<AssetType | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const instagramVariants: Variant[] = [
    {
      id: 1,
      tone: "Vibrant & Direct",
      caption: "☀️ Summer is here, and so is your new favorite organic sip! Fuel your glow from the inside out. Tap to shop!",
      hashtags: "#OrganicSummer #CleanSips #MillennialFuel #SustainableLiving"
    },
    {
      id: 2,
      tone: "Informative & Engaging",
      caption: "Did you know our new line is 100% sustainably sourced? Choose health for you and the planet. Learn more about our process on our website.",
      hashtags: "#SustainabilityGoals #EcoFriendlyDrinks #HealthConscious"
    },
    {
      id: 3,
      tone: "Curious & Playful",
      caption: "Your favorite organic ingredients, blended for the perfect summer escape. Which flavor are you trying first? Tell us below! 👇",
      hashtags: "#SmoothieTime #FlavorChallenge #TreatYourself #OrganicLife"
    }
  ];

  const adCopyVariants: Variant[] = [
    {
      id: 1,
      tone: "Urgent/FOMO",
      imageColor: "bg-success",
      imageLabel: "Ad Image 1\n(Product Focus)",
      copy: "Don't just sip, thrive! Our new organic line is selling out fast. Get yours before the summer ends. Limited availability. Shop now!"
    },
    {
      id: 2,
      tone: "Benefit-focused",
      imageColor: "bg-primary",
      imageLabel: "Ad Image 2\n(Lifestyle Shot)",
      copy: "Finally, a smoothie line that's good for you AND the planet. Fuel your busy urban life with sustainable, organic goodness. Discover the difference today."
    },
    {
      id: 3,
      tone: "Question/Engaging",
      imageColor: "bg-destructive",
      imageLabel: "Ad Image 3\n(Call to Action)",
      copy: "Tired of artificial ingredients? Reset your routine with our delicious, clean-label smoothies. Which flavor boosts your day? Click to choose!"
    }
  ];

  const whatsappVariants: Variant[] = [
    {
      id: 1,
      tone: "Direct Order Funnel",
      copy: "Hi [Name]! Ready for summer refreshment? Our organic smoothie line is now 15% off for you. Reply 'YES' to see the menu & order link instantly."
    },
    {
      id: 2,
      tone: "Educational/Soft Sell",
      copy: "Hey [Name], want a health upgrade? We just launched our organic line, and we think you'll love the sustainability story. Check out our mission here [Link]. Reply 'SMOOTHIE' for a discount code!"
    },
    {
      id: 3,
      tone: "Personalized Recommendation",
      copy: "Welcome back, [Name]! Since you loved [Old Flavor], we recommend our new 'Berry Boost'—it's 100% organic and hits those same fresh notes. Shop now: [Link]."
    }
  ];

  const openDialog = (assetType: AssetType) => {
    setSelectedAsset(assetType);
    setIsDialogOpen(true);
  };

  const getDialogTitle = () => {
    if (selectedAsset === "instagram") return "Instagram Story - 3 Variants";
    if (selectedAsset === "adcopy") return "Ad Copy Variations - 3 Variants";
    if (selectedAsset === "whatsapp") return "WhatsApp Campaign - 3 Variants";
    return "";
  };

  const getVariants = () => {
    if (selectedAsset === "instagram") return instagramVariants;
    if (selectedAsset === "adcopy") return adCopyVariants;
    if (selectedAsset === "whatsapp") return whatsappVariants;
    return [];
  };

  return (
    <Layout>
      <div className="space-y-8">
          <div>
            <h1 className="text-4xl font-bold mb-2 text-foreground">Generative Creative Studio</h1>
            <p className="text-muted-foreground">
              Transform ideas into high-performing campaigns with AI-powered creative generation.
            </p>
          </div>

          <div className="grid lg:grid-cols-2 gap-6">
            {/* Campaign Idea Input */}
            <Card className="p-6 card-shadow bg-card border-border">
              <h2 className="text-xl font-bold mb-2 flex items-center gap-2 text-foreground">
                <Sparkles className="w-5 h-5 text-primary" />
                Campaign Idea Input
              </h2>
              <p className="text-sm text-muted-foreground mb-4">
                Describe your campaign vision in natural language. Our AI will transform it into actionable creative assets.
              </p>
              <Textarea
                placeholder='E.g., "Create a summer promotion campaign for our new smoothie line targeting health-conscious millennials in urban areas. Emphasize organic ingredients and sustainability."'
                value={campaignIdea}
                onChange={(e) => setCampaignIdea(e.target.value)}
                className="min-h-32 mb-4 bg-input text-foreground border-border"
              />
              <Button className="w-full bg-primary hover:bg-primary/90 text-primary-foreground">
                <Sparkles className="w-4 h-4 mr-2" />
                Generate Creative Brief
              </Button>
            </Card>

            {/* AI-Generated Assets */}
            <Card className="p-6 card-shadow bg-card border-border">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2 text-foreground">
                <Zap className="w-5 h-5 text-primary" />
                AI-Generated Assets
              </h2>
              <div className="space-y-3">
                <div className="p-4 bg-muted/50 rounded-lg hover:bg-muted transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 rounded-lg bg-card flex items-center justify-center">
                        <Image className="w-5 h-5 text-primary" />
                      </div>
                      <div>
                        <p className="font-medium text-foreground">Instagram Story</p>
                        <p className="text-sm text-success">Ready - Caption & 3 Hashtag Variants</p>
                      </div>
                    </div>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className="text-primary hover:text-primary/80"
                      onClick={() => openDialog("instagram")}
                    >
                      View Variants
                    </Button>
                  </div>
                </div>

                <div className="p-4 bg-muted/50 rounded-lg hover:bg-muted transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 rounded-lg bg-card flex items-center justify-center">
                        <FileText className="w-5 h-5 text-primary" />
                      </div>
                      <div>
                        <p className="font-medium text-foreground">Ad Copy Variations</p>
                        <p className="text-sm text-success">Ready - 3 unique ad copy blocks available</p>
                      </div>
                    </div>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className="text-primary hover:text-primary/80"
                      onClick={() => openDialog("adcopy")}
                    >
                      View Variants
                    </Button>
                  </div>
                </div>

                <div className="p-4 bg-muted/50 rounded-lg hover:bg-muted transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 rounded-lg bg-card flex items-center justify-center">
                        <MessageSquare className="w-5 h-5 text-primary" />
                      </div>
                      <div>
                        <p className="font-medium text-foreground">WhatsApp Campaign</p>
                        <p className="text-sm text-success">Ready - 3 unique message flows available</p>
                      </div>
                    </div>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className="text-primary hover:text-primary/80"
                      onClick={() => openDialog("whatsapp")}
                    >
                      View Variants
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>

        {/* Variants Dialog */}
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-6xl bg-card border-border p-6">
          <DialogHeader>
            <DialogTitle className="text-2xl font-bold text-foreground">{getDialogTitle()}</DialogTitle>
            <DialogDescription className="text-muted-foreground">
              Compare the 3 generated variants. Click 'Copy' on your favorite one.
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid md:grid-cols-3 gap-6 mt-4">
            {getVariants().map((variant) => (
              <div key={variant.id} className="rounded-xl border-2 border-primary/30 bg-card/50 p-4 space-y-4">
                <div>
                  <h3 className="font-bold text-foreground mb-1">Variant {variant.id}</h3>
                  <p className="text-sm text-primary">Tone: {variant.tone}</p>
                </div>

                {selectedAsset === "adcopy" && variant.imageColor && (
                  <div className={`${variant.imageColor} rounded-lg aspect-video flex items-center justify-center`}>
                    <div className="text-center font-bold text-white whitespace-pre-line">
                      {variant.imageLabel}
                    </div>
                  </div>
                )}

                {variant.caption && (
                  <div>
                    <p className="text-xs text-muted-foreground italic mb-2">Caption:</p>
                    <div className="bg-muted/50 p-3 rounded-lg text-sm text-foreground">
                      {variant.caption}
                    </div>
                  </div>
                )}

                {variant.copy && (
                  <div>
                    <p className="text-xs text-muted-foreground italic mb-2">Generated Copy:</p>
                    <div className="bg-muted/50 p-3 rounded-lg text-sm text-foreground">
                      {variant.copy}
                    </div>
                  </div>
                )}

                {variant.hashtags && (
                  <div>
                    <p className="text-xs text-muted-foreground italic mb-2">Hashtags:</p>
                    <div className="bg-muted/50 p-3 rounded-lg text-sm text-foreground">
                      {variant.hashtags}
                    </div>
                  </div>
                )}

                <Button className="w-full bg-primary hover:bg-primary/90 text-primary-foreground">
                  Copy & Select
                </Button>
              </div>
            ))}
          </div>

          <div className="flex justify-end mt-4">
            <Button 
              variant="ghost" 
              onClick={() => setIsDialogOpen(false)}
              className="text-muted-foreground hover:text-foreground"
            >
              Close
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </Layout>
  );
};

export default CreativeStudio;
