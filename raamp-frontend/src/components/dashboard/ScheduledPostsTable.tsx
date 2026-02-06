import React, { useState } from "react";
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
import { MediaPreviewModal } from "./MediaPreviewModal";
import {
    X,
    Image as ImageIcon,
    Loader2,
    Instagram,
    Facebook,
    Expand
} from "lucide-react";
import { formatHistoryTimestamp, getTimezone } from "@/lib/history-utils";
import type { ScheduledPostItem } from "@/types/instagram.types";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { toast } from "sonner";
import { instagramService } from "@/services/instagramService";
import { useMemo } from "react";

interface ScheduledPostsTableProps {
    posts: ScheduledPostItem[];
    onRefresh?: () => void;
    searchQuery?: string;
    platformFilter?: string;
}

export const ScheduledPostsTable: React.FC<ScheduledPostsTableProps> = ({
    posts,
    onRefresh,
    searchQuery = "",
    platformFilter = "all"
}) => {
    const [previewMedia, setPreviewMedia] = useState<{ url: string; caption?: string } | null>(null);
    const [cancellingPostId, setCancellingPostId] = useState<string | null>(null);
    const [postToCancel, setPostToCancel] = useState<ScheduledPostItem | null>(null);

    // Filter logic to match History table
    const filteredPosts = useMemo(() => {
        return posts.filter((post) => {
            // Platform filtering (scheduled posts currently default to Instagram in model, 
            // but unified posting will create them with platform flags)
            const platform: string = "instagram"; // Default for scheduled for now
            if (platformFilter !== "all" && platform.toLowerCase() !== platformFilter.toLowerCase()) return false;

            // Search filtering
            if (searchQuery) {
                const q = searchQuery.toLowerCase();
                return (
                    post.post_id.toLowerCase().includes(q) ||
                    post.caption?.toLowerCase().includes(q)
                );
            }

            return true;
        });
    }, [posts, platformFilter, searchQuery]);

    const handleCancelPost = async (post: ScheduledPostItem) => {
        try {
            setCancellingPostId(post.post_id);
            const response = await instagramService.cancelScheduledPost(post.post_id);

            if (response.success) {
                toast.success("Scheduled post cancelled successfully");
                onRefresh?.();
            } else {
                toast.error(response.message || "Failed to cancel post");
            }
        } catch (error: any) {
            console.error("Error cancelling post:", error);
            toast.error(error.message || "Failed to cancel post");
        } finally {
            setCancellingPostId(null);
            setPostToCancel(null);
        }
    };

    if (posts.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-20 bg-white/5 border border-dashed border-white/10 rounded-xl">
                <ImageIcon className="w-12 h-12 text-white/20 mb-4" />
                <h3 className="text-xl font-medium text-white/90">No scheduled posts</h3>
                <p className="text-white/40 mt-1">Scheduled content will appear here.</p>
            </div>
        );
    }

    return (
        <>
            <div className="bg-white/[0.01] border border-white/10 rounded-xl overflow-hidden shadow-2xl">
                <Table>
                    <TableHeader className="bg-white/[0.04] border-b border-white/10">
                        <TableRow className="hover:bg-transparent h-14">
                            <TableHead className="w-[200px] text-[12px] uppercase font-black text-white/70 tracking-[0.15em] pl-6">Post Identifier</TableHead>
                            <TableHead className="w-[110px] text-[12px] uppercase font-black text-white/70 tracking-[0.15em] text-center">Platform</TableHead>
                            <TableHead className="w-[180px] text-[12px] uppercase font-black text-white/70 tracking-[0.15em]">Scheduled Time</TableHead>
                            <TableHead className="w-[140px] text-[12px] uppercase font-black text-white/70 tracking-[0.15em]">Current Status</TableHead>
                            <TableHead className="text-[12px] uppercase font-black text-white/70 tracking-[0.15em]">Content Summary</TableHead>
                            <TableHead className="w-[120px] text-right text-[12px] uppercase font-black text-white/70 tracking-[0.15em] pr-6">Detail / Cancel</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {filteredPosts.length === 0 ? (
                            <TableRow className="hover:bg-transparent">
                                <TableCell colSpan={6} className="h-40 text-center text-white/30 italic text-sm font-light">
                                    No scheduled posts matching filters.
                                </TableCell>
                            </TableRow>
                        ) : (
                            filteredPosts.map((post) => {
                                // Dynamic platform check support
                                const platform = (post as any).platform?.toLowerCase() || "instagram";
                                const isStory = post.status.toLowerCase().includes("story");
                                const summary = post.caption
                                    ? (post.caption.length > 80 ? post.caption.slice(0, 80) + "..." : post.caption)
                                    : (isStory ? "Shared as a Story (No caption)" : "No caption");

                                return (
                                    <TableRow key={post.post_id} className="group border-white/5 hover:bg-white/[0.04] transition-all h-24">
                                        <TableCell className="pl-6">
                                            <div className="flex flex-col gap-1.5">
                                                <span className="text-[13px] font-black text-white tracking-widest font-mono">
                                                    {post.post_id}
                                                </span>
                                                <div className="flex items-center gap-1.5 opacity-40">
                                                    <span className="text-[10px] font-bold uppercase tracking-widest">{isStory ? "Story Content" : "Feed Publication"}</span>
                                                </div>
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            <div className="flex justify-center">
                                                <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10">
                                                    {platform === "facebook" ? <Facebook className="w-3.5 h-3.5 text-blue-500" /> : <Instagram className="w-3.5 h-3.5 text-pink-500" />}
                                                    <span className="text-[10px] font-black uppercase tracking-wider text-white/80">{platform}</span>
                                                </div>
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            <div className="flex flex-col leading-snug">
                                                <span className="text-sm text-white/90 font-black tracking-tight">
                                                    {formatHistoryTimestamp(post.scheduled_time).split(" (")[0]}
                                                </span>
                                                <span className="text-[11px] text-white/40 font-medium mt-0.5 uppercase tracking-tighter">
                                                    Scheduled in {getTimezone()}
                                                </span>
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            <StatusBadge status={post.status} className="px-3" />
                                        </TableCell>
                                        <TableCell className="max-w-[350px]">
                                            <div className="flex items-center gap-4">
                                                {post.media_url && (
                                                    <div className="flex-shrink-0 w-12 h-12 rounded-lg overflow-hidden bg-black border border-white/10 shadow-lg group-hover:border-primary/30 transition-colors cursor-pointer"
                                                        onClick={() => setPreviewMedia({ url: post.media_url, caption: post.caption })}>
                                                        <img src={post.media_url} className="w-full h-full object-cover" alt="" />
                                                    </div>
                                                )}
                                                <p className="text-[14px] text-white/85 font-medium line-clamp-2 leading-relaxed tracking-tight">
                                                    {summary}
                                                </p>
                                            </div>
                                        </TableCell>
                                        <TableCell className="text-right pr-6">
                                            <div className="flex items-center justify-end gap-2">
                                                <Button
                                                    variant="outline"
                                                    size="icon"
                                                    onClick={() => setPreviewMedia({ url: post.media_url, caption: post.caption })}
                                                    className="h-10 w-10 text-white/40 hover:text-white hover:bg-white/10 border-white/10 rounded-xl transition-all"
                                                >
                                                    <Expand className="w-4 h-4" />
                                                </Button>
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="h-10 w-10 text-red-400/60 hover:text-red-400 hover:bg-red-500/10 rounded-xl"
                                                    onClick={() => setPostToCancel(post)}
                                                    disabled={cancellingPostId === post.post_id}
                                                >
                                                    {cancellingPostId === post.post_id ? (
                                                        <Loader2 className="w-4 h-4 animate-spin text-red-400" />
                                                    ) : (
                                                        <X className="w-4 h-4" />
                                                    )}
                                                </Button>
                                            </div>
                                        </TableCell>
                                    </TableRow>
                                );
                            })
                        )}
                    </TableBody>
                </Table>
            </div>

            {/* Media Preview Modal */}
            {previewMedia && (
                <MediaPreviewModal
                    open={!!previewMedia}
                    onOpenChange={(open) => !open && setPreviewMedia(null)}
                    mediaUrl={previewMedia.url}
                    caption={previewMedia.caption}
                />
            )}

            {/* Cancel Confirmation Dialog */}
            <AlertDialog open={!!postToCancel} onOpenChange={(open) => !open && setPostToCancel(null)}>
                <AlertDialogContent className="bg-[#09090B] border-white/10 rounded-2xl">
                    <AlertDialogHeader>
                        <AlertDialogTitle className="text-xl font-black uppercase tracking-tight">Cancel Scheduled Post?</AlertDialogTitle>
                        <AlertDialogDescription className="text-white/50">
                            This will prevent the post from being published. This action is permanent and cannot be reversed.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter className="mt-4">
                        <AlertDialogCancel className="bg-white/5 border-white/10 text-white hover:bg-white/10 rounded-xl">Keep Post</AlertDialogCancel>
                        <AlertDialogAction
                            onClick={() => postToCancel && handleCancelPost(postToCancel)}
                            className="bg-red-500/80 hover:bg-red-500 text-white font-bold rounded-xl"
                        >
                            Confirm Cancellation
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </>
    );
};
