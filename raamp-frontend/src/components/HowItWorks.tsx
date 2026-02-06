import { useRef } from "react";
import { Search, Sparkles, TrendingUp, ArrowRight } from "lucide-react";
import { Ultra3DCard } from "@/components/ui/ultra-3d-card";
import { motion, useScroll, useTransform } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer } from "@/utils/animations";

const steps = [
    {
        icon: Search,
        title: "Detect Geo-Intent",
        description: "Leverage advanced AI to identify and analyze real-time geo-intent signals, uncovering hyper-local market opportunities you're missing",
    },
    {
        icon: Sparkles,
        title: "Generate & Test",
        description: "Automatically create, test, and optimize campaign variations with predictive analytics, ensuring maximum impact for every ad dollar",
    },
    {
        icon: TrendingUp,
        title: "Explain & Iterate",
        description: "Receive clear, actionable insights into campaign performance, continuously refining strategies for sustained growth and superior ROI",
    },
];

const HowItWorks = () => {
    const containerRef = useRef<HTMLDivElement>(null);

    // Track scroll progress relative to the container
    const { scrollYProgress } = useScroll({
        target: containerRef,
        offset: ["start center", "end center"] // Start animation when section hits center of viewport, end when it leaves
    });

    // Map scroll progress to horizontal position (from center of first card to center of last card)
    // First card center is approx 16.66%, Last card center is approx 83.33%
    const x = useTransform(scrollYProgress, [0, 1], ["16%", "84%"]);

    // Opacity fade in/out at start/end of scroll
    const opacity = useTransform(scrollYProgress, [0, 0.1, 0.9, 1], [0, 1, 1, 0]);

    return (
        <section ref={containerRef} className="py-24 relative overflow-hidden">
            <div className="container mx-auto px-4">
                {/* Header with Blur Effect */}
                <div className="text-center mb-16 flex flex-col items-center">
                    <Reveal variant="blurInUp">
                        <h2 className="text-4xl md:text-5xl font-bold mb-4 font-bebas tracking-wide flex flex-col items-center gap-2">
                            <span>How RAAMP Works:</span>
                            <span className="text-primary">The Autonomous Optimization Loop</span>
                        </h2>
                    </Reveal>
                </div>

                {/* Staggered Grid Container */}
                <div className="relative max-w-6xl mx-auto">

                    {/* SCROLL-LINKED FLOW BEAM */}
                    <div className="absolute top-1/2 left-0 w-full -translate-y-1/2 pointer-events-none z-20 hidden md:block h-24">
                        <div className="relative w-full h-full flex items-center">
                            {/* Static Track (Dashed Line) - Visible between start and end points */}
                            <div className="absolute left-[16%] right-[16%] h-px bg-gradient-to-r from-transparent via-white/10 to-transparent border-t border-dashed border-white/20" />

                            {/* Moving Arrow Projectile */}
                            <motion.div
                                className="absolute top-1/2 -translate-y-1/2 flex items-center"
                                style={{ left: x, opacity }}
                            >
                                {/* The Head (Arrow) */}
                                <div className="relative z-10 bg-black p-3 rounded-full border border-primary shadow-[0_0_30px_#00E0D0] -translate-x-1/2">
                                    <ArrowRight className="w-6 h-6 text-primary" />
                                </div>

                                {/* The Tail (Gradient Stream) - Trailing behind */}
                                <div className="absolute right-1/2 top-1/2 -translate-y-1/2 h-1 w-48 bg-gradient-to-r from-transparent to-primary blur-sm origin-right" />
                            </motion.div>
                        </div>
                    </div>

                    <motion.div
                        className="grid md:grid-cols-3 gap-8 relative z-10"
                        variants={staggerContainer}
                        initial="hidden"
                        whileInView="visible"
                        viewport={{ once: true, margin: "-100px" }}
                    >
                        {steps.map((step, index) => (
                            <div key={index} className="h-[400px] relative group">
                                {/* Card Background */}
                                <div className="absolute inset-0 bg-black/40 backdrop-blur-md rounded-xl border border-white/5 z-0" />

                                {/* The Card Content */}
                                <Ultra3DCard
                                    title={step.title}
                                    description={step.description}
                                    icon={step.icon}
                                    className="h-full relative z-10 bg-transparent border-none"
                                >
                                    <div />
                                </Ultra3DCard>
                            </div>
                        ))}
                    </motion.div>
                </div>
            </div>
        </section>
    );
};

export default HowItWorks;
