import { useState, useEffect, useCallback, useMemo } from "react";
import { Button } from "@/components/ui/button";
import Layout from "@/components/Layout";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Zap, Sparkles, Image, FileText, MessageSquare, Copy, Check, Loader2, Trophy } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeInUp, hoverScale, hoverLift, zoomIn } from "@/utils/animations";
import { HolographicCard } from "@/components/ui/holographic-card";
import { BlurText } from "@/components/ui/text-reveal";

type Variant = {
  id: number;
  tone: string;
  caption?: string;
  hashtags?: string;
  copy?: string;
  imageColor?: string;
  imageLabel?: string;
  isRecommended?: boolean;
};

type AssetType = "instagram" | "adcopy" | "whatsapp";

const CreativeStudio = () => {
  const [campaignIdea, setCampaignIdea] = useState("");
  const [selectedAsset, setSelectedAsset] = useState<AssetType | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedVariantId, setSelectedVariantId] = useState<number | null>(null);
  const [copiedVariantId, setCopiedVariantId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedVariantData, setSelectedVariantData] = useState<Variant | null>(null);
  const [recommendedVariantId, setRecommendedVariantId] = useState<number | null>(null);
  const [isLoadingRecommendation, setIsLoadingRecommendation] = useState(false);

  const instagramVariants: Variant[] = useMemo(() => [
    {
      id: 1,
      tone: "Vibrant & Direct",
      caption: "☀️ Summer is here, and so is your new favorite organic sip! Fuel your glow from the inside out. Tap to shop!",
      hashtags: "#OrganicSummer #CleanSips #MillennialFuel #SustainableLiving"
    },
    {
      id: 2,
      tone: "Informative & Engaging",
      caption: "Did you know our new line is 100% sustainably sourced? Choose health for you and the planet. Learn more about our process on our website.",
      hashtags: "#SustainabilityGoals #EcoFriendlyDrinks #HealthConscious"
    },
    {
      id: 3,
      tone: "Curious & Playful",
      caption: "Your favorite organic ingredients, blended for the perfect summer escape. Which flavor are you trying first? Tell us below! 👇",
      hashtags: "#SmoothieTime #FlavorChallenge #TreatYourself #OrganicLife"
    }
  ], []);

  const adCopyVariants: Variant[] = useMemo(() => [
    {
      id: 1,
      tone: "Urgent/FOMO",
      imageColor: "bg-emerald-500/20",
      imageLabel: "Ad Image 1\n(Product Focus)",
      copy: "Don't just sip, thrive! Our new organic line is selling out fast. Get yours before the summer ends. Limited availability. Shop now!"
    },
    {
      id: 2,
      tone: "Benefit-focused",
      imageColor: "bg-primary/20",
      imageLabel: "Ad Image 2\n(Lifestyle Shot)",
      copy: "Finally, a smoothie line that's good for you AND the planet. Fuel your busy urban life with sustainable, organic goodness. Discover the difference today."
    },
    {
      id: 3,
      tone: "Question/Engaging",
      imageColor: "bg-red-500/20",
      imageLabel: "Ad Image 3\n(Call to Action)",
      copy: "Tired of artificial ingredients? Reset your routine with our delicious, clean-label smoothies. Which flavor boosts your day? Click to choose!"
    }
  ], []);

  const whatsappVariants: Variant[] = useMemo(() => [
    {
      id: 1,
      tone: "Direct Order Funnel",
      copy: "Hi [Name]! Ready for summer refreshment? Our organic smoothie line is now 15% off for you. Reply 'YES' to see the menu & order link instantly."
    },
    {
      id: 2,
      tone: "Educational/Soft Sell",
      copy: "Hey [Name], want a health upgrade? We just launched our organic line, and we think you'll love the sustainability story. Check out our mission here [Link]. Reply 'SMOOTHIE' for a discount code!"
    },
    {
      id: 3,
      tone: "Personalized Recommendation",
      copy: "Welcome back, [Name]! Since you loved [Old Flavor], we recommend our new 'Berry Boost'—it's 100% organic and hits those same fresh notes. Shop now: [Link]."
    }
  ], []);

  const getVariants = useCallback(() => {
    if (selectedAsset === "instagram") return instagramVariants;
    if (selectedAsset === "adcopy") return adCopyVariants;
    if (selectedAsset === "whatsapp") return whatsappVariants;
    return [];
  }, [selectedAsset, instagramVariants, adCopyVariants, whatsappVariants]);

  // Fetch AI recommendation when dialog opens
  const fetchAIRecommendation = useCallback(async () => {
    if (!selectedAsset) return;
    
    setIsLoadingRecommendation(true);
    try {
      const variants = getVariants();
      const response = await fetch('http://localhost:8000/api/variants/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          variant_type: selectedAsset,
          variants: variants.map(v => ({
            id: v.id,
            tone: v.tone,
            caption: v.caption,
            hashtags: v.hashtags,
            copy: v.copy
          }))
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setRecommendedVariantId(data.recommended_variant_id);
        toast.success('AI Recommendation Ready', {
          description: data.reason,
          duration: 4000
        });
      }
    } catch (error) {
      console.error('Failed to fetch AI recommendation:', error);
    } finally {
      setIsLoadingRecommendation(false);
    }
  }, [selectedAsset, getVariants]);

  const openDialog = (assetType: AssetType) => {
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
    
    if (selectedAsset === "instagram") {
      textToCopy = `${variant.caption || ""}\n\n${variant.hashtags || ""}`.trim();
    } else if (selectedAsset === "whatsapp" || selectedAsset === "adcopy") {
      textToCopy = variant.copy || "";
    }

    // Copy to clipboard
    try {
      await navigator.clipboard.writeText(textToCopy);
      
      // Update states
      setSelectedVariantId(variant.id);
      setCopiedVariantId(variant.id);
      
      // Show success toast
      toast.success("Copied to Clipboard!", {
        description: `Variant ${variant.id} (${variant.tone}) selected and copied`,
      });

      // Reset copied state after 2 seconds
      setTimeout(() => {
        setCopiedVariantId(null);
      }, 2000);
    } catch (error) {
      console.error("Failed to copy:", error);
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
    if (selectedAsset === "instagram") return "INSTAGRAM STORY - 3 VARIANTS";
    if (selectedAsset === "adcopy") return "AD COPY VARIATIONS - 3 VARIANTS";
    if (selectedAsset === "whatsapp") return "WHATSAPP CAMPAIGN - 3 VARIANTS";
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
              <h1 className="text-4xl font-bold mb-1 font-bebas tracking-wider text-white">
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
              <h2 className="text-xl font-bold mb-2 flex items-center gap-2 font-bebas tracking-wide text-white">
                <Sparkles className="w-5 h-5 text-primary" />
                CAMPAIGN IDEA INPUT
              </h2>
              <p className="text-xs text-muted-foreground mb-4 font-mono">
                  // DESCRIBE VISION // NATURAL LANGUAGE PROCESSING ACTIVE
              </p>
              <Textarea
                placeholder='E.g., "Create a summer promotion campaign for our new smoothie line targeting health-conscious millennials in urban areas. Emphasize organic ingredients and sustainability."'
                value={campaignIdea}
                onChange={(e) => setCampaignIdea(e.target.value)}
                className="min-h-40 mb-4 bg-black/40 text-white border-white/10 focus:border-primary/50 focus:ring-primary/20 font-mono text-sm resize-none"
              />
              <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                <Button className="w-full bg-primary text-primary-foreground hover:bg-primary/90 font-bold font-bebas tracking-wider h-12 shadow-[0_0_20px_rgba(0,224,208,0.3)]">
                  <Sparkles className="w-4 h-4 mr-2" />
                  GENERATE CREATIVE BRIEF
                </Button>
              </motion.div>
            </HolographicCard>
          </motion.div>

          {/* AI-Generated Assets */}
          <motion.div variants={fadeInUp}>
            <HolographicCard className="p-6 h-full">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2 font-bebas tracking-wide text-white">
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
                <motion.div variants={fadeInUp}>
                  <motion.div variants={hoverLift} initial="rest" whileHover="hover">
                    <div className="p-4 bg-white/5 rounded border border-white/10 hover:border-primary/30 transition-colors group">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3">
                          <div className="w-10 h-10 rounded bg-primary/10 border border-primary/20 flex items-center justify-center">
                            <Image className="w-5 h-5 text-primary" />
                          </div>
                          <div>
                            <p className="font-bold text-white font-mono text-sm">INSTAGRAM STORY</p>
                            <p className="text-[10px] text-emerald-400 font-mono flex items-center gap-1">
                              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                              READY - CAPTION & 3 HASHTAG VARIANTS
                            </p>
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-primary hover:text-primary hover:bg-primary/10 font-mono text-xs border border-primary/30"
                          onClick={() => openDialog("instagram")}
                        >
                          VIEW VARIANTS
                        </Button>
                      </div>
                    </div>
                  </motion.div>
                </motion.div>

                <motion.div variants={fadeInUp}>
                  <motion.div variants={hoverLift} initial="rest" whileHover="hover">
                    <div className="p-4 bg-white/5 rounded border border-white/10 hover:border-primary/30 transition-colors group">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3">
                          <div className="w-10 h-10 rounded bg-primary/10 border border-primary/20 flex items-center justify-center">
                            <FileText className="w-5 h-5 text-primary" />
                          </div>
                          <div>
                            <p className="font-bold text-white font-mono text-sm">AD COPY VARIATIONS</p>
                            <p className="text-[10px] text-emerald-400 font-mono flex items-center gap-1">
                              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                              READY - 3 UNIQUE BLOCKS AVAILABLE
                            </p>
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-primary hover:text-primary hover:bg-primary/10 font-mono text-xs border border-primary/30"
                          onClick={() => openDialog("adcopy")}
                        >
                          VIEW VARIANTS
                        </Button>
                      </div>
                    </div>
                  </motion.div>
                </motion.div>

                <motion.div variants={fadeInUp}>
                  <motion.div variants={hoverLift} initial="rest" whileHover="hover">
                    <div className="p-4 bg-white/5 rounded border border-white/10 hover:border-primary/30 transition-colors group">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3">
                          <div className="w-10 h-10 rounded bg-primary/10 border border-primary/20 flex items-center justify-center">
                            <MessageSquare className="w-5 h-5 text-primary" />
                          </div>
                          <div>
                            <p className="font-bold text-white font-mono text-sm">WHATSAPP CAMPAIGN</p>
                            <p className="text-[10px] text-emerald-400 font-mono flex items-center gap-1">
                              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                              READY - 3 MESSAGE FLOWS AVAILABLE
                            </p>
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
              </motion.div>
            </HolographicCard>
          </motion.div>
        </motion.div>
      </div>

      {/* Variants Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-6xl bg-black/90 backdrop-blur-xl border-white/10 p-6 shadow-[0_0_50px_rgba(0,0,0,0.8)]">
          <DialogHeader>
            <DialogTitle className="text-2xl font-bold text-white font-bebas tracking-wider flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-primary" />
              {getDialogTitle()}
            </DialogTitle>
            <DialogDescription className="text-white/50 font-mono text-xs">
              // COMPARE GENERATED VARIANTS // SELECT OPTIMAL OUTPUT
            </DialogDescription>
          </DialogHeader>

          <motion.div
            className="grid md:grid-cols-3 gap-6 mt-4"
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            key={selectedAsset} // Force re-animation on asset switch
          >
            {getVariants().map((variant) => (
              <motion.div key={variant.id} variants={zoomIn}>
                <motion.div
                  variants={hoverLift}
                  initial="rest"
                  whileHover="hover"
                  className={cn(
                    "rounded border p-4 space-y-4 h-full flex flex-col justify-between transition-all group relative overflow-hidden",
                    selectedVariantId === variant.id
                      ? "border-primary shadow-[0_0_20px_rgba(0,245,212,0.5)] bg-primary/5"
                      : "border-white/10 bg-white/5 hover:border-primary/50"
                  )}
                >
                  {/* Hover Glow */}
                  <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
                  
                  {/* AI Recommended Badge */}
                  {recommendedVariantId === variant.id && (
                    <Badge className="absolute top-2 left-2 bg-yellow-500 text-black font-mono text-[10px] z-20 font-bold flex items-center gap-1 shadow-[0_0_15px_rgba(234,179,8,0.6)]">
                      <Trophy className="w-3 h-3" />
                      AI RECOMMENDED
                    </Badge>
                  )}
                  
                  {/* Selected Badge */}
                  {selectedVariantId === variant.id && (
                    <Badge className="absolute top-2 right-2 bg-primary text-black font-mono text-[10px] z-20 font-bold">
                      ✓ SELECTED FOR POSTING
                    </Badge>
                  )}

                  <div className="space-y-4 relative z-10">
                    <div>
                      <h3 className="font-bold text-white font-bebas tracking-wide text-lg mb-1">VARIANT {variant.id}</h3>
                      <p className="text-xs text-primary font-mono uppercase border border-primary/30 inline-block px-2 py-0.5 rounded bg-primary/10">TONE: {variant.tone}</p>
                    </div>

                    {selectedAsset === "adcopy" && variant.imageColor && (
                      <div className="relative w-full h-32 rounded bg-gradient-to-br overflow-hidden" style={{ background: variant.imageColor }}>
                        <div className="text-center font-bold text-white whitespace-pre-line font-mono text-xs relative z-10 drop-shadow-md">
                          {variant.imageLabel}
                        </div>
                      </div>
                    )}

                    {variant.caption && (
                      <div>
                        <p className="text-[10px] text-white/40 font-mono uppercase mb-2">Caption Output:</p>
                        <div className="bg-black/40 border border-white/10 p-3 rounded text-sm text-white/90 font-mono leading-relaxed">
                          {variant.caption}
                        </div>
                      </div>
                    )}

                    {variant.copy && (
                      <div>
                        <p className="text-[10px] text-white/40 font-mono uppercase mb-2">Generated Copy:</p>
                        <div className="bg-black/40 border border-white/10 p-3 rounded text-sm text-white/90 font-mono leading-relaxed">
                          {variant.copy}
                        </div>
                      </div>
                    )}

                    {variant.hashtags && (
                      <div>
                        <p className="text-[10px] text-white/40 font-mono uppercase mb-2">Hashtags:</p>
                        <div className="bg-black/40 border border-white/10 p-3 rounded text-xs text-primary/80 font-mono">
                          {variant.hashtags}
                        </div>
                      </div>
                    )}
                  </div>

                  <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap" className="mt-4 relative z-10">
                    <Button 
                      onClick={() => handleCopyAndSelect(variant)}
                      disabled={isLoading}
                      className={`
                        w-full font-mono font-bold text-xs h-10 border-2 transition-all duration-300 relative overflow-hidden
                        ${
                          isLoading
                            ? "bg-primary/50 text-black/50 border-primary/50 cursor-not-allowed"
                            : selectedVariantId === variant.id
                            ? "bg-primary text-black border-primary shadow-[0_0_20px_rgba(0,245,212,0.6)]"
                            : "bg-primary/90 hover:bg-primary text-black border-primary/50 hover:border-primary hover:shadow-[0_0_25px_rgba(0,245,212,0.7)]"
                        }
                        active:scale-95
                      `}
                    >
                      {/* Neon glow effect */}
                      <div className={`
                        absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent 
                        ${selectedVariantId === variant.id ? "opacity-50" : "opacity-0 group-hover:opacity-30"}
                        transition-opacity
                      `} />
                      
                      {isLoading ? (
                        <>
                          <Loader2 className="w-3 h-3 mr-2 animate-spin" />
                          COPYING...
                        </>
                      ) : copiedVariantId === variant.id ? (
                        <>
                          <Check className="w-3 h-3 mr-2" />
                          COPIED & SELECTED
                        </>
                      ) : (
                        <>
                          <Copy className="w-3 h-3 mr-2" />
                          {selectedVariantId === variant.id ? "SELECTED" : "COPY & SELECT"}
                        </>
                      )}
                    </Button>
                  </motion.div>
                </motion.div>
              </motion.div>
            ))}
          </motion.div>

          <div className="flex justify-end mt-6">
            <Button
              variant="ghost"
              onClick={() => setIsDialogOpen(false)}
              className="text-white/50 hover:text-white hover:bg-white/10 font-mono text-xs"
            >
              CLOSE TERMINAL
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </Layout>
  );
};

export default CreativeStudio;