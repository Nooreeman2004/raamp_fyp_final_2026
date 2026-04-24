import { useState, useEffect, useCallback } from "react";
import { useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import Layout from "@/components/Layout";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Zap, Sparkles, Image, FileText, MessageSquare, Copy, Check, Loader2, Trophy, AlertCircle, Download, Video, Film, Hash, Mail, Expand, X, ChevronLeft, ChevronRight } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { API_ORIGIN, getMediaUrl } from "@/config/apiUtils";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeInUp, hoverScale, hoverLift, zoomIn } from "@/utils/animations";
import { HolographicCard } from "@/components/ui/holographic-card";
import { BlurText } from "@/components/ui/text-reveal";
import { ThemeEmoji } from "@/components/ui/emoji";

// Service imports
import {
  contentGenerationService,
  type ContentGenerationResponse,
  type ContentVariant,
  type MessageVariant
} from "@/services/contentGenerationService";
import {
  mediaGenerationService,
  type MediaGenerationResponse
} from "@/services/mediaGenerationService";
import { assetService } from "@/services/assetService";

type Variant = {
  id: number;
  caption_id?: string;  // For caption usage tracking
  hashtag_id?: string;  // For hashtag usage tracking
  message_id?: string;  // For message usage tracking
  tone: string;
  caption?: string;
  hashtags?: string;
  copy?: string;
  imagePrompt?: string;
  imagePath?: string | null;
  ml_score?: any;
  hashtag_source?: string;
};

type AssetType = "captions" | "hashtags" | "whatsapp" | "emails";

const CreativeStudio = () => {
  const location = useLocation();
  const [campaignIdea, setCampaignIdea] = useState("");

  // Pre-fill campaign idea when navigated from TrendCard "Use This Prompt"
  useEffect(() => {
    const state = location.state as { prefillPrompt?: string } | null;
    if (state?.prefillPrompt) {
      setCampaignIdea(state.prefillPrompt);
    }
  }, [location.state]);
  const [aspectRatio, setAspectRatio] = useState<'1:1' | '9:16' | '4:5'>('1:1');
  const [contentType, setContentType] = useState<'captions' | 'hashtags' | 'whatsapp' | 'emails' | 'all'>('all');
  const [imageIdea, setImageIdea] = useState("");
  const [generatedImages, setGeneratedImages] = useState<string[]>([]);
  const [imageAssetMap, setImageAssetMap] = useState<Map<string, string>>(new Map()); // image_path -> asset_id
  const [isGeneratingImages, setIsGeneratingImages] = useState(false);
  // Lightbox fullscreen preview
  const [lightboxImage, setLightboxImage] = useState<string | null>(null);
  const [lightboxIndex, setLightboxIndex] = useState<number>(0);
  // Image detail dialog
  const [showImageDetailsDialog, setShowImageDetailsDialog] = useState(false);
  const [imageThemeColor, setImageThemeColor] = useState("");
  const [imageMood, setImageMood] = useState("");
  const [imageSubject, setImageSubject] = useState("");
  const [imageStyle, setImageStyle] = useState("");
  const [selectedAsset, setSelectedAsset] = useState<AssetType | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedVariantId, setSelectedVariantId] = useState<number | null>(null);
  const [copiedVariantId, setCopiedVariantId] = useState<number | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isLoadingRecommendation, setIsLoadingRecommendation] = useState(false);
  const [recommendedVariantId, setRecommendedVariantId] = useState<number | null>(null);

  // Generated content state - starts as null until content is generated
  const [generatedContent, setGeneratedContent] = useState<ContentGenerationResponse | null>(null);
  const [hasGeneratedContent, setHasGeneratedContent] = useState(false);

  // Video/Reel generation state
  const [isGeneratingVideo, setIsGeneratingVideo] = useState(false);
  const [generatedVideos, setGeneratedVideos] = useState<MediaGenerationResponse | null>(null);
  const [videoIdea, setVideoIdea] = useState("");
  const [videoDuration, setVideoDuration] = useState(8); // Default 8 seconds (max allowed by API)

  // Prompt placeholder per content type
  const getPromptPlaceholder = () => {
    switch (contentType) {
      case 'captions':
        return 'E.g., "Launch our new matcha latte collection — highlight the health benefits and premium ingredients for health-conscious urban millennials aged 25-35."';
      case 'hashtags':
        return 'E.g., "Local artisan bakery in Lahore specialising in sourdough and croissants — targeting foodies and health-conscious customers. Growing to 10K followers."';
      case 'whatsapp':
        return 'E.g., "Weekend flash sale: 30% off all items this Saturday only — send an exciting broadcast to our WhatsApp customer list to drive foot traffic."';
      case 'emails':
        return 'E.g., "Monthly newsletter for our organic skincare brand — announce the new summer collection, feature bestsellers, and include an exclusive subscribers-only discount code SUMMER20."';
      default: // 'all'
        return 'E.g., "Create a summer promotion campaign for our new smoothie line targeting health-conscious millennials in urban areas. Emphasise organic ingredients and sustainability."';
    }
  };

  // Helper to get full image URL
  const getImageUrl = (path: string | null | undefined) => {
    return getMediaUrl(path || '');
  };

  // Convert generated content to variants for display
  const getVariants = useCallback((): Variant[] => {
    if (!generatedContent) return [];

    if (selectedAsset === "captions") {
      return generatedContent.caption_variants.map((variant: ContentVariant) => ({
        id: variant.id,
        caption_id: variant.caption_id,  // Preserve caption_id for tracking
        tone: variant.tone,
        caption: variant.caption,
        hashtags: variant.hashtags.join(" "),
        imagePrompt: generatedContent.image_prompts[variant.id - 1] || "",
        ml_score: variant.ml_score,
        hashtag_source: variant.hashtag_source
      }));
    }

    if (selectedAsset === "hashtags") {
      const setNames = ["Discovery-Focused", "Community-Focused", "Balanced Mix"];
      return (generatedContent.hashtag_sets || []).map((set: any, idx: number) => ({
        id: set.id || idx + 1,
        hashtag_id: set.hashtag_id,  // Preserve hashtag_id for tracking
        tone: setNames[idx] || `Set ${idx + 1}`,
        hashtags: Array.isArray(set) ? set.join(" ") : (set.hashtags || []).join(" "),
        copy: Array.isArray(set) ? set.join(" ") : (set.hashtags || []).join(" ")
      }));
    }

    if (selectedAsset === "whatsapp") {
      const variants = generatedContent.whatsapp_variants && generatedContent.whatsapp_variants.length > 0
        ? generatedContent.whatsapp_variants
        : generatedContent.message_variants;

      return variants.map((variant: MessageVariant, idx: number) => ({
        id: variant.id,
        message_id: variant.message_id,
        tone: variant.tone,
        copy: variant.message,
        imagePath: (generatedContent.image_paths || [])[idx] || null,
        ml_score: variant.ml_score
      }));
    }

    if (selectedAsset === "emails") {
      const variants = generatedContent.email_variants && generatedContent.email_variants.length > 0
        ? generatedContent.email_variants
        : generatedContent.message_variants;

      return variants.map((variant: MessageVariant) => ({
        id: variant.id,
        message_id: variant.message_id,
        tone: variant.tone,
        copy: variant.message,
        imagePath: null // Emails don't show the generated images in the preview card
      }));
    }

    return [];
  }, [selectedAsset, generatedContent]);

  // Handle content generation
  const handleGenerateContent = async () => {
    if (!campaignIdea.trim()) {
      toast.error("Campaign Idea Required", {
        description: "Please enter a campaign idea before generating content."
      });
      return;
    }

    if (campaignIdea.trim().length < 10) {
      toast.error("Campaign Idea Too Short", {
        description: "Please provide a more detailed campaign description (at least 10 characters)."
      });
      return;
    }

    setIsGenerating(true);
    try {
      console.log("🚀 Starting content generation:", {
        campaign_idea: campaignIdea.trim().substring(0, 50) + "...",
        aspect_ratio: aspectRatio,
        content_type: contentType,
        timestamp: new Date().toISOString()
      });

      toast.info("Generating Content...", {
        description: `AI is creating your ${contentType} content. This may take 10-15 seconds.`,
        duration: 15000
      });

      const response = await contentGenerationService.generateContent({
        campaign_idea: campaignIdea.trim(),
        aspect_ratio: aspectRatio,
        content_type: contentType
      });

      console.log("✅ Content generation response:", {
        success: response.success,
        caption_variants: response.caption_variants?.length || 0,
        hashtag_sets: response.hashtag_sets?.length || 0,
        whatsapp_variants: response.whatsapp_variants?.length || 0,
        email_variants: response.email_variants?.length || 0,
        image_paths: response.image_paths?.length || 0,
        generated_at: response.generated_at
      });

      setGeneratedContent(response);
      setHasGeneratedContent(true);

      // Auto-set AI recommendation based on ML best variant
      if (contentType === 'captions') {
        setRecommendedVariantId(response.best_caption_id);
      } else if (contentType === 'hashtags') {
        setRecommendedVariantId(response.best_hashtag_set_id);
      } else {
        setRecommendedVariantId(response.best_message_id);
      }

      // Store image_path -> asset_id mapping for campaign images too
      if (response.image_paths && response.asset_ids) {
        const newMap = new Map<string, string>();
        response.image_paths.forEach((path, idx) => {
          if (response.asset_ids[idx]) {
            newMap.set(path, response.asset_ids[idx]);
          }
        });
        // Merge with existing map (in case standalone image generation was used)
        setImageAssetMap(prev => new Map([...prev, ...newMap]));
      }

      toast.success("Content Generated Successfully!", {
        description: `View your AI-generated variants for Instagram, Ad Copy, and WhatsApp.`,
        duration: 5000
      });
    } catch (error) {
      console.error("❌ Content generation failed:", {
        error: error,
        message: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined,
        timestamp: new Date().toISOString()
      });
      
      const msg = error instanceof Error ? error.message : String(error);
      
      // Show detailed error to user
      toast.error("Content Generation Failed", {
        description: msg || "Unable to create content. Check console for details.",
        duration: 10000
      });
    } finally {
      setIsGenerating(false);
    }
  };

  // Handle Reel/Video generation
  const handleGenerateReel = async () => {
    if (!videoIdea.trim()) {
      toast.error("Reel Idea Required", {
        description: "Please describe your Reel idea before generating."
      });
      return;
    }

    if (videoIdea.trim().length < 10) {
      toast.error("Reel Idea Too Short", {
        description: "Please provide more details about your Reel (at least 10 characters)."
      });
      return;
    }

    setIsGeneratingVideo(true);
    try {
      const generatingToast = toast.info("Generating Instagram Reel...", {
        description: `AI is creating your ${videoDuration}s vertical video. Please wait 2-5 minutes...`,
        duration: 300000 // 5 minutes
      });

      const response = await mediaGenerationService.generateQuickReel({
        idea: videoIdea.trim(),
        duration_seconds: videoDuration
      });

      setGeneratedVideos(response);
      toast.dismiss(generatingToast);

      toast.success("Reel Generated Successfully!", {
        description: `Your ${response.duration_seconds}s vertical Reel is ready to preview and download!`,
        duration: 8000
      });
    } catch (error) {
      console.error("Reel generation failed:", error);

      // User-friendly error messages based on common issues
      const errorMessage = error instanceof Error && error.message.includes('429')
        ? "API quota exceeded. Please try again later or upgrade your plan."
        : error instanceof Error && error.message.includes('401')
          ? "Authentication failed. Please log in again."
          : "Reel generation failed. Please check your connection and try again.";

      toast.error("Reel Generation Failed", {
        description: errorMessage,
        duration: 6000
      });
    } finally {
      setIsGeneratingVideo(false);
    }
  };

  const handleGenerateVideo = async () => {
    if (!videoIdea.trim()) {
      toast.error("Video Idea Required", {
        description: "Please describe your video idea before generating."
      });
      return;
    }

    if (videoIdea.trim().length < 10) {
      toast.error("Video Idea Too Short", {
        description: "Please provide more details about your video (at least 10 characters)."
      });
      return;
    }

    setIsGeneratingVideo(true);
    try {
      const generatingToast = toast.info("Generating Video...", {
        description: `AI is creating your ${videoDuration}s horizontal video. Please wait 2-5 minutes...`,
        duration: 300000 // 5 minutes
      });

      // First generate prompt
      toast.loading("Step 1/2: Creating video script...", { duration: 2000 });
      const promptResponse = await mediaGenerationService.generateVideoPrompt({
        idea: videoIdea.trim(),
        aspect_ratio: '16:9'
      });

      // Then generate video from prompt
      toast.loading("Step 2/2: Generating video (2-5 min)...", { duration: 300000 });
      const response = await mediaGenerationService.generateVideos({
        video_prompt: promptResponse.video_prompt,
        duration_seconds: videoDuration,
        aspect_ratio: '16:9',
        count: 1
      });

      setGeneratedVideos(response);
      toast.dismiss(generatingToast);

      toast.success("Video Generated Successfully!", {
        description: `Your ${response.duration_seconds}s horizontal video is ready to preview and download!`,
        duration: 8000
      });
    } catch (error) {
      console.error("Video generation failed:", error);

      // User-friendly error messages based on common issues
      const errorMessage = error instanceof Error && error.message.includes('429')
        ? "API quota exceeded. Please try again later or upgrade your plan."
        : error instanceof Error && error.message.includes('401')
          ? "Authentication failed. Please log in again."
          : "Video generation failed. Please check your connection and try again.";

      toast.error("Video Generation Failed", {
        description: errorMessage,
        duration: 6000
      });
    } finally {
      setIsGeneratingVideo(false);
    }
  };

  const handleGenerateImages = async (skipDialog = false) => {
    const basePrompt = imageIdea.trim() || campaignIdea.trim();
    if (!basePrompt) {
      toast.error("Image Idea Required", {
        description: "Enter an image description or fill in the campaign idea above."
      });
      return;
    }
    // If details not provided and dialog hasn't been shown, show it first
    // SKIP dialog if current prompt already has substantial content (>100 chars)
    const isDetailedPrompt = basePrompt.length > 50;
    if (!skipDialog && !isDetailedPrompt && (!imageThemeColor && !imageMood && !imageSubject && !imageStyle)) {
      setShowImageDetailsDialog(true);
      return;
    }
    setIsGeneratingImages(true);
    setShowImageDetailsDialog(false);
    // Build an enriched prompt using extra details
    let enrichedPrompt = basePrompt;
    if (imageSubject) enrichedPrompt += `. Subject: ${imageSubject}`;
    if (imageMood) enrichedPrompt += `. Mood/Atmosphere: ${imageMood}`;
    if (imageThemeColor) enrichedPrompt += `. Color palette: ${imageThemeColor}`;
    if (imageStyle) enrichedPrompt += `. Visual style: ${imageStyle}`;
    try {
      toast.info("Generating Images...", {
        description: "AI is crafting your brand images. This may take 20-30 seconds.",
        duration: 30000
      });
      const response = await contentGenerationService.generateContent({
        campaign_idea: enrichedPrompt,
        aspect_ratio: aspectRatio,
        content_type: 'images'
      });
      setGeneratedImages(response.image_paths || []);

      // Store image_path -> asset_id mapping for usage tracking
      if (response.image_paths && response.asset_ids) {
        const newMap = new Map<string, string>();
        response.image_paths.forEach((path, idx) => {
          if (response.asset_ids[idx]) {
            newMap.set(path, response.asset_ids[idx]);
          }
        });
        setImageAssetMap(newMap);
      }

      if ((response.image_paths?.length || 0) > 0) {
        toast.success("Images Generated!", {
          description: `${response.image_paths!.length} image(s) are ready to download.`
        });
      } else {
        toast.warning("No Images Returned", {
          description: "The AI couldn't generate images. Try adding more details or a different prompt."
        });
      }
    } catch (error) {
      console.error("Image generation failed:", error);
      toast.error("Image Generation Failed", {
        description: "Unable to generate images. Please check your connection and try again."
      });
    } finally {
      setIsGeneratingImages(false);
    }
  };

  // Fetch AI recommendation when dialog opens
  const fetchAIRecommendation = useCallback(async () => {
    if (!selectedAsset || !generatedContent) return;

    setIsLoadingRecommendation(true);
    try {
      const variants = getVariants();

      const request = {
        variant_type: selectedAsset,
        variants: variants.map(v => ({
          id: v.id,
          tone: v.tone,
          caption: v.caption,
          hashtags: v.hashtags,
          variant_copy: v.copy
        }))
      };

      const data = await contentGenerationService.getVariantRecommendation(request);
      setRecommendedVariantId(data.recommended_variant_id);

      toast.success('AI Recommendation Ready', {
        description: data.reason,
        duration: 4000
      });
    } catch (error) {
      console.error('Failed to fetch AI recommendation:', error);
      // Don't show error toast - recommendations are nice-to-have
    } finally {
      setIsLoadingRecommendation(false);
    }
  }, [selectedAsset, generatedContent, getVariants]);

  const openDialog = (assetType: AssetType) => {
    if (!hasGeneratedContent) {
      toast.error("No Content Generated", {
        description: "Please generate content first by clicking 'Generate Creative Brief'."
      });
      return;
    }

    setSelectedAsset(assetType);
    setIsDialogOpen(true);
    setSelectedVariantId(null);
    setCopiedVariantId(null);
    setRecommendedVariantId(null);
  };

  // Fetch AI recommendation when dialog opens
  useEffect(() => {
    if (isDialogOpen && selectedAsset) {
      fetchAIRecommendation();
    }
  }, [isDialogOpen, selectedAsset, fetchAIRecommendation]);

  const handleCopyAndSelect = useCallback(async (variant: Variant) => {
    // Construct text to copy based on variant type
    let textToCopy = "";

    if (selectedAsset === "captions") {
      textToCopy = `${variant.caption || ""}\n\n${variant.hashtags || ""}`.trim();
    } else if (selectedAsset === "hashtags") {
      textToCopy = variant.hashtags || variant.copy || "";
    } else if (selectedAsset === "whatsapp" || selectedAsset === "emails") {
      textToCopy = variant.copy || "";
    }

    // Copy to clipboard
    try {
      await navigator.clipboard.writeText(textToCopy);

      // Track caption usage if this is a caption variant
      if (selectedAsset === "captions" && variant.caption_id) {
        try {
          await assetService.markCaptionUsed(variant.caption_id);
          console.log(`✅ Caption usage tracked: ${variant.caption_id}`);
        } catch (trackError) {
          console.error("Failed to track caption usage:", trackError);
          toast.warning("Caption tracking failed", {
            description: "Your copy succeeded, but analytics for this caption might be delayed."
          });
        }
      }

      // Track hashtag usage if this is a hashtag variant
      if (selectedAsset === "hashtags" && variant.hashtag_id) {
        try {
          await assetService.markCaptionUsed(variant.hashtag_id);  // Hashtags use same endpoint
          console.log(`✅ Hashtag usage tracked: ${variant.hashtag_id}`);
        } catch (trackError) {
          console.error("Failed to track hashtag usage:", trackError);
          toast.warning("Hashtag tracking failed", {
            description: "Your copy succeeded, but analytics for these hashtags might be delayed."
          });
        }
      }

      // Track message usage if this is a WhatsApp/Email variant
      if ((selectedAsset === "whatsapp" || selectedAsset === "emails") && variant.message_id) {
        try {
          await assetService.markCaptionUsed(variant.message_id);  // Messages use same endpoint
          console.log(`✅ Message usage tracked: ${variant.message_id}`);
        } catch (trackError) {
          console.error("Failed to track message usage:", trackError);
          toast.warning("Message tracking failed", {
            description: "Your copy succeeded, but analytics for this message might be delayed."
          });
        }
      }
      toast.success("Copied to clipboard!");
    } catch (error) {
      toast.error("Failed to Copy", {
        description: "Unable to copy to clipboard. Please try again.",
      });
    }
  }, [selectedAsset]);

  // Keyboard shortcut: Cmd/Ctrl + Enter to select first variant
  useEffect(() => {
    if (!isDialogOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd + Enter (Mac) or Ctrl + Enter (Windows/Linux)
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        e.preventDefault();
        const variants = getVariants();
        if (variants && variants.length > 0) {
          // Select the first variant if none selected, otherwise reselect current
          const variantToSelect = selectedVariantId
            ? variants.find(v => v.id === selectedVariantId)
            : variants[0];
          if (variantToSelect) {
            handleCopyAndSelect(variantToSelect);
          }
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isDialogOpen, selectedVariantId, getVariants, handleCopyAndSelect]);

  const getDialogTitle = () => {
    if (selectedAsset === "captions") return "INSTAGRAM CAPTIONS — 3 VARIANTS";
    if (selectedAsset === "hashtags") return "HASHTAG SETS — 3 STRATEGY SETS";
    if (selectedAsset === "whatsapp") return "WHATSAPP CAMPAIGN — 3 VARIANTS";
    if (selectedAsset === "emails") return "EMAIL CAMPAIGN — 3 VARIANTS";
    return "";
  };

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <Reveal variant="blurInUp">
          <div className="flex items-center gap-4 mb-2">
            <div className="p-3 bg-primary/10 rounded border border-primary/30">
              <Sparkles className="w-8 h-8 text-primary animate-pulse" />
            </div>
            <div>
              <h1 className="text-4xl font-bold mb-1 font-heading font-semibold text-foreground">
                <BlurText text="GENERATIVE CREATIVE STUDIO" />
              </h1>
              <p className="text-muted-foreground font-mono text-sm">
                  // AI-POWERED ASSET GENERATION // CAMPAIGN ACCELERATION
              </p>
            </div>
          </div>
        </Reveal>

        {/* Main Grid */}
        <motion.div
          className="grid lg:grid-cols-2 gap-6"
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
        >
          {/* Campaign Idea Input */}
          <motion.div variants={fadeInUp}>
            <HolographicCard className="p-6 h-full border-primary/30">
              <h2 className="text-xl font-bold mb-2 flex items-center gap-2 font-heading font-semibold text-foreground">
                <Sparkles className="w-5 h-5 text-primary" />
                CAMPAIGN IDEA INPUT
              </h2>
              <p className="text-xs text-muted-foreground mb-4 font-mono">
                  // DESCRIBE VISION // NATURAL LANGUAGE PROCESSING ACTIVE
              </p>

              {/* Content Parameters */}
              <div className="mb-4 space-y-3">
                <label className="text-xs font-mono text-muted-foreground mb-1 block">
                  CONTENT PARAMETERS
                </label>
                <div>
                  <label className="text-[10px] font-mono text-muted-foreground/80 mb-1 block">CONTENT TYPE</label>
                  <Select value={contentType} onValueChange={(value: 'captions' | 'hashtags' | 'whatsapp' | 'emails' | 'all') => setContentType(value)}>
                    <SelectTrigger className="w-full bg-card text-foreground border-border/50 focus:border-primary/50 focus:ring-primary/20 font-mono text-sm">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-card border-border/50">
                      <SelectItem value="all" className="font-mono text-sm text-foreground"><ThemeEmoji name="sparkles" className="mr-1" /> All Types</SelectItem>
                      <SelectItem value="captions" className="font-mono text-sm text-foreground"><ThemeEmoji name="pencil" className="mr-1" /> Captions</SelectItem>
                      <SelectItem value="hashtags" className="font-mono text-sm text-foreground"><ThemeEmoji name="tag" className="mr-1" /> Hashtags</SelectItem>
                      <SelectItem value="whatsapp" className="font-mono text-sm text-foreground"><ThemeEmoji name="whatsapp" className="mr-1" /> WhatsApp / Images</SelectItem>
                      <SelectItem value="emails" className="font-mono text-sm text-foreground"><ThemeEmoji name="email" className="mr-1" /> Emails</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <Textarea
                placeholder={getPromptPlaceholder()}
                value={campaignIdea}
                onChange={(e) => setCampaignIdea(e.target.value)}
                className="min-h-40 mb-4 bg-card text-foreground border-border/50 focus:border-primary/50 focus:ring-primary/20 font-mono text-sm resize-none"
              />
              <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                <Button
                  onClick={handleGenerateContent}
                  disabled={isGenerating || !campaignIdea.trim()}
                  className="w-full bg-primary text-primary-foreground hover:bg-primary/90 font-bold font-heading font-semibold h-12 shadow-[0_0_20px_rgba(0,224,208,0.3)] disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      GENERATING AI CONTENT...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 mr-2" />
                      GENERATE CREATIVE BRIEF
                    </>
                  )}
                </Button>
              </motion.div>
            </HolographicCard>
          </motion.div>

          {/* AI-Generated Assets */}
          <motion.div variants={fadeInUp}>
            <HolographicCard className="p-6 h-full">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2 font-heading font-semibold text-foreground">
                <Zap className="w-5 h-5 text-primary" />
                AI-GENERATED ASSETS
              </h2>

              {/* List Stagger */}
              <motion.div
                className="space-y-3"
                variants={staggerContainer}
                initial="hidden"
                animate="visible"
              >
                {/* CAPTIONS card */}
                {(contentType === 'captions' || contentType === 'all') && (
                  <motion.div variants={fadeInUp}>
                    <motion.div variants={hoverLift} initial="rest" whileHover="hover">
                      <div className="p-4 bg-foreground/5 rounded border border-border/50 hover:border-primary/30 transition-colors group">
                        <div className="flex items-start justify-between">
                          <div className="flex items-start gap-3">
                            <div className="w-10 h-10 rounded bg-primary/10 border border-primary/20 flex items-center justify-center">
                              <FileText className="w-5 h-5 text-primary" />
                            </div>
                            <div>
                              <p className="font-bold text-foreground font-mono text-sm">CAPTIONS</p>
                              {hasGeneratedContent ? (
                                <p className="text-[10px] text-emerald-400 font-mono flex items-center gap-1">
                                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                                  READY — 3 CAPTION VARIANTS
                                </p>
                              ) : (
                                <p className="text-[10px] text-amber-400 font-mono flex items-center gap-1">
                                  <AlertCircle className="w-3 h-3" />
                                  GENERATE CONTENT FIRST
                                </p>
                              )}
                            </div>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-primary hover:text-primary hover:bg-primary/10 font-mono text-xs border border-primary/30"
                            onClick={() => openDialog("captions")}
                          >
                            VIEW VARIANTS
                          </Button>
                        </div>
                      </div>
                    </motion.div>
                  </motion.div>
                )}

                {/* HASHTAGS card */}
                {(contentType === 'hashtags' || contentType === 'all') && (
                  <motion.div variants={fadeInUp}>
                    <motion.div variants={hoverLift} initial="rest" whileHover="hover">
                      <div className="p-4 bg-foreground/5 rounded border border-border/50 hover:border-primary/30 transition-colors group">
                        <div className="flex items-start justify-between">
                          <div className="flex items-start gap-3">
                            <div className="w-10 h-10 rounded bg-primary/10 border border-primary/20 flex items-center justify-center">
                              <Hash className="w-5 h-5 text-primary" />
                            </div>
                            <div>
                              <p className="font-bold text-foreground font-mono text-sm">HASHTAG SETS</p>
                              {hasGeneratedContent ? (
                                <p className="text-[10px] text-emerald-400 font-mono flex items-center gap-1">
                                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                                  READY — 3 STRATEGY SETS
                                </p>
                              ) : (
                                <p className="text-[10px] text-amber-400 font-mono flex items-center gap-1">
                                  <AlertCircle className="w-3 h-3" />
                                  GENERATE CONTENT FIRST
                                </p>
                              )}
                            </div>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-primary hover:text-primary hover:bg-primary/10 font-mono text-xs border border-primary/30"
                            onClick={() => openDialog("hashtags")}
                          >
                            VIEW SETS
                          </Button>
                        </div>
                      </div>
                    </motion.div>
                  </motion.div>
                )}

                {/* WHATSAPP card */}
                {(contentType === 'whatsapp' || contentType === 'all') && (
                  <motion.div variants={fadeInUp}>
                    <motion.div variants={hoverLift} initial="rest" whileHover="hover">
                      <div className="p-4 bg-foreground/5 rounded border border-border/50 hover:border-primary/30 transition-colors group">
                        <div className="flex items-start justify-between">
                          <div className="flex items-start gap-3">
                            <div className="w-10 h-10 rounded bg-primary/10 border border-primary/20 flex items-center justify-center">
                              <MessageSquare className="w-5 h-5 text-primary" />
                            </div>
                            <div>
                              <p className="font-bold text-foreground font-mono text-sm">WHATSAPP CAMPAIGN</p>
                              {hasGeneratedContent ? (
                                <p className="text-[10px] text-emerald-400 font-mono flex items-center gap-1">
                                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                                  READY — 3 BROADCAST MESSAGES
                                </p>
                              ) : (
                                <p className="text-[10px] text-amber-400 font-mono flex items-center gap-1">
                                  <AlertCircle className="w-3 h-3" />
                                  GENERATE CONTENT FIRST
                                </p>
                              )}
                            </div>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-primary hover:text-primary hover:bg-primary/10 font-mono text-xs border border-primary/30"
                            onClick={() => openDialog("whatsapp")}
                          >
                            VIEW VARIANTS
                          </Button>
                        </div>
                      </div>
                    </motion.div>
                  </motion.div>
                )}

                {/* EMAILS card */}
                {(contentType === 'emails' || contentType === 'all') && (
                  <motion.div variants={fadeInUp}>
                    <motion.div variants={hoverLift} initial="rest" whileHover="hover">
                      <div className="p-4 bg-foreground/5 rounded border border-border/50 hover:border-primary/30 transition-colors group">
                        <div className="flex items-start justify-between">
                          <div className="flex items-start gap-3">
                            <div className="w-10 h-10 rounded bg-primary/10 border border-primary/20 flex items-center justify-center">
                              <Mail className="w-5 h-5 text-primary" />
                            </div>
                            <div>
                              <p className="font-bold text-foreground font-mono text-sm">EMAIL CAMPAIGN</p>
                              {hasGeneratedContent ? (
                                <p className="text-[10px] text-emerald-400 font-mono flex items-center gap-1">
                                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                                  READY — 3 EMAIL VARIANTS
                                </p>
                              ) : (
                                <p className="text-[10px] text-amber-400 font-mono flex items-center gap-1">
                                  <AlertCircle className="w-3 h-3" />
                                  GENERATE CONTENT FIRST
                                </p>
                              )}
                            </div>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-primary hover:text-primary hover:bg-primary/10 font-mono text-xs border border-primary/30"
                            onClick={() => openDialog("emails")}
                          >
                            VIEW VARIANTS
                          </Button>
                        </div>
                      </div>
                    </motion.div>
                  </motion.div>
                )}
              </motion.div>
            </HolographicCard>
          </motion.div>
        </motion.div>

        {/* Image Generation Section */}
        <motion.div
          variants={fadeInUp}
          initial="hidden"
          animate="visible"
        >
          <HolographicCard className="p-6 border-primary/30">
            <h2 className="text-2xl font-bold mb-2 flex items-center gap-2 font-heading font-semibold text-foreground">
              <Image className="w-6 h-6 text-primary" />
              IMAGE GENERATION
            </h2>
            <p className="text-xs text-muted-foreground mb-6 font-mono">
              // AI-POWERED IMAGE CREATION // ASPECT RATIO CONTROL
            </p>
            <div className="grid lg:grid-cols-2 gap-6">
              {/* Input Section */}
              <div>
                <div className="mb-4">
                  <label className="text-xs font-mono text-muted-foreground mb-2 block">
                    IMAGE IDEA
                  </label>
                  <Textarea
                    placeholder='E.g., "A vibrant flat-lay of our summer product lineup on a sandy beach with golden hour lighting — warm, aspirational, lifestyle aesthetic"'
                    value={imageIdea}
                    onChange={(e) => setImageIdea(e.target.value)}
                    className="min-h-32 bg-card text-foreground border-border/50 focus:border-primary/50 focus:ring-primary/20 font-mono text-sm resize-none"
                  />
                  <p className="text-[10px] text-muted-foreground/60 font-mono mt-1">
                    Leave empty to use your campaign idea above
                  </p>
                </div>

                <div className="mb-4">
                  <label className="text-xs font-mono text-muted-foreground mb-2 block">
                    ASPECT RATIO
                  </label>
                  <Select value={aspectRatio} onValueChange={(value: '1:1' | '9:16' | '4:5') => setAspectRatio(value)}>
                    <SelectTrigger className="w-full bg-card text-foreground border-border/50 focus:border-primary/50 focus:ring-primary/20 font-mono text-sm">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-card border-border/50">
                      <SelectItem value="1:1" className="font-mono text-sm text-foreground"><ThemeEmoji name="square" className="mr-1" /> 1:1 — Square</SelectItem>
                      <SelectItem value="9:16" className="font-mono text-sm text-foreground"><ThemeEmoji name="ruler" className="mr-1" /> 9:16 — Vertical</SelectItem>
                      <SelectItem value="4:5" className="font-mono text-sm text-foreground"><ThemeEmoji name="frame" className="mr-1" /> 4:5 — Portrait</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                  <Button
                    onClick={() => handleGenerateImages(false)}
                    disabled={isGeneratingImages || (!imageIdea.trim() && !campaignIdea.trim())}
                    className="w-full bg-primary text-primary-foreground hover:bg-primary/90 font-bold font-heading font-semibold h-12 shadow-[0_0_20px_rgba(0,224,208,0.3)] disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isGeneratingImages ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        GENERATING IMAGES...
                      </>
                    ) : (
                      <>
                        <Image className="w-4 h-4 mr-2" />
                        GENERATE IMAGES
                      </>
                    )}
                  </Button>
                </motion.div>

                <div className="mt-4 p-3 bg-card border border-primary/20 rounded">
                  <p className="text-[10px] text-primary font-mono font-bold mb-1">⚡ IMAGE GENERATION INFO:</p>
                  <ul className="text-[10px] text-muted-foreground font-mono space-y-1">
                    <li>• Generates <span className="text-primary">3 image variations</span> per request</li>
                    <li>• Select aspect ratio to match your platform (Square, Vertical, Portrait)</li>
                    <li>• <span className="text-amber-400">Generation time: 10-20 seconds</span></li>
                  </ul>
                </div>
              </div>

              {/* Preview Section */}
              <div>
                <div className="bg-card border border-border/50 rounded p-4 min-h-[320px] flex flex-col">
                  {generatedImages.length > 0 ? (
                    <div className="w-full">
                      {/* Header */}
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-sm font-bold text-foreground font-heading font-semibold flex items-center gap-2">
                          <Image className="w-4 h-4 text-primary" />
                          GENERATED IMAGES
                        </h3>
                        <Badge className="bg-emerald-500 text-black font-mono text-[10px] font-bold">
                          ✓ {generatedImages.length} READY
                        </Badge>
                      </div>

                      {/* 3-column grid — mirrors caption layout */}
                      <div className="grid grid-cols-3 gap-3">
                        {generatedImages.map((imagePath, idx) => {
                          const isAiPick = idx === 0;
                          const imageUrl = imagePath.startsWith('http')
                            ? imagePath
                            : imagePath;   // goes through Vite proxy automatically

                          return (
                            <motion.div
                              key={idx}
                              variants={fadeInUp}
                              initial="hidden"
                              animate="visible"
                              className={`relative rounded-xl border overflow-hidden group flex flex-col transition-all duration-300 ${isAiPick
                                ? 'border-primary/60 shadow-[0_0_16px_rgba(0,245,212,0.2)]'
                                : 'border-border/50 hover:border-border/90'
                                }`}
                            >
                              {/* AI Recommended Badge */}
                              {isAiPick && (
                                <div className="absolute top-2 left-2 z-10">
                                  <Badge className="bg-primary text-black text-[9px] font-mono font-bold px-1.5 py-0.5 flex items-center gap-1 shadow-lg">
                                    <Trophy className="w-2.5 h-2.5" />
                                    AI PICK
                                  </Badge>
                                </div>
                              )}

                              {/* Variation Label top-right */}
                              <div className="absolute top-2 right-2 z-10">
                                <span className="bg-black/70 text-muted-foreground/80 text-[9px] font-mono px-1.5 py-0.5 rounded">
                                  VAR {idx + 1}
                                </span>
                              </div>

                              {/* Image container — fixed height, image fits */}
                              <div className="relative w-full h-52 bg-background/60 flex items-center justify-center overflow-hidden">
                                <img
                                  src={imageUrl}
                                  alt={`Generated image variation ${idx + 1}`}
                                  className="w-full h-full object-contain"
                                  onError={(e) => {
                                    const el = e.target as HTMLImageElement;
                                    el.style.display = 'none';
                                    if (el.parentElement) {
                                      el.parentElement.innerHTML = `
                                        <div class="flex flex-col items-center justify-center w-full h-full gap-2 text-center px-2">
                                          <svg xmlns="http://www.w3.org/2000/svg" class="w-8 h-8 text-white/20" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14M6 4h12a2 2 0 012 2v12a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2z"/></svg>
                                          <p class="text-[10px] text-white/30 font-mono">Failed to load</p>
                                          <p class="text-[9px] text-white/20 font-mono">Retry generation</p>
                                        </div>`;
                                    }
                                  }}
                                />

                                {/* Hover overlay with download + expand */}
                                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-end justify-between p-2">
                                  {/* Expand / fullscreen */}
                                  <button
                                    onClick={() => { setLightboxIndex(idx); setLightboxImage(imageUrl); }}
                                    className="bg-black/70 hover:bg-white/20 text-foreground rounded-full p-1.5 transition-all shadow-lg"
                                    title="View fullscreen"
                                  >
                                    <Expand className="w-3 h-3" />
                                  </button>
                                  {/* Download */}
                                  <button
                                    onClick={async () => {
                                      const link = document.createElement('a');
                                      link.href = imageUrl;
                                      link.download = `raamp_image_${idx + 1}.png`;
                                      link.target = '_blank';
                                      document.body.appendChild(link);
                                      link.click();
                                      document.body.removeChild(link);
                                      const assetId = imageAssetMap.get(imagePath);
                                      if (assetId) {
                                        try { await assetService.markAssetUsed(assetId); } catch { }
                                      }
                                      toast.success("Download Started", {
                                        description: `Saving variation ${idx + 1} to downloads`
                                      });
                                    }}
                                    className="bg-primary/90 hover:bg-primary text-black rounded-full p-1.5 transition-all shadow-lg"
                                    title="Download image"
                                  >
                                    <Download className="w-3 h-3" />
                                  </button>
                                </div>
                              </div>

                              {/* Footer label */}
                              <div className={`px-2 py-1.5 text-center ${isAiPick ? 'bg-primary/10' : 'bg-card'}`}>
                                <p className={`text-[10px] font-mono font-bold ${isAiPick ? 'text-primary' : 'text-muted-foreground/80'}`}>
                                  {isAiPick ? '⭐ RECOMMENDED' : `VARIATION ${idx + 1}`}
                                </p>
                              </div>
                            </motion.div>
                          );
                        })}
                      </div>
                    </div>
                  ) : (
                    <div className="flex-1 flex flex-col items-center justify-center text-center">
                      <Image className="w-16 h-16 text-white/20 mx-auto mb-3" />
                      <p className="text-muted-foreground/60 font-mono text-sm mb-2">No images generated yet</p>
                      <p className="text-[10px] text-white/30 font-mono">
                        Enter an image idea and click Generate Images
                      </p>
                    </div>
                  )}
                </div>
              </div>

            </div>
          </HolographicCard>
        </motion.div>

        {/* Video/Reel Generation Section */}
        <motion.div
          variants={fadeInUp}
          initial="hidden"
          animate="visible"
        >
          <HolographicCard className="p-6 border-primary/30">
            <h2 className="text-2xl font-bold mb-2 flex items-center gap-2 font-heading font-semibold text-foreground">
              <Video className="w-6 h-6 text-primary" />
              VIDEO & REEL GENERATION
            </h2>
            <p className="text-xs text-muted-foreground mb-6 font-mono">
              // GENERATE INSTAGRAM REELS (9:16 VERTICAL) OR VIDEOS (16:9 HORIZONTAL) // 4-8 SECONDS
            </p>

            <div className="grid lg:grid-cols-2 gap-6">
              {/* Input Section */}
              <div>
                <div className="mb-4">
                  <label className="text-xs font-mono text-muted-foreground mb-2 block">
                    VIDEO/REEL IDEA
                  </label>
                  <Textarea
                    placeholder='E.g., "Show a person opening our new product box with excitement, revealing the contents in slow motion with dynamic camera movements"'
                    value={videoIdea}
                    onChange={(e) => setVideoIdea(e.target.value)}
                    className="min-h-32 bg-card text-foreground border-border/50 focus:border-primary/50 focus:ring-primary/20 font-mono text-sm resize-none"
                  />
                </div>

                <div className="mb-4">
                  <label className="text-xs font-mono text-muted-foreground mb-2 block">
                    DURATION (4-8 SECONDS)
                  </label>
                  <Select
                    value={videoDuration.toString()}
                    onValueChange={(value) => setVideoDuration(parseInt(value))}
                  >
                    <SelectTrigger className="w-full bg-card text-foreground border-border/50 focus:border-primary/50 focus:ring-primary/20 font-mono text-sm">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-card border-border/50">
                      <SelectItem value="4" className="font-mono text-sm text-foreground">4 seconds</SelectItem>
                      <SelectItem value="5" className="font-mono text-sm text-foreground">5 seconds</SelectItem>
                      <SelectItem value="6" className="font-mono text-sm text-foreground">6 seconds</SelectItem>
                      <SelectItem value="7" className="font-mono text-sm text-foreground">7 seconds</SelectItem>
                      <SelectItem value="8" className="font-mono text-sm text-foreground">8 seconds (recommended)</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-[10px] text-white/30 font-mono mt-1">
                    Duration is limited to 8 seconds max per generation
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                    <Button
                      onClick={handleGenerateReel}
                      disabled={isGeneratingVideo || !videoIdea.trim()}
                      className="w-full bg-primary text-primary-foreground hover:bg-primary/90 font-bold font-heading font-semibold h-12 shadow-[0_0_20px_rgba(0,224,208,0.3)] disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isGeneratingVideo ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          GENERATING...
                        </>
                      ) : (
                        <>
                          <Film className="w-4 h-4 mr-2" />
                          REEL (9:16)
                        </>
                      )}
                    </Button>
                  </motion.div>

                  <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                    <Button
                      onClick={handleGenerateVideo}
                      disabled={isGeneratingVideo || !videoIdea.trim()}
                      className="w-full bg-primary/80 text-primary-foreground hover:bg-primary/70 font-bold font-heading font-semibold h-12 shadow-[0_0_20px_rgba(0,224,208,0.2)] disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isGeneratingVideo ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          GENERATING...
                        </>
                      ) : (
                        <>
                          <Video className="w-4 h-4 mr-2" />
                          VIDEO (16:9)
                        </>
                      )}
                    </Button>
                  </motion.div>
                </div>

                <div className="mt-4 p-3 bg-card border border-primary/20 rounded">
                  <p className="text-[10px] text-primary font-mono font-bold mb-1">⚡ KEY DIFFERENCES:</p>
                  <ul className="text-[10px] text-muted-foreground font-mono space-y-1">
                    <li>• <span className="text-primary">REEL (9:16)</span>: Vertical format for Instagram Reels, TikTok, YouTube Shorts</li>
                    <li>• <span className="text-primary">VIDEO (16:9)</span>: Horizontal format for YouTube, Facebook, Instagram Feed</li>
                    <li>• <span className="text-amber-400">Duration limit: 4-8 seconds</span> (API constraint, cannot be changed)</li>
                    <li>• <span className="text-amber-400">Generates 1 video per request</span> (unlike captions which create 3 variants)</li>
                  </ul>
                </div>
              </div>

              {/* Preview Section */}
              <div>
                <div className="bg-card border border-border/50 rounded p-4 min-h-[400px] flex flex-col items-center justify-center">
                  {generatedVideos && generatedVideos.media_paths.length > 0 ? (
                    <div className="w-full space-y-4">
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="text-sm font-bold text-foreground font-heading font-semibold">
                          GENERATED MEDIA
                        </h3>
                        <Badge className="bg-emerald-500 text-black font-mono text-[10px]">
                          ✓ READY
                        </Badge>
                      </div>

                      {generatedVideos.media_paths.map((path, idx) => (
                        <div key={idx} className="space-y-4 flex flex-col items-center">
                          <div
                            className={`
                              relative rounded-xl overflow-hidden border border-border/50 bg-background/60 shadow-2xl
                              ${generatedVideos.aspect_ratio === '9:16' ? 'max-w-[280px]' : 'w-full max-w-[600px]'}
                              transition-all duration-500
                            `}
                          >
                            <video
                              controls
                              className="w-full h-auto max-h-[500px]"
                              src={mediaGenerationService.getMediaUrl(path)}
                            >
                              Your browser does not support the video tag.
                            </video>
                          </div>

                          <Button
                            onClick={async () => {
                              const downloadToast = toast.loading("Preparing download...", { duration: 5000 });

                              // Track video asset usage if asset_id is available
                              if (generatedVideos.asset_ids && generatedVideos.asset_ids[idx]) {
                                try {
                                  await assetService.markAssetUsed(generatedVideos.asset_ids[idx]);
                                  console.log(`✅ Video asset usage tracked: ${generatedVideos.asset_ids[idx]}`);
                                } catch (trackError) {
                                  console.error("Failed to track video asset usage:", trackError);
                                  toast.warning("Usage tracking failed", {
                                    description: "Your download will proceed, but analytics for this asset might be delayed."
                                  });
                                }
                              }

                              mediaGenerationService.downloadMedia(
                                path,
                                `generated_media_${idx + 1}.mp4`
                              ).then(() => {
                                toast.dismiss(downloadToast);
                                toast.success("Download Started", {
                                  description: `Saving media ${idx + 1} to your downloads folder`
                                });
                              }).catch(() => {
                                toast.dismiss(downloadToast);
                                toast.error("Download Failed", {
                                  description: "Unable to download video. Please try again or check your connection."
                                });
                              });
                            }}
                            className="w-full max-w-[400px] bg-primary/20 hover:bg-primary/30 text-primary border border-primary/30 font-mono text-xs h-10 shadow-[0_0_15px_rgba(0,224,208,0.1)]"
                          >
                            <Download className="w-3 h-3 mr-2" />
                            DOWNLOAD VIDEO {idx + 1}
                          </Button>
                        </div>
                      ))}

                      <div className="mt-4 p-3 bg-primary/10 border border-primary/30 rounded">
                        <p className="text-[10px] text-primary font-mono">
                          ✓ Generated {generatedVideos.count} video(s) • {generatedVideos.duration_seconds}s each
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center">
                      <Film className="w-16 h-16 text-white/20 mx-auto mb-3" />
                      <p className="text-muted-foreground/60 font-mono text-sm mb-2">No videos generated yet</p>
                      <p className="text-[10px] text-white/30 font-mono">
                        Enter an idea and click a generation button
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </HolographicCard>
        </motion.div>
      </div>

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-[95vw] w-[95vw] h-fit max-h-[95vh] flex flex-col bg-background/90 backdrop-blur-xl border-border/50 p-0 shadow-[0_0_50px_rgba(0,0,0,0.8)] overflow-hidden transition-all duration-300">

          <div className="p-6 pb-4 border-b border-border/50 shrink-0 relative bg-black/50 z-10">
            <DialogHeader>
              <DialogTitle className="text-2xl font-bold text-foreground font-heading font-semibold flex items-center gap-2 pr-8">
                <Sparkles className="w-5 h-5 text-primary" />
                {getDialogTitle()}
              </DialogTitle>
              <DialogDescription className="text-muted-foreground/80 font-mono text-xs mt-1">
                // COMPARE GENERATED VARIANTS // SELECT OPTIMAL OUTPUT
              </DialogDescription>
            </DialogHeader>
          </div>

          <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
            {/* AI-Generated Images Section */}
            {generatedContent && generatedContent.image_paths && generatedContent.image_paths.length > 0 && (
              <motion.div
                className="mb-8"
                variants={fadeInUp}
                initial="hidden"
                animate="visible"
              >
                <h3 className="text-sm font-bold text-foreground font-heading font-semibold mb-3 flex items-center gap-2">
                  <Image className="w-4 h-4 text-primary" />
                  AI-GENERATED IMAGES
                </h3>
                <div className="grid grid-cols-3 gap-4">
                  {generatedContent.image_paths.map((imagePath, idx) => (
                    <div
                      key={idx}
                      className="relative rounded border border-border/50 overflow-hidden hover:border-primary/50 transition-all group"
                    >
                      <img
                        src={getImageUrl(imagePath)}
                        alt={`Generated variation ${idx + 1}`}
                        className="w-full h-auto object-cover"
                        onError={(e) => {
                          // Fallback if image fails to load
                          const img = e.target;
                          if (img instanceof HTMLImageElement) {
                            img.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="400"%3E%3Crect fill="%23000" width="400" height="400"/%3E%3Ctext fill="%2300f5d4" font-family="monospace" font-size="16" x="50%25" y="50%25" text-anchor="middle" dominant-baseline="middle"%3EImage Loading...%3C/text%3E%3C/svg%3E';
                          }
                        }}
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end justify-between p-3">
                        <p className="text-[10px] text-foreground font-mono">Variation {idx + 1}</p>
                        <button
                          onClick={async () => {
                            const link = document.createElement('a');
                            link.href = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}${imagePath}`;
                            link.download = `generated_variation_${idx + 1}.png`;
                            document.body.appendChild(link);
                            link.click();
                            document.body.removeChild(link);

                            const assetId = imageAssetMap.get(imagePath);
                            if (assetId) {
                              try {
                                await assetService.markAssetUsed(assetId);
                              } catch (error) {
                                console.error('Failed to track image usage:', error);
                                toast.warning("Image tracking failed", {
                                  description: "Your download will proceed, but analytics for this image might be delayed."
                                });
                              }
                            }

                            toast.success("Download Started", {
                              description: `Downloading variation ${idx + 1}`
                            });
                          }}
                          className="bg-primary/90 hover:bg-primary text-primary-foreground rounded-full p-2 transition-colors"
                        >
                          <Download className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
                {generatedContent.image_generation_prompt && (
                  <div className="mt-3 p-3 bg-card border border-border/50 rounded">
                    <p className="text-[10px] text-muted-foreground/60 font-mono uppercase mb-1">Image Generation Prompt:</p>
                    <p className="text-xs text-muted-foreground font-mono leading-relaxed">{generatedContent.image_generation_prompt.replace(/\*\*/g, '')}</p>
                  </div>
                )}
              </motion.div>
            )}

            <motion.div
              className="grid md:grid-cols-3 gap-6"
              variants={staggerContainer}
              initial="hidden"
              animate="visible"
              key={selectedAsset}
            >
              {getVariants().map((variant) => (
                <motion.div key={variant.id} variants={zoomIn} className="flex flex-col h-full">
                  <motion.div
                    variants={hoverLift}
                    initial="rest"
                    whileHover="hover"
                    className={cn(
                      "rounded-xl border p-5 flex flex-col h-full transition-all group relative overflow-hidden",
                      selectedVariantId === variant.id
                        ? "border-primary shadow-[0_0_30px_rgba(0,245,212,0.2)] bg-primary/10"
                        : "border-border bg-[#09151E] hover:border-primary/40 shadow-xl"
                    )}
                  >
                    <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />

                    {recommendedVariantId === variant.id && (
                      <Badge className="absolute top-3 left-4 bg-yellow-500 text-black font-mono text-[9px] z-20 font-bold flex items-center gap-1 shadow-lg py-1 px-3 border-none">
                        <Trophy className="w-3 h-3" />
                        AI RECOMMENDED
                      </Badge>
                    )}

                    {selectedVariantId === variant.id && (
                      <Badge className="absolute top-3 right-4 bg-primary text-black font-mono text-[9px] z-20 font-bold py-1 px-3">
                        ✓ SELECTED
                      </Badge>
                    )}

                    {variant.ml_score && (
                      <Badge className="absolute bottom-20 right-4 bg-emerald-500/10 text-emerald-400 font-mono text-[8px] z-20 font-bold py-0.5 px-2 border border-emerald-500/20 backdrop-blur-sm">
                        <Zap className="w-2.5 h-2.5 mr-1 inline" />
                        OPTIMIZED PREDICTION
                      </Badge>
                    )}



                    <div className={cn("flex flex-col flex-1 relative z-10", recommendedVariantId === variant.id || selectedVariantId === variant.id ? "pt-10" : "")}>
                      <div className="flex flex-col gap-1 border-l-2 border-primary/20 pl-3 mb-4 shrink-0">
                        <h3 className="font-heading font-semibold text-3xl text-foreground tracking-wider leading-none">VARIANT {variant.id}</h3>
                        <p className="text-[11px] text-primary/80 font-mono tracking-widest bg-primary/20 px-2 py-0.5 rounded inline-block self-start">
                          {variant.tone}
                        </p>
                      </div>

                      {/* ML PERFORMANCE METRIC - NEW */}
                      {variant.ml_score && (
                        <div className="mb-4 p-2.5 bg-black/40 border border-primary/10 rounded-lg flex items-center justify-between">
                          <div className="flex flex-col">
                            <span className="text-[9px] text-muted-foreground/60 font-mono uppercase tracking-tighter">Engagement Potential</span>
                            <div className="flex items-center gap-1.5 mt-0.5">
                              <span className={cn(
                                "text-lg font-bold font-mono tracking-tight",
                                variant.ml_score.score_label === "Strong" ? "text-emerald-400" : 
                                variant.ml_score.score_label === "Moderate" ? "text-amber-400" : "text-rose-400"
                              )}>
                                {(variant.ml_score.engagement_rate * 100).toFixed(1)}%
                              </span>
                              <Badge className={cn(
                                "text-[10px] py-0 px-1.5 border-none font-mono font-bold",
                                variant.ml_score.score_label === "Strong" ? "bg-emerald-400/20 text-emerald-400" : 
                                variant.ml_score.score_label === "Moderate" ? "bg-amber-400/20 text-amber-400" : "bg-rose-400/20 text-rose-400"
                              )}>
                                {variant.ml_score.score_label.toUpperCase()}
                              </Badge>
                            </div>
                          </div>
                          
                          <div className="text-right flex flex-col items-end">
                            <span className="text-[9px] text-muted-foreground/60 font-mono uppercase tracking-tighter">AI Confidence</span>
                            <span className={cn(
                              "text-[10px] font-mono font-bold mt-0.5",
                              variant.ml_score.confidence === "High" ? "text-primary" : 
                              variant.ml_score.confidence === "Medium" ? "text-amber-400" : "text-white/40"
                            )}>
                              {variant.ml_score.confidence.toUpperCase()}
                            </span>
                          </div>
                        </div>
                      )}


                      {variant.caption && (
                        <div className="flex-1 flex flex-col min-h-0">
                          <p className="text-[10px] text-muted-foreground/60 font-mono uppercase mb-2 tracking-widest shrink-0">Caption Output:</p>
                          <div className="bg-background/60 border border-border/50 p-4 rounded-lg text-[13px] text-foreground font-mono leading-relaxed whitespace-pre-wrap overflow-y-auto custom-scrollbar border-l-2 border-primary/20 flex-1">
                            {variant.caption.split(/(\*\*.*?\*\*)/g).filter(Boolean).map((part, i) => {
                              if (part.startsWith('**') && part.endsWith('**')) {
                                const content = part.slice(2, -2).trim();
                                if (!content) return null;
                                return <strong key={i} className="font-bold text-foreground">{content}</strong>;
                              }
                              return <span key={i} className="text-white/90">{part}</span>;
                            })}
                          </div>
                        </div>
                      )}

                      {variant.copy && selectedAsset !== "hashtags" && (
                        <div className="space-y-3 flex-1 flex flex-col min-h-0">
                          <p className="text-[10px] text-muted-foreground/60 font-mono uppercase mb-2 tracking-widest shrink-0">
                            {selectedAsset === "emails" ? "Full Email Content:" : "Message Body:"}
                          </p>
                          <div className={cn(
                            "bg-background/60 border border-border/50 p-5 rounded-lg text-[13px] text-foreground font-mono leading-relaxed whitespace-pre-wrap overflow-y-auto custom-scrollbar flex-1",
                            selectedAsset === "emails" ? "border-l-4 border-l-primary/50" : "border-l-2 border-l-primary/30"
                          )}>
                            {variant.copy.split(/(\*\*.*?\*\*)/g).filter(Boolean).map((part, i) => {
                              if (part.startsWith('**') && part.endsWith('**')) {
                                const content = part.slice(2, -2).trim();
                                if (!content) return null;
                                return <strong key={i} className="font-bold text-foreground">{content}</strong>;
                              }
                              return <span key={i} className="text-white/90">{part}</span>;
                            })}
                          </div>
                        </div>
                      )}

                      {variant.hashtags && selectedAsset !== "captions" && selectedAsset === "hashtags" && (
                        <div className="shrink-0">
                          <p className="text-[10px] text-muted-foreground/60 font-mono uppercase mb-2">Hashtag Set Strategy:</p>
                          <div className="bg-background/60 border border-border p-3 rounded flex flex-wrap gap-1.5 min-h-[100px]">
                            {(variant.hashtags || "").split(" ").filter(Boolean).map((tag, i) => (
                              <span key={i} className="px-2 py-0.5 rounded bg-primary/10 text-primary border border-primary/20 font-mono text-[10px] hover:bg-primary/20 transition-colors">
                                {tag}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {variant.hashtags && selectedAsset === "captions" && (
                        <div className="shrink-0 mt-4">
                          <div className="flex items-center justify-between mb-2">
                            <p className="text-[10px] text-muted-foreground/60 font-mono uppercase tracking-widest">Engagement Hashtags:</p>
                            {variant.hashtag_source && (
                              <span className="text-[8px] text-primary/60 font-mono uppercase bg-primary/10 px-1.5 py-0.5 rounded border border-primary/20">
                                {variant.hashtag_source.includes('ml') ? '✨ ML RECOMMENDED' : '🤖 AI GENERATED'}
                              </span>
                            )}
                          </div>
                          <div className="bg-primary/5 border border-primary/20 p-3 rounded text-[11px] text-primary/90 font-mono leading-relaxed">

                            {variant.hashtags.replace(/\*\*/g, '')}
                          </div>
                        </div>
                      )}
                    </div>

                    <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap" className="mt-5 shrink-0 relative z-10">
                      <Button
                        onClick={() => handleCopyAndSelect(variant)}
                        className={`
                          w-full font-mono font-bold text-xs h-10 border-2 transition-all duration-300 relative overflow-hidden
                          ${selectedVariantId === variant.id
                            ? "bg-primary text-black border-primary shadow-[0_0_20px_rgba(0,245,212,0.6)]"
                            : "bg-primary/90 hover:bg-primary text-black border-primary/50 hover:border-primary hover:shadow-[0_0_25px_rgba(0,245,212,0.7)]"
                          }
                          active:scale-95
                        `}
                      >
                        <div className={`
                          absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent 
                          ${selectedVariantId === variant.id ? "opacity-50" : "opacity-0 group-hover:opacity-30"}
                          transition-opacity
                        `} />

                        {copiedVariantId === variant.id ? (
                          <>
                            <Check className="w-3 h-3 mr-2" />
                            COPIED & SELECTED
                          </>
                        ) : (
                          <>
                            <Copy className="w-3 h-3 mr-2" />
                            {selectedVariantId === variant.id ? "SELECTED" : (selectedAsset === "whatsapp" ? "SELECT CAMPAIGN" : "COPY & SELECT")}
                          </>
                        )}
                      </Button>
                    </motion.div>
                  </motion.div>
                </motion.div>
              ))}
            </motion.div>
          </div>

          <div className="p-4 border-t border-border/50 shrink-0 flex justify-end bg-black/50 z-10">
            <Button
              variant="ghost"
              onClick={() => setIsDialogOpen(false)}
              className="text-muted-foreground/80 hover:text-foreground hover:bg-foreground/10 font-mono text-xs"
            >
              CLOSE TERMINAL
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Image Details Dialog */}
      <Dialog open={showImageDetailsDialog} onOpenChange={setShowImageDetailsDialog}>
        <DialogContent className="max-w-lg bg-[#060d13] border border-primary/20 p-6 shadow-[0_0_40px_rgba(0,245,212,0.1)]">
          <DialogHeader>
            <DialogTitle className="text-xl font-bold text-foreground font-heading font-semibold flex items-center gap-2">
              <Image className="w-5 h-5 text-primary" />
              ENHANCE YOUR IMAGE
            </DialogTitle>
            <DialogDescription className="text-muted-foreground/80 font-mono text-xs">
              // TELL THE AI MORE // BETTER DETAILS = BETTER IMAGES
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div>
              <label className="text-[10px] font-mono text-muted-foreground/80 uppercase tracking-widest mb-1.5 block">
                Subject / Main Focus
              </label>
              <input
                type="text"
                placeholder="e.g., A glowing bottle of perfume, a happy customer, a latte"
                value={imageSubject}
                onChange={(e) => setImageSubject(e.target.value)}
                className="w-full bg-background/60 border border-border/50 rounded px-3 py-2 text-sm text-foreground font-mono focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20 placeholder:text-white/20"
              />
            </div>
            <div>
              <label className="text-[10px] font-mono text-muted-foreground/80 uppercase tracking-widest mb-1.5 block">
                Mood / Atmosphere
              </label>
              <input
                type="text"
                placeholder="e.g., Elegant & luxurious, warm & friendly, energetic & bold"
                value={imageMood}
                onChange={(e) => setImageMood(e.target.value)}
                className="w-full bg-background/60 border border-border/50 rounded px-3 py-2 text-sm text-foreground font-mono focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20 placeholder:text-white/20"
              />
            </div>
            <div>
              <label className="text-[10px] font-mono text-muted-foreground/80 uppercase tracking-widest mb-1.5 block">
                Theme / Color Palette
              </label>
              <input
                type="text"
                placeholder="e.g., Deep teal & gold, pastel pink, dark moody black & white"
                value={imageThemeColor}
                onChange={(e) => setImageThemeColor(e.target.value)}
                className="w-full bg-background/60 border border-border/50 rounded px-3 py-2 text-sm text-foreground font-mono focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20 placeholder:text-white/20"
              />
            </div>
            <div>
              <label className="text-[10px] font-mono text-muted-foreground/80 uppercase tracking-widest mb-1.5 block">
                Visual Style
              </label>
              <input
                type="text"
                placeholder="e.g., Minimalist flat-lay, 3D product render, cinematic lifestyle"
                value={imageStyle}
                onChange={(e) => setImageStyle(e.target.value)}
                className="w-full bg-background/60 border border-border/50 rounded px-3 py-2 text-sm text-foreground font-mono focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/20 placeholder:text-white/20"
              />
            </div>
            <div className="flex gap-2 pt-2">
              <Button
                onClick={() => handleGenerateImages(true)}
                className="flex-1 bg-primary text-black font-bold font-mono text-xs h-10 hover:bg-primary/90 shadow-[0_0_20px_rgba(0,245,212,0.3)]"
              >
                <Sparkles className="w-3 h-3 mr-2" />
                GENERATE WITH DETAILS
              </Button>
              <Button
                variant="ghost"
                onClick={() => handleGenerateImages(true)}
                className="border border-border/50 text-muted-foreground/80 hover:text-foreground hover:bg-foreground/5 font-mono text-xs h-10 px-4"
              >
                SKIP
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* ── Lightbox / Fullscreen Image Viewer ── */}
      {lightboxImage && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/95 backdrop-blur-md"
          onClick={() => setLightboxImage(null)}
        >
          {/* Close */}
          <button
            onClick={() => setLightboxImage(null)}
            className="absolute top-4 right-4 z-10 bg-foreground/10 hover:bg-white/20 text-foreground rounded-full p-2.5 transition-all border border-border/50"
          >
            <X className="w-5 h-5" />
          </button>

          {/* Counter + Download */}
          <div className="absolute top-4 left-4 z-10 flex items-center gap-3">
            <span className="text-muted-foreground/80 font-mono text-xs bg-background/60 px-3 py-1.5 rounded-full border border-border/50">
              {lightboxIndex + 1} / {generatedImages.length}
              {lightboxIndex === 0 && (
                <span className="ml-2 text-primary">★ AI PICK</span>
              )}
            </span>
            <button
              onClick={async (e) => {
                e.stopPropagation();
                const link = document.createElement('a');
                link.href = lightboxImage;
                link.download = `raamp_image_${lightboxIndex + 1}.png`;
                link.target = '_blank';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                toast.success(`Downloading variation ${lightboxIndex + 1}`);
              }}
              className="flex items-center gap-1.5 bg-primary/90 hover:bg-primary text-black text-xs font-mono font-bold px-3 py-1.5 rounded-full transition-all shadow-[0_0_12px_rgba(0,245,212,0.3)]"
            >
              <Download className="w-3 h-3" />
              DOWNLOAD
            </button>
          </div>

          {/* Prev arrow */}
          {generatedImages.length > 1 && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                const prev = (lightboxIndex - 1 + generatedImages.length) % generatedImages.length;
                setLightboxIndex(prev);
                setLightboxImage(generatedImages[prev]);
              }}
              className="absolute left-4 top-1/2 -translate-y-1/2 bg-foreground/10 hover:bg-white/20 text-foreground rounded-full p-3 transition-all border border-border/50"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
          )}

          {/* Image */}
          <motion.img
            key={lightboxImage}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.2 }}
            src={lightboxImage}
            alt={`Generated image variation ${lightboxIndex + 1}`}
            className="max-h-[85vh] max-w-[85vw] object-contain rounded-xl shadow-2xl border border-border/50"
            onClick={(e) => e.stopPropagation()}
          />

          {/* Next arrow */}
          {generatedImages.length > 1 && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                const next = (lightboxIndex + 1) % generatedImages.length;
                setLightboxIndex(next);
                setLightboxImage(generatedImages[next]);
              }}
              className="absolute right-4 top-1/2 -translate-y-1/2 bg-foreground/10 hover:bg-white/20 text-foreground rounded-full p-3 transition-all border border-border/50"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          )}

          {/* Thumbnail strip */}
          {generatedImages.length > 1 && (
            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2">
              {generatedImages.map((img, i) => (
                <button
                  key={i}
                  onClick={(e) => { e.stopPropagation(); setLightboxIndex(i); setLightboxImage(img); }}
                  className={`w-14 h-14 rounded-lg overflow-hidden border-2 transition-all ${i === lightboxIndex ? 'border-primary scale-110 shadow-[0_0_10px_rgba(0,245,212,0.5)]' : 'border-border/80 opacity-60 hover:opacity-100'
                    }`}
                >
                  <img src={img} alt={`thumb ${i + 1}`} className="w-full h-full object-cover" />
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </Layout>

  );
};

export default CreativeStudio;