import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface MaskedTextRevealProps {
    text: string;
    className?: string;
    delay?: number;
    tag?: "h1" | "h2" | "h3" | "h4" | "p" | "span" | "div";
}

export const MaskedTextReveal = ({
    text,
    className,
    delay = 0,
    tag: Tag = "div",
}: MaskedTextRevealProps) => {
    const words = text.split(" ");

    const container = {
        hidden: { opacity: 0 },
        visible: (i = 1) => ({
            opacity: 1,
            transition: { staggerChildren: 0.1, delayChildren: delay * i },
        }),
    };

    const child = {
        visible: {
            opacity: 1,
            y: 0,
            transition: {
                type: "spring",
                damping: 20,
                stiffness: 100,
            },
        },
        hidden: {
            opacity: 0,
            y: "100%",
        },
    };

    return (
        <Tag className={cn("overflow-hidden flex flex-wrap", className)}>
            <motion.div
                variants={container}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                className="flex flex-wrap"
            >
                {words.map((word, index) => (
                    <div key={index} className="overflow-hidden inline-block mr-[0.25em] pb-1">
                        <motion.span
                            variants={child}
                            className="inline-block"
                        >
                            {word}
                        </motion.span>
                    </div>
                ))}
            </motion.div>
        </Tag>
    );
};
