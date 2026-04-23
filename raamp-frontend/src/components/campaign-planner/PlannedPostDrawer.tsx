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

const API_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/api\/?$/, "");
const getAuthToken = () => localStorage.getItem("token") || sessionStorage.getItem("token");

import { MediaPicker } from "@/components/shared/MediaPicker";

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
      if (!res?.success) throw new Error(res?.detail || "Request approval failed");
      toast.success("Approval requested", { description: `Request ID: ${res.request_id}` });
      onUpdated();
    } catch (e: any) {
      toast.error("Failed to request approval", { description: e?.message || "Please try again." });
    } finally {
      setSubmitting(false);
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
            {/* Left — Prompts */}
            <Card className="p-4 bg-card/40 border-border/50 space-y-3">
              <div className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest">Prompts</div>
              <div className="space-y-2">
                <div className="text-[10px] font-mono text-muted-foreground/70 uppercase tracking-widest">Caption prompt</div>
                <div className="text-[11px] font-mono text-muted-foreground/80 whitespace-pre-wrap">
                  {(item.prompts as any)?.caption_prompt || "—"}
                </div>
              </div>
              <div className="space-y-2">
                <div className="text-[10px] font-mono text-muted-foreground/70 uppercase tracking-widest">Creative prompt</div>
                <div className="text-[11px] font-mono text-muted-foreground/80 whitespace-pre-wrap">
                  {(item.prompts as any)?.creative_prompt || "—"}
                </div>
              </div>
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
