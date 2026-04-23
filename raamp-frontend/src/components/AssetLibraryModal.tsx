import { useState, useEffect } from "react";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Search, Sparkles, Video, Check, Loader2 } from "lucide-react";
import { assetService, type Asset } from "@/services/assetService";
import { toast } from "sonner";
import { ThemeEmoji } from "@/components/ui/emoji";

interface AssetLibraryModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSelect: (assets: Asset[]) => void;
    maxSelection?: number;
    /** How many images are already selected outside the modal (device + library already chosen) */
    alreadySelected?: number;
}

const AssetLibraryModal = ({ isOpen, onClose, onSelect, maxSelection = 5, alreadySelected = 0 }: AssetLibraryModalProps) => {
    const remainingSlots = maxSelection - alreadySelected;
    const [assets, setAssets] = useState<Asset[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedIds, setSelectedIds] = useState<string[]>([]);
    
    useEffect(() => {
        if (isOpen) {
            fetchAssets();
        }
    }, [isOpen]);

    const fetchAssets = async () => {
        setIsLoading(true);
        try {
            // Fetch images for A/B testing
            const response = await assetService.getAssetLibrary({
                per_page: 50
            });
            
            // Only show images or videos for A/B testing (usually images)
            const mediaAssets = response.assets.filter(a => 
                a.asset_type === 'generated_image' || 
                a.asset_type === 'uploaded_image'
            );
            
            setAssets(mediaAssets);
        } catch (error: any) {
            toast.error("Failed to load assets", { description: error.message });
        } finally {
            setIsLoading(false);
        }
    };

    const toggleSelection = (asset: Asset) => {
        setSelectedIds(prev => {
            if (prev.includes(asset.asset_id)) {
                return prev.filter(id => id !== asset.asset_id);
            }
            if (prev.length >= remainingSlots) {
                toast.warning(
                    remainingSlots === 0
                        ? `You already have ${alreadySelected} images selected. Remove some to add library images.`
                        : `You can only add ${remainingSlots} more image${remainingSlots === 1 ? '' : 's'} (max ${maxSelection} total)`
                );
                return prev;
            }
            return [...prev, asset.asset_id];
        });
    };

    const handleConfirm = () => {
        const selectedAssets = assets.filter(a => selectedIds.includes(a.asset_id));
        onSelect(selectedAssets);
        onClose();
        setSelectedIds([]);
    };

    const filteredAssets = assets.filter(a => 
        a.file_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        a.generation_prompt?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const getMediaUrl = (path: string | null | undefined) => {
        if (!path) return '';
        if (path.startsWith('http')) return path;
        const cleanPath = path.startsWith('/') ? path : `/${path}`;
        return `${window.location.origin}${cleanPath}`;
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="max-w-4xl max-h-[80vh] flex flex-col">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <ThemeEmoji name="folder" /> Select from Assets Library
                    </DialogTitle>
                </DialogHeader>

                <div className="flex items-center gap-4 mb-4">
                    <div className="relative flex-1">
                        <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Search your library..."
                            className="pl-9"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </div>
                    <Badge variant="outline" className="h-10 px-4">
                        {selectedIds.length} / {remainingSlots} Slots Used
                    </Badge>
                </div>

                <div className="flex-1 overflow-y-auto pr-2">
                    {isLoading ? (
                        <div className="flex flex-col items-center justify-center py-20 gap-4">
                            <Loader2 className="w-8 h-8 animate-spin text-primary" />
                            <p className="text-muted-foreground font-mono text-sm">Accessing Library...</p>
                        </div>
                    ) : filteredAssets.length === 0 ? (
                        <div className="text-center py-20 bg-muted/30 rounded-lg border-2 border-dashed">
                            <p className="text-muted-foreground">No matching images found in your library.</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                            {filteredAssets.map((asset) => {
                                const isSelected = selectedIds.includes(asset.asset_id);
                                return (
                                    <div
                                        key={asset.asset_id}
                                        className={`group relative aspect-square rounded-lg overflow-hidden border-2 transition-all cursor-pointer ${
                                            isSelected ? 'border-primary ring-2 ring-primary/20' : 'border-transparent hover:border-border'
                                        }`}
                                        onClick={() => toggleSelection(asset)}
                                    >
                                        <img
                                            src={getMediaUrl(asset.cloudinary_url || asset.storage_url)}
                                            alt={asset.file_name}
                                            className="w-full h-full object-cover"
                                        />
                                        
                                        {asset.generation_source === 'AI' && (
                                            <div className="absolute top-2 left-2">
                                                <Badge className="bg-primary/90 text-[10px] h-5 px-1.5">
                                                    <Sparkles className="w-2.5 h-2.5 mr-1" /> AI
                                                </Badge>
                                            </div>
                                        )}

                                        {isSelected && (
                                            <div className="absolute inset-0 bg-primary/20 flex items-center justify-center">
                                                <div className="bg-primary text-white rounded-full p-1 shadow-lg">
                                                    <Check className="w-5 h-5" />
                                                </div>
                                            </div>
                                        )}

                                        <div className="absolute bottom-0 inset-x-0 bg-black/60 p-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <p className="text-[10px] text-white truncate font-mono">
                                                {asset.file_name}
                                            </p>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>

                <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
                    <Button variant="ghost" onClick={onClose}>
                        Cancel
                    </Button>
                    <Button 
                        onClick={handleConfirm} 
                        disabled={selectedIds.length < 1}
                        className="gap-2"
                    >
                        Confirm Selection ({selectedIds.length})
                    </Button>
                </div>
            </DialogContent>
        </Dialog>
    );
};

export default AssetLibraryModal;
