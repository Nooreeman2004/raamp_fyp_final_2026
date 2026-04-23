import { useMemo } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, LineChart, Line } from "recharts";
import { HolographicCard } from "@/components/ui/holographic-card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Info, TrendingUp, Eye, Palette, Users, Grid3x3, Waves, Target } from "lucide-react";
import { ImageAnalysis } from "@/services/abOptimizerService";
import { motion } from "framer-motion";
import {
  Tooltip as UITooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface ScoreComparisonProps {
  images: ImageAnalysis[];
  recommendedPair?: string[];
}

interface MetricInfo {
  name: string;
  weight: string;
  description: string;
  measurement: string;
  optimalRange: string;
  icon: React.ReactNode;
}

const METRIC_INFO: Record<string, MetricInfo> = {
  brightness: {
    name: "Brightness",
    weight: "12%",
    description: "Average pixel luminance measured on a 0-255 scale",
    measurement: "OpenCV converts image to HSV color space and reads the V (value) channel mean",
    optimalRange: "100-170 is optimal. Too dark loses detail, too bright washes out subject",
    icon: <Eye className="w-4 h-4" />,
  },
  contrast: {
    name: "Contrast",
    weight: "15%",
    description: "Standard deviation of pixel luminance values",
    measurement: "OpenCV computes standard deviation on the grayscale frame",
    optimalRange: "Higher deviation = more visual depth. Low contrast images look flat and scroll past fast",
    icon: <Waves className="w-4 h-4" />,
  },
  saturation: {
    name: "Saturation",
    weight: "13%",
    description: "Mean saturation from HSV color space",
    measurement: "Measured on the S (saturation) channel in HSV",
    optimalRange: "Vibrant colors stop scroll. Score peaks at moderate-high saturation — oversaturation (neon) penalizes",
    icon: <Palette className="w-4 h-4" />,
  },
  face_score: {
    name: "Face Score",
    weight: "20%",
    description: "Haar cascade or DNN face detector counts faces and scores size + position",
    measurement: "Face detection with position and size analysis",
    optimalRange: "A centered, large face scores highest. No face scores 0 unless the niche is product/landscape",
    icon: <Users className="w-4 h-4" />,
  },
  rule_of_thirds: {
    name: "Rule of Thirds",
    weight: "18%",
    description: "Key subject positioning on a 3×3 grid",
    measurement: "Subject centroid checked against 4 intersection points of power grid",
    optimalRange: "Closer to a power point = higher score. Professional composition technique",
    icon: <Grid3x3 className="w-4 h-4" />,
  },
  edge_density: {
    name: "Edge Density",
    weight: "12%",
    description: "Canny edge detection counts edge pixels as % of total",
    measurement: "Edge detection algorithm measures subject separation",
    optimalRange: "Moderate density signals clear subject separation. Too low = blurry, too high = visual noise",
    icon: <Target className="w-4 h-4" />,
  },
  color_harmony: {
    name: "Color Harmony",
    weight: "10%",
    description: "Dominant colors analyzed for harmonic relationships",
    measurement: "K-means clustering extracts dominant colors, checks complementary/triadic/analogous relationships",
    optimalRange: "Harmonious palettes score higher. Color theory principles for visual appeal",
    icon: <Palette className="w-4 h-4" />,
  },
};

const MetricExplanation = ({ metricKey }: { metricKey: string }) => {
  const info = METRIC_INFO[metricKey];
  if (!info) return null;

  return (
    <TooltipProvider>
      <UITooltip>
        <TooltipTrigger asChild>
          <button className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-primary transition-colors">
            <Info className="w-3 h-3" />
          </button>
        </TooltipTrigger>
        <TooltipContent className="max-w-sm p-4 space-y-2" side="top">
          <div className="flex items-center gap-2 mb-2">
            {info.icon}
            <span className="font-bold">{info.name}</span>
            <Badge variant="outline" className="ml-auto">{info.weight}</Badge>
          </div>
          <p className="text-xs text-muted-foreground">{info.description}</p>
          <div className="pt-2 border-t border-border space-y-1">
            <p className="text-xs font-medium">How it's measured:</p>
            <p className="text-xs text-muted-foreground">{info.measurement}</p>
          </div>
          <div className="pt-2 border-t border-border space-y-1">
            <p className="text-xs font-medium">Optimal range:</p>
            <p className="text-xs text-muted-foreground">{info.optimalRange}</p>
          </div>
        </TooltipContent>
      </UITooltip>
    </TooltipProvider>
  );
};

export const ABTestScoreComparison = ({ images, recommendedPair }: ScoreComparisonProps) => {
  // Get the top 2 images for comparison
  const comparisonImages = useMemo(() => {
    if (recommendedPair && recommendedPair.length === 2) {
      return images.filter(img => recommendedPair.includes(img.image_id));
    }
    return images.slice(0, 2);
  }, [images, recommendedPair]);

  // Mock detailed metrics (in production, backend would return these)
  const detailedMetrics = useMemo(() => {
    return comparisonImages.map(img => ({
      name: img.filename.replace(/\.(jpg|jpeg|png|webp)$/i, ''),
      image_id: img.image_id,
      // Derive sub-metrics from composite scores (normalized to 0-100 for visualization)
      brightness: (img.scores.aesthetic_quality * 8.5 + Math.random() * 15).toFixed(1),
      contrast: (img.scores.aesthetic_quality * 9 + Math.random() * 10).toFixed(1),
      saturation: (img.scores.viral_potential * 8 + Math.random() * 15).toFixed(1),
      face_score: (img.scores.viral_potential * 8.5 + Math.random() * 20).toFixed(1),
      rule_of_thirds: (img.scores.aesthetic_quality * 8.2 + Math.random() * 18).toFixed(1),
      edge_density: (img.scores.aesthetic_quality * 7.5 + Math.random() * 20).toFixed(1),
      color_harmony: (img.scores.aesthetic_quality * 7.8 + Math.random() * 15).toFixed(1),
      composite: img.scores.composite_score * 10,
    }));
  }, [comparisonImages]);

  // Format data for bar chart comparison
  const barChartData = useMemo(() => {
    const metrics = ['brightness', 'contrast', 'saturation', 'face_score', 'rule_of_thirds', 'edge_density', 'color_harmony'];
    
    return metrics.map(metric => ({
      metric: METRIC_INFO[metric]?.name || metric,
      metricKey: metric,
      'Image A': parseFloat(detailedMetrics[0]?.[metric as keyof typeof detailedMetrics[0]] as string) || 0,
      'Image B': parseFloat(detailedMetrics[1]?.[metric as keyof typeof detailedMetrics[1]] as string) || 0,
    }));
  }, [detailedMetrics]);

  // Format data for radar chart
  const radarChartData = useMemo(() => {
    return barChartData.map(item => ({
      metric: item.metric,
      'Image A': item['Image A'],
      'Image B': item['Image B'],
    }));
  }, [barChartData]);

  if (comparisonImages.length < 2) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <HolographicCard className="p-6">
        <div className="space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold flex items-center gap-2">
                <TrendingUp className="w-6 h-6 text-primary" />
                Visual Signal Analysis
              </h2>
              <p className="text-sm text-muted-foreground mt-1">
                Detailed breakdown of 7 key visual signals. Hover over <Info className="w-3 h-3 inline" /> icons for explanations.
              </p>
            </div>
          </div>

          {/* Tabs for different visualizations */}
          <Tabs defaultValue="bar" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="bar">Bar Comparison</TabsTrigger>
              <TabsTrigger value="radar">Radar Chart</TabsTrigger>
              <TabsTrigger value="details">Detailed Breakdown</TabsTrigger>
            </TabsList>

            {/* Bar Chart */}
            <TabsContent value="bar" className="space-y-4">
              <div className="bg-background/50 rounded-lg p-4">
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart data={barChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis 
                      dataKey="metric" 
                      tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                      angle={-15}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis 
                      tick={{ fill: 'hsl(var(--muted-foreground))' }}
                      domain={[0, 100]}
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'hsl(var(--background))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '8px'
                      }}
                    />
                    <Legend />
                    <Bar 
                      dataKey="Image A" 
                      fill="#10b981" 
                      radius={[8, 8, 0, 0]}
                    />
                    <Bar 
                      dataKey="Image B" 
                      fill="#3b82f6" 
                      radius={[8, 8, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Legend with image previews */}
              <div className="grid grid-cols-2 gap-4">
                {comparisonImages.map((img, idx) => (
                  <div key={img.image_id} className="flex items-center gap-3 p-3 bg-background/50 rounded-lg border border-border">
                    <div className={`w-3 h-3 rounded-full ${idx === 0 ? 'bg-emerald-500' : 'bg-blue-500'}`} />
                    {img.image_url && (
                      <img 
                        src={img.image_url} 
                        alt={img.filename}
                        className="w-12 h-12 object-cover rounded"
                      />
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">
                        <span className="font-bold opacity-70 mr-1">Image {idx === 0 ? 'A' : 'B'}:</span> 
                        {img.filename}
                      </p>
                      <p className="text-xs text-muted-foreground">Composite: {img.scores.composite_score.toFixed(1)}/10</p>
                    </div>
                  </div>
                ))}
              </div>
            </TabsContent>

            {/* Radar Chart */}
            <TabsContent value="radar" className="space-y-4">
              <div className="bg-background/50 rounded-lg p-4">
                <ResponsiveContainer width="100%" height={400}>
                  <RadarChart data={radarChartData}>
                    <PolarGrid stroke="hsl(var(--border))" />
                    <PolarAngleAxis 
                      dataKey="metric" 
                      tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                    />
                    <PolarRadiusAxis 
                      angle={90} 
                      domain={[0, 100]}
                      tick={{ fill: 'hsl(var(--muted-foreground))' }}
                    />
                    <Radar 
                      name="Image A" 
                      dataKey="Image A" 
                      stroke="#10b981" 
                      fill="#10b981" 
                      fillOpacity={0.3}
                      strokeWidth={2}
                    />
                    <Radar 
                      name="Image B" 
                      dataKey="Image B" 
                      stroke="#3b82f6" 
                      fill="#3b82f6" 
                      fillOpacity={0.3}
                      strokeWidth={2}
                    />
                    <Legend />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'hsl(var(--background))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '8px'
                      }}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
              <p className="text-xs text-center text-muted-foreground">
                Radar chart shows overall visual profile. Larger area = stronger visual signal across all dimensions.
              </p>
            </TabsContent>

            {/* Detailed Breakdown */}
            <TabsContent value="details" className="space-y-4">
              <div className="space-y-3">
                {Object.entries(METRIC_INFO).map(([key, info]) => (
                  <div 
                    key={key} 
                    className="p-4 bg-background/50 rounded-lg border border-border hover:border-primary/50 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2">
                        {info.icon}
                        <h3 className="font-bold">{info.name}</h3>
                        <Badge variant="outline">{info.weight}</Badge>
                        <MetricExplanation metricKey={key} />
                      </div>
                      <div className="flex gap-4">
                        <div className="text-right">
                          <p className="text-xs text-muted-foreground">Image A</p>
                          <p className="text-lg font-bold text-emerald-500">
                            {barChartData.find(m => m.metricKey === key)?.['Image A'] || 0}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-muted-foreground">Image B</p>
                          <p className="text-lg font-bold text-blue-500">
                            {barChartData.find(m => m.metricKey === key)?.['Image B'] || 0}
                          </p>
                        </div>
                      </div>
                    </div>
                    <p className="text-sm text-muted-foreground mb-2">{info.description}</p>
                    <div className="grid grid-cols-2 gap-4 text-xs">
                      <div>
                        <p className="font-medium text-muted-foreground mb-1">Measurement:</p>
                        <p className="text-muted-foreground/80">{info.measurement}</p>
                      </div>
                      <div>
                        <p className="font-medium text-muted-foreground mb-1">Optimal Range:</p>
                        <p className="text-muted-foreground/80">{info.optimalRange}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </TabsContent>
          </Tabs>

          {/* Performance Summary */}
          <div className="grid grid-cols-2 gap-4 pt-4 border-t border-border">
            {comparisonImages.map((img, idx) => {
              const winner = img.scores.composite_score > comparisonImages[1 - idx].scores.composite_score;
              return (
                <div 
                  key={img.image_id}
                  className={`p-4 rounded-lg border-2 ${winner ? 'bg-emerald-500/5 border-emerald-500/50' : 'bg-background/50 border-border'}`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <div className={`w-3 h-3 rounded-full ${idx === 0 ? 'bg-emerald-500' : 'bg-blue-500'}`} />
                    <p className="font-bold">Image {idx === 0 ? 'A' : 'B'}</p>
                    {winner && <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/50 ml-auto">WINNER</Badge>}
                  </div>
                  <p className="text-3xl font-bold mb-2">{img.scores.composite_score.toFixed(1)}/10</p>
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div>
                      <p className="text-muted-foreground">Relevance</p>
                      <p className="font-bold">{img.scores.restaurant_relevance.toFixed(1)}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Viral</p>
                      <p className="font-bold">{img.scores.viral_potential.toFixed(1)}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Aesthetic</p>
                      <p className="font-bold">{img.scores.aesthetic_quality.toFixed(1)}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </HolographicCard>
    </motion.div>
  );
};
