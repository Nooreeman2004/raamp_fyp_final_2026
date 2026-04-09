import React, { useEffect, useState, useCallback } from "react";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { assetService, Asset } from "@/services/assetService";
import { Loader2, Search, Filter, Image as ImageIcon, Sparkles, Check } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";

interface AssetPickerDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSelectAsset: (asset: Asset) => void;
    assetType?: 'generated_image' | 'uploaded_image' | 'uploaded_video';
}

export const AssetPickerDialog: React.FC<AssetPickerDialogProps> = ({
    open,
    onOpenChange,
    onSelectAsset,
    assetType = 'generated_image',
}) => {
    const [assets, setAssets] = useState<Asset[]>([]);
    const [loading, setLoading] = useState(false);
    const [search, setSearch] = useState("");
    const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null);
    const [filters, setFilters] = useState({
        asset_type: assetType,
        source: undefined as 'AI' | 'user_upload' | undefined,
    });
    const [pagination, setPagination] = useState({
        page: 1,
        per_page: 12,
        total: 0,
        total_pages: 0,
    });

    const fetchAssets = useCallback(async () => {
        try {
            setLoading(true);
            const response = await assetService.getAssetLibrary({
                page: pagination.page,
                per_page: pagination.per_page,
                ...filters,
            });
            setAssets(response.assets);
            setPagination((prev) => ({
                ...prev,
                total: response.total,
                total_pages: Math.ceil(response.total / response.per_page),
            }));
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Failed to load assets';
            toast.error(message);
        } finally {
            setLoading(false);
        }
    }, [pagination.page, pagination.per_page, filters]);

    useEffect(() => {
        if (open) {
            fetchAssets();
        }
    }, [open, fetchAssets]);

    const handleSelectAsset = (asset: Asset) => {
        setSelectedAssetId(asset.asset_id);
        onSelectAsset(asset);
        onOpenChange(false);
    };

    const filteredAssets = assets.filter((asset) =>
        search.toLowerCase() === ""
            ? true
            : asset.file_name.toLowerCase().includes(search.toLowerCase()) ||
              asset.generation_prompt?.toLowerCase().includes(search.toLowerCase()) ||
              asset.campaign_idea?.toLowerCase().includes(search.toLowerCase())
    );

    const formatFileSize = (bytes: number) => {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-4xl max-h-[85vh] overflow-hidden bg-[#0A0A0B] border-border/50 text-foreground">
                <DialogHeader>
                    <DialogTitle className="text-xl font-bold flex items-center gap-2">
                        <ImageIcon className="w-5 h-5 text-primary" />
                        Select from Asset Library
                    </DialogTitle>
                    <DialogDescription className="text-gray-400">
                        Choose an image from your generated assets
                    </DialogDescription>
                </DialogHeader>

                {/* Filters and Search */}
                <div className="space-y-3">
                    <div className="flex gap-2">
                        <div className="flex-1 relative">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-500" />
                            <Input
                                placeholder="Search assets..."
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                className="pl-10 bg-[#141416] border-border/50"
                            />
                        </div>
                        <Select
                            value={filters.source || "all"}
                            onValueChange={(value) =>
                                setFilters((prev) => ({
                                    ...prev,
                                    source: value === "all" ? undefined : (value as 'AI' | 'user_upload'),
                                }))
                            }
                        >
                            <SelectTrigger className="w-[180px] bg-[#141416] border-border/50">
                                <Filter className="w-4 h-4 mr-2" />
                                <SelectValue placeholder="All Sources" />
                            </SelectTrigger>
                            <SelectContent className="bg-[#141416] border-border/50 text-foreground">
                                <SelectItem value="all">All Sources</SelectItem>
                                <SelectItem value="AI">AI Generated</SelectItem>
                                <SelectItem value="user_upload">User Uploaded</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                </div>

                {/* Assets Grid */}
                <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent pr-2">
                    {loading ? (
                        <div className="flex items-center justify-center py-20">
                            <Loader2 className="w-8 h-8 animate-spin text-primary" />
                        </div>
                    ) : filteredAssets.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-20 text-gray-500">
                            <ImageIcon className="w-12 h-12 mb-3 opacity-20" />
                            <p className="text-sm">No assets found</p>
                            {search && (
                                <Button
                                    variant="link"
                                    size="sm"
                                    onClick={() => setSearch("")}
                                    className="text-primary mt-2"
                                >
                                    Clear search
                                </Button>
                            )}
                        </div>
                    ) : (
                        <div className="grid grid-cols-3 gap-3 pb-4">
                            <AnimatePresence>
                                {filteredAssets.map((asset) => (
                                    <motion.div
                                        key={asset.asset_id}
                                        layout
                                        initial={{ opacity: 0, scale: 0.9 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        exit={{ opacity: 0, scale: 0.9 }}
                                        className="relative group cursor-pointer"
                                        onClick={() => handleSelectAsset(asset)}
                                    >
                                        <div
                                            className={`relative aspect-square rounded-lg overflow-hidden border-2 transition-all ${
                                                selectedAssetId === asset.asset_id
                                                    ? "border-primary ring-2 ring-primary/20"
                                                    : "border-border/50 hover:border-primary/50"
                                            }`}
                                        >
                                            <img
                                                src={asset.cloudinary_url || asset.storage_url}
                                                alt={asset.file_name}
                                                className="w-full h-full object-cover"
                                            />
                                            
                                            {/* Overlay */}
                                            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
                                                <div className="absolute bottom-0 left-0 right-0 p-3 space-y-2">
                                                    <div className="flex items-center gap-1 flex-wrap">
                                                        {asset.generation_source === 'AI' && (
                                                            <Badge variant="secondary" className="bg-primary/20 text-primary border-primary/30 text-[10px] px-1.5 py-0.5">
                                                                <Sparkles className="w-2.5 h-2.5 mr-1" />
                                                                AI
                                                            </Badge>
                                                        )}
                                                        {asset.times_used > 0 && (
                                                            <Badge variant="outline" className="border-border/80 text-foreground text-[10px] px-1.5 py-0.5">
                                                                Used {asset.times_used}x
                                                            </Badge>
                                                        )}
                                                    </div>
                                                    <p className="text-[10px] text-white/80 font-medium truncate">
                                                        {formatFileSize(asset.file_size_bytes)}
                                                    </p>
                                                </div>
                                            </div>

                                            {/* Selected Indicator */}
                                            {selectedAssetId === asset.asset_id && (
                                                <div className="absolute top-2 right-2 bg-primary rounded-full p-1">
                                                    <Check className="w-3 h-3 text-black" />
                                                </div>
                                            )}
                                        </div>
                                    </motion.div>
                                ))}
                            </AnimatePresence>
                        </div>
                    )}
                </div>

                {/* Pagination */}
                {pagination.total_pages > 1 && (
                    <div className="flex items-center justify-between pt-3 border-t border-border/50">
                        <p className="text-xs text-gray-500">
                            Page {pagination.page} of {pagination.total_pages} ({pagination.total} assets)
                        </p>
                        <div className="flex gap-2">
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setPagination((prev) => ({ ...prev, page: prev.page - 1 }))}
                                disabled={pagination.page === 1}
                                className="bg-[#141416] border-border/50"
                            >
                                Previous
                            </Button>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setPagination((prev) => ({ ...prev, page: prev.page + 1 }))}
                                disabled={pagination.page >= pagination.total_pages}
                                className="bg-[#141416] border-border/50"
                            >
                                Next
                            </Button>
                        </div>
                    </div>
                )}
            </DialogContent>
        </Dialog>
    );
};
