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
    Image,
    Download,
    Trash2,
    Search,
    Filter,
    Sparkles,
    Upload,
    Calendar,
    Eye,
    RefreshCw,
    Copy,
    Check,
    Heart,
    FileText,
    Video
} from "lucide-react";
import { toast } from "sonner";
import { assetService, type Asset, type CaptionAsset } from "@/services/assetService";
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { fadeInUp } from "@/utils/animations";
import { BlurText } from "@/components/ui/text-reveal";
import { ThemeEmoji } from "@/components/ui/emoji";

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
    const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);

    // Caption state
    const [captions, setCaptions] = useState<CaptionAsset[]>([]);
    const [captionTotal, setCaptionTotal] = useState(0);
    const [isLoadingCaptions, setIsLoadingCaptions] = useState(false);
    const [captionTypeFilter, setCaptionTypeFilter] = useState<string>("all");
    const [copiedCaptionId, setCopiedCaptionId] = useState<string | null>(null);

    const [activeTab, setActiveTab] = useState("images");

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

    const handleDownload = (asset: Asset) => {
        try {
            assetService.downloadAsset(asset.asset_id, asset.file_name);
            toast.success("Download Started", {
                description: `Downloading ${asset.file_name}`
            });
        } catch (error: any) {
            toast.error("Download Failed", {
                description: error.message
            });
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
                                <h1 className="text-3xl font-bold font-bebas tracking-wide">
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
                                            <SelectItem value="generated_video">Generated Videos</SelectItem>
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
                                        className="group relative aspect-square rounded-lg overflow-hidden border bg-card hover:shadow-lg transition-all"
                                        whileHover={{ scale: 1.02 }}
                                    >
                                        {/* Render video or image based on asset type */}
                                        {isVideoAsset(asset) ? (
                                            <video
                                                src={getMediaUrl(asset.storage_url)}
                                                className="w-full h-full object-cover"
                                                controls={false}
                                                muted
                                                loop
                                                playsInline
                                                onMouseEnter={(e) => (e.target as HTMLVideoElement).play()}
                                                onMouseLeave={(e) => {
                                                    const video = e.target as HTMLVideoElement;
                                                    video.pause();
                                                    video.currentTime = 0;
                                                }}
                                                onError={(e) => {
                                                    const video = e.target as HTMLVideoElement;
                                                    video.style.display = 'none';
                                                    const fallback = document.createElement('div');
                                                    fallback.className = 'w-full h-full flex items-center justify-center bg-black text-primary';
                                                    fallback.innerHTML = '<span class="text-sm font-mono">Video Not Found</span>';
                                                    video.parentElement?.appendChild(fallback);
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

                                        {/* Video indicator overlay (top left) */}
                                        {isVideoAsset(asset) && (
                                            <div className="absolute top-3 left-3">
                                                <Badge className="bg-purple-500/90 text-white gap-1">
                                                    <Video className="w-3 h-3" />
                                                    Video
                                                </Badge>
                                            </div>
                                        )}

                                        {/* Overlay with actions */}
                                        <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col justify-between p-3">
                                            <div className="flex justify-between items-start">
                                                {asset.generation_source === 'AI' && !isVideoAsset(asset) && (
                                                    <Badge className="bg-primary/90 text-primary-foreground gap-1">
                                                        <Sparkles className="w-3 h-3" />
                                                        AI
                                                    </Badge>
                                                )}
                                                {asset.times_used > 0 && (
                                                    <Badge variant="outline" className="bg-background/90 ml-auto">
                                                        <Eye className="w-3 h-3 mr-1" />
                                                        {asset.times_used}
                                                    </Badge>
                                                )}
                                            </div>

                                            <div className="flex gap-2">
                                                <Button
                                                    size="sm"
                                                    variant="secondary"
                                                    className="flex-1"
                                                    onClick={() => handleDownload(asset)}
                                                >
                                                    <Download className="w-4 h-4" />
                                                </Button>
                                                <Button
                                                    size="sm"
                                                    variant="destructive"
                                                    onClick={() => handleDelete(asset.asset_id)}
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </Button>
                                            </div>
                                        </div>

                                        {/* Info badge at bottom */}
                                        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-3 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <p className="text-white text-xs font-mono truncate">{asset.file_name}</p>
                                            <p className="text-white/60 text-[10px] font-mono">
                                                {formatDate(asset.created_at)} • {formatFileSize(asset.file_size_bytes)}
                                            </p>
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
                        {/* Caption Filters */}
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
        </Layout>
    );
};

export default AssetLibrary;
