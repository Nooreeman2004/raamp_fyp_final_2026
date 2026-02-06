import React from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

export const BackgroundBeams = ({ className }: { className?: string }) => {
    return (
        <div
            className={cn(
                "absolute h-full w-full inset-0 bg-neutral-950 overflow-hidden",
                className
            )}
        >
            <div className="absolute h-full w-full inset-0 bg-neutral-950 [mask-image:radial-gradient(ellipse_at_center,transparent_20%,black)]"></div>
            <div className="absolute inset-0 bg-fixed bg-center [mask-image:linear-gradient(to_bottom,transparent,black)]">
                <div className="absolute inset-0 bg-neutral-950 [mask-image:radial-gradient(ellipse_at_center,transparent_20%,black)]"></div>
            </div>
            <div className="absolute inset-0 overflow-hidden">
                <Beams />
            </div>
        </div>
    );
};

const Beams = () => {
    return (
        <div className="absolute inset-0 h-full w-full pointer-events-none">
            <svg
                className="absolute w-full h-full opacity-20"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 1000 1000"
                preserveAspectRatio="none"
            >
                <motion.path
                    d="M-200 0 L500 1000 L1200 0 Z"
                    fill="url(#grad1)"
                    initial={{ opacity: 0, pathLength: 0 }}
                    animate={{ opacity: 1, pathLength: 1 }}
                    transition={{
                        duration: 2,
                        ease: "easeInOut",
                        repeat: Infinity,
                        repeatType: "reverse",
                    }}
                />
                <motion.path
                    d="M-100 1000 L500 0 L1100 1000 Z"
                    fill="url(#grad2)"
                    initial={{ opacity: 0, pathLength: 0 }}
                    animate={{ opacity: 1, pathLength: 1 }}
                    transition={{
                        duration: 3,
                        ease: "easeInOut",
                        repeat: Infinity,
                        repeatType: "reverse",
                        delay: 1,
                    }}
                />
                <defs>
                    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" style={{ stopColor: "#00E0D0", stopOpacity: 0 }} />
                        <stop offset="50%" style={{ stopColor: "#00E0D0", stopOpacity: 0.5 }} />
                        <stop offset="100%" style={{ stopColor: "#00E0D0", stopOpacity: 0 }} />
                    </linearGradient>
                    <linearGradient id="grad2" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" style={{ stopColor: "#10b981", stopOpacity: 0 }} />
                        <stop offset="50%" style={{ stopColor: "#10b981", stopOpacity: 0.5 }} />
                        <stop offset="100%" style={{ stopColor: "#10b981", stopOpacity: 0 }} />
                    </linearGradient>
                </defs>
            </svg>
            {/* Moving Grid Lines */}
            <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_80%_50%_at_50%_0%,#000_70%,transparent_100%)]" />
        </div>
    );
};
