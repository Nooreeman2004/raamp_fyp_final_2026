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
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            className={cn(
                "relative rounded-2xl overflow-hidden border border-border/50 bg-card/30 backdrop-blur-xl shadow-xl transition-all duration-300 will-change-transform",
                enableHover &&
                    "hover:-translate-y-0.5 hover:border-primary/30 hover:ring-1 hover:ring-primary/20 hover:shadow-[0_0_28px_rgba(0,224,208,0.12)]",
                className
            )}
            {...props}
        >
            <div className={cn("relative z-10 p-6", contentClassName)}>
                {children}
            </div>
        </motion.div>
    );
}
