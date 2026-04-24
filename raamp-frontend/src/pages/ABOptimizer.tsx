import { useState } from "react";
import Layout from "@/components/Layout";
import { Sparkles, BarChart3, Target } from "lucide-react";
import Reveal from "@/components/ui/Reveal";
import { BlurText } from "@/components/ui/text-reveal";
import { TooltipProvider } from "@/components/ui/tooltip";
import AssetLibraryModal from "@/components/AssetLibraryModal";
import { type Asset } from "@/services/assetService";

// Hooks & Utils
import { useABOptimizer } from "@/hooks/useABOptimizer";
import { useToast } from "@/hooks/use-toast";
import { generateABAnalysisPDF } from "@/utils/abPdfGenerator";

// Types
import type { 
  ScheduleRecommendation, 
  ScheduleConfirmation, 
  WinnerResult 
} from "@/services/abOptimizerService";

// Sub-components
import { ABUploadSection } from "@/components/ab-optimizer/ABUploadSection";
import { ABHistoryModal } from "@/components/ab-optimizer/ABHistoryModal";
import { ABAnalysisResult } from "@/components/ab-optimizer/ABAnalysisResult";
import { ABScheduleRecommendation } from "@/components/ab-optimizer/ABScheduleRecommendation";
import { ABConfirmSchedule } from "@/components/ab-optimizer/ABConfirmSchedule";
import { ABMonitorSchedule } from "@/components/ab-optimizer/ABMonitorSchedule";
import { ABCalculateWinner } from "@/components/ab-optimizer/ABCalculateWinner";
import { ABGenerateAdBrief } from "@/components/ab-optimizer/ABGenerateAdBrief";

type WorkflowStage = 1 | 2 | 3 | 4 | 5 | 6;

const ABOptimizer = () => {
  const {
    selectedFiles,
    setSelectedFiles,
    previewUrls,
    setPreviewUrls,
    isAnalyzing,
    analysisResult,
    setAnalysisResult,
    batchHistory,
    isLoadingHistory,
    selectedLibraryAssets,
    setSelectedLibraryAssets,
    scoringConfig,
    loadPastBatch,
    handleAnalyze,
    resetAnalysis
  } = useABOptimizer();

  const { toast } = useToast();

  const [isHistoryDialogOpen, setIsHistoryDialogOpen] = useState(false);
  const [isLibraryModalOpen, setIsLibraryModalOpen] = useState(false);
  
  // Multi-stage workflow state - persist to sessionStorage to survive re-renders
  const [currentStage, setCurrentStage] = useState<WorkflowStage>(() => {
    const saved = sessionStorage.getItem('ab_optimizer_stage');
    return saved ? (parseInt(saved) as WorkflowStage) : 1;
  });
  const [scheduleRecommendation, setScheduleRecommendation] = useState<ScheduleRecommendation | null>(() => {
    const saved = sessionStorage.getItem('ab_optimizer_recommendation');
    return saved ? JSON.parse(saved) : null;
  });
  const [selectedPlatform, setSelectedPlatform] = useState<string>(() => {
    const saved = sessionStorage.getItem('ab_optimizer_platform');
    return saved || "instagram";
  });
  const [scheduleConfirmation, setScheduleConfirmation] = useState<ScheduleConfirmation | null>(null);
  const [winnerResult, setWinnerResult] = useState<WinnerResult | null>(null);

  // Handle library selection - now supports adding to existing uploads
  const handleLibrarySelect = (assets: Asset[]) => {
    const totalImages = selectedFiles.length + selectedLibraryAssets.length + assets.length;
    
    if (totalImages > 5) {
      // Filter to only allow up to 5 total
      const maxNew = 5 - (selectedFiles.length + selectedLibraryAssets.length);
      assets = assets.slice(0, maxNew);
    }
    
    setSelectedLibraryAssets([...selectedLibraryAssets, ...assets]);
    
    const newUrls = assets.map(asset => {
        const url = asset.cloudinary_url || asset.storage_url;
        if (url.startsWith('http')) return url;
        const cleanPath = url.startsWith('/') ? url : `/${url}`;
        return `${window.location.origin}${cleanPath}`;
    });
    
    setPreviewUrls([...previewUrls, ...newUrls]);
  };

  // Remove a file - supports mixed mode
  const removeFile = (index: number) => {
    const libraryCount = selectedLibraryAssets.length;
    
    if (index < libraryCount) {
      // Removing a library asset
      const newAssets = selectedLibraryAssets.filter((_, i) => i !== index);
      setSelectedLibraryAssets(newAssets);
    } else {
      // Removing an uploaded file
      const fileIndex = index - libraryCount;
      const newFiles = selectedFiles.filter((_, i) => i !== fileIndex);
      if (previewUrls[index]?.startsWith('blob:')) {
        URL.revokeObjectURL(previewUrls[index]);
      }
      setSelectedFiles(newFiles);
    }
    
    const newUrls = previewUrls.filter((_, i) => i !== index);
    setPreviewUrls(newUrls);
  };

  const handleFilesSelect = (files: File[]) => {
    const totalImages = selectedFiles.length + selectedLibraryAssets.length + files.length;
    
    if (totalImages > 5) {
      // Filter to only allow up to 5 total
      const maxNew = 5 - (selectedFiles.length + selectedLibraryAssets.length);
      files = files.slice(0, maxNew);
    }
    
    setSelectedFiles([...selectedFiles, ...files]);
    const newUrls = files.map(file => URL.createObjectURL(file));
    setPreviewUrls([...previewUrls, ...newUrls]);
  };

  // Workflow navigation handlers
  const handleStage1Complete = () => {
    setCurrentStage(2);
  };

  const handleStage2Complete = (recommendation: ScheduleRecommendation, platform: string) => {
    setScheduleRecommendation(recommendation);
    setSelectedPlatform(platform);
    setCurrentStage(3);
    
    // Persist to sessionStorage
    sessionStorage.setItem('ab_optimizer_stage', '3');
    sessionStorage.setItem('ab_optimizer_recommendation', JSON.stringify(recommendation));
    sessionStorage.setItem('ab_optimizer_platform', platform);
  };

  const handleStage3Complete = (confirmation: ScheduleConfirmation) => {
    setScheduleConfirmation(confirmation);
    setCurrentStage(4);
  };

  const handleStage4Complete = (scheduleId: string) => {
    setCurrentStage(5);
  };

  const handleMonitorFromHistory = (scheduleId: string) => {
    setScheduleConfirmation({ schedule_id: scheduleId, status: "scheduled", post_time: new Date().toISOString(), message: "" });
    setCurrentStage(4);
    setIsHistoryDialogOpen(false);
  };

  const handleStage5Complete = (winner: WinnerResult) => {
    setWinnerResult(winner);
    setCurrentStage(6);
  };

  const handleWorkflowComplete = () => {
    // Reset everything and go back to stage 1
    setCurrentStage(1);
    setScheduleRecommendation(null);
    setScheduleConfirmation(null);
    setWinnerResult(null);
    resetAnalysis();
    
    // Clear sessionStorage
    sessionStorage.removeItem('ab_optimizer_stage');
    sessionStorage.removeItem('ab_optimizer_recommendation');
    sessionStorage.removeItem('ab_optimizer_platform');
  };

  const goBackToStage1 = () => {
    setCurrentStage(1);
    sessionStorage.setItem('ab_optimizer_stage', '1');
  };

  // Dynamic breadcrumbs based on current stage
  const getBreadcrumbLabel = () => {
    const stageLabels: Record<WorkflowStage, string> = {
      1: "Upload & Analyze",
      2: "Schedule Recommendation",
      3: "Confirm Schedule",
      4: "Monitor Test",
      5: "Calculate Winner",
      6: "Generate Ad Brief",
    };
    return stageLabels[currentStage];
  };

  const headerActions = (
    <ABHistoryModal 
      isOpen={isHistoryDialogOpen}
      onOpenChange={setIsHistoryDialogOpen}
      isLoading={isLoadingHistory}
      history={batchHistory}
      currentBatchId={analysisResult?.batch_id}
      onLoadBatch={loadPastBatch}
      onReset={resetAnalysis}
      onMonitor={handleMonitorFromHistory}
    />
  );

  return (
    <TooltipProvider delayDuration={100}>
      <Layout
        breadcrumbItems={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'A/B Optimizer', href: '/dashboard/ab-optimizer' },
          ...(currentStage > 1 ? [{ label: getBreadcrumbLabel() }] : []),
        ]}
        headerActions={headerActions}
      >
        <div className="space-y-8">
          {/* Stage 1: Upload & Analyze */}
          {currentStage === 1 && (
            <>
              {/* Hero Header */}
              <Reveal variant="blurInUp" duration={0.6}>
                <div className="text-center space-y-4">
                  <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/30">
                    <Sparkles className="w-4 h-4 text-primary" />
                    <span className="text-sm font-medium text-primary uppercase tracking-wider">AI-Powered Image Analysis</span>
                  </div>
                  <h1 className="text-4xl md:text-5xl font-bold">
                    <BlurText text="A/B TEST OPTIMIZER" />
                  </h1>
                  <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
                    Upload 2-5 images. AI analyzes viral potential, aesthetic quality, and restaurant relevance to recommend the best pair for A/B testing.
                  </p>
                </div>
              </Reveal>

              {/* Upload Section */}
              {!analysisResult && (
                <ABUploadSection 
                  selectedFiles={selectedFiles}
                  selectedLibraryAssets={selectedLibraryAssets}
                  previewUrls={previewUrls}
                  isAnalyzing={isAnalyzing}
                  onFilesSelect={handleFilesSelect}
                  onLibraryTrigger={() => setIsLibraryModalOpen(true)}
                  onRemoveFile={removeFile}
                  onAnalyze={handleAnalyze}
                />
              )}

              {/* Feature Highlights (Show only on landing) */}
              {!analysisResult && !isAnalyzing && selectedFiles.length === 0 && selectedLibraryAssets.length === 0 && (
                <Reveal variant="fadeInUp" delay={0.4}>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl mx-auto mt-6">
                    {[
                      { icon: Sparkles, title: "AI Analysis", desc: "Scores on aesthetics & virality" },
                      { icon: BarChart3, title: "Clear Winners", desc: "Detailed breakdown of performers" },
                      { icon: Target, title: "Smart Pairing", desc: "Recommends the best 2 to test" }
                    ].map((feature, i) => (
                      <div key={i} className="flex items-center gap-3 p-4 rounded-xl border border-border/50 bg-card/30">
                        <div className="p-3 bg-primary/10 rounded-lg shrink-0">
                          <feature.icon className="w-5 h-5 text-primary" />
                        </div>
                        <div>
                          <h4 className="font-semibold text-sm leading-tight mb-0.5">{feature.title}</h4>
                          <p className="text-xs text-muted-foreground leading-snug">{feature.desc}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </Reveal>
              )}

              {/* Results Section */}
              {analysisResult && (
                <ABAnalysisResult 
                  result={analysisResult}
                  scoringConfig={scoringConfig}
                  onBack={() => setAnalysisResult(null)}
                  onExportPDF={() => generateABAnalysisPDF(analysisResult)}
                  onNewScan={resetAnalysis}
                  onContinue={analysisResult.recommended_pair ? handleStage1Complete : undefined}
                />
              )}
            </>
          )}

          {/* Stage 2: Schedule Recommendation */}
          {currentStage === 2 && analysisResult && (
            <ABScheduleRecommendation
              batchId={analysisResult.batch_id}
              onBack={goBackToStage1}
              onContinue={handleStage2Complete}
            />
          )}

          {/* Stage 3: Confirm Schedule */}
          {currentStage === 3 && analysisResult && scheduleRecommendation && (
            <ABConfirmSchedule
              batchId={analysisResult.batch_id}
              recommendation={scheduleRecommendation}
              platform={selectedPlatform}
              recommendedPair={analysisResult.recommended_pair}
              images={analysisResult.images}
              onBack={() => {
                setCurrentStage(2);
                sessionStorage.setItem('ab_optimizer_stage', '2');
              }}
              onContinue={handleStage3Complete}
            />
          )}
          
          {/* Fallback: If stage 3 but missing data, redirect back */}
          {currentStage === 3 && (!analysisResult || !scheduleRecommendation) && (
            (() => {
              // Auto-redirect back to stage 1 if data is missing
              setTimeout(() => {
                setCurrentStage(1);
                sessionStorage.setItem('ab_optimizer_stage', '1');
                toast({
                  title: "Session Lost",
                  description: "Analysis data was lost. Please start over.",
                  variant: "destructive",
                });
              }, 100);
              return null;
            })()
          )}

          {/* Stage 4: Monitor Schedule */}
          {currentStage === 4 && scheduleConfirmation && (
            <ABMonitorSchedule
              confirmation={scheduleConfirmation}
              onContinue={handleStage4Complete}
            />
          )}

          {/* Stage 5: Calculate Winner */}
          {currentStage === 5 && scheduleConfirmation && (
            <ABCalculateWinner
              scheduleId={scheduleConfirmation.schedule_id}
              onBack={() => setCurrentStage(4)}
              onContinue={handleStage5Complete}
            />
          )}

          {/* Stage 6: Generate Ad Brief */}
          {currentStage === 6 && winnerResult && (
            <ABGenerateAdBrief
              winnerResult={winnerResult}
              platform={selectedPlatform}
              onBack={() => setCurrentStage(5)}
              onComplete={handleWorkflowComplete}
            />
          )}
        </div>

        <AssetLibraryModal 
          isOpen={isLibraryModalOpen}
          onClose={() => setIsLibraryModalOpen(false)}
          onSelect={handleLibrarySelect}
          maxSelection={5}
          alreadySelected={selectedFiles.length + selectedLibraryAssets.length}
        />
      </Layout>
    </TooltipProvider>
  );
};

export default ABOptimizer;
