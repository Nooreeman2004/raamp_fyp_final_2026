import { useMemo, useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { ExternalLink, Copy } from "lucide-react";

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
  radiusMeters: number;
  personaSplit?: Array<{ type: string; pct: number; desc: string }>;
  areaName?: string | null;
  onClose: () => void;
}

function sanitizeCaptionNoDashes(raw: string): string {
  return String(raw || "")
    .split("\n")
    .map((line) => {
      const l = line.replace(/\s+$/g, "");
      if (/^\s*-\s+/.test(l)) return l.replace(/^\s*-\s+/, "• ");
      if (/^\s*-\s*$/.test(l)) return "";
      return l;
    })
    .filter((l) => l.trim().length > 0)
    .join("\n");
}

export default function MetaDeployModal({ zone, brief, radiusMeters, personaSplit = [], areaName, onClose }: Props) {
  const [open, setOpen] = useState(true);
  const [showFullPreview, setShowFullPreview] = useState(false);

  const budgetHint = useMemo(() => {
    const min = brief?.suggested_budget_min;
    const max = brief?.suggested_budget_max;
    if (typeof min === "number" && typeof max === "number" && min > 0 && max > 0) {
      return `RAAMP suggestion: ${min}–${max}`;
    }
    return "RAAMP suggestion: based on local intent + radius";
  }, [brief?.suggested_budget_min, brief?.suggested_budget_max]);

  const caption = useMemo(() => {
    const v = brief?.caption_variants || {};
    return sanitizeCaptionNoDashes(String(v.soft || v.urgency || v.aggressive || "").trim());
  }, [brief]);

  const statBudget = useMemo(() => {
    const min = brief?.suggested_budget_min;
    const max = brief?.suggested_budget_max;
    if (typeof min === "number" && typeof max === "number" && min > 0 && max > 0) {
      return `${min}–${max}`;
    }
    return "—";
  }, [brief?.suggested_budget_min, brief?.suggested_budget_max]);

  const personasText = useMemo(() => {
    const list = Array.isArray(personaSplit) ? personaSplit : [];
    const cleaned = list
      .map((p) => ({
        type: String(p?.type || "").trim(),
        pct: Number(p?.pct ?? 0) || 0,
      }))
      .filter((p) => p.type && p.pct > 0)
      .sort((a, b) => b.pct - a.pct);

    if (cleaned.length < 2) return null;
    // If the split looks suspicious (one persona dominates ~100%), hide it instead of implying false certainty.
    if (cleaned[0].pct >= 95) return null;
    const top = cleaned.slice(0, 4);
    return `Personas: ${top.map((p) => `${p.type} (${p.pct}%)`).join(", ")}`;
  }, [personaSplit]);

  const radiusKm = useMemo(() => {
    const km = radiusMeters / 1000;
    if (!Number.isFinite(km)) return "—";
    return km >= 10 ? `${Math.round(km)} km` : `${km.toFixed(1)} km`;
  }, [radiusMeters]);

  const exportText = useMemo(() => {
    const lines: string[] = [];
    lines.push(`RAAMP CAMPAIGN PACKAGE`);
    lines.push(`Zone: ${zone.label}`);
    lines.push(`Heat score: ${zone.score}/100`);
    lines.push(`Urgency: ${zone.urgency || "Medium"}`);
    lines.push(`Suggested budget: ${statBudget !== "—" ? statBudget : budgetHint}`);
    lines.push(``);
    lines.push(`TARGETING`);
    if (areaName) {
      lines.push(`Area: ${areaName}`);
    } else {
      lines.push(`Coordinates: ${zone.latitude.toFixed(5)}, ${zone.longitude.toFixed(5)}`);
    }
    lines.push(`Radius: ${radiusKm}`);
    if (personasText) lines.push(personasText);
    lines.push(``);
    lines.push(`CAPTION`);
    lines.push(caption || "—");
    return lines.join("\n");
  }, [zone, caption, budgetHint, statBudget, personasText, radiusKm, areaName]);

  const previewLines = useMemo(() => exportText.split("\n"), [exportText]);
  const previewShort = useMemo(() => previewLines.slice(0, 2).join("\n"), [previewLines]);

  return (
    <Dialog
      open={open}
      onOpenChange={(v) => {
        setOpen(v);
        if (!v) onClose();
      }}
    >
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
        <DialogHeader>
          {/* DialogContent renders its own close button top-right; reserve space to avoid overlap */}
          <DialogTitle className="flex items-center justify-between gap-3 pr-10">
            <span>Export campaign package</span>
            <Badge variant="outline" className="font-mono text-[10px] shrink-0">
              Heat {zone.score}/100
            </Badge>
          </DialogTitle>
        </DialogHeader>

        {!brief ? (
          <div className="text-sm text-muted-foreground">
            Preparing your export package…
          </div>
        ) : (
          <div className="flex-1 space-y-5 overflow-y-auto pr-2">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <Card className="p-3 bg-foreground/5 border-border/50">
                <div className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">Zone</div>
                <div className="text-sm font-semibold text-foreground mt-1">
                  {zone.label}
                </div>
                {!areaName && (
                  <div className="text-[10px] text-muted-foreground mt-0.5">
                    {zone.latitude.toFixed(2)}°N, {zone.longitude.toFixed(2)}°E
                  </div>
                )}
              </Card>
              <Card className="p-3 bg-foreground/5 border-border/50">
                <div className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">Urgency</div>
                <div className="text-sm font-semibold text-foreground mt-1">{zone.urgency || "Medium"}</div>
              </Card>
              <Card className="p-3 bg-foreground/5 border-border/50">
                <div className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">Suggested budget</div>
                <div className="text-sm font-semibold text-foreground mt-1">
                  {statBudget !== "—" ? statBudget : "—"}
                </div>
              </Card>
            </div>

            <Card className="p-4 bg-foreground/5 border-border/50">
              <div className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground mb-2">Caption (copy-ready)</div>
              <div className="whitespace-pre-wrap text-sm text-foreground font-sans leading-relaxed">
                {caption || "—"}
              </div>
            </Card>

            <Card className="p-4 bg-foreground/5 border-border/50">
              <div className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground mb-2">Targeting params</div>
              <div className="text-sm text-foreground space-y-1">
                {areaName ? (
                  <div className="text-muted-foreground">
                    Area: <span className="text-foreground">{areaName}</span>
                  </div>
                ) : (
                  <div className="text-muted-foreground">
                    Coordinates:{" "}
                    <span className="text-foreground">
                      {zone.latitude.toFixed(2)}°N, {zone.longitude.toFixed(2)}°E
                    </span>
                  </div>
                )}
                <div className="text-muted-foreground">
                  Radius: <span className="text-foreground">{radiusKm}</span>
                </div>
                {personasText ? (
                  <div className="text-muted-foreground">
                    <span className="text-foreground">{personasText}</span>
                  </div>
                ) : null}
              </div>
            </Card>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Button
                type="button"
                variant="secondary"
                onClick={async () => {
                  try {
                    await navigator.clipboard.writeText(caption || "");
                    toast.success("Caption copied");
                  } catch {
                    toast.error("Could not copy caption");
                  }
                }}
                disabled={!caption}
              >
                <Copy className="w-4 h-4 mr-2" />
                Copy caption
              </Button>
              <Button
                type="button"
                onClick={async () => {
                  try {
                    await navigator.clipboard.writeText(exportText);
                    toast.success("Package copied");
                  } catch {
                    toast.error("Could not copy package");
                  }
                }}
              >
                <Copy className="w-4 h-4 mr-2" />
                Copy all as text
              </Button>
            </div>

            <div className="rounded-xl border border-border/50 bg-background/40 px-4 py-3">
              <div className="flex items-center justify-between gap-3">
                <div className="text-xs text-muted-foreground">
                  Preview what “Copy all as text” copies
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  className="h-7 px-2 text-[10px] font-mono"
                  onClick={() => setShowFullPreview((v) => !v)}
                >
                  {showFullPreview ? "Show less" : "Show more"}
                </Button>
              </div>
              <pre className="mt-2 whitespace-pre-wrap text-[12px] leading-relaxed text-foreground font-mono">
{showFullPreview ? exportText : `${previewShort}\n…`}
              </pre>
            </div>

            <div className="text-xs text-center text-muted-foreground">
              Open Meta Ads Manager and paste the package manually.
              <Button
                type="button"
                variant="link"
                className="ml-2 h-auto p-0 text-primary"
                onClick={() => window.open("https://adsmanager.facebook.com", "_blank")}
              >
                Open Meta Ads Manager <ExternalLink className="w-3.5 h-3.5 ml-1" />
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

