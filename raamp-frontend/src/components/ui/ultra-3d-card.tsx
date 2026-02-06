import React, { useRef, useState, useEffect } from "react";
import { motion, useMotionTemplate, useMotionValue, useSpring, useTransform } from "framer-motion";
import { cn } from "@/lib/utils";

interface Ultra3DCardProps {
    children: React.ReactNode;
    className?: string;
    title?: string;
    description?: string;
    icon?: React.ElementType;
    disableHoverEffects?: boolean;
}

export const Ultra3DCard = ({ children, className, title, description, icon: Icon, disableHoverEffects = false }: Ultra3DCardProps) => {
    const ref = useRef<HTMLDivElement>(null);
    const x = useMotionValue(0);
    const y = useMotionValue(0);

    // Smooth spring physics for the tilt
    const mouseX = useSpring(x, { stiffness: 500, damping: 100 });
    const mouseY = useSpring(y, { stiffness: 500, damping: 100 });

    // Correctly define motion templates at the top level
    const rotateX = useMotionTemplate`${useTransform(mouseY, (v) => v * -20)}deg`;
    const rotateY = useMotionTemplate`${useTransform(mouseX, (v) => v * 20)}deg`;

    const borderGradient = useMotionTemplate`
        radial-gradient(
            450px circle at ${useTransform(mouseX, (v) => v * 100 + 50)}% ${useTransform(mouseY, (v) => v * 100 + 50)}%,
            rgba(0, 224, 208, 0.3),
            transparent 70%
        )
    `;



    const [hovered, setHovered] = useState(false);
    const lastUpdate = useRef(0);

    function onMouseMove({ currentTarget, clientX, clientY }: React.MouseEvent) {
        if (disableHoverEffects) return; // Don't apply 3D effects if disabled
        
        const now = Date.now();
        if (now - lastUpdate.current < 16) return; // ~60fps throttling
        lastUpdate.current = now;

        const { left, top, width, height } = currentTarget.getBoundingClientRect();

        // Calculate percentage from center (-0.5 to 0.5)
        const xPct = (clientX - left) / width - 0.5;
        const yPct = (clientY - top) / height - 0.5;

        x.set(xPct);
        y.set(yPct);
    }

    function onMouseLeave() {
        setHovered(false);
        x.set(0);
        y.set(0);
    }

    return (
        <motion.div
            ref={ref}
            onMouseMove={onMouseMove}
            onMouseEnter={() => !disableHoverEffects && setHovered(true)}
            onMouseLeave={onMouseLeave}
            className={cn(
                "group relative h-full rounded-xl border border-white/10 bg-gray-900/40 transition-all duration-300 will-change-transform",
                !disableHoverEffects && "hover:border-white/20",
                className
            )}
            style={{
                transformStyle: "preserve-3d",
                rotateX: disableHoverEffects ? "0deg" : rotateX,
                rotateY: disableHoverEffects ? "0deg" : rotateY,
            }}
        >
            {/* 1. Dynamic Border Gradient (The "Neon" Edge) - Disabled if disableHoverEffects is true */}
            {!disableHoverEffects && (
                <motion.div
                    className="absolute -inset-px rounded-xl opacity-0 transition duration-300 group-hover:opacity-100"
                    style={{
                        background: borderGradient,
                    }}
                />
            )}

            {/* 2. Inner Content Container with Parallax */}
            <div
                className="relative h-full overflow-hidden rounded-xl bg-gradient-to-br from-white/5 to-white/0 p-6 backdrop-blur-md"
                style={{ transform: "translateZ(0px)" }} // Fix for Safari/Chrome rendering
            >
                {/* Grid Pattern Overlay */}
                <div className="absolute inset-0 z-0 opacity-[0.03] bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]" />

                {/* 3. Surface Flash Removed */}

                {/* Content Layer - Pushed forward in Z-space */}
                <div className="relative z-10 flex flex-col h-full" style={{ transform: "translateZ(20px)" }}>
                    {Icon && (
                        <div
                            className={cn(
                                "mb-4 w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary shadow-[0_0_15px_rgba(0,224,208,0.2)] transition-transform duration-500",
                                !disableHoverEffects && "group-hover:scale-110"
                            )}
                            style={{ transform: "translateZ(30px)" }}
                        >
                            <Icon className="w-6 h-6" />
                        </div>
                    )}

                    {title && (
                        <h3
                            className={cn(
                                "text-xl font-bold mb-2 font-bebas tracking-wide text-white transition-colors duration-300",
                                !disableHoverEffects && "group-hover:text-primary"
                            )}
                            style={{ transform: "translateZ(25px)" }}
                        >
                            {title}
                        </h3>
                    )}

                    {description && (
                        <p
                            className="text-sm text-muted-foreground font-mono leading-relaxed"
                            style={{ transform: "translateZ(20px)" }}
                        >
                            {description}
                        </p>
                    )}

                    {children}
                </div>
            </div>
        </motion.div>
    );
};
