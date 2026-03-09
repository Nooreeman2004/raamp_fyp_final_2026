import { useRef, useState } from "react";
import { motion, useSpring, useMotionValue, useTransform } from "framer-motion";
import { cn } from "@/lib/utils";
import { Check } from "lucide-react";

interface PricingCard3DProps {
    title: string;
    price?: string;
    features: string[];
    buttonText?: string | undefined;
    isPopular?: boolean;
    isCurrentPlan?: boolean;
    className?: string;
    onClick?: () => void;
}

export const PricingCard3D = ({ title, price, features, buttonText, isPopular, isCurrentPlan, className, onClick }: PricingCard3DProps) => {
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
                "relative h-full w-full rounded-xl bg-card/40 border border-white/10 backdrop-blur-sm transition-all duration-500 cursor-pointer",
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

            {/* Badge — positioned outside card overflow so it's never clipped */}
            {isPopular && (
                <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 z-20">
                    <span className="bg-primary text-primary-foreground text-xs font-bold uppercase tracking-wider py-1.5 px-4 rounded-full shadow-lg whitespace-nowrap">
                        Most Popular
                    </span>
                </div>
            )}

            {/* Your Plan badge — top-right corner */}
            {isCurrentPlan && (
                <div className="absolute top-3 right-3 z-20">
                    <span className="bg-primary/20 border border-primary/50 text-primary text-[10px] font-bold uppercase tracking-wider py-1 px-2.5 rounded-full whitespace-nowrap">
                        ✓ Your Plan
                    </span>
                </div>
            )}

            <div className="relative z-10 p-8 h-full flex flex-col" style={{ transform: "translateZ(30px)" }}>

                <h3 className="text-3xl font-bold mb-2 font-bebas tracking-wide text-white group-hover:text-primary transition-colors">
                    {title}
                </h3>

                {price && (
                    <div className="mb-6 flex items-baseline text-white">
                        <span className="text-5xl font-extrabold tracking-tight">{price}</span>
                        <span className="ml-1 text-xl font-medium text-muted-foreground">/mo</span>
                    </div>
                )}

                <div className="space-y-4 flex-grow mb-8">
                    {features.map((feature, i) => (
                        <div key={i} className="flex items-start gap-3">
                            <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                                <Check className="w-4 h-4 text-primary" />
                            </div>
                            <p className="text-muted-foreground font-mono text-sm">{feature}</p>
                        </div>
                    ))}
                </div>

                {/* Action Button — only rendered when buttonText is provided */}
                {buttonText && (
                    <div className={cn(
                        "mt-auto flex items-center justify-center border py-3 rounded text-sm font-bold tracking-wider uppercase transition-all duration-300",
                        isCurrentPlan
                            ? "border-primary bg-primary/20 text-primary cursor-default"
                            : cn("border-primary/50 text-white", isHovered ? "bg-primary" : "bg-transparent")
                    )}>
                        {buttonText}
                    </div>
                )}
            </div>
        </motion.div>
    );
};
