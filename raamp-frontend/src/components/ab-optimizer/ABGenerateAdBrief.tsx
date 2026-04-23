import { useState } from "react";
import { motion } from "framer-motion";
import { Megaphone, DollarSign, Users, TrendingUp, Target, Lightbulb, CheckCircle, ExternalLink, Copy, ChevronLeft, MapPin } from "lucide-react";
import { Button } from "@/components/ui/button";
import { HolographicCard } from "@/components/ui/holographic-card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { useToast } from "@/hooks/use-toast";
import { abOptimizerService, WinnerResult, AdBrief } from "@/services/abOptimizerService";

interface ABGenerateAdBriefProps {
  winnerResult: WinnerResult;
  platform: string;
  onBack: () => void;
  onComplete: () => void;
}

export const ABGenerateAdBrief = ({
  winnerResult,
  platform,
  onBack,
  onComplete,
}: ABGenerateAdBriefProps) => {
  const { toast } = useToast();
  const [isGenerating, setIsGenerating] = useState(false);
  const [adBrief, setAdBrief] = useState<AdBrief | null>(null);
  const [customBudget, setCustomBudget] = useState<number | undefined>();
  const [customDuration, setCustomDuration] = useState<number | undefined>();

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      const result = await abOptimizerService.generateAdBrief(
        winnerResult.result_id,
        platform,
        customBudget,
        customDuration
      );

      setAdBrief(result);
      toast({
        title: "Ad Brief Generated",
        description: "Your campaign brief is ready!",
      });
    } catch (error) {
      toast({
        title: "Failed to Generate Brief",
        description: error instanceof Error ? error.message : "Please try again",
        variant: "destructive",
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied to Clipboard",
      description: `${label} copied successfully`,
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Megaphone className="w-6 h-6 text-primary" />
            Generate Ad Campaign Brief
          </h2>
          <p className="text-muted-foreground mt-1">
            Create a paid advertising campaign from your winning variant
          </p>
        </div>
        {!adBrief && (
          <Button variant="ghost" onClick={onBack}>
            <ChevronLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        )}
      </div>

      {!adBrief ? (
        /* Configuration Form */
        <HolographicCard className="p-6">
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold mb-4">Campaign Settings (Optional)</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Leave blank to use AI-recommended values based on your winning variant's organic performance
              </p>
              
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="budget">
                    Custom Daily Budget (USD)
                  </Label>
                  <Input
                    id="budget"
                    type="number"
                    min="10"
                    placeholder="Auto (AI recommended)"
                    value={customBudget || ''}
                    onChange={(e) => setCustomBudget(e.target.value ? Number(e.target.value) : undefined)}
                  />
                </div>
                <div>
                  <Label htmlFor="duration">
                    Custom Duration (Days)
                  </Label>
                  <Input
                    id="duration"
                    type="number"
                    min="1"
                    max="30"
                    placeholder="Auto (AI recommended)"
                    value={customDuration || ''}
                    onChange={(e) => setCustomDuration(e.target.value ? Number(e.target.value) : undefined)}
                  />
                </div>
              </div>
            </div>

            <Button
              onClick={handleGenerate}
              disabled={isGenerating}
              size="lg"
              className="w-full bg-primary hover:bg-primary/90"
            >
              {isGenerating ? (
                <>Generating Campaign Brief...</>
              ) : (
                <>
                  <Megaphone className="w-4 h-4 mr-2" />
                  Generate Ad Brief
                </>
              )}
            </Button>
          </div>
        </HolographicCard>
      ) : (
        /* Ad Brief Results */
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="space-y-6"
        >
          {/* Budget & Performance Estimates */}
          <div className="grid md:grid-cols-4 gap-4">
            <HolographicCard className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <DollarSign className="w-5 h-5 text-primary" />
                <span className="text-sm font-medium">Daily Budget</span>
              </div>
              <p className="text-2xl font-bold">${adBrief.suggested_budget_daily}</p>
            </HolographicCard>

            <HolographicCard className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <Users className="w-5 h-5 text-primary" />
                <span className="text-sm font-medium">Est. Reach</span>
              </div>
              <p className="text-2xl font-bold">
                {adBrief.estimated_reach.toLocaleString()}
              </p>
            </HolographicCard>

            <HolographicCard className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-5 h-5 text-primary" />
                <span className="text-sm font-medium">Est. Clicks</span>
              </div>
              <p className="text-2xl font-bold">
                {adBrief.estimated_clicks.toLocaleString()}
              </p>
            </HolographicCard>

            <HolographicCard className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <Target className="w-5 h-5 text-primary" />
                <span className="text-sm font-medium">Est. CTR</span>
              </div>
              <p className="text-2xl font-bold">{adBrief.estimated_ctr.toFixed(2)}%</p>
            </HolographicCard>
          </div>

          {/* Campaign Overview */}
          <HolographicCard className="p-6">
            <h3 className="text-xl font-bold mb-4">Campaign Overview</h3>
            <div className="space-y-3">
              <div className="flex justify-between py-2">
                <span className="text-muted-foreground">Platform</span>
                <span className="font-semibold capitalize">{adBrief.platform}</span>
              </div>
              <Separator />
              <div className="flex justify-between py-2">
                <span className="text-muted-foreground">Duration</span>
                <span className="font-semibold">{adBrief.suggested_duration_days} days</span>
              </div>
              <Separator />
              <div className="flex justify-between py-2">
                <span className="text-muted-foreground">Total Budget</span>
                <span className="font-semibold">${adBrief.total_spend.toLocaleString()}</span>
              </div>
              <Separator />
              <div className="flex justify-between py-2">
                <span className="text-muted-foreground">Cost Per Click</span>
                <span className="font-semibold">${adBrief.estimated_cost_per_click.toFixed(2)}</span>
              </div>
            </div>
          </HolographicCard>

          {/* Targeting */}
          <HolographicCard className="p-6">
            <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
              <MapPin className="w-5 h-5" />
              Targeting
            </h3>
            <div className="space-y-3">
              <div>
                <Label className="text-sm font-medium">Geographic Target</Label>
                <div className="flex items-center justify-between mt-1">
                  <p className="text-lg">{adBrief.target_geo}</p>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => copyToClipboard(adBrief.target_geo, "Location")}
                  >
                    <Copy className="w-4 h-4" />
                  </Button>
                </div>
              </div>
              <Separator />
              <div>
                <Label className="text-sm font-medium">Audience Segment</Label>
                <div className="flex items-center justify-between mt-1">
                  <p className="text-lg">{adBrief.audience_segment}</p>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => copyToClipboard(adBrief.audience_segment, "Audience")}
                  >
                    <Copy className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>
          </HolographicCard>

          {/* Creative Guidance */}
          <HolographicCard className="p-6">
            <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
              <Lightbulb className="w-5 h-5" />
              Creative Guidance
            </h3>
            <div className="space-y-4">
              <div>
                <Label className="text-sm font-medium text-primary">Hook</Label>
                <p className="mt-1">{adBrief.creative_hook}</p>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => copyToClipboard(adBrief.creative_hook, "Hook")}
                  className="mt-2"
                >
                  <Copy className="w-4 h-4 mr-2" />
                  Copy Hook
                </Button>
              </div>
              <Separator />
              <div>
                <Label className="text-sm font-medium text-primary">Call-to-Action</Label>
                <p className="mt-1">{adBrief.cta_recommendation}</p>
              </div>
              <Separator />
              <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                <Label className="text-sm font-medium text-amber-500 flex items-center gap-2">
                  <CheckCircle className="w-4 h-4" />
                  What NOT to Change
                </Label>
                <p className="mt-1 text-sm">{adBrief.what_not_to_change}</p>
              </div>
            </div>
          </HolographicCard>

          {/* Actions */}
          <div className="flex gap-4">
            <Button
              asChild
              size="lg"
              className="flex-1 bg-primary hover:bg-primary/90"
            >
              <a
                href={adBrief.meta_ads_link}
                target="_blank"
                rel="noopener noreferrer"
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                Open Meta Ads Manager
              </a>
            </Button>
            <Button
              variant="outline"
              size="lg"
              onClick={onComplete}
            >
              <CheckCircle className="w-4 h-4 mr-2" />
              Complete
            </Button>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};
