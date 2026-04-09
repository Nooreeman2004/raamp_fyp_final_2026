import { useEffect, useMemo, useState } from "react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { trendService, TrendAIAnalysis } from "@/services/trendService";
import {
  Tooltip as TooltipUI,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { toast } from "sonner";

type ExecuteKind = "draft-caption" | "generate-hooks" | "blog-outline";

export function AIStrategyDrawer(props: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  trendId: string | null;
  analysis: TrendAIAnalysis | null;
  onRegenerate: () => void;
  onOpenInCreative?: (text: string) => void;
}) {
  const { open, onOpenChange, trendId, analysis, onRegenerate, onOpenInCreative } = props;
  const [tab, setTab] = useState<"analysis" | "strategy" | "execute">("analysis");
  const [execLoading, setExecLoading] = useState<ExecuteKind | null>(null);
  const [execText, setExecText] = useState<Record<ExecuteKind, string>>({
    "draft-caption": "",
    "generate-hooks": "",
    "blog-outline": "",
  });

  useEffect(() => {
    if (!open) return;
    setTab("analysis");
  }, [open]);

  const scores = useMemo(() => {
    const s = analysis?.opportunity_score || {};
    return {
      urgency: Number((s as any)?.urgency ?? 0) || 0,
      relevance: Number((s as any)?.relevance ?? 0) || 0,
      competition: Number((s as any)?.competition ?? 0) || 0,
    };
  }, [analysis]);

  const run = async (kind: ExecuteKind) => {
    if (!trendId) return;
    setExecLoading(kind);
    setExecText((p) => ({ ...p, [kind]: "" }));
    try {
      await trendService.streamExecute(trendId, kind, {
        onChunk: (c) => setExecText((p) => ({ ...p, [kind]: (p[kind] || "") + c })),
      });
    } finally {
      setExecLoading(null);
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-[45vw] overflow-y-auto">
        <SheetHeader>
          <SheetTitle className="flex items-center justify-between gap-3">
            <span className="truncate">{analysis?.trend_keyword || "AI Strategy"}</span>
            <TooltipProvider>
              <div className="flex items-center gap-2">
                <TooltipUI>
                  <TooltipTrigger asChild>
                    <Badge variant="secondary" className="cursor-help">Urgency {scores.urgency}</Badge>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p className="text-xs">How time-sensitive this trend is (0–100).</p>
                  </TooltipContent>
                </TooltipUI>
                <TooltipUI>
                  <TooltipTrigger asChild>
                    <Badge variant="secondary" className="cursor-help">Relevance {scores.relevance}</Badge>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p className="text-xs">Fit for your niche/brand (0–100).</p>
                  </TooltipContent>
                </TooltipUI>
                <TooltipUI>
                  <TooltipTrigger asChild>
                    <Badge variant="secondary" className="cursor-help">Competition {scores.competition}</Badge>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p className="text-xs">How crowded the space is (0–100).</p>
                  </TooltipContent>
                </TooltipUI>
                <Button size="sm" variant="outline" onClick={onRegenerate}>
                  Regenerate
                </Button>
              </div>
            </TooltipProvider>
          </SheetTitle>
        </SheetHeader>

        <div className="mt-4 flex gap-2">
          <Button variant={tab === "analysis" ? "default" : "outline"} size="sm" onClick={() => setTab("analysis")}>
            Analysis
          </Button>
          <Button variant={tab === "strategy" ? "default" : "outline"} size="sm" onClick={() => setTab("strategy")}>
            Strategy
          </Button>
          <Button variant={tab === "execute" ? "default" : "outline"} size="sm" onClick={() => setTab("execute")}>
            Execute
          </Button>
        </div>

        {tab === "analysis" && (
          <div className="mt-4 space-y-4">
            <div className="rounded-lg border p-3">
              <div className="text-sm font-semibold">Executive summary</div>
              <div className="mt-2 text-sm text-muted-foreground">
                {analysis?.executive_summary || "No summary yet."}
              </div>
            </div>
            <div className="rounded-lg border p-3">
              <div className="text-sm font-semibold">Market context</div>
              <div className="mt-2 text-sm text-muted-foreground">
                {analysis?.market_context || "—"}
              </div>
            </div>
            <div className="rounded-lg border p-3">
              <div className="flex items-center justify-between">
                <div className="text-sm font-semibold">Risk</div>
                <Badge variant="outline">{analysis?.risk_level || "—"}</Badge>
              </div>
              <div className="mt-2 text-sm text-muted-foreground">
                {analysis?.risk_explanation || "—"}
              </div>
            </div>
          </div>
        )}

        {tab === "strategy" && (
          <div className="mt-4 space-y-4">
            <div className="rounded-lg border p-3">
              <div className="text-sm font-semibold">Content angles</div>
              <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-muted-foreground">
                {(analysis?.content_angles || []).map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ol>
            </div>
            <div className="rounded-lg border p-3">
              <div className="text-sm font-semibold">Hashtag pack</div>
              <div className="mt-2 space-y-2 text-sm">
                <div>
                  <div className="text-xs text-muted-foreground">Primary</div>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {(analysis?.hashtag_pack?.primary || []).map((h) => (
                      <Badge key={h} variant="secondary" className="cursor-pointer" onClick={() => navigator.clipboard?.writeText(h)}>
                        {h}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">Secondary</div>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {(analysis?.hashtag_pack?.secondary || []).map((h) => (
                      <Badge key={h} variant="secondary" className="cursor-pointer" onClick={() => navigator.clipboard?.writeText(h)}>
                        {h}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">Niche</div>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {(analysis?.hashtag_pack?.niche || []).map((h) => (
                      <Badge key={h} variant="secondary" className="cursor-pointer" onClick={() => navigator.clipboard?.writeText(h)}>
                        {h}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
            </div>
            <div className="rounded-lg border p-3">
              <div className="text-sm font-semibold">Posting window</div>
              <div className="mt-2 text-sm text-muted-foreground">{analysis?.posting_window || "—"}</div>
            </div>
          </div>
        )}

        {tab === "execute" && (
          <div className="mt-4 space-y-3">
            {([
              ["draft-caption", "Draft Caption"],
              ["generate-hooks", "Generate Hooks"],
              ["blog-outline", "Blog Outline"],
            ] as Array<[ExecuteKind, string]>).map(([kind, label]) => (
              <div key={kind} className="rounded-lg border p-3">
                <Button
                  className="w-full"
                  disabled={!!execLoading}
                  onClick={() => run(kind)}
                >
                  {execLoading === kind ? "Streaming..." : label}
                </Button>
                {execText[kind] ? (
                  <>
                    <pre className="mt-3 max-h-[40vh] overflow-y-auto whitespace-pre-wrap rounded-md bg-muted p-3 text-sm">
                      {execText[kind]}
                    </pre>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={async () => {
                          try {
                            await navigator.clipboard.writeText(execText[kind] || "");
                            toast.success("Copied to clipboard");
                          } catch {
                            toast.error("Copy failed");
                          }
                        }}
                      >
                        Copy
                      </Button>
                      <Button
                        size="sm"
                        onClick={() => onOpenInCreative?.(execText[kind] || "")}
                        disabled={!onOpenInCreative}
                      >
                        Open in Creative →
                      </Button>
                    </div>
                  </>
                ) : null}
              </div>
            ))}
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}

