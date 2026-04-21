import { useEffect, useMemo, useState } from "react";
import Layout from "@/components/Layout";
import Reveal from "@/components/ui/Reveal";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { Check, RefreshCw, Search, X, MessageSquare } from "lucide-react";
import { autoReplyService, AutoReplyDraftItem } from "@/services/autoReplyService";

function isActive(status: string) {
  return String(status || "").toLowerCase() === "active";
}

export default function AutoReplies() {
  const [loading, setLoading] = useState(false);
  const [rows, setRows] = useState<AutoReplyDraftItem[]>([]);
  const [search, setSearch] = useState("");
  const [edited, setEdited] = useState<Record<string, string>>({});

  const fetchRows = async () => {
    setLoading(true);
    try {
      const res = await autoReplyService.listDrafts("active", 80, 0);
      setRows(Array.isArray(res?.drafts) ? res.drafts : []);
    } catch (e: any) {
      toast.error("Failed to load auto-replies", { description: e?.message || "Please try again." });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRows();
  }, []);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    const base = rows.filter((r) => isActive(r.status));
    if (!q) return base;
    return base.filter((r) => {
      const c = String(r.comment_text || "").toLowerCase();
      const s = String(r.suggested_reply || "").toLowerCase();
      const p = String(r.platform || "").toLowerCase();
      return c.includes(q) || s.includes(q) || p.includes(q) || String(r.comment_id || "").toLowerCase().includes(q);
    });
  }, [rows, search]);

  const approve = async (d: AutoReplyDraftItem) => {
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
      await fetchRows();
    } catch (e: any) {
      toast.error("Send failed", { description: e?.message || "Please try again." });
    }
  };

  const skip = async (d: AutoReplyDraftItem) => {
    try {
      const res = await autoReplyService.skipDraft(d.id, "Skipped by user");
      if (!res?.success) {
        toast.message("Not skipped", { description: `Status: ${res?.status || "unknown"}` });
      } else {
        toast.success("Skipped");
      }
      await fetchRows();
    } catch (e: any) {
      toast.error("Skip failed", { description: e?.message || "Please try again." });
    }
  };

  return (
    <Layout breadcrumbItems={[{ label: "Dashboard", href: "/dashboard" }, { label: "Auto Replies" }]}>
      <div className="space-y-6 px-6 pt-6 pb-24">
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
              <div className="text-[10px] font-mono text-muted-foreground/50 uppercase tracking-widest">
                Active: {filtered.length}
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
                        <div className="text-[11px] font-mono text-muted-foreground/80 whitespace-pre-wrap">
                          <span className="text-muted-foreground/60">Comment: </span>
                          {d.comment_text}
                        </div>
                      )}
                      <div className="text-[10px] font-mono text-muted-foreground/60 break-all">
                        Comment ID: {d.comment_id}
                      </div>
                    </div>

                    <div className="flex gap-2 md:justify-end">
                      <Button onClick={() => approve(d)} className="bg-primary text-black">
                        <Check className="w-4 h-4 mr-2" /> Approve & Send
                      </Button>
                      <Button variant="outline" onClick={() => skip(d)} className="border-border/50">
                        <X className="w-4 h-4 mr-2" /> Skip
                      </Button>
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

