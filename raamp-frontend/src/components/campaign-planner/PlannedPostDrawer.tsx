import { useMemo, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { campaignPlannerService, PlannedPostItem } from "@/services/campaignPlannerService";

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

  const canRequestApproval = useMemo(() => {
    const u = mediaUrl.trim();
    return u.startsWith("https://");
  }, [mediaUrl]);

  if (!item) return null;

  const convertToDraft = async () => {
    try {
      setSubmitting(true);
      const res = await (await fetch(`/api/campaign-planner/planned-posts/${item.id}/convert-to-draft`, { method: "POST" })).json();
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
      const url = new URL(`/api/campaign-planner/planned-posts/${item.id}/request-approval`, window.location.origin);
      url.searchParams.set("mode", mode);
      url.searchParams.set("platform", platform);
      url.searchParams.set("media_url", mediaUrl.trim());
      const res = await fetch(url.toString(), { method: "POST" }).then((r) => r.json());
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
      <DialogContent className="border border-border/50 text-foreground max-w-2xl rounded-2xl">
        <DialogHeader>
          <DialogTitle className="font-heading font-semibold text-xl tracking-wide">{item.title}</DialogTitle>
          <DialogDescription className="text-muted-foreground/70 text-sm">
            Planned for {new Date(item.scheduled_time).toLocaleString()} ({timezone}) · Status: {item.status}
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
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

          <Card className="p-4 bg-card/40 border-border/50 space-y-3">
            <div className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest">Actions</div>

            <div className="flex gap-2">
              <Button variant="outline" className="flex-1 border-border/50" onClick={convertToDraft} disabled={submitting}>
                Convert to Draft
              </Button>
              <Button variant="outline" className="flex-1 border-border/50" onClick={onUpdated} disabled={submitting}>
                Refresh
              </Button>
            </div>

            <div className="pt-2 space-y-2">
              <Label className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest">Media URL (required for approval)</Label>
              <Input value={mediaUrl} onChange={(e) => setMediaUrl(e.target.value)} placeholder="https://...jpg / ...mp4" className="bg-foreground/5 border-border/50" />
            </div>

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

            <Button className="w-full bg-primary text-black" onClick={requestApproval} disabled={submitting || !canRequestApproval}>
              {submitting ? "Submitting..." : "Request approval (Planner)"}
            </Button>
          </Card>
        </div>
      </DialogContent>
    </Dialog>
  );
}

