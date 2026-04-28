import { useMemo, useRef, useState, useEffect } from "react";
import { useAuth } from "@/hooks/useAuth";
import { complaintService, Complaint } from "@/services/complaintService";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";
import { 
  AlertCircle, 
  CheckCircle2, 
  Clock, 
  MessageSquare, 
  Send, 
  ShieldAlert, 
  User, 
  Mail, 
  Phone,
  LifeBuoy,
  Paperclip,
  Copy,
  PhoneCall,
  Trash2,
  ExternalLink,
  Edit3,
  Save,
  X
} from "lucide-react";
import { Separator } from "@/components/ui/separator";
import Layout from "@/components/Layout";

const Complaints = () => {
  const { user } = useAuth();
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [selectedComplaint, setSelectedComplaint] = useState<Complaint | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const pageSize = 20;

  // Filters
  const [filterQuery, setFilterQuery] = useState("");
  const [dateFilter, setDateFilter] = useState<"all" | "7d" | "30d">("all");

  // Form State
  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("medium");
  const [attachments, setAttachments] = useState<File[]>([]);
  const attachmentInputRef = useRef<HTMLInputElement | null>(null);
  const [detailEditMode, setDetailEditMode] = useState(false);
  const [detailSubject, setDetailSubject] = useState("");
  const [detailDescription, setDetailDescription] = useState("");
  const [detailPriority, setDetailPriority] = useState("medium");
  const [detailComment, setDetailComment] = useState("");
  const [savingDetail, setSavingDetail] = useState(false);
  const [postingComment, setPostingComment] = useState(false);

  const DESCRIPTION_MAX = 2000;

  const filteredComplaints = useMemo(() => {
    const q = filterQuery.trim().toLowerCase();
    const now = Date.now();
    const cutoff =
      dateFilter === "7d"
        ? now - 7 * 24 * 60 * 60 * 1000
        : dateFilter === "30d"
          ? now - 30 * 24 * 60 * 60 * 1000
          : null;

    return complaints.filter((c) => {
      const created = new Date(c.createdAt).getTime();
      if (cutoff && Number.isFinite(created) && created < cutoff) return false;
      if (!q) return true;
      const hay = [c.id, c.subject, c.description, c.status, c.priority]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return hay.includes(q);
    });
  }, [complaints, dateFilter, filterQuery]);

  const pendingComplaints = useMemo(
    () =>
      filteredComplaints.filter((c) => {
        const s = (c.status || "").toLowerCase();
        return s === "pending" || s === "in_progress" || s === "in progress";
      }),
    [filteredComplaints]
  );

  const resolvedComplaints = useMemo(
    () => {
      return filteredComplaints.filter((c) => {
        const s = (c.status || "").toLowerCase();
        return s === "resolved" || s === "rejected";
      });
    },
    [filteredComplaints]
  );

  const breadcrumbItems = [
    { label: "Dashboard", href: "/dashboard" },
    { label: "Complaints & Support", active: true }
  ];

  useEffect(() => {
    fetchComplaints(true);
  }, []);

  const fetchComplaints = async (reset: boolean = false) => {
    try {
      if (reset) {
        setLoading(true);
        setHasMore(true);
      } else {
        setLoadingMore(true);
      }
      const offset = reset ? 0 : complaints.length;
      const data = await complaintService.getUserComplaintsPaginated(pageSize, offset);
      const sorted = (data || []).sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
      setComplaints((prev) => (reset ? sorted : [...prev, ...sorted]));
      if (!data || data.length < pageSize) setHasMore(false);
    } catch (error) {
      console.error("Failed to fetch complaints:", error);
      toast.error("Failed to load your complaints");
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  const handleDeleteComplaint = async (complaintId: string) => {
    try {
      setDeletingId(complaintId);
      await complaintService.deleteComplaint(complaintId);
      toast.success("Complaint deleted", { description: `Ticket #${complaintId.substring(0, 8)} was removed.` });
      fetchComplaints();
    } catch (e: any) {
      toast.error("Could not delete complaint", {
        description: "Only pending complaints can be deleted. If support has started reviewing it, you can’t remove it anymore.",
      });
    } finally {
      setDeletingId((prev) => (prev === complaintId ? null : prev));
    }
  };

  const openComplaintDetail = (c: Complaint) => {
    setSelectedComplaint(c);
    setDetailEditMode(false);
    setDetailSubject(c.subject || "");
    setDetailDescription(c.description || "");
    setDetailPriority((c.priority || "medium").toLowerCase());
    setDetailComment("");
  };

  const updateComplaintInList = (updated: Complaint) => {
    setComplaints((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
    setSelectedComplaint((prev) => (prev?.id === updated.id ? updated : prev));
  };

  const handleSaveEdits = async () => {
    if (!selectedComplaint) return;
    if ((selectedComplaint.status || "").toLowerCase() !== "pending") return;
    if (!detailSubject.trim() || !detailDescription.trim()) {
      toast.error("Please fill in subject and description.");
      return;
    }
    setSavingDetail(true);
    try {
      await complaintService.updateComplaint(selectedComplaint.id, {
        subject: detailSubject.trim(),
        description: detailDescription.trim(),
        priority: detailPriority,
      });
      const now = new Date().toISOString();
      const next: Complaint = {
        ...selectedComplaint,
        subject: detailSubject.trim(),
        description: detailDescription.trim(),
        priority: detailPriority,
        updatedAt: now,
      };
      updateComplaintInList(next);
      toast.success("Updated", { description: "Your complaint was updated." });
      setDetailEditMode(false);
    } catch {
      toast.error("Could not update complaint", { description: "Please try again in a moment." });
    } finally {
      setSavingDetail(false);
    }
  };

  const handleAddDetailComment = async () => {
    if (!selectedComplaint) return;
    const text = detailComment.trim();
    if (!text) return;
    setPostingComment(true);
    try {
      await complaintService.addComment(selectedComplaint.id, text);
      const now = new Date().toISOString();
      const next: Complaint = {
        ...selectedComplaint,
        comments: [
          ...(selectedComplaint.comments || []),
          { text, author: "You", timestamp: now, isAdmin: false },
        ],
        updatedAt: now,
      };
      updateComplaintInList(next);
      setDetailComment("");
      toast.success("Comment added");
    } catch {
      toast.error("Could not add comment", { description: "Please try again." });
    } finally {
      setPostingComment(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!subject.trim() || !description.trim()) {
      toast.error("Please fill in all required fields");
      return;
    }

    try {
      setSubmitting(true);
      const response = await complaintService.submitComplaint({
        subject: subject.trim(),
        description: description.trim(),
        priority
      });
      
      toast.success("Complaint Submitted", {
        description: `We’re sorry you ran into this. Ticket #${response.id.substring(0, 8)} was created — you’ll receive an acknowledgement email shortly. We aim to respond within 2–3 business days.`
      });
      
      // Reset form
      setSubject("");
      setDescription("");
      setPriority("medium");
      setAttachments([]);

      // Upload attachments (optional)
      if (attachments.length > 0) {
        const toastId = "complaints-attachments";
        toast.loading("Uploading attachments…", {
          id: toastId,
          description: `${attachments.length} file(s)`,
          duration: 600000,
        });
        try {
          for (let i = 0; i < attachments.length; i++) {
            await complaintService.uploadAttachment(response.id, attachments[i]);
          }
          toast.success("Attachments uploaded", {
            id: toastId,
            description: "Your files were added to the complaint.",
            duration: 3000,
          });
        } catch (e) {
          toast.error("Attachment upload failed", {
            id: toastId,
            description: "Your complaint was submitted, but one or more files could not be uploaded.",
            duration: 5000,
          });
        }
      }
      
      // Refresh list
      fetchComplaints(true);
    } catch (error) {
      toast.error("Submission failed", {
        description: "We couldn't submit your complaint. Please try again later."
      });
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case "pending":
        return <Badge variant="outline" className="bg-yellow-500/10 text-yellow-500 border-yellow-500/20"><Clock className="w-3 h-3 mr-1" /> Pending</Badge>;
      case "in_progress":
      case "in progress":
        return <Badge variant="outline" className="bg-blue-500/10 text-blue-500 border-blue-500/20"><Clock className="w-3 h-3 mr-1" /> In Progress</Badge>;
      case "resolved":
        return <Badge variant="outline" className="bg-green-500/10 text-green-500 border-green-500/20"><CheckCircle2 className="w-3 h-3 mr-1" /> Resolved</Badge>;
      case "rejected":
        return <Badge variant="outline" className="bg-red-500/10 text-red-500 border-red-500/20"><AlertCircle className="w-3 h-3 mr-1" /> Rejected</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <Layout breadcrumbItems={[{ label: "Dashboard", href: "/dashboard" }, { label: "Support" }]}>
      <div className="space-y-8 max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Support Center</h1>
            <p className="text-muted-foreground mt-1">Submit technical issues or track existing support requests.</p>
          </div>
          
          <div className="flex items-center gap-3">
            <Card className="bg-foreground/5 border-border/50 p-2 px-4 h-12 flex items-center gap-3">
              <a
                className="flex items-center gap-2 text-xs font-medium hover:underline"
                href="mailto:support@raamp.ai"
              >
                <Mail className="w-3.5 h-3.5 text-primary" />
                <span>support@raamp.ai</span>
              </a>
              <Separator orientation="vertical" className="h-4" />
              <div className="group flex items-center gap-2 text-xs font-medium">
                <Phone className="w-3.5 h-3.5 text-primary" />
                <span className="select-text">+1 (800) RAAMP-AI</span>

                <div className="flex items-center gap-2 md:opacity-0 md:pointer-events-none md:group-hover:opacity-100 md:group-hover:pointer-events-auto md:group-focus-within:opacity-100 md:group-focus-within:pointer-events-auto transition-opacity">
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    className="h-7 px-2 text-[10px]"
                    onClick={() => {
                      const value = "+1 (800) RAAMP-AI";
                      navigator.clipboard
                        .writeText(value)
                        .then(() => toast.success("Phone copied", { description: value }))
                        .catch(() => toast.error("Could not copy phone number"));
                    }}
                  >
                    <Copy className="w-3 h-3 mr-1" />
                    Copy
                  </Button>
                  <Button
                    asChild
                    type="button"
                    size="sm"
                    variant="default"
                    className="h-7 px-2 text-[10px]"
                  >
                    <a href="tel:+18007226724">
                      <PhoneCall className="w-3 h-3 mr-1" />
                      Call
                    </a>
                  </Button>
                </div>
              </div>
            </Card>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Submission Form */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="lg:col-span-1"
          >
                <Card className="border-border/50 bg-card/50 backdrop-blur-sm sticky top-0">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-xl">
                      <LifeBuoy className="w-5 h-5 text-primary" />
                      New Complaint
                    </CardTitle>
                    <CardDescription>File a formal record of your issue.</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                      <div className="space-y-2">
                        <label className="text-sm font-medium">
                          Subject <span className="text-red-500">*</span>
                        </label>
                        <Input 
                          placeholder="Brief subject of your complaint"
                          value={subject}
                          onChange={(e) => setSubject(e.target.value)}
                          className="bg-background/50 border-border/50 focus:border-primary/50"
                        />
                      </div>
                      
                      <div className="space-y-2">
                        <div className="flex items-center justify-between gap-3">
                          <label className="text-sm font-medium">
                            Description <span className="text-red-500">*</span>
                          </label>
                          <span className="text-[10px] font-mono text-muted-foreground">
                            {description.length}/{DESCRIPTION_MAX}
                          </span>
                        </div>
                        <Textarea 
                          placeholder="Describe the issue in detail. If it happened on a specific page, please mention it."
                          className="min-h-[140px] bg-background/50 border-border/50 focus:border-primary/50 resize-none"
                          value={description}
                          maxLength={DESCRIPTION_MAX}
                          onChange={(e) => setDescription(e.target.value)}
                        />
                      </div>

                      <div className="space-y-2">
                        <label className="text-sm font-medium">Attachments (optional)</label>
                        <input
                          ref={attachmentInputRef}
                          type="file"
                          className="hidden"
                          multiple
                          accept="image/*,application/pdf"
                          onChange={(e) => {
                            const files = Array.from(e.target.files || []);
                            if (files.length === 0) return;
                            const maxMb = 10;
                            const ok = files.filter((f) => f.size <= maxMb * 1024 * 1024);
                            const rejected = files.length - ok.length;
                            if (rejected > 0) {
                              toast.error("Some files are too large", {
                                description: `Max ${maxMb}MB per file.`,
                              });
                            }
                            setAttachments((prev) => [...prev, ...ok].slice(0, 5));
                            e.currentTarget.value = "";
                          }}
                        />
                        <div className="flex items-center gap-2">
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            className="h-9"
                            onClick={() => attachmentInputRef.current?.click()}
                          >
                            <Paperclip className="w-4 h-4 mr-2" />
                            Add attachment
                          </Button>
                          {attachments.length > 0 && (
                            <span className="text-[10px] font-mono text-muted-foreground">
                              {attachments.length} file(s) selected (max 5)
                            </span>
                          )}
                        </div>
                        {attachments.length > 0 && (
                          <div className="space-y-1">
                            {attachments.map((f, idx) => (
                              <div key={`${f.name}-${idx}`} className="flex items-center justify-between text-[11px]">
                                <span className="truncate text-muted-foreground">{f.name}</span>
                                <Button
                                  type="button"
                                  size="sm"
                                  variant="ghost"
                                  className="h-7 px-2 text-[10px]"
                                  onClick={() => setAttachments((prev) => prev.filter((_, i) => i !== idx))}
                                >
                                  Remove
                                </Button>
                              </div>
                            ))}
                          </div>
                        )}
                        <p className="text-[10px] text-muted-foreground">
                          Allowed: images/PDF. Max 10MB per file.
                        </p>
                      </div>

                      <div className="space-y-2">
                        <label className="text-sm font-medium">Priority</label>
                        <div className="flex gap-2">
                          {["low", "medium", "high"].map((p) => (
                            <Button
                              key={p}
                              type="button"
                              variant={priority === p ? "default" : "outline"}
                              size="sm"
                              onClick={() => setPriority(p)}
                              className="capitalize flex-1 h-9"
                            >
                              {p}
                            </Button>
                          ))}
                        </div>
                      </div>

                      <Button 
                        type="submit" 
                        className="w-full mt-6 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold h-11"
                        disabled={submitting}
                      >
                        {submitting ? "Submitting..." : (
                          <>
                            Submit Complaint
                            <Send className="w-4 h-4 ml-2" />
                          </>
                        )}
                      </Button>
                    </form>
                  </CardContent>
                  <CardFooter className="pt-0 flex flex-col items-start bg-foreground/5 p-4 rounded-b-xl border-t border-border/10">
                    <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest mb-1">Authenticated As</p>
                    <div className="flex items-center gap-2">
                      <div className="w-5 h-5 rounded-full bg-primary/20 flex items-center justify-center">
                        <User className="w-3 h-3 text-primary" />
                      </div>
                      <span className="text-xs font-medium">{user?.email}</span>
                    </div>
                  </CardFooter>
                </Card>
          </motion.div>

              {/* Complaints List/History */}
              <div className="lg:col-span-2 space-y-6">
                <Tabs defaultValue="all" className="w-full">
                  <div className="flex items-center justify-between mb-4">
                    <TabsList className="bg-foreground/5 border border-border/50 p-1">
                      <TabsTrigger
                        value="all"
                        className="data-[state=active]:bg-background data-[state=active]:shadow-sm data-[state=active]:border data-[state=active]:border-border/60"
                      >
                        Recent Issues
                      </TabsTrigger>
                      <TabsTrigger
                        value="pending"
                        className="data-[state=active]:bg-background data-[state=active]:shadow-sm data-[state=active]:border data-[state=active]:border-border/60"
                      >
                        Open
                      </TabsTrigger>
                      <TabsTrigger
                        value="resolved"
                        className="data-[state=active]:bg-background data-[state=active]:shadow-sm data-[state=active]:border data-[state=active]:border-border/60"
                      >
                        Resolved
                      </TabsTrigger>
                    </TabsList>
                    <div className="flex items-center gap-2">
                      <Input
                        value={filterQuery}
                        onChange={(e) => setFilterQuery(e.target.value)}
                        placeholder="Search tickets…"
                        className="h-9 w-[220px] bg-foreground/5 border-border/50"
                      />
                      <select
                        value={dateFilter}
                        onChange={(e) => setDateFilter(e.target.value as any)}
                        className="h-9 rounded-md border border-border/50 bg-background text-foreground px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/40"
                      >
                        <option value="all">All time</option>
                        <option value="7d">Last 7 days</option>
                        <option value="30d">Last 30 days</option>
                      </select>
                    </div>
                  </div>

                  <TabsContent value="all" className="space-y-4">
                    <AnimatePresence mode="popLayout">
                      {loading ? (
                        <div className="flex items-center justify-center p-12">
                          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                        </div>
                      ) : filteredComplaints.length === 0 ? (
                        <Card className="border-dashed border-border/50 bg-transparent text-center p-12">
                          <div className="bg-foreground/5 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4">
                            <MessageSquare className="w-6 h-6 text-muted-foreground" />
                          </div>
                          <h3 className="text-lg font-semibold">No complaints found</h3>
                          <p className="text-muted-foreground text-sm max-w-[250px] mx-auto mt-1">If you have an issue, use the form on the left to file a record.</p>
                        </Card>
                      ) : (
                        filteredComplaints.map((complaint, idx) => (
                          <motion.div
                            key={complaint.id}
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: idx * 0.05 }}
                          >
                            <Card
                              className="border-border/50 bg-card/30 hover:bg-card/50 transition-colors group cursor-pointer"
                              onClick={() => openComplaintDetail(complaint)}
                              role="button"
                              tabIndex={0}
                            >
                              <CardHeader className="pb-3">
                                <div className="flex justify-between items-start">
                                  <div className="space-y-1">
                                    <div className="flex items-center gap-2">
                                      <h3 className="font-bold text-lg">{complaint.subject}</h3>
                                      <Badge variant="outline" className="text-[10px] opacity-70">
                                        #{complaint.id.substring(0, 8)}
                                      </Badge>
                                    </div>
                                    <p className="text-xs text-muted-foreground">
                                      Submitted on {new Date(complaint.createdAt).toLocaleDateString()} at {new Date(complaint.createdAt).toLocaleTimeString()}
                                    </p>
                                  </div>
                                  {getStatusBadge(complaint.status)}
                                </div>
                              </CardHeader>
                              <CardContent className="pb-4">
                                <p className="text-sm text-foreground/80 line-clamp-2 italic">"{complaint.description}"</p>
                                
                                {complaint.adminResponse && (
                                  <div className="mt-4 p-4 rounded-lg bg-primary/10 border border-primary/20">
                                    <div className="flex items-center gap-2 mb-2">
                                      <ShieldAlert className="w-4 h-4 text-primary" />
                                      <span className="text-xs font-bold text-primary uppercase tracking-wider">RAAMP Support Response</span>
                                    </div>
                                    <p className="text-sm font-medium">{complaint.adminResponse}</p>
                                  </div>
                                )}
                              </CardContent>
                              <CardFooter className="pt-0 flex justify-between border-t border-border/10 mt-2 p-4">
                                <div className="flex items-center gap-3">
                                  <div className="flex items-center gap-1 text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                                    <AlertCircle className="w-3 h-3" />
                                    Priority: {complaint.priority}
                                  </div>
                                </div>
                                <div className="flex items-center gap-2">
                                  {(complaint.status || "").toLowerCase() === "pending" ? (
                                    <AlertDialog>
                                      <AlertDialogTrigger asChild>
                                        <Button
                                          type="button"
                                          size="sm"
                                          variant="outline"
                                          className="h-8 px-2 text-[10px]"
                                          disabled={deletingId === complaint.id}
                                          title="Delete this complaint"
                                        >
                                          <Trash2 className="w-3.5 h-3.5 mr-1" />
                                          Delete
                                        </Button>
                                      </AlertDialogTrigger>
                                      <AlertDialogContent>
                                        <AlertDialogHeader>
                                          <AlertDialogTitle>Delete this complaint?</AlertDialogTitle>
                                          <AlertDialogDescription>
                                            This will permanently remove ticket #{complaint.id.substring(0, 8)}. You can only delete complaints that are still pending.
                                          </AlertDialogDescription>
                                        </AlertDialogHeader>
                                        <AlertDialogFooter>
                                          <AlertDialogCancel>Cancel</AlertDialogCancel>
                                          <AlertDialogAction onClick={() => handleDeleteComplaint(complaint.id)}>
                                            Delete
                                          </AlertDialogAction>
                                        </AlertDialogFooter>
                                      </AlertDialogContent>
                                    </AlertDialog>
                                  ) : (
                                    <Button
                                      type="button"
                                      size="sm"
                                      variant="outline"
                                      className="h-8 px-2 text-[10px] opacity-60 cursor-not-allowed"
                                      disabled
                                      title="Only pending complaints can be deleted"
                                    >
                                      <Trash2 className="w-3.5 h-3.5 mr-1" />
                                      Delete
                                    </Button>
                                  )}
                                </div>
                              </CardFooter>
                            </Card>
                          </motion.div>
                        ))
                      )}
                    </AnimatePresence>
                    {!loading && hasMore && (
                      <div className="pt-2">
                        <Button
                          variant="outline"
                          className="w-full"
                          disabled={loadingMore}
                          onClick={() => fetchComplaints(false)}
                        >
                          {loadingMore ? "Loading…" : "Load more"}
                        </Button>
                      </div>
                    )}
                  </TabsContent>

                  <TabsContent value="pending" className="space-y-4">
                    <AnimatePresence mode="popLayout">
                      {loading ? (
                        <div className="flex items-center justify-center p-12">
                          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                        </div>
                      ) : pendingComplaints.length === 0 ? (
                        <Card className="border-dashed border-border/50 bg-transparent text-center p-12">
                          <div className="bg-foreground/5 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4">
                            <Clock className="w-6 h-6 text-muted-foreground" />
                          </div>
                          <h3 className="text-lg font-semibold">No open tickets</h3>
                          <p className="text-muted-foreground text-sm max-w-[320px] mx-auto mt-1">
                            You’re all caught up. If something breaks, file a new complaint and we’ll jump on it.
                          </p>
                        </Card>
                      ) : (
                        pendingComplaints.map((complaint, idx) => (
                          <motion.div
                            key={complaint.id}
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: idx * 0.05 }}
                          >
                            <Card
                              className="border-border/50 bg-card/30 hover:bg-card/50 transition-colors group cursor-pointer"
                              onClick={() => openComplaintDetail(complaint)}
                              role="button"
                              tabIndex={0}
                            >
                              <CardHeader className="pb-3">
                                <div className="flex justify-between items-start">
                                  <div className="space-y-1">
                                    <div className="flex items-center gap-2">
                                      <h3 className="font-bold text-lg">{complaint.subject}</h3>
                                      <Badge variant="outline" className="text-[10px] opacity-70">
                                        #{complaint.id.substring(0, 8)}
                                      </Badge>
                                    </div>
                                    <p className="text-xs text-muted-foreground">
                                      Submitted on {new Date(complaint.createdAt).toLocaleDateString()} at{" "}
                                      {new Date(complaint.createdAt).toLocaleTimeString()}
                                    </p>
                                  </div>
                                  {getStatusBadge(complaint.status)}
                                </div>
                              </CardHeader>
                              <CardContent className="pb-4">
                                <p className="text-sm text-foreground/80 line-clamp-2 italic">"{complaint.description}"</p>
                              </CardContent>
                              <CardFooter className="pt-0 flex justify-between border-t border-border/10 mt-2 p-4">
                                <div className="flex items-center gap-3">
                                  <div className="flex items-center gap-1 text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                                    <AlertCircle className="w-3 h-3" />
                                    Priority: {complaint.priority}
                                  </div>
                                </div>
                                <div className="flex items-center gap-2">
                                  {(complaint.status || "").toLowerCase() === "pending" ? (
                                    <AlertDialog>
                                      <AlertDialogTrigger asChild>
                                        <Button
                                          type="button"
                                          size="sm"
                                          variant="outline"
                                          className="h-8 px-2 text-[10px]"
                                          disabled={deletingId === complaint.id}
                                          title="Delete this complaint"
                                        >
                                          <Trash2 className="w-3.5 h-3.5 mr-1" />
                                          Delete
                                        </Button>
                                      </AlertDialogTrigger>
                                      <AlertDialogContent>
                                        <AlertDialogHeader>
                                          <AlertDialogTitle>Delete this complaint?</AlertDialogTitle>
                                          <AlertDialogDescription>
                                            This will permanently remove ticket #{complaint.id.substring(0, 8)}. You can only delete complaints that are still pending.
                                          </AlertDialogDescription>
                                        </AlertDialogHeader>
                                        <AlertDialogFooter>
                                          <AlertDialogCancel>Cancel</AlertDialogCancel>
                                          <AlertDialogAction onClick={() => handleDeleteComplaint(complaint.id)}>
                                            Delete
                                          </AlertDialogAction>
                                        </AlertDialogFooter>
                                      </AlertDialogContent>
                                    </AlertDialog>
                                  ) : (
                                    <Button
                                      type="button"
                                      size="sm"
                                      variant="outline"
                                      className="h-8 px-2 text-[10px] opacity-60 cursor-not-allowed"
                                      disabled
                                      title="Only pending complaints can be deleted"
                                    >
                                      <Trash2 className="w-3.5 h-3.5 mr-1" />
                                      Delete
                                    </Button>
                                  )}
                                </div>
                              </CardFooter>
                            </Card>
                          </motion.div>
                        ))
                      )}
                    </AnimatePresence>
                  </TabsContent>

                  <TabsContent value="resolved" className="space-y-4">
                    <AnimatePresence mode="popLayout">
                      {loading ? (
                        <div className="flex items-center justify-center p-12">
                          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                        </div>
                      ) : resolvedComplaints.length === 0 ? (
                        <Card className="border-dashed border-border/50 bg-transparent text-center p-12">
                          <div className="bg-foreground/5 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4">
                            <CheckCircle2 className="w-6 h-6 text-muted-foreground" />
                          </div>
                          <h3 className="text-lg font-semibold">No resolved tickets yet</h3>
                          <p className="text-muted-foreground text-sm max-w-[320px] mx-auto mt-1">
                            Once a support request is closed, it will show up here with the resolution details.
                          </p>
                        </Card>
                      ) : (
                        resolvedComplaints.map((complaint, idx) => (
                          <motion.div
                            key={complaint.id}
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: idx * 0.05 }}
                          >
                            <Card
                              className="border-border/50 bg-card/30 hover:bg-card/50 transition-colors group cursor-pointer"
                              onClick={() => openComplaintDetail(complaint)}
                              role="button"
                              tabIndex={0}
                            >
                              <CardHeader className="pb-3">
                                <div className="flex justify-between items-start">
                                  <div className="space-y-1">
                                    <div className="flex items-center gap-2">
                                      <h3 className="font-bold text-lg">{complaint.subject}</h3>
                                      <Badge variant="outline" className="text-[10px] opacity-70">
                                        #{complaint.id.substring(0, 8)}
                                      </Badge>
                                    </div>
                                    <p className="text-xs text-muted-foreground">
                                      Submitted on {new Date(complaint.createdAt).toLocaleDateString()} at{" "}
                                      {new Date(complaint.createdAt).toLocaleTimeString()}
                                    </p>
                                  </div>
                                  {getStatusBadge(complaint.status)}
                                </div>
                              </CardHeader>
                              <CardContent className="pb-4">
                                <p className="text-sm text-foreground/80 line-clamp-2 italic">"{complaint.description}"</p>

                                {complaint.adminResponse && (
                                  <div className="mt-4 p-4 rounded-lg bg-primary/10 border border-primary/20">
                                    <div className="flex items-center gap-2 mb-2">
                                      <ShieldAlert className="w-4 h-4 text-primary" />
                                      <span className="text-xs font-bold text-primary uppercase tracking-wider">
                                        RAAMP Support Response
                                      </span>
                                    </div>
                                    <p className="text-sm font-medium">{complaint.adminResponse}</p>
                                  </div>
                                )}
                              </CardContent>
                              <CardFooter className="pt-0 flex justify-between border-t border-border/10 mt-2 p-4">
                                <div className="flex items-center gap-3">
                                  <div className="flex items-center gap-1 text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                                    <AlertCircle className="w-3 h-3" />
                                    Priority: {complaint.priority}
                                  </div>
                                </div>
                              </CardFooter>
                            </Card>
                          </motion.div>
                        ))
                      )}
                    </AnimatePresence>
                  </TabsContent>
                </Tabs>
              </div>
        </div>

        {/* Complaint Detail Modal */}
        <Dialog open={!!selectedComplaint} onOpenChange={(v) => !v && setSelectedComplaint(null)}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle className="flex items-center justify-between gap-3">
                <span className="truncate">
                  Ticket #{selectedComplaint?.id?.substring(0, 8)} · {selectedComplaint?.subject}
                </span>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => setSelectedComplaint(null)}
                  title="Close"
                >
                  <X className="w-4 h-4" />
                </Button>
              </DialogTitle>
            </DialogHeader>

            {selectedComplaint && (
              <div className="space-y-4">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    {getStatusBadge(selectedComplaint.status)}
                    <Badge variant="outline" className="text-[10px] font-mono opacity-70">
                      Priority: {selectedComplaint.priority}
                    </Badge>
                  </div>
                  {(selectedComplaint.status || "").toLowerCase() === "pending" && (
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-xs font-mono gap-2"
                      onClick={() => setDetailEditMode((v) => !v)}
                      disabled={savingDetail}
                    >
                      <Edit3 className="w-4 h-4" />
                      {detailEditMode ? "Cancel edit" : "Edit"}
                    </Button>
                  )}
                </div>

                <Card className="p-4 bg-foreground/5 border-border/50 space-y-3">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <Label>Subject</Label>
                      <Input
                        value={detailSubject}
                        onChange={(e) => setDetailSubject(e.target.value)}
                        disabled={!detailEditMode}
                        className="bg-background/50 border-border/50"
                      />
                    </div>
                    <div className="space-y-1">
                      <Label>Priority</Label>
                      <div className="flex gap-2">
                        {["low", "medium", "high"].map((p) => (
                          <Button
                            key={p}
                            type="button"
                            variant={detailPriority === p ? "default" : "outline"}
                            size="sm"
                            onClick={() => detailEditMode && setDetailPriority(p)}
                            className="capitalize flex-1 h-9"
                            disabled={!detailEditMode}
                          >
                            {p}
                          </Button>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="space-y-1">
                    <Label>Description</Label>
                    <Textarea
                      value={detailDescription}
                      onChange={(e) => setDetailDescription(e.target.value)}
                      disabled={!detailEditMode}
                      className="min-h-[120px] bg-background/50 border-border/50"
                    />
                  </div>

                  {detailEditMode && (
                    <Button onClick={handleSaveEdits} disabled={savingDetail} className="w-full">
                      <Save className="w-4 h-4 mr-2" />
                      {savingDetail ? "Saving…" : "Save changes"}
                    </Button>
                  )}
                </Card>

                {/* Attachments */}
                <Card className="p-4 border-border/50">
                  <div className="font-semibold text-sm mb-2">Attachments</div>
                  {(selectedComplaint.attachments || []).length === 0 ? (
                    <div className="text-sm text-muted-foreground">No attachments uploaded.</div>
                  ) : (
                    <div className="space-y-2">
                      {(selectedComplaint.attachments || []).map((u) => (
                        <div key={u} className="flex items-center justify-between gap-3 text-sm">
                          <div className="truncate text-muted-foreground">{u.split("/").slice(-1)[0]}</div>
                          <Button asChild size="sm" variant="outline" className="gap-2">
                            <a href={u} target="_blank" rel="noreferrer">
                              <ExternalLink className="w-4 h-4" />
                              Open
                            </a>
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                </Card>

                {/* Comments */}
                <Card className="p-4 border-border/50 space-y-3">
                  <div className="font-semibold text-sm">Comments</div>
                  {(selectedComplaint.comments || []).length === 0 ? (
                    <div className="text-sm text-muted-foreground">No comments yet.</div>
                  ) : (
                    <div className="space-y-2 max-h-[180px] overflow-y-auto pr-1">
                      {(selectedComplaint.comments || []).map((c, i) => (
                        <div
                          key={`${c.timestamp}-${i}`}
                          className={`p-3 rounded-lg border text-sm ${
                            c.isAdmin ? "bg-primary/5 border-primary/20" : "bg-foreground/[0.02] border-border/50"
                          }`}
                        >
                          <div className="flex items-center justify-between text-[10px] font-mono text-muted-foreground mb-1">
                            <span>{c.author}{c.isAdmin ? " (Support)" : ""}</span>
                            <span>{new Date(c.timestamp).toLocaleString()}</span>
                          </div>
                          <div className="text-foreground/90 whitespace-pre-wrap">{c.text}</div>
                        </div>
                      ))}
                    </div>
                  )}
                  <div className="space-y-2">
                    <Textarea
                      value={detailComment}
                      onChange={(e) => setDetailComment(e.target.value)}
                      placeholder="Add a comment…"
                      className="min-h-[80px]"
                    />
                    <Button
                      variant="outline"
                      onClick={handleAddDetailComment}
                      disabled={postingComment || !detailComment.trim()}
                      className="w-full"
                    >
                      {postingComment ? "Posting…" : "Add comment"}
                    </Button>
                  </div>
                </Card>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
};

export default Complaints;
