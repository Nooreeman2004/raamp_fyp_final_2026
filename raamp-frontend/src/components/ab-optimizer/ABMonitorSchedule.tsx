import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Clock, Calendar, CheckCircle, ChevronRight, RefreshCw, TrendingUp, Megaphone, ExternalLink, BarChart3, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { HolographicCard } from "@/components/ui/holographic-card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/hooks/use-toast";
import { abOptimizerService, ScheduleConfirmation, ScheduleStatus } from "@/services/abOptimizerService";

interface ABMonitorScheduleProps {
  confirmation: ScheduleConfirmation;
  onContinue: (scheduleId: string) => void;
}

export const ABMonitorSchedule = ({
  confirmation,
  onContinue,
}: ABMonitorScheduleProps) => {
  const { toast } = useToast();
  const [status, setStatus] = useState<ScheduleStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const loadStatus = async () => {
    setIsLoading(true);
    try {
      const result = await abOptimizerService.getScheduleStatus(confirmation.schedule_id);
      setStatus(result);
    } catch (error) {
      toast({
        title: "Failed to Load Status",
        description: error instanceof Error ? error.message : "Please try again",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadStatus();
  }, [confirmation.schedule_id]);

  useEffect(() => {
    if (autoRefresh && status?.status === "active") {
      const interval = setInterval(loadStatus, 30000); // Refresh every 30 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh, status?.status]);

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case "scheduled":
        return <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/50">Scheduled</Badge>;
      case "active":
        return <Badge className="bg-green-500/20 text-green-400 border-green-500/50">Active</Badge>;
      case "completed":
        return <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/50">Completed</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  const getTimeRemaining = () => {
    if (!status) return null;

    const startTime = new Date(status.monitoring_start_time || status.post_time);
    const endTime = new Date(status.monitoring_end_time || (new Date(status.post_time).getTime() + status.test_duration_hours * 60 * 60 * 1000));
    const now = new Date();

    if (now < startTime) {
      const hoursUntilPost = Math.floor((startTime.getTime() - now.getTime()) / (60 * 60 * 1000));
      return `Posting in ${hoursUntilPost} hours`;
    } else if (now < endTime) {
      const hoursRemaining = Math.floor((endTime.getTime() - now.getTime()) / (60 * 60 * 1000));
      return `${hoursRemaining} hours remaining`;
    } else {
      return "Test complete";
    }
  };

  const getProgressPercentage = () => {
    if (!status) return 0;

    const startTime = new Date(status.monitoring_start_time || status.post_time);
    const endTime = new Date(status.monitoring_end_time || (new Date(status.post_time).getTime() + status.test_duration_hours * 60 * 60 * 1000));
    const now = new Date();

    if (now < startTime) return 0;
    if (now >= endTime) return 100;

    const elapsed = now.getTime() - startTime.getTime();
    const total = endTime.getTime() - startTime.getTime();
    return Math.floor((elapsed / total) * 100);
  };

  const openAdsLink = (url?: string) => {
    if (!url) return;
    window.open(url, "_blank", "noopener,noreferrer");
  };

  const getActiveVariant = (): 'a' | 'b' | 'none' => {
    if (!status) return 'none';
    
    const now = new Date();
    const postTimeA = new Date(status.variant_a_post_time);
    const postTimeB = new Date(status.variant_b_post_time);
    const endTimeA = new Date(postTimeA.getTime() + status.test_duration_hours * 60 * 60 * 1000);
    const endTimeB = new Date(postTimeB.getTime() + status.test_duration_hours * 60 * 60 * 1000);

    // Check if Variant A is currently active
    if (now >= postTimeA && now < endTimeA) {
      return 'a';
    }
    
    // Check if Variant B is currently active
    if (now >= postTimeB && now < endTimeB) {
      return 'b';
    }
    
    return 'none';
  };

  const canProceed = status?.status === "completed";

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
            <TrendingUp className="w-6 h-6 text-primary" />
            Monitor A/B Test
          </h2>
          <p className="text-muted-foreground mt-1">
            Track your test progress and wait for completion
          </p>
        </div>
        <Button
          size="sm"
          onClick={loadStatus}
          loading={isLoading}
          disabled={isLoading}
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Loading state */}
      {isLoading && !status && (
        <HolographicCard className="p-10">
          <div className="space-y-6">
            {/* Skeleton header */}
            <div className="flex items-center justify-between">
              <div className="space-y-2">
                <div className="h-6 w-32 bg-muted/40 rounded animate-pulse" />
                <div className="h-4 w-52 bg-muted/30 rounded animate-pulse" />
              </div>
              <div className="h-6 w-20 bg-muted/40 rounded-full animate-pulse" />
            </div>

            {/* Skeleton platform row */}
            <div className="p-4 bg-muted/10 rounded-lg border border-border space-y-2">
              <div className="h-4 w-16 bg-muted/40 rounded animate-pulse" />
              <div className="h-5 w-28 bg-muted/30 rounded animate-pulse" />
            </div>

            {/* Skeleton variant cards */}
            {[0, 1].map((i) => (
              <div key={i} className="p-4 rounded-lg border border-border space-y-2">
                <div className="flex items-center justify-between">
                  <div className="h-5 w-20 bg-muted/40 rounded-full animate-pulse" />
                  <div className="h-5 w-5 bg-muted/30 rounded animate-pulse" />
                </div>
                <div className="h-5 w-44 bg-muted/30 rounded animate-pulse" />
              </div>
            ))}

            {/* Skeleton progress */}
            <div className="space-y-2">
              <div className="flex justify-between">
                <div className="h-4 w-24 bg-muted/40 rounded animate-pulse" />
                <div className="h-4 w-32 bg-muted/30 rounded animate-pulse" />
              </div>
              <div className="h-3 w-full bg-muted/20 rounded-full animate-pulse" />
            </div>
          </div>
        </HolographicCard>
      )}

      {/* Error / no status fallback */}
      {!isLoading && !status && (
        <HolographicCard className="p-12 flex flex-col items-center gap-4 text-center">
          <Clock className="w-10 h-10 text-muted-foreground" />
          <div>
            <p className="font-semibold">Could not load schedule status</p>
            <p className="text-sm text-muted-foreground mt-1">
              Schedule ID: {confirmation.schedule_id}
            </p>
          </div>
          <Button variant="outline" size="sm" onClick={loadStatus}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Retry
          </Button>
        </HolographicCard>
      )}

      {/* Status Card */}
      {status && (
        <HolographicCard className="p-6">
          <div className="space-y-6">
            {/* Status Header */}
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xl font-bold mb-1">Test Status</h3>
                <p className="text-sm text-muted-foreground">
                  Schedule ID: {confirmation.schedule_id}
                </p>
              </div>
              {getStatusBadge(status.status)}
            </div>

            {/* Platform & Timing */}
            <div className="grid gap-4">
              <div className="p-4 bg-card rounded-lg border border-border">
                <div className="flex items-center gap-2 mb-2">
                  <Calendar className="w-5 h-5 text-primary" />
                  <span className="font-semibold">Platform</span>
                </div>
                <p className="text-lg capitalize">{status.platform}</p>
              </div>

              {/* Variant A */}
              <HolographicCard className={`p-4 transition-all ${getActiveVariant() === 'a' ? 'border-2 border-primary bg-primary/10' : 'border border-primary/30 bg-primary/5'}`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Badge className="bg-primary/20 text-primary border-primary/50 font-semibold">Variant A</Badge>
                    {getActiveVariant() === 'a' && (
                      <Badge className="bg-green-500/20 text-green-400 border-green-500/50">
                        Active Now
                      </Badge>
                    )}
                  </div>
                  <Clock className="w-5 h-5 text-primary" />
                </div>
                <p className="text-lg font-medium text-foreground">
                  {new Date(status.variant_a_post_time).toLocaleString()}
                </p>
              </HolographicCard>

              {/* Variant B */}
              <HolographicCard className={`p-4 transition-all ${getActiveVariant() === 'b' ? 'border-2 border-orange-400 bg-orange-500/10' : 'border border-orange-500/30 bg-orange-500/5'}`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Badge className="bg-orange-500/20 text-orange-400 border-orange-500/50 font-semibold">Variant B</Badge>
                    {getActiveVariant() === 'b' && (
                      <Badge className="bg-green-500/20 text-green-400 border-green-500/50">
                        Active Now
                      </Badge>
                    )}
                  </div>
                  <Clock className="w-5 h-5 text-orange-400" />
                </div>
                <p className="text-lg font-medium text-foreground">
                  {new Date(status.variant_b_post_time).toLocaleString()}
                </p>
              </HolographicCard>
            </div>

            {/* Progress Bar */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium">Test Progress</span>
                <span className="text-sm text-muted-foreground">
                  {getTimeRemaining()}
                </span>
              </div>
              <Progress value={getProgressPercentage()} className="h-3" />
              <p className="text-xs text-muted-foreground mt-1">
                Duration: {status.test_duration_hours} hours
              </p>
            </div>

            {/* Pre-ranking + Promote now */}
            {status.pre_ranking && (
              <div className="p-4 rounded-lg border border-amber-400/30 bg-amber-500/10 space-y-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h4 className="font-semibold text-amber-400 flex items-center gap-2">
                      <Sparkles className="w-4 h-4" />
                      AI Pre-Ranking (Before Final Metrics)
                    </h4>
                    <p className="text-sm text-muted-foreground mt-1">
                      Recommended variant: <span className="font-semibold uppercase text-foreground">{status.pre_ranking.recommended_variant.replace("_", " ")}</span> • Confidence: {status.pre_ranking.confidence}
                    </p>
                  </div>
                  <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/40">
                    Gap: {status.pre_ranking.score_gap.toFixed(2)}
                  </Badge>
                </div>

                <div className="grid md:grid-cols-2 gap-3 text-sm">
                  <div className="rounded-md border border-primary/30 bg-primary/10 p-3">
                    <p className="text-primary font-medium">Variant A composite</p>
                    <p className="text-foreground text-lg font-semibold">{status.pre_ranking.variant_a_composite.toFixed(2)}</p>
                  </div>
                  <div className="rounded-md border border-orange-500/30 bg-orange-500/10 p-3">
                    <p className="text-orange-400 font-medium">Variant B composite</p>
                    <p className="text-foreground text-lg font-semibold">{status.pre_ranking.variant_b_composite.toFixed(2)}</p>
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-3">
                  <Button
                    onClick={() => openAdsLink(status.variant_a_ads_link || status.meta_ads_link)}
                    className="bg-primary hover:bg-primary/90 text-black"
                  >
                    <Megaphone className="w-4 h-4 mr-2" />
                    Put Ad on Variant A
                    <ExternalLink className="w-4 h-4 ml-2" />
                  </Button>
                  <Button
                    onClick={() => openAdsLink(status.variant_b_ads_link || status.meta_ads_link)}
                    className="bg-orange-600 hover:bg-orange-500 text-white"
                  >
                    <Megaphone className="w-4 h-4 mr-2" />
                    Put Ad on Variant B
                    <ExternalLink className="w-4 h-4 ml-2" />
                  </Button>
                </div>
              </div>
            )}

            {/* Stats needed for post-monitoring decision */}
            {status.stats_template && (
              <div className="p-4 rounded-lg border border-emerald-500/30 bg-emerald-500/10 space-y-3">
                <h4 className="font-semibold text-emerald-400 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4" />
                  Stats You Need To Decide Ads
                </h4>
                <div className="flex flex-wrap gap-2">
                  {status.stats_template.fields.map((field) => (
                    <Badge key={field} variant="outline" className="border-emerald-400/40 text-emerald-400">
                      {field.toUpperCase()}
                    </Badge>
                  ))}
                </div>
                <p className="text-sm text-muted-foreground">{status.stats_template.notes}</p>
                {status.meta_ads_link && (
                  <Button variant="outline" size="sm" onClick={() => openAdsLink(status.meta_ads_link)} className="border-emerald-500/40">
                    Open Meta Ads Manager
                    <ExternalLink className="w-4 h-4 ml-2" />
                  </Button>
                )}
              </div>
            )}

            {status.result && (
              <div className="p-4 rounded-lg border border-indigo-500/30 bg-indigo-500/10 space-y-2">
                <h4 className="font-semibold text-indigo-400">Monitoring Summary</h4>
                <p className="text-sm text-foreground">
                  Winner image: {status.result.winner_image_id}
                  {typeof status.result.delta_percentage === "number" ? ` • Delta: ${status.result.delta_percentage.toFixed(1)}%` : ""}
                  {status.result.confidence_level ? ` • Confidence: ${status.result.confidence_level}` : ""}
                </p>
              </div>
            )}

            {/* Instructions */}
            <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
              <h4 className="font-semibold text-blue-400 mb-2">Next Steps</h4>
              {status.status === "scheduled" && (
                <p className="text-sm">
                  Your test is scheduled. The posts will go live automatically at the specified time.
                  Come back after the test duration to enter engagement metrics.
                </p>
              )}
              {status.status === "active" && (
                <p className="text-sm">
                  Your A/B test is currently running. Wait for the test duration to complete,
                  then return to enter the final engagement metrics from your analytics.
                </p>
              )}
              {status.status === "completed" && (
                <p className="text-sm">
                  Test complete! Collect your engagement metrics from your social media analytics
                  and proceed to calculate the winner.
                </p>
              )}
            </div>

            {/* Continue Button */}
            {canProceed && (
              <Button
                onClick={() => onContinue(confirmation.schedule_id)}
                size="lg"
                className="w-full"
              >
                <CheckCircle className="w-4 h-4 mr-2" />
                Enter Results &amp; Calculate Winner
                <ChevronRight className="w-4 h-4 ml-2" />
              </Button>
            )}

            {/* Auto-refresh Toggle */}
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="rounded"
              />
              <span>Auto-refresh every 30 seconds</span>
            </div>
          </div>
        </HolographicCard>
      )}
    </motion.div>
  );
};
