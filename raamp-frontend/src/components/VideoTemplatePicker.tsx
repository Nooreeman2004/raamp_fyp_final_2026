import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import { ThemeEmoji } from "@/components/ui/emoji";
import type { LucideIcon } from "lucide-react";
import { Zap, Film, Sparkles, BookOpen, Rocket, Star, Package, Eye, Mic, Scale, Search, Timer, HelpCircle, Target } from "lucide-react";

interface VideoTemplate {
    id: string;
    name: string;
    category: string;
    prompt: string;
    duration: string;
    tags: string[];
    icon: LucideIcon;
}

const VIDEO_TEMPLATES: VideoTemplate[] = [
    // Quick Cuts (15-30s)
    {
        id: "quick-montage",
        name: "5 Ways Montage",
        category: "Quick Cuts",
        icon: Zap,
        prompt: "Fast-paced montage showing 5 ways to use {product} with upbeat music, quick cuts, energetic and engaging",
        duration: "15-20s",
        tags: ["montage", "fast", "energetic"]
    },
    {
        id: "day-in-life",
        name: "Behind the Scenes",
        category: "Quick Cuts",
        icon: Film,
        prompt: "Day in the life: Behind-the-scenes of making {dish/product} from start to finish, authentic and engaging",
        duration: "20-30s",
        tags: ["bts", "process", "authentic"]
    },
    {
        id: "transformation",
        name: "Transformation Reveal",
        category: "Quick Cuts",
        icon: Sparkles,
        prompt: "Transformation reveal: Slow-mo of {before → after} with dramatic music, satisfying and impactful",
        duration: "10-15s",
        tags: ["reveal", "slowmo", "dramatic"]
    },
    {
        id: "tutorial",
        name: "Quick Tutorial",
        category: "Quick Cuts",
        icon: BookOpen,
        prompt: "Recipe/Tutorial: Step-by-step process with text overlays and trending audio, clear and easy to follow",
        duration: "20-30s",
        tags: ["tutorial", "steps", "educational"]
    },
    
    // Storytelling (30-60s)
    {
        id: "customer-journey",
        name: "Customer Journey",
        category: "Storytelling",
        icon: Rocket,
        prompt: "Customer journey: Problem → Discovery → Solution using {product}, relatable and emotional narrative",
        duration: "45-60s",
        tags: ["story", "journey", "emotional"]
    },
    {
        id: "brand-story",
        name: "Brand Story",
        category: "Storytelling",
        icon: Star,
        prompt: "Brand story: Founder's passion, craftsmanship, and values in 60 seconds, inspiring and authentic",
        duration: "50-60s",
        tags: ["brand", "founder", "values"]
    },
    {
        id: "unboxing",
        name: "Unboxing Experience",
        category: "Storytelling",
        icon: Package,
        prompt: "Unboxing experience: First impressions and reactions to {product}, genuine excitement and discovery",
        duration: "30-45s",
        tags: ["unboxing", "reaction", "discovery"]
    },
    
    // Trending Formats
    {
        id: "pov-style",
        name: "POV First Time",
        category: "Trending",
        icon: Eye,
        prompt: "POV: You're trying {product} for the first time (reaction-style), relatable and engaging perspective",
        duration: "15-20s",
        tags: ["pov", "reaction", "trending"]
    },
    {
        id: "voiceover-tour",
        name: "Voiceover Tour",
        category: "Trending",
        icon: Mic,
        prompt: "Voiceover tour: Walk through {location} showcasing menu/products, informative and inviting",
        duration: "30-40s",
        tags: ["tour", "voiceover", "showcase"]
    },
    {
        id: "comparison",
        name: "Product Comparison",
        category: "Trending",
        icon: Scale,
        prompt: "Comparison: Our {item} vs. competitors (side-by-side), clear advantages and honest presentation",
        duration: "20-30s",
        tags: ["comparison", "vs", "honest"]
    },
    {
        id: "myth-busting",
        name: "Myth Busting",
        category: "Trending",
        icon: Search,
        prompt: "Myth-busting: 3 common misconceptions about {product category}, educational and surprising",
        duration: "25-35s",
        tags: ["myths", "facts", "educational"]
    },
    
    // Engagement Hooks
    {
        id: "wait-for-it",
        name: "Wait For It...",
        category: "Engagement",
        icon: Timer,
        prompt: "Wait for it... {surprising reveal or twist ending}, suspenseful build-up with satisfying payoff",
        duration: "10-15s",
        tags: ["suspense", "reveal", "hook"]
    },
    {
        id: "guess-ingredient",
        name: "Guess the Secret",
        category: "Engagement",
        icon: HelpCircle,
        prompt: "Guess the secret ingredient in our {dish} - comment below! Interactive and curiosity-driven",
        duration: "15-20s",
        tags: ["interactive", "guess", "engagement"]
    },
    {
        id: "choose-option",
        name: "Which Would You Choose?",
        category: "Engagement",
        icon: Target,
        prompt: "Which would you choose? A or B? Show two options side-by-side, encouraging comments and interaction",
        duration: "10-15s",
        tags: ["choice", "poll", "interactive"]
    }
];

interface VideoTemplatePickerProps {
    onSelectTemplate: (prompt: string) => void;
}

export function VideoTemplatePicker({ onSelectTemplate }: VideoTemplatePickerProps) {
    const [open, setOpen] = useState(false);
    const [selectedCategory, setSelectedCategory] = useState<string>("all");

    const categories = ["all", ...Array.from(new Set(VIDEO_TEMPLATES.map(t => t.category)))];
    
    const filteredTemplates = selectedCategory === "all" 
        ? VIDEO_TEMPLATES 
        : VIDEO_TEMPLATES.filter(t => t.category === selectedCategory);

    const handleSelect = (template: VideoTemplate) => {
        onSelectTemplate(template.prompt);
        setOpen(false);
    };

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button 
                    variant="outline" 
                    size="sm"
                    className="gap-2"
                >
                    <ThemeEmoji name="sparkles" className="w-4 h-4" />
                    Use Template
                </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden flex flex-col bg-card border-border shadow-[0_0_40px_rgba(0,245,212,0.12)]">
                <DialogHeader>
                    <DialogTitle className="font-heading text-2xl flex items-center gap-2">
                        <ThemeEmoji name="video" className="w-6 h-6" />
                        Video & Reel Templates
                    </DialogTitle>
                    <DialogDescription className="font-mono text-xs uppercase tracking-wider">
                        Choose a template to generate engaging videos
                    </DialogDescription>
                </DialogHeader>

                {/* Category Filter */}
                <div className="flex gap-2 flex-wrap pb-4 border-b border-border">
                    {categories.map((category) => (
                        <button
                            key={category}
                            onClick={() => setSelectedCategory(category)}
                            className={cn(
                                "px-3 py-1 rounded-full text-xs font-mono uppercase tracking-wider transition-all",
                                selectedCategory === category
                                    ? "bg-primary text-black"
                                    : "bg-card border border-border hover:border-primary/50 text-muted-foreground"
                            )}
                        >
                            {category}
                        </button>
                    ))}
                </div>

                {/* Templates Grid */}
                <div className="overflow-y-auto flex-1 pr-2">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {filteredTemplates.map((template) => {
                            const TemplateIcon = template.icon;
                            return (
                            <button
                                key={template.id}
                                onClick={() => handleSelect(template)}
                                className="text-left p-4 rounded-lg border border-border hover:border-primary/50 hover:bg-primary/5 transition-all group"
                            >
                                <div className="flex items-start justify-between mb-2">
                                    <div className="flex items-center gap-2">
                                        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary/10 shrink-0">
                                            <TemplateIcon className="w-4 h-4 text-primary" />
                                        </div>
                                        <h3 className="font-semibold text-sm group-hover:text-primary transition-colors">
                                            {template.name}
                                        </h3>
                                    </div>
                                    <div className="flex flex-col items-end gap-1">
                                        <span className="text-[10px] font-mono text-muted-foreground uppercase px-2 py-0.5 bg-background rounded">
                                            {template.category}
                                        </span>
                                        <span className="text-[9px] font-mono text-primary px-2 py-0.5 bg-primary/10 rounded">
                                            {template.duration}
                                        </span>
                                    </div>
                                </div>
                                <p className="text-xs text-muted-foreground mb-3 line-clamp-2">
                                    {template.prompt}
                                </p>
                                <div className="flex gap-1 flex-wrap">
                                    {template.tags.map((tag) => (
                                        <span
                                            key={tag}
                                            className="text-[9px] font-mono px-2 py-0.5 rounded-full bg-primary/10 text-primary"
                                        >
                                            {tag}
                                        </span>
                                    ))}
                                </div>
                            </button>
                            );
                        })}
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}
