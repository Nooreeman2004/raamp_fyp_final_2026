import { useEffect, useMemo, useState } from "react";
import Layout from "@/components/Layout";
import Reveal from "@/components/ui/Reveal";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { CalendarDays, Plus, RefreshCw, Search, Sparkles, TrendingUp } from "lucide-react";
import { campaignPlannerService, CampaignPlanListItem } from "@/services/campaignPlannerService";
import { CreateCampaignPlanDialog } from "@/components/campaign-planner/CreateCampaignPlanDialog";
import { Link } from "react-router-dom";

export default function CampaignPlanner() {
  const [loading, setLoading] = useState(false);
  const [rows, setRows] = useState<CampaignPlanListItem[]>([]);
  const [search, setSearch] = useState("");
  const [open, setOpen] = useState(false);

  const fetchRows = async () => {
    setLoading(true);
    try {
      const res = await campaignPlannerService.listPlans(80, 0);
      setRows(Array.isArray(res?.plans) ? res.plans : []);
    } catch (e: any) {
      toast.error("Failed to load campaign plans", { description: e?.message || "Please try again." });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRows();
  }, []);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return rows;
    return rows.filter((r) => {
      return (
        (r.name || "").toLowerCase().includes(q) ||
        (r.objective || "").toLowerCase().includes(q) ||
        (r.timezone || "").toLowerCase().includes(q)
      );
    });
  }, [rows, search]);

  // De-dupe visually identical plans (common when generation fails and user retries).
  // Keep the most recent by created_at.
  const deduped = useMemo(() => {
    const sorted = [...filtered].sort((a, b) => +new Date(b.created_at) - +new Date(a.created_at));
    const seen = new Set<string>();
    const out: CampaignPlanListItem[] = [];
    for (const r of sorted) {
      const key = [
        (r.name || "").trim().toLowerCase(),
        (r.objective || "").trim().toLowerCase(),
        new Date(r.start_date).toISOString().slice(0, 10),
        new Date(r.end_date).toISOString().slice(0, 10),
        (r.timezone || "").trim().toLowerCase(),
        (r.generation_status || "").trim().toLowerCase(),
      ].join("|");
      if (seen.has(key)) continue;
      seen.add(key);
      out.push(r);
    }
    // restore chronological reveal feel
    return out.sort((a, b) => +new Date(a.created_at) - +new Date(b.created_at));
  }, [filtered]);

  return (
    <Layout breadcrumbItems={[{ label: "Dashboard", href: "/dashboard" }, { label: "Campaign Planner" }]}>
      <div className="space-y-6 px-6 pt-6 pb-24">
        <Reveal variant="fadeInUp">
          <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div className="space-y-2">
              <h1 className="text-2xl font-bold font-heading tracking-[0.12em] uppercase flex items-center gap-3">
                <CalendarDays className="w-6 h-6 text-primary" /> Campaign Planner
              </h1>
              <div className="space-y-1">
                <p className="text-xs font-mono text-muted-foreground/70 uppercase tracking-widest flex items-center gap-2">
                  <Sparkles className="w-3.5 h-3.5 text-primary" />
                  Brand-driven planning
                </p>
                <p className="text-[11px] font-mono text-muted-foreground/60 leading-relaxed">
                  Build a calendar from your Brand DNA (theme, tone, specialties). For trend-driven opportunities, use{" "}
                  <Link to="/dashboard/trends" className="underline underline-offset-4">
                    Trend Arbitrage
                  </Link>{" "}
                  <TrendingUp className="inline w-3 h-3 ml-1" />. This page will never generate trend-led plans.
                </p>
              </div>
            </div>

            <div className="flex gap-2">
              <Button variant="outline" onClick={fetchRows} disabled={loading} className="border-border/50">
                <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
                Refresh
              </Button>
              <Button onClick={() => setOpen(true)} className="bg-primary text-black">
                <Plus className="w-4 h-4 mr-2" /> Create plan
              </Button>
            </div>
          </div>
        </Reveal>

        <Reveal variant="fadeInUp" delay={0.1}>
          <Card className="p-4 bg-card/50 border-border/50">
            <div className="flex items-center gap-3">
              <Search className="w-4 h-4 text-muted-foreground/60" />
              <Input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by name, objective, timezone..."
                className="bg-foreground/5 border-border/50"
              />
              <div className="shrink-0 h-10 flex items-center whitespace-nowrap text-[10px] leading-none font-mono text-muted-foreground/50 uppercase tracking-widest">
                Plans: {deduped.length}
              </div>
            </div>
          </Card>
        </Reveal>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {deduped.map((r, idx) => (
            <Reveal key={r.id} variant="fadeInUp" delay={0.03 * idx}>
              <Card className="p-5 bg-card/40 border-border/50 space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="text-[10px] font-mono text-muted-foreground/60 uppercase tracking-widest">
                      {new Date(r.created_at).toLocaleString()} · {r.timezone}
                    </div>
                    <div className="text-lg font-heading font-semibold">{r.name}</div>
                    <div className="text-[11px] font-mono text-muted-foreground/70">
                      Objective: {r.objective || "—"}
                    </div>
                  </div>
                  <Button asChild variant="outline" className="border-border/50">
                    <Link to={`/dashboard/campaign-planner/${r.id}`}>Open</Link>
                  </Button>
                </div>
                <div className="text-[10px] font-mono text-muted-foreground/60 uppercase tracking-widest">
                  Range: {new Date(r.start_date).toLocaleDateString()} → {new Date(r.end_date).toLocaleDateString()}
                </div>
                <div className="text-[10px] font-mono text-muted-foreground/60 uppercase tracking-widest">
                  Generation: {r.generation_status}
                </div>
              </Card>
            </Reveal>
          ))}
        </div>

        <CreateCampaignPlanDialog
          open={open}
          onOpenChange={setOpen}
          onCreated={async () => {
            setOpen(false);
            await fetchRows();
          }}
        />
      </div>
    </Layout>
  );
}

