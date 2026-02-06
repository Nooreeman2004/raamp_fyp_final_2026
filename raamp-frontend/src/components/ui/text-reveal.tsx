import { motion } from "framer-motion";

interface BlurTextProps {
    text: string;
    className?: string;
    delay?: number;
    duration?: number;
}

export const BlurText = ({ text, className = "", delay = 0, duration = 0.8 }: BlurTextProps) => {
    return (
        <motion.span
            initial={{ opacity: 0, filter: "blur(10px)", y: 20 }}
            whileInView={{ opacity: 1, filter: "blur(0px)", y: 0 }}
            viewport={{ once: true }}
            transition={{ duration, delay, ease: [0.22, 1, 0.36, 1] }} // Custom cubic-bezier for Apple-like smooth ease
            className={className}
        >
            {text}
        </motion.span>
    );
};

interface StaggerTextProps {
    text: string;
    className?: string;
    delay?: number;
}

export const StaggerText = ({ text, className = "", delay = 0 }: StaggerTextProps) => {
    const words = text.split(" ");

    const container = {
        hidden: { opacity: 0 },
        visible: (i = 1) => ({
            opacity: 1,
            transition: { staggerChildren: 0.12, delayChildren: delay * i },
        }),
    };

    const child = {
        visible: {
            opacity: 1,
            y: 0,
            filter: "blur(0px)",
            transition: {
                type: "spring",
                damping: 12,
                stiffness: 100,
            },
        },
        hidden: {
            opacity: 0,
            y: 20,
            filter: "blur(10px)",
        },
    };

    return (
        <motion.div
            style={{ overflow: "hidden", display: "flex", flexWrap: "wrap" }}
            variants={container}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            className={className}
        >
            {words.map((word, index) => (
                <motion.span variants={child} style={{ marginRight: "0.25em" }} key={index}>
                    {word}
                </motion.span>
            ))}
        </motion.div>
    );
};
