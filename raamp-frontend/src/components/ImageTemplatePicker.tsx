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
import { Camera, Utensils, Coffee, LayoutGrid, Zap, Layers, Sparkles, Users, PartyPopper, Sun, Leaf, Star, Smartphone } from "lucide-react";

interface ImageTemplate {
    id: string;
    name: string;
    category: string;
    prompt: string;
    tags: string[];
    icon: LucideIcon;
}

const IMAGE_TEMPLATES: ImageTemplate[] = [
    // Product/Food Photography
    {
        id: "flatlay",
        name: "Flat-lay Product Shot",
        category: "Product Photography",
        icon: Camera,
        prompt: "Flat-lay of {product} on marble surface with natural lighting and minimal props, professional food photography style",
        tags: ["product", "minimal", "professional"]
    },
    {
        id: "hero-food",
        name: "Hero Food Shot",
        category: "Product Photography",
        icon: Utensils,
        prompt: "Close-up hero shot of {dish} with steam rising, garnished beautifully on dark plate, dramatic lighting, restaurant quality",
        tags: ["food", "dramatic", "closeup"]
    },
    {
        id: "lifestyle",
        name: "Lifestyle Product",
        category: "Product Photography",
        icon: Coffee,
        prompt: "Lifestyle shot: hands holding {product} in cozy café setting with warm lighting, authentic and inviting atmosphere",
        tags: ["lifestyle", "authentic", "warm"]
    },
    {
        id: "overhead-grid",
        name: "Overhead Grid",
        category: "Product Photography",
        icon: LayoutGrid,
        prompt: "Overhead view of {items} arranged in a grid pattern on white background, clean and organized, e-commerce style",
        tags: ["overhead", "clean", "grid"]
    },
    
    // Promotional/Marketing
    {
        id: "bold-text",
        name: "Bold Promo Text",
        category: "Promotional",
        icon: Zap,
        prompt: "Bold text overlay '{offer}' on vibrant gradient background with geometric shapes, modern and eye-catching design",
        tags: ["promo", "bold", "modern"]
    },
    {
        id: "before-after",
        name: "Before/After Split",
        category: "Promotional",
        icon: Layers,
        prompt: "Before/after split screen showing {transformation}, clear comparison with arrows, professional presentation",
        tags: ["comparison", "transformation", "split"]
    },
    {
        id: "minimal-showcase",
        name: "Minimal Product Showcase",
        category: "Promotional",
        icon: Sparkles,
        prompt: "Minimalist product showcase: {item} centered on solid {color} background with soft shadow, clean and elegant",
        tags: ["minimal", "elegant", "centered"]
    },
    {
        id: "customer-collage",
        name: "Customer Collage",
        category: "Promotional",
        icon: Users,
        prompt: "Collage of 3-4 customer photos using {product} in real settings, authentic and diverse, social proof style",
        tags: ["collage", "social-proof", "authentic"]
    },
    
    // Seasonal/Event
    {
        id: "festive",
        name: "Festive Holiday",
        category: "Seasonal",
        icon: PartyPopper,
        prompt: "Festive {holiday} themed setup with {product} as centerpiece, warm bokeh lights, cozy and celebratory atmosphere",
        tags: ["holiday", "festive", "cozy"]
    },
    {
        id: "summer-vibes",
        name: "Summer Vibes",
        category: "Seasonal",
        icon: Sun,
        prompt: "Summer vibes: {product} on beach towel with sunglasses and tropical fruits, bright and cheerful, vacation aesthetic",
        tags: ["summer", "beach", "bright"]
    },
    {
        id: "autumn-cozy",
        name: "Autumn Cozy",
        category: "Seasonal",
        icon: Leaf,
        prompt: "Cozy autumn aesthetic: {item} with pumpkins, leaves, and warm coffee, rustic and inviting atmosphere",
        tags: ["autumn", "cozy", "rustic"]
    },
    
    // Social Proof
    {
        id: "testimonial",
        name: "Testimonial Card",
        category: "Social Proof",
        icon: Star,
        prompt: "Customer testimonial card: 5-star rating with quote overlay on brand colors, professional and trustworthy design",
        tags: ["testimonial", "rating", "trust"]
    },
    {
        id: "ugc-style",
        name: "User Content Style",
        category: "Social Proof",
        icon: Smartphone,
        prompt: "User-generated content style: authentic photo of happy customer with {product}, candid and relatable",
        tags: ["ugc", "authentic", "candid"]
    }
];

interface ImageTemplatePickerProps {
    onSelectTemplate: (prompt: string) => void;
}

export function ImageTemplatePicker({ onSelectTemplate }: ImageTemplatePickerProps) {
    const [open, setOpen] = useState(false);
    const [selectedCategory, setSelectedCategory] = useState<string>("all");

    const categories = ["all", ...Array.from(new Set(IMAGE_TEMPLATES.map(t => t.category)))];
    
    const filteredTemplates = selectedCategory === "all" 
        ? IMAGE_TEMPLATES 
        : IMAGE_TEMPLATES.filter(t => t.category === selectedCategory);

    const handleSelect = (template: ImageTemplate) => {
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
                        <ThemeEmoji name="image" className="w-6 h-6" />
                        Image Templates
                    </DialogTitle>
                    <DialogDescription className="font-mono text-xs uppercase tracking-wider">
                        Choose a template to generate professional images
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
                                    <span className="text-[10px] font-mono text-muted-foreground uppercase px-2 py-0.5 bg-background rounded">
                                        {template.category}
                                    </span>
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
