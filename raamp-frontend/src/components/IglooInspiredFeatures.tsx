import { motion } from 'framer-motion';
import {
    Sparkles,
    Zap,
    Globe,
    BarChart3,
    Target,
    TrendingUp,
    Users,
    Brain
} from 'lucide-react';
import { MorphingText, ScrollMorphText, WaveText } from '@/components/ui/morphing-text';
import { BentoGridAdvanced, BentoCardAdvanced, BentoFeatureCard } from '@/components/ui/bento-grid-advanced';

const IglooInspiredFeatures = () => {
    return (
        <section className="relative py-24 px-4 sm:px-6 lg:px-8 overflow-hidden">
            {/* Background Elements */}
            <div className="absolute inset-0 bg-gradient-to-b from-background via-background/95 to-background" />

            {/* Animated Grid Background */}
            <div className="absolute inset-0 opacity-10">
                <div className="absolute inset-0 bg-[linear-gradient(to_right,#00E0D0_1px,transparent_1px),linear-gradient(to_bottom,#00E0D0_1px,transparent_1px)] bg-[size:4rem_4rem]" />
            </div>

            <div className="max-w-7xl mx-auto relative z-10">
                {/* Section Header with Morphing Text */}
                <div className="text-center mb-16 space-y-6">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.6 }}
                    >
                        <span className="inline-block px-4 py-2 rounded-full bg-primary/10 border border-primary/20 text-primary text-sm font-mono mb-6">
                            ✨ NEXT-GEN FEATURES
                        </span>
                    </motion.div>

                    <MorphingText
                        text="Advanced Marketing Intelligence"
                        className="text-4xl md:text-6xl font-bold text-white"
                        delay={0.2}
                    />

                    <ScrollMorphText
                        text="Experience the future of autonomous marketing with AI-powered insights and real-time optimization"
                        className="text-xl text-muted-foreground max-w-3xl mx-auto"
                    />
                </div>

                {/* Bento Grid Layout */}
                <BentoGridAdvanced className="mb-12">
                    {/* Large Feature Card - AI Optimization */}
                    <BentoFeatureCard
                        title="✦ AI-Powered Optimization"
                        description="Autonomous algorithms that continuously learn and adapt to maximize your marketing ROI across all channels."
                        icon={<Brain className="w-6 h-6" />}
                        colSpan="md:col-span-6 lg:col-span-6"
                        rowSpan="row-span-2"
                        stats={[
                            { label: 'Avg. ROAS Increase', value: '340%' },
                            { label: 'Time Saved', value: '25hrs/wk' },
                        ]}
                    />

                    {/* Medium Cards */}
                    <BentoCardAdvanced
                        title="◈ Geo-Intent Mapping"
                        description="Pinpoint your ideal customers with hyper-local precision using our proprietary location intelligence."
                        icon={<Globe className="w-6 h-6" />}
                        colSpan="md:col-span-3 lg:col-span-3"
                        rowSpan="row-span-1"
                        gradient="from-blue-500/20 via-blue-500/5 to-transparent"
                    />

                    <BentoCardAdvanced
                        title="❖ Real-Time Analytics"
                        description="Monitor campaign performance with live dashboards and predictive insights."
                        icon={<BarChart3 className="w-6 h-6" />}
                        colSpan="md:col-span-3 lg:col-span-3"
                        rowSpan="row-span-1"
                        gradient="from-purple-500/20 via-purple-500/5 to-transparent"
                    />

                    <BentoCardAdvanced
                        title="◆ Smart Targeting"
                        description="AI identifies and targets your most valuable audience segments automatically."
                        icon={<Target className="w-6 h-6" />}
                        colSpan="md:col-span-3 lg:col-span-3"
                        rowSpan="row-span-1"
                        gradient="from-green-500/20 via-green-500/5 to-transparent"
                    />

                    <BentoCardAdvanced
                        title="⬥ Growth Acceleration"
                        description="Scale your campaigns across 5+ platforms with a single click."
                        icon={<TrendingUp className="w-6 h-6" />}
                        colSpan="md:col-span-3 lg:col-span-3"
                        rowSpan="row-span-1"
                        gradient="from-orange-500/20 via-orange-500/5 to-transparent"
                    />

                    {/* Wide Card */}
                    <BentoCardAdvanced
                        title="⬢ Audience Intelligence"
                        description="Deep insights into customer behavior, preferences, and purchase patterns powered by advanced machine learning algorithms."
                        icon={<Users className="w-6 h-6" />}
                        colSpan="md:col-span-6 lg:col-span-6"
                        rowSpan="row-span-2"
                        gradient="from-pink-500/20 via-pink-500/5 to-transparent"
                    >
                        <div className="flex gap-6 mt-4">
                            <div className="flex-1">
                                <div className="text-3xl font-bold text-primary">2.5M+</div>
                                <div className="text-xs text-muted-foreground">Data Points Analyzed</div>
                            </div>
                            <div className="flex-1">
                                <div className="text-3xl font-bold text-primary">98%</div>
                                <div className="text-xs text-muted-foreground">Accuracy Rate</div>
                            </div>
                            <div className="flex-1">
                                <div className="text-3xl font-bold text-primary">24/7</div>
                                <div className="text-xs text-muted-foreground">Monitoring</div>
                            </div>
                        </div>
                    </BentoCardAdvanced>

                    {/* Tall Card */}
                    <BentoCardAdvanced
                        title="⚙ Campaign Automation"
                        description="Set it and forget it. Our AI handles bidding, creative optimization, and audience targeting automatically."
                        icon={<Zap className="w-6 h-6" />}
                        colSpan="md:col-span-6 lg:col-span-6"
                        rowSpan="row-span-2"
                        gradient="from-yellow-500/20 via-yellow-500/5 to-transparent"
                    >
                        <div className="space-y-3 mt-4">
                            <div className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/10">
                                <span className="text-sm">Auto-Bidding</span>
                                <div className="flex items-center gap-2">
                                    <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                                    <span className="text-xs text-green-500">Active</span>
                                </div>
                            </div>
                            <div className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/10">
                                <span className="text-sm">Creative Testing</span>
                                <div className="flex items-center gap-2">
                                    <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                                    <span className="text-xs text-green-500">Active</span>
                                </div>
                            </div>
                            <div className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/10">
                                <span className="text-sm">Audience Optimization</span>
                                <div className="flex items-center gap-2">
                                    <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                                    <span className="text-xs text-green-500">Active</span>
                                </div>
                            </div>
                        </div>
                    </BentoCardAdvanced>
                </BentoGridAdvanced>

                {/* Bottom CTA with Wave Text */}
                <motion.div
                    className="text-center mt-16"
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6, delay: 0.3 }}
                >
                    <WaveText
                        text="Ready to Transform Your Marketing?"
                        className="text-3xl font-bold text-white mb-4"
                    />
                    <p className="text-muted-foreground mb-8">
                        Join thousands of businesses already using RAAMP to scale their growth
                    </p>
                    <motion.button
                        className="px-8 py-4 rounded-full bg-primary text-primary-foreground font-semibold text-lg shadow-[0_0_30px_rgba(0,224,208,0.4)] hover:shadow-[0_0_50px_rgba(0,224,208,0.6)] transition-all duration-300"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                    >
                        <span className="flex items-center gap-2">
                            <Sparkles className="w-5 h-5" />
                            Start Free Trial
                        </span>
                    </motion.button>
                </motion.div>
            </div>
        </section>
    );
};

export default IglooInspiredFeatures;
