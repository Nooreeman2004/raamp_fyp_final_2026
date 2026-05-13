import { useEffect, useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "@/components/Layout";
import Reveal from "@/components/ui/Reveal";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { FileText, RefreshCw, Sparkles, Trash2, Film, Images, BookImage, Copy, Check, Search, SlidersHorizontal } from "lucide-react";
import { trendService, CampaignDraftItem, CampaignDraftKind } from "@/services/trendService";
import ConfirmationDialog from "@/components/ConfirmationDialog";
import { apiClient } from "@/services/api";

const KIND_ICONS: Record<CampaignDraftKind, React.ElementType> = {
  carousel: Images,
  reel: Film,
  story: BookImage,
};

const KIND_LABELS: Record<CampaignDraftKind, string> = {
  carousel: "Carousel",
  reel: "Reel",
  story: "Story",
};

export default function CampaignDrafts() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [drafts, setDrafts] = useState<CampaignDraftItem[]>([]);
  const [deleteTarget, setDeleteTarget] = useState<CampaignDraftItem | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  
  // Filters & search
  const [search, setSearch] = useState("");
  const [kindFilter, setKindFilter] = useState<"all" | CampaignDraftKind>("all");
  const [sortBy, setSortBy] = useState<"newest" | "oldest">("newest");

  const fetchDrafts = async () => {
    setLoading(true);
    try {
      const res = await trendService.listCampaignDrafts({ limit: 80, skip: 0 });
      setDrafts(Array.isArray(res?.drafts) ? res.drafts : []);
    } catch (e: any) {
      toast.error("Failed to load drafts", { description: e?.message || "Please try again." });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDrafts();
  }, []);

  // Filter and sort drafts
  const filteredDrafts = useMemo(() => {
    const q = search.trim().toLowerCase();
    
    let filtered = drafts.filter((draft) => {
      // Kind filter
      if (kindFilter !== "all" && draft.kind !== kindFilter) return false;
      
      // Search filter
      if (q) {
        const titleMatch = draft.title.toLowerCase().includes(q);
        const keywordMatch = draft.trend_keyword?.toLowerCase().includes(q);
        const nicheMatch = draft.niche?.toLowerCase().includes(q);
        const locationMatch = draft.location?.toLowerCase().includes(q);
        const captionMatch = (draft.content?.caption || "").toLowerCase().includes(q);
        const hashtagsMatch = (draft.content?.hashtags || []).some((tag: string) => 
          tag.toLowerCase().includes(q)
        );
        
        if (!titleMatch && !keywordMatch && !nicheMatch && !locationMatch && !captionMatch && !hashtagsMatch) {
          return false;
        }
      }
      
      return true;
    });
    
    // Sort
    filtered.sort((a, b) => {
      const dateA = new Date(a.created_at).getTime();
      const dateB = new Date(b.created_at).getTime();
      return sortBy === "newest" ? dateB - dateA : dateA - dateB;
    });
    
    return filtered;
  }, [drafts, search, kindFilter, sortBy]);

  // Get unique niches and locations for additional info
  const stats = useMemo(() => {
    const niches = new Set(drafts.filter(d => d.niche).map(d => d.niche));
    const locations = new Set(drafts.filter(d => d.location).map(d => d.location));
    const byKind = {
      carousel: drafts.filter(d => d.kind === "carousel").length,
      reel: drafts.filter(d => d.kind === "reel").length,
      story: drafts.filter(d => d.kind === "story").length,
    };
    return { niches: niches.size, locations: locations.size, byKind };
  }, [drafts]);

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await apiClient.delete(`/campaign-drafts/${deleteTarget.id}`);
      setDrafts((prev) => prev.filter((d) => d.id !== deleteTarget.id));
      toast.success("Draft deleted");
    } catch (e: any) {
      toast.error("Failed to delete draft", { description: e?.message || "Please try again." });
    } finally {
      setDeleteTarget(null);
    }
  };

  const copyCaption = async (draft: CampaignDraftItem) => {
    const text =
      draft.content?.caption ||
      draft.content?.caption_prompt ||
      draft.content?.creative_prompt ||
      "";
    if (!text) { toast.error("No caption to copy"); return; }
    await navigator.clipboard.writeText(text);
    setCopiedId(draft.id);
    toast.success("Caption copied!");
    setTimeout(() => setCopiedId(null), 2000);
  };

  const openInCreativeStudio = (draft: CampaignDraftItem) => {
    const prompt =
      draft.content?.caption_prompt ||
      draft.content?.creative_prompt ||
      draft.content?.caption ||
      draft.trend_keyword ||
      "";
    navigate("/dashboard/creative", { state: { prefillPrompt: prompt } });
  };

  return (
    <Layout>
      <div className="container mx-auto px-4 py-8 max-w-5xl">
        <Reveal variant="fadeInUp">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
                <FileText className="w-6 h-6 text-primary" />
                My Drafts
              </h1>
              <p className="text-sm text-muted-foreground mt-1">
                Content drafts from Campaign Planner and Trend Arbitrage
              </p>
            </div>
            <Button variant="outline" size="sm" onClick={fetchDrafts} disabled={loading}>
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>
        </Reveal>

        {/* Filters & Search */}
        {drafts.length > 0 && (
          <Reveal variant="fadeInUp" delay={0.1}>
            <Card className="p-4 bg-card/50 border-border/50 mb-6">
              <div className="flex flex-col gap-3">
                {/* Search bar */}
                <div className="flex items-center gap-2">
                  <Search className="w-4 h-4 text-muted-foreground/60 shrink-0" />
                  <Input
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search by title, keyword, niche, location, caption..."
                    className="bg-foreground/5 border-border/50"
                  />
                </div>
                
                {/* Filters row */}
                <div className="flex items-center gap-3 flex-wrap">
                  <SlidersHorizontal className="w-4 h-4 text-muted-foreground/60 shrink-0" />
                  
                  <Select value={kindFilter} onValueChange={(v: any) => setKindFilter(v)}>
                    <SelectTrigger className="w-[140px] bg-foreground/5 border-border/50">
                      <SelectValue placeholder="Type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Types</SelectItem>
                      <SelectItem value="carousel">Carousel ({stats.byKind.carousel})</SelectItem>
                      <SelectItem value="reel">Reel ({stats.byKind.reel})</SelectItem>
                      <SelectItem value="story">Story ({stats.byKind.story})</SelectItem>
                    </SelectContent>
                  </Select>
                  
                  <Select value={sortBy} onValueChange={(v: any) => setSortBy(v)}>
                    <SelectTrigger className="w-[130px] bg-foreground/5 border-border/50">
                      <SelectValue placeholder="Sort" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="newest">Newest First</SelectItem>
                      <SelectItem value="oldest">Oldest First</SelectItem>
                    </SelectContent>
                  </Select>
                  
                  <div className="ml-auto shrink-0 text-xs font-mono font-medium text-muted-foreground uppercase tracking-widest">
                    Showing {filteredDrafts.length} of {drafts.length}
                  </div>
                </div>
              </div>
            </Card>
          </Reveal>
        )}

        {loading && drafts.length === 0 ? (
          <div className="flex justify-center py-20 text-muted-foreground text-sm">Loading drafts...</div>
        ) : drafts.length === 0 ? (
          <Reveal variant="fadeIn">
            <Card className="flex flex-col items-center justify-center py-20 gap-3 border-dashed">
              <FileText className="w-10 h-10 text-muted-foreground/40" />
              <p className="text-muted-foreground text-sm">No drafts yet.</p>
              <p className="text-xs text-muted-foreground/60">
                Use "Convert to Draft" in Campaign Planner or "Draft Content" in Trend Arbitrage.
              </p>
            </Card>
          </Reveal>
        ) : filteredDrafts.length === 0 ? (
          <Reveal variant="fadeIn">
            <Card className="flex flex-col items-center justify-center py-20 gap-3 border-dashed">
              <Search className="w-10 h-10 text-muted-foreground/40" />
              <p className="text-muted-foreground text-sm">No drafts match your filters.</p>
              <Button variant="outline" size="sm" onClick={() => { setSearch(""); setKindFilter("all"); }}>
                Clear Filters
              </Button>
            </Card>
          </Reveal>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 auto-rows-fr">
            {filteredDrafts.map((draft) => {
              const Icon = KIND_ICONS[draft.kind] ?? FileText;
              const caption: string =
                draft.content?.caption ||
                draft.content?.caption_prompt ||
                "";
              const hashtags: string[] = Array.isArray(draft.content?.hashtags)
                ? draft.content.hashtags
                : [];
              const creativePrompt: string = draft.content?.creative_prompt || "";
              return (
                <Reveal key={draft.id} variant="fadeInUp" className="h-full">
                  <Card className="p-4 flex flex-col gap-3 h-full hover:shadow-md transition-shadow">
                    {/* Header */}
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2 min-w-0">
                        <Icon className="w-4 h-4 shrink-0 text-primary" />
                        <span className="font-medium text-sm truncate">{draft.title}</span>
                      </div>
                      <Badge variant="secondary" className="shrink-0 text-[10px]">
                        {KIND_LABELS[draft.kind] ?? draft.kind}
                      </Badge>
                    </div>

                    {/* Tags */}
                    {(draft.trend_keyword || draft.niche || draft.location) && (
                      <div className="flex flex-wrap gap-1">
                        {draft.trend_keyword && (
                          <Badge variant="outline" className="text-[10px]">#{draft.trend_keyword}</Badge>
                        )}
                        {draft.niche && (
                          <Badge variant="outline" className="text-[10px]">{draft.niche}</Badge>
                        )}
                        {draft.location && (
                          <Badge variant="outline" className="text-[10px]">{draft.location}</Badge>
                        )}
                      </div>
                    )}

                    {/* Caption preview */}
                    {caption && (
                      <div className="text-[11px] font-mono text-muted-foreground/80 bg-background/60 border border-border/30 rounded p-2 line-clamp-4 whitespace-pre-wrap">
                        {caption}
                      </div>
                    )}

                    {/* Hashtags */}
                    {hashtags.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {hashtags.slice(0, 6).map((tag, i) => (
                          <span key={i} className="text-[10px] text-primary font-mono">
                            {tag.startsWith("#") ? tag : `#${tag}`}
                          </span>
                        ))}
                        {hashtags.length > 6 && (
                          <span className="text-[10px] text-muted-foreground font-mono">+{hashtags.length - 6} more</span>
                        )}
                      </div>
                    )}

                    {/* Image prompt */}
                    {creativePrompt && (
                      <div className="text-[10px] text-muted-foreground/60 italic line-clamp-2">
                        ðŸŽ¨ {creativePrompt}
                      </div>
                    )}

                    {/* Spacer to push content to bottom */}
                    <div className="flex-grow"></div>

                    <p className="text-xs text-muted-foreground">
                      {new Date(draft.created_at).toLocaleDateString(undefined, {
                        year: "numeric",
                        month: "short",
                        day: "numeric",
                      })}
                    </p>

                    {/* Actions */}
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        className="flex-1 gap-1"
                        onClick={() => openInCreativeStudio(draft)}
                      >
                        <Sparkles className="w-3 h-3" />
                        Open in Studio
                      </Button>
                      {caption && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="gap-1 border-border/50"
                          onClick={() => copyCaption(draft)}
                          title="Copy caption"
                        >
                          {copiedId === draft.id ? (
                            <Check className="w-3 h-3 text-green-500" />
                          ) : (
                            <Copy className="w-3 h-3" />
                          )}
                        </Button>
                      )}
                      <Button
                        size="sm"
                        variant="ghost"
                        className="text-destructive hover:text-destructive"
                        onClick={() => setDeleteTarget(draft)}
                      >
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  </Card>
                </Reveal>
              );
            })}
          </div>
        )}
      </div>
        
        <ConfirmationDialog
        open={!!deleteTarget}
        onOpenChange={(v) => { if (!v) setDeleteTarget(null); }}
        title="Delete draft?"
        description={`"${deleteTarget?.title}" will be permanently deleted.`}
        confirmText="Delete"
        onConfirm={handleDelete}
        variant="destructive"
      />
    </Layout>
  );
}
