import { useEffect, useMemo, useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { apiClient } from "@/services/api";
import { toast } from "sonner";
import { Loader2, ExternalLink, CheckCircle2, AlertTriangle } from "lucide-react";
import { getErrorMessage } from "@/utils/errorHandler";

interface AdAccount {
  id: string;
  name?: string | null;
  currency?: string | null;
  account_status?: number | null;
}

export interface FBPage {
  id: string;
  name?: string | null;
}

export interface MetaZone {
  label: string;
  latitude: number;
  longitude: number;
  score: number;
  urgency?: string;
}

export interface MetaBrief {
  caption_variants?: { aggressive?: string; soft?: string; urgency?: string };
  suggested_budget_min?: number;
  suggested_budget_max?: number;
  meta_objective?: string;
}

interface Props {
  zone: MetaZone;
  brief: MetaBrief | null;
  pageId: string | null;
  fbPages?: FBPage[];
  radiusMeters: number;
  onClose: () => void;
}

export default function MetaDeployModal({ zone, brief, pageId, fbPages = [], radiusMeters, onClose }: Props) {
  const [open, setOpen] = useState(true);
  const [adAccounts, setAdAccounts] = useState<AdAccount[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<string>("");
  const [selectedCaption, setSelectedCaption] = useState<"aggressive" | "soft" | "urgency">("soft");
  const [budget, setBudget] = useState<string>("1000"); // cents
  const [loading, setLoading] = useState(false);
  const [successUrl, setSuccessUrl] = useState("");
  const [selectedPageId, setSelectedPageId] = useState<string>(pageId || "");

  const captions = useMemo(() => {
    const v = brief?.caption_variants || {};
    return {
      aggressive: String(v.aggressive || "").trim(),
      soft: String(v.soft || "").trim(),
      urgency: String(v.urgency || "").trim(),
    };
  }, [brief]);

  const canDeploy = Boolean(
    selectedAccount &&
      selectedPageId &&
      brief &&
      (captions.aggressive || captions.soft || captions.urgency) &&
      !loading
  );

  useEffect(() => {
    setSelectedPageId(pageId || "");
  }, [pageId]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const d = await apiClient.get<{ ad_accounts: AdAccount[]; selected_ad_account_id?: string | null }>(
          "/profile/connections/facebook/ad-accounts"
        );
        if (cancelled) return;
        const list = Array.isArray(d?.ad_accounts) ? d.ad_accounts : [];
        setAdAccounts(list);
        if (d?.selected_ad_account_id) setSelectedAccount(d.selected_ad_account_id);
        else if (list.length === 1) setSelectedAccount(list[0].id);
      } catch {
        // silent: show empty state below
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleAccountChange = async (id: string) => {
    setSelectedAccount(id);
    try {
      await apiClient.post<{ ok: boolean }>("/profile/connections/facebook/ad-accounts/select", { ad_account_id: id });
    } catch {
      // non-blocking
    }
  };

  const budgetHint = useMemo(() => {
    const min = brief?.suggested_budget_min;
    const max = brief?.suggested_budget_max;
    if (typeof min === "number" && typeof max === "number" && min > 0 && max > 0) {
      return `RAAMP suggestion: ${min}–${max}`;
    }
    return "RAAMP suggestion: based on local intent + radius";
  }, [brief?.suggested_budget_min, brief?.suggested_budget_max]);

  async function handleDeploy() {
    if (!brief) return;
    setLoading(true);
    try {
      const obj = brief?.meta_objective || "OUTCOME_TRAFFIC";
      const caption =
        captions[selectedCaption] ||
        captions.soft ||
        captions.aggressive ||
        captions.urgency ||
        "";

      if (!caption.trim()) {
        toast.error("Caption is missing. Generate a brief first.");
        return;
      }

      const resp = await apiClient.post<{ ads_manager_url: string }>(
        "/v1/meta/deploy-draft",
        {
          ad_account_id: selectedAccount,
          campaign_name: `RAAMP – Zone ${zone.label} – ${new Date().toLocaleDateString()}`,
          objective: obj,
          daily_budget: parseInt(budget || "0", 10),
          caption,
          latitude: zone.latitude,
          longitude: zone.longitude,
          radius_meters: radiusMeters,
          page_id: selectedPageId,
        }
      );
      setSuccessUrl(resp?.ads_manager_url || "");
    } catch (e: any) {
      toast.error("Could not create draft", {
        description: getErrorMessage(e),
      });
    } finally {
      setLoading(false);
    }
  }

  if (successUrl) {
    return (
      <Dialog
        open={open}
        onOpenChange={(v) => {
          setOpen(v);
          if (!v) onClose();
        }}
      >
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-primary" />
              Draft created (paused)
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Your ad was created as <strong>Paused</strong>. Review it in Meta Ads Manager before publishing.
            </p>
            <Button asChild className="w-full">
              <a href={successUrl} target="_blank" rel="noreferrer">
                Open Ads Manager
                <ExternalLink className="w-4 h-4 ml-2" />
              </a>
            </Button>
            <Button variant="outline" className="w-full" onClick={onClose}>
              Close
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(v) => {
        setOpen(v);
        if (!v) onClose();
      }}
    >
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between gap-3">
            <span>Deploy to Meta Ads</span>
            <Badge variant="outline" className="font-mono text-[10px]">
              Zone {zone.label} · {zone.score}/100
            </Badge>
          </DialogTitle>
        </DialogHeader>

        {!brief ? (
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <Loader2 className="w-4 h-4 animate-spin" />
            Preparing your deploy brief…
          </div>
        ) : (
          <div className="space-y-5">
            <Card className="p-3 bg-foreground/5 border-border/50">
              <div className="flex items-center justify-between gap-3">
                <div className="text-sm">
                  <span className="text-muted-foreground">Target:</span>{" "}
                  <span className="font-semibold">
                    {zone.latitude.toFixed(5)}, {zone.longitude.toFixed(5)}
                  </span>
                  <span className="text-muted-foreground"> · Radius:</span>{" "}
                  <span className="font-semibold">{Math.round(radiusMeters)}m</span>
                </div>
                <Badge variant="outline" className="text-[10px] font-mono">
                  {zone.urgency || "Medium"}
                </Badge>
              </div>
            </Card>

            <div className="space-y-1.5">
              <Label>Facebook Page (required)</Label>
              {fbPages.length === 0 ? (
                <div className="flex items-start gap-2 text-sm text-amber-600 dark:text-amber-400">
                  <AlertTriangle className="w-4 h-4 mt-0.5" />
                  <div>No Facebook Pages found. Reconnect Facebook and grant page permissions.</div>
                </div>
              ) : (
                <Select value={selectedPageId} onValueChange={setSelectedPageId}>
                  <SelectTrigger className="bg-foreground/5 border-border/50">
                    <SelectValue placeholder="Select a Page" />
                  </SelectTrigger>
                  <SelectContent>
                    {fbPages.map((p) => (
                      <SelectItem key={p.id} value={p.id}>
                        {p.name || p.id}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>

            <div className="space-y-1.5">
              <Label>Ad Account</Label>
              {adAccounts.length === 0 ? (
                <div className="flex items-start gap-2 text-sm text-amber-600 dark:text-amber-400">
                  <AlertTriangle className="w-4 h-4 mt-0.5" />
                  <div>No ad accounts found. Make sure Facebook is connected with ads permissions.</div>
                </div>
              ) : (
                <Select value={selectedAccount} onValueChange={handleAccountChange}>
                  <SelectTrigger className="bg-foreground/5 border-border/50">
                    <SelectValue placeholder="Select an Ad Account" />
                  </SelectTrigger>
                  <SelectContent>
                    {adAccounts.map((a) => (
                      <SelectItem key={a.id} value={a.id}>
                        {a.name || a.id}{a.currency ? ` (${a.currency})` : ""}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>

            <div className="space-y-2">
              <Label>Caption Variant</Label>
              <RadioGroup value={selectedCaption} onValueChange={(v) => setSelectedCaption(v as any)} className="space-y-2">
                {(["aggressive", "soft", "urgency"] as const).map((k) => (
                  <label
                    key={k}
                    className={`flex items-start gap-3 p-3 rounded-xl border cursor-pointer text-sm ${
                      selectedCaption === k ? "border-primary/50 bg-primary/10" : "border-border/50 bg-foreground/[0.02]"
                    }`}
                  >
                    <RadioGroupItem value={k} className="mt-1" />
                    <div className="min-w-0">
                      <div className="font-medium capitalize">{k}</div>
                      <div className="text-muted-foreground mt-1 line-clamp-3">
                        {captions[k] || "Not available for this brief."}
                      </div>
                    </div>
                  </label>
                ))}
              </RadioGroup>
            </div>

            <div className="space-y-1.5">
              <Label>Daily Budget (cents)</Label>
              <Input
                type="number"
                value={budget}
                onChange={(e) => setBudget(e.target.value)}
                className="bg-foreground/5 border-border/50"
                min={0}
              />
              <div className="text-xs text-muted-foreground">{budgetHint}</div>
            </div>

            <Button className="w-full" disabled={!canDeploy} onClick={handleDeploy}>
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Creating draft…
                </>
              ) : (
                "Deploy as Draft"
              )}
            </Button>

            <div className="text-xs text-center text-muted-foreground">
              Ad will be created as <strong>Paused</strong>. Nothing goes live until you publish in Meta.
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

