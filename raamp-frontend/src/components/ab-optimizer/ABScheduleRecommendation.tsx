import { useState } from "react";
import { motion } from "framer-motion";
import { Calendar, Clock, TrendingUp, ChevronRight, ChevronLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { HolographicCard } from "@/components/ui/holographic-card";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { abOptimizerService, ScheduleRecommendation } from "@/services/abOptimizerService";

interface ABScheduleRecommendationProps {
  batchId: string;
  onBack: () => void;
  onContinue: (recommendation: ScheduleRecommendation, platform: string) => void;
}

export const ABScheduleRecommendation = ({
  batchId,
  onBack,
  onContinue,
}: ABScheduleRecommendationProps) => {
  const { toast } = useToast();
  const [platform, setPlatform] = useState<string>("instagram");
  const [niche] = useState<string>("restaurant");
  const [isLoading, setIsLoading] = useState(false);
  const [recommendation, setRecommendation] = useState<ScheduleRecommendation | null>(null);

  /** Maps raw server/network errors to safe user-facing messages. */
  const getUserFriendlyError = (error: unknown): string => {
    if (error instanceof Error) {
      const msg = error.message.toLowerCase();
      if (msg.includes("internal server") || msg.includes("500") || msg.includes("unexpected")) {
        return "Something went wrong on our end. Please try again shortly.";
      }
      if (msg.includes("network") || msg.includes("failed to fetch")) {
        return "Unable to reach the server. Check your connection and try again.";
      }
      if (msg.includes("not found") || msg.includes("404")) {
        return "This analysis session could not be found. Please start a new scan.";
      }
    }
    return "Something went wrong. Please try again.";
  };

  const handleGetRecommendation = async () => {
    setIsLoading(true);
    try {
      const result = await abOptimizerService.getScheduleRecommendation(
        batchId,
        platform,
        niche
      );
      setRecommendation(result);
      toast({
        title: "Schedule Recommendation Ready",
        description: `Optimal times found for ${platform}`,
      });
    } catch (error) {
      toast({
        title: "Couldn't Load Recommendation",
        description: getUserFriendlyError(error),
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleContinue = () => {
    if (recommendation) {
      onContinue(recommendation, platform);
    }
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
            <Calendar className="w-6 h-6 text-primary" />
            Schedule Recommendation
          </h2>
          <p className="text-muted-foreground mt-1">
            Get optimal posting times based on platform data
          </p>
        </div>
        <Button variant="ghost" onClick={onBack}>
          <ChevronLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
      </div>

      {/* Platform Selection */}
      <HolographicCard className="p-6">
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-2 block">
              Select Platform
            </label>
            <Select value={platform} onValueChange={setPlatform}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Choose platform" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="instagram">Instagram</SelectItem>
                <SelectItem value="facebook">Facebook</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Button
            onClick={handleGetRecommendation}
            loading={isLoading}
            disabled={isLoading}
            className="w-full"
            size="lg"
          >
            {isLoading ? "Analyzing Platform Data..." : (
              <>
                <TrendingUp className="w-4 h-4 mr-2" />
                Get Optimal Times
              </>
            )}
          </Button>
        </div>
      </HolographicCard>

      {/* Recommendation Results */}
      {recommendation && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="space-y-4"
        >
          <HolographicCard className="p-6 bg-gradient-to-br from-primary/10 to-purple-500/10 border-2 border-primary/50">
            <div className="space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-xl font-bold mb-1">
                    Optimal Posting Schedule
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    Based on {recommendation.source}
                  </p>
                </div>
                <Badge className="bg-primary/20 text-primary border-primary/50">
                  {recommendation.confidence} Confidence
                </Badge>
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                <div className="p-4 bg-card rounded-lg border border-border">
                  <div className="flex items-center gap-2 mb-2">
                    <Calendar className="w-5 h-5 text-primary" />
                    <span className="font-semibold">Best Days</span>
                  </div>
                  <p className="text-lg">{recommendation.days}</p>
                </div>

                <div className="p-4 bg-card rounded-lg border border-border">
                  <div className="flex items-center gap-2 mb-2">
                    <Clock className="w-5 h-5 text-primary" />
                    <span className="font-semibold">Best Times</span>
                  </div>
                  <p className="text-lg">{recommendation.time_range}</p>
                </div>
              </div>

              {recommendation.next_optimal && (
                <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                  <p className="font-semibold text-blue-400 mb-1">
                    Next Optimal Window
                  </p>
                  <p className="text-sm text-foreground">
                    {recommendation.next_optimal.day} at{" "}
                    {recommendation.next_optimal.time}
                  </p>
                </div>
              )}

              <Button
                onClick={handleContinue}
                size="lg"
                className="w-full"
              >
                Continue to Schedule
                <ChevronRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </HolographicCard>
        </motion.div>
      )}
    </motion.div>
  );
};
