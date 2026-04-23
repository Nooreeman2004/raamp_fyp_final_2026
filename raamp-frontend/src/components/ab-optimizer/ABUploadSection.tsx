import { useRef } from "react";
import { Upload, Image, Sparkles, Loader2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { HolographicCard } from "@/components/ui/holographic-card";
import Reveal from "@/components/ui/Reveal";
import { useToast } from "@/hooks/use-toast";
import { type Asset } from "@/services/assetService";

interface ABUploadSectionProps {
    selectedFiles: File[];
    selectedLibraryAssets: Asset[];
    previewUrls: string[];
    isAnalyzing: boolean;
    onFilesSelect: (files: File[]) => void;
    onLibraryTrigger: () => void;
    onRemoveFile: (index: number) => void;
    onAnalyze: () => void;
}

export const ABUploadSection = ({
    selectedFiles,
    selectedLibraryAssets,
    previewUrls,
    isAnalyzing,
    onFilesSelect,
    onLibraryTrigger,
    onRemoveFile,
    onAnalyze
}: ABUploadSectionProps) => {
    const { toast } = useToast();
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const files = Array.from(event.target.files || []);
        const totalAfterUpload = files.length + selectedLibraryAssets.length;
        
        if (totalAfterUpload < 2) {
            toast({
                title: "Too few images",
                description: "Please select at least 2 images total (device + library)",
                variant: "destructive",
            });
            return;
        }
        
        if (totalAfterUpload > 5) {
            toast({
                title: "Too many images",
                description: `You can only select ${5 - selectedLibraryAssets.length} more image(s). Maximum 5 total.`,
                variant: "destructive",
            });
            return;
        }

        const validTypes = ["image/jpeg", "image/jpg", "image/png", "image/webp"];
        const invalidFiles = files.filter(f => !validTypes.includes(f.type));
        
        const MAX_SIZE = 10 * 1024 * 1024; // 10MB
        const oversizedFiles = files.filter(f => f.size > MAX_SIZE);
        
        if (oversizedFiles.length > 0) {
            toast({
                title: "File too large",
                description: `Images must be smaller than 10MB. Found ${oversizedFiles.length} oversized file(s).`,
                variant: "destructive",
            });
            return;
        }

        if (invalidFiles.length > 0) {
            toast({
                title: "Invalid file type",
                description: "Please upload only JPEG, PNG, or WebP images",
                variant: "destructive",
            });
            return;
        }

        onFilesSelect(files);
    };

    return (
        <Reveal variant="fadeInUp" delay={0.2}>
            <HolographicCard className="p-4 sm:p-6">
                <div className="space-y-4">
                    {/* Flow Indicator */}
                    <div className="flex justify-center mb-4">
                        <div className="flex items-center gap-2 sm:gap-4 text-xs sm:text-sm font-medium text-muted-foreground">
                            <div className="flex items-center gap-2 text-primary font-bold">
                                <div className="w-5 h-5 sm:w-6 sm:h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center">1</div>
                                <span>Upload</span>
                            </div>
                            <div className="w-4 sm:w-8 h-[1px] bg-border"></div>
                            <div className="flex items-center gap-2 opacity-60">
                                <div className="w-5 h-5 sm:w-6 sm:h-6 rounded-full bg-muted flex items-center justify-center">2</div>
                                <span>Analyze</span>
                            </div>
                            <div className="w-4 sm:w-8 h-[1px] bg-border"></div>
                            <div className="flex items-center gap-2 opacity-60">
                                <div className="w-5 h-5 sm:w-6 sm:h-6 rounded-full bg-muted flex items-center justify-center">3</div>
                                <span>Compare</span>
                            </div>
                        </div>
                    </div>

                    <div className="text-center">
                        <h2 className="text-xl font-bold mb-1">Upload Images</h2>
                        <p className="text-sm text-muted-foreground">
                            Select 2-5 images from device, library, or both (JPEG, PNG, WebP)
                        </p>
                    </div>

                    <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/jpeg,image/png,image/webp"
                        multiple
                        onChange={handleFileChange}
                        className="hidden"
                    />

                    {selectedFiles.length === 0 && selectedLibraryAssets.length === 0 ? (
                        <div className="flex flex-col gap-4">
                            <div
                                onClick={() => fileInputRef.current?.click()}
                                className="border-2 border-dashed border-muted-foreground/30 rounded-lg p-4 sm:p-6 text-center cursor-pointer hover:border-primary/50 transition-colors"
                            >
                                <Upload className="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
                                <p className="text-base font-medium mb-1">Click to upload images</p>
                                <p className="text-xs text-muted-foreground">
                                    2-5 images • Max 10MB each
                                </p>
                            </div>
                            <div className="flex items-center gap-4">
                                <div className="h-[1px] flex-1 bg-border" />
                                <span className="text-xs text-muted-foreground font-mono">OR</span>
                                <div className="h-[1px] flex-1 bg-border" />
                            </div>
                            <Button 
                                variant="outline" 
                                className="w-full h-12 border-primary/30 hover:bg-primary/5 text-primary gap-2"
                                onClick={onLibraryTrigger}
                            >
                                <Image className="w-5 h-5" />
                                Select from Assets Library
                            </Button>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                                {previewUrls.map((url, index) => {
                                    const isFromLibrary = index < selectedLibraryAssets.length;
                                    const fileName = isFromLibrary 
                                        ? selectedLibraryAssets[index]?.file_name 
                                        : selectedFiles[index - selectedLibraryAssets.length]?.name;
                                    
                                    return (
                                        <div key={index} className="relative group">
                                            <img
                                                src={url}
                                                alt={fileName}
                                                className="w-full h-32 object-cover rounded-lg border border-border"
                                            />
                                            <button
                                                onClick={() => onRemoveFile(index)}
                                                className="absolute top-2 right-2 p-1 bg-red-500/80 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                                            >
                                                <X className="w-4 h-4 text-white" />
                                            </button>
                                            <div className={`absolute top-2 left-2 px-2 py-0.5 rounded-full text-xs font-semibold ${
                                                isFromLibrary
                                                    ? 'bg-primary/90 text-primary-foreground'
                                                    : 'bg-black/70 text-white'
                                            }`}>
                                                {isFromLibrary ? 'Library' : 'Device'}
                                            </div>
                                            <p className="text-xs text-muted-foreground mt-1 truncate">
                                                {fileName}
                                            </p>
                                        </div>
                                    );
                                })}
                            </div>

                            <div className="flex gap-4 justify-center">
                                <Button
                                    variant="outline"
                                    onClick={() => fileInputRef.current?.click()}
                                    disabled={isAnalyzing}
                                >
                                    <Upload className="w-4 h-4 mr-2" />
                                    Change Images
                                </Button>
                                
                                <Button
                                    variant="outline"
                                    onClick={onLibraryTrigger}
                                    disabled={isAnalyzing}
                                >
                                    <Image className="w-4 h-4 mr-2" />
                                    Library
                                </Button>
                                
                                <Button
                                    onClick={onAnalyze}
                                    disabled={isAnalyzing || (selectedFiles.length + selectedLibraryAssets.length < 2)}
                                    className="bg-gradient-to-r from-primary to-purple-600 px-8"
                                >
                                    {isAnalyzing ? (
                                        <>
                                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                            Analyzing...
                                        </>
                                    ) : (
                                        <>
                                            <Sparkles className="w-4 h-4 mr-2" />
                                            Analyze with AI
                                        </>
                                    )}
                                </Button>
                            </div>
                            
                            {isAnalyzing && (
                                <div className="space-y-2">
                                    <Progress value={66} className="h-2" />
                                    <p className="text-sm text-center text-muted-foreground">
                                        AI is analyzing your images... This may take 10-15 seconds
                                    </p>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </HolographicCard>
        </Reveal>
    );
};
