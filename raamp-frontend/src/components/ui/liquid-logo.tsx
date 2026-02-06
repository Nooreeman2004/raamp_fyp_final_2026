import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface LiquidLogoProps {
    className?: string;
    src: string;
    logoClassName?: string;
}

export const LiquidLogo = ({ className, src, logoClassName }: LiquidLogoProps) => {
    return (
        <div className={cn("relative rounded-full overflow-hidden bg-black/40 border border-primary/20 backdrop-blur-sm group", className)}>

            {/* Liquid Wave Animation Background */}
            <div className="absolute inset-0 z-0 opacity-50 group-hover:opacity-80 transition-opacity duration-500">
                <motion.div
                    className="absolute bottom-0 left-0 right-0 bg-primary/30 w-[200%] h-[200%] -translate-x-1/2"
                    style={{ borderRadius: "40%" }}
                    animate={{
                        y: ["100%", "10%"],
                        rotate: [0, 360]
                    }}
                    transition={{
                        y: { duration: 8, ease: "easeInOut", repeat: Infinity, repeatType: "reverse" },
                        rotate: { duration: 10, repeat: Infinity, ease: "linear" }
                    }}
                />
                <motion.div
                    className="absolute bottom-0 left-0 right-0 bg-primary/20 w-[200%] h-[200%] -translate-x-1/2"
                    style={{ borderRadius: "45%" }}
                    animate={{
                        y: ["100%", "20%"],
                        rotate: [0, -360]
                    }}
                    transition={{
                        y: { duration: 12, ease: "easeInOut", repeat: Infinity, repeatType: "reverse", delay: 1 },
                        rotate: { duration: 15, repeat: Infinity, ease: "linear" }
                    }}
                />
            </div>

            {/* Logo Centered */}
            <div className="absolute inset-0 z-10 flex items-center justify-center p-6">
                <img
                    src={src}
                    alt="RAAMP Logo"
                    className={cn("w-full h-full object-contain drop-shadow-[0_0_15px_rgba(0,224,208,0.5)]", logoClassName)}
                />
            </div>

            {/* Glass Shine/Reflection */}
            <div className="absolute inset-0 z-20 bg-gradient-to-br from-white/10 via-transparent to-transparent rounded-full pointer-events-none" />

            {/* Active Ring */}
            <div className="absolute inset-0 border-2 border-primary/10 rounded-full z-30 group-hover:border-primary/30 transition-colors duration-500" />
        </div>
    );
};
