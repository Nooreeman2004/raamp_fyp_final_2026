import { useState, useEffect } from "react";
import Layout from "@/components/Layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import {
    Image,
    Download,
    Trash2,
    Search,
    Sparkles,
    Eye,
    RefreshCw,
    Copy,
    Check,
    Heart,
    FileText,
    Video,
    Maximize2,
} from "lucide-react";
import { toast } from "sonner";
import { assetService, type Asset, type CaptionAsset } from "@/services/assetService";
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { fadeInUp } from "@/utils/animations";
import { BlurText } from "@/components/ui/text-reveal";
import { ThemeEmoji } from "@/components/ui/emoji";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { instagramService, type ROIMetrics, type ROISummary } from "@/services/instagramService";
import { BarChart3, TrendingUp, Users, Activity, Clock, AlertCircle } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

const AssetLibrary = () => {
    // Image assets state
    const [assets, setAssets] = useState<Asset[]>([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [perPage] = useState(24);
    const [isLoading, setIsLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [assetTypeFilter, setAssetTypeFilter] = useState("all");
    const [sourceFilter, setSourceFilter] = useState("all");

    // Caption state
    const [captions, setCaptions] = useState<CaptionAsset[]>([]);
    const [captionTotal, setCaptionTotal] = useState(0);
    const [isLoadingCaptions, setIsLoadingCaptions] = useState(false);
    const [captionTypeFilter, setCaptionTypeFilter] = useState<string>("all");
    const [copiedCaptionId, setCopiedCaptionId] = useState<string | null>(null);

    const [activeTab, setActiveTab] = useState("images");
    const [isRescanning, setIsRescanning] = useState(false);
    const [viewAsset, setViewAsset] = useState<Asset | null>(null);
    const queryClient = useQueryClient();

    // Fetch Connection for Business ID
    const { data: connection } = useQuery({
        queryKey: ['instagram-connection'],
        queryFn: () => instagramService.getConnectionStatus(),
        staleTime: 60 * 60 * 1000 // 1 hour
    });

    const businessId = connection?.ig_business_id;

    // ROI Summary Query
    const { data: roiSummary } = useQuery<ROISummary>({
        queryKey: ['roi-summary', businessId],
        queryFn: () => instagramService.getROISummary(businessId!),
        enabled: !!businessId,
        staleTime: 30 * 60 * 1000 // 30 minutes
    });

    // Refresh Individual Post ROI
    const refreshROIMutation = useMutation({
        mutationFn: (postId: string) => instagramService.refreshPostROI(postId),
        onSuccess: (_, postId) => {
            queryClient.invalidateQueries({ queryKey: ['post-roi', postId] });
            toast.success("Metrics Refreshed");
        },
        onError: (err: any) => {
            toast.error("Refresh Failed", { description: err.message });
        }
    });

    const handleRescan = async () => {
        setIsRescanning(true);
        try {
            const result = await assetService.rescanFiles();
            toast.success(`Rescan Complete`, { description: result.message });
            if (result.imported > 0) fetchAssets();
        } catch (error: any) {
            toast.error("Rescan Failed", { description: error.message });
        } finally {
            setIsRescanning(false);
        }
    };

    // Helper to get full media URL safely
    const getMediaUrl = (path: string | null | undefined) => {
        if (!path) return '';
        if (path.startsWith('http')) return path;
        // Use window.location.origin for media URLs to avoid double /api/ issue
        const cleanPath = path.startsWith('/') ? path : `/${path}`;
        return `${window.location.origin}${cleanPath}`;
    };

    // Fetch assets
    const fetchAssets = async () => {
        setIsLoading(true);
        try {
            const filters: any = { page, per_page: perPage };

            if (assetTypeFilter !== 'all') {
                filters.asset_type = assetTypeFilter;
            }

            if (sourceFilter !== 'all') {
                filters.source = sourceFilter;
            }

            const response = await assetService.getAssetLibrary(filters);
            setAssets(response.assets);
            setTotal(response.total);
        } catch (error: any) {
            console.error("Failed to fetch assets:", error);
            toast.error("Failed to Load Assets", {
                description: error.message || "We encountered an issue while loading your media assets."
            });
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchAssets();
    }, [page, assetTypeFilter, sourceFilter]);

    // Fetch captions
    const fetchCaptions = async () => {
        setIsLoadingCaptions(true);
        try {
            const filters: any = {};

            if (captionTypeFilter !== 'all') {
                filters.asset_type = captionTypeFilter.toUpperCase();
            }

            const response = await assetService.getCaptions(filters);
            setCaptions(response.captions);
            setCaptionTotal(response.total);
        } catch (error: any) {
            console.error("Failed to fetch captions:", error);
            toast.error("Failed to Load Captions", {
                description: error.message || "We couldn't retrieve your text assets at this time."
            });
        } finally {
            setIsLoadingCaptions(false);
        }
    };

    useEffect(() => {
        if (activeTab === "captions") {
            fetchCaptions();
        }
    }, [activeTab, captionTypeFilter]);

    const handleCopyCaption = async (caption: CaptionAsset) => {
        try {
            const textToCopy = `${caption.caption_text}\n\n${caption.hashtags.join(' ')}`;
            await navigator.clipboard.writeText(textToCopy);

            setCopiedCaptionId(caption.caption_id);

            // Mark as used in backend
            await assetService.markCaptionUsed(caption.caption_id);

            toast.success("Caption Copied!", {
                description: "Caption and hashtags copied to clipboard"
            });

            setTimeout(() => {
                setCopiedCaptionId(null);
            }, 2000);
        } catch (error) {
            console.error("Failed to copy caption:", error);
            toast.error("Failed to Copy", {
                description: "Unable to copy caption to clipboard"
            });
        }
    };

    const handleToggleFavorite = async (captionId: string) => {
        try {
            const result = await assetService.toggleCaptionFavorite(captionId);

            // Update local state
            setCaptions(prev => prev.map(c =>
                c.caption_id === captionId
                    ? { ...c, is_favorite: result.is_favorite }
                    : c
            ));

            toast.success(
                result.is_favorite ? "Added to Favorites" : "Removed from Favorites"
            );
        } catch (error: any) {
            toast.error("Failed to Update Favorite", {
                description: error.message
            });
        }
    };

    const handleDownload = async (asset: Asset) => {
        try {
            await assetService.downloadAsset(asset.asset_id, asset.file_name);
            toast.success("Download Started", {
                description: `Downloading ${asset.file_name}`
            });
        } catch (error: any) {
            toast.error("Download Failed", {
                description: error.message
            });
        }
    };

    const handleToggleAssetFavorite = async (asset: Asset, e: React.MouseEvent) => {
        e.stopPropagation();
        try {
            const result = await assetService.toggleAssetFavorite(asset.asset_id);
            setAssets(prev => prev.map(a =>
                a.asset_id === asset.asset_id ? { ...a, is_favorite: result.is_favorite } : a
            ));
            if (viewAsset?.asset_id === asset.asset_id) {
                setViewAsset(v => v ? { ...v, is_favorite: result.is_favorite } : v);
            }
            toast.success(result.is_favorite ? "Added to Favorites" : "Removed from Favorites");
        } catch (error: any) {
            toast.error("Failed to update favorite", { description: error.message });
        }
    };

    const handleDelete = async (assetId: string) => {
        if (!confirm("Are you sure you want to delete this asset?")) return;

        try {
            await assetService.deleteAsset(assetId);
            toast.success("Asset Deleted");
            fetchAssets(); // Refresh
        } catch (error: any) {
            toast.error("Delete Failed", {
                description: error.message
            });
        }
    };

    const formatFileSize = (bytes: number) => {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    };

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    };

    // Helper to check if asset is a video
    const isVideoAsset = (asset: Asset) => {
        return asset.asset_type === 'generated_video' ||
            asset.asset_type === 'generated_reel' ||
            asset.asset_type === 'uploaded_video';
    };

    return (
        <Layout breadcrumbItems={[
            { label: "Dashboard", href: "/dashboard" },
            { label: "Asset Library" }
        ]}>
            <div className="space-y-6 max-w-7xl mx-auto">
                {/* Header */}
                <Reveal variant="blurInUp">
                    <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-4">
                            <div className="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center">
                                <Sparkles className="w-7 h-7 text-primary" />
                            </div>
                            <div>
                                <h1 className="text-3xl font-bold font-heading font-semibold">
                                    <BlurText text="Asset Library" />
                                </h1>
                                <p className="text-muted-foreground font-mono text-sm">
                                    {activeTab === "images"
                                        ? `${total} media assets • Images & Videos`
                                        : `${captionTotal} text assets • Captions, Emails, WhatsApp & More`
                                    }
                                </p>
                            </div>
                        </div>
                        <div className="flex gap-2">
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={handleRescan}
                                disabled={isRescanning}
                                className="gap-2"
                                title="Scan disk for existing videos & reels not yet in library"
                            >
                                <RefreshCw className={`w-4 h-4 ${isRescanning ? 'animate-spin' : ''}`} />
                                {isRescanning ? 'Scanning...' : 'Rescan Files'}
                            </Button>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => activeTab === "images" ? fetchAssets() : fetchCaptions()}
                                disabled={activeTab === "images" ? isLoading : isLoadingCaptions}
                                className="gap-2"
                            >
                                <RefreshCw className={`w-4 h-4 ${(isLoading || isLoadingCaptions) ? 'animate-spin' : ''}`} />
                                Refresh
                            </Button>
                        </div>
                    </div>
                </Reveal>

                {/* Tabs */}
                <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                    <TabsList className="grid w-full grid-cols-2 max-w-md">
                        <TabsTrigger value="images" className="gap-2">
                            <Video className="w-4 h-4" />
                            Media
                        </TabsTrigger>
                        <TabsTrigger value="captions" className="gap-2">
                            <FileText className="w-4 h-4" />
                            Text Assets
                        </TabsTrigger>
                    </TabsList>

                    {/* Media Tab (Images, Videos, Reels) */}
                    <TabsContent value="images" className="space-y-6 mt-6">
                        {/* Filters */}
                        <Reveal variant="fadeInUp" delay={0.1}>
                            <Card className="p-4">
                                <div className="flex flex-col md:flex-row gap-4">
                                    <div className="flex-1">
                                        <div className="relative">
                                            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                            <Input
                                                placeholder="Search assets..."
                                                value={searchQuery}
                                                onChange={(e) => setSearchQuery(e.target.value)}
                                                className="pl-9"
                                            />
                                        </div>
                                    </div>
                                    <Select value={sourceFilter} onValueChange={setSourceFilter}>
                                        <SelectTrigger className="w-full md:w-[180px]">
                                            <SelectValue placeholder="Source" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="all">All Sources</SelectItem>
                                            <SelectItem value="AI"><ThemeEmoji name="sparkles" className="mr-1" /> AI Generated</SelectItem>
                                            <SelectItem value="user_upload"><ThemeEmoji name="folder" className="mr-1" /> User Uploaded</SelectItem>
                                        </SelectContent>
                                    </Select>
                                    <Select value={assetTypeFilter} onValueChange={setAssetTypeFilter}>
                                        <SelectTrigger className="w-full md:w-[180px]">
                                            <SelectValue placeholder="Type" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="all">All Types</SelectItem>
                                            <SelectItem value="generated_image">Generated Images</SelectItem>
                                            <SelectItem value="video">Generated Videos &amp; Reels</SelectItem>
                                            <SelectItem value="uploaded_image">Uploaded Images</SelectItem>
                                            <SelectItem value="uploaded_video">Uploaded Videos</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                            </Card>
                        </Reveal>

                        {/* Assets Grid */}
                        {isLoading ? (
                            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                                {[...Array(8)].map((_, i) => (
                                    <div key={i} className="aspect-square bg-muted animate-pulse rounded-lg" />
                                ))}
                            </div>
                        ) : assets.length === 0 ? (
                            <Card className="p-12 text-center">
                                <Video className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                                <h3 className="text-lg font-semibold mb-2">No Assets Found</h3>
                                <p className="text-muted-foreground mb-4">
                                    Start creating content in the Creative Studio to generate AI images and videos
                                </p>
                                <p className="text-muted-foreground text-sm mb-4">
                                    Already generated content? Click <strong>Rescan Files</strong> to import existing videos &amp; reels.
                                </p>
                                <Button variant="outline" onClick={handleRescan} disabled={isRescanning} className="gap-2">
                                    <RefreshCw className={`w-4 h-4 ${isRescanning ? 'animate-spin' : ''}`} />
                                    {isRescanning ? 'Scanning...' : 'Rescan Files'}
                                </Button>
                            </Card>
                        ) : (
                            <motion.div
                                className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4"
                                variants={fadeInUp}
                                initial="hidden"
                                animate="visible"
                            >
                                {assets.map((asset) => (
                                    <motion.div
                                        key={asset.asset_id}
                                        className="group relative aspect-square rounded-lg overflow-hidden border bg-card hover:shadow-lg transition-all cursor-pointer"
                                        whileHover={{ scale: 1.02 }}
                                        onClick={() => setViewAsset(asset)}
                                    >
                                        {/* Media */}
                                        {isVideoAsset(asset) ? (
                                            <video
                                                src={getMediaUrl(asset.storage_url)}
                                                className="w-full h-full object-cover"
                                                controls={false}
                                                muted
                                                loop
                                                playsInline
                                                onMouseEnter={(e) => { e.stopPropagation(); (e.target as HTMLVideoElement).play(); }}
                                                onMouseLeave={(e) => {
                                                    const v = e.target as HTMLVideoElement;
                                                    v.pause(); v.currentTime = 0;
                                                }}
                                                onError={(e) => {
                                                    const v = e.target as HTMLVideoElement;
                                                    v.style.display = 'none';
                                                    const fb = document.createElement('div');
                                                    fb.className = 'w-full h-full flex items-center justify-center bg-background text-primary';
                                                    fb.innerHTML = '<span class="text-sm font-mono">Video Not Found</span>';
                                                    v.parentElement?.appendChild(fb);
                                                }}
                                            />
                                        ) : (
                                            <img
                                                src={getMediaUrl(asset.storage_url)}
                                                alt={asset.file_name}
                                                className="w-full h-full object-cover"
                                                onError={(e) => {
                                                    (e.target as HTMLImageElement).src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="400"%3E%3Crect fill="%23000" width="400" height="400"/%3E%3Ctext fill="%2300f5d4" font-family="monospace" font-size="16" x="50%25" y="50%25" text-anchor="middle" dominant-baseline="middle"%3EImage Not Found%3C/text%3E%3C/svg%3E';
                                                }}
                                            />
                                        )}

                                        {/* Top-left: Video/Reel badge (always visible) */}
                                        {isVideoAsset(asset) && (
                                            <div className="absolute top-2 left-2">
                                                <Badge className="bg-purple-600/90 text-foreground gap-1 text-[10px] px-1.5 py-0.5">
                                                    <Video className="w-2.5 h-2.5" />
                                                    {asset.asset_type === 'generated_reel' ? 'Reel' : 'Video'}
                                                </Badge>
                                            </div>
                                        )}

                                        {/* Top-left AI badge for images */}
                                        {!isVideoAsset(asset) && asset.generation_source === 'AI' && (
                                            <div className="absolute top-2 left-2">
                                                <Badge className="bg-primary/90 text-primary-foreground gap-1 text-[10px] px-1.5 py-0.5">
                                                    <Sparkles className="w-2.5 h-2.5" />
                                                    AI
                                                </Badge>
                                            </div>
                                        )}

                                        {/* Top-right: Favorite heart (always visible when favorited, else on hover) */}
                                        <button
                                            className={`absolute top-2 right-2 p-1.5 rounded-full transition-all ${
                                                asset.is_favorite
                                                    ? 'bg-red-500/90 opacity-100'
                                                    : 'bg-black/50 opacity-0 group-hover:opacity-100'
                                            }`}
                                            onClick={(e) => handleToggleAssetFavorite(asset, e)}
                                            title={asset.is_favorite ? 'Remove from favorites' : 'Add to favorites'}
                                        >
                                            <Heart className={`w-3.5 h-3.5 ${asset.is_favorite ? 'fill-white text-foreground' : 'text-foreground'}`} />
                                        </button>

                                        {/* ROI Badge (Top-left if top post) */}
                                        {roiSummary?.best_performing_post?.post_id === asset.instagram_post_id && (
                                            <div className="absolute top-8 left-2">
                                                <Badge className="bg-amber-500/90 text-foreground gap-1 text-[10px] px-1.5 py-0.5 animate-pulse">
                                                    <TrendingUp className="w-2.5 h-2.5" />
                                                    Top Post
                                                </Badge>
                                            </div>
                                        )}

                                        {/* ROI Metrics Row (Compact Overlay) */}
                                        {asset.instagram_post_id && (
                                            <ROIMetricsOverlay postId={asset.instagram_post_id} onRefresh={refreshROIMutation.mutate} isRefreshing={refreshROIMutation.isPending} />
                                        )}

                                        {/* Bottom: always-visible info bar */}
                                        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 via-black/60 to-transparent p-2.5 pt-6">
                                            <p className="text-foreground text-xs font-mono truncate leading-tight">{asset.file_name}</p>
                                            <p className="text-muted-foreground/80 text-[10px] font-mono mt-0.5">
                                                {formatDate(asset.created_at)} · {formatFileSize(asset.file_size_bytes)}
                                            </p>
                                        </div>

                                        {/* Bottom-right: action buttons (on hover, above info bar) */}
                                        <div className="absolute bottom-12 right-2 flex flex-col gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <button
                                                className="p-1.5 bg-white/20 hover:bg-white/40 backdrop-blur rounded-md transition-colors"
                                                onClick={(e) => { e.stopPropagation(); setViewAsset(asset); }}
                                                title="View fullscreen"
                                            >
                                                <Maximize2 className="w-3.5 h-3.5 text-foreground" />
                                            </button>
                                            <button
                                                className="p-1.5 bg-white/20 hover:bg-primary/80 backdrop-blur rounded-md transition-colors"
                                                onClick={(e) => { e.stopPropagation(); handleDownload(asset); }}
                                                title="Download"
                                            >
                                                <Download className="w-3.5 h-3.5 text-foreground" />
                                            </button>
                                            <button
                                                className="p-1.5 bg-white/20 hover:bg-red-600/80 backdrop-blur rounded-md transition-colors"
                                                onClick={(e) => { e.stopPropagation(); handleDelete(asset.asset_id); }}
                                                title="Delete"
                                            >
                                                <Trash2 className="w-3.5 h-3.5 text-foreground" />
                                            </button>
                                        </div>
                                    </motion.div>
                                ))}
                            </motion.div>
                        )}

                        {/* Pagination */}
                        {total > perPage && (
                            <div className="flex justify-center gap-2">
                                <Button
                                    variant="outline"
                                    onClick={() => setPage(p => Math.max(1, p - 1))}
                                    disabled={page === 1}
                                >
                                    Previous
                                </Button>
                                <div className="flex items-center gap-2 px-4">
                                    <span className="text-sm text-muted-foreground">
                                        Page {page} of {Math.ceil(total / perPage)}
                                    </span>
                                </div>
                                <Button
                                    variant="outline"
                                    onClick={() => setPage(p => p + 1)}
                                    disabled={page >= Math.ceil(total / perPage)}
                                >
                                    Next
                                </Button>
                            </div>
                        )}
                    </TabsContent>

                    {/* Captions Tab */}
                    <TabsContent value="captions" className="space-y-6 mt-6">
                        {/* ROI Summary Banner */}
                        {roiSummary && (roiSummary.total_posts > 0) && (
                            <Reveal>
                                <motion.div 
                                    className="mb-8 p-4 bg-primary/5 border border-primary/20 backdrop-blur rounded-xl flex flex-wrap items-center justify-between gap-6"
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                >
                                    <div className="flex items-center gap-3">
                                        <div className="p-2 bg-primary/10 rounded-lg">
                                            <TrendingUp className="w-5 h-5 text-primary" />
                                        </div>
                                        <div>
                                            <h4 className="text-sm font-semibold">Total Performance</h4>
                                            <p className="text-xs text-muted-foreground">Across {roiSummary.total_posts} posts</p>
                                        </div>
                                    </div>
                                    
                                    <div className="flex flex-wrap gap-8">
                                        <div className="flex flex-col">
                                            <span className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1 flex items-center gap-1">
                                                <Users className="w-3 h-3" /> Total Reach
                                            </span>
                                            <span className="text-xl font-bold font-mono text-primary">{roiSummary.total_reach.toLocaleString()}</span>
                                        </div>
                                        <div className="flex flex-col">
                                            <span className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1 flex items-center gap-1">
                                                <Eye className="w-3 h-3" /> Impressions
                                            </span>
                                            <span className="text-xl font-bold font-mono text-purple-400">{roiSummary.total_impressions.toLocaleString()}</span>
                                        </div>
                                        <div className="flex flex-col">
                                            <span className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1 flex items-center gap-1">
                                                <Activity className="w-3 h-3" /> Avg Engagement
                                            </span>
                                            <span className="text-xl font-bold font-mono text-teal-400">{roiSummary.avg_engagement_rate}%</span>
                                        </div>
                                    </div>
                                    
                                    <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 bg-primary/10 rounded-full border border-primary/20">
                                        <Sparkles className="w-3.5 h-3.5 text-primary" />
                                        <span className="text-xs font-semibold">Campaign Loop Optimized</span>
                                    </div>
                                </motion.div>
                            </Reveal>
                        )}

                        {/* Search and Filters */}
                        <Card className="p-4">
                            <div className="flex flex-col md:flex-row gap-4">
                                <Select value={captionTypeFilter} onValueChange={setCaptionTypeFilter}>
                                    <SelectTrigger className="w-full md:w-[200px]">
                                        <SelectValue placeholder="Platform Type" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="all">All Platforms</SelectItem>
                                        <SelectItem value="post"><ThemeEmoji name="post" className="mr-1" /> Posts</SelectItem>
                                        <SelectItem value="story"><ThemeEmoji name="story" className="mr-1" /> Stories</SelectItem>
                                        <SelectItem value="reel"><ThemeEmoji name="video" className="mr-1" /> Reels / TikTok</SelectItem>
                                        <SelectItem value="carousel"><ThemeEmoji name="image" className="mr-1" /> Carousel</SelectItem>
                                        <SelectItem value="ad_copy"><ThemeEmoji name="ad_copy" className="mr-1" /> Ad Copy</SelectItem>
                                        <SelectItem value="whatsapp"><ThemeEmoji name="whatsapp" className="mr-1" /> WhatsApp</SelectItem>
                                        <SelectItem value="email"><ThemeEmoji name="email" className="mr-1" /> Email</SelectItem>
                                        <SelectItem value="hashtag"><ThemeEmoji name="sparkles" className="mr-1" /> Hashtags</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </Card>

                        {/* Captions Grid */}
                        {isLoadingCaptions ? (
                            <div className="grid gap-4">
                                {[...Array(6)].map((_, i) => (
                                    <div key={i} className="h-32 bg-muted animate-pulse rounded-lg" />
                                ))}
                            </div>
                        ) : captions.length === 0 ? (
                            <Card className="p-12 text-center">
                                <FileText className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                                <h3 className="text-lg font-semibold mb-2">No Captions Found</h3>
                                <p className="text-muted-foreground mb-4">
                                    Generate content in the Creative Studio to save captions
                                </p>
                            </Card>
                        ) : (
                            <div className="grid gap-4">
                                {captions.map((caption) => (
                                    <motion.div
                                        key={caption.caption_id}
                                        className="group relative"
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                    >
                                        <Card className="p-4 hover:shadow-lg transition-all">
                                            <div className="flex items-start justify-between gap-4">
                                                <div className="flex-1 space-y-2">
                                                    {/* Header */}
                                                    <div className="flex items-center gap-2 flex-wrap">
                                                        <Badge variant="outline" className="gap-1 flex items-center">
                                                            {caption.asset_type === 'POST' && <><ThemeEmoji name="post" /> Post</>}
                                                            {caption.asset_type === 'STORY' && <><ThemeEmoji name="story" /> Story</>}
                                                            {caption.asset_type === 'REEL' && <><ThemeEmoji name="video" /> Reel</>}
                                                            {caption.asset_type === 'CAROUSEL' && <><ThemeEmoji name="image" /> Carousel</>}
                                                            {caption.asset_type === 'AD_COPY' && <><ThemeEmoji name="ad_copy" /> Ad Copy</>}
                                                            {caption.asset_type === 'WHATSAPP' && <><ThemeEmoji name="whatsapp" /> WhatsApp</>}
                                                            {caption.asset_type === 'EMAIL' && <><ThemeEmoji name="email" /> Email</>}
                                                        </Badge>
                                                        <Badge variant="secondary">{caption.tone}</Badge>
                                                        {caption.is_favorite && (
                                                            <Badge className="bg-red-500/10 text-red-500 border-red-500/20">
                                                                <Heart className="w-3 h-3 fill-red-500" />
                                                            </Badge>
                                                        )}
                                                        {caption.times_used > 0 && (
                                                            <Badge variant="outline">
                                                                <Eye className="w-3 h-3 mr-1" />
                                                                {caption.times_used}
                                                            </Badge>
                                                        )}
                                                    </div>

                                                    {/* Caption Text */}
                                                    <p className="text-sm whitespace-pre-wrap">
                                                        {caption.caption_text.split(/(\*\*.*?\*\*)/g).filter(Boolean).map((part, i) => {
                                                            if (part.startsWith('**') && part.endsWith('**')) {
                                                                const content = part.slice(2, -2).trim();
                                                                if (!content) return null;
                                                                return <strong key={i} className="font-bold">{content}</strong>;
                                                            }
                                                            return <span key={i}>{part}</span>;
                                                        })}
                                                    </p>

                                                    {/* Hashtags */}
                                                    {caption.hashtags.length > 0 && (
                                                        <p className="text-xs text-primary font-mono">
                                                            {caption.hashtags.join(' ')}
                                                        </p>
                                                    )}

                                                    {/* Campaign Info */}
                                                    {caption.campaign_idea && (
                                                        <p className="text-xs text-muted-foreground italic">
                                                            Campaign: {caption.campaign_idea}
                                                        </p>
                                                    )}

                                                    {/* Footer */}
                                                    <p className="text-xs text-muted-foreground">
                                                        {formatDate(caption.created_at)}
                                                        {caption.predicted_performance &&
                                                            ` • ${caption.predicted_performance}`
                                                        }
                                                    </p>
                                                </div>

                                                {/* Action Buttons */}
                                                <div className="flex flex-col gap-2">
                                                    <Button
                                                        size="sm"
                                                        variant={copiedCaptionId === caption.caption_id ? "default" : "outline"}
                                                        className="gap-2"
                                                        onClick={() => handleCopyCaption(caption)}
                                                    >
                                                        {copiedCaptionId === caption.caption_id ? (
                                                            <>
                                                                <Check className="w-4 h-4" />
                                                                Copied
                                                            </>
                                                        ) : (
                                                            <>
                                                                <Copy className="w-4 h-4" />
                                                                Copy
                                                            </>
                                                        )}
                                                    </Button>
                                                    <Button
                                                        size="sm"
                                                        variant="ghost"
                                                        onClick={() => handleToggleFavorite(caption.caption_id)}
                                                    >
                                                        <Heart
                                                            className={`w-4 h-4 ${caption.is_favorite ? 'fill-red-500 text-red-500' : ''}`}
                                                        />
                                                    </Button>
                                                </div>
                                            </div>
                                        </Card>
                                    </motion.div>
                                ))}
                            </div>
                        )}
                    </TabsContent>
                </Tabs>
            </div>

            {/* Fullscreen Asset Viewer Modal */}
            <Dialog open={!!viewAsset} onOpenChange={(open) => !open && setViewAsset(null)}>
                <DialogContent className="max-w-5xl w-full p-0 overflow-hidden bg-background border-border">
                    <DialogHeader className="absolute top-0 left-0 right-0 z-10 flex flex-row items-center justify-between p-4 bg-gradient-to-b from-black/80 to-transparent">
                        <DialogTitle className="text-foreground font-mono text-sm truncate max-w-md">
                            {viewAsset?.file_name}
                        </DialogTitle>
                        <div className="flex items-center gap-2">
                            {viewAsset && (
                                <button
                                    className={`p-2 rounded-full transition-colors ${
                                        viewAsset.is_favorite ? 'bg-red-500 text-foreground' : 'bg-foreground/10 hover:bg-white/20 text-foreground'
                                    }`}
                                    onClick={(e) => viewAsset && handleToggleAssetFavorite(viewAsset, e)}
                                    title={viewAsset.is_favorite ? 'Remove from favorites' : 'Add to favorites'}
                                >
                                    <Heart className={`w-4 h-4 ${viewAsset.is_favorite ? 'fill-white' : ''}`} />
                                </button>
                            )}
                            {viewAsset && (
                                <button
                                    className="p-2 rounded-full bg-foreground/10 hover:bg-primary/80 text-foreground transition-colors"
                                    onClick={() => viewAsset && handleDownload(viewAsset)}
                                    title="Download"
                                >
                                    <Download className="w-4 h-4" />
                                </button>
                            )}
                        </div>
                    </DialogHeader>

                    {/* Media */}
                    <div className="flex items-center justify-center min-h-[60vh] max-h-[80vh] bg-background">
                        {viewAsset && isVideoAsset(viewAsset) ? (
                            <video
                                src={getMediaUrl(viewAsset.storage_url)}
                                className="max-w-full max-h-[80vh] object-contain"
                                controls
                                autoPlay
                                loop
                            />
                        ) : viewAsset ? (
                            <img
                                src={getMediaUrl(viewAsset.storage_url)}
                                alt={viewAsset.file_name}
                                className="max-w-full max-h-[80vh] object-contain"
                            />
                        ) : null}
                    </div>

                    {/* Metadata footer */}
                    {viewAsset && (
                        <div className="p-4 bg-card border-t border-border flex flex-wrap gap-4 text-sm text-muted-foreground font-mono">
                            <span><span className="text-foreground">Type:</span> {viewAsset.asset_type.replace('_', ' ')}</span>
                            <span><span className="text-foreground">Size:</span> {formatFileSize(viewAsset.file_size_bytes)}</span>
                            <span><span className="text-foreground">Created:</span> {formatDate(viewAsset.created_at)}</span>
                            {viewAsset.generation_source && (
                                <span><span className="text-foreground">Source:</span> {viewAsset.generation_source}</span>
                            )}
                            {viewAsset.times_used > 0 && (
                                <span><span className="text-foreground">Used:</span> {viewAsset.times_used}×</span>
                            )}
                        </div>
                    )}
                </DialogContent>
            </Dialog>
        </Layout>
    );
};

// --- HELPER COMPONENTS ---

const ROIMetricsOverlay = ({ postId, onRefresh, isRefreshing }: { postId: string, onRefresh: (id: string) => void, isRefreshing: boolean }) => {
    const { data: metrics, isLoading } = useQuery<ROIMetrics>({
        queryKey: ['post-roi', postId],
        queryFn: () => instagramService.getPostROI(postId),
        staleTime: 30 * 60 * 1000
    });

    if (isLoading) {
        return (
            <div className="absolute top-2 left-1/2 -translate-x-1/2 px-2 py-0.5 bg-black/60 backdrop-blur rounded-full flex items-center gap-2">
                <RefreshCw className="w-2.5 h-2.5 animate-spin text-primary" />
                <span className="text-[10px] text-foreground font-mono">Fetching ROI...</span>
            </div>
        );
    }

    if (!metrics) return null;

    return (
        <div className="absolute top-0 left-0 right-0 p-2 bg-gradient-to-b from-black/80 to-transparent flex flex-col gap-1 transition-transform translate-y-[-100%] group-hover:translate-y-0">
            {metrics.fetch_status === 'pending' ? (
                <div className="flex items-center gap-1.5 text-amber-400 px-1 py-0.5 rounded bg-amber-400/10">
                    <Clock className="w-3 h-3" />
                    <span className="text-[9px] font-semibold uppercase font-mono">Insights ready in 24h</span>
                </div>
            ) : metrics.fetch_status === 'failed' ? (
                <div className="flex items-center justify-between w-full">
                    <div className="flex items-center gap-1 text-red-400">
                        <AlertCircle className="w-3 h-3" />
                        <span className="text-[9px] font-semibold">Sync Failed</span>
                    </div>
                    <button 
                        onClick={(e) => { e.stopPropagation(); onRefresh(postId); }}
                        className="text-[9px] text-primary hover:underline"
                    >
                        Retry
                    </button>
                </div>
            ) : (
                <div className="w-full flex flex-col gap-1.5">
                    <div className="flex items-center justify-between">
                        <div className="flex gap-2">
                            <MetricStat label="Reach" value={metrics.reach} color="text-primary" />
                            <MetricStat label="ER" value={`${metrics.engagement_rate}%`} color="text-teal-400" />
                        </div>
                        <button 
                            disabled={isRefreshing}
                            onClick={(e) => { e.stopPropagation(); onRefresh(postId); }}
                            className={`p-1 rounded bg-black/40 hover:bg-black/60 transition-colors ${isRefreshing ? 'animate-spin' : ''}`}
                        >
                            <RefreshCw className="w-2.5 h-2.5" />
                        </button>
                    </div>
                    <div className="grid grid-cols-4 gap-1 border-t border-white/10 pt-1">
                        <SmallMetric label="Likes" val={metrics.likes} />
                        <SmallMetric label="Comm" val={metrics.comments} />
                        <SmallMetric label="Share" val={metrics.shares} />
                        <SmallMetric label="Saved" val={metrics.saved} />
                    </div>
                    {metrics.last_fetched_at && (
                        <p className="text-[8px] text-muted-foreground/60 font-mono text-right">
                            Updated {formatDistanceToNow(new Date(metrics.last_fetched_at))} ago
                        </p>
                    )}
                </div>
            )}
        </div>
    );
};

const MetricStat = ({ label, value, color }: { label: string, value: string | number, color: string }) => (
    <div className="flex flex-col">
        <span className="text-[7px] uppercase tracking-tighter text-muted-foreground/80 leading-none">{label}</span>
        <span className={`text-[11px] font-bold font-mono ${color} leading-tight`}>{value}</span>
    </div>
);

const SmallMetric = ({ label, val }: { label: string, val: number }) => (
    <div className="flex flex-col items-center">
        <span className="text-[6px] uppercase tracking-tighter text-muted-foreground/60">{label}</span>
        <span className="text-[9px] font-mono text-foreground/90">{val > 999 ? `${(val/1000).toFixed(1)}k` : val}</span>
    </div>
);

export default AssetLibrary;
