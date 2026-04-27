import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Copy, Check, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { apiClient } from "@/services/api";

export interface QuickTrendPostProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  topic: string;
  location?: string;
  niche?: string;
}

interface CaptionVariant {
  caption: string;
  hashtags: string[];
}

export const QuickTrendPost = ({ open, onOpenChange, topic, location, niche }: QuickTrendPostProps) => {
  const [variants, setVariants] = useState<CaptionVariant[]>([]);
  const [loading, setLoading] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const generateCaptions = async () => {
    setLoading(true);
    try {
      // Call backend endpoint to generate restaurant-specific captions
      const response = await apiClient.post<{ variants: CaptionVariant[] }>("/content/generate-from-trend", {
        topic,
        location: location || "GLOBAL",
        niche: niche || "restaurant",
        business_type: "restaurant",
        count: 3,
      });

      setVariants(response.variants || []);
    } catch (error: any) {
      console.error("Failed to generate captions:", error);
      toast.error("Failed to generate captions", {
        description: error?.message || "Please try again",
      });
      
      // Fallback to mock data for now (remove when backend is ready)
      setVariants([
        {
          caption: `Craving ${topic}? We've got you covered! 😋 Fresh, delicious, and made with love. Come taste the difference today!`,
          hashtags: ["#" + topic.replace(/\s+/g, ""), "#FoodLovers", "#LocalEats", "#Delicious", "#FoodieLife"],
        },
        {
          caption: `${topic} season is here! 🎉 Don't miss out on our special menu featuring the best ${topic} in town. Your taste buds will thank you!`,
          hashtags: ["#" + topic.replace(/\s+/g, ""), "#FoodPorn", "#Yummy", "#MustTry", "#LocalFood"],
        },
        {
          caption: `What makes our ${topic} special? Fresh ingredients, authentic recipes, and a whole lot of passion. Visit us today! ✨`,
          hashtags: ["#" + topic.replace(/\s+/g, ""), "#Foodie", "#Restaurant", "#TasteTheGoodness", "#FreshFood"],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async (index: number) => {
    const variant = variants[index];
    const fullText = `${variant.caption}\n\n${variant.hashtags.join(" ")}`;
    
    try {
      await navigator.clipboard.writeText(fullText);
      setCopiedIndex(index);
      toast.success("Copied to clipboard!", {
        description: "Paste it into your social media post",
      });
      
      setTimeout(() => setCopiedIndex(null), 2000);
    } catch (error) {
      toast.error("Failed to copy", {
        description: "Please try again",
      });
    }
  };

  // Generate captions when dialog opens
  useEffect(() => {
    if (open && variants.length === 0) {
      generateCaptions();
    }
  }, [open]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold">Create Post About "{topic}"</DialogTitle>
          <DialogDescription>
            Choose a caption variant and copy it to your clipboard. Each includes hashtags optimized for reach.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 mt-4">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-12 space-y-3">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
              <p className="text-sm text-muted-foreground">Generating captions...</p>
            </div>
          ) : variants.length > 0 ? (
            variants.map((variant, index) => (
              <div
                key={index}
                className="p-4 rounded-xl border border-border bg-card/50 hover:bg-card/70 transition-colors space-y-3"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 space-y-2">
                    <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                      Variant {index + 1}
                    </div>
                    <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">
                      {variant.caption}
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {variant.hashtags.map((tag, tagIndex) => (
                        <span
                          key={tagIndex}
                          className="text-xs px-2 py-1 rounded-md bg-primary/10 text-primary font-mono"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleCopy(index)}
                    className="shrink-0"
                  >
                    {copiedIndex === index ? (
                      <>
                        <Check className="w-4 h-4 mr-1" />
                        Copied
                      </>
                    ) : (
                      <>
                        <Copy className="w-4 h-4 mr-1" />
                        Copy
                      </>
                    )}
                  </Button>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <p>No captions generated yet.</p>
              <Button onClick={generateCaptions} className="mt-4">
                Generate Captions
              </Button>
            </div>
          )}
        </div>

        <div className="flex justify-end gap-2 mt-6 pt-4 border-t border-border">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
          {variants.length > 0 && (
            <Button onClick={generateCaptions} disabled={loading}>
              Regenerate
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};
