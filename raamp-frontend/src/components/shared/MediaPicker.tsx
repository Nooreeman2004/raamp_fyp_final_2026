import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Upload, Library, Link2, X, CheckCircle2, Loader2, ImageIcon } from "lucide-react";
import { assetService, Asset } from "@/services/assetService";

import { API_ORIGIN } from "@/config/apiUtils";
const getAuthToken = () => localStorage.getItem("token") || sessionStorage.getItem("token");

export type MediaTab = "upload" | "library" | "url";

export function AssetLibraryPicker({ onSelect }: { onSelect: (url: string) => void }) {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    assetService.getAssetLibrary({ per_page: 40 })
      .then((r) => setAssets(r.assets))
      .catch(() => toast.error("Could not load asset library"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-40 text-muted-foreground gap-2">
        <Loader2 className="w-4 h-4 animate-spin" /> Loading assets…
      </div>
    );
  }

  if (assets.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-40 text-muted-foreground gap-2">
        <ImageIcon className="w-8 h-8 opacity-30" />
        <span className="text-sm">No assets in your library yet.</span>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-3 sm:grid-cols-4 gap-2 max-h-52 overflow-y-auto pr-1">
      {assets.map((asset) => {
        const url = asset.cloudinary_url || asset.storage_url;
        const isSelected = selected === url;
        return (
          <button
            key={asset.asset_id}
            type="button"
            onClick={() => {
              setSelected(url);
              onSelect(url);
            }}
            className={`relative rounded-lg overflow-hidden aspect-square border-2 transition-all ${
              isSelected ? "border-primary ring-2 ring-primary/40" : "border-border/40 hover:border-primary/50"
            }`}
          >
            <img src={url} alt={asset.file_name} className="w-full h-full object-cover" />
            {isSelected && (
              <div className="absolute inset-0 bg-primary/20 flex items-center justify-center">
                <CheckCircle2 className="w-6 h-6 text-primary drop-shadow" />
              </div>
            )}
          </button>
        );
      })}
    </div>
  );
}

export function DeviceUploadPicker({ onSelect }: { onSelect: (url: string) => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const handleFile = async (file: File) => {
    const objectUrl = URL.createObjectURL(file);
    setPreview(objectUrl);
    setUploading(true);
    try {
      const token = getAuthToken();
      if (!token) throw new Error("Not authenticated");
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(`${API_ORIGIN}/api/assets/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: form,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error((err as any).detail || "Upload failed");
      }
      const data = await res.json();
      const url: string = data.cloudinary_url || data.public_url || "";
      if (!url) throw new Error("No URL in upload response");
      toast.success("Uploaded!", { description: "Media ready for use." });
      onSelect(url);
    } catch (e: any) {
      toast.error("Upload failed", { description: e?.message });
      setPreview(null);
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  };

  return (
    <div
      className="border-2 border-dashed border-border/50 rounded-xl p-4 flex flex-col items-center justify-center gap-3 min-h-[9rem] cursor-pointer hover:border-primary/50 transition-colors relative"
      onClick={() => !uploading && inputRef.current?.click()}
      onDrop={handleDrop}
      onDragOver={(e) => e.preventDefault()}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/*,video/*"
        className="hidden"
        onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
      />

      {uploading ? (
        <div className="flex flex-col items-center gap-2 text-muted-foreground">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <span className="text-sm">Uploading…</span>
        </div>
      ) : preview ? (
        <div className="relative w-full">
          <img src={preview} alt="preview" className="max-h-36 mx-auto rounded-lg object-contain" />
          <button
            type="button"
            className="absolute top-1 right-1 bg-background/80 rounded-full p-0.5 hover:bg-destructive/80 transition-colors"
            onClick={(e) => { e.stopPropagation(); setPreview(null); onSelect(""); }}
          >
            <X className="w-4 h-4" />
          </button>
          <p className="text-xs text-center text-muted-foreground mt-1">Click to replace</p>
        </div>
      ) : (
        <>
          <Upload className="w-8 h-8 text-muted-foreground/50" />
          <p className="text-sm text-muted-foreground text-center">
            Drag & drop or <span className="text-primary font-medium">click to browse</span>
          </p>
          <p className="text-xs text-muted-foreground/60">JPG, PNG, MP4, MOV — max 50 MB</p>
        </>
      )}
    </div>
  );
}

export function MediaPicker({ 
  value, 
  onChange 
}: { 
  value: string; 
  onChange: (url: string) => void 
}) {
  const [activeTab, setActiveTab] = useState<MediaTab>("upload");
  const [pasteUrl, setPasteUrl] = useState("");

  const tabs: { id: MediaTab; label: string; icon: React.ReactNode }[] = [
    { id: "upload", label: "Upload", icon: <Upload className="w-3.5 h-3.5" /> },
    { id: "library", label: "Asset Lib", icon: <Library className="w-3.5 h-3.5" /> },
    { id: "url", label: "Paste URL", icon: <Link2 className="w-3.5 h-3.5" /> },
  ];

  return (
    <div className="space-y-2">
      <div className="flex rounded-lg bg-foreground/5 border border-border/40 p-0.5 gap-0.5">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setActiveTab(t.id)}
            className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 text-xs font-medium rounded-md transition-all ${
              activeTab === t.id
                ? "bg-primary text-black shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {t.icon}
            {t.label}
          </button>
        ))}
      </div>

      <div className="pt-1">
        {activeTab === "upload" && (
          <DeviceUploadPicker onSelect={onChange} />
        )}
        {activeTab === "library" && (
          <AssetLibraryPicker onSelect={onChange} />
        )}
        {activeTab === "url" && (
          <div className="space-y-2">
            <Input
              value={pasteUrl}
              onChange={(e) => {
                setPasteUrl(e.target.value);
                onChange(e.target.value);
              }}
              placeholder="https://example.com/image.jpg"
              className="bg-foreground/5 border-border/50"
            />
            <p className="text-[10px] text-muted-foreground/60">
              Must be a publicly accessible https:// URL.
            </p>
          </div>
        )}
      </div>

      {value && (
        <div className="flex items-center gap-2 bg-primary/10 border border-primary/20 rounded-lg px-3 py-2 text-xs text-primary font-mono">
          <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
          <span className="truncate">{value}</span>
          <button 
            type="button" 
            onClick={() => { onChange(""); setPasteUrl(""); }} 
            className="ml-auto shrink-0 hover:text-destructive transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </div>
  );
}
