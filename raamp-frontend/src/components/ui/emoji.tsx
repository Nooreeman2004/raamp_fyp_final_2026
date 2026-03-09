import React from "react";
import {
    Sprout,
    Rocket,
    TrendingUp,
    AlertCircle,
    TrendingDown,
    Sparkles,
    Folder,
    Camera,
    Video,
    Image as ImageIcon,
    Layout,
    BookOpen,
    Globe,
    AlertTriangle,
    Check,
    X,
    Info,
    Lightbulb,
    Megaphone,
    MessageCircle,
    Mail,
    Pencil,
    Tag,
    Square,
    Ruler,
    LucideProps
} from "lucide-react";

export const themeIcons = {
    emerging: Sprout,
    breakout: Rocket,
    mainstream: TrendingUp,
    saturated: AlertCircle,
    declining: TrendingDown,
    sparkles: Sparkles,
    folder: Folder,
    camera: Camera,
    video: Video,
    image: ImageIcon,
    post: Layout,
    story: BookOpen,
    globe: Globe,
    warning: AlertTriangle,
    check: Check,
    cross: X,
    info: Info,
    lightbulb: Lightbulb,
    ad_copy: Megaphone,
    whatsapp: MessageCircle,
    email: Mail,
    pencil: Pencil,
    tag: Tag,
    square: Square,
    ruler: Ruler,
    frame: ImageIcon,
} as const;

export type EmojiName = keyof typeof themeIcons;

interface EmojiProps extends Omit<LucideProps, "name"> {
    name: EmojiName;
}

export const ThemeEmoji: React.FC<EmojiProps> = ({ name, className = "", ...props }) => {
    const Icon = themeIcons[name];
    if (!Icon) return null;
    return (
        <Icon className={`inline-block text-primary w-[1.2em] h-[1.2em] ${className}`} {...props} />
    );
};
