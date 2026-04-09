import { motion } from 'framer-motion';
import {
    Sparkles,
    Zap,
    Globe,
    BarChart3,
    Target,
    TrendingUp,
    Brain,
    Rocket
} from 'lucide-react';
import { Text3DScroll, SplitText3D, PerspectiveText } from '@/components/ui/text-3d';
import { MagneticImage, DepthParallaxCard, TiltCard } from '@/components/ui/magnetic-image';
import { ScrollReveal, ParallaxScroll, ScrollProgressBar, HorizontalScrollSection } from '@/components/ui/lusion-scroll';
import { HolographicCard } from '@/components/ui/holographic-card';
import raampIcon from "@/assets/raamp-logo-v5.png";
import { LiquidLogo } from "@/components/ui/liquid-logo";

const LusionInspiredShowcase = () => {
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
                            className="px-8 py-4 rounded-full bg-primary text-primary-foreground font-semibold text-lg shadow-[0_0_30px_rgba(0,224,208,0.4)] hover:shadow-[0_0_50px_rgba(0,224,208,0.6)] transition-all duration-300"
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                        >
                            <span className="flex items-center gap-2">
                                <Rocket className="w-5 h-5" />
                                Launch Platform
                            </span>
                        </motion.button>

                        <motion.button
                            className="px-8 py-4 rounded-full border border-border/50 bg-foreground/5 text-foreground hover:bg-foreground/10 backdrop-blur-sm font-medium text-lg transition-all duration-300"
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
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
            <section className="relative py-32 px-4 sm:px-6 lg:px-8 overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-b from-background via-primary/5 to-background" />

                <div className="max-w-7xl mx-auto relative z-10">
                    <ScrollReveal className="text-center mb-20">
                        <h2 className="text-5xl md:text-7xl font-bold text-foreground mb-6">
                            Intelligent Features
                        </h2>
                        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                            Experience marketing automation powered by cutting-edge AI
                        </p>
                    </ScrollReveal>

                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {[
                            {
                                icon: <Brain className="w-8 h-8" />,
                                title: 'AI Optimization',
                                description: 'Autonomous algorithms that continuously learn and adapt to maximize your ROI',
                                stat: '340%',
                                label: 'Avg. ROAS Increase'
                            },
                            {
                                icon: <Globe className="w-8 h-8" />,
                                title: 'Geo-Intent Mapping',
                                description: 'Pinpoint your ideal customers with hyper-local precision',
                                stat: '2.5M+',
                                label: 'Data Points'
                            },
                            {
                                icon: <BarChart3 className="w-8 h-8" />,
                                title: 'Real-Time Analytics',
                                description: 'Monitor performance with live dashboards and predictive insights',
                                stat: '24/7',
                                label: 'Monitoring'
                            },
                            {
                                icon: <Target className="w-8 h-8" />,
                                title: 'Smart Targeting',
                                description: 'AI identifies and targets your most valuable audience segments',
                                stat: '98%',
                                label: 'Accuracy'
                            },
                            {
                                icon: <TrendingUp className="w-8 h-8" />,
                                title: 'Growth Acceleration',
                                description: 'Scale campaigns across 5+ platforms with a single click',
                                stat: '5x',
                                label: 'Faster Growth'
                            },
                            {
                                icon: <Zap className="w-8 h-8" />,
                                title: 'Campaign Automation',
                                description: 'Set it and forget it with fully automated campaign management',
                                stat: '25hrs',
                                label: 'Time Saved/Week'
                            },
                        ].map((feature, index) => (
                            <ScrollReveal key={index} delay={index * 0.1}>
                                <TiltCard className="h-full">
                                    <HolographicCard className="p-8 h-full">
                                        <div className="flex flex-col h-full">
                                            <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-6 text-primary">
                                                {feature.icon}
                                            </div>

                                            <h3 className="text-2xl font-bold text-foreground mb-3">
                                                {feature.title}
                                            </h3>

                                            <p className="text-muted-foreground mb-6 flex-grow">
                                                {feature.description}
                                            </p>

                                            <div className="p-4 rounded-xl bg-foreground/5 border border-border/50">
                                                <div className="text-3xl font-bold text-primary mb-1">
                                                    {feature.stat}
                                                </div>
                                                <div className="text-xs text-muted-foreground">
                                                    {feature.label}
                                                </div>
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
                            className="px-12 py-6 rounded-full bg-primary text-primary-foreground font-bold text-xl shadow-[0_0_40px_rgba(0,224,208,0.5)] hover:shadow-[0_0_60px_rgba(0,224,208,0.7)] transition-all duration-300"
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
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
