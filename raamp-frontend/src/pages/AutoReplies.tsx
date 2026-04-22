import { useEffect, useMemo, useState } from "react";
import Layout from "@/components/Layout";
import Reveal from "@/components/ui/Reveal";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { Check, RefreshCw, Search, X, MessageSquare, AlertTriangle } from "lucide-react";
import { autoReplyService, AutoReplyDraftItem, SocialEscalationTicket } from "@/services/autoReplyService";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";

function isActive(status: string) {
  return String(status || "").toLowerCase() === "active";
}

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

function prettyStatus(p?: string | null) {
  const s = String(p || "").toLowerCase();
  if (s === "open") return "Open";
  if (s === "acknowledged") return "Acknowledged";
  if (s === "resolved") return "Resolved";
  return p || "—";
}

function statusLabel(status: string) {
  const s = String(status || "").toLowerCase();
  if (s === "sent") return "Sent";
  if (s === "skipped") return "Skipped";
  if (s === "expired") return "Expired";
  if (s === "active") return "Active";
  return status || "Unknown";
}

export default function AutoReplies() {
  const [loading, setLoading] = useState(false);
  const [rows, setRows] = useState<AutoReplyDraftItem[]>([]);
  const [search, setSearch] = useState("");
  const [edited, setEdited] = useState<Record<string, string>>({});
  const [busyById, setBusyById] = useState<Record<string, boolean>>({});
  const [statusFilter, setStatusFilter] = useState<"active" | "sent" | "skipped" | "expired">("active");

  const [ticketOpen, setTicketOpen] = useState(false);
  const [ticketId, setTicketId] = useState<string | null>(null);
  const [ticketLoading, setTicketLoading] = useState(false);
  const [ticket, setTicket] = useState<SocialEscalationTicket | null>(null);
  const [ticketAction, setTicketAction] = useState<"ack" | "resolve" | null>(null);

  const fetchRows = async () => {
    setLoading(true);
    try {
      const res = await autoReplyService.listDrafts(statusFilter, 80, 0);
      const drafts = Array.isArray(res?.drafts) ? res.drafts : [];
      // Ensure newest-first ordering for all views (active + history).
      drafts.sort((a, b) => {
        const ta = new Date(a.created_at).getTime();
        const tb = new Date(b.created_at).getTime();
        return tb - ta;
      });
      setRows(drafts);
    } catch (e: any) {
      toast.error("Failed to load auto-replies", { description: e?.message || "Please try again." });
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
    const base = statusFilter === "active" ? rows.filter((r) => isActive(r.status)) : rows;
    if (!q) return base;
    return base.filter((r) => {
      const c = String(r.comment_text || "").toLowerCase();
      const s = String(r.suggested_reply || "").toLowerCase();
      const p = String(r.platform || "").toLowerCase();
      return c.includes(q) || s.includes(q) || p.includes(q) || String(r.comment_id || "").toLowerCase().includes(q);
    });
  }, [rows, search, statusFilter]);

  const openTicket = async (id: string) => {
    setTicketId(id);
    setTicket(null);
    setTicketOpen(true);
    setTicketLoading(true);
    try {
      const t = await autoReplyService.getEscalationTicket(id);
      setTicket(t);
    } catch (e: any) {
      toast.error("Failed to load escalation ticket", { description: e?.message || "Please try again." });
      setTicketOpen(false);
    } finally {
      setTicketLoading(false);
    }
  };

  const ackTicket = async () => {
    if (!ticketId) return;
    setTicketAction("ack");
    try {
      const res = await autoReplyService.ackEscalationTicket(ticketId);
      setTicket((p) => (p ? { ...p, status: res.status, acknowledged_at: p.acknowledged_at || new Date().toISOString() } : p));
      toast.success("Ticket acknowledged");
    } catch (e: any) {
      toast.error("Acknowledge failed", { description: e?.message || "Please try again." });
    } finally {
      setTicketAction(null);
    }
  };

  const resolveTicket = async () => {
    if (!ticketId) return;
    setTicketAction("resolve");
    try {
      const res = await autoReplyService.resolveEscalationTicket(ticketId);
      setTicket((p) => (p ? { ...p, status: res.status, resolved_at: new Date().toISOString() } : p));
      toast.success("Ticket resolved");
      // refresh counts/badges after resolving
      await fetchRows();
    } catch (e: any) {
      toast.error("Resolve failed", { description: e?.message || "Please try again." });
    } finally {
      setTicketAction(null);
    }
  };

  const approve = async (d: AutoReplyDraftItem) => {
    if (busyById[d.id]) return;
    setBusyById((p) => ({ ...p, [d.id]: true }));
    const message = (edited[d.id] ?? d.suggested_reply ?? "").trim();
    try {
      const res = await autoReplyService.approveDraft(d.id, {
        approval_nonce: d.approval_nonce,
        message,
      });
      if (!res?.success) {
        toast.error("Send failed", { description: res?.message || "Please try again." });
      } else {
        toast.success("Reply sent", { description: d.platform === "instagram" ? "Posted to Instagram" : "Posted to Facebook" });
      }
      // Optimistic remove from current list to avoid repeat actions while refreshing
      setRows((prev) => prev.filter((x) => x.id !== d.id));
      // Best-effort refresh for accurate history counts
      await fetchRows();
    } catch (e: any) {
      toast.error("Send failed", { description: e?.message || "Please try again." });
    } finally {
      setBusyById((p) => ({ ...p, [d.id]: false }));
    }
  };

  const skip = async (d: AutoReplyDraftItem) => {
    if (busyById[d.id]) return;
    setBusyById((p) => ({ ...p, [d.id]: true }));
    try {
      const res = await autoReplyService.skipDraft(d.id, "Skipped by user");
      if (!res?.success) {
        toast.message("Not skipped", { description: `Status: ${res?.status || "unknown"}` });
      } else {
        toast.success("Skipped");
      }
      setRows((prev) => prev.filter((x) => x.id !== d.id));
      await fetchRows();
    } catch (e: any) {
      toast.error("Skip failed", { description: e?.message || "Please try again." });
    } finally {
      setBusyById((p) => ({ ...p, [d.id]: false }));
    }
  };

  return (
    <Layout breadcrumbItems={[{ label: "Dashboard", href: "/dashboard" }, { label: "Auto Replies" }]}>
      <div className="space-y-6 px-6 pt-6 pb-24">
        <Sheet open={ticketOpen} onOpenChange={(v) => setTicketOpen(v)}>
          <SheetContent side="right" className="w-full sm:max-w-[520px] overflow-y-auto">
            <SheetHeader>
              <SheetTitle className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-destructive" />
                Social escalation ticket
              </SheetTitle>
            </SheetHeader>

            <div className="mt-4 space-y-3">
              {ticketLoading ? (
                <div className="text-sm font-mono text-muted-foreground">Loading…</div>
              ) : !ticket ? (
                <div className="text-sm font-mono text-muted-foreground">No ticket loaded.</div>
              ) : (
                <>
                  <div className="rounded-lg border border-border/50 bg-card/40 p-3 space-y-2">
                    <div className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest">
                      {ticket.platform} · {prettyPriority(ticket.priority)} · {prettyStatus(ticket.status)}
                    </div>
                    <div className="text-xs font-mono text-muted-foreground break-all">Ticket ID: {ticket.id}</div>
                    <div className="text-xs font-mono text-muted-foreground break-all">Comment ID: {ticket.comment_id}</div>
                    <div className="text-xs font-mono text-muted-foreground">Created: {fmtTime(ticket.created_at)}</div>
                    <div className="text-xs font-mono text-muted-foreground">SLA due: {fmtTime(ticket.sla_due_at)}</div>
                    <div className="text-xs font-mono text-muted-foreground">Acknowledged: {fmtTime(ticket.acknowledged_at)}</div>
                    <div className="text-xs font-mono text-muted-foreground">Resolved: {fmtTime(ticket.resolved_at)}</div>
                  </div>

                  {!!ticket?.context?.comment_text && (
                    <div className="rounded-lg border border-border/50 bg-foreground/5 p-3">
                      <div className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest">Comment</div>
                      <div className="mt-2 text-sm font-mono text-foreground/90 whitespace-pre-wrap">
                        {String(ticket.context.comment_text)}
                      </div>
                    </div>
                  )}

                  <div className="flex flex-wrap gap-2">
                    <Button
                      variant="outline"
                      className="border-border/50"
                      disabled={ticketAction !== null || String(ticket.status).toLowerCase() === "resolved"}
                      onClick={ackTicket}
                    >
                      {ticketAction === "ack" ? "Acknowledging..." : "Acknowledge"}
                    </Button>
                    <Button
                      className="bg-destructive text-destructive-foreground"
                      disabled={ticketAction !== null || String(ticket.status).toLowerCase() === "resolved"}
                      onClick={resolveTicket}
                    >
                      {ticketAction === "resolve" ? "Resolving..." : "Resolve"}
                    </Button>
                  </div>
                </>
              )}
            </div>
          </SheetContent>
        </Sheet>

        <Reveal variant="fadeInUp">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="space-y-1">
              <h1 className="text-2xl font-bold font-heading tracking-[0.12em] uppercase flex items-center gap-3">
                <MessageSquare className="w-6 h-6 text-primary" /> Auto Replies
              </h1>
              <p className="text-xs font-mono text-muted-foreground/60 uppercase tracking-widest">
                Review reply drafts and approve, edit, or skip.
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
                placeholder="Search by comment, reply, platform, comment ID..."
                className="bg-foreground/5 border-border/50"
              />
              <div className="w-[200px]">
                <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v as any)}>
                  <SelectTrigger className="h-9 bg-foreground/5 border-border/50 text-[11px] font-mono text-foreground">
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="sent">Sent (history)</SelectItem>
                    <SelectItem value="skipped">Skipped (history)</SelectItem>
                    <SelectItem value="expired">Expired (history)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest whitespace-nowrap">
                {statusLabel(statusFilter)}: {filtered.length}
              </div>
            </div>
          </Card>
        </Reveal>

        <div className="space-y-4">
          {filtered.length === 0 ? (
            <Reveal variant="fadeInUp" delay={0.2}>
              <Card className="p-10 text-center bg-card/30 border-border/50">
                <div className="text-sm font-mono text-muted-foreground/70">No active reply drafts.</div>
              </Card>
            </Reveal>
          ) : (
            filtered.map((d, idx) => (
              <Reveal key={d.id} variant="fadeInUp" delay={0.05 * idx}>
                <Card className="p-5 bg-card/40 border-border/50 space-y-4">
                  <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                    <div className="space-y-2">
                      <div className="text-[10px] font-mono text-muted-foreground/60 uppercase tracking-widest">
                        {d.platform} · {new Date(d.created_at).toLocaleString()} · expires {new Date(d.expires_at).toLocaleString()}
                      </div>
                      {d.comment_text && (
                        <div className="text-[11px] font-mono text-foreground/80 whitespace-pre-wrap">
                          <span className="text-muted-foreground">Comment: </span>
                          {d.comment_text}
                        </div>
                      )}
                      <div className="text-[10px] font-mono text-muted-foreground break-all">
                        Comment ID: {d.comment_id}
                      </div>
                      {!!d.escalation_ticket_id && (
                        <div className="inline-flex items-center gap-2 text-[10px] font-mono uppercase tracking-widest text-destructive border border-destructive/40 bg-destructive/10 rounded-md px-2 py-1 w-fit">
                          <AlertTriangle className="w-3 h-3 text-destructive" />
                          Escalation
                        </div>
                      )}
                    </div>

                    <div className="flex gap-2 md:justify-end">
                      {isActive(d.status) ? (
                        <>
                          {!!d.escalation_ticket_id && (
                            <Button
                              variant="outline"
                              className="border-destructive/40 text-destructive"
                              onClick={() => openTicket(String(d.escalation_ticket_id))}
                              disabled={!!busyById[d.id]}
                            >
                              View ticket
                            </Button>
                          )}
                          <Button onClick={() => approve(d)} className="bg-primary text-black" disabled={!!busyById[d.id]}>
                            <Check className="w-4 h-4 mr-2" />
                            {busyById[d.id] ? "Sending..." : "Approve & Send"}
                          </Button>
                          <Button variant="outline" onClick={() => skip(d)} className="border-border/50" disabled={!!busyById[d.id]}>
                            <X className="w-4 h-4 mr-2" />
                            {busyById[d.id] ? "Working..." : "Skip"}
                          </Button>
                        </>
                      ) : (
                        <div className="text-[10px] font-mono text-muted-foreground/60 uppercase tracking-widest border border-border/50 bg-foreground/5 rounded-md px-3 py-2 whitespace-nowrap">
                          {statusLabel(d.status)}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="text-[10px] font-mono text-muted-foreground/60 uppercase tracking-widest">
                      Reply (edit before sending)
                    </div>
                    <Textarea
                      value={edited[d.id] ?? d.suggested_reply ?? ""}
                      onChange={(e) => setEdited((prev) => ({ ...prev, [d.id]: e.target.value }))}
                      className="bg-foreground/5 border-border/50 min-h-[90px]"
                      readOnly={!isActive(d.status)}
                    />
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

