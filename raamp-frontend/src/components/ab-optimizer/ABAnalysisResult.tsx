import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, X, Download, Upload, Target, AlertTriangle, TrendingUp, BarChart3, CheckCircle, AlertCircle, XCircle, Utensils, Megaphone, Home, Menu, Users, Camera } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { HolographicCard } from "@/components/ui/holographic-card";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { ABTestScoreComparison } from "@/components/ABTestScoreComparison";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Legend } from "recharts";
import { BatchAnalysisResponse, ScoringConfig, ImageAnalysis } from "@/services/abOptimizerService";

interface ABAnalysisResultProps {
    result: BatchAnalysisResponse;
    scoringConfig: ScoringConfig | null;
    onBack: () => void;
    onExportPDF: () => void;
    onNewScan: () => void;
    onContinue?: () => void;
}

export const ABAnalysisResult = ({
    result,
    scoringConfig,
    onBack,
    onExportPDF,
    onNewScan,
    onContinue
}: ABAnalysisResultProps) => {
    
    const getScoreColor = (grade?: string): string => {
        if (grade === 'excellent') return "text-emerald-500";
        if (grade === 'good') return "text-amber-500";
        return "text-red-500";
    };

    const getRelevanceBadge = (level?: string) => {
        if (level === 'relevant') {
            return (
                <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/50">
                    <CheckCircle className="w-3 h-3 mr-1" />
                    RELEVANT
                </Badge>
            );
        } else if (level === 'weak') {
            return (
                <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/50">
                    <AlertCircle className="w-3 h-3 mr-1" />
                    WEAK
                </Badge>
            );
        } else if (level === 'not_relevant') {
            return (
                <Badge className="bg-red-500/20 text-red-400 border-red-500/50">
                    <XCircle className="w-3 h-3 mr-1" />
                    NOT RELEVANT
                </Badge>
            );
        }
        // Fallback for undefined/unknown levels
        return (
            <Badge className="bg-muted/50 text-muted-foreground border-border">
                <AlertCircle className="w-3 h-3 mr-1" />
                UNKNOWN
            </Badge>
        );
    };

    const getContentTypeIcon = (type: string) => {
        const iconMap: Record<string, React.ReactNode> = {
            food: <Utensils className="w-4 h-4" />,
            poster: <Megaphone className="w-4 h-4" />,
            interior: <Home className="w-4 h-4" />,
            menu: <Menu className="w-4 h-4" />,
            people: <Users className="w-4 h-4" />,
            other: <XCircle className="w-4 h-4" />
        };
        return iconMap[type] || <Camera className="w-4 h-4" />;
    };

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-8"
            >
                {/* Header Actions */}
                <div className="flex flex-wrap items-center justify-between gap-4 bg-card p-4 rounded-xl border border-border shadow-sm">
                    <div className="flex flex-col">
                        <h2 className="text-xl font-bold flex items-center gap-2">
                            <Sparkles className="w-5 h-5 text-primary" />
                            Analysis Complete
                        </h2>
                        <p className="text-sm text-muted-foreground">
                            Viewing results for {result.total_images} images
                        </p>
                    </div>
                    
                    <div className="flex items-center gap-2 flex-wrap">
                        <Button variant="ghost" size="sm" onClick={onBack}>
                            <X className="w-4 h-4 mr-2" />
                            Back to Upload
                        </Button>
                        <Button variant="outline" size="sm" onClick={onExportPDF}>
                            <Download className="w-4 h-4 mr-2" />
                            Export PDF
                        </Button>
                        <Button size="sm" onClick={onNewScan} className="bg-primary hover:bg-primary/90 text-primary-foreground">
                            <Upload className="w-4 h-4 mr-2" />
                            Run New Analysis
                        </Button>
                        {onContinue && result.recommended_pair && (
                            <Button size="sm" onClick={onContinue} className="bg-emerald-500 hover:bg-emerald-600 text-white">
                                <TrendingUp className="w-4 h-4 mr-2" />
                                Continue to Schedule
                            </Button>
                        )}
                    </div>
                </div>

                {/* A/B Test Recommendation */}
                {result.recommended_pair && (
                    <HolographicCard className="p-6 bg-gradient-to-br from-primary/10 to-purple-500/10 border-2 border-primary/50">
                        <div className="flex items-start gap-4">
                            <div className="p-3 bg-primary/20 rounded-lg shrink-0">
                                <Target className="w-6 h-6 text-primary" />
                            </div>
                            <div className="flex-1">
                                <h3 className="text-xl font-bold mb-2">
                                    A/B Test Recommendation
                                </h3>
                                <p className="text-muted-foreground mb-3">
                                    {result.test_advice}
                                </p>
                                <div className="flex gap-4 items-center">
                                    <Tooltip>
                                        <TooltipTrigger asChild>
                                            <Badge className="bg-primary/20 text-primary border-primary/50 cursor-help">
                                                Score Gap: {result.score_gap?.toFixed(2)}
                                            </Badge>
                                        </TooltipTrigger>
                                        <TooltipContent>
                                            <p>Score gap between top 2 images. Higher is better.</p>
                                        </TooltipContent>
                                    </Tooltip>
                                    <p className="text-sm text-muted-foreground">
                                        Testing: {result.images.find(img => img.image_id === result.recommended_pair?.[0])?.filename} vs{' '}
                                        {result.images.find(img => img.image_id === result.recommended_pair?.[1])?.filename}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </HolographicCard>
                )}

                {/* Irrelevant Images Warning */}
                {result.irrelevant_images.length > 0 && (
                    <HolographicCard className="p-6 bg-red-500/5 border-2 border-red-500/50">
                        <div className="flex items-start gap-4">
                            <div className="p-3 bg-red-500/10 rounded-lg shrink-0">
                                <AlertTriangle className="w-6 h-6 text-red-500" />
                            </div>
                            <div>
                                <h3 className="text-xl font-bold text-red-500 mb-2">
                                    Non-Restaurant Content Detected
                                </h3>
                                <p className="text-muted-foreground mb-3">
                                    The following images have low restaurant relevance and should not be used for marketing:
                                </p>
                                <ul className="space-y-2">
                                    {result.irrelevant_images.map((img, idx) => (
                                        <li key={idx} className="text-sm">
                                            <span className="font-medium">{img.filename}</span> - Relevance: {img.relevance_score}/10
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    </HolographicCard>
                )}

                {/* Charts */}
                {result.images.length >= 2 && (
                    <div className="space-y-8">
                        <ABTestScoreComparison 
                            images={result.images}
                            recommendedPair={result.recommended_pair}
                        />

                        <HolographicCard className="p-6">
                            <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
                                <TrendingUp className="w-6 h-6 text-primary" />
                                Score Trend Across Images
                            </h2>
                            <ResponsiveContainer width="100%" height={300}>
                                <LineChart
                                    data={result.images
                                        .sort((a, b) => b.scores.composite_score - a.scores.composite_score)
                                        .map((img, idx) => ({
                                            name: `Image ${String.fromCharCode(65 + idx)}`,
                                            filename: img.filename,
                                            'Composite': img.scores.composite_score,
                                            'Restaurant Relevance': img.scores.restaurant_relevance,
                                            'Viral Potential': img.scores.viral_potential,
                                            'Aesthetic Quality': img.scores.aesthetic_quality,
                                        }))}
                                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                                >
                                    <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                                    <XAxis dataKey="name" className="text-xs font-bold" stroke="currentColor" />
                                    <YAxis domain={[0, 10]} className="text-xs" stroke="currentColor" />
                                    <RechartsTooltip
                                        labelFormatter={(label, payload) => {
                                            if (payload && payload.length > 0) {
                                                return `${label}: ${payload[0].payload.filename}`;
                                            }
                                            return label;
                                        }}
                                        contentStyle={{
                                            backgroundColor: 'hsl(var(--card))',
                                            border: '1px solid hsl(var(--border))',
                                            borderRadius: '8px',
                                        }}
                                    />
                                    <Legend />
                                    <Line type="monotone" dataKey="Composite" stroke="hsl(var(--primary))" strokeWidth={5} dot={{ r: 6 }} />
                                    <Line type="monotone" dataKey="Restaurant Relevance" stroke="#10b981" strokeWidth={2} strokeDasharray="5 5" />
                                    <Line type="monotone" dataKey="Viral Potential" stroke="#f59e0b" strokeWidth={2} strokeDasharray="5 5" />
                                    <Line type="monotone" dataKey="Aesthetic Quality" stroke="#3b82f6" strokeWidth={2} strokeDasharray="5 5" />
                                </LineChart>
                            </ResponsiveContainer>
                        </HolographicCard>
                    </div>
                )}

                {/* Individual Cards */}
                <div>
                    <h2 className="text-2xl font-bold flex items-center gap-2 mb-4">
                        <BarChart3 className="w-6 h-6 text-primary" />
                        Image Rankings
                    </h2>
                    <div className="grid gap-6">
                        {result.images
                            .sort((a, b) => b.scores.composite_score - a.scores.composite_score)
                            .map((image, index) => (
                                <HolographicCard key={image.image_id} className="p-6">
                                    <div className="flex flex-col md:flex-row gap-6">
                                        <div className="md:w-48 flex-shrink-0">
                                            {image.image_url && (
                                                <img src={image.image_url} alt={image.filename} className="w-full h-48 object-cover rounded-lg border border-border" />
                                            )}
                                            <p className="text-sm text-muted-foreground mt-2 truncate">{image.filename}</p>
                                        </div>
                                        <div className="flex-1 space-y-4">
                                            <div className="flex items-start justify-between">
                                                <div>
                                                    <div className="flex items-center gap-3 mb-2">
                                                        <span className="text-2xl font-bold">#{index + 1}</span>
                                                        <div className="flex items-center gap-2">
                                                            {getContentTypeIcon(image.content_type)}
                                                            <Badge variant="outline">{image.content_type.toUpperCase()}</Badge>
                                                        </div>
                                                        {getRelevanceBadge(image.relevance_level)}
                                                    </div>
                                                    <p className={`text-3xl font-bold ${getScoreColor(image.score_grade)}`}>
                                                        {image.scores.composite_score.toFixed(1)}/10
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="grid grid-cols-3 gap-4">
                                                <div>
                                                    <p className="text-sm text-muted-foreground mb-1">Relevance</p>
                                                    <p className="text-lg font-bold">{image.scores.restaurant_relevance.toFixed(1)}/10</p>
                                                </div>
                                                <div>
                                                    <p className="text-sm text-muted-foreground mb-1">Viral</p>
                                                    <p className="text-lg font-bold">{image.scores.viral_potential.toFixed(1)}/10</p>
                                                </div>
                                                <div>
                                                    <p className="text-sm text-muted-foreground mb-1">Aesthetic</p>
                                                    <p className="text-lg font-bold">{image.scores.aesthetic_quality.toFixed(1)}/10</p>
                                                </div>
                                            </div>
                                            <div className="grid md:grid-cols-2 gap-4">
                                                <div className="p-3 bg-blue-500/5 border border-blue-500/30 rounded-lg">
                                                    <p className="font-medium text-blue-400 mb-1 flex items-center gap-2 text-sm"><CheckCircle className="w-4 h-4" /> Strengths</p>
                                                    <p className="text-xs text-muted-foreground whitespace-pre-line">{image.why_good}</p>
                                                </div>
                                                <div className="p-3 bg-red-500/5 border border-red-500/30 rounded-lg">
                                                    <p className="font-medium text-red-400 mb-1 flex items-center gap-2 text-sm"><AlertTriangle className="w-4 h-4" /> Weaknesses</p>
                                                    <p className="text-xs text-muted-foreground whitespace-pre-line">{image.why_bad}</p>
                                                </div>
                                            </div>
                                            <div className="p-3 bg-primary/10 border-2 border-primary/30 rounded-xl mt-2">
                                                <p className="font-bold text-primary mb-1 flex items-center gap-2 text-sm"><Sparkles className="w-4 h-4" /> Recommendation</p>
                                                <p className="text-xs text-muted-foreground leading-relaxed font-medium">{image.recommendation}</p>
                                            </div>
                                        </div>
                                    </div>
                                </HolographicCard>
                            ))}
                    </div>
                </div>
            </motion.div>
        </AnimatePresence>
    );
};
