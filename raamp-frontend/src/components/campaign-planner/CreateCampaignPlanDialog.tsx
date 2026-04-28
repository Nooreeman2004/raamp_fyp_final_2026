import { useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { campaignPlannerService } from "@/services/campaignPlannerService";


const DEFAULT_TZ = "UTC";

export function CreateCampaignPlanDialog({
  open,
  onOpenChange,
  onCreated,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  onCreated: () => void;
}) {
  const submitLockRef = useRef(false);
  const [idea, setIdea] = useState("");
  const [objective, setObjective] = useState<"awareness" | "engagement" | "foot_traffic" | "sales" | "leads">("engagement");
  const [budgetMin, setBudgetMin] = useState<string>("");
  const [budgetMax, setBudgetMax] = useState<string>("");
  const [startDate, setStartDate] = useState<string>("");
  const [endDate, setEndDate] = useState<string>("");
  const [timezone, setTimezone] = useState<string>(DEFAULT_TZ);
  const [frequency, setFrequency] = useState<"daily" | "3_per_week" | "5_per_week" | "custom">("3_per_week");
  const [platform, setPlatform] = useState<"instagram" | "facebook" | "both">("instagram");
  const [targetAudience, setTargetAudience] = useState("");
  const [offerOrCta, setOfferOrCta] = useState("");
  const [constraints, setConstraints] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const canSubmit = useMemo(() => {
    return idea.trim().length >= 10 && !!startDate && !!endDate && !!timezone.trim();
  }, [idea, startDate, endDate, timezone]);

  // When the dialog reopens, clear any stale lock/submitting state from the
  // previous session (Dialog keeps children mounted even when closed).
  useEffect(() => {
    if (open) {
      submitLockRef.current = false;
      setSubmitting(false);
    }
  }, [open]);

  const validateForm = (): string | null => {
    if (idea.trim().length < 10) return "Campaign idea must be at least 10 characters.";
    if (!startDate || !endDate) return "Start and end dates are required.";

    const start = new Date(startDate);
    const end = new Date(endDate);
    if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
      return "Please provide valid start/end dates.";
    }
    if (end < start) return "End date must be after start date.";

    const min = budgetMin ? Number(budgetMin) : null;
    const max = budgetMax ? Number(budgetMax) : null;
    if (min !== null && Number.isNaN(min)) return "Budget min must be a valid number.";
    if (max !== null && Number.isNaN(max)) return "Budget max must be a valid number.";
    if (min !== null && min < 0) return "Budget min cannot be negative.";
    if (max !== null && max < 0) return "Budget max cannot be negative.";
    if (min !== null && max !== null && min > max) return "Budget min cannot exceed budget max.";

    if (!timezone.trim()) return "Timezone is required.";
    return null;
  };

  const submit = async () => {
    // Hard lock to prevent same-frame double clicks (state updates are async).
    if (submitLockRef.current) return;
    submitLockRef.current = true;
    if (!canSubmit) {
      toast.error("Missing required fields", { description: "Add a campaign idea + start/end dates to generate a plan." });
      submitLockRef.current = false;
      return;
    }
    const validationError = validateForm();
    if (validationError) {
      toast.error("Invalid form data", { description: validationError });
      submitLockRef.current = false;
      return;
    }
    try {
      setSubmitting(true);
      const toastId = toast.loading("Generating plan…", {
        description: "This can take 15–20 seconds. Please don't refresh.",
      });
      const payload = {
        idea: idea.trim(),
        objective,
        budget_min: budgetMin ? Math.round(Number(budgetMin)) : null,
        budget_max: budgetMax ? Math.round(Number(budgetMax)) : null,
        start_date: new Date(startDate).toISOString(),
        end_date: new Date(endDate).toISOString(),
        timezone: timezone || DEFAULT_TZ,
        posting_frequency: frequency,
        platforms: [platform],
        target_audience: targetAudience.trim() || null,
        offer_or_cta: offerOrCta.trim() || null,
        constraints: constraints.trim() || null,
        reference_media_url: null,
      } as const;

      console.log("🚀 Creating campaign plan:", {
        idea_length: idea.trim().length,
        objective,
        date_range: `${startDate} → ${endDate}`,
        frequency,
        platform,
        timestamp: new Date().toISOString()
      });

      const res = await campaignPlannerService.createPlan(payload as any);
      
      console.log("✅ Campaign plan created:", {
        plan_id: res.plan_id,
        generation_status: res.generation_status,
        timestamp: new Date().toISOString()
      });

      toast.success("Campaign plan generated", { id: toastId, description: `Status: ${res.generation_status}` });
      onCreated();
      onOpenChange(false);
      // Do NOT reset the lock here — the dialog is closing.
      // submitLockRef stays true until the dialog reopens (see useEffect above).
      // This prevents any re-render between onOpenChange(false) and unmount from
      // briefly re-enabling the button and allowing a duplicate submission.
    } catch (e: any) {
      console.error("❌ Campaign plan generation failed:", {
        error: e,
        message: e?.message || String(e),
        response: e?.response,
        status: e?.status,
        stack: e?.stack,
        timestamp: new Date().toISOString()
      });

      const msg = String(e?.message || "");
      const isOffline =
        msg.toLowerCase().includes("failed to fetch") ||
        msg.toLowerCase().includes("network") ||
        msg.toLowerCase().includes("econnrefused");
      toast.error("Failed to generate plan", {
        description: isOffline
          ? "Can't reach the server right now. Start the backend (port 8000) and try again."
          : msg || "Check console for details.",
        duration: 10000
      });
      // Only reset lock on failure so the user can retry.
      setSubmitting(false);
      submitLockRef.current = false;
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      {/* flex-col + no overflow on the root so header/footer stay pinned */}
      <DialogContent className="border border-border/50 text-foreground w-[calc(100vw-2rem)] max-w-2xl rounded-2xl max-h-[85vh] flex flex-col p-0 gap-0 overflow-hidden">
        {/* ── Sticky header (includes the built-in × close button) ── */}
        <DialogHeader className="px-6 pt-6 pb-4 border-b border-border/50 shrink-0">
          <DialogTitle className="font-heading font-semibold text-xl tracking-wide">Create Brand-Driven Campaign Plan</DialogTitle>
          <DialogDescription className="text-muted-foreground text-sm font-medium">
            This planner uses your Brand Settings + Specialties to build a posting calendar. It does not rely on trends.
          </DialogDescription>
        </DialogHeader>

        {/* ── Scrollable body ── */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 min-w-0">
          <Card className="p-4 bg-card/40 border-border/50 space-y-3">
            <div className="space-y-2">
              <Label className="text-xs font-mono font-medium text-muted-foreground uppercase tracking-widest">Campaign idea <span className="text-red-500">*</span></Label>
              <Textarea
                value={idea}
                onChange={(e) => setIdea(e.target.value)}
                rows={5}
                placeholder="e.g. Eid dinner specials + family bundles with a warm premium tone..."
                className="bg-foreground/5 border-border/50 resize-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label className="text-xs font-mono font-medium text-muted-foreground uppercase tracking-widest">Objective <span className="text-red-500">*</span></Label>
                <Select value={objective} onValueChange={(v) => setObjective(v as any)}>
                  <SelectTrigger className="bg-foreground/5 border-border/50 w-full min-w-0">
                    <SelectValue placeholder="Objective" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="engagement">Engagement</SelectItem>
                    <SelectItem value="foot_traffic">Foot traffic</SelectItem>
                    <SelectItem value="sales">Sales</SelectItem>
                    <SelectItem value="leads">Leads</SelectItem>
                    <SelectItem value="awareness">Awareness</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label className="text-xs font-mono font-medium text-muted-foreground uppercase tracking-widest">Platform <span className="text-red-500">*</span></Label>
                <Select value={platform} onValueChange={(v) => setPlatform(v as any)}>
                  <SelectTrigger className="bg-foreground/5 border-border/50 w-full min-w-0">
                    <SelectValue placeholder="Platform" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="instagram">Instagram</SelectItem>
                    <SelectItem value="facebook">Facebook</SelectItem>
                    <SelectItem value="both">Both</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </Card>

          <Card className="p-4 bg-card/40 border-border/50 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label className="text-xs font-mono font-medium text-muted-foreground uppercase tracking-widest">Start <span className="text-red-500">*</span></Label>
                <div className="relative">
                  <Input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="bg-foreground/5 border-border/50 w-full min-w-0 dark:[color-scheme:dark] focus-visible:ring-2 focus-visible:ring-primary/30 focus-visible:ring-offset-0"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label className="text-xs font-mono font-medium text-muted-foreground uppercase tracking-widest">End <span className="text-red-500">*</span></Label>
                <div className="relative">
                  <Input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="bg-foreground/5 border-border/50 w-full min-w-0 dark:[color-scheme:dark] focus-visible:ring-2 focus-visible:ring-primary/30 focus-visible:ring-offset-0"
                  />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label className="text-xs font-mono font-medium text-muted-foreground uppercase tracking-widest">Timezone <span className="text-red-500">*</span></Label>
                <Input value={timezone} onChange={(e) => setTimezone(e.target.value)} placeholder="UTC / Asia/Karachi" className="bg-foreground/5 border-border/50 w-full min-w-0" />
              </div>
              <div className="space-y-2">
                <Label className="text-xs font-mono font-medium text-muted-foreground uppercase tracking-widest">Frequency <span className="text-red-500">*</span></Label>
                <Select value={frequency} onValueChange={(v) => setFrequency(v as any)}>
                  <SelectTrigger className="bg-foreground/5 border-border/50 w-full min-w-0">
                    <SelectValue placeholder="Frequency" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="3_per_week">3 / week</SelectItem>
                    <SelectItem value="5_per_week">5 / week</SelectItem>
                    <SelectItem value="daily">Daily</SelectItem>
                    <SelectItem value="custom">Custom</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label className="text-xs font-mono font-medium text-muted-foreground uppercase tracking-widest">Budget min (optional)</Label>
                <Input type="number" min={0} value={budgetMin} onChange={(e) => setBudgetMin(e.target.value)} placeholder="0" className="bg-foreground/5 border-border/50 w-full min-w-0" />
              </div>
              <div className="space-y-2">
                <Label className="text-xs font-mono font-medium text-muted-foreground uppercase tracking-widest">Budget max (optional)</Label>
                <Input type="number" min={0} value={budgetMax} onChange={(e) => setBudgetMax(e.target.value)} placeholder="0" className="bg-foreground/5 border-border/50 w-full min-w-0" />
              </div>
            </div>
          </Card>
        </div>

        <Card className="p-4 bg-card/30 border-border/50">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label className="text-xs font-mono font-medium text-muted-foreground uppercase tracking-widest">Target audience (optional)</Label>
              <Input value={targetAudience} onChange={(e) => setTargetAudience(e.target.value)} placeholder="e.g. families in Islamabad" className="bg-foreground/5 border-border/50 w-full min-w-0" />
            </div>
            <div className="space-y-2">
              <Label className="text-xs font-mono font-medium text-muted-foreground uppercase tracking-widest">Offer / CTA (optional)</Label>
              <Input value={offerOrCta} onChange={(e) => setOfferOrCta(e.target.value)} placeholder="e.g. 15% off family platter" className="bg-foreground/5 border-border/50 w-full min-w-0" />
            </div>
            <div className="space-y-2">
              <Label className="text-xs font-mono font-medium text-muted-foreground uppercase tracking-widest">Constraints (optional)</Label>
              <Input value={constraints} onChange={(e) => setConstraints(e.target.value)} placeholder="Do not mention alcohol, keep it premium…" className="bg-foreground/5 border-border/50 w-full min-w-0" />
            </div>
          </div>
        </Card>

        </div>{/* ── end scrollable body ── */}

        {/* ── Sticky footer ── always visible */}
        <div className="flex gap-2 px-6 py-4 border-t border-border/50 bg-background/80 backdrop-blur-sm shrink-0">
          <Button variant="outline" className="flex-1 border-border/50" onClick={() => onOpenChange(false)} disabled={submitting}>
            Cancel
          </Button>
          <Button className="flex-1 bg-primary text-black font-semibold" onClick={submit} disabled={submitting || !canSubmit}>
            {submitting ? "Generating..." : "Generate plan"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

