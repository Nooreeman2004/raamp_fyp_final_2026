import Layout from "@/components/Layout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { MessageSquare, Save, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { BlurText } from "@/components/ui/text-reveal";
import { autoReplyService } from "@/services/autoReplyService";

type Mode = "review_only" | "hybrid_auto";

export default function AutoReplySettings() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [instagramEnabled, setInstagramEnabled] = useState(false);
  const [instagramMode, setInstagramMode] = useState<Mode>("review_only");
  const [facebookEnabled, setFacebookEnabled] = useState(false);
  const [facebookMode, setFacebookMode] = useState<Mode>("review_only");

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const s = await autoReplyService.getSettings();
      setInstagramEnabled(Boolean(s.instagram_auto_replies_enabled));
      setInstagramMode((s.instagram_mode as Mode) || "review_only");
      setFacebookEnabled(Boolean(s.facebook_auto_replies_enabled));
      setFacebookMode((s.facebook_mode as Mode) || "review_only");
    } catch (e: any) {
      toast.error("Failed to load auto reply settings", { description: e?.message || "Please try again." });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const save = async () => {
    setSaving(true);
    try {
      await autoReplyService.patchSettings({
        instagram_auto_replies_enabled: instagramEnabled,
        instagram_mode: instagramMode,
        facebook_auto_replies_enabled: facebookEnabled,
        facebook_mode: facebookMode,
      });
      toast.success("Saved", { description: "Auto reply settings updated." });
    } catch (e: any) {
      toast.error("Save failed", { description: e?.message || "Please try again." });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Layout breadcrumbItems={[{ label: "Settings", href: "/settings" }, { label: "Auto Replies" }]}>
      <motion.div
        className="space-y-6 max-w-2xl mx-auto"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Reveal variant="blurInUp">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center">
                <MessageSquare className="w-7 h-7 text-primary" />
              </div>
              <div>
                <h1 className="text-3xl font-bold font-heading font-semibold">
                  <BlurText text="Auto Replies" />
                </h1>
                <p className="text-muted-foreground font-mono text-sm">
                  Safety-first by default. Enable per platform when you’re ready.
                </p>
              </div>
            </div>
          </div>
        </Reveal>

        {loading ? (
          <div className="flex justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : (
          <>
            <Reveal variant="fadeInUp" delay={0.1}>
              <Card className="p-6 bg-card/70 backdrop-blur-sm border-primary/10 space-y-5">
                <div className="flex items-center justify-between">
                  <div>
                    <Label className="font-mono text-sm">Instagram Auto Replies</Label>
                    <p className="text-sm text-muted-foreground font-mono">Enable/disable Instagram comment replies</p>
                  </div>
                  <Switch checked={instagramEnabled} onCheckedChange={setInstagramEnabled} />
                </div>

                <div className="flex items-center justify-between gap-4">
                  <div>
                    <Label className="font-mono text-sm">Instagram Mode</Label>
                    <p className="text-sm text-muted-foreground font-mono">Review-only or hybrid auto</p>
                  </div>
                  <div className="w-[220px]">
                    <Select value={instagramMode} onValueChange={(v) => setInstagramMode(v as Mode)}>
                      <SelectTrigger className="bg-foreground/5 border-border/50">
                        <SelectValue placeholder="Select mode" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="review_only">review_only</SelectItem>
                        <SelectItem value="hybrid_auto">hybrid_auto</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </Card>
            </Reveal>

            <Reveal variant="fadeInUp" delay={0.2}>
              <Card className="p-6 bg-card/70 backdrop-blur-sm border-primary/10 space-y-5">
                <div className="flex items-center justify-between">
                  <div>
                    <Label className="font-mono text-sm">Facebook Auto Replies</Label>
                    <p className="text-sm text-muted-foreground font-mono">Enable/disable Facebook comment replies</p>
                  </div>
                  <Switch checked={facebookEnabled} onCheckedChange={setFacebookEnabled} />
                </div>

                <div className="flex items-center justify-between gap-4">
                  <div>
                    <Label className="font-mono text-sm">Facebook Mode</Label>
                    <p className="text-sm text-muted-foreground font-mono">Review-only or hybrid auto</p>
                  </div>
                  <div className="w-[220px]">
                    <Select value={facebookMode} onValueChange={(v) => setFacebookMode(v as Mode)}>
                      <SelectTrigger className="bg-foreground/5 border-border/50">
                        <SelectValue placeholder="Select mode" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="review_only">review_only</SelectItem>
                        <SelectItem value="hybrid_auto">hybrid_auto</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </Card>
            </Reveal>

            <Reveal variant="fadeInUp" delay={0.3}>
              <div className="flex justify-end gap-3">
                <Button variant="outline" onClick={fetchSettings} className="font-mono text-xs" disabled={saving}>
                  Reload
                </Button>
                <Button onClick={save} className="font-mono text-xs" disabled={saving}>
                  {saving ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Saving
                    </>
                  ) : (
                    <>
                      <Save className="w-4 h-4 mr-2" />
                      Save
                    </>
                  )}
                </Button>
              </div>
            </Reveal>
          </>
        )}
      </motion.div>
    </Layout>
  );
}

