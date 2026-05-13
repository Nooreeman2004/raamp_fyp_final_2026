import { useEffect, useMemo, useState } from "react";
import Layout from "@/components/Layout";
import Reveal from "@/components/ui/Reveal";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { CalendarDays, Plus, RefreshCw, Search, Sparkles, TrendingUp, Trash2 } from "lucide-react";
import { campaignPlannerService, CampaignPlanListItem } from "@/services/campaignPlannerService";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { CreateCampaignPlanDialog } from "@/components/campaign-planner/CreateCampaignPlanDialog";
import ConfirmationDialog from "@/components/ConfirmationDialog";
import { Link } from "react-router-dom";

export default function CampaignPlanner() {
  const [loading, setLoading] = useState(false);
  const [rows, setRows] = useState<CampaignPlanListItem[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "past" | "failed">("all");
  const [open, setOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<{ id: string; name: string } | null>(null);

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      setLoading(true);
      const deletedId = deleteTarget.id;
      await campaignPlannerService.deletePlan(deletedId);
      // Optimistic UI update so the deleted plan disappears immediately.
      setRows((prev) => prev.filter((r) => r.id !== deletedId));
      toast.success("Campaign plan deleted");
      await fetchRows();
    } catch (e: any) {
      toast.error("Failed to delete plan", { description: e?.message || "Please try again." });
    } finally {
      setLoading(false);
      setDeleteTarget(null);
    }
  };

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

  // Auto-polling for "running" plans
  useEffect(() => {
    const hasRunning = rows.some((r) => r.generation_status === "running");
    if (!hasRunning) return;

    const interval = setInterval(() => {
      fetchRows();
    }, 5000);

    return () => clearInterval(interval);
  }, [rows]);

  const hasRunning = rows.some((r) => r.generation_status === "running");

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    const now = new Date().getTime();

    return rows.filter((r) => {
      // NEVER show failed campaigns unless explicitly filtered to "failed"
      const isFailed = r.generation_status.toLowerCase() === "failed";
      if (statusFilter !== "failed" && isFailed) {
        return false;
      }
      
      // 1. Status Filter
      if (statusFilter === "failed") {
        // Only show failed campaigns
        if (!isFailed) return false;
      } else if (statusFilter === "active" || statusFilter === "past") {
        // For active/past, check date range
        const endMs = new Date(r.end_date).getTime();
        if (statusFilter === "active" && endMs < now) return false;
        if (statusFilter === "past" && endMs >= now) return false;
      }
      // "all" shows everything except failed (already filtered above)
      
      // 2. Search Filter
      if (!q) return true;
      return (
        (r.name || "").toLowerCase().includes(q) ||
        (r.objective || "").toLowerCase().includes(q) ||
        (r.timezone || "").toLowerCase().includes(q)
      );
    });
  }, [rows, search, statusFilter]);

  // Keep 1:1 fidelity with backend records.
  const visibleRows = filtered;

  return (
    <Layout breadcrumbItems={[{ label: "Dashboard", href: "/dashboard" }, { label: "Campaign Planner" }]}>
      <div className="space-y-6 px-6 pt-6 pb-24">
        <Reveal variant="fadeInUp">
          <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div className="space-y-2">
              <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent flex items-center gap-3">
                <CalendarDays className="w-8 h-8 text-primary shadow-[0_0_20px_rgba(0,224,208,0.2)]" />
                Campaign Planner
              </h1>
              <div className="space-y-1">
                <p className="text-xs font-mono font-medium text-muted-foreground uppercase tracking-widest flex items-center gap-2">
                  <Sparkles className="w-3.5 h-3.5 text-primary" />
                  Brand-driven planning
                </p>
                <p className="text-xs font-mono font-medium text-muted-foreground leading-relaxed">
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
              <Button onClick={() => setOpen(true)} className="bg-primary text-black" disabled={hasRunning}>
                <Plus className="w-4 h-4 mr-2" /> {hasRunning ? "Generating…" : "Create plan"}
              </Button>
            </div>
          </div>
        </Reveal>

        <Reveal variant="fadeInUp" delay={0.1}>
          <Card className="p-4 bg-card/50 border-border/50">
            <div className="flex items-center gap-3">
              <Select value={statusFilter} onValueChange={(v: any) => setStatusFilter(v)}>
                <SelectTrigger className="w-[130px] bg-foreground/5 border-border/50 shrink-0">
                  <SelectValue placeholder="Filter" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Plans</SelectItem>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="past">Past</SelectItem>
                  <SelectItem value="failed">Failed</SelectItem>
                </SelectContent>
              </Select>
              <Search className="w-4 h-4 text-muted-foreground/60 shrink-0" />
              <Input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by name, objective, timezone..."
                className="bg-foreground/5 border-border/50"
              />
              <div className="shrink-0 h-10 flex items-center whitespace-nowrap text-xs leading-none font-mono font-medium text-muted-foreground uppercase tracking-widest">
                Plans: {visibleRows.length}
              </div>
            </div>
          </Card>
        </Reveal>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {visibleRows.map((r, idx) => (
            <Reveal key={r.id} variant="fadeInUp" delay={0.03 * idx}>
              <Card className="p-5 bg-card/40 border-border/50 space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="text-xs font-mono font-medium text-muted-foreground uppercase tracking-widest">
                      {new Date(r.created_at).toLocaleString()} · {r.timezone}
                    </div>
                    <div className="text-lg font-heading font-semibold">{r.name}</div>
                    <div className="text-xs font-mono font-medium text-muted-foreground">
                      Objective: {r.objective || "—"}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-red-500 hover:text-red-400 hover:bg-red-500/10"
                      onClick={() => setDeleteTarget({ id: r.id, name: r.name })}
                      disabled={loading}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                    <Button asChild variant="outline" className="border-border/50">
                      <Link to={`/dashboard/campaign-planner/${r.id}`}>Open</Link>
                    </Button>
                  </div>
                </div>
                <div className="text-xs font-mono font-medium text-muted-foreground uppercase tracking-widest">
                  Range: {new Date(r.start_date).toLocaleDateString()} → {new Date(r.end_date).toLocaleDateString()}
                </div>
                <div className="text-xs font-mono font-medium text-muted-foreground uppercase tracking-widest">
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

        <ConfirmationDialog
          open={!!deleteTarget}
          onOpenChange={(o) => { if (!o) setDeleteTarget(null); }}
          onConfirm={handleDelete}
          title="Delete Campaign Plan?"
          description={`"${deleteTarget?.name ?? ""}" will be permanently deleted. This action cannot be undone.`}
          confirmText="Delete"
          cancelText="Keep it"
          variant="destructive"
        />
      </div>
    </Layout>
  );
}

