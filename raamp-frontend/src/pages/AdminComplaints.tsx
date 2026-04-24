import { useEffect, useMemo, useState } from "react";
import Layout from "@/components/Layout";
import { Link } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { apiClient } from "@/services/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { MESSAGES } from "@/constants/messages";

type Complaint = {
  id: string;
  userId: string;
  subject: string;
  description: string;
  status: string;
  priority: string;
  adminResponse?: string;
  createdAt: string;
};

const AdminComplaints = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [items, setItems] = useState<Complaint[]>([]);
  const [filter, setFilter] = useState("");

  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [adminResponse, setAdminResponse] = useState("");
  const [comment, setComment] = useState("");

  // Type guard: Check if user has is_admin field
  const isAdmin = Boolean(user && 'is_admin' in user && user.is_admin);

  const filtered = useMemo(() => {
    const q = filter.trim().toLowerCase();
    if (!q) return items;
    return items.filter((c) => {
      return (
        c.id.toLowerCase().includes(q) ||
        c.userId.toLowerCase().includes(q) ||
        (c.subject || "").toLowerCase().includes(q) ||
        (c.status || "").toLowerCase().includes(q)
      );
    });
  }, [items, filter]);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const data = await apiClient.get<Complaint[]>("/complaints/admin?limit=100&offset=0");
      setItems(data || []);
    } catch {
      toast.error("Load Failed", { description: MESSAGES.COMPLAINTS.LOAD_FAILED });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const [targetId, setTargetId] = useState("");

  const loadOne = async () => {
    const id = targetId.trim();
    if (!id) return;
    try {
      const data = await apiClient.get<Complaint[]>(`/complaints/admin?limit=1&offset=0&q=${encodeURIComponent(id)}`);
      const found = (data || [])[0];
      if (!found) {
        toast.error("Not Found", { description: MESSAGES.COMPLAINTS.NOT_FOUND });
        return;
      }
      setItems((prev) => {
        const exists = prev.some((p) => p.id === found.id);
        return exists ? prev : [found, ...prev];
      });
      toast.success("Ticket Loaded", { description: MESSAGES.COMPLAINTS.LOADED(found.id) });
    } catch {
      toast.error("Could not load complaint");
    }
  };

  const setStatus = async (id: string, status: string) => {
    try {
      setUpdatingId(id);
      await apiClient.post(`/complaints/admin/${id}/status`, {
        status,
        adminResponse,
        comment,
      });
      toast.success(MESSAGES.COMPLAINTS.STATUS_UPDATE_SUCCESS);
    } catch {
      toast.error("Update Failed", { description: MESSAGES.COMPLAINTS.UPDATE_FAILED });
    } finally {
      setUpdatingId(null);
    }
  };

  if (!isAdmin) {
    return (
      <Layout breadcrumbItems={[{ label: "Dashboard", href: "/dashboard" }, { label: "Admin Support" }]}>
        <Card className="p-6 max-w-xl mx-auto">
          <p className="text-sm">Forbidden.</p>
        </Card>
      </Layout>
    );
  }

  return (
    <Layout breadcrumbItems={[{ label: "Admin" }, { label: "Complaints" }]}>
      <div className="max-w-3xl mx-auto space-y-4">
        <Card className="p-5 space-y-3">
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <div className="flex items-center gap-2">
              <Badge variant="outline">Admin</Badge>
              <span className="text-sm font-medium">Complaints</span>
            </div>
            <Button variant="outline" onClick={fetchAll} disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Loading...
                </>
              ) : (
                "Refresh"
              )}
            </Button>
          </div>

          <div className="grid gap-2">
            <Input value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="Filter (id/user/subject/status)" />
          </div>
        </Card>

        <Card className="p-5 space-y-3">
          <div className="grid gap-2">
            <Input value={targetId} onChange={(e) => setTargetId(e.target.value)} placeholder="Complaint ID (to manage)" />
            <Button variant="outline" onClick={loadOne}>
              Load complaint (needs backend endpoint)
            </Button>
          </div>

          <div className="grid gap-2">
            <Textarea value={adminResponse} onChange={(e) => setAdminResponse(e.target.value)} placeholder="Admin response (optional)" />
            <Input value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Internal comment / status update note (optional)" />
          </div>

          <div className="flex gap-2 flex-wrap">
            <Button
              disabled={!targetId.trim() || updatingId === targetId.trim()}
              onClick={() => setStatus(targetId.trim(), "in_progress")}
            >
              {updatingId === targetId.trim() ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Updating...</>
              ) : "Set In Progress"}
            </Button>
            <Button
              disabled={!targetId.trim() || updatingId === targetId.trim()}
              variant="outline"
              onClick={() => setStatus(targetId.trim(), "resolved")}
            >
              {updatingId === targetId.trim() ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Updating...</>
              ) : "Resolve"}
            </Button>
            <Button
              disabled={!targetId.trim() || updatingId === targetId.trim()}
              variant="destructive"
              onClick={() => setStatus(targetId.trim(), "rejected")}
            >
              {updatingId === targetId.trim() ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Updating...</>
              ) : "Reject"}
            </Button>
          </div>
        </Card>

        {filtered.length > 0 && (
          <Card className="p-5">
            <div className="text-sm font-medium mb-2">Loaded items</div>
            <div className="space-y-2">
              {filtered.map((c) => (
                <div key={c.id} className="text-xs border border-border/50 rounded p-3">
                  <div className="flex items-center justify-between gap-3">
                    <div className="font-mono">#{c.id}</div>
                    <Badge variant="outline">{c.status}</Badge>
                  </div>
                  <div className="mt-1 text-muted-foreground">{c.subject}</div>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    </Layout>
  );
};

export default AdminComplaints;

