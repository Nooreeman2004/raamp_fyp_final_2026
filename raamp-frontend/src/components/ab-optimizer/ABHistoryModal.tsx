import { History, Image, Clock, Check, Loader2, Sparkles, Upload, Activity } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { motion } from "framer-motion";
import { BatchSummary } from "@/services/abOptimizerService";

interface ABHistoryModalProps {
    isOpen: boolean;
    onOpenChange: (open: boolean) => void;
    isLoading: boolean;
    history: BatchSummary[];
    currentBatchId?: string;
    onLoadBatch: (batchId: string) => void;
    onReset: () => void;
    onMonitor?: (scheduleId: string) => void;
}

export const ABHistoryModal = ({
    isOpen,
    onOpenChange,
    isLoading,
    history = [],
    currentBatchId,
    onLoadBatch,
    onReset,
    onMonitor
}: ABHistoryModalProps) => {
    return (
        <Dialog open={isOpen} onOpenChange={onOpenChange}>
            <DialogTrigger asChild>
                <Button variant="outline" size="sm" className="flex items-center gap-2 h-8 px-2 sm:px-3 relative group overflow-hidden border-primary/30 hover:bg-primary/5 transition-all">
                    <div className="absolute inset-0 bg-primary/5 group-hover:bg-primary/10 transition-colors" />
                    <History className="w-4 h-4 text-primary relative z-10" />
                    <span className="hidden sm:inline text-primary font-medium relative z-10">History</span>
                </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl max-h-[85vh] flex flex-col">
                <DialogHeader className="flex flex-col gap-2">
                    <div className="flex items-center gap-2">
                        <Button variant="ghost" size="icon" className="h-8 w-8 -ml-2 text-muted-foreground" onClick={() => onOpenChange(false)}>
                            <span className="sr-only">Back</span>
                            &larr;
                        </Button>
                        <DialogTitle className="flex items-center gap-2 text-xl">
                            <History className="w-5 h-5 text-primary" />
                            Past Scans
                        </DialogTitle>
                    </div>
                    <DialogDescription className="pl-10">
                        View and load your previous A/B test analyses
                    </DialogDescription>
                </DialogHeader>
                
                {isLoading ? (
                    <div className="flex justify-center py-12">
                        <Loader2 className="w-8 h-8 animate-spin text-primary" />
                    </div>
                ) : (!Array.isArray(history) || history.length === 0) ? (
                    <div className="flex flex-col items-center justify-center py-12 text-center">
                        <div className="w-16 h-16 bg-muted/30 rounded-full flex items-center justify-center mb-4">
                            <Sparkles className="w-8 h-8 text-muted-foreground/40" />
                        </div>
                        <h3 className="text-lg font-medium mb-2">No History Yet</h3>
                        <p className="text-sm text-muted-foreground max-w-xs mb-6">
                            You haven't run any A/B tests yet. Upload your first batch of images to start optimizing.
                        </p>
                        <Button onClick={() => {
                            onOpenChange(false);
                            onReset();
                        }}>
                            <Upload className="w-4 h-4 mr-2" />
                            Upload Images
                        </Button>
                    </div>
                ) : (
                    <ScrollArea className="h-[500px] pr-4">
                        <div className="space-y-3">
                            {history.map((batch) => (
                                <motion.div
                                    key={batch.batch_id}
                                    whileHover={{ scale: 1.01 }}
                                    whileTap={{ scale: 0.99 }}
                                >
                                    <div
                                        className={`w-full text-left p-4 rounded-lg border transition-all ${
                                            currentBatchId === batch.batch_id
                                                ? 'border-primary bg-primary/10'
                                                : 'border-border bg-card'
                                        }`}
                                    >
                                        <div className="flex items-start justify-between mb-3">
                                            <div className="flex items-center gap-2">
                                                <Image className="w-5 h-5 text-primary" />
                                                <span className="font-medium">
                                                    {batch.image_count} Images
                                                </span>
                                            </div>
                                            {batch.score_gap !== undefined && batch.score_gap !== null && (
                                                <Tooltip>
                                                    <TooltipTrigger asChild>
                                                        <Badge variant="outline" className="text-xs cursor-help">
                                                            Gap: {batch.score_gap.toFixed(2)}
                                                        </Badge>
                                                    </TooltipTrigger>
                                                    <TooltipContent>
                                                        <p>Score gap between top 2 images. Higher is better.</p>
                                                    </TooltipContent>
                                                </Tooltip>
                                            )}
                                        </div>
                                        
                                        <div className="flex items-center justify-between mt-2">
                                            <div>
                                                <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
                                                    <Clock className="w-4 h-4" />
                                                    {new Date(batch.created_at).toLocaleDateString('en-US', {
                                                        month: 'short',
                                                        day: 'numeric',
                                                        year: 'numeric',
                                                        hour: '2-digit',
                                                        minute: '2-digit',
                                                    })}
                                                </div>
                                                
                                                {batch.recommended_pair && (
                                                    <div className="flex items-center gap-1 text-sm text-primary">
                                                        <Check className="w-4 h-4" />
                                                        A/B pair recommended
                                                    </div>
                                                )}
                                            </div>
                                            
                                            <div className="flex items-center gap-2">
                                                <Button
                                                    variant={currentBatchId === batch.batch_id ? "secondary" : "outline"}
                                                    size="sm"
                                                    onClick={() => {
                                                        onLoadBatch(batch.batch_id);
                                                        onOpenChange(false);
                                                    }}
                                                    className="min-w-[100px]"
                                                >
                                                    {currentBatchId === batch.batch_id ? (
                                                        <>
                                                            <Check className="w-3 h-3 mr-1" />
                                                            Viewing
                                                        </>
                                                    ) : (
                                                        <>
                                                            <Sparkles className="w-3 h-3 mr-1" />
                                                            View Analysis
                                                        </>
                                                    )}
                                                </Button>
                                                <Button
                                                    variant="default"
                                                    size="sm"
                                                    className="bg-primary text-black hover:bg-primary/90 min-w-[100px]"
                                                    onClick={() => {
                                                        if (batch.schedule_id && onMonitor) {
                                                            onMonitor(batch.schedule_id);
                                                        } else {
                                                            // No schedule - just load the analysis results
                                                            onLoadBatch(batch.batch_id);
                                                        }
                                                        onOpenChange(false);
                                                    }}
                                                >
                                                    <Activity className="w-3 h-3 mr-1" />
                                                    {batch.schedule_id ? "Monitor Post" : "View Results"}
                                                </Button>
                                            </div>
                                        </div>
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    </ScrollArea>
                )}
            </DialogContent>
        </Dialog>
    );
};
