import React from "react";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";

interface MediaPreviewModalProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    mediaUrl: string;
    caption?: string;
}

export const MediaPreviewModal: React.FC<MediaPreviewModalProps> = ({
    open,
    onOpenChange,
    mediaUrl,
    caption,
}) => {
    const isVideo = (url: string) => {
        return url.match(/\.(mp4|webm|ogg|mov)$/i);
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-auto">
                <DialogHeader>
                    <DialogTitle>Media Preview</DialogTitle>
                </DialogHeader>
                <div className="relative">
                    {isVideo(mediaUrl) ? (
                        <video
                            src={mediaUrl}
                            controls
                            className="w-full rounded-lg"
                            autoPlay
                        />
                    ) : (
                        <img
                            src={mediaUrl}
                            alt={caption || "Media preview"}
                            className="w-full rounded-lg"
                        />
                    )}
                </div>
                {caption && (
                    <div className="mt-4 p-4 bg-white/5 rounded-lg border border-white/10">
                        <p className="text-sm text-muted-foreground mb-1">Caption:</p>
                        <p className="text-sm">{caption}</p>
                    </div>
                )}
            </DialogContent>
        </Dialog>
    );
};
