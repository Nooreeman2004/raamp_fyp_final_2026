import { useRef, useState } from "react";
import { motion, useSpring, useMotionValue, useTransform } from "framer-motion";
import { cn } from "@/lib/utils";
import { Check } from "lucide-react";

interface PricingCard3DProps {
    title: string;
    features: string[];
    className?: string;
    onClick?: () => void;
}

export const PricingCard3D = ({ title, features, className, onClick }: PricingCard3DProps) => {
    const ref = useRef<HTMLDivElement>(null);
    const [isHovered, setIsHovered] = useState(false);

    const x = useMotionValue(0);
    const y = useMotionValue(0);

    const mouseX = useSpring(x, { stiffness: 500, damping: 100 });
    const mouseY = useSpring(y, { stiffness: 500, damping: 100 });

    const rotateX = useTransform(mouseY, [-0.5, 0.5], ["10deg", "-10deg"]);
    const rotateY = useTransform(mouseX, [-0.5, 0.5], ["-10deg", "10deg"]);

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
                "relative h-full w-full rounded-xl bg-card/40 border border-white/10 backdrop-blur-sm overflow-hidden transition-all duration-500 cursor-pointer",
                isHovered ? "border-primary/50 bg-card/60 shadow-[0_0_50px_rgba(0,224,208,0.15)]" : "",
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
            onClick={onClick}
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
        >
            {/* Spotlight Gradient */}
            <div
                className="absolute inset-0 z-0 transition-opacity duration-500"
                style={{
                    background: "radial-gradient(circle at center, var(--primary) 0%, transparent 60%)",
                    opacity: isHovered ? 0.1 : 0,
                    transform: `translate(${x.get() * 150}px, ${y.get() * 150}px)`,
                }}
            />

            <div className="relative z-10 p-8 h-full flex flex-col" style={{ transform: "translateZ(30px)" }}>
                <h3 className="text-3xl font-bold mb-8 font-bebas tracking-wide text-white group-hover:text-primary transition-colors">
                    {title}
                </h3>

                <div className="space-y-4 flex-grow">
                    {features.map((feature, i) => (
                        <div key={i} className="flex items-start gap-3">
                            <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                                <Check className="w-4 h-4 text-primary" />
                            </div>
                            <p className="text-muted-foreground font-mono text-sm">{feature}</p>
                        </div>
                    ))}
                </div>

                {/* Action Hint */}
                <div className={cn(
                    "mt-8 flex items-center justify-center text-primary text-sm font-bold tracking-wider uppercase transition-opacity duration-300",
                    isHovered ? "opacity-100" : "opacity-0"
                )}>
                    Select Plan
                </div>
            </div>
        </motion.div>
    );
};
