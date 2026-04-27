import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { campaignLaunchService, CampaignLaunchMode, CampaignLaunchPlatform } from "@/services/campaignLaunchService";
import { instagramService } from "@/services/instagramService";

export interface LaunchCampaignPrefill {
  trend_id?: string | null;
  keyword?: string | null;
  niche?: string | null;
  location?: string | null;
  suggested_platforms?: string[] | null;
  hashtags?: string[] | null;
  lifecycle_stage?: string | null;
}

function toHashtag(h: string): string {
  const t = (h || "").trim();
  if (!t) return "";
  return t.startsWith("#") ? t : `#${t.replace(/\s+/g, "")}`;
}

export function LaunchCampaignDialog({
  open,
  onOpenChange,
  prefill,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  prefill?: LaunchCampaignPrefill;
}) {
  const keyword = (prefill?.keyword || "").trim();
  const niche = (prefill?.niche || "").trim();
  const location = (prefill?.location || "").trim();

  const defaultPlatform: CampaignLaunchPlatform = useMemo(() => {
    const plats = (prefill?.suggested_platforms || []).map((p) => (p || "").toLowerCase());
    if (plats.includes("facebook") && plats.includes("instagram")) return "both";
    if (plats.includes("facebook")) return "facebook";
    return "instagram";
  }, [prefill?.suggested_platforms]);

  const [platform, setPlatform] = useState<CampaignLaunchPlatform>("instagram");
  const [mode, setMode] = useState<CampaignLaunchMode>("post_now");
  const [mediaUrl, setMediaUrl] = useState("");
  const [mediaFile, setMediaFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [caption, setCaption] = useState("");
  const [scheduledTime, setScheduledTime] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!open) return;
    setPlatform(defaultPlatform);
    setMode("post_now");
    setMediaUrl("");
    setMediaFile(null);
    setScheduledTime("");

    // Generate a proper caption using the trend keyword
    const generateCaption = async () => {
      if (!keyword) {
        setCaption("");
        return;
      }

      try {
        // Generate an engaging caption using the content generation API
        const response = await fetch("/api/content/generate", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            campaign_idea: `Create engaging content about the trending topic: ${keyword}${niche ? ` in the ${niche} niche` : ""}${location ? ` for ${location}` : ""}`,
            target_audience: niche || "general audience",
            campaign_tone: "engaging",
            platform_type: "post",
            content_type: "captions",
          }),
        });

        if (response.ok) {
          const data = await response.json();
          const firstVariant = data.captions?.[0];
          if (firstVariant?.text) {
            // Use the generated caption with relevant hashtags
            const tags = Array.from(
              new Set(
                (prefill?.hashtags || [])
                  .filter((h): h is string => typeof h === "string")
                  .map((h) => toHashtag(h))
                  .filter(Boolean)
              )
            ).slice(0, 5);
            
            const captionText = firstVariant.text;
            const hashtagText = tags.length ? `\n\n${tags.join(" ")}` : "";
            setCaption(`${captionText}${hashtagText}`);
            return;
          }
        }
      } catch (error) {
        console.error("Failed to generate caption:", error);
      }

      // Fallback: Create a simple engaging caption
      const tags = Array.from(
        new Set(
          (prefill?.hashtags || [])
            .filter((h): h is string => typeof h === "string")
            .map((h) => toHashtag(h))
            .filter(Boolean)
        )
      ).slice(0, 5);

      const fallbackCaption = keyword
        ? `🔥 Trending now: ${keyword}! ${location ? `Perfect for ${location}` : "Don't miss out!"}`
        : "";
      const hashtagText = tags.length ? `\n\n${tags.join(" ")}` : "";
      setCaption(`${fallbackCaption}${hashtagText}`);
    };

    generateCaption();
  }, [open, defaultPlatform, keyword, niche, location, prefill?.hashtags]);

  const uploadAndGetUrl = async (): Promise<string> => {
    if (!mediaFile) {
      throw new Error("No file selected");
    }
    try {
      setUploading(true);
      const res = await instagramService.uploadMedia(mediaFile);
      const url = (res as any)?.public_url || (res as any)?.cloudinary_url || "";
      if (!url) throw new Error("Upload succeeded but no public URL returned");
      setMediaUrl(url);
      return url;
    } catch (e: any) {
      throw e;
    } finally {
      setUploading(false);
    }
  };

  const handleSubmit = async () => {
    let url = mediaUrl.trim();
    if (mode === "schedule_post" && !scheduledTime) {
      toast.error("Scheduled time is required for scheduled posts");
      return;
    }

    try {
      setSubmitting(true);

      // Accept either:
      // - a pasted public URL, OR
      // - a selected file (auto-upload on submit)
      if (!url && mediaFile) {
        try {
          url = await uploadAndGetUrl();
          toast.success("Uploaded", { description: "Media uploaded and attached to this request." });
        } catch (e: any) {
          toast.error("Upload failed", { description: e?.message || "Please try again." });
          return;
        }
      }

      if (!url) {
        toast.error("Media is required (upload a file or paste a URL)");
        return;
      }
      if (!url.startsWith("https://")) {
        toast.error("Media URL must be a public HTTPS URL");
        return;
      }

      const scheduledIso =
        mode === "schedule_post" && scheduledTime
          ? new Date(scheduledTime).toISOString()
          : null;

      const res = await campaignLaunchService.createRequest({
        platform,
        mode,
        media_url: url,
        caption: caption.trim() || null,
        scheduled_time: scheduledIso,
        trend_keyword: keyword || null,
        trend_signal_id: (prefill?.trend_id || null) as any,
      });

      toast.success("Launch request created", {
        description: res.message || "Approval required to execute.",
      });
      onOpenChange(false);
    } catch (e: any) {
      toast.error("Failed to create launch request", {
        description: e?.message || "Please try again.",
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="border border-border/50 text-foreground max-w-lg rounded-2xl">
        <DialogHeader>
          <DialogTitle className="font-heading font-semibold text-xl tracking-wide">
            Launch Campaign
          </DialogTitle>
          <DialogDescription className="text-muted-foreground/70 text-sm">
            Create an approval-gated launch request for this trend.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 pt-2">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <div className="text-[10px] font-mono text-muted-foreground/70 uppercase tracking-widest">
                Platform
              </div>
              <Select value={platform} onValueChange={(v) => setPlatform(v as CampaignLaunchPlatform)}>
                <SelectTrigger className="bg-foreground/5 border-border/50">
                  <SelectValue placeholder="Select platform" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="instagram">Instagram</SelectItem>
                  <SelectItem value="facebook">Facebook</SelectItem>
                  <SelectItem value="both">Both</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <div className="text-[10px] font-mono text-muted-foreground/70 uppercase tracking-widest">
                Mode
              </div>
              <Select value={mode} onValueChange={(v) => setMode(v as CampaignLaunchMode)}>
                <SelectTrigger className="bg-foreground/5 border-border/50">
                  <SelectValue placeholder="Select mode" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="post_now">Post now</SelectItem>
                  <SelectItem value="schedule_post">Schedule post</SelectItem>
                  <SelectItem value="post_story">Post story</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <div className="text-[10px] font-mono text-muted-foreground/70 uppercase tracking-widest">
              Media (upload or public HTTPS URL)
            </div>
            <div className="flex flex-col gap-2">
              <Input
                type="file"
                accept="image/*,video/*"
                onChange={(e) => {
                  const f = e.target.files?.[0] || null;
                  setMediaFile(f);
                }}
                className="bg-foreground/5 border-border/50"
              />
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  className="border-border/50"
                  onClick={async () => {
                    if (!mediaFile) {
                      toast.error("Select an image or video to upload");
                      return;
                    }
                    try {
                      const u = await uploadAndGetUrl();
                      toast.success("Uploaded", { description: "Media uploaded and attached to this request." });
                      if (u) setMediaUrl(u);
                    } catch (e: any) {
                      toast.error("Upload failed", { description: e?.message || "Please try again." });
                    }
                  }}
                  disabled={uploading || !mediaFile}
                >
                  {uploading ? "Uploading..." : "Upload"}
                </Button>
                <div className="text-[10px] font-mono text-muted-foreground/60 flex items-center">
                  {mediaFile ? mediaFile.name : "No file selected"}
                </div>
              </div>
            </div>
            <Input
              value={mediaUrl}
              onChange={(e) => setMediaUrl(e.target.value)}
              placeholder="https://...jpg / ...mp4"
              className="bg-foreground/5 border-border/50"
            />
            {!!mediaUrl && (
              <div className="text-[10px] font-mono text-muted-foreground/60 break-all">
                Attached: {mediaUrl}
              </div>
            )}
          </div>

          {mode === "schedule_post" && (
            <div className="space-y-2">
              <div className="text-[10px] font-mono text-muted-foreground/70 uppercase tracking-widest">
                Scheduled time
              </div>
              <Input
                type="datetime-local"
                value={scheduledTime}
                onChange={(e) => setScheduledTime(e.target.value)}
                className="bg-foreground/5 border-border/50"
              />
            </div>
          )}

          <div className="space-y-2">
            <div className="text-[10px] font-mono text-muted-foreground/70 uppercase tracking-widest">
              Caption (optional)
            </div>
            <textarea
              value={caption}
              onChange={(e) => setCaption(e.target.value)}
              rows={4}
              className="w-full bg-foreground/5 border border-border/50 rounded-md p-3 text-sm resize-none focus:outline-none focus:border-primary/50"
            />
          </div>

          <div className="flex gap-2 pt-2">
            <Button
              variant="outline"
              className="flex-1 border-border/50"
              onClick={() => onOpenChange(false)}
              disabled={submitting || uploading}
            >
              Cancel
            </Button>
            <Button className="flex-1" onClick={handleSubmit} disabled={submitting || uploading}>
              {submitting ? "Submitting..." : "Request approval"}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

