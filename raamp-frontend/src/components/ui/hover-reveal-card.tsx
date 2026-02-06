import { useRef, useState, useEffect } from "react";
import { motion, useSpring, useMotionValue, useTransform } from "framer-motion";
import { cn } from "@/lib/utils";

interface HoverRevealCardProps {
    title: string;
    description: string;
    icon: React.ElementType;
    index: number;
    className?: string;
}

export const HoverRevealCard = ({ title, description, icon: Icon, index, className }: HoverRevealCardProps) => {
    const ref = useRef<HTMLDivElement>(null);
    const [isHovered, setIsHovered] = useState(false);

    const x = useMotionValue(0);
    const y = useMotionValue(0);

    const mouseX = useSpring(x, { stiffness: 500, damping: 100 });
    const mouseY = useSpring(y, { stiffness: 500, damping: 100 });

    const rotateX = useTransform(mouseY, [-0.5, 0.5], ["17.5deg", "-17.5deg"]);
    const rotateY = useTransform(mouseX, [-0.5, 0.5], ["-17.5deg", "17.5deg"]);

    const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
        if (!ref.current) return;

        const rect = ref.current.getBoundingClientRect();

        const width = rect.width;
        const height = rect.height;

        const mouseXFromCenter = e.clientX - rect.left - width / 2;
        const mouseYFromCenter = e.clientY - rect.top - height / 2;

        x.set(mouseXFromCenter / width);
        y.set(mouseYFromCenter / height);
    };

    const handleMouseLeave = () => {
        setIsHovered(false);
        x.set(0);
        y.set(0);
    };

    const handleMouseEnter = () => {
        setIsHovered(true);
    };

    return (
        <motion.div
            ref={ref}
            className={cn(
                "relative h-full w-full rounded-xl bg-card/40 border border-white/10 backdrop-blur-sm overflow-hidden transition-colors duration-500",
                isHovered ? "border-primary/50 bg-card/60" : "",
                className
            )}
            style={{
                transformStyle: "preserve-3d",
                rotateX,
                rotateY,
            }}
            onMouseMove={handleMouseMove}
            onMouseLeave={handleMouseLeave}
            onMouseEnter={handleMouseEnter}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: index * 0.1 }}
        >
            {/* Spotlight Gradient */}
            <div
                className="absolute inset-0 z-0 transition-opacity duration-500"
                style={{
                    background: "radial-gradient(circle at center, var(--primary) 0%, transparent 70%)",
                    opacity: isHovered ? 0.15 : 0,
                    transform: `translate(${x.get() * 100}px, ${y.get() * 100}px)`,
                }}
            />

            <div className="relative z-10 p-6 h-full flex flex-col" style={{ transform: "translateZ(50px)" }}>
                <div className="mb-4 w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary group-hover:scale-110 transition-transform duration-300">
                    <Icon className="w-6 h-6" />
                </div>

                <h3 className="text-xl font-bold mb-2 font-bebas tracking-wide text-white group-hover:text-primary transition-colors">
                    {title}
                </h3>

                <p className="text-sm text-muted-foreground font-mono leading-relaxed">
                    {description}
                </p>

                {/* Reveal Line */}
                <div className={cn(
                    "absolute bottom-0 left-0 h-1 bg-primary transition-all duration-500 ease-out",
                    isHovered ? "w-full" : "w-0"
                )} />
            </div>
        </motion.div>
    );
};
