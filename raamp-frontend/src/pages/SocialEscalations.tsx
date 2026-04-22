import { useEffect, useMemo, useState } from "react";
import Layout from "@/components/Layout";
import Reveal from "@/components/ui/Reveal";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { AlertTriangle, RefreshCw, Search } from "lucide-react";
import { apiClient } from "@/services/api";
import { autoReplyService, SocialEscalationTicket } from "@/services/autoReplyService";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

function fmtTime(v?: string | null) {
  if (!v) return "—";
  const t = new Date(v);
  if (Number.isNaN(t.getTime())) return "—";
  return t.toLocaleString();
}

function prettyPriority(p?: string | null) {
  const s = String(p || "").toLowerCase();
  if (s === "critical") return "Critical";
  if (s === "high") return "High";
  if (s === "medium") return "Medium";
  return p || "—";
}

function priorityClass(p?: string | null) {
  const s = String(p || "").toLowerCase();
  if (s === "critical") return "text-destructive border-destructive/40 bg-destructive/10";
  if (s === "high") return "text-foreground border-border/50 bg-foreground/5";
  return "text-muted-foreground border-border/50 bg-foreground/5";
}

export default function SocialEscalations() {
  const [loading, setLoading] = useState(false);
  const [rows, setRows] = useState<SocialEscalationTicket[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"open" | "acknowledged" | "resolved" | "all">("open");

  const fetchRows = async () => {
    setLoading(true);
    try {
      const qs = new URLSearchParams();
      qs.set("status_filter", statusFilter);
      qs.set("limit", "80");
      qs.set("skip", "0");
      const res = await apiClient.get<{ tickets: SocialEscalationTicket[]; total: number }>(
        `/social-escalations?${qs.toString()}`
      );
      const tickets = Array.isArray(res?.tickets) ? (res.tickets as SocialEscalationTicket[]) : [];
      tickets.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      setRows(tickets);
    } catch (e: any) {
      toast.error("Failed to load escalation tickets", { description: e?.message || "Please try again." });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRows();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return rows;
    return rows.filter((t) => {
      const text = String((t.context as any)?.comment_text || "").toLowerCase();
      return (
        String(t.platform || "").toLowerCase().includes(q) ||
        String(t.comment_id || "").toLowerCase().includes(q) ||
        String(t.intent || "").toLowerCase().includes(q) ||
        text.includes(q)
      );
    });
  }, [rows, search]);

  const ack = async (id: string) => {
    try {
      await autoReplyService.ackEscalationTicket(id);
      toast.success("Acknowledged");
      await fetchRows();
    } catch (e: any) {
      toast.error("Acknowledge failed", { description: e?.message || "Please try again." });
    }
  };

  const resolve = async (id: string) => {
    try {
      await autoReplyService.resolveEscalationTicket(id);
      toast.success("Resolved");
      await fetchRows();
    } catch (e: any) {
      toast.error("Resolve failed", { description: e?.message || "Please try again." });
    }
  };

  return (
    <Layout breadcrumbItems={[{ label: "Dashboard", href: "/dashboard" }, { label: "Escalations" }]}>
      <div className="space-y-6 px-6 pt-6 pb-24">
        <Reveal variant="fadeInUp">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="space-y-1">
              <h1 className="text-2xl font-bold font-heading tracking-[0.12em] uppercase flex items-center gap-3">
                <AlertTriangle className="w-6 h-6 text-destructive" /> Escalations
              </h1>
              <p className="text-xs font-mono text-muted-foreground/60 uppercase tracking-widest">
                All social escalation tickets (complaints/refunds/scam).
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
                placeholder="Search by comment text, intent, platform, comment ID..."
                className="bg-foreground/5 border-border/50"
              />
              <div className="w-[220px]">
                <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v as any)}>
                  <SelectTrigger className="h-9 bg-foreground/5 border-border/50 text-[11px] font-mono text-foreground">
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="open">Open</SelectItem>
                    <SelectItem value="acknowledged">Acknowledged</SelectItem>
                    <SelectItem value="resolved">Resolved</SelectItem>
                    <SelectItem value="all">All</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest whitespace-nowrap">
                {statusFilter}: {filtered.length}
              </div>
            </div>
          </Card>
        </Reveal>

        <div className="space-y-4">
          {filtered.length === 0 ? (
            <Reveal variant="fadeInUp" delay={0.2}>
              <Card className="p-10 text-center bg-card/30 border-border/50">
                <div className="text-sm font-mono text-muted-foreground/70">No tickets.</div>
              </Card>
            </Reveal>
          ) : (
            filtered.map((t, idx) => (
              <Reveal key={t.id} variant="fadeInUp" delay={0.05 * idx}>
                <Card className="p-5 bg-card/40 border-border/50 space-y-3">
                  <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                    <div className="space-y-2">
                      <div className="text-[10px] font-mono text-muted-foreground/60 uppercase tracking-widest">
                        {t.platform} · {fmtTime(t.created_at)} · SLA {fmtTime(t.sla_due_at)}
                      </div>
                      <div className={`inline-flex items-center gap-2 text-[10px] font-mono uppercase tracking-widest border rounded-md px-2 py-1 w-fit ${priorityClass(t.priority)}`}>
                        <AlertTriangle className="w-3 h-3" />
                        {prettyPriority(t.priority)} · {String(t.status || "").toUpperCase()}
                      </div>
                      {!!(t.context as any)?.comment_text && (
                        <div className="text-[11px] font-mono text-foreground/85 whitespace-pre-wrap">
                          <span className="text-muted-foreground">Comment: </span>
                          {String((t.context as any).comment_text)}
                        </div>
                      )}
                      <div className="text-[10px] font-mono text-muted-foreground break-all">
                        Ticket ID: {t.id} · Comment ID: {t.comment_id}
                      </div>
                    </div>
                    <div className="flex gap-2 md:justify-end">
                      <Button
                        variant="outline"
                        className="border-border/50"
                        onClick={() => ack(t.id)}
                        disabled={String(t.status).toLowerCase() === "resolved"}
                      >
                        Acknowledge
                      </Button>
                      <Button
                        className="bg-destructive text-destructive-foreground"
                        onClick={() => resolve(t.id)}
                        disabled={String(t.status).toLowerCase() === "resolved"}
                      >
                        Resolve
                      </Button>
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

