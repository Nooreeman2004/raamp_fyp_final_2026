import { useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { campaignPlannerService, PlannedPostItem } from "@/services/campaignPlannerService";
import { assetService, Asset } from "@/services/assetService";
import { Upload, Library, Link2, X, CheckCircle2, Loader2, ImageIcon } from "lucide-react";

// ─── helpers ────────────────────────────────────────────────────────────────

import { API_ORIGIN } from "@/config/apiUtils";
// API_ORIGIN resolves to the backend origin from the centralized config (no hardcoded localhost)
const getAuthToken = () => localStorage.getItem("token") || sessionStorage.getItem("token");

import { MediaPicker } from "@/components/shared/MediaPicker";
import { CommentIntelligenceGrid } from "./CommentIntelligenceGrid";

// ─── main component ──────────────────────────────────────────────────────────

export function PlannedPostDrawer({
  open,
  onOpenChange,
  item,
  timezone,
  onUpdated,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  item: PlannedPostItem | null;
  timezone: string;
  onUpdated: () => void;
}) {
  const [submitting, setSubmitting] = useState(false);
  const [generatingImage, setGeneratingImage] = useState(false);
  const [mediaUrl, setMediaUrl] = useState("");
  const [mode, setMode] = useState<"post_now" | "schedule_post" | "post_story">("schedule_post");
  const [platform, setPlatform] = useState<"instagram" | "facebook" | "both">("instagram");

  // Reset when dialog closes
  useEffect(() => {
    if (!open) {
      setMediaUrl("");
    }
  }, [open]);

  const canRequestApproval = useMemo(() => {
    const u = mediaUrl.trim();
    return u.startsWith("https://") || u.startsWith("http://");
  }, [mediaUrl]);

  if (!item) return null;

  const convertToDraft = async () => {
    try {
      setSubmitting(true);
      const res = await campaignPlannerService.convertToDraft(item.id);
      if (!res?.success) throw new Error("Convert to draft failed");
      toast.success("Draft created", { description: `Draft ID: ${res.draft_id}` });
      onUpdated();
    } catch (e: any) {
      toast.error("Failed to convert", { description: e?.message || "Please try again." });
    } finally {
      setSubmitting(false);
    }
  };

  const requestApproval = async () => {
    if (!canRequestApproval) return;
    try {
      setSubmitting(true);
      const res = await campaignPlannerService.requestApproval(item.id, {
        mode,
        platform,
        media_url: mediaUrl.trim(),
      });
      if (!res?.success) throw new Error("Request approval failed");
      toast.success("Approval requested", { description: `Request ID: ${res.request_id}` });
      onUpdated();
    } catch (e: any) {
      toast.error("Failed to request approval", { description: e?.message || "Please try again." });
    } finally {
      setSubmitting(false);
    }
  };

  const generateImage = async () => {
    const creativePrompt = (item?.prompts as any)?.creative_prompt;
    if (!creativePrompt) {
      toast.error("No image prompt", { description: "This post doesn't have a creative prompt." });
      return;
    }

    try {
      setGeneratingImage(true);
      toast.info("Generating image...", {
        description: "AI is creating your image. This takes ~15-20 seconds.",
        duration: 20000,
      });

      const res = await campaignPlannerService.generateImage(item.id, creativePrompt);

      if (!res?.success || !res.image_url) {
        throw new Error(res?.error || "Image generation failed");
      }

      // Auto-populate media URL
      setMediaUrl(res.image_url);
      toast.success("Image generated!", {
        description: "Image is ready and loaded. You can now request approval.",
      });
    } catch (e: any) {
      toast.error("Image generation failed", {
        description: e?.message || "Please try again or upload manually.",
      });
    } finally {
      setGeneratingImage(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="border border-border/50 text-foreground max-w-2xl rounded-2xl max-h-[85vh] flex flex-col p-0 gap-0 overflow-hidden">
        {/* Sticky header */}
        <DialogHeader className="px-6 pt-6 pb-4 border-b border-border/50 shrink-0">
          <DialogTitle className="font-heading font-semibold text-xl tracking-wide">{item.title}</DialogTitle>
          <DialogDescription className="text-muted-foreground/70 text-sm">
            Planned for {new Date(item.scheduled_time).toLocaleString()} ({timezone}) · Status: {item.status}
          </DialogDescription>
        </DialogHeader>

        {/* Scrollable body */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Left — Caption & Creative Prompt */}
            <Card className="p-4 bg-card/40 border-border/50 space-y-3">
              <div className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest">Content</div>
              
              {/* Caption (actual usable text) */}
              <div className="space-y-2">
                <div className="text-[10px] font-mono text-muted-foreground/70 uppercase tracking-widest">Caption</div>
                <div className="text-[11px] font-mono text-muted-foreground/80 whitespace-pre-wrap bg-background/50 p-3 rounded border border-border/30">
                  {item.caption || "No caption generated"}
                </div>
              </div>

              {/* Creative Prompt (for image generation) */}
              <div className="space-y-2">
                <div className="text-[10px] font-mono text-muted-foreground/70 uppercase tracking-widest">Image Prompt</div>
                <div className="text-[11px] font-mono text-muted-foreground/80 whitespace-pre-wrap">
                  {(item.prompts as any)?.creative_prompt || "—"}
                </div>
                {(item.prompts as any)?.creative_prompt && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full mt-2 border-primary/30 hover:bg-primary/10"
                    onClick={generateImage}
                    disabled={generatingImage || submitting}
                  >
                    {generatingImage ? (
                      <>
                        <Loader2 className="w-3 h-3 mr-2 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <ImageIcon className="w-3 h-3 mr-2" />
                        Generate Image
                      </>
                    )}
                  </Button>
                )}
              </div>

              {/* CTA & Hashtags */}
              {item.cta && (
                <div className="space-y-2">
                  <div className="text-[10px] font-mono text-muted-foreground/70 uppercase tracking-widest">Call to Action</div>
                  <div className="text-[11px] font-mono text-muted-foreground/80">{item.cta}</div>
                </div>
              )}
              {item.hashtags && item.hashtags.length > 0 && (
                <div className="space-y-2">
                  <div className="text-[10px] font-mono text-muted-foreground/70 uppercase tracking-widest">Hashtags</div>
                  <div className="text-[11px] font-mono text-muted-foreground/80 flex flex-wrap gap-1">
                    {item.hashtags.map((tag, idx) => (
                      <span key={idx} className="text-primary">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </Card>

            {/* Right — Actions */}
            <Card className="p-4 bg-card/40 border-border/50 space-y-4">
              <div className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest">Actions</div>

              {/* Convert to Draft (single button, no useless Refresh) */}
              <Button
                variant="outline"
                className="w-full border-border/50"
                onClick={convertToDraft}
                disabled={submitting}
              >
                Convert to Draft
              </Button>

              {/* ── Media Picker ── */}
              <div className="space-y-2">
                <Label className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest">
                  Media (required for approval)
                </Label>
                <MediaPicker value={mediaUrl} onChange={setMediaUrl} />
              </div>

              {/* Platform + Mode */}
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest">Platform</Label>
                  <Select value={platform} onValueChange={(v) => setPlatform(v as any)}>
                    <SelectTrigger className="bg-foreground/5 border-border/50">
                      <SelectValue placeholder="Platform" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="instagram">Instagram</SelectItem>
                      <SelectItem value="facebook">Facebook</SelectItem>
                      <SelectItem value="both">Both</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest">Mode</Label>
                  <Select value={mode} onValueChange={(v) => setMode(v as any)}>
                    <SelectTrigger className="bg-foreground/5 border-border/50">
                      <SelectValue placeholder="Mode" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="schedule_post">Schedule post</SelectItem>
                      <SelectItem value="post_now">Post now</SelectItem>
                      <SelectItem value="post_story">Post story</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </Card>
          </div>

          {/* Social Analysis Section - Only for Published Posts */}
          {item.published_post_id && (
            <div className="mt-8 pt-8 border-t border-border/50 space-y-4">
              <div className="flex flex-col gap-1">
                <h3 className="text-sm font-semibold tracking-wide flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-primary" />
                  Post Analysis
                </h3>
                <p className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest">
                  Live metrics from {item.published_post_id}
                </p>
              </div>
              <CommentIntelligenceGrid postId={item.published_post_id} />
            </div>
          )}
        </div>

        {/* Sticky footer */}
        <div className="px-6 py-4 border-t border-border/50 bg-background/80 backdrop-blur-sm shrink-0">
          <Button
            className="w-full bg-primary text-black font-semibold"
            onClick={requestApproval}
            disabled={submitting || !canRequestApproval}
          >
            {submitting ? "Submitting…" : "Request approval (Planner)"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
