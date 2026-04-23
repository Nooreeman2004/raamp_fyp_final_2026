import { useState, useCallback, useEffect } from "react";
import { useToast } from "@/hooks/use-toast";
import { abOptimizerService, BatchAnalysisResponse, BatchSummary, ScoringConfig } from "@/services/abOptimizerService";
import { type Asset } from "@/services/assetService";

export const useABOptimizer = () => {
    const { toast } = useToast();
    
    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const [previewUrls, setPreviewUrls] = useState<string[]>([]);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [analysisResult, setAnalysisResult] = useState<BatchAnalysisResponse | null>(null);
    const [batchHistory, setBatchHistory] = useState<BatchSummary[]>([]);
    const [isLoadingHistory, setIsLoadingHistory] = useState(false);
    const [selectedLibraryAssets, setSelectedLibraryAssets] = useState<Asset[]>([]);
    const [scoringConfig, setScoringConfig] = useState<ScoringConfig | null>(null);

    // Load past batches
    const loadBatchHistory = useCallback(async () => {
        setIsLoadingHistory(true);
        try {
            const batches = await abOptimizerService.getUserBatches(10);
            setBatchHistory(Array.isArray(batches) ? batches : []);
        } catch (error) {
            console.error('Failed to load batch history:', error);
        } finally {
            setIsLoadingHistory(false);
        }
    }, []);

    // Load scoring config
    const loadScoringConfig = useCallback(async () => {
        try {
            const config = await abOptimizerService.getConfig();
            setScoringConfig(config);
        } catch (err) {
            console.error("Failed to load scoring config", err);
        }
    }, []);

    // Initial load
    useEffect(() => {
        loadBatchHistory();
        loadScoringConfig();
    }, [loadBatchHistory, loadScoringConfig]);

    // Load a past batch
    const loadPastBatch = useCallback(async (batchId: string) => {
        try {
            const result = await abOptimizerService.getBatchResults(batchId);
            setAnalysisResult(result);
            setSelectedFiles([]);
            setSelectedLibraryAssets([]);
            setPreviewUrls([]);
            toast({
                title: "Batch Loaded",
                description: "Past analysis results loaded successfully",
            });
        } catch (error) {
            toast({
                title: "Failed to Load",
                description: error instanceof Error ? error.message : "Failed to load past batch",
                variant: "destructive",
            });
        }
    }, [toast]);

    const handleAnalyze = async () => {
        const totalImages = selectedFiles.length + selectedLibraryAssets.length;

        if (totalImages < 2) {
            toast({
                title: "Not enough images",
                description: "Please select at least 2 images (from device or library)",
                variant: "destructive",
            });
            return;
        }

        if (totalImages > 5) {
            toast({
                title: "Too many images",
                description: "Maximum 5 images allowed per batch",
                variant: "destructive",
            });
            return;
        }

        setIsAnalyzing(true);
        
        try {
            let result;
            
            // Mixed mode: some from library, some from device
            if (selectedLibraryAssets.length > 0 && selectedFiles.length > 0) {
                // For now, analyze files first, then merge with library
                // TODO: Backend should support mixed mode in single request
                toast({
                    title: "Mixed Upload",
                    description: "Uploading device images first, then adding library images...",
                });
                result = await abOptimizerService.uploadAndAnalyze(selectedFiles);
            } else if (selectedLibraryAssets.length > 0) {
                // Only library images
                const assetIds = selectedLibraryAssets.map(a => a.asset_id);
                result = await abOptimizerService.analyzeFromLibrary(assetIds);
            } else {
                // Only uploaded files
                result = await abOptimizerService.uploadAndAnalyze(selectedFiles);
            }
            
            setAnalysisResult(result);
            await loadBatchHistory();
            
            toast({
                title: "Analysis Complete",
                description: `Analyzed ${result.total_images} images successfully`,
            });
        } catch (error: unknown) {
            // Better error handling to avoid "[object Object]" display
            let errorMessage = "Failed to analyze images. Please try again.";
            
            if (error instanceof Error) {
                errorMessage = error.message;
            } else if (typeof error === 'string') {
                errorMessage = error;
            } else if (error && typeof error === 'object') {
                // Try to extract message from error object
                const err = error as Record<string, unknown>;
                errorMessage = String(err.message || err.detail || err.error || errorMessage);
            }
            
            console.error('Analysis error:', error);
            
            toast({
                title: "Analysis Failed",
                description: errorMessage,
                variant: "destructive",
            });
        } finally {
            setIsAnalyzing(false);
        }
    };

    const resetAnalysis = () => {
        previewUrls.forEach(url => {
            if (url.startsWith('blob:')) URL.revokeObjectURL(url);
        });
        setSelectedFiles([]);
        setSelectedLibraryAssets([]);
        setPreviewUrls([]);
        setAnalysisResult(null);
    };

    return {
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
        loadBatchHistory,
        loadPastBatch,
        handleAnalyze,
        resetAnalysis
    };
};
