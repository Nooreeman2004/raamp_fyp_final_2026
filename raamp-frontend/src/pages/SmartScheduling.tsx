import React, { useState } from "react";
import Layout from "@/components/Layout";
import { Button } from "@/components/ui/button";
import { EnhancedPostCreatorPanel } from "@/components/dashboard/EnhancedPostCreatorPanel";
import { ScheduledPostsTable } from "@/components/dashboard/ScheduledPostsTable";
import { PostingHistoryTable } from "@/components/dashboard/PostingHistoryTable";
import { GlobalConnectionBanner } from "@/components/dashboard/GlobalConnectionBanner";
import { Calendar, History, Plus, RefreshCw, AlertCircle, Search } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { instagramService } from "@/services/instagramService";
import { facebookService } from "@/services/facebookService";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Link } from "react-router-dom";
import type { SocialConnectionStatus } from "@/types/instagram.types";

const SmartScheduling = () => {
    const [isCreatorOpen, setIsCreatorOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");
    const [platformFilter, setPlatformFilter] = useState("all");

    // Fetch scheduled posts from both platforms
    const {
        data: scheduledPosts,
        isLoading: isLoadingScheduled,
        error: scheduledError,
        refetch: refetchScheduled,
    } = useQuery({
        queryKey: ["scheduled-posts"],
        queryFn: async () => {
            // Fetch from both platforms
            const [igPosts, fbPosts] = await Promise.allSettled([
                instagramService.getScheduledPosts(),
                facebookService.getScheduledPosts()
            ]);

            // Combine results with proper fallback handling
            const igPostsData = igPosts.status === 'fulfilled' && Array.isArray(igPosts.value?.posts)
                ? igPosts.value.posts
                : [];

            // Map Facebook scheduled posts to match ScheduledPostItem structure
            const fbPostsData = fbPosts.status === 'fulfilled' && Array.isArray(fbPosts.value?.posts)
                ? fbPosts.value.posts.map((post: any) => ({
                    post_id: post.post_id,
                    media_url: post.media_url || '',
                    caption: post.message || '',
                    scheduled_time: post.scheduled_time,
                    status: post.status,
                    created_at: post.created_at,
                    platform: post.platform || 'facebook'
                }))
                : [];

            const allPosts = [...igPostsData, ...fbPostsData];
            return {
                posts: allPosts,
                total: allPosts.length
            };
        },
        refetchInterval: 30000,
    });

    // Fetch posting history from both platforms
    const {
        data: postHistory,
        isLoading: isLoadingHistory,
        error: historyError,
        refetch: refetchHistory,
    } = useQuery({
        queryKey: ["post-history"],
        queryFn: async () => {
            // Fetch from both platforms
            const [igHistory, fbHistory] = await Promise.allSettled([
                instagramService.getCombinedHistory(100),
                facebookService.getPostHistory(100)
            ]);

            // Combine results with proper fallback handling
            const igPostsData = igHistory.status === 'fulfilled' && Array.isArray(igHistory.value?.posts)
                ? igHistory.value.posts
                : [];

            // Map Facebook posts to match PostHistoryItem structure
            const fbPostsData = fbHistory.status === 'fulfilled' && Array.isArray(fbHistory.value?.posts)
                ? fbHistory.value.posts.map((post: any) => ({
                    post_id: post.post_id,
                    internal_id: post.post_id,
                    platform: post.platform || 'facebook',
                    media_url: post.media_url || '',
                    caption: post.message || '',
                    status: post.status,
                    facebook_post_id: post.facebook_post_id,
                    created_at: post.created_at,
                    published_at: post.published_at,
                    error_message: post.error
                }))
                : [];

            // Combine and sort by created_at (newest first)
            const allPosts = [...igPostsData, ...fbPostsData].sort((a, b) => {
                return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
            });

            return {
                posts: allPosts,
                total: allPosts.length
            };
        },
        refetchInterval: 30000,
    });

    // Fetch connection status
    const { data: connectionStatus } = useQuery({
        queryKey: ["instagram-connection"],
        queryFn: () => instagramService.getConnectionStatus(),
    });

    // Fetch social connection status (Instagram + Facebook) - REAL-TIME, NO CACHE
    const { data: socialStatus, isLoading: isLoadingSocialStatus, refetch: refetchSocialStatus, error: socialStatusError } = useQuery<SocialConnectionStatus>({
        queryKey: ["social-connection-status"],
        queryFn: async () => {
            const status = await instagramService.getSocialConnectionStatus();
            console.log("🔌 SOCIAL STATUS RESPONSE:", status);
            return status;
        },
        staleTime: 0,
        gcTime: 0,
        refetchOnMount: true,
        refetchOnWindowFocus: true,
        retry: 3,
    });

    const handleRefreshAll = () => {
        // Full page reload as requested
        window.location.reload();
    };

    const handlePostSuccess = () => {
        // Refresh both tables after successful post creation
        refetchScheduled();
        refetchHistory();
    };

    const handleCreatePostClick = () => {
        // Refetch social status when opening modal to ensure latest connection state
        refetchSocialStatus();
        setIsCreatorOpen(true);
    };

    const breadcrumbItems = [
        { label: "Dashboard", href: "/dashboard" },
        { label: "Smart Scheduling", href: "/dashboard/smart-scheduling" },
    ];

    return (
        <Layout breadcrumbItems={breadcrumbItems}>
            <div className="space-y-6">
                {/* Header */}
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">
                            Smart Scheduling
                        </h1>
                        <p className="text-muted-foreground mt-1">
                            Schedule posts for optimal times when your audience is most active
                        </p>
                    </div>
                    <div className="flex gap-3">
                        <Button
                            variant="outline"
                            size="icon"
                            onClick={handleRefreshAll}
                            className="bg-white/5 border-white/10 hover:bg-white/10 transition-colors"
                            title="Refresh Page"
                        >
                            <RefreshCw className="w-4 h-4 shadow-[0_0_10px_rgba(255,255,255,0.1)]" />
                        </Button>
                        <Button
                            onClick={handleCreatePostClick}
                            className="bg-[#00E0D0] hover:bg-[#00E0D0]/90 text-black font-bold shadow-[0_0_20px_rgba(0,224,208,0.2)]"
                        >
                            <Plus className="w-4 h-4 mr-2" />
                            Create Post
                        </Button>
                    </div>
                </div>

                {/* Global Filters Section */}
                <div className="flex flex-col md:flex-row items-center gap-4 bg-white/5 p-4 rounded-xl border border-white/10">
                    <div className="relative flex-1 w-full">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
                        <Input
                            placeholder="Search logs and scheduled content..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-9 h-10 w-full bg-black/20 border-white/10 text-sm focus:ring-[#00E0D0]/50"
                        />
                    </div>
                    <Select value={platformFilter} onValueChange={setPlatformFilter}>
                        <SelectTrigger className="h-10 w-full md:w-[180px] bg-black/20 border-white/10 text-xs font-bold uppercase tracking-widest">
                            <SelectValue placeholder="All Platforms" />
                        </SelectTrigger>
                        <SelectContent className="bg-[#0A0A0B] border-white/10">
                            <SelectItem value="all">All Platforms</SelectItem>
                            <SelectItem value="instagram">Instagram</SelectItem>
                            <SelectItem value="facebook">Facebook</SelectItem>
                        </SelectContent>
                    </Select>
                </div>

                {/* Global Connection Banner */}
                <div className="space-y-3">
                    {isLoadingSocialStatus ? (
                        <Skeleton className="h-24 w-full rounded-xl" />
                    ) : (
                        <GlobalConnectionBanner
                            instagramConnected={socialStatus?.instagram_connected}
                            facebookConnected={socialStatus?.facebook_connected}
                        />
                    )}

                    {/* Show error only if critical API failure */}
                    {socialStatusError && !isLoadingSocialStatus && (
                        <Alert variant="destructive" className="rounded-xl border-destructive/20 bg-destructive/5">
                            <AlertCircle className="h-4 w-4" />
                            <AlertTitle>System Alert</AlertTitle>
                            <AlertDescription>
                                We're having trouble reaching the social connection service. Please try refreshing.
                            </AlertDescription>
                        </Alert>
                    )}
                </div>

                {/* Scheduled Posts Section */}
                <div className="space-y-4">
                    <div className="flex items-center gap-2">
                        <Calendar className="w-5 h-5 text-primary" />
                        <h2 className="text-xl font-semibold">Scheduled Posts</h2>
                        <span className="text-sm text-muted-foreground">
                            ({scheduledPosts?.total || 0})
                        </span>
                    </div>

                    {isLoadingScheduled ? (
                        <div className="space-y-3">
                            <Skeleton className="h-12 w-full" />
                            <Skeleton className="h-12 w-full" />
                            <Skeleton className="h-12 w-full" />
                        </div>
                    ) : scheduledError ? (
                        <Alert variant="destructive">
                            <AlertCircle className="h-4 w-4" />
                            <AlertTitle>Error Loading Scheduled Posts</AlertTitle>
                            <AlertDescription>
                                {(scheduledError as any).message || "Failed to load scheduled posts"}
                            </AlertDescription>
                        </Alert>
                    ) : (
                        <ScheduledPostsTable
                            posts={scheduledPosts?.posts || []}
                            onRefresh={refetchScheduled}
                            searchQuery={searchQuery}
                            platformFilter={platformFilter}
                        />
                    )}
                </div>

                {/* Posting History Section */}
                <div className="space-y-4">
                    <div className="flex items-center gap-2">
                        <History className="w-5 h-5 text-primary" />
                        <h2 className="text-xl font-semibold">Posting History & Logs</h2>
                        <span className="text-sm text-muted-foreground">
                            ({postHistory?.total || 0})
                        </span>
                    </div>

                    {isLoadingHistory ? (
                        <div className="space-y-3">
                            <Skeleton className="h-12 w-full" />
                            <Skeleton className="h-12 w-full" />
                            <Skeleton className="h-12 w-full" />
                        </div>
                    ) : historyError ? (
                        <Alert variant="destructive">
                            <AlertCircle className="h-4 w-4" />
                            <AlertTitle>Error Loading History</AlertTitle>
                            <AlertDescription>
                                {(historyError as any).message || "Failed to load posting history"}
                            </AlertDescription>
                        </Alert>
                    ) : (
                        <PostingHistoryTable
                            posts={postHistory?.posts || []}
                            searchQuery={searchQuery}
                            platformFilter={platformFilter}
                        />
                    )}
                </div>
            </div>

            {/* Post Creator Panel */}
            <EnhancedPostCreatorPanel
                open={isCreatorOpen}
                onOpenChange={setIsCreatorOpen}
                onSuccess={handlePostSuccess}
            />
        </Layout>
    );
};

export default SmartScheduling;
