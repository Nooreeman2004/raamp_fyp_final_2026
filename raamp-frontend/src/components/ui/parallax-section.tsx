import { useRef } from "react";
import { motion, useScroll, useTransform, useSpring } from "framer-motion";
import { cn } from "@/lib/utils";

interface ParallaxSectionProps {
    children: React.ReactNode;
    className?: string;
    speed?: number; // Negative for reverse direction
    direction?: "vertical" | "horizontal";
}

export const ParallaxSection = ({
    children,
    className,
    speed = 0.5,
    direction = "vertical",
}: ParallaxSectionProps) => {
    const ref = useRef<HTMLDivElement>(null);
    const { scrollYProgress } = useScroll({
        target: ref,
        offset: ["start end", "end start"],
    });

    const springConfig = { stiffness: 100, damping: 30, restDelta: 0.001 };
    const smoothProgress = useSpring(scrollYProgress, springConfig);

    const y = useTransform(smoothProgress, [0, 1], ["0%", `${speed * 100}%`]);
    const x = useTransform(smoothProgress, [0, 1], ["0%", `${speed * 100}%`]);

    return (
        <div ref={ref} className={cn("relative overflow-hidden", className)}>
            <motion.div
                style={{
                    y: direction === "vertical" ? y : 0,
                    x: direction === "horizontal" ? x : 0,
                }}
                className="w-full h-full"
            >
                {children}
            </motion.div>
        </div>
    );
};
