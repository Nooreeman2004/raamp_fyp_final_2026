import { useEffect, useMemo, useState } from "react";
import Layout from "@/components/Layout";
import Reveal from "@/components/ui/Reveal";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { Check, X, RefreshCw, Search, ShieldCheck } from "lucide-react";
import { campaignLaunchService, CampaignLaunchItem } from "@/services/campaignLaunchService";

function isPending(status: string) {
  return String(status || "").toLowerCase() === "pending";
}

export default function CampaignApprovals() {
  const [loading, setLoading] = useState(false);
  const [rows, setRows] = useState<CampaignLaunchItem[]>([]);
  const [search, setSearch] = useState("");
  const [rejectReason, setRejectReason] = useState<Record<string, string>>({});

  const fetchRows = async () => {
    setLoading(true);
    try {
      const res = await campaignLaunchService.listRequests(80, 0);
      setRows(Array.isArray(res?.requests) ? res.requests : []);
    } catch (e: any) {
      toast.error("Failed to load approvals", { description: e?.message || "Please try again." });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRows();
  }, []);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    const base = rows.filter((r) => isPending(r.status));
    if (!q) return base;
    return base.filter((r) => {
      const kw = (r.trend_keyword || "").toLowerCase();
      const cap = (r.caption || "").toLowerCase();
      const plat = (r.platform || "").toLowerCase();
      return kw.includes(q) || cap.includes(q) || plat.includes(q);
    });
  }, [rows, search]);

  const approve = async (id: string) => {
    try {
      const res = await campaignLaunchService.approveRequest(id);
      if (String(res.status || "").toLowerCase() === "failed" || res.success === false) {
        const err = (res as any)?.result?.error || (res as any)?.result?.message || "Execution failed";
        toast.error("Approved but execution failed", { description: String(err) });
      } else {
        toast.success("Approved & executed", { description: `Status: ${res.status}` });
      }
      await fetchRows();
    } catch (e: any) {
      toast.error("Approval failed", { description: e?.message || "Please try again." });
    }
  };

  const reject = async (id: string) => {
    const reason = (rejectReason[id] || "").trim() || "Rejected by user";
    try {
      const res = await campaignLaunchService.rejectRequest(id, reason);
      toast.success("Rejected", { description: `Status: ${res.status}` });
      await fetchRows();
    } catch (e: any) {
      toast.error("Rejection failed", { description: e?.message || "Please try again." });
    }
  };

  return (
    <Layout>
      <div className="space-y-6 px-6 pt-6 pb-24">
        <Reveal variant="fadeInUp">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="space-y-1">
              <h1 className="text-2xl font-bold font-heading tracking-[0.12em] uppercase flex items-center gap-3">
                <ShieldCheck className="w-6 h-6 text-primary" /> Campaign Approvals
              </h1>
              <p className="text-xs font-mono text-muted-foreground/60 uppercase tracking-widest">
                Review pending launch requests and approve/reject execution.
              </p>
            </div>
            <Button variant="outline" onClick={fetchRows} disabled={loading} className="border-border/50">
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>
        </Reveal>

        <Reveal variant="fadeInUp" delay={0.1}>
          <Card className="p-4 bg-card/50 border-border/50">
            <div className="flex items-center gap-3">
              <Search className="w-4 h-4 text-muted-foreground/60" />
              <Input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by keyword, caption, platform..."
                className="bg-foreground/5 border-border/50"
              />
              <div className="text-[10px] font-mono text-muted-foreground/50 uppercase tracking-widest">
                Pending: {filtered.length}
              </div>
            </div>
          </Card>
        </Reveal>

        <div className="space-y-4">
          {filtered.length === 0 ? (
            <Reveal variant="fadeInUp" delay={0.2}>
              <Card className="p-10 text-center bg-card/30 border-border/50">
                <div className="text-sm font-mono text-muted-foreground/70">No pending approvals.</div>
              </Card>
            </Reveal>
          ) : (
            filtered.map((r, idx) => (
              <Reveal key={r.id} variant="fadeInUp" delay={0.05 * idx}>
                <Card className="p-5 bg-card/40 border-border/50 space-y-4">
                  <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                    <div className="space-y-1">
                      <div className="text-[10px] font-mono text-muted-foreground/60 uppercase tracking-widest">
                        {r.platform} · {r.mode} · {new Date(r.created_at).toLocaleString()}
                      </div>
                      <div className="text-lg font-heading font-semibold text-foreground">
                        {r.trend_keyword || "Campaign launch request"}
                      </div>
                      {r.caption && (
                        <div className="text-[11px] font-mono text-muted-foreground/70 line-clamp-3">
                          {r.caption}
                        </div>
                      )}
                      <div className="text-[10px] font-mono text-muted-foreground/60 break-all">
                        Media: {r.media_url}
                      </div>
                    </div>

                    <div className="flex gap-2 md:justify-end">
                      <Button onClick={() => approve(r.id)} className="bg-primary text-black">
                        <Check className="w-4 h-4 mr-2" /> Approve & Execute
                      </Button>
                      <Button variant="outline" onClick={() => reject(r.id)} className="border-border/50">
                        <X className="w-4 h-4 mr-2" /> Reject
                      </Button>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <div className="text-[10px] font-mono text-muted-foreground/60 uppercase tracking-widest">
                        Reject reason (optional)
                      </div>
                      <Input
                        value={rejectReason[r.id] || ""}
                        onChange={(e) => setRejectReason((prev) => ({ ...prev, [r.id]: e.target.value }))}
                        placeholder="e.g. wrong media, not aligned to brand..."
                        className="bg-foreground/5 border-border/50"
                      />
                    </div>
                  </div>
                </Card>
              </Reveal>
            ))
          )}
        </div>
      </div>
    </Layout>
  );
}

