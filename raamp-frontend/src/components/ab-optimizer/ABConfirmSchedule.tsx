import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Calendar, Clock, CheckCircle, ChevronLeft, Image as ImageIcon, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { HolographicCard } from "@/components/ui/holographic-card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { abOptimizerService, ScheduleRecommendation, ScheduleConfirmation, ImageAnalysis } from "@/services/abOptimizerService";

interface ABConfirmScheduleProps {
  batchId: string;
  recommendation: ScheduleRecommendation;
  platform: string;
  recommendedPair?: string[];
  images: ImageAnalysis[];
  onBack: () => void;
  onContinue: (confirmation: ScheduleConfirmation) => void;
}

export const ABConfirmSchedule = ({
  batchId,
  recommendation,
  platform,
  recommendedPair,
  images,
  onBack,
  onContinue,
}: ABConfirmScheduleProps) => {
  const { toast } = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [postTimeA, setPostTimeA] = useState("");
  const [postTimeB, setPostTimeB] = useState("");
  const [captionA, setCaptionA] = useState("");
  const [captionB, setCaptionB] = useState("");
  const [testDuration, setTestDuration] = useState(48);

  const variantAImage = images.find(img => img.image_id === recommendedPair?.[0]);
  const variantBImage = images.find(img => img.image_id === recommendedPair?.[1]);

  // Auto-populate suggested times based on recommendation
  useEffect(() => {
    if (recommendation && !postTimeA && !postTimeB) {
      // Parse the recommendation to suggest times
      // Variant A: Next optimal day at start of time range
      const now = new Date();
      const nextDay = new Date(now.getTime() + 24 * 60 * 60 * 1000); // Tomorrow
      
      // Extract first time from range (e.g., "11 AM - 1 PM" -> "11 AM")
      const timeMatch = recommendation.time_range.match(/(\d+)\s*(AM|PM)/i);
      if (timeMatch) {
        let hour = parseInt(timeMatch[1]);
        const isPM = timeMatch[2].toUpperCase() === 'PM';
        
        // Convert to 24-hour format
        if (isPM && hour !== 12) hour += 12;
        if (!isPM && hour === 12) hour = 0;
        
        // Variant A: Tomorrow at optimal time
        const suggestedA = new Date(nextDay);
        suggestedA.setHours(hour, 0, 0, 0);
        
        // Variant B: 2 days later at same optimal time
        const suggestedB = new Date(nextDay);
        suggestedB.setDate(suggestedB.getDate() + 2);
        suggestedB.setHours(hour, 0, 0, 0);
        
        setPostTimeA(suggestedA.toISOString().slice(0, 16));
        setPostTimeB(suggestedB.toISOString().slice(0, 16));
      }
    }
  }, [recommendation, postTimeA, postTimeB]);

  const handleConfirm = async () => {
    if (!postTimeA || !postTimeB) {
      toast({
        title: "Missing Information",
        description: "Please select posting times for both variants",
        variant: "destructive",
      });
      return;
    }

    if (!variantAImage || !variantBImage) {
      toast({
        title: "Missing Variants",
        description: "A/B test variants not found",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);
    try {
      const result = await abOptimizerService.confirmSchedule(
        batchId,
        variantAImage.image_id,
        variantBImage.image_id,
        platform,
        new Date(postTimeA),
        new Date(postTimeB),
        captionA || undefined,
        captionB || undefined,
        testDuration
      );

      toast({
        title: "Schedule Confirmed",
        description: result.message,
      });

      onContinue(result);
    } catch (error) {
      toast({
        title: "Failed to Confirm Schedule",
        description: error instanceof Error ? error.message : "Please try again",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Generate minimum datetime (now + 1 hour)
  const minDateTime = new Date(Date.now() + 60 * 60 * 1000).toISOString().slice(0, 16);

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
            <CheckCircle className="w-6 h-6 text-primary" />
            Confirm Schedule
          </h2>
          <p className="text-muted-foreground mt-1">
            Set your A/B test timing and details
          </p>
        </div>
        <Button variant="ghost" onClick={onBack}>
          <ChevronLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
      </div>

      {/* Recommendation Summary */}
      <HolographicCard className="p-4 bg-primary/5 border-primary/30">
        <div className="flex items-center gap-4 flex-wrap">
          <Badge className="bg-primary/20 text-primary border-primary/50">
            Optimal Times
          </Badge>
          <div className="flex items-center gap-2 text-sm">
            <Calendar className="w-4 h-4" />
            <span>{recommendation.days}</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Clock className="w-4 h-4" />
            <span>{recommendation.time_range}</span>
          </div>
        </div>
      </HolographicCard>

      {/* A/B Test Variants */}
      <div>
        <h3 className="text-lg font-semibold mb-3">A/B Test Variants</h3>
        <div className="grid md:grid-cols-2 gap-4">
          {[
            { label: "Variant A", image: variantAImage },
            { label: "Variant B", image: variantBImage },
          ].map((variant) => (
            <HolographicCard key={variant.label} className="p-4">
              <div className="flex items-center gap-3 mb-3">
                <Badge variant="outline">{variant.label}</Badge>
                <span className="font-semibold text-lg">
                  {variant.image?.scores.composite_score.toFixed(1)}/10
                </span>
              </div>
              {variant.image?.image_url && (
                <div className="w-full h-48 flex items-center justify-center bg-muted/20 rounded-lg border border-border mb-2 overflow-hidden">
                  <img
                    src={variant.image.image_url}
                    alt={variant.image.filename}
                    className="max-w-full max-h-full object-contain"
                  />
                </div>
              )}
              <p className="text-sm text-muted-foreground truncate">
                {variant.image?.filename}
              </p>
            </HolographicCard>
          ))}
        </div>
      </div>

      {/* Schedule Form */}
      <HolographicCard className="p-6">
        <div className="space-y-4">
          {/* Two-column layout: each column has date+caption stacked together */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* Variant A Column */}
            <div className="space-y-4">
              <div>
                <Label htmlFor="postTimeA" className="flex items-center gap-2 mb-2">
                  <Clock className="w-4 h-4" />
                  Variant A - Date &amp; Time
                  <span className="text-red-500 font-bold ml-0.5">*</span>
                </Label>
                <Input
                  id="postTimeA"
                  type="datetime-local"
                  value={postTimeA}
                  onChange={(e) => setPostTimeA(e.target.value)}
                  min={minDateTime}
                  className="w-full"
                />
                <p className="text-xs text-muted-foreground mt-1">Post on first day</p>
              </div>

              <div>
                <Label htmlFor="captionA" className="flex items-center gap-2 mb-2">
                  <MessageSquare className="w-4 h-4" />
                  Variant A - Caption (Optional)
                </Label>
                <Textarea
                  id="captionA"
                  value={captionA}
                  onChange={(e) => setCaptionA(e.target.value)}
                  placeholder="Caption for Variant A..."
                  rows={3}
                  className="w-full"
                />
              </div>
            </div>

            {/* Variant B Column */}
            <div className="space-y-4">
              <div>
                <Label htmlFor="postTimeB" className="flex items-center gap-2 mb-2">
                  <Clock className="w-4 h-4" />
                  Variant B - Date &amp; Time
                  <span className="text-red-500 font-bold ml-0.5">*</span>
                </Label>
                <Input
                  id="postTimeB"
                  type="datetime-local"
                  value={postTimeB}
                  onChange={(e) => setPostTimeB(e.target.value)}
                  min={minDateTime}
                  className="w-full"
                />
                <p className="text-xs text-muted-foreground mt-1">Post on different day</p>
              </div>

              <div>
                <Label htmlFor="captionB" className="flex items-center gap-2 mb-2">
                  <MessageSquare className="w-4 h-4" />
                  Variant B - Caption (Optional)
                </Label>
                <Textarea
                  id="captionB"
                  value={captionB}
                  onChange={(e) => setCaptionB(e.target.value)}
                  placeholder="Caption for Variant B..."
                  rows={3}
                  className="w-full"
                />
              </div>
            </div>
          </div>

          <div>
            <Label htmlFor="duration" className="mb-2 block">
              Test Duration (Hours)
              <span className="text-red-500 font-bold ml-0.5">*</span>
            </Label>
            <Input
              id="duration"
              type="number"
              value={testDuration}
              onChange={(e) => setTestDuration(Number(e.target.value))}
              min={24}
              max={168}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Recommended: 48-72 hours for reliable results
            </p>
          </div>

          <Button
            onClick={handleConfirm}
            disabled={!postTimeA || !postTimeB || testDuration < 24}
            loading={isSubmitting}
            size="lg"
            className="w-full"
          >
            {isSubmitting ? "Confirming Schedule..." : (
              <>
                <CheckCircle className="w-4 h-4 mr-2" />
                Confirm &amp; Schedule Test
              </>
            )}
          </Button>
        </div>
      </HolographicCard>
    </motion.div>
  );
};
