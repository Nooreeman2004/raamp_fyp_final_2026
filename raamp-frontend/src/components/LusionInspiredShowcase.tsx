import { motion } from 'framer-motion';
import {
    Sparkles,
    Zap,
    Globe,
    BarChart3,
    Target,
    TrendingUp,
    Brain,
    Rocket,
    MessageSquare,
    CalendarClock,
    LibraryBig,
    CheckCircle2,
    MessageCircleReply,
    Bell,
    Shield
} from 'lucide-react';
import { Text3DScroll, SplitText3D, PerspectiveText } from '@/components/ui/text-3d';
import { MagneticImage, DepthParallaxCard, TiltCard } from '@/components/ui/magnetic-image';
import { ScrollReveal, ParallaxScroll, ScrollProgressBar, HorizontalScrollSection } from '@/components/ui/lusion-scroll';
import { HolographicCard } from '@/components/ui/holographic-card';
import raampIcon from "@/assets/raamp-logo-v5.png";
import { LiquidLogo } from "@/components/ui/liquid-logo";
import { useNavigate } from "react-router-dom";

const LusionInspiredShowcase = () => {
    const navigate = useNavigate();

    return (
        <>
            {/* Scroll Progress Indicator */}
            <ScrollProgressBar />

            {/* Hero Section with 3D Text */}
            <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-b from-background via-background/50 to-background z-0" />

                {/* Animated Grid Background */}
                <div className="absolute inset-0 opacity-10">
                    <div className="absolute inset-0 bg-[linear-gradient(to_right,#00E0D0_1px,transparent_1px),linear-gradient(to_bottom,#00E0D0_1px,transparent_1px)] bg-[size:4rem_4rem]" />
                </div>

                <div className="relative z-10 text-center px-4">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.8 }}
                        className="mb-6 flex justify-center"
                    >
                        <LiquidLogo
                            src={raampIcon}
                            className="w-32 h-32 border-none bg-transparent"
                            logoClassName="w-16 h-16"
                        />
                    </motion.div>

                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8, delay: 0.2 }}
                        className="mb-8"
                    >
                        <span className="inline-block px-6 py-3 rounded-full bg-primary/10 border border-primary/20 text-primary text-sm font-mono backdrop-blur-sm">
                            NEXT-GENERATION PLATFORM
                        </span>
                    </motion.div>

                    <SplitText3D
                        text="RAAMP"
                        className="text-7xl md:text-[12rem] font-bold mb-6"
                        delay={0.3}
                    />

                    <motion.p
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 1.5, duration: 0.8 }}
                        className="text-xl md:text-2xl text-muted-foreground max-w-3xl mx-auto mb-12"
                    >
                        Revolutionary AI-Powered Autonomous Marketing Platform
                    </motion.p>

                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 2, duration: 0.8 }}
                        className="flex flex-col sm:flex-row gap-4 justify-center"
                    >
                        <motion.button
                            type="button"
                            className="px-8 py-4 rounded-full bg-primary text-primary-foreground font-semibold text-lg shadow-[0_0_30px_rgba(0,224,208,0.4)] hover:shadow-[0_0_50px_rgba(0,224,208,0.6)] transition-all duration-300"
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={() => navigate("/signup")}
                        >
                            <span className="flex items-center gap-2">
                                <Rocket className="w-5 h-5" />
                                Start Free Trial
                            </span>
                        </motion.button>

                        <motion.button
                            type="button"
                            className="px-8 py-4 rounded-full border border-border/50 bg-foreground/5 text-foreground hover:bg-foreground/10 backdrop-blur-sm font-medium text-lg transition-all duration-300"
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={() => {
                                // More reliable than anchor jumps inside animated/scroll effects.
                                requestAnimationFrame(() => {
                                    document.getElementById("demo-features")?.scrollIntoView({ behavior: "smooth", block: "start" });
                                });
                            }}
                        >
                            Explore Features
                        </motion.button>
                    </motion.div>
                </div>

                {/* Scroll Indicator */}
                <motion.div
                    className="absolute bottom-10 left-1/2 -translate-x-1/2"
                    animate={{ y: [0, 10, 0] }}
                    transition={{ duration: 2, repeat: Infinity }}
                >
                    <div className="flex flex-col items-center gap-2 text-muted-foreground/80">
                        <span className="text-[10px] uppercase tracking-[0.2em]">Scroll</span>
                        <div className="w-[1px] h-12 bg-gradient-to-b from-primary to-transparent" />
                    </div>
                </motion.div>
            </section>

            {/* 3D Scroll Text Section */}
            <Text3DScroll text="TRANSFORM" className="bg-background" />

            {/* Features Grid with Depth Parallax */}
            <section id="demo-features" className="relative py-32 px-4 sm:px-6 lg:px-8 overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-b from-background via-primary/5 to-background" />

                <div className="max-w-7xl mx-auto relative z-10">
                    <ScrollReveal className="text-center mb-20">
                        <h2 className="text-5xl md:text-7xl font-bold text-foreground mb-6">
                            Modules
                        </h2>
                        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                            Explore the full RAAMP suite. Sign up to unlock and run these modules live.
                        </p>
                    </ScrollReveal>

                    <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
                        {[
                            {
                                icon: Brain,
                                title: "RAAMP AI Assistant",
                                desc: "Chat with an AI copilot for strategy, optimization, and next-best actions.",
                                highlight: "Ask • Plan • Optimize",
                                route: "/dashboard/assistant"
                            },
                            {
                                icon: Globe,
                                title: "Geo‑Intent Radar",
                                desc: "Find high‑intent locations and neighborhoods to target with confidence.",
                                highlight: "Where to target",
                                route: "/dashboard/geo-intent"
                            },
                            {
                                icon: Zap,
                                title: "Creative Studio",
                                desc: "Generate scroll‑stopping ad creatives and variations in minutes.",
                                highlight: "Make better ads",
                                route: "/dashboard/creative"
                            },
                            {
                                icon: TrendingUp,
                                title: "Trend Arbitrage",
                                desc: "Spot trending topics early and turn spikes into campaigns faster.",
                                highlight: "Catch trends early",
                                route: "/dashboard/trends"
                            },
                            {
                                icon: Target,
                                title: "A/B Testing Lab",
                                desc: "Run controlled tests to find winners for creatives and audiences.",
                                highlight: "Prove what works",
                                route: "/dashboard/ab-testing"
                            },
                            {
                                icon: CalendarClock,
                                title: "Smart Scheduling",
                                desc: "Auto‑schedule content for the best times to post and convert.",
                                highlight: "Post at peak times",
                                route: "/dashboard/smart-scheduling"
                            },
                            {
                                icon: LibraryBig,
                                title: "Asset Library",
                                desc: "Store, organize, and reuse your creatives, templates, and exports.",
                                highlight: "Everything in one place",
                                route: "/dashboard/assets"
                            },
                            {
                                icon: CheckCircle2,
                                title: "Campaign Approvals",
                                desc: "Review campaigns and approve launches with a clear audit trail.",
                                highlight: "Review → approve",
                                route: "/dashboard/approvals"
                            },
                            {
                                icon: MessageCircleReply,
                                title: "Auto‑Replies",
                                desc: "Automatically respond to comments and messages with rules and AI drafts.",
                                highlight: "Never miss a reply",
                                route: "/dashboard/auto-replies"
                            },
                            {
                                icon: Bell,
                                title: "Command Alerts",
                                desc: "Get important updates like approvals, issues, and performance changes.",
                                highlight: "Stay informed",
                                route: "/notifications"
                            },
                            {
                                icon: Shield,
                                title: "Account Security",
                                desc: "Protect access with security controls, password tools, and verification.",
                                highlight: "Secure your account",
                                route: "/settings/security"
                            },
                        ].map((m, index) => (
                            <ScrollReveal key={m.title} delay={0.01}>
                                <TiltCard className="h-full">
                                    <HolographicCard className="p-7 h-full">
                                        <div className="flex h-full flex-col">
                                            <div className="flex items-start justify-between gap-3">
                                                <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center text-primary">
                                                    <m.icon className="w-6 h-6" />
                                                </div>
                                                <motion.button
                                                    type="button"
                                                    onClick={() => navigate("/signup")}
                                                    className="rounded-full border border-border/60 bg-foreground/5 px-4 py-2 text-xs font-mono text-foreground hover:bg-foreground/10 transition-colors"
                                                    whileHover={{ scale: 1.03 }}
                                                    whileTap={{ scale: 0.97 }}
                                                    title={`Unlock ${m.title}`}
                                                >
                                                    Unlock
                                                </motion.button>
                                            </div>

                                            <h3 className="mt-5 text-xl font-bold text-foreground">
                                                {m.title}
                                            </h3>
                                            <p className="mt-2 text-sm text-muted-foreground flex-grow">
                                                {m.desc}
                                            </p>

                                            <div className="mt-5 flex items-center justify-between gap-3">
                                                <span className="text-[10px] font-mono uppercase tracking-widest text-primary/80">
                                                    {m.highlight}
                                                </span>
                                                <motion.button
                                                    type="button"
                                                    onClick={() => navigate("/signup")}
                                                    className="text-xs font-semibold text-primary hover:text-primary/80 transition-colors"
                                                    whileHover={{ x: 2 }}
                                                >
                                                    Start Free Trial →
                                                </motion.button>
                                            </div>
                                        </div>
                                    </HolographicCard>
                                </TiltCard>
                            </ScrollReveal>
                        ))}
                    </div>
                </div>
            </section>

            {/* Perspective Text Section */}
            <PerspectiveText text="INNOVATE" className="bg-background" />

            {/* Horizontal Scroll Section */}
            <HorizontalScrollSection className="bg-background">
                {[
                    { title: 'Strategy', color: 'from-teal-500/20' },
                    { title: 'Execute', color: 'from-purple-500/20' },
                    { title: 'Optimize', color: 'from-pink-500/20' },
                    { title: 'Scale', color: 'from-primary/20' },
                ].map((item, index) => (
                    <div
                        key={index}
                        className="min-w-[80vw] h-[80vh] rounded-3xl border border-border/50 bg-card/50 backdrop-blur-sm p-12 flex items-center justify-center"
                    >
                        <div className={`w-full h-full rounded-2xl bg-gradient-to-br ${item.color} to-transparent flex items-center justify-center`}>
                            <h3 className="text-6xl md:text-8xl font-bold text-foreground">
                                {item.title}
                            </h3>
                        </div>
                    </div>
                ))}
            </HorizontalScrollSection>

            {/* Magnetic Images Section */}
            <section className="relative py-32 px-4 sm:px-6 lg:px-8">
                <div className="max-w-7xl mx-auto">
                    <ScrollReveal className="text-center mb-20">
                        <h2 className="text-5xl md:text-7xl font-bold text-foreground mb-6">
                            Platform Preview
                        </h2>
                        <p className="text-xl text-muted-foreground">
                            Hover to explore our interface
                        </p>
                    </ScrollReveal>

                    <div className="grid md:grid-cols-2 gap-8">
                        <ParallaxScroll offset={100}>
                            <DepthParallaxCard>
                                <div className="aspect-video rounded-2xl bg-gradient-to-br from-primary/20 to-purple-500/20 border border-border/50 p-8 flex items-center justify-center">
                                    <div className="text-center">
                                        <BarChart3 className="w-16 h-16 text-primary mx-auto mb-4" />
                                        <h3 className="text-2xl font-bold text-foreground">Analytics Dashboard</h3>
                                    </div>
                                </div>
                            </DepthParallaxCard>
                        </ParallaxScroll>

                        <ParallaxScroll offset={-100}>
                            <DepthParallaxCard>
                                <div className="aspect-video rounded-2xl bg-gradient-to-br from-teal-500/20 to-primary/20 border border-border/50 p-8 flex items-center justify-center">
                                    <div className="text-center">
                                        <Globe className="w-16 h-16 text-primary mx-auto mb-4" />
                                        <h3 className="text-2xl font-bold text-foreground">Geo-Targeting Map</h3>
                                    </div>
                                </div>
                            </DepthParallaxCard>
                        </ParallaxScroll>
                    </div>
                </div>
            </section>

            {/* Final CTA with 3D Text */}
            <section className="relative py-32 px-4 text-center">
                <ScrollReveal>
                    <div className="max-w-4xl mx-auto">
                        <h2 className="text-5xl md:text-7xl font-bold text-foreground mb-6">
                            Ready to Transform Your Marketing?
                        </h2>
                        <p className="text-xl text-muted-foreground mb-12">
                            Join thousands of businesses already using RAAMP
                        </p>

                        <motion.button
                            type="button"
                            className="px-12 py-6 rounded-full bg-primary text-primary-foreground font-bold text-xl shadow-[0_0_40px_rgba(0,224,208,0.5)] hover:shadow-[0_0_60px_rgba(0,224,208,0.7)] transition-all duration-300"
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={() => navigate("/signup")}
                        >
                            <span className="flex items-center gap-3">
                                <Sparkles className="w-6 h-6" />
                                Start Free Trial
                                <Sparkles className="w-6 h-6" />
                            </span>
                        </motion.button>
                    </div>
                </ScrollReveal>
            </section>
        </>
    );
};

export default LusionInspiredShowcase;
