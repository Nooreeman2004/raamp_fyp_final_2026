import { useState } from "react";
import { motion } from "framer-motion";
import { Trophy, ChevronRight, ChevronLeft, TrendingUp, Heart, MessageCircle, Share2, Bookmark, Users, MousePointer } from "lucide-react";
import { Button } from "@/components/ui/button";
import { HolographicCard } from "@/components/ui/holographic-card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { abOptimizerService, WinnerResult, EngagementMetrics } from "@/services/abOptimizerService";

interface ABCalculateWinnerProps {
  scheduleId: string;
  onBack: () => void;
  onContinue: (winner: WinnerResult) => void;
}

export const ABCalculateWinner = ({
  scheduleId,
  onBack,
  onContinue,
}: ABCalculateWinnerProps) => {
  const { toast } = useToast();
  const [isCalculating, setIsCalculating] = useState(false);
  const [winnerResult, setWinnerResult] = useState<WinnerResult | null>(null);
  
  const [variantA, setVariantA] = useState<EngagementMetrics>({
    likes: 0,
    comments: 0,
    shares: 0,
    saves: 0,
    reach: 0,
    ctr: 0,
  });

  const [variantB, setVariantB] = useState<EngagementMetrics>({
    likes: 0,
    comments: 0,
    shares: 0,
    saves: 0,
    reach: 0,
    ctr: 0,
  });

  const handleCalculate = async () => {
    // Validation
    if (variantA.reach === 0 || variantB.reach === 0) {
      toast({
        title: "Missing Data",
        description: "Please enter reach for both variants",
        variant: "destructive",
      });
      return;
    }

    setIsCalculating(true);
    try {
      const result = await abOptimizerService.calculateWinner(
        scheduleId,
        variantA,
        variantB
      );

      setWinnerResult(result);
      toast({
        title: "Winner Calculated",
        description: `${result.winner === 'variant_a' ? 'Variant A' : 'Variant B'} is the winner!`,
      });
    } catch (error) {
      toast({
        title: "Calculation Failed",
        description: error instanceof Error ? error.message : "Please try again",
        variant: "destructive",
      });
    } finally {
      setIsCalculating(false);
    }
  };

  const updateVariant = (variant: 'a' | 'b', field: keyof EngagementMetrics, value: number) => {
    if (variant === 'a') {
      setVariantA({ ...variantA, [field]: value });
    } else {
      setVariantB({ ...variantB, [field]: value });
    }
  };

  const getConfidenceBadge = (level: string) => {
    switch (level) {
      case "clear_winner":
        return <Badge className="bg-green-500/20 text-green-400 border-green-500/50">Clear Winner</Badge>;
      case "moderate":
        return <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/50">Moderate Confidence</Badge>;
      case "too_close":
        return <Badge className="bg-red-500/20 text-red-400 border-red-500/50">Too Close</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  const MetricInput = ({ 
    label, 
    icon: Icon, 
    field, 
    variant 
  }: { 
    label: string; 
    icon: typeof Heart; 
    field: keyof EngagementMetrics; 
    variant: 'a' | 'b' 
  }) => (
    <div>
      <Label htmlFor={`${variant}-${field}`} className="flex items-center gap-2 mb-2">
        <Icon className="w-4 h-4" />
        {label}
      </Label>
      <Input
        id={`${variant}-${field}`}
        type="number"
        min="0"
        step={field === 'ctr' ? '0.01' : '1'}
        value={variant === 'a' ? variantA[field] : variantB[field]}
        onChange={(e) => updateVariant(variant, field, Number(e.target.value))}
        className="w-full"
      />
    </div>
  );

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
            <Trophy className="w-6 h-6 text-primary" />
            Calculate Winner
          </h2>
          <p className="text-muted-foreground mt-1">
            Enter engagement metrics from your social media analytics
          </p>
        </div>
        {!winnerResult && (
          <Button variant="ghost" onClick={onBack}>
            <ChevronLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        )}
      </div>

      {!winnerResult ? (
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Variant A Metrics */}
          <HolographicCard className="p-6">
            <div className="mb-4">
              <h3 className="text-xl font-bold flex items-center gap-2">
                <Badge variant="outline">Variant A</Badge>
              </h3>
              <p className="text-sm text-muted-foreground mt-1">
                Enter metrics from your first post
              </p>
            </div>
            <div className="space-y-4">
              <MetricInput label="Likes" icon={Heart} field="likes" variant="a" />
              <MetricInput label="Comments" icon={MessageCircle} field="comments" variant="a" />
              <MetricInput label="Shares" icon={Share2} field="shares" variant="a" />
              <MetricInput label="Saves" icon={Bookmark} field="saves" variant="a" />
              <MetricInput label="Reach" icon={Users} field="reach" variant="a" />
              <MetricInput label="CTR (%)" icon={MousePointer} field="ctr" variant="a" />
            </div>
          </HolographicCard>

          {/* Variant B Metrics */}
          <HolographicCard className="p-6">
            <div className="mb-4">
              <h3 className="text-xl font-bold flex items-center gap-2">
                <Badge variant="outline">Variant B</Badge>
              </h3>
              <p className="text-sm text-muted-foreground mt-1">
                Enter metrics from your second post
              </p>
            </div>
            <div className="space-y-4">
              <MetricInput label="Likes" icon={Heart} field="likes" variant="b" />
              <MetricInput label="Comments" icon={MessageCircle} field="comments" variant="b" />
              <MetricInput label="Shares" icon={Share2} field="shares" variant="b" />
              <MetricInput label="Saves" icon={Bookmark} field="saves" variant="b" />
              <MetricInput label="Reach" icon={Users} field="reach" variant="b" />
              <MetricInput label="CTR (%)" icon={MousePointer} field="ctr" variant="b" />
            </div>
          </HolographicCard>

          {/* Calculate Button */}
          <div className="lg:col-span-2">
            <Button
              onClick={handleCalculate}
              loading={isCalculating}
              disabled={variantA.reach === 0 || variantB.reach === 0}
              size="lg"
              className="w-full"
            >
              {isCalculating ? "Calculating Winner..." : (
                <>
                  <Trophy className="w-4 h-4 mr-2" />
                  Calculate Winner
                </>
              )}
            </Button>
          </div>
        </div>
      ) : (
        /* Winner Results */
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="space-y-6"
        >
          <HolographicCard className="p-8 bg-gradient-to-br from-primary/10 to-purple-500/10 border-2 border-primary/50 text-center">
            <Trophy className="w-16 h-16 mx-auto mb-4 text-primary" />
            <h3 className="text-3xl font-bold mb-2">
              {winnerResult.winner === 'variant_a' ? 'Variant A' : 'Variant B'} Wins!
            </h3>
            <div className="flex items-center justify-center gap-4 mb-4">
              {getConfidenceBadge(winnerResult.confidence_level)}
              <Badge className="bg-primary/20 text-primary border-primary/50">
                +{winnerResult.delta_percentage.toFixed(1)}% Better
              </Badge>
            </div>
          </HolographicCard>

          {/* Scores Comparison */}
          <div className="grid md:grid-cols-2 gap-4">
            <HolographicCard className={`p-6 ${winnerResult.winner === 'variant_a' ? 'border-2 border-primary' : ''}`}>
              <div className="flex items-center justify-between mb-2">
                <Badge variant="outline">Variant A</Badge>
                {winnerResult.winner === 'variant_a' && (
                  <Trophy className="w-5 h-5 text-primary" />
                )}
              </div>
              <p className="text-4xl font-bold">
                {winnerResult.variant_a_composite.toFixed(1)}
              </p>
              <p className="text-sm text-muted-foreground">Composite Score</p>
            </HolographicCard>

            <HolographicCard className={`p-6 ${winnerResult.winner === 'variant_b' ? 'border-2 border-primary' : ''}`}>
              <div className="flex items-center justify-between mb-2">
                <Badge variant="outline">Variant B</Badge>
                {winnerResult.winner === 'variant_b' && (
                  <Trophy className="w-5 h-5 text-primary" />
                )}
              </div>
              <p className="text-4xl font-bold">
                {winnerResult.variant_b_composite.toFixed(1)}
              </p>
              <p className="text-sm text-muted-foreground">Composite Score</p>
            </HolographicCard>
          </div>

          {/* Recommendation */}
          <HolographicCard className="p-6 bg-blue-500/10 border-blue-500/30">
            <h4 className="font-semibold text-blue-500 mb-2 flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              Recommendation
            </h4>
            <p>{winnerResult.recommendation}</p>
          </HolographicCard>

          <Button
            onClick={() => onContinue(winnerResult)}
            size="lg"
            className="w-full"
          >
            Generate Ad Campaign Brief
            <ChevronRight className="w-4 h-4 ml-2" />
          </Button>
        </motion.div>
      )}
    </motion.div>
  );
};
