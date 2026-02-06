import { useRef } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import { cn } from "@/lib/utils";

const StickyScrollReveal = ({
    content,
    contentClassName,
}: {
    content: {
        title: string;
        description: string;
        content?: React.ReactNode | any;
    }[];
    contentClassName?: string;
}) => {
    const targetRef = useRef(null);
    const { scrollYProgress } = useScroll({
        target: targetRef,
        offset: ["start start", "end end"],
    });

    const backgroundColors = [
        "var(--slate-900)",
        "var(--black)",
        "var(--neutral-900)",
    ];
    const linearGradients = [
        "linear-gradient(to bottom right, var(--cyan-500), var(--emerald-500))",
        "linear-gradient(to bottom right, var(--pink-500), var(--indigo-500))",
        "linear-gradient(to bottom right, var(--orange-500), var(--yellow-500))",
    ];

    return (
        <div ref={targetRef} className="relative h-[300vh] bg-background">
            <div className="sticky top-0 h-screen flex items-center overflow-hidden">
                <div className="container mx-auto px-4 grid grid-cols-1 lg:grid-cols-2 gap-10 relative">

                    {/* Text Content */}
                    <div className="relative z-10">
                        {content.map((item, index) => {
                            // Calculate opacity based on scroll position for each item
                            const start = index / content.length;
                            const end = (index + 1) / content.length;
                            const opacity = useTransform(scrollYProgress, [start, start + 0.1, end - 0.1, end], [0, 1, 1, 0]);
                            const y = useTransform(scrollYProgress, [start, end], [50, -50]);

                            // We only want one item visible at a time, so we absolutely position them
                            // But to keep layout flow, we might need a different approach.
                            // For "Sticky" feel, usually the text scrolls and the image stays, or vice versa.
                            // Let's try: Text stays sticky, Image changes.

                            return (
                                <motion.div
                                    key={item.title + index}
                                    style={{ opacity }}
                                    className="absolute top-0 left-0 w-full h-full flex flex-col justify-center pointer-events-none"
                                >
                                    <h2 className="text-4xl md:text-6xl font-bold text-white mb-6 font-bebas tracking-wide">
                                        {item.title}
                                    </h2>
                                    <p className="text-lg text-muted-foreground max-w-md font-mono">
                                        {item.description}
                                    </p>
                                </motion.div>
                            );
                        })}
                        {/* Spacer to give height to the text container */}
                        <div className="h-[50vh]" />
                    </div>

                    {/* Visual Content (Cards/Images) */}
                    <div
                        className={cn(
                            "hidden lg:block h-[60vh] w-full rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md overflow-hidden sticky top-[20vh]",
                            contentClassName
                        )}
                    >
                        {content.map((item, index) => {
                            const start = index / content.length;
                            const end = (index + 1) / content.length;
                            const opacity = useTransform(scrollYProgress, [start, start + 0.05, end - 0.05, end], [0, 1, 1, 0]);
                            const scale = useTransform(scrollYProgress, [start, start + 0.1], [0.8, 1]);

                            return (
                                <motion.div
                                    key={index}
                                    style={{ opacity, scale }}
                                    className="absolute inset-0 flex items-center justify-center p-10"
                                >
                                    {item.content}
                                </motion.div>
                            )
                        })}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default StickyScrollReveal;
