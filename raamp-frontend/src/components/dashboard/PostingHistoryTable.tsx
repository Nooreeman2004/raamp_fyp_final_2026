import React, { useState, useMemo } from "react";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/status-badge";
import { Input } from "@/components/ui/input";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import {
    Tabs,
    TabsList,
    TabsTrigger,
} from "@/components/ui/tabs";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import {
    Search,
    RefreshCcw,
    Filter,
    Globe,
    AlertTriangle,
    Instagram,
    Facebook,
    Expand,
    BookOpen,
    Camera,
    Image as ImageIcon
} from "lucide-react";
import { format } from "date-fns";
import { mapBackendErrorToUI, formatHistoryTimestamp, getTimezone } from "@/lib/history-utils";
import type { PostHistoryItem } from "@/types/instagram.types";

interface PostingHistoryTableProps {
    posts: PostHistoryItem[];
    searchQuery?: string;
    platformFilter?: string;
}

export const PostingHistoryTable: React.FC<PostingHistoryTableProps> = ({
    posts,
    searchQuery = "",
    platformFilter = "all"
}) => {
    const [activeTab, setActiveTab] = useState("all");
    const [selectedPost, setSelectedPost] = useState<PostHistoryItem | null>(null);

    const getPlatformPillClasses = (platform: string) => {
        const p = String(platform || "").toLowerCase();
        if (p === "facebook") {
            return {
                wrap: "bg-[#1877F2]/10 border-[#1877F2]/30",
                icon: "text-[#1877F2]",
                text: "text-[#1877F2]"
            };
        }
        // default: instagram
        return {
            wrap: "bg-pink-500/10 border-pink-500/30",
            icon: "text-pink-500",
            text: "text-pink-600 dark:text-pink-400"
        };
    };

    // Filter logic
    const filteredPosts = useMemo(() => {
        return posts.filter((post) => {
            // Tab filtering
            if (activeTab !== "all") {
                const s = post.status.toLowerCase();
                const isSuccess = s === "published" || s === "posted" || s === "success";
                const isPending = s === "pending" || s === "queued" || s === "scheduled" || s === "processing";
                const isFailed = s === "failed" || s === "error";

                if (activeTab === "success" && !isSuccess) return false;
                if (activeTab === "pending" && !isPending) return false;
                if (activeTab === "failed" && !isFailed) return false;
            }

            // Platform filtering
            if (platformFilter !== "all" && post.platform?.toLowerCase() !== platformFilter.toLowerCase()) return false;

            // Search filtering
            if (searchQuery) {
                const q = searchQuery.toLowerCase();
                return (
                    post.instagram_post_id?.toLowerCase().includes(q) ||
                    post.internal_id?.toLowerCase().includes(q) ||
                    post.caption?.toLowerCase().includes(q) ||
                    post.error_message?.toLowerCase().includes(q)
                );
            }

            return true;
        });
    }, [posts, activeTab, platformFilter, searchQuery]);

    if (posts.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-20 bg-foreground/5 border border-dashed border-border/50 rounded-xl">
                <Globe className="w-12 h-12 text-white/20 mb-4" />
                <h3 className="text-xl font-medium text-white/90">No posting history yet</h3>
                <p className="text-muted-foreground/60 mt-1">Activity logs will appear here once you post.</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header / Tabs */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full md:w-auto">
                    <TabsList className="bg-foreground/5 border border-border/50 p-1 h-10">
                        <TabsTrigger value="all" className="text-xs px-4">All Logs</TabsTrigger>
                        <TabsTrigger value="success" className="text-xs px-4 data-[state=active]:text-emerald-400">Success</TabsTrigger>
                        <TabsTrigger value="pending" className="text-xs px-4 data-[state=active]:text-amber-400">Pending</TabsTrigger>
                        <TabsTrigger value="failed" className="text-xs px-4 data-[state=active]:text-red-400">Failed</TabsTrigger>
                    </TabsList>
                </Tabs>

                <div className="flex items-center gap-2">
                    <span className="text-[10px] text-white/30 font-bold uppercase tracking-widest">
                        Timezone: {getTimezone()}
                    </span>
                </div>
            </div>

            {/* Table */}
            <div className="bg-white/[0.01] border border-border/50 rounded-xl overflow-hidden shadow-2xl">
                <Table>
                    <TableHeader className="bg-white/[0.04] border-b border-border/50">
                        <TableRow className="hover:bg-transparent h-14">
                            <TableHead className="w-[200px] text-[12px] uppercase font-black text-muted-foreground tracking-[0.15em] pl-6">Post Identifier</TableHead>
                            <TableHead className="w-[110px] text-[12px] uppercase font-black text-muted-foreground tracking-[0.15em] text-center">Platform</TableHead>
                            <TableHead className="w-[180px] text-[12px] uppercase font-black text-muted-foreground tracking-[0.15em]">Published At</TableHead>
                            <TableHead className="w-[140px] text-[12px] uppercase font-black text-muted-foreground tracking-[0.15em]">Current Status</TableHead>
                            <TableHead className="text-[12px] uppercase font-black text-muted-foreground tracking-[0.15em]">Content Summary</TableHead>
                            <TableHead className="w-[80px] text-right text-[12px] uppercase font-black text-muted-foreground tracking-[0.15em] pr-6">Detail</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {filteredPosts.length === 0 ? (
                            <TableRow className="hover:bg-transparent">
                                <TableCell colSpan={6} className="h-40 text-center text-white/30 italic text-sm font-light">
                                    No records found matching your current filters.
                                </TableCell>
                            </TableRow>
                        ) : (
                            filteredPosts.map((post) => {
                                const platform = post.platform?.toLowerCase() || "instagram";
                                const isStory = !post.caption;
                                const pill = getPlatformPillClasses(platform);
                                const summary = post.caption
                                    ? (post.caption.length > 80 ? post.caption.slice(0, 80) + "..." : post.caption)
                                    : "Shared as a Story (No caption)";

                                return (
                                    <TableRow key={post.post_id} className="group border-border hover:bg-white/[0.04] transition-all h-24">
                                        <TableCell className="pl-6">
                                            <div className="flex flex-col gap-1.5">
                                                <span className="text-[13px] font-black text-foreground tracking-widest font-mono">
                                                    {post.instagram_post_id ? post.instagram_post_id : (post.internal_id || "LOCAL_LOG")}
                                                </span>
                                                <div className="flex items-center gap-1.5 opacity-40">
                                                    <span className="text-[10px] font-bold uppercase tracking-widest">{isStory ? "Story Content" : "Feed Publication"}</span>
                                                </div>
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            <div className="flex justify-center">
                                                <div className={`flex items-center gap-2 px-3 py-1 rounded-full border ${pill.wrap}`}>
                                                    {platform === "facebook"
                                                        ? <Facebook className={`w-3.5 h-3.5 ${pill.icon}`} />
                                                        : <Instagram className={`w-3.5 h-3.5 ${pill.icon}`} />
                                                    }
                                                    <span className={`text-[10px] font-black uppercase tracking-wider ${pill.text}`}>{platform}</span>
                                                </div>
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            <div className="flex flex-col leading-snug">
                                                <span className="text-sm text-white/90 font-black tracking-tight">
                                                    {format(new Date(post.created_at), "MMM dd, yyyy")}
                                                </span>
                                                <span className="text-[11px] text-muted-foreground/60 font-medium mt-0.5">
                                                    {format(new Date(post.created_at), "h:mm a")} ({formatHistoryTimestamp(post.created_at).split(" (")[1].replace(")", "")})
                                                </span>
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            <StatusBadge status={post.status} className="px-3" />
                                        </TableCell>
                                        <TableCell className="max-w-[350px]">
                                            <div className="flex items-center gap-4">
                                                {post.media_url && (
                                                    <div className="flex-shrink-0 w-12 h-12 rounded-lg overflow-hidden bg-background border border-border/50 shadow-lg group-hover:border-primary/30 transition-colors">
                                                        <img src={post.media_url} className="w-full h-full object-cover" alt="" />
                                                    </div>
                                                )}
                                                <div className="flex flex-col gap-1.5 min-w-0">
                                                    <p className={`text-[14px] line-clamp-2 leading-relaxed tracking-tight ${post.status.toLowerCase() === "failed" ? "text-red-400 font-bold" : "text-white/85 font-medium"}`}>
                                                        {post.status.toLowerCase() === "failed"
                                                            ? mapBackendErrorToUI(post.error_message)
                                                            : summary
                                                        }
                                                    </p>
                                                    {post.status.toLowerCase() === "failed" && (
                                                        <div className="flex items-center gap-2 text-[10px] text-red-500 font-black uppercase tracking-widest">
                                                            <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
                                                            Diagnostic Available
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </TableCell>
                                        <TableCell className="text-right pr-6">
                                            <Button
                                                variant="outline"
                                                size="icon"
                                                onClick={() => setSelectedPost(post)}
                                                className="h-10 w-10 text-muted-foreground/60 hover:text-foreground hover:bg-foreground/10 border-border/50 rounded-xl transition-all"
                                            >
                                                <Expand className="w-4 h-4" />
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                );
                            })
                        )}
                    </TableBody>
                </Table>
            </div>

            {/* Modal Detail */}
            <Dialog open={!!selectedPost} onOpenChange={(open) => !open && setSelectedPost(null)}>
                <DialogContent className="max-w-2xl bg-[#09090B] border border-border/50 p-0 overflow-hidden shadow-2xl rounded-2xl">
                    {selectedPost && (
                        <div className="flex flex-col max-h-[90vh]">
                            <DialogHeader className="p-6 pb-2 border-b border-border bg-white/[0.02]">
                                <div className="flex items-start justify-between">
                                    <div className="flex items-center gap-4">
                                        <div className="w-12 h-12 rounded-xl bg-foreground/5 flex items-center justify-center border border-border/50 shadow-inner">
                                            {selectedPost.platform === "facebook" ? <Facebook className="w-6 h-6 text-teal-500" /> : <Instagram className="w-6 h-6 text-pink-500" />}
                                        </div>
                                        <div>
                                            <DialogTitle className="text-xl font-black uppercase tracking-tight">Post Log Detail</DialogTitle>
                                            <DialogDescription className="text-[10px] opacity-40 font-mono mt-0.5 tracking-widest uppercase">
                                                ID_TRACE: {selectedPost.internal_id || "LOCAL_LOG"}
                                            </DialogDescription>
                                        </div>
                                    </div>
                                    <div className="mr-8">
                                        <StatusBadge status={selectedPost.status} />
                                    </div>
                                </div>
                            </DialogHeader>

                            <div className="p-6 space-y-8 overflow-y-auto">
                                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                                    <div className="p-4 rounded-xl bg-white/[0.02] border border-border">
                                        <p className="text-[10px] text-white/30 uppercase font-black tracking-widest mb-2">Timestamp</p>
                                        <p className="text-sm font-bold text-white/90">{format(new Date(selectedPost.created_at), "MMM dd, yyyy · h:mm a")}</p>
                                    </div>
                                    <div className="p-4 rounded-xl bg-white/[0.02] border border-border">
                                        <p className="text-[10px] text-white/30 uppercase font-black tracking-widest mb-2">Post Mode</p>
                                        <p className="text-sm font-bold uppercase tracking-tight text-white/90">{!selectedPost.caption ? "Story Content" : "Feed Publication"}</p>
                                    </div>
                                    <div className="p-4 rounded-xl bg-white/[0.02] border border-border">
                                        <p className="text-[10px] text-white/30 uppercase font-black tracking-widest mb-2">Platform</p>
                                        <p className="text-sm font-bold capitalize text-white/90">{selectedPost.platform || "Instagram"}</p>
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                                    {selectedPost.media_url && (
                                        <div className="md:col-span-1">
                                            <p className="text-[10px] text-white/30 uppercase font-black tracking-widest mb-3">Post Media</p>
                                            <div className="aspect-square rounded-xl overflow-hidden bg-background border border-border/50 shadow-2xl">
                                                <img src={selectedPost.media_url} className="w-full h-full object-contain" alt="" />
                                            </div>
                                        </div>
                                    )}
                                    <div className={selectedPost.media_url ? "md:col-span-2" : "md:col-span-3"}>
                                        <p className="text-[10px] text-white/30 uppercase font-black tracking-widest mb-3">Caption Metadata</p>
                                        <div className="p-5 rounded-xl bg-white/[0.03] border border-border text-base text-white/80 leading-relaxed font-light min-h-[140px] whitespace-pre-wrap">
                                            {selectedPost.caption || <span className="text-white/20 italic font-mono text-xs">LOGGED_WITH_NO_CAPTION</span>}
                                        </div>
                                    </div>
                                </div>

                                {selectedPost.status.toLowerCase() === "failed" && (
                                    <div className="space-y-3">
                                        <p className="text-[11px] text-red-500 uppercase font-black tracking-widest flex items-center gap-2">
                                            <AlertTriangle className="w-4 h-4" />
                                            System Log Reference
                                        </p>
                                        <div className="p-6 rounded-2xl bg-red-500/[0.03] border border-red-500/10 font-medium text-sm text-red-100/80 leading-relaxed overflow-x-auto whitespace-pre-wrap">
                                            {mapBackendErrorToUI(selectedPost.error_message)}
                                        </div>
                                    </div>
                                )}
                            </div>

                            <div className="p-6 border-t border-border flex justify-end">
                                <Button
                                    onClick={() => setSelectedPost(null)}
                                    className="h-10 px-8 text-xs font-black uppercase tracking-widest bg-foreground/5 hover:bg-foreground/10 text-foreground border border-border/50 transition-all rounded-xl shadow-lg"
                                >
                                    Dismiss Detail
                                </Button>
                            </div>
                        </div>
                    )}
                </DialogContent>
            </Dialog>
        </div>
    );
};
