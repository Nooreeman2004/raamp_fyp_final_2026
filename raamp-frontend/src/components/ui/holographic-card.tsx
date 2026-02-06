import { cn } from "@/lib/utils";
import { HTMLMotionProps, motion } from "framer-motion";

interface HolographicCardProps extends HTMLMotionProps<"div"> {
    children: React.ReactNode;
    className?: string;
    contentClassName?: string;
    enableHover?: boolean;
}

export function HolographicCard({ children, className, contentClassName, enableHover = true, ...props }: HolographicCardProps) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            className={cn(
                "relative overflow-hidden rounded-xl bg-card/40 border border-white/10",
                "backdrop-blur-xl backdrop-saturate-150", // Stronger blur and saturation for "Refractive" look
                "shadow-[0_8px_32px_0_rgba(0,0,0,0.36)]", // Deep glass shadow
                enableHover && "hover:border-primary/30 hover:shadow-[0_0_30px_rgba(0,224,208,0.1)] transition-all duration-500 group",
                className
            )}
            {...props}
        >
            {/* Chromatic Aberration / Prismatic Edge Effect */}
            <div className="absolute -inset-[1px] bg-gradient-to-r from-transparent via-white/10 to-transparent opacity-0 group-hover:opacity-100 blur-sm transition-opacity duration-500 pointer-events-none" />

            {/* Subtle Gradient Overlay */}
            <div className="absolute inset-0 bg-gradient-to-br from-white/5 via-transparent to-black/20 pointer-events-none" />

            {/* Content */}
            <div className={cn("relative z-10", contentClassName)}>
                {children}
            </div>
        </motion.div>
    );
}
