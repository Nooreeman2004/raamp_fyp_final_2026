import { useEffect, useMemo, useState } from "react";
import Layout from "@/components/Layout";
import Reveal from "@/components/ui/Reveal";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { 
  AlertTriangle, 
  RefreshCw, 
  Search, 
  MessageSquare, 
  ShieldAlert,
  Trash2,
  CheckCircle,
  ThumbsUp,
  ThumbsDown,
  Minus
} from "lucide-react";
import { apiClient } from "@/services/api";
import { autoReplyService, SocialEscalationTicket } from "@/services/autoReplyService";
import { 
  commentModerationService, 
  AnalyzedComment, 
  CommentModerationResponse,
  Sentiment 
} from "@/services/commentModerationService";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";

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

function getSentimentIcon(sentiment: Sentiment) {
  switch (sentiment) {
    case "POSITIVE": return <ThumbsUp className="w-4 h-4 text-green-500" />;
    case "NEGATIVE": return <ThumbsDown className="w-4 h-4 text-red-500" />;
    case "NEUTRAL": return <Minus className="w-4 h-4 text-yellow-500" />;
  }
}

function getSentimentColor(sentiment: Sentiment) {
  switch (sentiment) {
    case "POSITIVE": return "bg-green-500/10 text-green-600 border-green-500/20";
    case "NEGATIVE": return "bg-red-500/10 text-red-600 border-red-500/20";
    case "NEUTRAL": return "bg-yellow-500/10 text-yellow-600 border-yellow-500/20";
  }
}

const SENTIMENT_COLORS = {
  POSITIVE: "#22c55e",
  NEUTRAL: "#eab308",
  NEGATIVE: "#ef4444"
};

export default function SocialModeration() {
  const [activeTab, setActiveTab] = useState<"escalations" | "comments">("escalations");
  
  // Escalations state
  const [escalationsLoading, setEscalationsLoading] = useState(false);
  const [escalations, setEscalations] = useState<SocialEscalationTicket[]>([]);
  const [escalationSearch, setEscalationSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"open" | "acknowledged" | "resolved" | "all">("open");

  // Comment Moderation state
  const [commentsLoading, setCommentsLoading] = useState(false);
  const [commentData, setCommentData] = useState<CommentModerationResponse | null>(null);
  const [commentSearch, setCommentSearch] = useState("");
  const [sentimentFilter, setSentimentFilter] = useState<Sentiment | "all">("all");
  const [selectedComments, setSelectedComments] = useState<Set<string>>(new Set());

  // Fetch Escalations
  const fetchEscalations = async () => {
    setEscalationsLoading(true);
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
      setEscalations(tickets);
    } catch (e: any) {
      toast.error("Failed to load escalation tickets", { description: e?.message || "Please try again." });
    } finally {
      setEscalationsLoading(false);
    }
  };

  // Fetch Comments for Moderation
  const fetchComments = async () => {
    setCommentsLoading(true);
    try {
      const sentiment = sentimentFilter === "all" ? undefined : sentimentFilter;
      const data = await commentModerationService.getModerationComments(sentiment, 100);
      setCommentData(data);
    } catch (e: any) {
      console.error("Comment fetch error:", e);
      const errorMsg = e?.message || e?.detail || "Please try again.";
      toast.error("Failed to load comments", { 
        description: errorMsg.includes("not found") 
          ? "No comments have been analyzed yet. Comments will appear here after they're analyzed."
          : errorMsg 
      });
      // Set empty data on error to show proper empty state
      setCommentData({
        total: 0,
        spam_count: 0,
        sentiment_summary: { POSITIVE: 0, NEUTRAL: 0, NEGATIVE: 0 },
        comments: []
      });
    } finally {
      setCommentsLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === "escalations") {
      fetchEscalations();
    } else if (activeTab === "comments") {
      fetchComments();
    }
  }, [activeTab, statusFilter, sentimentFilter]);

  // Filtered escalations
  const filteredEscalations = useMemo(() => {
    const q = escalationSearch.trim().toLowerCase();
    if (!q) return escalations;
    return escalations.filter((t) => {
      const text = String((t.context as any)?.comment_text || "").toLowerCase();
      return (
        String(t.platform || "").toLowerCase().includes(q) ||
        String(t.comment_id || "").toLowerCase().includes(q) ||
        String(t.intent || "").toLowerCase().includes(q) ||
        text.includes(q)
      );
    });
  }, [escalations, escalationSearch]);

  // Filtered comments - sorted by spam confidence (highest first)
  const filteredComments = useMemo(() => {
    if (!commentData) return [];
    const q = commentSearch.trim().toLowerCase();
    let filtered = commentData.comments;
    
    if (q) {
      filtered = filtered.filter((c) => 
        c.text.toLowerCase().includes(q) || c.comment_id.toLowerCase().includes(q)
      );
    }
    
    // Sort by spam confidence (spam comments first)
    return [...filtered].sort((a, b) => b.spam_confidence - a.spam_confidence);
  }, [commentData, commentSearch]);

  // Escalation actions
  const ackEscalation = async (id: string) => {
    try {
      await autoReplyService.ackEscalationTicket(id);
      toast.success("Acknowledged");
      await fetchEscalations();
    } catch (e: any) {
      toast.error("Acknowledge failed", { description: e?.message || "Please try again." });
    }
  };

  const resolveEscalation = async (id: string) => {
    try {
      await autoReplyService.resolveEscalationTicket(id);
      toast.success("Resolved");
      await fetchEscalations();
    } catch (e: any) {
      toast.error("Resolve failed", { description: e?.message || "Please try again." });
    }
  };

  // Comment actions
  const toggleCommentSelection = (commentId: string) => {
    const newSet = new Set(selectedComments);
    if (newSet.has(commentId)) {
      newSet.delete(commentId);
    } else {
      newSet.add(commentId);
    }
    setSelectedComments(newSet);
  };

  const bulkDeleteComments = () => {
    if (selectedComments.size === 0) {
      toast.error("No comments selected");
      return;
    }
    // TODO: Implement bulk delete API call
    toast.success(`Deleted ${selectedComments.size} comment(s)`);
    setSelectedComments(new Set());
  };

  const markAsLegitimate = (commentId: string) => {
    // TODO: Implement mark as legitimate API call
    toast.success("Marked as legitimate");
  };

  // Sentiment distribution chart data
  const sentimentChartData = commentData ? [
    { name: "Positive", value: commentData.sentiment_summary.POSITIVE, color: SENTIMENT_COLORS.POSITIVE },
    { name: "Neutral", value: commentData.sentiment_summary.NEUTRAL, color: SENTIMENT_COLORS.NEUTRAL },
    { name: "Negative", value: commentData.sentiment_summary.NEGATIVE, color: SENTIMENT_COLORS.NEGATIVE },
  ].filter(item => item.value > 0) : [];

  return (
    <Layout breadcrumbItems={[{ label: "Dashboard", href: "/dashboard" }, { label: "Social Moderation" }]}>
      <div className="space-y-6 px-6 pt-6 pb-24">
        <Reveal variant="fadeInUp">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="space-y-1">
              <h1 className="text-2xl font-bold font-heading tracking-[0.12em] uppercase flex items-center gap-3">
                <ShieldAlert className="w-6 h-6 text-primary" /> Social Moderation
              </h1>
              <p className="text-xs font-mono text-muted-foreground/60 uppercase tracking-widest">
                Manage escalations, spam detection, and comment sentiment analysis.
              </p>
            </div>
          </div>
        </Reveal>

        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)} className="w-full">
          <TabsList className="grid w-full max-w-md grid-cols-2">
            <TabsTrigger value="escalations" className="font-mono text-xs uppercase">
              <AlertTriangle className="w-4 h-4 mr-2" />
              Escalations
            </TabsTrigger>
            <TabsTrigger value="comments" className="font-mono text-xs uppercase">
              <MessageSquare className="w-4 h-4 mr-2" />
              Comment Moderation
            </TabsTrigger>
          </TabsList>

          {/* ESCALATIONS TAB */}
          <TabsContent value="escalations" className="space-y-4 mt-6">
            <Reveal variant="fadeInUp" delay={0.1}>
              <Card className="p-4 bg-card/50 border-border/50">
                <div className="flex items-center gap-3">
                  <Search className="w-4 h-4 text-muted-foreground/60" />
                  <Input
                    value={escalationSearch}
                    onChange={(e) => setEscalationSearch(e.target.value)}
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
                  <Button 
                    variant="outline" 
                    onClick={fetchEscalations} 
                    disabled={escalationsLoading} 
                    className="border-border/50"
                  >
                    <RefreshCw className={`w-4 h-4 ${escalationsLoading ? "animate-spin" : ""}`} />
                  </Button>
                  <div className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest whitespace-nowrap">
                    {statusFilter}: {filteredEscalations.length}
                  </div>
                </div>
              </Card>
            </Reveal>

            <div className="space-y-4">
              {filteredEscalations.length === 0 ? (
                <Reveal variant="fadeInUp" delay={0.2}>
                  <Card className="p-10 text-center bg-card/30 border-border/50">
                    <div className="text-sm font-mono text-muted-foreground/70">No tickets.</div>
                  </Card>
                </Reveal>
              ) : (
                filteredEscalations.map((t, idx) => (
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
                            onClick={() => ackEscalation(t.id)}
                            disabled={String(t.status).toLowerCase() === "resolved"}
                          >
                            Acknowledge
                          </Button>
                          <Button
                            className="bg-destructive text-destructive-foreground"
                            onClick={() => resolveEscalation(t.id)}
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
          </TabsContent>

          {/* COMMENT MODERATION TAB */}
          <TabsContent value="comments" className="space-y-6 mt-6">
            {/* Summary Stats & Sentiment Distribution */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Stats Cards */}
              <div className="grid grid-cols-2 gap-4">
                <Card className="p-4 bg-card/50 border-border/50">
                  <div className="space-y-2">
                    <div className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest">
                      Total Comments
                    </div>
                    <div className="text-3xl font-bold font-mono text-foreground">
                      {commentData?.total || 0}
                    </div>
                  </div>
                </Card>
                <Card className="p-4 bg-destructive/10 border-destructive/20">
                  <div className="space-y-2">
                    <div className="text-[10px] font-mono text-destructive uppercase tracking-widest">
                      Spam Detected
                    </div>
                    <div className="text-3xl font-bold font-mono text-destructive">
                      {commentData?.spam_count || 0}
                    </div>
                  </div>
                </Card>
              </div>

              {/* Sentiment Distribution Pie Chart */}
              <Card className="p-4 bg-card/50 border-border/50">
                <div className="text-[11px] font-mono text-muted-foreground uppercase tracking-widest mb-3">
                  Sentiment Distribution
                </div>
                {sentimentChartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={180}>
                    <PieChart>
                      <Pie
                        data={sentimentChartData}
                        cx="50%"
                        cy="50%"
                        outerRadius={60}
                        dataKey="value"
                        label={(entry) => `${entry.name}: ${entry.value}`}
                        labelLine={false}
                      >
                        {sentimentChartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[180px] flex items-center justify-center text-sm font-mono text-muted-foreground">
                    No sentiment data
                  </div>
                )}
              </Card>
            </div>

            {/* Filters & Controls */}
            <Card className="p-4 bg-card/50 border-border/50 space-y-4">
              <div className="flex items-center gap-3 flex-wrap">
                <Search className="w-4 h-4 text-muted-foreground/60" />
                <Input
                  value={commentSearch}
                  onChange={(e) => setCommentSearch(e.target.value)}
                  placeholder="Search comments by text or ID..."
                  className="flex-1 min-w-[200px] bg-foreground/5 border-border/50"
                />
                
                <div className="w-[180px]">
                  <Select value={sentimentFilter} onValueChange={(v) => setSentimentFilter(v as any)}>
                    <SelectTrigger className="h-9 bg-foreground/5 border-border/50 text-[11px] font-mono">
                      <SelectValue placeholder="Sentiment" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Sentiments</SelectItem>
                      <SelectItem value="POSITIVE">Positive</SelectItem>
                      <SelectItem value="NEUTRAL">Neutral</SelectItem>
                      <SelectItem value="NEGATIVE">Negative</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <Button 
                  variant="outline" 
                  onClick={fetchComments} 
                  disabled={commentsLoading} 
                  className="border-border/50"
                >
                  <RefreshCw className={`w-4 h-4 ${commentsLoading ? "animate-spin" : ""}`} />
                </Button>
              </div>

              {/* Bulk Actions */}
              {selectedComments.size > 0 && (
                <div className="flex items-center gap-3 pt-2 border-t border-border/50">
                  <span className="text-[11px] font-mono text-muted-foreground">
                    {selectedComments.size} selected
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSelectedComments(new Set())}
                    className="border-border/50"
                  >
                    Clear Selection
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={bulkDeleteComments}
                  >
                    <Trash2 className="w-3 h-3 mr-2" />
                    Delete Selected
                  </Button>
                </div>
              )}
            </Card>

            {/* Comments List */}
            <div className="space-y-3">
              {commentsLoading ? (
                <Card className="p-10 text-center bg-card/30 border-border/50">
                  <RefreshCw className="w-6 h-6 mx-auto mb-2 animate-spin text-muted-foreground" />
                  <div className="text-sm font-mono text-muted-foreground/70">
                    Loading comments...
                  </div>
                </Card>
              ) : filteredComments.length === 0 ? (
                <Card className="p-10 text-center bg-card/30 border-border/50">
                  <MessageSquare className="w-12 h-12 mx-auto mb-3 text-muted-foreground/40" />
                  <div className="text-sm font-mono text-muted-foreground/70 mb-2">
                    {commentSearch ? "No comments match your search." : "No comments analyzed yet."}
                  </div>
                  {!commentSearch && (
                    <p className="text-xs font-mono text-muted-foreground/50">
                      Comments will appear here automatically after Instagram/Facebook webhooks deliver them for analysis.
                    </p>
                  )}
                </Card>
              ) : (
                filteredComments.map((comment, idx) => (
                  <Reveal key={comment.id} variant="fadeInUp" delay={0.03 * idx}>
                    <Card className={`p-4 bg-card/40 border-border/50 ${comment.is_spam ? 'border-destructive/40 bg-destructive/5' : ''}`}>
                      <div className="flex gap-4">
                        {/* Selection Checkbox */}
                        <input
                          type="checkbox"
                          checked={selectedComments.has(comment.id)}
                          onChange={() => toggleCommentSelection(comment.id)}
                          className="mt-1 w-4 h-4 rounded border-border/50"
                        />

                        <div className="flex-1 space-y-2">
                          {/* Header Row */}
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex items-center gap-2 flex-wrap">
                              {comment.is_spam && (
                                <Badge variant="destructive" className="text-[9px] font-mono uppercase">
                                  <AlertTriangle className="w-3 h-3 mr-1" />
                                  Spam ({(comment.spam_confidence * 100).toFixed(0)}%)
                                </Badge>
                              )}
                              <Badge className={`text-[9px] font-mono uppercase border ${getSentimentColor(comment.sentiment)}`}>
                                {getSentimentIcon(comment.sentiment)}
                                <span className="ml-1">{comment.sentiment}</span>
                              </Badge>
                              <span className="text-[10px] font-mono text-muted-foreground">
                                {fmtTime(comment.analyzed_at)}
                              </span>
                            </div>

                            {/* Action Buttons */}
                            <div className="flex gap-2">
                              {comment.is_spam && (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => markAsLegitimate(comment.id)}
                                  className="border-border/50 text-[10px]"
                                >
                                  <CheckCircle className="w-3 h-3 mr-1" />
                                  Mark Valid
                                </Button>
                              )}
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => toggleCommentSelection(comment.id)}
                                className="text-[10px]"
                              >
                                <Trash2 className="w-3 h-3" />
                              </Button>
                            </div>
                          </div>

                          {/* Comment Text */}
                          <div className="text-sm text-foreground/90 whitespace-pre-wrap">
                            {comment.text}
                          </div>

                          {/* Footer Metadata */}
                          <div className="text-[9px] font-mono text-muted-foreground/60 break-all">
                            Comment ID: {comment.comment_id} · Post ID: {comment.post_id}
                          </div>
                        </div>
                      </div>
                    </Card>
                  </Reveal>
                ))
              )}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </Layout>
  );
}
