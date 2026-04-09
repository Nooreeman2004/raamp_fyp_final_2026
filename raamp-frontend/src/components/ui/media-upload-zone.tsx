import React, { useCallback, useState } from "react";
import { Upload, Link as LinkIcon, X, Image as ImageIcon, Video } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "./button";
import { Input } from "./input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./tabs";

interface MediaUploadZoneProps {
    onMediaSelect: (file: File | null, url: string | null) => void;
    accept?: string;
    maxSizeMB?: number;
    className?: string;
}

export const MediaUploadZone: React.FC<MediaUploadZoneProps> = ({
    onMediaSelect,
    accept = "image/*,video/*",
    maxSizeMB = 100,
    className,
}) => {
    const [isDragging, setIsDragging] = useState(false);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [mediaUrl, setMediaUrl] = useState("");
    const [preview, setPreview] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<"upload" | "url">("upload");

    const validateFile = (file: File): string | null => {
        const maxSize = maxSizeMB * 1024 * 1024;
        if (file.size > maxSize) {
            return `File size must be less than ${maxSizeMB}MB`;
        }
        return null;
    };

    const handleFileSelect = useCallback(
        (file: File) => {
            const validationError = validateFile(file);
            if (validationError) {
                setError(validationError);
                return;
            }

            setError(null);
            setSelectedFile(file);

            // Create preview
            const reader = new FileReader();
            reader.onload = (e) => {
                setPreview(e.target?.result as string);
            };
            reader.readAsDataURL(file);

            onMediaSelect(file, null);
        },
        [onMediaSelect, maxSizeMB]
    );

    const handleDrop = useCallback(
        (e: React.DragEvent) => {
            e.preventDefault();
            setIsDragging(false);

            const file = e.dataTransfer.files[0];
            if (file) {
                handleFileSelect(file);
            }
        },
        [handleFileSelect]
    );

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback(() => {
        setIsDragging(false);
    }, []);

    const handleFileInputChange = useCallback(
        (e: React.ChangeEvent<HTMLInputElement>) => {
            const file = e.target.files?.[0];
            if (file) {
                handleFileSelect(file);
            }
        },
        [handleFileSelect]
    );

    const handleUrlChange = useCallback(
        (url: string) => {
            setMediaUrl(url);
            setError(null);

            if (url.trim()) {
                // Validate URL format
                try {
                    new URL(url);
                    setPreview(url);
                    onMediaSelect(null, url);
                } catch {
                    setError("Please enter a valid URL");
                }
            } else {
                setPreview(null);
                onMediaSelect(null, null);
            }
        },
        [onMediaSelect]
    );

    const handleClear = useCallback(() => {
        setSelectedFile(null);
        setMediaUrl("");
        setPreview(null);
        setError(null);
        onMediaSelect(null, null);
    }, [onMediaSelect]);

    const isVideo = (src: string) => {
        return src.match(/\.(mp4|webm|ogg|mov)$/i) || selectedFile?.type.startsWith("video/");
    };

    return (
        <div className={cn("w-full", className)}>
            <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "upload" | "url")}>
                <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="upload">
                        <Upload className="w-4 h-4 mr-2" />
                        Upload File
                    </TabsTrigger>
                    <TabsTrigger value="url">
                        <LinkIcon className="w-4 h-4 mr-2" />
                        Media URL
                    </TabsTrigger>
                </TabsList>

                <TabsContent value="upload" className="mt-4">
                    {!preview ? (
                        <div
                            onDrop={handleDrop}
                            onDragOver={handleDragOver}
                            onDragLeave={handleDragLeave}
                            className={cn(
                                "border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer",
                                isDragging
                                    ? "border-primary bg-primary/5"
                                    : "border-border/50 hover:border-border/80 bg-foreground/5"
                            )}
                            onClick={() => document.getElementById("file-input")?.click()}
                        >
                            <input
                                id="file-input"
                                type="file"
                                accept={accept}
                                onChange={handleFileInputChange}
                                className="hidden"
                            />
                            <Upload className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                            <p className="text-sm text-muted-foreground mb-2">
                                Drag and drop your media here, or click to browse
                            </p>
                            <p className="text-xs text-muted-foreground">
                                Supports images and videos (max {maxSizeMB}MB)
                            </p>
                        </div>
                    ) : (
                        <div className="relative rounded-lg overflow-hidden border border-border/50 bg-card/50">
                            {isVideo(preview) ? (
                                <video src={preview} controls className="w-full max-h-64 object-contain" />
                            ) : (
                                <img src={preview} alt="Preview" className="w-full max-h-64 object-contain" />
                            )}
                            <Button
                                variant="destructive"
                                size="icon"
                                className="absolute top-2 right-2"
                                onClick={handleClear}
                            >
                                <X className="w-4 h-4" />
                            </Button>
                        </div>
                    )}
                </TabsContent>

                <TabsContent value="url" className="mt-4">
                    <div className="space-y-4">
                        <Input
                            placeholder="https://example.com/image.jpg"
                            value={mediaUrl}
                            onChange={(e) => handleUrlChange(e.target.value)}
                            className="bg-foreground/5 border-border/50"
                        />
                        {preview && (
                            <div className="relative rounded-lg overflow-hidden border border-border/50 bg-card/50">
                                {isVideo(preview) ? (
                                    <video src={preview} controls className="w-full max-h-64 object-contain" />
                                ) : (
                                    <img src={preview} alt="Preview" className="w-full max-h-64 object-contain" />
                                )}
                                <Button
                                    variant="destructive"
                                    size="icon"
                                    className="absolute top-2 right-2"
                                    onClick={handleClear}
                                >
                                    <X className="w-4 h-4" />
                                </Button>
                            </div>
                        )}
                    </div>
                </TabsContent>
            </Tabs>

            {error && (
                <p className="text-sm text-red-500 mt-2">{error}</p>
            )}
        </div>
    );
};
