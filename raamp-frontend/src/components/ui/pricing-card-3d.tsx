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
                "relative h-full w-full rounded-2xl bg-card/80 border backdrop-blur-md transition-all duration-500 cursor-pointer",
                isHovered ? "border-primary shadow-xl" : "border-border/50 shadow-xl",
                isPopular ? "ring-2 ring-primary/30" : "",
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
            initial={{ opacity: 0, scale: 0.9, y: 50 }}
            whileInView={{ opacity: 1, scale: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ 
                type: "spring",
                stiffness: 100,
                damping: 20
            }}
            whileHover={{ scale: 1.02 }}
        >
            {/* Spotlight Gradient */}
            <div
                className="absolute inset-0 z-0 transition-opacity duration-500"
                style={{
                    background: "radial-gradient(circle at center, var(--primary) 0%, transparent 60%)",
                    opacity: isHovered ? 0.15 : 0,
                    transform: `translate(${x.get() * 150}px, ${y.get() * 150}px)`,
                }}
            />

            {/* Animated border gradient */}
            <motion.div
                className="absolute inset-0 rounded-2xl opacity-0 transition-opacity duration-500"
                style={{
                    background: "linear-gradient(45deg, transparent, var(--primary), transparent)",
                    backgroundSize: "200% 200%",
                    opacity: isHovered ? 0.3 : 0,
                }}
                animate={isHovered ? {
                    backgroundPosition: ['0% 50%', '100% 50%', '0% 50%'],
                } : {}}
                transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
            />

            {/* Floating particles effect */}
            {isHovered && (
                <>
                    {[...Array(8)].map((_, i) => (
                        <motion.div
                            key={i}
                            className="absolute w-1 h-1 bg-primary/60 rounded-full"
                            initial={{ 
                                x: Math.random() * 100 + '%',
                                y: '100%',
                                opacity: 0
                            }}
                            animate={{
                                y: '-20%',
                                opacity: [0, 1, 0],
                            }}
                            transition={{
                                duration: 2 + Math.random() * 2,
                                repeat: Infinity,
                                delay: i * 0.2,
                                ease: "easeOut"
                            }}
                        />
                    ))}
                </>
            )}

            {/* Badge — positioned outside card overflow so it's never clipped */}
            {isPopular && (
                <motion.div 
                    className="absolute -top-3.5 left-1/2 -translate-x-1/2 z-20"
                    animate={{
                        y: [0, -3, 0],
                    }}
                    transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                >
                    <span className="bg-primary text-primary-foreground text-xs font-bold uppercase tracking-wider py-1.5 px-4 rounded-full whitespace-nowrap">
                        ⭐ Most Popular
                    </span>
                </motion.div>
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

                <h3 className="text-3xl font-bold mb-2 text-foreground">
                    {title}
                </h3>

                {price && (
                    <div className="mb-6 flex items-baseline">
                        <span className="text-6xl font-black tracking-tight text-primary">
                            {price}
                        </span>
                        <span className="ml-2 text-xl font-medium text-muted-foreground">/mo</span>
                    </div>
                )}

                <div className="space-y-4 flex-grow mb-8">
                    {features.map((feature, i) => (
                        <motion.div 
                            key={i} 
                            className="flex items-start gap-3"
                            initial={{ opacity: 0, x: -20 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            viewport={{ once: true }}
                            transition={{ delay: i * 0.1 }}
                        >
                            <motion.div 
                                className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0 mt-0.5 border border-primary/30"
                                whileHover={{ scale: 1.2, rotate: 360 }}
                                transition={{ type: "spring", stiffness: 400 }}
                            >
                                <Check className="w-4 h-4 text-primary" />
                            </motion.div>
                            <p className="text-foreground/80 text-sm leading-relaxed hover:text-foreground transition-colors">{feature}</p>
                        </motion.div>
                    ))}
                </div>

                {/* Action Button — only rendered when buttonText is provided */}
                {buttonText && (
                    <motion.div 
                        className={cn(
                            "mt-auto flex items-center justify-center border-2 py-3.5 rounded-lg text-sm font-bold tracking-wider uppercase transition-all duration-300",
                            isCurrentPlan
                                ? "border-primary bg-primary/20 text-primary cursor-default"
                                : cn("border-primary bg-primary/10 text-primary", isHovered ? "bg-primary text-black" : "")
                        )}
                        whileHover={!isCurrentPlan ? { scale: 1.05 } : {}}
                        whileTap={!isCurrentPlan ? { scale: 0.95 } : {}}
                    >
                        {buttonText}
                    </motion.div>
                )}
            </div>
        </motion.div>
    );
};
